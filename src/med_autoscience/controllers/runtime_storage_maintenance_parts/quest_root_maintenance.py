from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers import study_runtime_resolution
from med_autoscience.controllers.runtime_storage_maintenance_parts import backend_maintenance
from med_autoscience.controllers.runtime_storage_maintenance_parts.authority_boundary import (
    storage_refs_only_adapter_boundary,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.jsonl_slimming import (
    slim_oversized_jsonl_files,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction import (
    compact_cold_runtime_buckets,
    restore_proof_compaction_blockers,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import domain_authority_refs_index


SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
_PRIMARY_BUCKETS = ("bash_exec", "codex_homes", "runs", "codex_history", "worktrees")


def maintain_quest_runtime_storage(
    *,
    profile: WorkspaceProfile,
    quest_root: Path,
    include_worktrees: bool = True,
    older_than_seconds: int = 6 * 3600,
    jsonl_max_mb: int = 64,
    text_max_mb: int = 16,
    event_segment_max_mb: int = 64,
    slim_jsonl_threshold_mb: int | None = 8,
    dedupe_worktree_min_mb: int | None = 16,
    head_lines: int = 200,
    tail_lines: int = 200,
    allow_live_runtime: bool = False,
    restore_proof_compaction: bool = False,
    include_parked_controller_stop: bool = False,
    include_operator_confirmed_parked_active: bool = False,
    restore_proof_buckets: Iterable[str] | None = None,
) -> dict[str, Any]:
    recorded_at = _utc_now()
    selected_restore_proof_buckets = _restore_proof_buckets(restore_proof_buckets)
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    quest_id = _quest_id_from_root(resolved_quest_root)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "profile_name": profile.name,
        "study_id": None,
        "study_root": None,
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "include_worktrees": include_worktrees,
        "allow_live_runtime": allow_live_runtime,
        "restore_proof_compaction_enabled": restore_proof_compaction,
        "include_parked_controller_stop": include_parked_controller_stop,
        "include_operator_confirmed_parked_active": include_operator_confirmed_parked_active,
        "restore_proof_buckets": list(selected_restore_proof_buckets),
        "orphan_quest_root_mode": True,
        "storage_refs_only_adapter_boundary": storage_refs_only_adapter_boundary(
            report_mode="orphan_quest_runtime_storage_maintenance",
        ),
    }
    result["quest_runtime_before"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_before"] = _size_summary(resolved_quest_root, buckets=selected_restore_proof_buckets)

    if not result["quest_runtime_before"]["quest_exists"]:
        result["status"] = "blocked_missing_quest_root"
        result["summary"] = "quest root 尚未就绪，当前无法执行 runtime storage maintenance。"
    elif restore_proof_compaction:
        _apply_restore_proof_compaction(
            result=result,
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            buckets=selected_restore_proof_buckets,
            include_parked_controller_stop=include_parked_controller_stop,
            include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
        )
    elif (
        not allow_live_runtime
        and result["quest_runtime_before"]["status"] in _LIVE_RUNTIME_STATUSES
        and result["quest_runtime_before"]["active_run_id"] is not None
    ):
        result["status"] = "blocked_live_runtime"
        result["summary"] = "quest 当前仍在 live runtime，storage maintenance 需要先停车或显式放行。"
    else:
        _apply_backend_maintenance(
            result=result,
            profile=profile,
            quest_root=resolved_quest_root,
            include_worktrees=include_worktrees,
            older_than_seconds=older_than_seconds,
            jsonl_max_mb=jsonl_max_mb,
            text_max_mb=text_max_mb,
            event_segment_max_mb=event_segment_max_mb,
            slim_jsonl_threshold_mb=slim_jsonl_threshold_mb,
            dedupe_worktree_min_mb=dedupe_worktree_min_mb,
            head_lines=head_lines,
            tail_lines=tail_lines,
        )

    result["quest_runtime_after"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_after"] = _size_summary(resolved_quest_root, buckets=selected_restore_proof_buckets)
    report_path = _quest_runtime_maintenance_report_path(resolved_quest_root, recorded_at)
    latest_report_path = _quest_runtime_maintenance_latest_path(resolved_quest_root)
    result["report_path"] = str(report_path)
    result["latest_report_path"] = str(latest_report_path)
    _write_json(report_path, result)
    _write_json(latest_report_path, result)
    return result


def _apply_restore_proof_compaction(
    *,
    result: dict[str, Any],
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    buckets: tuple[str, ...],
    include_parked_controller_stop: bool,
    include_operator_confirmed_parked_active: bool,
) -> None:
    blockers = restore_proof_compaction_blockers(
        result["quest_runtime_before"],
        include_parked_controller_stop=include_parked_controller_stop,
        include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
    )
    if blockers:
        result["status"] = "blocked_restore_proof_compaction"
        result["summary"] = "quest 未达到 stopped-cold restore-proof compaction 条件。"
        result["restore_proof_compaction"] = {
            "surface_kind": "runtime_restore_proof_compaction",
            "status": "blocked_not_stopped_cold",
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "actual_release_bytes": 0,
            "blockers": blockers,
        }
        return

    compaction_result = compact_cold_runtime_buckets(
        quest_root=quest_root,
        quest_id=quest_id,
        recorded_at=recorded_at,
        buckets=buckets,
    )
    result["restore_proof_compaction"] = compaction_result
    archive_ref = compaction_result.get("archive_ref")
    if isinstance(archive_ref, Mapping):
        result["domain_authority_archive_ref_index"] = domain_authority_refs_index.record_archive_ref(
            quest_root=quest_root,
            archive_ref=archive_ref,
        )
    status = str(compaction_result.get("status") or "")
    if status in {"compacted", "nothing_to_archive"}:
        result["status"] = "maintained"
        result["summary"] = "orphan/legacy quest runtime restore-proof compaction 已完成。"
    else:
        result["status"] = status or "blocked_restore_proof_compaction"
        result["summary"] = "orphan/legacy quest runtime restore-proof compaction 未完成。"


def _apply_backend_maintenance(
    *,
    result: dict[str, Any],
    profile: WorkspaceProfile,
    quest_root: Path,
    include_worktrees: bool,
    older_than_seconds: int,
    jsonl_max_mb: int,
    text_max_mb: int,
    event_segment_max_mb: int,
    slim_jsonl_threshold_mb: int | None,
    dedupe_worktree_min_mb: int | None,
    head_lines: int,
    tail_lines: int,
) -> None:
    jsonl_slimming_result = slim_oversized_jsonl_files(
        quest_root=quest_root,
        recorded_at=str(result["recorded_at"]),
        threshold_mb=slim_jsonl_threshold_mb,
        head_lines=head_lines,
        tail_lines=tail_lines,
    )
    result["jsonl_slimming"] = jsonl_slimming_result
    backend_result = backend_maintenance.run_quest_storage_maintenance(
        profile=profile,
        quest_root=quest_root,
        include_worktrees=include_worktrees,
        older_than_seconds=older_than_seconds,
        jsonl_max_mb=jsonl_max_mb,
        text_max_mb=text_max_mb,
        event_segment_max_mb=event_segment_max_mb,
        slim_jsonl_threshold_mb=slim_jsonl_threshold_mb,
        dedupe_worktree_min_mb=dedupe_worktree_min_mb,
        head_lines=head_lines,
        tail_lines=tail_lines,
    )
    if backend_result is None:
        if jsonl_slimming_result.get("status") == "slimmed":
            result["status"] = "maintained"
            result["summary"] = "orphan/legacy quest oversized runtime JSONL 已由 MAS refs-only maintenance 瘦身。"
        else:
            result["status"] = "blocked_backend_unavailable"
            result["summary"] = "med-deepscientist runtime storage maintenance 脚本当前不可用。"
    else:
        result["maintenance"] = backend_result
        if backend_result.get("status") in {"backend_failed", "backend_output_invalid"}:
            result["status"] = str(backend_result.get("status"))
            result["summary"] = "med-deepscientist runtime storage maintenance 执行失败。"
        else:
            result["status"] = "maintained"
            result["summary"] = "orphan/legacy quest runtime storage maintenance 已完成。"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_slug(recorded_at: str) -> str:
    normalized = recorded_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = study_runtime_resolution._load_yaml_dict(path)
    return payload if isinstance(payload, dict) else {}


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for current_root, _, filenames in os.walk(path):
        current_path = Path(current_root)
        for filename in filenames:
            candidate = current_path / filename
            try:
                total += candidate.stat().st_size
            except OSError:
                continue
    return total


def _size_summary(quest_root: Path, *, buckets: Iterable[str] | None = None) -> dict[str, Any]:
    ds_root = quest_root / ".ds"
    bucket_summaries: dict[str, Any] = {}
    for bucket_name in _restore_proof_buckets(buckets):
        bucket_path = ds_root / bucket_name
        bucket_summaries[bucket_name] = {
            "path": str(bucket_path),
            "bytes": _directory_size_bytes(bucket_path),
        }
    return {
        "root": str(ds_root),
        "total_bytes": _directory_size_bytes(ds_root),
        "buckets": bucket_summaries,
    }


def _restore_proof_buckets(buckets: Iterable[str] | None) -> tuple[str, ...]:
    if buckets is None:
        return _PRIMARY_BUCKETS
    selected = tuple(dict.fromkeys(str(bucket).strip() for bucket in buckets if str(bucket).strip()))
    return selected or _PRIMARY_BUCKETS


def _quest_runtime_snapshot(quest_root: Path) -> dict[str, Any]:
    runtime_state: dict[str, Any] = {}
    runtime_state_error: str | None = None
    try:
        runtime_state = quest_state.load_runtime_state(quest_root)
    except (OSError, json.JSONDecodeError) as exc:
        runtime_state_error = f"{type(exc).__name__}: {exc}"
    return {
        "quest_exists": (quest_root / "quest.yaml").exists(),
        "status": str(runtime_state.get("status") or "").strip().lower() or None,
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
        "runtime_state_error": runtime_state_error,
    }


def _quest_id_from_root(quest_root: Path) -> str:
    quest_payload = _read_yaml_dict(quest_root / "quest.yaml")
    quest_id = str(quest_payload.get("quest_id") or "").strip()
    return quest_id or quest_root.name


def _quest_runtime_maintenance_report_path(quest_root: Path, recorded_at: str) -> Path:
    return quest_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / f"{_artifact_slug(recorded_at)}.json"


def _quest_runtime_maintenance_latest_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / "latest.json"
