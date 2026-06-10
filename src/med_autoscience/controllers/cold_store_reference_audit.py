from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    write_json,
)


SURFACE_KIND = "cold_store_reference_audit"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_REF_KEYS = {"cold_object_path", "cold_archive_path", "source_manifest_path", "restore_proof_path"}
_META_SUFFIXES = (".manifest.json", ".restore_proof.json", ".cold_ref.json", ".detail_ref.json")


def run_cold_store_reference_audit(
    *,
    root: Path,
    reference_roots: Sequence[Path],
    apply: bool,
    min_mb: int = 16,
    max_objects: int | None = None,
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    resolved_reference_roots = tuple(Path(item).expanduser().resolve() for item in reference_roots) or (resolved_root,)
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    refs, ref_file_count, unreadable_json_count = _collect_cold_refs(
        cold_root=resolved_root,
        reference_roots=resolved_reference_roots,
    )
    candidates = [
        candidate
        for candidate in _orphan_candidates(root=resolved_root, refs=refs)
        if int(candidate["bytes"]) >= threshold_bytes
    ]
    if max_objects is not None:
        candidates = candidates[: max(0, int(max_objects))]

    deleted_count = 0
    actual_release_bytes = 0
    blockers: list[dict[str, Any]] = []
    if apply:
        for candidate in candidates:
            applied = _delete_candidate(candidate)
            candidate.update(applied)
            if applied.get("status") == "deleted_unreferenced_cold_object":
                deleted_count += 1
                actual_release_bytes += int(applied.get("release_bytes") or 0)
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(candidate)

    status = (
        "blocked"
        if apply and blockers
        else "applied"
        if apply and deleted_count
        else "planned"
        if candidates
        else "nothing_to_collect"
    )
    body_count, body_bytes = _body_object_totals(resolved_root)
    receipt = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "root": str(resolved_root),
        "reference_roots": [str(item) for item in resolved_reference_roots],
        "apply": bool(apply),
        "min_bytes": threshold_bytes,
        "max_objects": max_objects,
        "body_object_count": body_count,
        "body_object_bytes": body_bytes,
        "referenced_path_count": len(refs),
        "ref_file_count": ref_file_count,
        "unreadable_json_count": unreadable_json_count,
        "orphan_candidate_count": len(candidates),
        "deleted_count": deleted_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "mutation_policy": {
            "deletes_only_unreferenced_cold_objects": bool(apply),
            "rewrites_cold_refs_or_restore_commands": False,
            "deletes_online_workspace_files": False,
            "deletes_domain_truth": False,
            "deletes_data_assets": False,
        },
        "candidate_samples": _sample_entries(candidates),
        "blocker_samples": _sample_entries(blockers),
    }
    receipt_root = resolved_root / ".retention" / SURFACE_KIND
    receipt_path = receipt_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = receipt_root / "latest.json"
    write_json(receipt_path, receipt)
    write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)
    return receipt


def _collect_cold_refs(*, cold_root: Path, reference_roots: Sequence[Path]) -> tuple[set[str], int, int]:
    refs: set[str] = set()
    ref_file_count = 0
    unreadable_json_count = 0
    for reference_root in reference_roots:
        if not reference_root.exists():
            continue
        paths = [reference_root] if reference_root.is_file() else sorted(reference_root.rglob("*.json"))
        for path in paths:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                unreadable_json_count += 1
                continue
            before = len(refs)
            _collect_refs_from_payload(payload=payload, refs=refs, cold_root=cold_root)
            if len(refs) > before:
                ref_file_count += 1
    return refs, ref_file_count, unreadable_json_count


def _collect_refs_from_payload(*, payload: Any, refs: set[str], cold_root: Path) -> None:
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, value in item.items():
                if key in _REF_KEYS and isinstance(value, str):
                    candidate = Path(value).expanduser()
                    if candidate.is_absolute():
                        try:
                            resolved = str(candidate.resolve())
                        except OSError:
                            resolved = str(candidate)
                        if resolved == str(cold_root) or resolved.startswith(f"{cold_root}/"):
                            refs.add(resolved)
                elif isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(item, list):
            stack.extend(value for value in item if isinstance(value, (dict, list)))


def _orphan_candidates(*, root: Path, refs: set[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in _iter_cold_object_files(root):
        try:
            resolved = str(path.resolve())
            size_bytes = path.stat().st_size
        except OSError:
            continue
        if resolved in refs:
            continue
        candidates.append(
            {
                "status": "candidate",
                "path": str(path),
                "bytes": size_bytes,
                "sha256": _sha256(path),
                "reason": "not_referenced_by_any_scanned_cold_ref",
            }
        )
    return sorted(candidates, key=lambda item: int(item["bytes"]), reverse=True)


def _delete_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    path = Path(str(candidate["path"]))
    expected_sha = str(candidate.get("sha256") or "")
    if not path.is_file():
        return {"status": "blocked_missing_cold_object", "release_bytes": 0}
    observed_sha = _sha256(path)
    if observed_sha != expected_sha:
        return {
            "status": "blocked_sha256_mismatch",
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
            "release_bytes": 0,
        }
    release_bytes = path.stat().st_size
    path.unlink()
    return {"status": "deleted_unreferenced_cold_object", "release_bytes": release_bytes}


def _body_object_totals(root: Path) -> tuple[int, int]:
    count = 0
    total = 0
    for path in _iter_cold_object_files(root):
        try:
            total += path.stat().st_size
            count += 1
        except OSError:
            continue
    return count, total


def _iter_cold_object_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        parts = path.parts
        if len(parts) < 3 or parts[-3] != "objects":
            continue
        if path.name.endswith(_META_SUFFIXES):
            continue
        yield path


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


__all__ = ["run_cold_store_reference_audit"]
