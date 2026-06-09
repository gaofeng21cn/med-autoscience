from __future__ import annotations

from collections import deque
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
    safe_artifact_id as _safe_artifact_id,
    write_json as _write_json,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.legacy_executor_home import (
    migrate_legacy_codex_homes,
)


SCHEMA_VERSION = 1
CAPSULE_SURFACE_KIND = "runtime_attempt_evidence_capsule"
SEMANTIC_RETENTION_SURFACE_KIND = "runtime_semantic_process_retention"
SEMANTIC_REF_SURFACE_KIND = "runtime_semantic_process_ref"
_SUCCESS_STATUSES = frozenset({"completed", "complete", "success", "succeeded", "done", "ok"})
_FAILED_STATUSES = frozenset({"failed", "failure", "error", "errored", "crashed", "timeout", "timed_out"})
_METADATA_FILENAMES = ("attempt.json", "metadata.json", "run.json", "receipt.json")
_LOG_SUFFIXES = frozenset({".log", ".out", ".err"})
_LOG_NAME_TOKENS = ("stdout", "stderr", "console", "terminal", "events", "trace", "transcript")


def materialize_attempt_evidence_capsules(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    semantic_process_retention: bool = False,
    semantic_process_retention_apply: bool = False,
    semantic_process_retention_apply_allowed: bool = False,
    semantic_retention_max_log_bytes: int = 256 * 1024,
    semantic_retention_max_raw_bytes: int = 1024 * 1024,
    semantic_retention_keep_failed_raw: bool = True,
    semantic_retention_max_files: int | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    attempt_records = [
        _write_attempt_capsule(
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            attempt_root=attempt_root,
            recorded_at=recorded_at,
        )
        for attempt_root in _attempt_roots(resolved_quest_root)
    ]
    capsule_summary = _write_capsule_latest(
        quest_root=resolved_quest_root,
        quest_id=quest_id,
        recorded_at=recorded_at,
        attempt_records=attempt_records,
    )
    result: dict[str, Any] = {"attempt_evidence_capsules": capsule_summary}
    if semantic_process_retention:
        result["semantic_process_retention"] = _apply_semantic_process_retention(
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            attempt_records=attempt_records,
            apply=semantic_process_retention_apply,
            apply_allowed=semantic_process_retention_apply_allowed,
            max_log_bytes=semantic_retention_max_log_bytes,
            max_raw_bytes=semantic_retention_max_raw_bytes,
            keep_failed_raw=semantic_retention_keep_failed_raw,
            max_files=semantic_retention_max_files,
        )
        result["legacy_codex_homes_retention"] = migrate_legacy_codex_homes(
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            apply=semantic_process_retention_apply,
            apply_allowed=semantic_process_retention_apply_allowed,
        )
    return result


def _attempt_roots(quest_root: Path) -> list[Path]:
    runs_root = quest_root / ".ds" / "runs"
    if not runs_root.exists():
        return []
    return sorted(path for path in runs_root.iterdir() if path.is_dir())


def _write_attempt_capsule(
    *,
    quest_root: Path,
    quest_id: str,
    attempt_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    metadata_path, metadata = _read_attempt_metadata(attempt_root)
    attempt_id = str(metadata.get("attempt_id") or metadata.get("run_id") or attempt_root.name)
    attempt_status = _attempt_status(metadata)
    capsule_root = _capsule_root(quest_root, attempt_id)
    replay_manifest = _replay_manifest(
        quest_root=quest_root,
        attempt_root=attempt_root,
        metadata_path=metadata_path,
        metadata=metadata,
    )
    input_manifest = _declared_and_directory_manifest(
        quest_root=quest_root,
        attempt_root=attempt_root,
        declared_values=metadata.get("inputs"),
        directory_name="inputs",
    )
    output_manifest = _declared_and_directory_manifest(
        quest_root=quest_root,
        attempt_root=attempt_root,
        declared_values=metadata.get("outputs"),
        directory_name="outputs",
    )
    log_digest = _log_digest(quest_root=quest_root, attempt_root=attempt_root)
    retention_receipt = {
        "surface_kind": SEMANTIC_RETENTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "not_requested",
        "quest_id": quest_id,
        "attempt_id": attempt_id,
        "recorded_at": recorded_at,
        "body_included": False,
    }
    replay_path = capsule_root / "replay_manifest.json"
    input_path = capsule_root / "input_manifest.json"
    output_path = capsule_root / "output_manifest.json"
    log_digest_path = capsule_root / "log_digest.json"
    retention_receipt_path = capsule_root / "retention_receipt.json"
    capsule_path = capsule_root / "capsule.json"
    _write_json(replay_path, replay_manifest)
    _write_json(input_path, input_manifest)
    _write_json(output_path, output_manifest)
    _write_json(log_digest_path, log_digest)
    _write_json(retention_receipt_path, retention_receipt)
    capsule = {
        "surface_kind": CAPSULE_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "attempt_id": attempt_id,
        "source_kind": "legacy_ds_intake",
        "legacy_attempt_root": str(attempt_root),
        "legacy_attempt_root_relpath": _relpath(attempt_root, quest_root),
        "attempt_status": attempt_status,
        "recorded_at": recorded_at,
        "body_included": False,
        "raw_body_policy": {
            "stores_full_raw_body": False,
            "uses_manifest_hashes": True,
            "semantic_process_retention_supported": True,
            "failed_raw_default": "retain",
            "legacy_ds_long_term_read_allowed": False,
        },
        "replay_manifest": replay_manifest,
        "input_manifest": _manifest_summary(input_manifest),
        "output_manifest": _manifest_summary(output_manifest),
        "log_digest": log_digest,
        "replay_manifest_path": _relpath(replay_path, quest_root),
        "input_manifest_path": _relpath(input_path, quest_root),
        "output_manifest_path": _relpath(output_path, quest_root),
        "log_digest_path": _relpath(log_digest_path, quest_root),
        "retention_receipt_path": _relpath(retention_receipt_path, quest_root),
    }
    _write_json(capsule_path, capsule)
    return {
        "attempt_id": attempt_id,
        "attempt_status": attempt_status,
        "legacy_attempt_root": str(attempt_root),
        "legacy_attempt_root_relpath": _relpath(attempt_root, quest_root),
        "capsule_path": _relpath(capsule_path, quest_root),
        "retention_receipt_path": _relpath(retention_receipt_path, quest_root),
        "semantic_ref_path": _relpath(capsule_root / "semantic_process_ref.json", quest_root),
        "log_files": log_digest["files"],
        "raw_bytes": _directory_size_bytes(attempt_root),
    }


def _write_capsule_latest(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    attempt_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    capsule_refs = [
        {
            "attempt_id": str(record.get("attempt_id") or ""),
            "attempt_status": record.get("attempt_status"),
            "capsule_path": str(record.get("capsule_path") or ""),
            "retention_receipt_path": str(record.get("retention_receipt_path") or ""),
        }
        for record in attempt_records
    ]
    summary = {
        "surface_kind": "runtime_attempt_evidence_capsule_index",
        "schema_version": SCHEMA_VERSION,
        "status": "planned" if capsule_refs else "nothing_to_capsule",
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "recorded_at": recorded_at,
        "capsule_count": len(capsule_refs),
        "capsule_refs": capsule_refs,
        "body_included": False,
    }
    latest_path = _capsules_root(quest_root) / "latest.json"
    _write_json(latest_path, summary)
    summary["latest_capsule_index_path"] = _relpath(latest_path, quest_root)
    return summary


def _apply_semantic_process_retention(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    attempt_records: list[Mapping[str, Any]],
    apply: bool,
    apply_allowed: bool,
    max_log_bytes: int,
    max_raw_bytes: int,
    keep_failed_raw: bool,
    max_files: int | None,
) -> dict[str, Any]:
    if apply and not apply_allowed:
        summary = {
            "surface_kind": SEMANTIC_RETENTION_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "blocked_storage_maintenance_not_maintained",
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "recorded_at": recorded_at,
            "apply": True,
            "actual_release_bytes": 0,
            "candidate_count": 0,
            "applied_count": 0,
            "skipped_failed_raw_count": 0,
            "body_included": False,
        }
        return _write_semantic_latest(quest_root=quest_root, summary=summary)

    max_attempt_count = None if max_files is None else max(0, int(max_files))
    remaining = max_attempt_count
    candidates: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    skipped_failed_raw_count = 0
    skipped_unknown_raw_count = 0
    actual_release_bytes = 0
    for record in attempt_records:
        status_kind = _status_kind(record.get("attempt_status"))
        oversized_logs = _oversized_logs(
            record=record,
            max_log_bytes=max(1, int(max_log_bytes)),
            max_raw_bytes=max(1, int(max_raw_bytes)),
        )
        has_candidate = bool(oversized_logs)
        if status_kind == "failed" and keep_failed_raw:
            skipped_failed_raw_count += 1 if has_candidate else 0
            _write_attempt_retention_receipt(
                quest_root=quest_root,
                record=record,
                recorded_at=recorded_at,
                status="skipped_failed_raw_retained",
                apply=apply,
                candidates=[],
                applied=[],
                actual_release_bytes=0,
            )
            continue
        if status_kind != "success":
            skipped_unknown_raw_count += 1 if has_candidate else 0
            _write_attempt_retention_receipt(
                quest_root=quest_root,
                record=record,
                recorded_at=recorded_at,
                status="skipped_non_success_status",
                apply=apply,
                candidates=[],
                applied=[],
                actual_release_bytes=0,
            )
            continue
        if not has_candidate:
            selected_logs: list[dict[str, Any]] = []
        elif remaining is None or remaining > 0:
            selected_logs = oversized_logs
            if remaining is not None:
                remaining -= 1
            candidates.append(_attempt_candidate(record=record, selected_logs=selected_logs))
        else:
            selected_logs = []
        attempt_applied: list[dict[str, Any]] = []
        attempt_release_bytes = 0
        if apply and selected_logs:
            applied_entry = _migrate_success_attempt(
                quest_root=quest_root,
                quest_id=quest_id,
                record=record,
                log_entries=selected_logs,
                recorded_at=recorded_at,
            )
            applied.append(applied_entry)
            attempt_applied.append(applied_entry)
            attempt_release_bytes += int(applied_entry.get("released_bytes") or 0)
        actual_release_bytes += attempt_release_bytes
        _write_attempt_retention_receipt(
            quest_root=quest_root,
            record=record,
            recorded_at=recorded_at,
            status="applied" if attempt_applied else "planned" if selected_logs else "nothing_to_retain",
            apply=apply,
            candidates=selected_logs,
            applied=attempt_applied,
            actual_release_bytes=attempt_release_bytes,
        )

    status = (
        "applied"
        if apply and applied
        else "planned"
        if candidates
        else "nothing_to_retain"
    )
    summary = {
        "surface_kind": SEMANTIC_RETENTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "recorded_at": recorded_at,
        "apply": bool(apply),
        "max_log_bytes": max(1, int(max_log_bytes)),
        "max_raw_bytes": max(1, int(max_raw_bytes)),
        "keep_failed_raw": bool(keep_failed_raw),
        "max_attempts": max_attempt_count,
        "candidate_count": len(candidates),
        "applied_count": len(applied),
        "skipped_failed_raw_count": skipped_failed_raw_count,
        "skipped_unknown_raw_count": skipped_unknown_raw_count,
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "mutation_policy": {
            "migrates_success_legacy_ds_runs_to_canonical_attempt_evidence": bool(apply),
            "archives_legacy_attempt_root_before_removal": bool(apply),
            "keeps_failed_raw_by_default": bool(keep_failed_raw),
            "deletes_domain_truth": False,
            "deletes_latest_aliases": False,
            "deletes_owner_receipts_or_typed_blockers": False,
            "legacy_ds_long_term_read_allowed": False,
        },
        "candidate_samples": _sample_entries(candidates),
        "applied_samples": _sample_entries(applied),
    }
    return _write_semantic_latest(quest_root=quest_root, summary=summary)


def _write_semantic_latest(*, quest_root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    latest_path = _capsules_root(quest_root) / "latest_semantic_process_retention.json"
    _write_json(latest_path, summary)
    summary["latest_receipt_path"] = _relpath(latest_path, quest_root)
    return summary


def _write_attempt_retention_receipt(
    *,
    quest_root: Path,
    record: Mapping[str, Any],
    recorded_at: str,
    status: str,
    apply: bool,
    candidates: list[Mapping[str, Any]],
    applied: list[Mapping[str, Any]],
    actual_release_bytes: int,
) -> None:
    receipt_path = quest_root / str(record.get("retention_receipt_path") or "")
    receipt = {
        "surface_kind": SEMANTIC_RETENTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "attempt_id": record.get("attempt_id"),
        "attempt_status": record.get("attempt_status"),
        "apply": bool(apply),
        "candidate_count": len(candidates),
        "applied_count": len(applied),
        "actual_release_bytes": int(actual_release_bytes),
        "body_included": False,
        "candidate_samples": _sample_entries(candidates),
        "applied_samples": _sample_entries(applied),
    }
    _write_json(receipt_path, receipt)


def _attempt_candidate(*, record: Mapping[str, Any], selected_logs: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "attempt_id": record.get("attempt_id"),
        "attempt_status": record.get("attempt_status"),
        "legacy_attempt_root_relpath": record.get("legacy_attempt_root_relpath"),
        "capsule_path": record.get("capsule_path"),
        "log_file_count": len(selected_logs),
        "raw_bytes": int(record.get("raw_bytes") or 0),
        "body_included": False,
    }


def _oversized_logs(
    *,
    record: Mapping[str, Any],
    max_log_bytes: int,
    max_raw_bytes: int,
) -> list[dict[str, Any]]:
    raw_bytes = int(record.get("raw_bytes") or 0)
    result: list[dict[str, Any]] = []
    for log_file in list(record.get("log_files") or []):
        if not isinstance(log_file, Mapping):
            continue
        size_bytes = int(log_file.get("size_bytes") or 0)
        if size_bytes <= max_log_bytes and raw_bytes <= max_raw_bytes:
            continue
        if str(log_file.get("surface_kind") or "") == SEMANTIC_REF_SURFACE_KIND:
            continue
        result.append(dict(log_file))
    return result


def _migrate_success_attempt(
    *,
    quest_root: Path,
    quest_id: str,
    record: Mapping[str, Any],
    log_entries: list[Mapping[str, Any]],
    recorded_at: str,
) -> dict[str, Any]:
    legacy_attempt_root = quest_root / str(record.get("legacy_attempt_root_relpath") or "")
    bytes_before = _directory_size_bytes(legacy_attempt_root)
    archive_path = _legacy_attempt_archive_path(
        quest_root=quest_root,
        attempt_id=str(record.get("attempt_id") or "attempt"),
        recorded_at=recorded_at,
        source_root=legacy_attempt_root,
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = _legacy_attempt_source_manifest(
        quest_root=quest_root,
        attempt_root=legacy_attempt_root,
        recorded_at=recorded_at,
    )
    source_manifest_path = archive_path.with_suffix(".manifest.json")
    restore_proof_path = archive_path.with_suffix(".restore_proof.json")
    _write_json(source_manifest_path, manifest)
    _write_tar_gz_archive(source_root=legacy_attempt_root, archive_path=archive_path)
    restore_proof = _tar_gz_restore_proof(archive_path=archive_path, manifest=manifest, verified_at=_utc_now())
    _write_json(restore_proof_path, restore_proof)
    if restore_proof.get("status") != "verified":
        return {
            "status": "blocked_restore_proof_failed",
            "archive_path": _relpath(archive_path, quest_root),
            "source_manifest_path": _relpath(source_manifest_path, quest_root),
            "restore_proof_path": _relpath(restore_proof_path, quest_root),
            "bytes_before": bytes_before,
            "released_bytes": 0,
            "restore_proof": restore_proof,
        }
    log_entry = log_entries[0] if log_entries else {}
    log_bytes = sum(int(entry.get("size_bytes") or 0) for entry in log_entries)
    ref_payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SEMANTIC_REF_SURFACE_KIND,
        "status": "semantic_ref",
        "quest_id": quest_id,
        "attempt_id": record.get("attempt_id"),
        "attempt_status": record.get("attempt_status"),
        "recorded_at": recorded_at,
        "source_kind": "legacy_ds_intake",
        "legacy_attempt_root": record.get("legacy_attempt_root_relpath"),
        "legacy_attempt_root_removed": True,
        "original_bytes": bytes_before,
        "original_sha256": manifest.get("manifest_sha256"),
        "log_bytes": log_bytes,
        "log_file_count": len(log_entries),
        "archive_path": _relpath(archive_path, quest_root),
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": _sha256(archive_path),
        "source_manifest_path": _relpath(source_manifest_path, quest_root),
        "restore_proof_path": _relpath(restore_proof_path, quest_root),
        "capsule_ref": str(record.get("capsule_path") or ""),
        "line_count": log_entry.get("line_count"),
        "retained_head": log_entry.get("head") or [],
        "retained_tail": log_entry.get("tail") or [],
        "error_samples": log_entry.get("error_samples") or [],
        "restore_proof": restore_proof,
        "body_included": False,
    }
    semantic_ref_path = quest_root / str(record.get("semantic_ref_path") or "")
    _write_json(semantic_ref_path, ref_payload)
    shutil.rmtree(legacy_attempt_root)
    bytes_after = semantic_ref_path.stat().st_size
    return {
        "status": "applied",
        "semantic_ref_path": _relpath(semantic_ref_path, quest_root),
        "archive_path": _relpath(archive_path, quest_root),
        "source_manifest_path": _relpath(source_manifest_path, quest_root),
        "restore_proof_path": _relpath(restore_proof_path, quest_root),
        "legacy_attempt_root": record.get("legacy_attempt_root_relpath"),
        "legacy_attempt_root_removed": True,
        "bytes_before": bytes_before,
        "bytes_after": bytes_after,
        "archive_bytes": archive_path.stat().st_size,
        "released_bytes": max(0, bytes_before - bytes_after - archive_path.stat().st_size),
        "sha256_before": manifest.get("manifest_sha256"),
        "sha256_after": _sha256(semantic_ref_path),
        "capsule_ref": str(record.get("capsule_path") or ""),
    }


def _read_attempt_metadata(attempt_root: Path) -> tuple[Path | None, dict[str, Any]]:
    for filename in _METADATA_FILENAMES:
        path = attempt_root / filename
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return path, payload
    return None, {}


def _attempt_status(metadata: Mapping[str, Any]) -> str | None:
    for key in ("status", "outcome", "state", "result"):
        value = str(metadata.get(key) or "").strip().lower()
        if value:
            return value
    return None


def _status_kind(status: object) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in _SUCCESS_STATUSES:
        return "success"
    if normalized in _FAILED_STATUSES:
        return "failed"
    return "unknown"


def _replay_manifest(
    *,
    quest_root: Path,
    attempt_root: Path,
    metadata_path: Path | None,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    command = metadata.get("command") or metadata.get("argv") or metadata.get("cmd")
    cwd = metadata.get("cwd") or metadata.get("working_dir")
    env_keys = metadata.get("env_keys") or metadata.get("environment_keys") or []
    return {
        "surface_kind": "runtime_attempt_replay_manifest",
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if command and cwd else "partial_replay_metadata",
        "attempt_metadata_path": _relpath(metadata_path, quest_root) if metadata_path else None,
        "legacy_attempt_root": _relpath(attempt_root, quest_root),
        "legacy_source_retained": True,
        "legacy_ds_long_term_read_allowed": False,
        "command": command,
        "cwd": str(cwd) if cwd else None,
        "env_keys": sorted(str(key) for key in env_keys) if isinstance(env_keys, list) else [],
        "body_included": False,
    }


def _declared_and_directory_manifest(
    *,
    quest_root: Path,
    attempt_root: Path,
    declared_values: object,
    directory_name: str,
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for path in _declared_paths(quest_root=quest_root, attempt_root=attempt_root, declared_values=declared_values):
        if path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(_file_manifest(path=resolved, quest_root=quest_root, attempt_root=attempt_root))
    directory = attempt_root / directory_name
    if directory.exists():
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(_file_manifest(path=resolved, quest_root=quest_root, attempt_root=attempt_root))
    return {
        "surface_kind": f"runtime_attempt_{directory_name}_manifest",
        "schema_version": SCHEMA_VERSION,
        "status": "materialized" if files else "empty",
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "files": files,
        "body_included": False,
    }


def _declared_paths(*, quest_root: Path, attempt_root: Path, declared_values: object) -> list[Path]:
    values: list[object]
    if isinstance(declared_values, list):
        values = declared_values
    elif isinstance(declared_values, str):
        values = [declared_values]
    else:
        values = []
    paths: list[Path] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        if candidate.is_absolute():
            paths.append(candidate)
            continue
        attempt_candidate = attempt_root / candidate
        paths.append(attempt_candidate if attempt_candidate.exists() else quest_root / candidate)
    return paths


def _log_digest(*, quest_root: Path, attempt_root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(attempt_root.rglob("*")):
        if not path.is_file() or not _is_log_file(path):
            continue
        digest = _text_digest(path=path, quest_root=quest_root, attempt_root=attempt_root)
        files.append(digest)
    return {
        "surface_kind": "runtime_attempt_log_digest",
        "schema_version": SCHEMA_VERSION,
        "status": "materialized" if files else "empty",
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "files": files,
        "body_included": False,
    }


def _is_log_file(path: Path) -> bool:
    name = path.name.lower()
    if name in _METADATA_FILENAMES:
        return False
    if path.suffix.lower() in _LOG_SUFFIXES:
        return True
    if path.suffix.lower() in {".txt", ".jsonl"} and any(token in name for token in _LOG_NAME_TOKENS):
        return True
    return False


def _text_digest(*, path: Path, quest_root: Path, attempt_root: Path) -> dict[str, Any]:
    line_count = 0
    head: list[str] = []
    tail: deque[str] = deque(maxlen=8)
    error_samples: list[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line_count += 1
                normalized = line.rstrip("\n")
                if len(head) < 8:
                    head.append(normalized)
                tail.append(normalized)
                lowered = normalized.lower()
                if len(error_samples) < 8 and any(token in lowered for token in ("error", "traceback", "exception")):
                    error_samples.append(normalized)
    except OSError:
        pass
    semantic_ref_kind = _semantic_ref_kind(path)
    payload = {
        "path": _relpath(path, quest_root),
        "attempt_path": _relpath(path, attempt_root),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "line_count": line_count,
        "head": head,
        "tail": list(tail),
        "error_samples": error_samples,
        "body_included": False,
    }
    if semantic_ref_kind:
        payload["surface_kind"] = semantic_ref_kind
    return payload


def _semantic_ref_kind(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and payload.get("surface_kind") == SEMANTIC_REF_SURFACE_KIND:
        return SEMANTIC_REF_SURFACE_KIND
    return None


def _file_manifest(*, path: Path, quest_root: Path, attempt_root: Path) -> dict[str, Any]:
    return {
        "path": _relpath(path, quest_root),
        "attempt_path": _relpath(path, attempt_root),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "body_included": False,
    }


def _manifest_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": manifest.get("surface_kind"),
        "status": manifest.get("status"),
        "file_count": manifest.get("file_count"),
        "total_bytes": manifest.get("total_bytes"),
        "body_included": False,
    }


def _legacy_attempt_archive_path(
    *,
    quest_root: Path,
    attempt_id: str,
    recorded_at: str,
    source_root: Path,
) -> Path:
    relative = str(_relpath(source_root, quest_root) or "legacy_attempt").replace("/", "__")
    safe_attempt = _safe_artifact_id(attempt_id)
    slug = _artifact_slug(recorded_at)
    return (
        quest_root
        / "artifacts"
        / "runtime"
        / "restore_index"
        / "legacy_attempt_raw"
        / f"{slug}_{safe_attempt}_{relative}.tar.gz"
    )


def _legacy_attempt_source_manifest(*, quest_root: Path, attempt_root: Path, recorded_at: str) -> dict[str, Any]:
    files = [
        _file_manifest(path=path.resolve(), quest_root=quest_root, attempt_root=attempt_root)
        for path in sorted(attempt_root.rglob("*"))
        if path.is_file()
    ]
    payload = {
        "surface_kind": "legacy_attempt_raw_source_manifest",
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "source_kind": "legacy_ds_intake",
        "legacy_attempt_root": _relpath(attempt_root, quest_root),
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "files": files,
        "body_included": False,
    }
    payload["manifest_sha256"] = _sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


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


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(candidate.stat().st_size for candidate in path.rglob("*") if candidate.is_file())


def _sample_entries(entries: list[Mapping[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return [dict(entry) for entry in entries[: max(0, int(limit))]]


def _capsules_root(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "attempt_evidence"


def _capsule_root(quest_root: Path, attempt_id: str) -> Path:
    return _capsules_root(quest_root) / _safe_artifact_id(attempt_id)


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


__all__ = [
    "CAPSULE_SURFACE_KIND",
    "SEMANTIC_REF_SURFACE_KIND",
    "SEMANTIC_RETENTION_SURFACE_KIND",
    "materialize_attempt_evidence_capsules",
]
