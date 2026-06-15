from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    file_sha256,
)


def compact_database(db_path: Path) -> dict[str, Any]:
    before_bytes = db_path.stat().st_size
    sidecars_before = sqlite_sidecar_infos(db_path)
    with tempfile.TemporaryDirectory(prefix="mas-runtime-lifecycle-retention.") as tmpdir:
        compacted = Path(tmpdir) / "runtime_lifecycle.compacted.sqlite"
        with sqlite3.connect(db_path) as conn:
            quoted_compacted = str(compacted).replace("'", "''")
            conn.execute(f"VACUUM INTO '{quoted_compacted}'")
        with sqlite3.connect(compacted) as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            return {
                "status": "blocked_compacted_integrity_check_failed",
                "bytes_before": before_bytes,
                "integrity_check": integrity,
            }
        compacted.replace(db_path)
    sidecar_cleanup = remove_sqlite_sidecars(db_path, status="removed_after_compact_replace")
    after_bytes = db_path.stat().st_size
    return {
        "status": "compacted",
        "bytes_before": before_bytes,
        "bytes_after": after_bytes,
        "release_bytes": max(0, before_bytes - after_bytes),
        "sidecars_before": sidecars_before,
        "sidecar_cleanup": sidecar_cleanup,
    }


def sqlite_sidecar_infos(db_path: Path) -> list[dict[str, Any]]:
    sidecars: list[dict[str, Any]] = []
    for path in (Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
        if not path.exists():
            continue
        sidecars.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return sidecars


def remove_sqlite_sidecars(db_path: Path, *, status: str) -> list[dict[str, Any]]:
    removed: list[dict[str, Any]] = []
    for sidecar in sqlite_sidecar_infos(db_path):
        Path(str(sidecar["path"])).unlink()
        sidecar["status"] = status
        removed.append(sidecar)
    return removed


def sqlite_integrity_check(db_path: Path, *, immutable: bool) -> dict[str, Any]:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    if immutable:
        uri = f"{uri}&immutable=1"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            value = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.Error as exc:
        return {
            "status": "error",
            "mode": "immutable" if immutable else "normal_readonly",
            "error": str(exc),
        }
    return {
        "status": "ok" if value == "ok" else "failed",
        "mode": "immutable" if immutable else "normal_readonly",
        "result": value,
    }


__all__ = [
    "compact_database",
    "remove_sqlite_sidecars",
    "sqlite_integrity_check",
    "sqlite_sidecar_infos",
]
