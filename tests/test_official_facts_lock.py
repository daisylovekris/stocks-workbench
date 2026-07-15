import hashlib
import json
import threading
import time
from contextlib import contextmanager
from types import SimpleNamespace
from pathlib import Path

import pytest

from tools import generate_daily_facts as gdf
from tools import official_facts_lock as ofl


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "daily_facts"


def generator_args(output: Path) -> SimpleNamespace:
    return SimpleNamespace(
        symbol="300274",
        date="2026-07-10",
        output=str(output),
        source="tencent",
        dry_run=False,
        no_write=False,
        write_partial=True,
        timeout=1.0,
    )


def generator_quote(name: str) -> dict:
    payload = json.loads((FIXTURE_ROOT / "tencent_quote_0710.json").read_text(encoding="utf-8"))
    payload["source_name"] = name
    return payload


def generator_write(
    official: Path,
    *,
    expected_sha256: str | None,
    name: str,
    lock_dir: Path,
) -> str | None:
    _facts, _status, wrote, final_sha = gdf.write_generated_facts_transaction(
        args=generator_args(official),
        output_path=official,
        quote_result=generator_quote(name),
        volume_ratio_candidate=None,
        expected_sha256=expected_sha256,
        lock_dir=lock_dir,
    )
    assert wrote
    return final_sha


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


def test_two_compliant_writers_serialize_and_second_stale_sha_stops(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    official = tmp_path / "official.json"
    lock_dir = tmp_path / "locks"
    old_sha = write_json(official, {"symbol": "300274", "trade_date": "2026-07-10", "name": "old"})
    first_at_replace = threading.Event()
    release_first = threading.Event()
    original_replace = gdf.os.replace

    def delayed_replace(src, dst):
        if threading.current_thread().name == "first-writer" and Path(dst) == official:
            first_at_replace.set()
            assert release_first.wait(5)
        return original_replace(src, dst)

    monkeypatch.setattr(gdf.os, "replace", delayed_replace)
    results: dict[str, object] = {}

    def first_writer() -> None:
        results["first_sha"] = generator_write(
            official,
            expected_sha256=old_sha,
            name="first",
            lock_dir=lock_dir,
        )
        results["first"] = "written"

    def second_writer() -> None:
        try:
            generator_write(
                official,
                expected_sha256=old_sha,
                name="second",
                lock_dir=lock_dir,
            )
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
    assert isinstance(results["second"], ofl.OfficialFactsChangedError)
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
        context.setattr(
            gdf,
            "validate_generated_facts_pack",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("write stopped")),
        )
        with pytest.raises(RuntimeError, match="write stopped"):
            generator_write(
                official,
                expected_sha256=old_sha,
                name="failed",
                lock_dir=lock_dir,
            )

    assert json.loads(official.read_text(encoding="utf-8")) == old_payload
    assert not [path for path in tmp_path.iterdir() if path.name.startswith(".official.json.")]
    assert not list(tmp_path.glob("*.lock"))
    generator_write(
        official,
        expected_sha256=old_sha,
        name="next",
        lock_dir=lock_dir,
    )
    assert json.loads(official.read_text(encoding="utf-8"))["name"] == "next"


def test_generator_full_transaction_actions_observe_held_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    official = tmp_path / "official.json"
    lock_dir = tmp_path / "locks"
    old_sha = write_json(
        official,
        {"symbol": "300274", "trade_date": "2026-07-10", "name": "old"},
    )
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
    real_parse = gdf.parse_existing_official_bytes
    real_build = gdf.build_facts_pack
    real_validate = gdf.validate_generated_facts_pack
    real_temp = gdf.tempfile.NamedTemporaryFile
    real_replace = gdf.os.replace

    def observed_read(*args, **kwargs):
        mark("read_official")
        return real_read(*args, **kwargs)

    def observed_sha(data):
        mark("sha256")
        return real_sha(data)

    def observed_parse(*args, **kwargs):
        mark("parse_official")
        return real_parse(*args, **kwargs)

    def observed_build(*args, **kwargs):
        mark("build_final")
        return real_build(*args, **kwargs)

    def observed_validate(*args, **kwargs):
        mark("validator")
        return real_validate(*args, **kwargs)

    def observed_temp(*args, **kwargs):
        mark("temp_write")
        return real_temp(*args, **kwargs)

    def observed_replace(src, dst):
        mark("replace")
        return real_replace(src, dst)

    monkeypatch.setattr(ofl, "official_facts_lock", observed_lock)
    monkeypatch.setattr(ofl, "read_current_official", observed_read)
    monkeypatch.setattr(ofl, "sha256_bytes", observed_sha)
    monkeypatch.setattr(gdf, "parse_existing_official_bytes", observed_parse)
    monkeypatch.setattr(gdf, "build_facts_pack", observed_build)
    monkeypatch.setattr(gdf, "validate_generated_facts_pack", observed_validate)
    monkeypatch.setattr(gdf.tempfile, "NamedTemporaryFile", observed_temp)
    monkeypatch.setattr(gdf.os, "replace", observed_replace)

    final_sha = generator_write(
        official,
        expected_sha256=old_sha,
        name="locked result",
        lock_dir=lock_dir,
    )
    assert final_sha is not None
    assert events[0] == "lock_enter" and events[-1] == "lock_exit"
    for required in (
        "read_official",
        "sha256",
        "parse_official",
        "build_final",
        "validator",
        "temp_write",
        "replace",
    ):
        assert required in events
    replace_index = events.index("replace")
    assert "read_official" in events[replace_index + 1 :]
    assert "sha256" in events[replace_index + 1 :]
