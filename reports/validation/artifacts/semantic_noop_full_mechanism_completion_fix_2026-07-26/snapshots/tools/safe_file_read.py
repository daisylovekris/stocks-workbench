"""No-follow reads for evidence files constrained beneath an allowed root."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class SafeFileReadError(ValueError):
    """Raised when an evidence path cannot be read without following links."""


def _absolute_lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def read_regular_file_beneath(
    path: Path,
    *,
    root: Path,
    label: str,
    missing_ok: bool = False,
) -> tuple[bytes | None, Path]:
    """Read one regular file through a single ``O_NOFOLLOW`` fd chain."""

    if not hasattr(os, "O_NOFOLLOW"):
        raise SafeFileReadError(f"{label} cannot be read safely on this platform")
    root_path = _absolute_lexical_path(root)
    target_path = _absolute_lexical_path(path)
    if not _inside(target_path, root_path):
        raise SafeFileReadError(f"{label} escapes its allowed root")
    root_resolved = root_path.resolve(strict=False)
    target_resolved = target_path.resolve(strict=False)
    if not _inside(target_resolved, root_resolved):
        raise SafeFileReadError(f"{label} resolves outside its allowed root")

    relative = target_path.relative_to(root_path)
    if not relative.parts:
        raise SafeFileReadError(f"{label} must name a regular file below its allowed root")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []
    try:
        current = os.open(root_path, directory_flags)
        descriptors.append(current)
        if not stat.S_ISDIR(os.fstat(current).st_mode):
            raise SafeFileReadError(f"{label} allowed root is not a directory")
        for component in relative.parts[:-1]:
            current = os.open(component, directory_flags, dir_fd=current)
            descriptors.append(current)
            if not stat.S_ISDIR(os.fstat(current).st_mode):
                raise SafeFileReadError(f"{label} parent is not a directory")
        descriptor = os.open(relative.parts[-1], file_flags, dir_fd=current)
        descriptors.append(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise SafeFileReadError(f"{label} is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), target_path
    except FileNotFoundError as exc:
        if missing_ok:
            return None, target_path
        raise SafeFileReadError(f"{label} is missing") from exc
    except SafeFileReadError:
        raise
    except OSError as exc:
        raise SafeFileReadError(f"{label} is unsafe or unreadable: {type(exc).__name__}") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
