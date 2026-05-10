from __future__ import annotations

from pathlib import Path
import subprocess


def assert_db_not_tracked(db_path: Path) -> None:
    tracked_paths = tracked_sqlite_sidecars(db_path)
    if tracked_paths:
        tracked = ", ".join(tracked_paths)
        raise RuntimeError(f"runtime lifecycle SQLite sidecar must not be tracked by Git: {tracked}")


def tracked_sqlite_sidecars(db_path: Path) -> tuple[str, ...]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    git_root = git_root_for_path(resolved_db_path.parent)
    if git_root is None:
        return ()
    candidates = (
        resolved_db_path,
        Path(f"{resolved_db_path}-wal"),
        Path(f"{resolved_db_path}-shm"),
    )
    tracked: list[str] = []
    for candidate in candidates:
        try:
            relative = candidate.relative_to(git_root)
        except ValueError:
            continue
        result = subprocess.run(
            ["git", "-C", str(git_root), "ls-files", "--cached", "--error-unmatch", "--", relative.as_posix()],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            tracked.append(relative.as_posix())
    return tuple(tracked)


def git_root_for_path(path: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root).resolve() if root else None


__all__ = ["assert_db_not_tracked", "git_root_for_path", "tracked_sqlite_sidecars"]
