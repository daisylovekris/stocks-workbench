"""Shared exclusive-lock contract for repository-owned official facts writers.

Every repository writer that can replace ``data/daily/*_facts.json`` must hold
this lock from the locked re-read and expected-SHA check through validation,
comparison, temporary-file write, atomic replace, directory fsync, and the
post-replace bytes/SHA fingerprint.

The lock coordinates repository writers that follow this convention.  A process
that bypasses the shared lock can still change a pathname between a final hash
check and POSIX ``os.replace``; POSIX replacement does not provide a content-hash
conditional update.  Callers must not claim coverage for such external writes
and must not add retry loops that imply that guarantee.
"""

from __future__ import annotations

import fcntl
import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DEFAULT_LOCK_DIR = Path("/private/tmp/stocks-facts-locks")


class OfficialFactsChangedError(ValueError):
    """Raised when the locked official file no longer matches its expected SHA."""


@dataclass
class OfficialFactsLockState:
    """Read-only observable state for one held official-facts lock."""

    official_path: Path
    lock_path: Path
    _held: bool = False

    @property
    def held(self) -> bool:
        return self._held

    def assert_held_for(self, official_path: Path) -> None:
        if not self._held:
            raise RuntimeError("official facts lock is not held")
        resolved = official_path.expanduser().resolve(strict=False)
        if resolved != self.official_path:
            raise RuntimeError(
                f"official facts lock targets {self.official_path}, not {resolved}"
            )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def lock_path_for(official_path: Path, *, lock_dir: Path | None = None) -> Path:
    resolved = str(official_path.expanduser().resolve(strict=False))
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()
    return (lock_dir or DEFAULT_LOCK_DIR) / f"{digest}.lock"


@contextmanager
def official_facts_lock(
    official_path: Path,
    *,
    lock_dir: Path | None = None,
) -> Iterator[OfficialFactsLockState]:
    """Hold the persistent repository-writer lock for one official facts path."""

    path = lock_path_for(official_path, lock_dir=lock_dir)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    state = OfficialFactsLockState(
        official_path=official_path.expanduser().resolve(strict=False),
        lock_path=path,
    )
    with path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        state._held = True
        try:
            yield state
        finally:
            state._held = False
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_current_official(
    official_path: Path,
    *,
    lock_state: OfficialFactsLockState,
) -> tuple[bytes | None, str | None]:
    """Read the current official bytes and SHA while the matching lock is held."""

    lock_state.assert_held_for(official_path)
    if not official_path.exists():
        return None, None
    data = official_path.read_bytes()
    return data, sha256_bytes(data)


def read_locked_official(
    official_path: Path,
    *,
    expected_sha256: str | None,
    lock_state: OfficialFactsLockState,
) -> tuple[bytes | None, str | None]:
    """Read and compare an official file while its shared lock is held.

    ``expected_sha256=None`` means that the caller observed no official file and
    requires it to remain absent.
    """

    data, actual = read_current_official(
        official_path,
        lock_state=lock_state,
    )
    if data is None:
        if expected_sha256 is not None:
            raise OfficialFactsChangedError(
                f"official facts disappeared: expected sha256 {expected_sha256}"
            )
        return None, None
    if actual is None:
        raise AssertionError("existing official facts must have a sha256")
    if expected_sha256 is None:
        raise OfficialFactsChangedError(
            f"official facts appeared after initial read: got sha256 {actual}"
        )
    if actual != expected_sha256:
        raise OfficialFactsChangedError(
            f"official sha256 mismatch: expected {expected_sha256}, got {actual}"
        )
    return data, actual


def snapshot_official_sha(
    official_path: Path,
    *,
    lock_dir: Path | None = None,
) -> str | None:
    """Take a short, locked SHA snapshot before lock-free raw-data preparation."""

    with official_facts_lock(official_path, lock_dir=lock_dir) as lock_state:
        _data, sha256 = read_current_official(
            official_path,
            lock_state=lock_state,
        )
        return sha256
