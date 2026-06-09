from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    artifact_slug as _artifact_slug,
    write_json as _write_json,
)


SCHEMA_VERSION = 1
RECEIPT_SURFACE_KIND = "legacy_codex_homes_migration_receipt"


def migrate_legacy_codex_homes(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    apply: bool,
    apply_allowed: bool,
) -> dict[str, Any]:
    legacy_root = quest_root / ".ds" / "codex_homes"
    bytes_before = _directory_size_bytes(legacy_root)
    if not legacy_root.exists():
        return _write_latest(
            quest_root=quest_root,
            summary=_receipt_base(
                quest_root=quest_root,
                quest_id=quest_id,
                recorded_at=recorded_at,
                apply=apply,
                legacy_root=legacy_root,
                status="nothing_to_retain",
                exists=False,
            ),
        )

    manifest = _legacy_bucket_source_manifest(
        quest_root=quest_root,
        source_root=legacy_root,
        recorded_at=recorded_at,
    )
    source_manifest_path = _legacy_executor_home_root(quest_root) / "source_manifest.json"
    if apply and not apply_allowed:
        summary = _receipt_base(
            quest_root=quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            apply=True,
            legacy_root=legacy_root,
            status="blocked_storage_maintenance_not_maintained",
            exists=True,
        )
        summary.update(_manifest_summary(manifest, source_manifest_path=source_manifest_path, quest_root=quest_root))
        _write_json(source_manifest_path, manifest)
        return _write_latest(quest_root=quest_root, summary=summary)

    if not apply:
        summary = _receipt_base(
            quest_root=quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            apply=False,
            legacy_root=legacy_root,
            status="planned",
            exists=True,
        )
        summary.update(_manifest_summary(manifest, source_manifest_path=source_manifest_path, quest_root=quest_root))
        _write_json(source_manifest_path, manifest)
        return _write_latest(quest_root=quest_root, summary=summary)

    archive_path = _legacy_codex_homes_archive_path(
        quest_root=quest_root,
        recorded_at=recorded_at,
        source_root=legacy_root,
    )
    restore_proof_path = archive_path.with_suffix(".restore_proof.json")
    source_manifest_path = archive_path.with_suffix(".manifest.json")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(source_manifest_path, manifest)
    _write_tar_gz_archive(source_root=legacy_root, archive_path=archive_path)
    restore_proof = _tar_gz_restore_proof(archive_path=archive_path, manifest=manifest, verified_at=_utc_now())
    _write_json(restore_proof_path, restore_proof)
    if restore_proof.get("status") != "verified":
        summary = _receipt_base(
            quest_root=quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            apply=True,
            legacy_root=legacy_root,
            status="blocked_restore_proof_failed",
            exists=True,
        )
        summary.update(_manifest_summary(manifest, source_manifest_path=source_manifest_path, quest_root=quest_root))
        summary.update(_archive_summary(archive_path=archive_path, restore_proof_path=restore_proof_path, quest_root=quest_root))
        summary["restore_proof"] = restore_proof
        return _write_latest(quest_root=quest_root, summary=summary)

    shutil.rmtree(legacy_root)
    archive_bytes = archive_path.stat().st_size
    summary = _receipt_base(
        quest_root=quest_root,
        quest_id=quest_id,
        recorded_at=recorded_at,
        apply=True,
        legacy_root=legacy_root,
        status="applied",
        exists=False,
        removed=True,
    )
    summary.update(_manifest_summary(manifest, source_manifest_path=source_manifest_path, quest_root=quest_root))
    summary.update(_archive_summary(archive_path=archive_path, restore_proof_path=restore_proof_path, quest_root=quest_root))
    summary.update(
        {
            "archive_bytes": archive_bytes,
            "archive_sha256": _sha256(archive_path),
            "restore_proof": restore_proof,
            "actual_release_bytes": max(0, bytes_before - archive_bytes),
        }
    )
    return _write_latest(quest_root=quest_root, summary=summary)


def _receipt_base(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    apply: bool,
    legacy_root: Path,
    status: str,
    exists: bool,
    removed: bool = False,
) -> dict[str, Any]:
    return {
        "surface_kind": RECEIPT_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "recorded_at": recorded_at,
        "apply": bool(apply),
        "source_kind": "legacy_ds_intake",
        "legacy_codex_homes_root": _relpath(legacy_root, quest_root),
        "legacy_codex_homes_exists": bool(exists),
        "legacy_codex_homes_removed": bool(removed),
        "actual_release_bytes": 0,
        "body_included": False,
        "legacy_ds_long_term_read_allowed": False,
    }


def _manifest_summary(
    manifest: Mapping[str, Any],
    *,
    source_manifest_path: Path,
    quest_root: Path,
) -> dict[str, Any]:
    return {
        "source_manifest_path": _relpath(source_manifest_path, quest_root),
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
    }


def _archive_summary(*, archive_path: Path, restore_proof_path: Path, quest_root: Path) -> dict[str, Any]:
    return {
        "archive_path": _relpath(archive_path, quest_root),
        "restore_proof_path": _relpath(restore_proof_path, quest_root),
    }


def _write_latest(*, quest_root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    latest_path = _legacy_executor_home_root(quest_root) / "latest.json"
    _write_json(latest_path, summary)
    summary["latest_receipt_path"] = _relpath(latest_path, quest_root)
    return summary


def _legacy_bucket_source_manifest(
    *,
    quest_root: Path,
    source_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    files = [
        _file_manifest(path=path.resolve(), quest_root=quest_root, source_root=source_root)
        for path in sorted(source_root.rglob("*"))
        if path.is_file()
    ]
    payload = {
        "surface_kind": "legacy_codex_homes_source_manifest",
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "source_kind": "legacy_ds_intake",
        "legacy_source_root": _relpath(source_root, quest_root),
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "files": files,
        "body_included": False,
        "legacy_ds_long_term_read_allowed": False,
    }
    payload["manifest_sha256"] = _sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def _file_manifest(*, path: Path, quest_root: Path, source_root: Path) -> dict[str, Any]:
    return {
        "path": _relpath(path, quest_root),
        "attempt_path": _relpath(path, source_root),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "body_included": False,
    }


def _write_tar_gz_archive(*, source_root: Path, archive_path: Path) -> None:
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in sorted(source_root.rglob("*")):
            archive.add(path, arcname=path.relative_to(source_root.parent))


def _tar_gz_restore_proof(*, archive_path: Path, manifest: Mapping[str, Any], verified_at: str) -> dict[str, Any]:
    expected = {
        str(item.get("attempt_path") or ""): str(item.get("sha256") or "")
        for item in list(manifest.get("files") or [])
        if isinstance(item, Mapping)
    }
    observed: dict[str, str] = {}
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                digest = hashlib.sha256()
                for chunk in iter(lambda: extracted.read(1024 * 1024), b""):
                    digest.update(chunk)
                parts = Path(member.name).parts
                attempt_path = "/".join(parts[1:]) if len(parts) > 1 else member.name
                observed[attempt_path] = digest.hexdigest()
    except (OSError, tarfile.TarError) as exc:
        return {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "archive_path": str(archive_path),
        }
    missing = sorted(path for path in expected if path not in observed)
    mismatched = sorted(path for path, sha in expected.items() if observed.get(path) != sha)
    status = "verified" if not missing and not mismatched and len(observed) == len(expected) else "failed"
    return {
        "status": status,
        "archive_path": str(archive_path),
        "archive_sha256": _sha256(archive_path),
        "source_manifest_sha256": manifest.get("manifest_sha256"),
        "expected_file_count": len(expected),
        "observed_file_count": len(observed),
        "missing": missing,
        "mismatched": mismatched,
        "verified_at": verified_at,
    }


def _legacy_executor_home_root(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "restore_index" / "legacy_executor_home"


def _legacy_codex_homes_archive_path(
    *,
    quest_root: Path,
    recorded_at: str,
    source_root: Path,
) -> Path:
    relative = str(_relpath(source_root, quest_root) or "legacy_codex_homes").replace("/", "__")
    slug = _artifact_slug(recorded_at)
    return _legacy_executor_home_root(quest_root) / f"{slug}_{relative}.tar.gz"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(candidate.stat().st_size for candidate in path.rglob("*") if candidate.is_file())


def _relpath(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = ["RECEIPT_SURFACE_KIND", "migrate_legacy_codex_homes"]
