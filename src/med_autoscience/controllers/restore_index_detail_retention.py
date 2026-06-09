from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "restore_index_detail_retention"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_DETAIL_KEYS = ("source_files", "verified_entries")


def run_restore_index_detail_retention(
    *,
    root: Path,
    apply: bool,
    cold_store_root: Path,
    min_mb: int = 1,
    max_files: int | None = None,
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    cold_root = _cold_store_root(root=resolved_root, cold_store_root=cold_store_root)
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    moved_count = 0
    actual_release_bytes = 0
    for json_path in _candidate_json_paths(resolved_root):
        inspection = _inspect_detail_json(json_path=json_path, threshold_bytes=threshold_bytes)
        if inspection.get("status") == "blocked":
            blockers.append(inspection)
            continue
        if inspection.get("status") != "candidate":
            continue
        if max_files is not None and len(candidates) >= max(0, int(max_files)):
            break
        if apply:
            applied = _apply_detail_retention(
                json_path=json_path,
                inspection=inspection,
                cold_root=cold_root,
                recorded_at=recorded_at,
            )
            inspection.update(applied)
            actual_release_bytes += int(applied.get("online_release_bytes") or 0)
            if applied.get("status") == "detail_moved_to_cold_object":
                moved_count += 1
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(inspection)
        candidates.append(inspection)
    status = (
        "applied"
        if apply and moved_count
        else "blocked"
        if apply and blockers
        else "planned"
        if candidates
        else "nothing_to_retain"
        if not blockers
        else "blocked"
    )
    receipt = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "root": str(resolved_root),
        "apply": bool(apply),
        "min_bytes": threshold_bytes,
        "max_files": max_files,
        "cold_store_root": str(cold_root),
        "candidate_count": len(candidates),
        "moved_count": moved_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "retains_status_counts_and_hashes_online": True,
        "mutation_policy": {
            "moves_large_detail_arrays": bool(apply),
            "keeps_original_json_path": True,
            "keeps_verified_status_online": True,
            "deletes_archive_body": False,
            "deletes_domain_truth": False,
        },
        "candidate_samples": _sample_entries(candidates),
        "blocker_samples": _sample_entries(blockers),
    }
    receipt_root = _receipt_root(resolved_root)
    receipt_path = receipt_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = receipt_root / "latest.json"
    write_json(receipt_path, receipt)
    write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)
    return receipt


def _candidate_json_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if _has_restore_index_detail_name(root) else []
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if _has_restore_index_detail_name(path))


def _has_restore_index_detail_name(path: Path) -> bool:
    name = path.name
    return name.endswith(".manifest.json") or name.endswith(".restore_proof.json") or name in {
        "source_manifest.json",
        "restore_proof.json",
    }


def _inspect_detail_json(*, json_path: Path, threshold_bytes: int) -> dict[str, Any]:
    size_bytes = json_path.stat().st_size
    if size_bytes < threshold_bytes:
        return {"status": "below_threshold", "json_path": str(json_path), "bytes": size_bytes}
    payload = _read_json_mapping(json_path)
    if not payload:
        return {"status": "blocked", "reason": "json_not_readable_or_not_object", "json_path": str(json_path)}
    detail_counts = {key: len(value) for key, value in _detail_arrays(payload).items()}
    if not detail_counts:
        return {"status": "below_threshold_no_detail_arrays", "json_path": str(json_path), "bytes": size_bytes}
    if str(payload.get("status") or "verified") not in {"verified", ""} and json_path.name.endswith(
        "restore_proof.json"
    ):
        return {
            "status": "blocked",
            "reason": "restore_proof_not_verified",
            "json_path": str(json_path),
            "restore_proof_status": payload.get("status"),
        }
    detail_payload = _detail_payload(payload)
    detail_bytes = _json_bytes(detail_payload)
    return {
        "status": "candidate",
        "json_path": str(json_path),
        "bytes": size_bytes,
        "detail_bytes": len(detail_bytes),
        "detail_sha256": hashlib.sha256(detail_bytes).hexdigest(),
        "detail_counts": detail_counts,
        "surface_kind": payload.get("surface_kind"),
    }


def _apply_detail_retention(
    *,
    json_path: Path,
    inspection: Mapping[str, Any],
    cold_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    payload = _read_json_mapping(json_path)
    detail_payload = _detail_payload(payload)
    detail_bytes = _json_bytes(detail_payload)
    detail_sha256 = hashlib.sha256(detail_bytes).hexdigest()
    if detail_sha256 != str(inspection.get("detail_sha256") or ""):
        return {"status": "blocked_detail_sha256_changed", "online_release_bytes": 0}
    object_path = cold_root / "objects" / detail_sha256[:2] / f"{detail_sha256}.detail.json"
    object_path.parent.mkdir(parents=True, exist_ok=True)
    if object_path.exists():
        if _sha256(object_path) != detail_sha256:
            return {
                "status": "blocked_cold_detail_sha256_mismatch",
                "cold_object_path": str(object_path),
                "online_release_bytes": 0,
            }
    else:
        object_path.write_bytes(detail_bytes)
    original_bytes = json_path.stat().st_size
    detail_ref_path = json_path.with_name(json_path.name + ".detail_ref.json")
    slim_payload = _slim_payload(
        payload=payload,
        json_path=json_path,
        cold_object_path=object_path,
        detail_sha256=detail_sha256,
        detail_bytes=len(detail_bytes),
        recorded_at=recorded_at,
    )
    write_json(json_path, slim_payload)
    detail_ref = {
        "surface_kind": "restore_index_detail_cold_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "detail_body_moved_to_cold_object",
        "recorded_at": recorded_at,
        "json_path": str(json_path),
        "cold_object_path": str(object_path),
        "detail_sha256": detail_sha256,
        "detail_bytes": len(detail_bytes),
        "detail_counts": dict(inspection.get("detail_counts") or {}),
        "restore_command": f"cp {object_path} <detail-json-destination>",
        "body_included": False,
    }
    write_json(detail_ref_path, detail_ref)
    online_after = json_path.stat().st_size + detail_ref_path.stat().st_size
    return {
        "status": "detail_moved_to_cold_object",
        "cold_object_path": str(object_path),
        "detail_ref_path": str(detail_ref_path),
        "online_release_bytes": max(0, original_bytes - online_after),
    }


def _slim_payload(
    *,
    payload: Mapping[str, Any],
    json_path: Path,
    cold_object_path: Path,
    detail_sha256: str,
    detail_bytes: int,
    recorded_at: str,
) -> dict[str, Any]:
    slim = dict(payload)
    detail_counts: dict[str, int] = {}
    for key in _DETAIL_KEYS:
        value = slim.pop(key, None)
        if isinstance(value, list):
            detail_counts[key] = len(value)
    slim["detail_retention"] = {
        "surface_kind": "restore_index_detail_retention_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "detail_body_moved_to_cold_object",
        "recorded_at": recorded_at,
        "json_path": str(json_path),
        "cold_object_path": str(cold_object_path),
        "detail_sha256": detail_sha256,
        "detail_bytes": detail_bytes,
        "detail_counts": detail_counts,
        "body_included": False,
    }
    slim["body_included"] = False
    return slim


def _detail_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"detail": {key: value for key, value in _detail_arrays(payload).items()}}


def _detail_arrays(payload: Mapping[str, Any]) -> dict[str, list[Any]]:
    return {key: value for key in _DETAIL_KEYS if isinstance((value := payload.get(key)), list)}


def _cold_store_root(*, root: Path, cold_store_root: Path) -> Path:
    return Path(cold_store_root).expanduser().resolve() / safe_artifact_id(root.name) / "restore_index_detail"


def _receipt_root(root: Path) -> Path:
    base = root if root.is_dir() else root.parent
    return base / "retention" / "restore_index_detail"


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_slug(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _sample_entries(entries: Iterable[Mapping[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return [dict(entry) for entry in list(entries)[:limit]]


__all__ = ["run_restore_index_detail_retention"]
