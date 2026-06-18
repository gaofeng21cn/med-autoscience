from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers import study_runtime_resolution
from med_autoscience.controllers.runtime_storage_maintenance_parts import backend_maintenance
from med_autoscience.controllers.runtime_storage_maintenance_parts.archive_report_retention import (
    retain_report_snapshots,
    retain_restore_proof_archive_bodies,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.attempt_evidence_capsule import (
    materialize_attempt_evidence_capsules,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.authority_boundary import (
    storage_refs_only_adapter_boundary,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.maintenance_authorization import (
    AUTHORIZATION_BLOCKER_STATUS,
    AUTHORIZATION_TYPED_BLOCKER,
    opl_storage_maintenance_authorization_result,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.jsonl_slimming import (
    slim_oversized_jsonl_files,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction import (
    archive_refs_from_compaction_result,
    compact_cold_runtime_buckets,
    plan_restore_proof_compaction_canary,
    restore_proof_compaction_blockers,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import domain_authority_refs_index
from med_autoscience.runtime_protocol import refs_only_state_index_pilot as refs_only_state_index_pilot_module


SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
_PRIMARY_BUCKETS = ("bash_exec", "codex_homes", "runs", "codex_history", "worktrees")
_QUEST_RUNTIME_MAINTENANCE_OPERATION = "quest_runtime_storage_apply"
_QUEST_RUNTIME_MAINTENANCE_SURFACE = "quest_runtime_storage_maintenance"


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
    attempt_evidence_capsules: bool = False,
    semantic_process_retention: bool = False,
    semantic_process_retention_apply: bool = False,
    semantic_retention_max_log_bytes: int = 256 * 1024,
    semantic_retention_max_raw_bytes: int = 1024 * 1024,
    semantic_retention_keep_failed_raw: bool = True,
    semantic_retention_max_files: int | None = None,
    opl_maintenance_authorization: Mapping[str, Any] | None = None,
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
        "restore_proof_canary_enabled": restore_proof_canary,
        "restore_proof_canary_entry_limit": int(restore_proof_canary_entry_limit),
        "restore_proof_max_shards": restore_proof_max_shards,
        "include_parked_controller_stop": include_parked_controller_stop,
        "include_operator_confirmed_parked_active": include_operator_confirmed_parked_active,
        "restore_proof_buckets": list(selected_restore_proof_buckets),
        "refs_only_state_index_pilot_enabled": refs_only_state_index_pilot,
        "refs_only_state_index_only": refs_only_state_index_only,
        "archive_retention_enabled": archive_retention,
        "archive_retention_apply": archive_retention_apply,
        "archive_retention_min_mb": archive_retention_min_mb,
        "report_retention_enabled": report_retention,
        "report_retention_apply": report_retention_apply,
        "report_retention_keep_recent_days": report_retention_keep_recent_days,
        "report_retention_daily_samples": report_retention_daily_samples,
        "report_retention_max_files": report_retention_max_files,
        "attempt_evidence_capsules_enabled": attempt_evidence_capsules,
        "semantic_process_retention_enabled": semantic_process_retention,
        "semantic_process_retention_apply": semantic_process_retention_apply,
        "semantic_retention_max_log_bytes": semantic_retention_max_log_bytes,
        "semantic_retention_max_raw_bytes": semantic_retention_max_raw_bytes,
        "semantic_retention_keep_failed_raw": semantic_retention_keep_failed_raw,
        "semantic_retention_max_files": semantic_retention_max_files,
        "orphan_quest_root_mode": True,
        "storage_refs_only_adapter_boundary": storage_refs_only_adapter_boundary(
            report_mode="orphan_quest_runtime_storage_maintenance",
        ),
    }
    authorization_required = _quest_runtime_storage_apply_requires_authorization(
        restore_proof_compaction=restore_proof_compaction,
        restore_proof_canary=restore_proof_canary,
        refs_only_state_index_only=refs_only_state_index_only,
        archive_retention=archive_retention,
        archive_retention_apply=archive_retention_apply,
        report_retention=report_retention,
        report_retention_apply=report_retention_apply,
        attempt_evidence_capsules=attempt_evidence_capsules,
        semantic_process_retention=semantic_process_retention,
        semantic_process_retention_apply=semantic_process_retention_apply,
    )
    authorization_proof, authorization_blocker = opl_storage_maintenance_authorization_result(
        apply=authorization_required,
        authorization=opl_maintenance_authorization,
        operation=_QUEST_RUNTIME_MAINTENANCE_OPERATION,
        maintenance_surface=_QUEST_RUNTIME_MAINTENANCE_SURFACE,
        workspace_root=profile.workspace_root,
        quest_root=resolved_quest_root,
    )
    result["opl_maintenance_authorization"] = authorization_proof
    if authorization_blocker is not None:
        result.update(
            {
                "status": AUTHORIZATION_BLOCKER_STATUS,
                "typed_blocker": AUTHORIZATION_TYPED_BLOCKER,
                "stable_blocker": True,
                "owner": "one-person-lab",
                "mas_role": "maintenance_callable_adapter",
                "summary": "OPL runtime storage maintenance authorization is required before MAS can apply physical runtime storage maintenance.",
                "blockers": [authorization_blocker],
            }
        )
        result["quest_runtime_after"] = result["quest_runtime_before"] = _quest_runtime_snapshot(resolved_quest_root)
        result["size_before"] = _size_summary_skipped(resolved_quest_root, reason=AUTHORIZATION_TYPED_BLOCKER)
        result["size_after"] = result["size_before"]
        report_path = _quest_runtime_maintenance_report_path(resolved_quest_root, recorded_at)
        latest_report_path = _quest_runtime_maintenance_latest_path(resolved_quest_root)
        result["report_path"] = str(report_path)
        result["latest_report_path"] = str(latest_report_path)
        _write_json(report_path, result)
        _write_json(latest_report_path, result)
        return result
    lightweight_buckets = selected_restore_proof_buckets if restore_proof_compaction else ()
    result["runtime_state_materialization"] = quest_state.materialize_runtime_state_surface(
        resolved_quest_root,
        recorded_at=recorded_at,
    )
    result["quest_runtime_before"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_before"] = (
        _size_summary_skipped(resolved_quest_root, reason="refs_only_state_index_only")
        if refs_only_state_index_only
        else _size_summary(
            resolved_quest_root,
            buckets=selected_restore_proof_buckets,
            lightweight_buckets=lightweight_buckets,
        )
    )

    if restore_proof_compaction and restore_proof_canary:
        result["status"] = "blocked_restore_proof_mode_conflict"
        result["summary"] = "--restore-proof-canary cannot be combined with --restore-proof-compaction."
    elif refs_only_state_index_only and not refs_only_state_index_pilot:
        result["status"] = "blocked_refs_only_state_index_only_without_pilot"
        result["summary"] = "--refs-only-state-index-only requires --refs-only-state-index-pilot."
    elif not result["quest_runtime_before"]["quest_exists"]:
        result["status"] = "blocked_missing_quest_root"
        result["summary"] = "quest root 尚未就绪，当前无法执行 runtime storage maintenance。"
    elif refs_only_state_index_only and not restore_proof_canary:
        result["status"] = "maintained"
        result["summary"] = "refs-only state index pilot 已完成；legacy backend storage maintenance 已按显式 only 模式跳过。"
        result["legacy_backend_status"] = "skipped_by_refs_only_state_index_only"
    elif restore_proof_compaction:
        _apply_restore_proof_compaction(
            result=result,
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            buckets=selected_restore_proof_buckets,
            max_shards=restore_proof_max_shards,
            include_parked_controller_stop=include_parked_controller_stop,
            include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
        )
    elif restore_proof_canary:
        _apply_restore_proof_canary(
            result=result,
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            buckets=selected_restore_proof_buckets,
            entry_limit=restore_proof_canary_entry_limit,
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
    elif _quest_runtime_storage_plan_only_request(
        archive_retention=archive_retention,
        archive_retention_apply=archive_retention_apply,
        report_retention=report_retention,
        report_retention_apply=report_retention_apply,
        attempt_evidence_capsules=attempt_evidence_capsules,
        semantic_process_retention=semantic_process_retention,
        semantic_process_retention_apply=semantic_process_retention_apply,
    ):
        result["status"] = "maintained"
        result["summary"] = "quest runtime storage refs/projection plan 已完成；legacy backend physical maintenance 已跳过。"
        result["legacy_backend_status"] = "skipped_by_plan_only_projection"
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

    if refs_only_state_index_pilot:
        if result.get("status") == "maintained":
            result["refs_only_state_index_pilot"] = refs_only_state_index_pilot_module.rebuild_refs_only_state_index(
                workspace_root=profile.workspace_root,
                study_root=None,
                quest_root=resolved_quest_root,
            )
        else:
            result["refs_only_state_index_pilot"] = {
                "surface_kind": refs_only_state_index_pilot_module.SURFACE_KIND,
                "status": "skipped",
                "skip_reason": str(result.get("status") or "storage_maintenance_not_maintained"),
                "body_included": False,
            }
    elif refs_only_state_index_only:
        result["refs_only_state_index_pilot"] = {
            "surface_kind": refs_only_state_index_pilot_module.SURFACE_KIND,
            "status": "skipped",
            "skip_reason": str(result.get("status") or "refs_only_state_index_pilot_not_enabled"),
            "body_included": False,
        }

    _apply_retention_if_requested(
        result=result,
        quest_root=resolved_quest_root,
        quest_id=quest_id,
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
    _apply_attempt_evidence_capsules_if_requested(
        result=result,
        quest_root=resolved_quest_root,
        quest_id=quest_id,
        attempt_evidence_capsules=attempt_evidence_capsules,
        semantic_process_retention=semantic_process_retention,
        semantic_process_retention_apply=semantic_process_retention_apply,
        semantic_retention_max_log_bytes=semantic_retention_max_log_bytes,
        semantic_retention_max_raw_bytes=semantic_retention_max_raw_bytes,
        semantic_retention_keep_failed_raw=semantic_retention_keep_failed_raw,
        semantic_retention_max_files=semantic_retention_max_files,
    )

    result["quest_runtime_after"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_after"] = (
        _size_summary_skipped(resolved_quest_root, reason="refs_only_state_index_only")
        if refs_only_state_index_only
        else _size_summary(
            resolved_quest_root,
            buckets=selected_restore_proof_buckets,
            lightweight_buckets=lightweight_buckets,
        )
    )
    report_path = _quest_runtime_maintenance_report_path(resolved_quest_root, recorded_at)
    latest_report_path = _quest_runtime_maintenance_latest_path(resolved_quest_root)
    result["report_path"] = str(report_path)
    result["latest_report_path"] = str(latest_report_path)
    _write_json(report_path, result)
    _write_json(latest_report_path, result)
    return result


def _quest_runtime_storage_apply_requires_authorization(
    *,
    restore_proof_compaction: bool,
    restore_proof_canary: bool,
    refs_only_state_index_only: bool,
    archive_retention: bool,
    archive_retention_apply: bool,
    report_retention: bool,
    report_retention_apply: bool,
    attempt_evidence_capsules: bool,
    semantic_process_retention: bool,
    semantic_process_retention_apply: bool,
) -> bool:
    if restore_proof_compaction or archive_retention_apply or report_retention_apply or semantic_process_retention_apply:
        return True
    if restore_proof_canary or refs_only_state_index_only:
        return False
    if _quest_runtime_storage_plan_only_request(
        archive_retention=archive_retention,
        archive_retention_apply=archive_retention_apply,
        report_retention=report_retention,
        report_retention_apply=report_retention_apply,
        attempt_evidence_capsules=attempt_evidence_capsules,
        semantic_process_retention=semantic_process_retention,
        semantic_process_retention_apply=semantic_process_retention_apply,
    ):
        return False
    return True


def _quest_runtime_storage_plan_only_request(
    *,
    archive_retention: bool,
    archive_retention_apply: bool,
    report_retention: bool,
    report_retention_apply: bool,
    attempt_evidence_capsules: bool,
    semantic_process_retention: bool,
    semantic_process_retention_apply: bool,
) -> bool:
    if archive_retention_apply or report_retention_apply or semantic_process_retention_apply:
        return False
    return archive_retention or report_retention or attempt_evidence_capsules or semantic_process_retention


def _apply_restore_proof_compaction(
    *,
    result: dict[str, Any],
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    buckets: tuple[str, ...],
    max_shards: int | None,
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
        max_shards=max_shards,
    )
    result["restore_proof_compaction"] = compaction_result
    archive_refs = _archive_refs_from_compaction(compaction_result)
    if archive_refs:
        indexed_results = [
            domain_authority_refs_index.record_archive_ref(
                quest_root=quest_root,
                archive_ref=archive_ref,
            )
            for archive_ref in archive_refs
        ]
        result["domain_authority_archive_ref_index"] = _archive_ref_index_summary(indexed_results)
    status = str(compaction_result.get("status") or "")
    if status in {"compacted", "nothing_to_archive"}:
        result["status"] = "maintained"
        result["summary"] = "orphan/legacy quest runtime restore-proof compaction 已完成。"
    else:
        result["status"] = status or "blocked_restore_proof_compaction"
        result["summary"] = "orphan/legacy quest runtime restore-proof compaction 未完成。"


def _apply_restore_proof_canary(
    *,
    result: dict[str, Any],
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    buckets: tuple[str, ...],
    entry_limit: int,
    include_parked_controller_stop: bool,
    include_operator_confirmed_parked_active: bool,
) -> None:
    blockers = restore_proof_compaction_blockers(
        result["quest_runtime_before"],
        include_parked_controller_stop=include_parked_controller_stop,
        include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
    )
    canary_result = plan_restore_proof_compaction_canary(
        quest_root=quest_root,
        quest_id=quest_id,
        recorded_at=recorded_at,
        buckets=buckets,
        entry_limit=entry_limit,
        blockers=blockers,
    )
    result["restore_proof_canary"] = canary_result
    result["legacy_backend_status"] = (
        "skipped_by_restore_proof_canary_and_refs_only_state_index_only"
        if bool(result.get("refs_only_state_index_only"))
        else "skipped_by_restore_proof_canary"
    )
    if canary_result.get("status") == "verified":
        result["status"] = "maintained"
        result["summary"] = "orphan/legacy quest bounded restore-proof canary 已完成，源 runtime payload 已保留。"
    elif canary_result.get("status") == "nothing_to_archive":
        result["status"] = "maintained"
        result["summary"] = "orphan/legacy quest bounded restore-proof canary 未发现可采样 runtime payload。"
    else:
        result["status"] = "blocked_restore_proof_canary"
        result["summary"] = "orphan/legacy quest bounded restore-proof canary 未完成。"


def _archive_refs_from_compaction(compaction: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return archive_refs_from_compaction_result(compaction)


def _archive_ref_index_summary(indexed_results: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not indexed_results:
        return {}
    result = dict(indexed_results[-1])
    result["indexed_count"] = len(indexed_results)
    result["emitted_source_ref_count"] = len(indexed_results)
    result["indexed_results_inlined"] = False
    return result


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


def _apply_retention_if_requested(
    *,
    result: dict[str, Any],
    quest_root: Path,
    quest_id: str,
    archive_retention: bool,
    archive_retention_apply: bool,
    archive_retention_min_mb: int,
    archive_retention_cold_store_root: Path | None,
    report_retention: bool,
    report_retention_apply: bool,
    report_retention_keep_recent_days: int,
    report_retention_daily_samples: int,
    report_retention_max_files: int | None,
) -> None:
    apply_allowed = result.get("status") in {"maintained", "blocked_backend_unavailable"}
    if archive_retention:
        if archive_retention_apply and not apply_allowed:
            archive_result = {
                "surface_kind": "runtime_restore_proof_archive_body_retention",
                "status": "blocked_storage_maintenance_not_maintained",
                "quest_id": quest_id,
                "quest_root": str(quest_root),
                "apply": True,
                "blocker": str(result.get("status") or "storage_maintenance_not_maintained"),
                "actual_release_bytes": 0,
            }
        else:
            archive_result = retain_restore_proof_archive_bodies(
                quest_root=quest_root,
                quest_id=quest_id,
                recorded_at=str(result["recorded_at"]),
                apply=archive_retention_apply,
                min_archive_mb=archive_retention_min_mb,
                cold_store_root=archive_retention_cold_store_root,
            )
        result["archive_retention"] = archive_result
        if archive_retention_apply and archive_result.get("status") in {"applied", "nothing_to_retain"}:
            result["status"] = "maintained"
            result["summary"] = "quest runtime restore-proof archive body retention 已完成。"
    if report_retention:
        if report_retention_apply and not apply_allowed:
            report_result = {
                "surface_kind": "runtime_report_snapshot_retention",
                "status": "blocked_storage_maintenance_not_maintained",
                "quest_id": quest_id,
                "quest_root": str(quest_root),
                "apply": True,
                "blocker": str(result.get("status") or "storage_maintenance_not_maintained"),
                "actual_release_bytes": 0,
            }
        else:
            report_result = retain_report_snapshots(
                quest_root=quest_root,
                quest_id=quest_id,
                recorded_at=str(result["recorded_at"]),
                apply=report_retention_apply,
                keep_recent_days=report_retention_keep_recent_days,
                daily_samples=report_retention_daily_samples,
                max_files=report_retention_max_files,
            )
        result["report_retention"] = report_result
        if report_retention_apply and report_result.get("status") in {"applied", "nothing_to_retain"}:
            result["status"] = "maintained"
            result["summary"] = "quest runtime report snapshot retention 已完成。"


def _apply_attempt_evidence_capsules_if_requested(
    *,
    result: dict[str, Any],
    quest_root: Path,
    quest_id: str,
    attempt_evidence_capsules: bool,
    semantic_process_retention: bool,
    semantic_process_retention_apply: bool,
    semantic_retention_max_log_bytes: int,
    semantic_retention_max_raw_bytes: int,
    semantic_retention_keep_failed_raw: bool,
    semantic_retention_max_files: int | None,
) -> None:
    if not (attempt_evidence_capsules or semantic_process_retention):
        return
    apply_allowed = result.get("status") in {"maintained", "blocked_backend_unavailable"}
    capsule_result = materialize_attempt_evidence_capsules(
        quest_root=quest_root,
        quest_id=quest_id,
        recorded_at=str(result["recorded_at"]),
        semantic_process_retention=semantic_process_retention,
        semantic_process_retention_apply=semantic_process_retention_apply,
        semantic_process_retention_apply_allowed=apply_allowed,
        semantic_retention_max_log_bytes=semantic_retention_max_log_bytes,
        semantic_retention_max_raw_bytes=semantic_retention_max_raw_bytes,
        semantic_retention_keep_failed_raw=semantic_retention_keep_failed_raw,
        semantic_retention_max_files=semantic_retention_max_files,
    )
    result.update(capsule_result)
    semantic_result = capsule_result.get("semantic_process_retention")
    if (
        semantic_process_retention_apply
        and isinstance(semantic_result, Mapping)
        and semantic_result.get("status") in {"applied", "nothing_to_retain"}
    ):
        result["status"] = "maintained"
        result["summary"] = "quest runtime semantic process retention 已完成。"


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


def _size_summary(
    quest_root: Path,
    *,
    buckets: Iterable[str] | None = None,
    lightweight_buckets: Iterable[str] | None = None,
) -> dict[str, Any]:
    ds_root = quest_root / ".ds"
    bucket_summaries: dict[str, Any] = {}
    lightweight_bucket_names = {str(bucket) for bucket in (lightweight_buckets or [])}
    for bucket_name in _restore_proof_buckets(buckets):
        bucket_path = ds_root / bucket_name
        if bucket_name in lightweight_bucket_names:
            bucket_summaries[bucket_name] = {
                "path": str(bucket_path),
                "bytes": None,
                "lightweight": True,
                "entry_count": _top_level_entry_count(bucket_path),
            }
        else:
            bucket_summaries[bucket_name] = {
                "path": str(bucket_path),
                "bytes": _directory_size_bytes(bucket_path),
            }
    total_bytes = None if lightweight_bucket_names else _directory_size_bytes(ds_root)
    return {
        "root": str(ds_root),
        "total_bytes": total_bytes,
        "lightweight_buckets": sorted(lightweight_bucket_names),
        "buckets": bucket_summaries,
    }


def _size_summary_skipped(quest_root: Path, *, reason: str) -> dict[str, Any]:
    return {
        "root": str(quest_root / ".ds"),
        "status": "skipped",
        "skip_reason": reason,
        "total_bytes": None,
        "lightweight_buckets": [],
        "buckets": {},
    }


def _top_level_entry_count(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    try:
        return sum(1 for _ in path.iterdir())
    except OSError:
        return 0


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
