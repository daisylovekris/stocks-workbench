import hashlib
import json
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

from tools import official_facts_lock as ofl
from tools import official_facts_transaction as oft


def transaction_candidate(name: str) -> dict:
    return {
        "schema_version": "facts_pack_v0.2",
        "trade_date": "2026-07-10",
        "symbol": "300274",
        "name": name,
        "quote": {
            "open": 123.17,
            "high": 123.8,
            "low": 114.0,
            "close": 114.79,
            "prev_close": 124.01,
            "pct_change": -7.434884283525522,
            "amount": 111.28,
            "turnover_rate": 5.92,
        },
        "quote_verification": {"status": "confirmed", "source_date": "2026-07-10"},
        "volume_ratio": {
            "candidate_value": 1.79,
            "confirmed_value": 1.79,
            "source": "manual_check",
            "verification": {"status": "manual_confirmed", "method": "legacy_manual_confirmation"},
            "manual_verification": {
                "decided_by": "pytest",
                "decided_at": "2026-07-10T16:00:00Z",
                "source": "pytest",
                "reason": "transaction test",
            },
        },
        "missing": {"market_indices": None, "sector_context": None, "disclosure_status": None, "news_policy_context": None},
        "needs_manual_check": {
            "volume_ratio": False,
            "market_indices": False,
            "sector_context": False,
            "disclosure_status": False,
            "news_policy_context": False,
        },
        "run": {"status": "success"},
    }


def generator_write(
    official: Path,
    *,
    expected_sha256: str | None,
    name: str,
    lock_dir: Path,
) -> tuple[bool, str | None]:
    candidate = transaction_candidate(name)
    result = oft.promote_candidate_to_official(
        repo_root=official.parent,
        official_path=official,
        candidate=candidate,
        candidate_bytes=oft.json_bytes(candidate),
        symbol="300274",
        target_date="2026-07-10",
        expected_sha256=expected_sha256,
        lock_dir=lock_dir,
        enforce_canonical_path=False,
    )
    return result.write_action in {"created", "identical_noop"}, result.official_sha256_after


def write_json(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ofl.sha256_file(path)


def test_lock_path_uses_absolute_path_hash_and_persistent_lock_file(tmp_path: Path) -> None:
    official = tmp_path / "official.json"
    lock_dir = tmp_path / "locks"
    expected = ofl.lock_path_for(official, lock_dir=lock_dir)
    digest = hashlib.sha256(str(official.resolve()).encode("utf-8")).hexdigest()
    assert expected == lock_dir / f"{digest}.lock"
    state = None
    with pytest.raises(RuntimeError, match="stop"):
        with ofl.official_facts_lock(official, lock_dir=lock_dir) as state:
            assert state.held
            assert expected.exists()
            raise RuntimeError("stop")
    assert state is not None and not state.held
    assert expected.exists()
    assert not list(tmp_path.glob("*.lock"))
    with ofl.official_facts_lock(official, lock_dir=lock_dir):
        pass


def test_canonical_official_path_is_symbol_date_derived_and_rejects_traversal(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    expected = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    assert oft.canonical_official_path(repo, "300274", "2026-07-16") == expected
    with pytest.raises(ValueError):
        oft.canonical_official_path(repo, "../300274", "2026-07-16")
    with pytest.raises(ValueError):
        oft.canonical_official_path(repo, "300274", "../2026-07-16")


def test_official_symlink_target_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    daily = repo / "data" / "daily"
    daily.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    official = daily / "300274_2026-07-16_facts.json"
    official.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes repository|symlink"):
        oft.validate_official_path(official, repo, "300274", "2026-07-16")


def test_two_compliant_writers_serialize_and_second_stale_sha_stops(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    official = tmp_path / "official.json"
    lock_dir = tmp_path / "locks"
    old_sha = None
    first_at_replace = threading.Event()
    release_first = threading.Event()
    original_replace = oft.os.replace

    def delayed_replace(src, dst):
        if threading.current_thread().name == "first-writer" and Path(dst) == official:
            first_at_replace.set()
            assert release_first.wait(5)
        return original_replace(src, dst)

    monkeypatch.setattr(oft.os, "replace", delayed_replace)
    results: dict[str, object] = {}

    def first_writer() -> None:
        wrote, sha = generator_write(
            official,
            expected_sha256=old_sha,
            name="first",
            lock_dir=lock_dir,
        )
        assert wrote
        results["first_sha"] = sha
        results["first"] = "written"

    def second_writer() -> None:
        try:
            wrote, _sha = generator_write(
                official,
                expected_sha256=old_sha,
                name="second",
                lock_dir=lock_dir,
            )
            results["second"] = "blocked" if not wrote else "written"
        except Exception as exc:  # asserted below
            results["second"] = exc

    first = threading.Thread(target=first_writer, name="first-writer")
    second = threading.Thread(target=second_writer, name="second-writer")
    first.start()
    assert first_at_replace.wait(5)
    second.start()
    time.sleep(0.05)
    assert second.is_alive()
    release_first.set()
    first.join(5)
    second.join(5)

    assert results["first"] == "written"
    assert results["second"] == "blocked"
    assert json.loads(official.read_text(encoding="utf-8"))["name"] == "first"
    assert results["first_sha"] == ofl.sha256_file(official)
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_writer_exception_cleans_temp_and_next_writer_can_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    official = tmp_path / "official.json"
    lock_dir = tmp_path / "locks"
    old_payload = {"symbol": "300274", "trade_date": "2026-07-10", "name": "old"}
    old_sha = write_json(official, old_payload)

    with monkeypatch.context() as context:
        context.setattr(oft.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("write stopped")))
        with pytest.raises(RuntimeError, match="write stopped"):
            generator_write(
                tmp_path / "new_official.json",
                expected_sha256=None,
                name="failed",
                lock_dir=lock_dir,
            )

    assert json.loads(official.read_text(encoding="utf-8")) == old_payload
    assert not [path for path in tmp_path.iterdir() if path.name.endswith(".tmp")]
    assert not list(tmp_path.glob("*.lock"))
    wrote, _sha = generator_write(
        official,
        expected_sha256=old_sha,
        name="next",
        lock_dir=lock_dir,
    )
    assert not wrote
    assert json.loads(official.read_text(encoding="utf-8")) == old_payload


def test_generator_full_transaction_actions_observe_held_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    official = tmp_path / "official.json"
    lock_dir = tmp_path / "locks"
    old_sha = None
    holder: dict[str, object] = {}
    events: list[str] = []
    real_lock = ofl.official_facts_lock

    @contextmanager
    def observed_lock(*args, **kwargs):
        with real_lock(*args, **kwargs) as state:
            holder["state"] = state
            events.append("lock_enter")
            yield state
            assert state.held
        events.append("lock_exit")
        assert not state.held

    def mark(name: str) -> None:
        state = holder.get("state")
        assert isinstance(state, ofl.OfficialFactsLockState) and state.held
        events.append(name)

    real_read = ofl.read_current_official
    real_sha = ofl.sha256_bytes
    real_temp = oft.tempfile.NamedTemporaryFile
    real_replace = oft.os.replace

    def observed_read(*args, **kwargs):
        mark("read_official")
        return real_read(*args, **kwargs)

    def observed_sha(data):
        state = holder.get("state")
        if isinstance(state, ofl.OfficialFactsLockState) and state.held:
            mark("sha256")
        return real_sha(data)

    def observed_temp(*args, **kwargs):
        mark("temp_write")
        return real_temp(*args, **kwargs)

    def observed_replace(src, dst):
        mark("replace")
        return real_replace(src, dst)

    monkeypatch.setattr(ofl, "official_facts_lock", observed_lock)
    monkeypatch.setattr(ofl, "read_current_official", observed_read)
    monkeypatch.setattr(ofl, "sha256_bytes", observed_sha)
    monkeypatch.setattr(oft.tempfile, "NamedTemporaryFile", observed_temp)
    monkeypatch.setattr(oft.os, "replace", observed_replace)

    wrote, final_sha = generator_write(
        official,
        expected_sha256=old_sha,
        name="locked result",
        lock_dir=lock_dir,
    )
    assert wrote
    assert final_sha is not None
    assert events[0] == "lock_enter" and events[-1] == "lock_exit"
    for required in (
        "read_official",
        "sha256",
        "temp_write",
        "replace",
    ):
        assert required in events
    replace_index = events.index("replace")
    assert "read_official" in events[replace_index + 1 :]
    assert "sha256" in events[replace_index + 1 :]
