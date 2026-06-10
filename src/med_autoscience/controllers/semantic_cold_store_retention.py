from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "semantic_cold_store_retention"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_REF_KEYS = {"cold_object_path", "cold_archive_path"}
_RETIRED_SURFACE_KIND = "semantic_cold_store_retention_ref"
_KNOWN_REF_SURFACE_KINDS = {
    "historical_body_cold_ref",
    "historical_directory_cold_ref",
    "legacy_ds_cold_archive_body_ref",
    "legacy_ds_archive_cold_ref",
}


def run_semantic_cold_store_retention(
    *,
    root: Path,
    reference_roots: Sequence[Path],
    apply: bool,
    retire_exact_raw_restore: bool,
    min_mb: int = 16,
    max_objects: int | None = None,
    reference_file_lists: Sequence[Path] = (),
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    resolved_reference_roots = tuple(Path(item).expanduser().resolve() for item in reference_roots) or (resolved_root,)
    resolved_reference_file_lists = tuple(Path(item).expanduser().resolve() for item in reference_file_lists)
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    ref_index, ref_file_count, unreadable_json_count = _collect_semantic_refs(
        cold_root=resolved_root,
        reference_roots=resolved_reference_roots,
        reference_file_lists=resolved_reference_file_lists,
    )
    inspected_candidates = [
        candidate
        for candidate in _candidate_objects(root=resolved_root, ref_index=ref_index)
        if int(candidate["bytes"]) >= threshold_bytes
    ]
    candidates = [candidate for candidate in inspected_candidates if candidate.get("status") == "candidate"]
    blockers = [candidate for candidate in inspected_candidates if str(candidate.get("status") or "").startswith("blocked")]
    if max_objects is not None:
        candidates = candidates[: max(0, int(max_objects))]

    replaced_count = 0
    actual_release_bytes = 0
    capsule_root = resolved_root / ".retention" / SURFACE_KIND / "capsules" / _artifact_slug(recorded_at)
    if apply:
        if not retire_exact_raw_restore:
            blockers.append(
                {
                    "status": "blocked_missing_explicit_policy_flag",
                    "reason": "--retire-exact-raw-restore is required with --apply",
                }
            )
        else:
            for candidate in candidates:
                applied = _apply_semantic_replacement(
                    candidate=candidate,
                    capsule_root=capsule_root,
                    recorded_at=recorded_at,
                )
                candidate.update(applied)
                if applied.get("status") == "raw_body_replaced_by_semantic_ref":
                    replaced_count += 1
                    actual_release_bytes += int(applied.get("release_bytes") or 0)
                elif str(applied.get("status") or "").startswith("blocked"):
                    blockers.append(candidate)

    status = (
        "blocked"
        if apply and blockers
        else "applied"
        if apply and replaced_count
        else "planned_with_blockers"
        if candidates and blockers
        else "planned"
        if candidates
        else "nothing_to_retain"
    )
    receipt = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "root": str(resolved_root),
        "reference_roots": [str(item) for item in resolved_reference_roots],
        "reference_file_lists": [str(item) for item in resolved_reference_file_lists],
        "apply": bool(apply),
        "retire_exact_raw_restore": bool(retire_exact_raw_restore),
        "min_bytes": threshold_bytes,
        "max_objects": max_objects,
        "ref_file_count": ref_file_count,
        "unreadable_json_count": unreadable_json_count,
        "candidate_count": len(candidates),
        "replaced_count": replaced_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "restore_policy": {
            "exact_legacy_raw_restore_retired": bool(apply and retire_exact_raw_restore and replaced_count),
            "byte_for_byte_restore_of_legacy_raw_body": False,
            "preserves_original_sha256": True,
            "preserves_original_bytes": True,
            "preserves_source_ref_paths": True,
            "preserves_semantic_capsule": True,
            "reproducibility_basis": "manifest_hash_digest_current_mas_truth_refs",
        },
        "mutation_policy": {
            "rewrites_cold_object_body_to_semantic_ref": bool(apply and retire_exact_raw_restore),
            "deletes_online_workspace_files": False,
            "deletes_domain_truth": False,
            "deletes_data_assets": False,
            "deletes_currentness_surfaces": False,
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


def _collect_semantic_refs(
    *,
    cold_root: Path,
    reference_roots: Sequence[Path],
    reference_file_lists: Sequence[Path],
) -> tuple[dict[str, list[dict[str, Any]]], int, int]:
    ref_index: dict[str, list[dict[str, Any]]] = {}
    ref_file_count = 0
    unreadable_json_count = 0
    for path in _iter_reference_files(reference_roots=reference_roots, reference_file_lists=reference_file_lists):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            unreadable_json_count += 1
            continue
        before = sum(len(items) for items in ref_index.values())
        _collect_refs_from_payload(payload=payload, ref_index=ref_index, cold_root=cold_root, ref_file=path)
        if sum(len(items) for items in ref_index.values()) > before:
            ref_file_count += 1
    return ref_index, ref_file_count, unreadable_json_count


def _iter_reference_files(*, reference_roots: Sequence[Path], reference_file_lists: Sequence[Path]) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for reference_root in reference_roots:
        if not reference_root.exists():
            continue
        candidates = [reference_root] if reference_root.is_file() else sorted(reference_root.rglob("*.json"))
        for candidate in candidates:
            _append_unique_path(paths=paths, seen=seen, path=candidate)
    for list_path in reference_file_lists:
        try:
            lines = list_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            _append_unique_path(paths=paths, seen=seen, path=list_path)
            continue
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            candidate = Path(stripped).expanduser()
            if not candidate.is_absolute():
                candidate = list_path.parent / candidate
            _append_unique_path(paths=paths, seen=seen, path=candidate)
    return paths


def _append_unique_path(*, paths: list[Path], seen: set[str], path: Path) -> None:
    key = str(path.expanduser().resolve()) if path.exists() else str(path.expanduser())
    if key in seen:
        return
    seen.add(key)
    paths.append(path)


def _collect_refs_from_payload(
    *,
    payload: Any,
    ref_index: dict[str, list[dict[str, Any]]],
    cold_root: Path,
    ref_file: Path,
) -> None:
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            surface_kind = str(item.get("surface_kind") or "")
            for key, value in item.items():
                if key in _REF_KEYS and isinstance(value, str):
                    candidate = Path(value).expanduser()
                    if not candidate.is_absolute():
                        continue
                    try:
                        resolved = str(candidate.resolve())
                    except OSError:
                        resolved = str(candidate)
                    if resolved == str(cold_root) or not resolved.startswith(f"{cold_root}/"):
                        continue
                    if surface_kind and surface_kind not in _KNOWN_REF_SURFACE_KINDS:
                        continue
                    original_sha = item.get("original_sha256") or item.get("sha256")
                    original_bytes = item.get("original_bytes") or item.get("bytes")
                    ref_index.setdefault(resolved, []).append(
                        {
                            "ref_file": str(ref_file),
                            "ref_key": key,
                            "surface_kind": surface_kind or "unknown_cold_ref",
                            "original_sha256": original_sha,
                            "sha256": original_sha,
                            "original_bytes": original_bytes,
                            "bytes": original_bytes,
                            "restore_command": item.get("restore_command"),
                            "workspace_relative_path": item.get("workspace_relative_path"),
                        }
                    )
                elif isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(item, list):
            stack.extend(value for value in item if isinstance(value, (dict, list)))


def _candidate_objects(*, root: Path, ref_index: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for object_path, refs in ref_index.items():
        path = Path(object_path)
        if not path.is_file() or path.is_symlink():
            continue
        if _is_retired_ref_object(path):
            continue
        try:
            size_bytes = path.stat().st_size
        except OSError:
            continue
        ref_sha = _first_ref_value(refs, "original_sha256")
        ref_bytes = _first_ref_value(refs, "original_bytes")
        sha256 = str(ref_sha or "")
        if not sha256:
            candidates.append(
                {
                    "status": "blocked_missing_ref_sha256",
                    "path": str(path),
                    "cold_store_relative_path": path.relative_to(root).as_posix(),
                    "bytes": size_bytes,
                    "observed_size_bytes": size_bytes,
                    "reference_count": len(refs),
                    "reference_samples": _sample_entries(refs, limit=5),
                    "semantic_retention_mode": "retire_exact_raw_restore",
                }
            )
            continue
        planned_bytes = _int_or_none(ref_bytes) or size_bytes
        candidates.append(
            {
                "status": "candidate",
                "path": str(path),
                "cold_store_relative_path": path.relative_to(root).as_posix(),
                "bytes": planned_bytes,
                "observed_size_bytes": size_bytes,
                "sha256": sha256,
                "reference_count": len(refs),
                "reference_samples": _sample_entries(refs, limit=5),
                "semantic_retention_mode": "retire_exact_raw_restore",
            }
        )
    return sorted(candidates, key=lambda item: int(item["bytes"]), reverse=True)


def _is_retired_ref_object(path: Path) -> bool:
    try:
        if path.stat().st_size > 1024 * 1024:
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and payload.get("surface_kind") == _RETIRED_SURFACE_KIND


def _first_ref_value(refs: Sequence[Mapping[str, Any]], key: str) -> Any:
    for ref in refs:
        value = ref.get(key)
        if value not in (None, ""):
            return value
    return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _apply_semantic_replacement(
    *,
    candidate: Mapping[str, Any],
    capsule_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    object_path = Path(str(candidate["path"]))
    expected_sha = str(candidate.get("sha256") or "")
    if not object_path.is_file() or object_path.is_symlink():
        return {"status": "blocked_missing_cold_object", "release_bytes": 0}
    observed_sha = _sha256(object_path)
    if observed_sha != expected_sha:
        return {
            "status": "blocked_sha256_mismatch",
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
            "release_bytes": 0,
        }
    original_bytes = object_path.stat().st_size
    capsule = _semantic_capsule(candidate=candidate, object_path=object_path, recorded_at=recorded_at)
    capsule_path = capsule_root / f"{safe_artifact_id(object_path.stem)[:80]}-{observed_sha[:12]}.json"
    write_json(capsule_path, capsule)
    replacement = {
        "surface_kind": _RETIRED_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "exact_raw_body_retired",
        "recorded_at": recorded_at,
        "cold_object_path": str(object_path),
        "semantic_capsule_path": str(capsule_path),
        "original_sha256": observed_sha,
        "original_bytes": original_bytes,
        "body_included": False,
        "restore_policy": {
            "byte_for_byte_restore_of_legacy_raw_body": False,
            "restore_legacy_semantics_from_capsule": True,
            "reproducibility_basis": "source_ref_paths_original_hashes_log_digest_current_mas_truth_refs",
        },
    }
    object_path.write_text(json.dumps(replacement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ref_update = _update_reference_files(candidate=candidate, recorded_at=recorded_at, capsule_path=capsule_path)
    replacement_bytes = object_path.stat().st_size
    return {
        "status": "raw_body_replaced_by_semantic_ref",
        "semantic_capsule_path": str(capsule_path),
        "reference_update": ref_update,
        "replacement_bytes": replacement_bytes,
        "release_bytes": max(0, original_bytes - replacement_bytes),
    }


def _update_reference_files(
    *,
    candidate: Mapping[str, Any],
    recorded_at: str,
    capsule_path: Path,
) -> dict[str, Any]:
    updated = 0
    blocked: list[dict[str, Any]] = []
    for ref in _sample_entries(candidate.get("reference_samples") or (), limit=100000):
        ref_file = Path(str(ref.get("ref_file") or ""))
        if not ref_file.is_file():
            blocked.append({"ref_file": str(ref_file), "reason": "missing_ref_file"})
            continue
        try:
            payload = json.loads(ref_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            blocked.append({"ref_file": str(ref_file), "reason": "unreadable_ref_file", "error": str(exc)})
            continue
        if not isinstance(payload, dict):
            blocked.append({"ref_file": str(ref_file), "reason": "non_object_ref_payload"})
            continue
        payload["semantic_restore_policy"] = {
            "status": "exact_raw_restore_retired",
            "recorded_at": recorded_at,
            "semantic_capsule_path": str(capsule_path),
            "byte_for_byte_restore_of_legacy_raw_body": False,
            "original_sha256": candidate.get("sha256"),
            "original_bytes": candidate.get("bytes"),
            "body_included": False,
        }
        payload["restore_command"] = None
        write_json(ref_file, payload)
        updated += 1
    return {"updated_ref_file_count": updated, "blocked_ref_file_count": len(blocked), "blockers": blocked[:20]}


def _semantic_capsule(*, candidate: Mapping[str, Any], object_path: Path, recorded_at: str) -> dict[str, Any]:
    head, tail = _head_tail_hex(object_path)
    return {
        "surface_kind": "semantic_cold_store_capsule",
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "recorded_at": recorded_at,
        "source_cold_object_path": str(object_path),
        "source_sha256": candidate.get("sha256"),
        "source_bytes": candidate.get("bytes"),
        "reference_count": candidate.get("reference_count"),
        "reference_samples": candidate.get("reference_samples"),
        "byte_digest": {
            "sha256": candidate.get("sha256"),
            "bytes": candidate.get("bytes"),
            "head_hex": head,
            "tail_hex": tail,
        },
        "current_truth_refs": {
            "domain_truth_mutated": False,
            "publication_eval_mutated": False,
            "controller_decisions_mutated": False,
            "owner_receipts_mutated": False,
        },
        "restore_policy": {
            "byte_for_byte_restore_of_legacy_raw_body": False,
            "legacy_raw_body_retired_by_explicit_policy": True,
            "semantic_replay_requires_current_mas_truth_refs": True,
        },
        "body_included": False,
    }


def _head_tail_hex(path: Path, limit: int = 4096) -> tuple[str, str]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        head = handle.read(limit)
        if size > limit:
            handle.seek(max(0, size - limit))
            tail = handle.read(limit)
        else:
            tail = head
    return head.hex(), tail.hex()


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


__all__ = ["run_semantic_cold_store_retention"]
