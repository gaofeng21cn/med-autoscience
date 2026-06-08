from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_resolution
from med_autoscience.controllers.runtime_storage_maintenance_parts.authority_boundary import (
    storage_refs_only_adapter_boundary,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.quest_root_maintenance import (
    maintain_quest_runtime_storage,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import refs_only_state_index_pilot as refs_only_state_index_pilot_module
from med_autoscience.runtime_protocol.study_runtime import resolve_study_runtime_paths


SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def maintain_runtime_storage(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
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
    restore_proof_canary: bool = False,
    restore_proof_canary_entry_limit: int = 20,
    restore_proof_max_shards: int | None = None,
    include_parked_controller_stop: bool = False,
    include_operator_confirmed_parked_active: bool = False,
    restore_proof_buckets: Iterable[str] | None = None,
    refs_only_state_index_pilot: bool = False,
    refs_only_state_index_only: bool = False,
    archive_retention: bool = False,
    archive_retention_apply: bool = False,
    archive_retention_min_mb: int = 16,
    archive_retention_cold_store_root: Path | None = None,
    report_retention: bool = False,
    report_retention_apply: bool = False,
    report_retention_keep_recent_days: int = 1,
    report_retention_daily_samples: int = 2,
    report_retention_max_files: int | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = study_runtime_resolution._resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    quest_id = _resolve_quest_id(
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
    )
    runtime_paths = resolve_study_runtime_paths(
        profile=profile,
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        quest_id=quest_id,
    )
    resolved_quest_root = Path(runtime_paths["quest_root"]).expanduser().resolve()
    result = maintain_quest_runtime_storage(
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
        allow_live_runtime=allow_live_runtime,
        restore_proof_compaction=restore_proof_compaction,
        restore_proof_canary=restore_proof_canary,
        restore_proof_canary_entry_limit=restore_proof_canary_entry_limit,
        restore_proof_max_shards=restore_proof_max_shards,
        include_parked_controller_stop=include_parked_controller_stop,
        include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
        restore_proof_buckets=restore_proof_buckets,
        refs_only_state_index_pilot=refs_only_state_index_pilot,
        refs_only_state_index_only=refs_only_state_index_only,
        archive_retention=archive_retention,
        archive_retention_apply=archive_retention_apply,
        archive_retention_min_mb=archive_retention_min_mb,
        archive_retention_cold_store_root=archive_retention_cold_store_root,
        report_retention=report_retention,
        report_retention_apply=report_retention_apply,
        report_retention_keep_recent_days=report_retention_keep_recent_days,
        report_retention_daily_samples=report_retention_daily_samples,
        report_retention_max_files=report_retention_max_files,
    )
    result["schema_version"] = SCHEMA_VERSION
    result["study_id"] = resolved_study_id
    result["study_root"] = str(resolved_study_root)
    result["quest_id"] = quest_id
    result["orphan_quest_root_mode"] = False
    result["storage_refs_only_adapter_boundary"] = storage_refs_only_adapter_boundary(
        report_mode="study_runtime_storage_maintenance",
    )
    _rebuild_study_refs_index_if_needed(
        result=result,
        profile=profile,
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        refs_only_state_index_pilot=refs_only_state_index_pilot,
        refs_only_state_index_only=refs_only_state_index_only,
    )
    recorded_at = str(result.get("recorded_at") or _utc_now())
    report_path = _timestamped_report_path(resolved_study_root, recorded_at)
    latest_report_path = _latest_report_path(resolved_study_root)
    result["report_path"] = str(report_path)
    result["latest_report_path"] = str(latest_report_path)
    _write_json(report_path, result)
    _write_json(latest_report_path, result)
    return result


def _rebuild_study_refs_index_if_needed(
    *,
    result: dict[str, Any],
    profile: WorkspaceProfile,
    study_root: Path,
    quest_root: Path,
    refs_only_state_index_pilot: bool,
    refs_only_state_index_only: bool,
) -> None:
    if refs_only_state_index_pilot and result.get("status") in {"maintained", "blocked_backend_unavailable"}:
        previous_status = str(result.get("status") or "")
        result["refs_only_state_index_pilot"] = refs_only_state_index_pilot_module.rebuild_refs_only_state_index(
            workspace_root=profile.workspace_root,
            study_root=study_root,
            quest_root=quest_root,
        )
        if previous_status == "blocked_backend_unavailable":
            result["legacy_backend_status"] = previous_status
            result["status"] = "maintained"
            result["summary"] = "refs-only state index pilot 已完成；legacy backend storage maintenance 当前不可用。"
    elif refs_only_state_index_only:
        result["refs_only_state_index_pilot"] = {
            "surface_kind": refs_only_state_index_pilot_module.SURFACE_KIND,
            "status": "skipped",
            "skip_reason": str(result.get("status") or "refs_only_state_index_pilot_not_enabled"),
            "body_included": False,
        }


def _resolve_quest_id(*, study_id: str, study_root: Path, study_payload: Mapping[str, Any]) -> str:
    runtime_binding = _read_yaml_dict(study_root / "runtime_binding.yaml")
    binding_quest_id = str(runtime_binding.get("quest_id") or "").strip()
    if binding_quest_id:
        return binding_quest_id
    execution = study_payload.get("execution")
    if isinstance(execution, Mapping):
        execution_quest_id = str(execution.get("quest_id") or "").strip()
        if execution_quest_id:
            return execution_quest_id
    return study_id


def _read_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = study_runtime_resolution._load_yaml_dict(path)
    return payload if isinstance(payload, dict) else {}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_slug(recorded_at: str) -> str:
    normalized = recorded_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _report_root(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_storage_maintenance"


def _latest_report_path(study_root: Path) -> Path:
    return _report_root(study_root) / "latest.json"


def _timestamped_report_path(study_root: Path, recorded_at: str) -> Path:
    return _report_root(study_root) / f"{_artifact_slug(recorded_at)}.json"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


__all__ = ["maintain_runtime_storage"]
