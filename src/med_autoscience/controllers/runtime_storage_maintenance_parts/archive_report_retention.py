from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    artifact_slug as _artifact_slug,
    file_sha256 as _file_sha256,
    safe_artifact_id as _safe_artifact_id,
    utc_now as _utc_now,
    write_json as _write_json,
)


SCHEMA_VERSION = 1
ARCHIVE_RETENTION_SURFACE_KIND = "runtime_restore_proof_archive_body_retention"
REPORT_RETENTION_SURFACE_KIND = "runtime_report_snapshot_retention"


def retain_restore_proof_archive_bodies(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    apply: bool = False,
    min_archive_mb: int = 16,
    cold_store_root: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    threshold_bytes = max(0, int(min_archive_mb)) * 1024 * 1024
    cold_root = _cold_store_root(
        quest_root=resolved_quest_root,
        quest_id=quest_id,
        cold_store_root=cold_store_root,
    )
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    actual_release_bytes = 0
    moved_count = 0
    deduped_count = 0
    for archive_path in _restore_proof_archive_paths(resolved_quest_root):
        inspection = _inspect_restore_archive(
            quest_root=resolved_quest_root,
            archive_path=archive_path,
            threshold_bytes=threshold_bytes,
        )
        if inspection.get("status") == "blocked":
            blockers.append(inspection)
            continue
        if inspection.get("status") != "candidate":
            continue
        if apply:
            applied = _apply_archive_body_retention(
                archive_path=archive_path,
                quest_root=resolved_quest_root,
                cold_root=cold_root,
                inspection=inspection,
            )
            inspection.update(applied)
            actual_release_bytes += int(applied.get("active_release_bytes") or 0)
            if applied.get("status") == "moved_to_cold_object":
                moved_count += 1
            elif applied.get("status") == "deduped_to_existing_cold_object":
                deduped_count += 1
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(inspection)
        candidates.append(inspection)

    status = (
        "applied"
        if apply and (moved_count or deduped_count)
        else "blocked"
        if apply and blockers
        else "planned"
        if candidates
        else "nothing_to_retain"
        if not blockers
        else "blocked"
    )
    receipt = {
        "surface_kind": ARCHIVE_RETENTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "recorded_at": recorded_at,
        "apply": bool(apply),
        "min_archive_bytes": threshold_bytes,
        "cold_store_root": str(cold_root),
        "candidate_count": len(candidates),
        "moved_count": moved_count,
        "deduped_count": deduped_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "restore_proof_required": True,
        "mutation_policy": {
            "moves_archive_body": bool(apply),
            "keeps_original_archive_path_as_symlink": bool(apply),
            "deletes_restore_manifest_or_proof": False,
            "deletes_domain_truth": False,
        },
        "candidate_samples": _sample_entries(candidates),
        "blocker_samples": _sample_entries(blockers),
    }
    receipt_path = _retention_root(resolved_quest_root) / f"{_artifact_slug(recorded_at)}.archive_body_retention.json"
    latest_path = _retention_root(resolved_quest_root) / "latest_archive_body_retention.json"
    _write_json(receipt_path, receipt)
    _write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)
    return receipt


def retain_report_snapshots(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    apply: bool = False,
    keep_recent_days: int = 1,
    daily_samples: int = 2,
    max_files: int | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    reports_root = resolved_quest_root / "artifacts" / "reports"
    keep_cutoff = datetime.now(UTC) - timedelta(days=max(0, int(keep_recent_days)))
    retained = _retained_report_paths(
        reports_root=reports_root,
        keep_cutoff=keep_cutoff,
        daily_samples=max(0, int(daily_samples)),
    )
    candidates = [
        path
        for path in _report_snapshot_paths(reports_root)
        if path not in retained and not _is_latest_alias(path) and _mtime_utc(path) < keep_cutoff
    ]
    if max_files is not None:
        candidates = candidates[: max(0, int(max_files))]
    manifest: dict[str, Any] | None = None
    restore_proof: dict[str, Any] | None = None
    bundle_path: Path | None = None
    actual_release_bytes = 0
    if candidates:
        manifest = _report_manifest(
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            source_paths=candidates,
            keep_recent_days=keep_recent_days,
            daily_samples=daily_samples,
        )
        bundle_root = _retention_root(resolved_quest_root) / "report_snapshot_bundles"
        bundle_root.mkdir(parents=True, exist_ok=True)
        slug = _artifact_slug(recorded_at)
        safe_quest_id = _safe_artifact_id(quest_id)
        bundle_path = bundle_root / f"{safe_quest_id}-{slug}-report-snapshots.tar.gz"
        manifest_path = bundle_root / f"{safe_quest_id}-{slug}-report-snapshots.manifest.json"
        restore_proof_path = bundle_root / f"{safe_quest_id}-{slug}-report-snapshots.restore_proof.json"
        if apply:
            if bundle_path.exists() or manifest_path.exists() or restore_proof_path.exists():
                raise FileExistsError(f"runtime report retention target already exists: {bundle_path}")
            _write_json(manifest_path, manifest)
            _write_report_bundle(quest_root=resolved_quest_root, bundle_path=bundle_path, source_paths=candidates)
            restore_proof = _verify_report_bundle(bundle_path=bundle_path, manifest=manifest, verified_at=_utc_now())
            _write_json(restore_proof_path, restore_proof)
            if restore_proof["status"] == "verified":
                bytes_before = sum(int(item["size_bytes"]) for item in manifest["source_files"])
                for path in candidates:
                    path.unlink()
                actual_release_bytes = max(
                    0,
                    bytes_before - bundle_path.stat().st_size - manifest_path.stat().st_size - restore_proof_path.stat().st_size,
                )
        else:
            manifest_path = bundle_root / f"{safe_quest_id}-{slug}-report-snapshots.manifest.json"
            restore_proof_path = bundle_root / f"{safe_quest_id}-{slug}-report-snapshots.restore_proof.json"

    status = (
        "applied"
        if apply and restore_proof and restore_proof.get("status") == "verified"
        else "blocked_restore_proof_failed"
        if apply and candidates
        else "planned"
        if candidates
        else "nothing_to_retain"
    )
    receipt = {
        "surface_kind": REPORT_RETENTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "recorded_at": recorded_at,
        "apply": bool(apply),
        "reports_root": str(reports_root),
        "keep_recent_days": int(keep_recent_days),
        "daily_samples": int(daily_samples),
        "candidate_count": len(candidates),
        "retained_count": len(retained),
        "actual_release_bytes": actual_release_bytes,
        "bundle_path": str(bundle_path) if bundle_path else None,
        "source_manifest_path": str(manifest_path) if candidates else None,
        "restore_proof_path": str(restore_proof_path) if candidates else None,
        "restore_proof": _restore_proof_summary(restore_proof) if restore_proof else None,
        "candidate_samples": _sample_values([path.relative_to(resolved_quest_root).as_posix() for path in candidates]),
        "retained_samples": _sample_values([path.relative_to(resolved_quest_root).as_posix() for path in sorted(retained)]),
        "body_included": False,
        "mutation_policy": {
            "bundles_timestamped_reports": bool(apply),
            "deletes_only_after_restore_proof": bool(apply),
            "keeps_latest_aliases": True,
            "keeps_recent_files": True,
            "keeps_daily_samples": int(daily_samples) > 0,
            "deletes_domain_truth": False,
        },
    }
    receipt_path = _retention_root(resolved_quest_root) / f"{_artifact_slug(recorded_at)}.report_snapshot_retention.json"
    latest_path = _retention_root(resolved_quest_root) / "latest_report_snapshot_retention.json"
    _write_json(receipt_path, receipt)
    _write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)
    return receipt


def _restore_proof_archive_paths(quest_root: Path) -> list[Path]:
    root = (
        quest_root
        / "artifacts"
        / "runtime"
        / "runtime_storage_maintenance"
        / "restore_proof_archives"
        / "runtime_bucket_compaction"
    )
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.tar.gz") if path.is_file() and not path.is_symlink())


def _inspect_restore_archive(*, quest_root: Path, archive_path: Path, threshold_bytes: int) -> dict[str, Any]:
    size_bytes = archive_path.stat().st_size
    if size_bytes < threshold_bytes:
        return {"status": "below_threshold", "archive_path": str(archive_path), "bytes": size_bytes}
    manifest_path = archive_path.with_name(archive_path.name.removesuffix(".tar.gz") + ".manifest.json")
    restore_proof_path = archive_path.with_name(archive_path.name.removesuffix(".tar.gz") + ".restore_proof.json")
    if not manifest_path.is_file() or not restore_proof_path.is_file():
        return {
            "status": "blocked",
            "reason": "missing_manifest_or_restore_proof",
            "archive_path": str(archive_path),
            "manifest_path": str(manifest_path),
            "restore_proof_path": str(restore_proof_path),
        }
    restore_proof = _read_json_mapping(restore_proof_path)
    if restore_proof.get("status") != "verified":
        return {
            "status": "blocked",
            "reason": "restore_proof_not_verified",
            "archive_path": str(archive_path),
            "restore_proof_path": str(restore_proof_path),
        }
    observed_sha = _file_sha256(archive_path)
    expected_sha = str(restore_proof.get("archive_sha256") or "").strip()
    if expected_sha and observed_sha != expected_sha:
        return {
            "status": "blocked",
            "reason": "archive_sha256_mismatch",
            "archive_path": str(archive_path),
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
        }
    return {
        "status": "candidate",
        "archive_path": str(archive_path),
        "workspace_relative_archive_path": archive_path.relative_to(quest_root).as_posix(),
        "manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "bytes": size_bytes,
        "sha256": observed_sha,
    }


def _apply_archive_body_retention(
    *,
    archive_path: Path,
    quest_root: Path,
    cold_root: Path,
    inspection: Mapping[str, Any],
) -> dict[str, Any]:
    sha256 = str(inspection.get("sha256") or "")
    object_path = cold_root / "objects" / sha256[:2] / f"{sha256}.tar.gz"
    object_path.parent.mkdir(parents=True, exist_ok=True)
    size_before = archive_path.stat().st_size
    if object_path.exists():
        if _file_sha256(object_path) != sha256:
            return {
                "status": "blocked_cold_object_sha256_mismatch",
                "cold_object_path": str(object_path),
                "active_release_bytes": 0,
            }
        archive_path.unlink()
        _write_relative_symlink(target=object_path, link_path=archive_path)
        status = "deduped_to_existing_cold_object"
    else:
        shutil.move(str(archive_path), str(object_path))
        _write_relative_symlink(target=object_path, link_path=archive_path)
        status = "moved_to_cold_object"
    symlink_bytes = archive_path.lstat().st_size
    ref_path = archive_path.with_name(archive_path.name + ".cold_ref.json")
    cold_ref = {
        "surface_kind": "runtime_cold_archive_body_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "online_path_retained_as_symlink",
        "archive_path": str(archive_path),
        "cold_object_path": str(object_path),
        "sha256": sha256,
        "bytes": size_before,
        "restore_command": f"tar -xzf {archive_path} -C {quest_root / '.ds'}",
    }
    _write_json(ref_path, cold_ref)
    return {
        "status": status,
        "cold_object_path": str(object_path),
        "cold_ref_path": str(ref_path),
        "active_release_bytes": max(0, size_before - symlink_bytes - ref_path.stat().st_size),
        "source_archive_path_is_symlink": archive_path.is_symlink(),
    }


def _write_relative_symlink(*, target: Path, link_path: Path) -> None:
    relative_target = os.path.relpath(target, start=link_path.parent)
    link_path.symlink_to(relative_target)


def _report_snapshot_paths(reports_root: Path) -> list[Path]:
    if not reports_root.exists():
        return []
    return sorted(
        path
        for path in reports_root.rglob("*")
        if path.is_file() and path.suffix in {".json", ".md"} and not _is_latest_alias(path)
    )


def _retained_report_paths(*, reports_root: Path, keep_cutoff: datetime, daily_samples: int) -> set[Path]:
    retained: set[Path] = set()
    if not reports_root.exists():
        return retained
    retained.update(path for path in reports_root.rglob("latest.*") if path.is_file())
    grouped: dict[tuple[str, str, str], list[Path]] = defaultdict(list)
    for path in _report_snapshot_paths(reports_root):
        if _mtime_utc(path) >= keep_cutoff:
            retained.add(path)
            continue
        date_key = _report_date_key(path)
        family = path.parent.relative_to(reports_root).as_posix()
        grouped[(family, date_key, path.suffix)].append(path)
    for paths in grouped.values():
        for path in _bounded_samples(sorted(paths), daily_samples):
            retained.add(path)
    return retained


def _bounded_samples(paths: list[Path], count: int) -> list[Path]:
    if count <= 0 or not paths:
        return []
    if len(paths) <= count:
        return list(paths)
    if count == 1:
        return [paths[-1]]
    samples = [paths[0], paths[-1]]
    if count <= 2:
        return samples
    step = max(1, len(paths) // (count - 1))
    for index in range(step, len(paths) - 1, step):
        samples.append(paths[index])
        if len(samples) >= count:
            break
    return sorted(set(samples), key=paths.index)


def _report_date_key(path: Path) -> str:
    name = path.name
    if len(name) >= 10 and name[4] == "-" and name[7] == "-":
        return name[:10]
    return _mtime_utc(path).date().isoformat()


def _report_manifest(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    source_paths: Iterable[Path],
    keep_recent_days: int,
    daily_samples: int,
) -> dict[str, Any]:
    source_files = []
    for path in source_paths:
        source_files.append(
            {
                "path": path.relative_to(quest_root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
                "mtime": _mtime_utc(path).isoformat(),
            }
        )
    return {
        "surface_kind": "runtime_report_snapshot_retention_manifest",
        "schema_version": SCHEMA_VERSION,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "recorded_at": recorded_at,
        "keep_recent_days": int(keep_recent_days),
        "daily_samples": int(daily_samples),
        "source_file_count": len(source_files),
        "source_files": source_files,
    }


def _write_report_bundle(*, quest_root: Path, bundle_path: Path, source_paths: Iterable[Path]) -> None:
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path in source_paths:
            tar.add(path, arcname=path.relative_to(quest_root).as_posix(), recursive=False)


def _verify_report_bundle(*, bundle_path: Path, manifest: Mapping[str, Any], verified_at: str) -> dict[str, Any]:
    expected = {str(item["path"]): dict(item) for item in manifest.get("source_files", []) if isinstance(item, Mapping)}
    observed: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    try:
        with tarfile.open(bundle_path, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    errors.append({"path": member.name, "reason": "unsupported_member_type"})
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    errors.append({"path": member.name, "reason": "member_not_readable"})
                    continue
                observed[member.name] = {
                    "path": member.name,
                    "size_bytes": member.size,
                    "sha256": hashlib.sha256(extracted.read()).hexdigest(),
                }
    except tarfile.TarError as exc:
        errors.append({"path": str(bundle_path), "reason": "bundle_not_readable", "error": str(exc)})
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    mismatch = [
        path
        for path in sorted(set(expected) & set(observed))
        if int(expected[path].get("size_bytes") or 0) != int(observed[path].get("size_bytes") or 0)
        or str(expected[path].get("sha256") or "") != str(observed[path].get("sha256") or "")
    ]
    errors.extend({"path": path, "reason": "missing_from_bundle"} for path in missing)
    errors.extend({"path": path, "reason": "unexpected_bundle_member"} for path in extra)
    errors.extend({"path": path, "reason": "bundle_member_hash_or_size_mismatch"} for path in mismatch)
    return {
        "surface_kind": "runtime_report_snapshot_retention_restore_proof",
        "schema_version": SCHEMA_VERSION,
        "status": "verified" if not errors else "failed",
        "verified_at": verified_at,
        "bundle_path": str(bundle_path),
        "bundle_sha256": _file_sha256(bundle_path) if bundle_path.exists() else None,
        "source_file_count": len(expected),
        "verified_file_count": len(observed),
        "errors": errors,
    }


def _restore_proof_summary(proof: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not proof:
        return None
    return {
        "surface_kind": proof.get("surface_kind"),
        "status": proof.get("status"),
        "source_file_count": proof.get("source_file_count"),
        "verified_file_count": proof.get("verified_file_count"),
        "error_count": len(list(proof.get("errors") or [])),
    }


def _retention_root(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / "retention"


def _cold_store_root(*, quest_root: Path, quest_id: str, cold_store_root: Path | None) -> Path:
    if cold_store_root is not None:
        return Path(cold_store_root).expanduser().resolve() / _safe_artifact_id(quest_id)
    return quest_root.parent / "_cold_objects" / "runtime_restore_proof_archives" / _safe_artifact_id(quest_id)


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _mtime_utc(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC)


def _is_latest_alias(path: Path) -> bool:
    return path.name.startswith("latest.")


def _sample_entries(entries: Iterable[Mapping[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return [dict(entry) for entry in list(entries)[:limit]]


def _sample_values(values: Iterable[str], limit: int = 20) -> list[str]:
    return list(values)[:limit]


__all__ = [
    "ARCHIVE_RETENTION_SURFACE_KIND",
    "REPORT_RETENTION_SURFACE_KIND",
    "retain_report_snapshots",
    "retain_restore_proof_archive_bodies",
]
