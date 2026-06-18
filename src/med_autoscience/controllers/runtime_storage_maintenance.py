from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import study_runtime_resolution
from med_autoscience.controllers.artifact_lifecycle_inventory import build_study_artifact_lifecycle_registry
from med_autoscience.controllers.runtime_storage_maintenance_parts import backend_maintenance
from med_autoscience.controllers.runtime_storage_maintenance_parts import cache_cleanup
from med_autoscience.controllers.runtime_storage_maintenance_parts import git_garbage
from med_autoscience.controllers.runtime_storage_maintenance_parts.authority_boundary import (
    storage_refs_only_adapter_boundary,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.maintenance_authorization import (
    AUTHORIZATION_BLOCKER_STATUS as _STORAGE_AUTHORIZATION_BLOCKER_STATUS,
    AUTHORIZATION_TYPED_BLOCKER as _STORAGE_AUTHORIZATION_TYPED_BLOCKER,
    opl_storage_maintenance_authorization_result,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.quest_root_maintenance import (
    maintain_quest_runtime_storage,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.study_runtime_maintenance import (
    maintain_runtime_storage,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction import (
    archive_refs_from_compaction_result,
    restore_proof_compaction_candidate,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.dataset_retention import (
    audit_dataset_retention as _dataset_retention_audit,
    dataset_release_blockers as _dataset_release_blockers,
    dataset_release_decision as _dataset_release_decision,
    release_checksum as _release_checksum,
    release_rehydrate_verification as _release_rehydrate_verification,
    release_restore_handle as _release_restore_handle,
    superseded_release_index as _superseded_release_index,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import domain_authority_refs_index
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.study_runtime import resolve_study_runtime_paths


SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
_TERMINAL_RUNTIME_STATUSES = frozenset({"completed", "failed", "stopped", "terminated"})
_PRIMARY_BUCKETS = ("bash_exec", "codex_homes", "runs", "codex_history", "worktrees")
_WORKSPACE_STORAGE_MAINTENANCE_SURFACE = "workspace_runtime_storage_maintenance"
_WORKSPACE_STORAGE_MAINTENANCE_OPERATION = "workspace_storage_apply"


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


def _report_root(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_storage_maintenance"


def _latest_report_path(study_root: Path) -> Path:
    return _report_root(study_root) / "latest.json"


def _timestamped_report_path(study_root: Path, recorded_at: str) -> Path:
    return _report_root(study_root) / f"{_artifact_slug(recorded_at)}.json"


def _read_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = study_runtime_resolution._load_yaml_dict(path)
    return payload if isinstance(payload, dict) else {}


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


def _study_artifact_size_summary(study_root: Path) -> dict[str, Any]:
    buckets: dict[str, Any] = {}
    for name in ("artifacts", "manuscript", "paper"):
        path = study_root / name
        buckets[name] = {
            "path": str(path),
            "bytes": _directory_size_bytes(path),
        }
    return {
        "root": str(study_root),
        "total_bytes": sum(int(item["bytes"]) for item in buckets.values()),
        "buckets": buckets,
        "candidate_action": "keep-online",
        "risk": "high_traceability_surface",
        "estimated_release_bytes": 0,
    }


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


def _selected_study_roots(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    all_studies: bool,
) -> list[Path]:
    if study_id:
        return [profile.studies_root / study_id]
    if not all_studies:
        return []
    if not profile.studies_root.exists():
        return []
    return sorted(
        path
        for path in profile.studies_root.iterdir()
        if path.is_dir() and ((path / "study.yaml").exists() or (path / "runtime_binding.yaml").exists())
    )


def _runtime_candidate(
    *,
    quest_root: Path,
    snapshot: Mapping[str, Any],
    size_summary: Mapping[str, Any],
) -> dict[str, Any]:
    status = str(snapshot.get("status") or "").strip().lower()
    active_run_id = snapshot.get("active_run_id")
    if not bool(snapshot.get("quest_exists")):
        return _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="missing_truth_surface",
            candidate_action="blocked-missing-quest",
            estimated_release_bytes=0,
            blockers=["missing_quest_root"],
        )
    if snapshot.get("runtime_state_error"):
        return _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="runtime_state_unreadable",
            candidate_action="audit-only",
            estimated_release_bytes=0,
            blockers=["runtime_state_unreadable"],
        )
    if status in _LIVE_RUNTIME_STATUSES and active_run_id is not None:
        return _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="live_runtime",
            candidate_action="audit-only",
            estimated_release_bytes=0,
            blockers=["live_runtime_active"],
        )
    if status in _TERMINAL_RUNTIME_STATUSES or not active_run_id:
        candidate = _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="process_state_only",
            candidate_action="compress-online",
            estimated_release_bytes=_primary_runtime_bucket_bytes(size_summary),
            blockers=[],
        )
        candidate["secondary_actions"] = ["dedupe-online", "archive-expanded-worktree-runtime"]
        return candidate
    return _runtime_candidate_payload(
        quest_root=quest_root,
        size_summary=size_summary,
        risk="unknown_runtime_state",
        candidate_action="audit-only",
        estimated_release_bytes=0,
        blockers=["unknown_runtime_state"],
    )


def _runtime_candidate_payload(
    *,
    quest_root: Path,
    size_summary: Mapping[str, Any],
    risk: str,
    candidate_action: str,
    estimated_release_bytes: int,
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "category": "runtime",
        "path": str(quest_root),
        "bytes": int(size_summary.get("total_bytes") or 0),
        "risk": risk,
        "candidate_action": candidate_action,
        "estimated_release_bytes": estimated_release_bytes,
        "blockers": blockers,
    }


def _primary_runtime_bucket_bytes(size_summary: Mapping[str, Any]) -> int:
    return sum(
        int(bucket.get("bytes") or 0)
        for name, bucket in dict(size_summary.get("buckets") or {}).items()
        if name in _PRIMARY_BUCKETS
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _git_storage_audit(
    workspace_root: Path,
    *,
    older_than_seconds: int = git_garbage.GIT_TEMP_GARBAGE_MIN_AGE_SECONDS,
    apply: bool = False,
    reinitialize_empty_workspace_git: bool = False,
    retire_workspace_root_git: bool = False,
) -> dict[str, Any]:
    return git_garbage.audit_git_storage(
        workspace_root,
        older_than_seconds=older_than_seconds,
        apply=apply,
        reinitialize_empty_workspace_git=reinitialize_empty_workspace_git,
        retire_workspace_root_git=retire_workspace_root_git,
    )


def _delete_safe_candidates(
    workspace_root: Path,
    *,
    apply: bool = False,
    scan_roots: list[Path] | None = None,
) -> dict[str, Any]:
    return cache_cleanup.delete_safe_candidates(workspace_root, apply=apply, scan_roots=scan_roots)


def _cache_scan_roots(*, workspace_root: Path, scan_roots: list[Path] | None) -> list[Path]:
    return cache_cleanup.cache_scan_roots(workspace_root=workspace_root, scan_roots=scan_roots)


def _empty_cache_apply_result(status: str) -> dict[str, Any]:
    return cache_cleanup.empty_cache_apply_result(status)


def _apply_delete_safe_candidates(
    *,
    workspace_root: Path,
    candidates: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return cache_cleanup.apply_delete_safe_candidates(workspace_root=workspace_root, candidates=candidates)


def _path_is_inside_workspace(path: Path, workspace_root: Path) -> bool:
    return cache_cleanup.path_is_inside_workspace(path, workspace_root)


def _skipped_storage_category(*, category: str, workspace_root: Path, reason: str) -> dict[str, Any]:
    return {
        "category": category,
        "workspace_root": str(workspace_root),
        "bytes": 0,
        "total_bytes": 0,
        "candidate_action": f"skipped-{reason}",
        "estimated_release_bytes": 0,
        "actual_release_bytes": 0,
        "blockers": [reason],
    }


def _actual_release_bytes(before: Mapping[str, Any], after: Mapping[str, Any]) -> int:
    return max(0, int(before.get("total_bytes") or 0) - int(after.get("total_bytes") or 0))


def _restore_proof_actual_release_bytes(apply_result: Mapping[str, Any] | None) -> int:
    if not isinstance(apply_result, Mapping):
        return 0
    compaction = _mapping(apply_result.get("restore_proof_compaction"))
    return int(compaction.get("actual_release_bytes") or 0)


def _retention_actual_release_bytes(apply_result: Mapping[str, Any] | None) -> int:
    if not isinstance(apply_result, Mapping):
        return 0
    archive_retention = _mapping(apply_result.get("archive_retention"))
    report_retention = _mapping(apply_result.get("report_retention"))
    semantic_retention = _mapping(apply_result.get("semantic_process_retention"))
    legacy_codex_homes_retention = _mapping(apply_result.get("legacy_codex_homes_retention"))
    return int(archive_retention.get("actual_release_bytes") or 0) + int(
        report_retention.get("actual_release_bytes") or 0
    ) + int(
        semantic_retention.get("actual_release_bytes") or 0
    ) + int(
        legacy_codex_homes_retention.get("actual_release_bytes") or 0
    )


def _deleted_bytes_from_apply_result(report: Mapping[str, Any]) -> int:
    apply_result = report.get("apply_result")
    deleted_bytes = int(apply_result.get("deleted_bytes") or 0) if isinstance(apply_result, Mapping) else 0
    reinitialize_result = report.get("empty_repo_reinitialize_result")
    reinitialized_bytes = (
        int(reinitialize_result.get("released_bytes") or 0) if isinstance(reinitialize_result, Mapping) else 0
    )
    retirement_result = report.get("workspace_root_git_retirement_result")
    retired_bytes = int(retirement_result.get("released_bytes") or 0) if isinstance(retirement_result, Mapping) else 0
    return deleted_bytes + reinitialized_bytes + retired_bytes


def audit_workspace_storage(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    all_studies: bool = True,
    stopped_only: bool = False,
    apply: bool = False,
    git_only: bool = False,
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
    reinitialize_empty_workspace_git: bool = False,
    retire_workspace_root_git: bool = False,
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
    workspace_root = profile.workspace_root.expanduser().resolve()
    authorization_proof, authorization_blocker = opl_storage_maintenance_authorization_result(
        apply=apply,
        authorization=opl_maintenance_authorization,
        workspace_root=workspace_root,
        operation=_WORKSPACE_STORAGE_MAINTENANCE_OPERATION,
        maintenance_surface=_WORKSPACE_STORAGE_MAINTENANCE_SURFACE,
    )
    if authorization_blocker is not None:
        return _blocked_workspace_storage_audit_report(
            profile=profile,
            workspace_root=workspace_root,
            recorded_at=recorded_at,
            study_id=study_id,
            all_studies=all_studies,
            stopped_only=stopped_only,
            git_only=git_only,
            opl_maintenance_authorization=authorization_proof,
            authorization_blocker=authorization_blocker,
        )
    selected_restore_proof_buckets = _restore_proof_buckets(restore_proof_buckets)
    selected_roots = [] if git_only else _selected_study_roots(profile=profile, study_id=study_id, all_studies=all_studies)
    study_reports: list[dict[str, Any]] = []
    runtime_total_bytes = 0
    runtime_estimated_release_bytes = 0
    runtime_actual_release_bytes = 0
    artifact_total_bytes = 0
    cache_scan_roots: list[Path] | None = [] if study_id and not git_only else None
    for selected_study_root in selected_roots:
        try:
            resolved_study_id, resolved_study_root, study_payload = study_runtime_resolution._resolve_study(
                profile=profile,
                study_id=selected_study_root.name,
                study_root=None,
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
            quest_root = Path(runtime_paths["quest_root"]).expanduser().resolve()
            if cache_scan_roots is not None:
                cache_scan_roots.extend([resolved_study_root, quest_root])
            snapshot = _quest_runtime_snapshot(quest_root)
            lightweight_buckets = selected_restore_proof_buckets if restore_proof_compaction or restore_proof_canary else ()
            size_before = (
                _size_summary_skipped(quest_root, reason="refs_only_state_index_only")
                if refs_only_state_index_only
                else _size_summary(
                    quest_root,
                    buckets=selected_restore_proof_buckets,
                    lightweight_buckets=lightweight_buckets,
                )
            )
            candidate = _runtime_candidate(quest_root=quest_root, snapshot=snapshot, size_summary=size_before)
            if restore_proof_compaction:
                candidate = restore_proof_compaction_candidate(
                    candidate=candidate,
                    snapshot=snapshot,
                    include_parked_controller_stop=include_parked_controller_stop,
                    include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
                )
            if restore_proof_canary:
                candidate["restore_proof_canary"] = {
                    "enabled": True,
                    "entry_limit_per_bucket": int(restore_proof_canary_entry_limit),
                    "source_retained": True,
                    "actual_release_bytes": 0,
                }
            if stopped_only and str(snapshot.get("status") or "") not in _TERMINAL_RUNTIME_STATUSES:
                runtime_report = dict(candidate)
                if apply:
                    runtime_report["estimated_release_bytes"] = 0
                runtime_report["actual_release_bytes"] = 0
                study_reports.append(
                    {
                        "study_id": resolved_study_id,
                        "study_root": str(resolved_study_root),
                        "quest_id": quest_id,
                        "quest_root": str(quest_root),
                        "status": "skipped_stopped_only",
                        "quest_runtime": snapshot,
                        "runtime": runtime_report,
                        "actual_runtime_release_bytes": 0,
                    }
                )
                continue
            apply_result: dict[str, Any] | None = None
            if apply:
                apply_result = maintain_runtime_storage(
                    profile=profile,
                    study_id=resolved_study_id,
                    study_root=None,
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
                    restore_proof_buckets=selected_restore_proof_buckets,
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
                    attempt_evidence_capsules=attempt_evidence_capsules,
                    semantic_process_retention=semantic_process_retention,
                    semantic_process_retention_apply=semantic_process_retention_apply,
                    semantic_retention_max_log_bytes=semantic_retention_max_log_bytes,
                    semantic_retention_max_raw_bytes=semantic_retention_max_raw_bytes,
                    semantic_retention_keep_failed_raw=semantic_retention_keep_failed_raw,
                    semantic_retention_max_files=semantic_retention_max_files,
                    opl_maintenance_authorization=opl_maintenance_authorization,
                )
                workspace_archive_index = _record_workspace_archive_ref(
                    workspace_root=workspace_root,
                    quest_root=quest_root,
                    apply_result=apply_result,
                )
                if workspace_archive_index:
                    apply_result["runtime_lifecycle_workspace_archive_index"] = workspace_archive_index
            size_after = (
                _size_summary_skipped(quest_root, reason="refs_only_state_index_only")
                if refs_only_state_index_only
                else _size_summary(
                    quest_root,
                    buckets=selected_restore_proof_buckets,
                    lightweight_buckets=lightweight_buckets,
                )
            )
            actual_runtime_release_bytes = (
                _restore_proof_actual_release_bytes(apply_result)
                if apply and restore_proof_compaction
                else _retention_actual_release_bytes(apply_result)
                if apply and (archive_retention or report_retention or semantic_process_retention)
                else _actual_release_bytes(size_before, size_after)
                if apply
                else 0
            )
            runtime_report = dict(candidate)
            runtime_estimated_release_bytes_for_report = (
                actual_runtime_release_bytes
                if apply
                else int(candidate.get("estimated_release_bytes") or 0)
            )
            runtime_report["estimated_release_bytes"] = runtime_estimated_release_bytes_for_report
            runtime_report["actual_release_bytes"] = actual_runtime_release_bytes
            artifact_summary = _study_artifact_size_summary(resolved_study_root)
            artifact_lifecycle_registry = build_study_artifact_lifecycle_registry(
                study_root=resolved_study_root,
                workspace_root=workspace_root,
                quest_root=quest_root,
                runtime_status=snapshot,
            )
            runtime_total_bytes += int(size_before.get("total_bytes") or 0)
            runtime_estimated_release_bytes += runtime_estimated_release_bytes_for_report
            runtime_actual_release_bytes += actual_runtime_release_bytes
            artifact_total_bytes += int(artifact_summary.get("total_bytes") or 0)
            study_reports.append(
                {
                    "study_id": resolved_study_id,
                    "study_root": str(resolved_study_root),
                    "quest_id": quest_id,
                    "quest_root": str(quest_root),
                    "status": "applied" if apply_result and apply_result.get("status") == "maintained" else "audited",
                    "quest_runtime": snapshot,
                    "runtime": runtime_report,
                    "artifact_lifecycle_registry": artifact_lifecycle_registry,
                    "size_before": size_before,
                    "size_after": size_after,
                    "study_artifacts": artifact_summary,
                    "apply_result": apply_result,
                    "restore_proof_compaction": _mapping(apply_result.get("restore_proof_compaction"))
                    if isinstance(apply_result, Mapping)
                    else {},
                    "actual_runtime_release_bytes": actual_runtime_release_bytes,
                }
            )
        except Exception as exc:
            if cache_scan_roots is not None:
                cache_scan_roots.append(selected_study_root)
            study_reports.append(
                {
                    "study_root": str(selected_study_root),
                    "status": "blocked_study_resolution_failed",
                    "error": str(exc),
                }
            )

    dataset_report = (
        _skipped_storage_category(category="dataset", workspace_root=workspace_root, reason="git_only")
        if git_only
        else _dataset_retention_audit(workspace_root)
    )
    git_report = _git_storage_audit(
        workspace_root,
        older_than_seconds=older_than_seconds,
        apply=apply,
        reinitialize_empty_workspace_git=reinitialize_empty_workspace_git,
        retire_workspace_root_git=retire_workspace_root_git,
    )
    git_report["actual_release_bytes"] = _deleted_bytes_from_apply_result(git_report)
    cache_report = (
        _skipped_storage_category(category="cache", workspace_root=workspace_root, reason="git_only")
        if git_only
        else _delete_safe_candidates(workspace_root, apply=apply, scan_roots=cache_scan_roots)
    )
    cache_actual_release_bytes = int(cache_report.get("actual_release_bytes") or 0)
    dataset_estimated_release_bytes = int(dataset_report.get("estimated_release_bytes") or 0)
    estimated_release_bytes = (
        runtime_estimated_release_bytes
        + (0 if apply else dataset_estimated_release_bytes)
        + int(git_report.get("estimated_release_bytes") or 0)
        + int(cache_report.get("estimated_release_bytes") or 0)
    )
    actual_release_bytes = (
        runtime_actual_release_bytes
        + int(git_report.get("actual_release_bytes") or 0)
        + cache_actual_release_bytes
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "profile_name": profile.name,
        "workspace_root": str(workspace_root),
        "mode": "apply" if apply else "dry-run",
        "storage_refs_only_adapter_boundary": storage_refs_only_adapter_boundary(
            report_mode="workspace_storage_audit",
        ),
        "opl_maintenance_authorization": authorization_proof,
        "selection": {
            "study_id": study_id,
            "all_studies": all_studies,
            "stopped_only": stopped_only,
            "allow_live_runtime": allow_live_runtime,
            "restore_proof_compaction": restore_proof_compaction,
            "restore_proof_max_shards": restore_proof_max_shards,
            "include_parked_controller_stop": include_parked_controller_stop,
            "include_operator_confirmed_parked_active": include_operator_confirmed_parked_active,
            "restore_proof_buckets": list(selected_restore_proof_buckets),
            "git_only": git_only,
            "reinitialize_empty_workspace_git": reinitialize_empty_workspace_git,
            "retire_workspace_root_git": retire_workspace_root_git,
            "refs_only_state_index_pilot": refs_only_state_index_pilot,
            "archive_retention": archive_retention,
            "archive_retention_apply": archive_retention_apply,
            "archive_retention_min_mb": archive_retention_min_mb,
            "archive_retention_cold_store_root": str(archive_retention_cold_store_root)
            if archive_retention_cold_store_root
            else None,
            "report_retention": report_retention,
            "report_retention_apply": report_retention_apply,
            "report_retention_keep_recent_days": report_retention_keep_recent_days,
            "report_retention_daily_samples": report_retention_daily_samples,
            "report_retention_max_files": report_retention_max_files,
            "attempt_evidence_capsules": attempt_evidence_capsules,
            "semantic_process_retention": semantic_process_retention,
            "semantic_process_retention_apply": semantic_process_retention_apply,
            "semantic_retention_max_log_bytes": semantic_retention_max_log_bytes,
            "semantic_retention_max_raw_bytes": semantic_retention_max_raw_bytes,
            "semantic_retention_keep_failed_raw": semantic_retention_keep_failed_raw,
            "semantic_retention_max_files": semantic_retention_max_files,
        },
        "summary": {
            "study_count": len(study_reports),
            "estimated_release_bytes": estimated_release_bytes,
            "actual_release_bytes": actual_release_bytes,
            "runtime_total_bytes": runtime_total_bytes,
            "runtime_estimated_release_bytes": runtime_estimated_release_bytes,
            "runtime_actual_release_bytes": runtime_actual_release_bytes,
            "dataset_total_bytes": dataset_report["total_bytes"],
            "dataset_archive_offline_candidate_bytes": dataset_report["estimated_release_bytes"],
            "cache_delete_safe_bytes": cache_report["estimated_release_bytes"],
            "cache_actual_release_bytes": cache_actual_release_bytes,
            "git_actual_release_bytes": int(git_report.get("actual_release_bytes") or 0),
            "study_artifact_total_bytes": artifact_total_bytes,
        },
        "categories": {
            "runtime": {
                "category": "runtime",
                "bytes": runtime_total_bytes,
                "candidate_action": "skipped-git-only" if git_only else "compress-online",
                "estimated_release_bytes": runtime_estimated_release_bytes,
                "actual_release_bytes": runtime_actual_release_bytes,
                "actual_runtime_release_bytes": runtime_actual_release_bytes,
                "studies": study_reports,
            },
            "dataset": dataset_report,
            "git": git_report,
            "cache": cache_report,
            "study_artifact": {
                "category": "study_artifact",
                "bytes": artifact_total_bytes,
                "candidate_action": "keep-online",
                "estimated_release_bytes": 0,
            },
        },
    }
    audit_root = workspace_root / "storage_audit"
    report_path = audit_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = audit_root / "latest.json"
    report["report_path"] = str(report_path)
    report["latest_report_path"] = str(latest_path)
    _write_json(report_path, report)
    _write_json(latest_path, report)
    return report


def _blocked_workspace_storage_audit_report(
    *,
    profile: WorkspaceProfile,
    workspace_root: Path,
    recorded_at: str,
    study_id: str | None,
    all_studies: bool,
    stopped_only: bool,
    git_only: bool,
    opl_maintenance_authorization: Mapping[str, Any],
    authorization_blocker: Mapping[str, Any],
) -> dict[str, Any]:
    report_path = _timestamped_workspace_storage_report_path(workspace_root, recorded_at)
    latest_path = _latest_workspace_storage_report_path(workspace_root)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_storage_audit",
        "recorded_at": recorded_at,
        "profile_name": profile.name,
        "workspace_root": str(workspace_root),
        "mode": "apply",
        "status": _STORAGE_AUTHORIZATION_BLOCKER_STATUS,
        "typed_blocker": _STORAGE_AUTHORIZATION_TYPED_BLOCKER,
        "stable_blocker": True,
        "owner": "one-person-lab",
        "mas_role": "maintenance_callable_adapter",
        "storage_refs_only_adapter_boundary": storage_refs_only_adapter_boundary(
            report_mode="workspace_storage_audit",
        ),
        "opl_maintenance_authorization": dict(opl_maintenance_authorization),
        "blockers": [dict(authorization_blocker)],
        "selection": {
            "study_id": study_id,
            "all_studies": all_studies,
            "stopped_only": stopped_only,
            "git_only": git_only,
        },
        "summary": {
            "study_count": 0,
            "estimated_release_bytes": 0,
            "actual_release_bytes": 0,
            "runtime_total_bytes": 0,
            "runtime_estimated_release_bytes": 0,
            "runtime_actual_release_bytes": 0,
            "dataset_total_bytes": 0,
            "dataset_archive_offline_candidate_bytes": 0,
            "cache_delete_safe_bytes": 0,
            "cache_actual_release_bytes": 0,
            "git_actual_release_bytes": 0,
            "study_artifact_total_bytes": 0,
        },
        "categories": {
            "runtime": _blocked_storage_category(category="runtime", workspace_root=workspace_root),
            "dataset": _blocked_storage_category(category="dataset", workspace_root=workspace_root),
            "git": _blocked_storage_category(category="git", workspace_root=workspace_root),
            "cache": _blocked_storage_category(category="cache", workspace_root=workspace_root),
            "study_artifact": _blocked_storage_category(category="study_artifact", workspace_root=workspace_root),
        },
        "report_path": str(report_path),
        "latest_report_path": str(latest_path),
    }
    _write_json(report_path, report)
    _write_json(latest_path, report)
    return report


def _blocked_storage_category(*, category: str, workspace_root: Path) -> dict[str, Any]:
    return {
        "category": category,
        "workspace_root": str(workspace_root),
        "bytes": 0,
        "total_bytes": 0,
        "candidate_action": "blocked-opl-runtime-storage-maintenance-authorization-required",
        "estimated_release_bytes": 0,
        "actual_release_bytes": 0,
        "blockers": [_STORAGE_AUTHORIZATION_TYPED_BLOCKER],
    }


def _timestamped_workspace_storage_report_path(workspace_root: Path, recorded_at: str) -> Path:
    return workspace_root / "storage_audit" / f"{_artifact_slug(recorded_at)}.json"


def _latest_workspace_storage_report_path(workspace_root: Path) -> Path:
    return workspace_root / "storage_audit" / "latest.json"


def _record_workspace_archive_ref(
    *,
    workspace_root: Path,
    quest_root: Path,
    apply_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(apply_result, Mapping):
        return {}
    compaction = _mapping(apply_result.get("restore_proof_compaction"))
    archive_refs = _archive_refs_from_compaction(compaction)
    if not archive_refs:
        return {}
    indexed_results = [
        domain_authority_refs_index.record_archive_ref(
            quest_root=quest_root,
            archive_ref=archive_ref,
            db_path=domain_authority_refs_index.workspace_authority_refs_index_path(workspace_root),
        )
        for archive_ref in archive_refs
    ]
    return _archive_ref_index_summary(indexed_results)


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
