from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import paper_work_unit_lifecycle_for_action
from med_autoscience.runtime_control import repeat_suppression
from med_autoscience.runtime_protocol import domain_authority_refs_index

from . import runtime_dispatch_cost, domain_status_projection, progress_first_blocker_budget
from .default_executor_stage_log import paper_stage_log_for_default_executor_execution
from .domain_owner_action_dispatch_parts import action_execution
from .domain_owner_action_dispatch_parts import action_router
from .domain_owner_action_dispatch_parts import controller_refresh
from .domain_owner_action_dispatch_parts import dispatch_contract
from .domain_owner_action_dispatch_parts import output_readiness
from .domain_owner_action_dispatch_parts import paper_progress_stall_diagnostic
from .domain_owner_action_dispatch_parts import persisted_dispatches
from .domain_owner_action_dispatch_parts import record_only_handoff
from .domain_action_request_materializer import (
    CONSUMER_LATEST_RELATIVE_PATH,
    DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
    FORBIDDEN_SURFACES,
    SUPPORTED_MODE,
)
from .default_executor_action_policy import SUPPORTED_ACTION_TYPES


SCHEMA_VERSION = 1
EXECUTION_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_execution")
EXECUTION_LATEST_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "latest.json"
EXECUTION_HISTORY_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "history.jsonl"
EXECUTION_LEDGER_LIMIT = 80
SUPERVISION_LATEST_RELATIVE_PATH = persisted_dispatches.SUPERVISION_LATEST_RELATIVE_PATH


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _dispatch_dir(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT


def _consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def _execution_latest_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / EXECUTION_LATEST_RELATIVE_PATH


def _execution_history_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / EXECUTION_HISTORY_RELATIVE_PATH


def _execution_identity(execution: Mapping[str, Any]) -> str:
    return (
        _text(execution.get("execution_id"))
        or "::".join(
            item
            for item in (
                _text(execution.get("action_type")),
                _text(execution.get("idempotency_key")),
                _text(execution.get("generated_at")),
            )
            if item
        )
        or json.dumps(dict(execution), ensure_ascii=False, sort_keys=True)
    )


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _merged_execution_ledger(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_executions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for execution in [
        *_mapping_list(_mapping(previous_payload).get("execution_ledger")),
        *_mapping_list(_mapping(previous_payload).get("executions")),
        *study_executions,
    ]:
        merged[_execution_identity(execution)] = dict(execution)
    return list(merged.values())[-EXECUTION_LEDGER_LIMIT:]


def _dispatches(
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    *,
    consumer_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return persisted_dispatches.selected_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=action_types,
        consumer_payload=consumer_payload,
        consumer_latest_path=_consumer_latest_path(profile),
        scan_payload=persisted_dispatches.scan_latest_payload(profile),
        supported_action_types=SUPPORTED_ACTION_TYPES,
        dispatch_relative_root=DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
    )


def _dispatch_path(dispatch: Mapping[str, Any]) -> Path:
    path_text = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    if path_text is None:
        return Path("<consumer-latest-inline-dispatch>")
    return Path(path_text).expanduser().resolve()


def _resolve_study_ids(
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    *,
    consumer_payload: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    if not profile.studies_root.is_dir():
        return ()
    resolved: list[str] = []
    latest = dict(consumer_payload) if consumer_payload is not None else (_read_json_object(_consumer_latest_path(profile)) or {})
    for dispatch in latest.get("default_executor_dispatches") or []:
        if isinstance(dispatch, Mapping) and (study_id := _text(dispatch.get("study_id"))) is not None:
            resolved.append(study_id)
    for dispatch_dir in sorted(
        profile.studies_root.glob(f"*/{DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT.as_posix()}"),
        key=lambda item: item.as_posix(),
    ):
        try:
            study_id = dispatch_dir.relative_to(profile.studies_root).parts[0]
        except (ValueError, IndexError):
            continue
        if any(dispatch_dir.glob("*.json")):
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _contract_guard(dispatch: Mapping[str, Any]) -> tuple[bool, str | None]:
    dispatch_error = _dispatch_contract_error(dispatch)
    if dispatch_error is not None:
        return False, dispatch_error
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if not prompt_contract:
        return False, "prompt_contract_missing"
    prompt_contract_error = _prompt_contract_error(
        prompt_contract,
        dispatch_authority=_text(dispatch.get("dispatch_authority")),
    )
    if prompt_contract_error is not None:
        return False, prompt_contract_error
    return True, None


def _dispatch_contract_error(dispatch: Mapping[str, Any]) -> str | None:
    if _text(dispatch.get("surface")) != "default_executor_dispatch_request":
        return "unsupported_dispatch_surface"
    if _text(dispatch.get("dispatch_status")) != "ready":
        return "dispatch_not_ready"
    if _text(dispatch.get("executor_kind")) != "codex_cli_default":
        return "unsupported_executor_kind"
    if dispatch.get("chat_completion_only_executor_forbidden") is not True:
        return "chat_completion_only_guard_missing"
    action_type = _text(dispatch.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return "unsupported_action_type"
    return None


def _executor_boundary(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "adapter_owner": "med-autoscience",
        "executor_requirement_owner": "one-person-lab",
        "mas_executor_adapter_policy": "codex_cli_default_only",
        "supported_executor_kind": "codex_cli_default",
        "default_executor_kind": "codex_cli_default",
        "received_executor_kind": _text(dispatch.get("executor_kind")),
        "unsupported_executor_policy": "fail_closed",
        "local_codex_cli_scope": "standalone_diagnostics_only",
        "external_executor_opt_in_owner": "one-person-lab",
        "external_executor_opt_in_policy": "typed_closeout_or_domain_task_receipt_only",
        "mas_owned_hermes_or_claude_executor": False,
    }


def _prompt_contract_error(prompt_contract: Mapping[str, Any], *, dispatch_authority: str | None) -> str | None:
    return dispatch_contract.prompt_contract_error(
        prompt_contract,
        forbidden_surfaces=FORBIDDEN_SURFACES,
        dispatch_authority=dispatch_authority,
    )


def _current_owner_route(
    profile: WorkspaceProfile,
    study_id: str,
    *,
    dispatch: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    return persisted_dispatches.current_owner_route_from_scan_payload(
        scan_payload=persisted_dispatches.scan_latest_payload(profile),
        study_id=study_id,
        dispatch=dispatch,
    )


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _owner_route_block_reason(*, dispatch: Mapping[str, Any], current_route: Mapping[str, Any] | None) -> str | None:
    if not _dispatch_owner_route(dispatch):
        return "owner_route_missing"
    if current_route is None:
        return "current_owner_route_missing"
    if not owner_route_part.owner_route_matches(dispatch=dispatch, current_route=current_route):
        return "owner_route_stale"
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=current_route):
        return "owner_route_next_owner_mismatch"
    if not owner_route_attempt_protocol.route_protocol_dispatchable(
        current_route,
        action_type=_text(dispatch.get("action_type")),
    ):
        return "owner_route_currentness_basis_missing"
    return None


def _execution_owner_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    bridged_route = persisted_dispatches.bridged_quality_repair_writer_handoff_route(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        bridged_route is not None
        and _owner_route_block_reason(dispatch=dispatch, current_route=bridged_route) is None
    ):
        return bridged_route, "bridged_writer_handoff"
    publication_owner_bridge_route = persisted_dispatches.bridged_publication_owner_materialization_route(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        publication_owner_bridge_route is not None
        and _owner_route_block_reason(dispatch=dispatch, current_route=publication_owner_bridge_route) is None
        ):
            return publication_owner_bridge_route, "bridged_publication_owner_materialization"
    if not _dispatch_uses_bridge_authority(dispatch):
        scan_route, scan_route_basis = _current_owner_route(profile, study_id, dispatch=dispatch)
        route_block_reason = _owner_route_block_reason(dispatch=dispatch, current_route=scan_route)
        if scan_route_basis != "dispatch_owner_route" and route_block_reason is None:
            return scan_route, scan_route_basis or "scan_latest"
        live_attempt_route = persisted_dispatches.live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=persisted_dispatches.scan_latest_payload(profile),
            study_id=study_id,
            dispatch=dispatch,
        )
        if (
            live_attempt_route is not None
            and _owner_route_block_reason(dispatch=dispatch, current_route=live_attempt_route) is None
        ):
            return live_attempt_route, "live_provider_attempt_dispatch"
    request_route = persisted_dispatches.owner_request_route(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    )
    if request_route is not None:
        return request_route, "owner_request"
    if _dispatch_uses_bridge_authority(dispatch):
        return None, "bridge_currentness_failed"
    scan_route, scan_route_basis = _current_owner_route(profile, study_id, dispatch=dispatch)
    route_block_reason = _owner_route_block_reason(dispatch=dispatch, current_route=scan_route)
    if scan_route_basis != "dispatch_owner_route" and route_block_reason is None:
        return scan_route, scan_route_basis or "scan_latest"
    live_attempt_route = persisted_dispatches.live_provider_attempt_owner_route_from_scan_payload(
        scan_payload=persisted_dispatches.scan_latest_payload(profile),
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        live_attempt_route is not None
        and _owner_route_block_reason(dispatch=dispatch, current_route=live_attempt_route) is None
    ):
        return live_attempt_route, "live_provider_attempt_dispatch"
    return scan_route, scan_route_basis or "scan_latest"


def _dispatch_uses_bridge_authority(dispatch: Mapping[str, Any]) -> bool:
    route = _dispatch_owner_route(dispatch)
    refs = _mapping(route.get("source_refs"))
    return _text(refs.get("bridge_authority")) is not None


def _progress_first_closeout_block_reason(dispatch: Mapping[str, Any]) -> str | None:
    admission = _mapping(dispatch.get("progress_first_closeout_admission"))
    if _text(admission.get("admission_status")) != "blocked":
        return None
    return _text(admission.get("blocked_reason")) or "closeout_required_before_new_default_executor_task"


def _progress_first_typed_blocker(
    *,
    dispatch: Mapping[str, Any],
    execution: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any] | None:
    admission = _mapping(dispatch.get("progress_first_closeout_admission"))
    source = _mapping(admission.get("typed_blocker"))
    if not source and _text(admission.get("blocked_reason")) is None:
        return None
    owner_route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(owner_route.get("source_refs"))
    return progress_first_blocker_budget.enrich_typed_blocker(
        source
        or {
            "reason": _text(admission.get("blocked_reason")),
            "next_owner": _text(owner_route.get("next_owner")),
        },
        study_id=_text(dispatch.get("study_id")) or "unknown-study",
        work_unit_id=_text(source_refs.get("work_unit_id")) or _text(owner_route.get("work_unit_id")) or "unknown_work_unit",
        eval_id=_text(source_refs.get("source_eval_id")) or _text(dispatch.get("source_eval_id")),
        source_fingerprint=_text(owner_route.get("source_fingerprint")) or _text(dispatch.get("source_fingerprint")),
        repeat_count=_repeat_count(execution),
        first_seen=generated_at,
        last_seen=generated_at,
        deliverable_progress_delta=_mapping(
            execution.get("deliverable_progress_delta")
            or execution.get("paper_progress_delta")
        ),
        paper_progress_delta=_mapping(execution.get("paper_progress_delta")),
        platform_repair_delta=_mapping(execution.get("platform_repair_delta")),
        no_forbidden_write_refs=list(dispatch.get("forbidden_surfaces") or []),
    )


def _repeat_count(execution: Mapping[str, Any]) -> int:
    value = execution.get("repeat_count")
    if isinstance(value, bool) or value is None:
        return 1
    if isinstance(value, int):
        return max(1, value)
    if isinstance(value, float):
        return max(1, int(value))
    return 1


def _execute_publication_gate_specificity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return action_execution.execute_publication_gate_specificity(profile=profile, study_id=study_id, apply=apply)


def _execute_ai_reviewer_workflow(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return action_execution.execute_ai_reviewer_workflow(
        profile=profile,
        study_id=study_id,
        apply=apply,
        dispatch=dispatch,
        controller_decision_refresh=_refresh_controller_decision_after_ai_reviewer_eval,
    )


def _refresh_controller_decision_after_ai_reviewer_eval(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    apply: bool = True,
    source: str = "ai_reviewer_publication_eval_workflow",
) -> dict[str, Any]:
    return controller_refresh.refresh_controller_decision_after_ai_reviewer_eval(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        apply=apply,
        source=source,
    )


def refresh_controller_decisions_for_current_publication_eval(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="controller_decision_refresh",
    )
    developer_mode_payload = developer_mode.to_dict()
    if apply and (
        _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE
        or developer_mode_payload.get("safe_actions_enabled") is not True
    ):
        return {
            "surface": "domain_owner_action_controller_decision_refresh",
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "workspace_root": str(profile.workspace_root),
            "dry_run": False,
            "requested_mode": mode,
            "effective_mode": developer_mode.mode,
            "developer_supervisor_mode": developer_mode_payload,
            "refresh_count": 0,
            "materialized_count": 0,
            "blocked_count": 1,
            "skipped_count": 0,
            "refreshes": [
                {
                    "refresh_status": "blocked",
                    "blocked_reason": _github_block_reason(developer_mode_payload) or "developer_apply_safe_required",
                }
            ],
        }
    resolved_study_ids = _resolve_study_ids(profile, study_ids)
    refreshes = [
        {
            "study_id": study_id,
            **_refresh_controller_decision_after_ai_reviewer_eval(
                profile=profile,
                study_id=study_id,
                study_root=_study_root(profile, study_id),
                apply=apply,
                source="domain_owner_action_controller_decision_refresh",
            ),
        }
        for study_id in resolved_study_ids
    ]
    return {
        "surface": "domain_owner_action_controller_decision_refresh",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "requested_studies": list(resolved_study_ids),
        "refresh_count": len(refreshes),
        "materialized_count": sum(item.get("refresh_status") == "materialized" for item in refreshes),
        "blocked_count": sum(item.get("refresh_status") == "blocked" for item in refreshes),
        "skipped_count": sum(item.get("refresh_status") == "skipped" for item in refreshes),
        "dry_run_count": sum(item.get("refresh_status") == "dry_run" for item in refreshes),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "refreshes": refreshes,
    }


def _execute_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch_payload: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    dispatch = _mapping(dispatch_payload)
    dispatch_path = _dispatch_path(dispatch)
    if not dispatch:
        return {
            "generated_at": generated_at,
            "study_id": study_id,
            "dispatch_path": str(dispatch_path),
            "execution_status": "blocked",
            "blocked_reason": "dispatch_payload_missing_or_invalid",
        }
    dispatch = record_only_handoff.canonical_record_only_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    action_type = _text(dispatch.get("action_type")) or "unknown_action"
    action_fingerprint = runtime_dispatch_cost.dispatch_action_fingerprint(
        dispatch=dispatch,
        dispatch_path=dispatch_path,
    )
    guard_ok, guard_reason = _contract_guard(dispatch)
    current_route, owner_route_basis = _execution_owner_route(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    )
    owner_route_block_reason = _owner_route_block_reason(dispatch=dispatch, current_route=current_route)
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    current_study = persisted_dispatches.current_scan_study(profile=profile, study_id=study_id)
    required_output_pending = output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        current_study=current_study,
    )
    stall_diagnostic = paper_progress_stall_diagnostic.diagnostic(
        action_type=action_type,
        dispatch=dispatch,
        current_study=current_study,
        current_route=current_route,
        required_output_pending=required_output_pending,
    )
    stall_block_reason, stall_handoff_allowed = paper_progress_stall_diagnostic.block_from_diagnostic(stall_diagnostic)
    repeat_guard = repeat_suppression.execution_repeat_suppression(
        dispatch={**dict(dispatch), "owner_route": _dispatch_owner_route(dispatch), "prompt_contract": prompt_contract},
        current_study=current_study,
        previous_execution_latest=_read_json_object(_execution_latest_path(profile, study_id)),
        required_output_pending=required_output_pending,
    )
    closeout_block_reason = _progress_first_closeout_block_reason(dispatch)
    execution = _dispatch_pre_execution_block(
        guard_ok=guard_ok,
        guard_reason=guard_reason,
        owner_route_block_reason=owner_route_block_reason,
        current_route=current_route,
        stall_block_reason=stall_block_reason,
        closeout_block_reason=closeout_block_reason,
        repeat_guard=repeat_guard,
        dispatch=dispatch,
        developer_mode_payload=developer_mode_payload,
        apply=apply,
    ) or _execute_owner_dispatch_action(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
        apply=apply,
    )
    action_cost = runtime_dispatch_cost.executor_action_cost(
        action_type=action_type,
        apply=apply,
        execution=execution,
        action_fingerprint=action_fingerprint,
    )
    return _dispatch_execution_payload(
        profile=profile,
        generated_at=generated_at,
        study_id=study_id,
        dispatch_path=dispatch_path,
        dispatch=dispatch,
        action_type=action_type,
        guard_ok=guard_ok,
        guard_reason=guard_reason,
        current_route=current_route,
        owner_route_basis=owner_route_basis,
        owner_route_block_reason=owner_route_block_reason,
        prompt_contract=prompt_contract,
        repeat_guard=repeat_guard,
        action_fingerprint=action_fingerprint,
        action_cost=action_cost,
        stall_handoff_allowed=stall_handoff_allowed,
        stall_diagnostic=stall_diagnostic,
        apply=apply,
        developer_mode_payload=developer_mode_payload,
        execution=execution,
    )

def _dispatch_pre_execution_block(
    *,
    guard_ok: bool,
    guard_reason: str | None,
    owner_route_block_reason: str | None,
    current_route: Mapping[str, Any] | None,
    stall_block_reason: str | None,
    closeout_block_reason: str | None,
    repeat_guard: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any] | None:
    if not guard_ok:
        return {
            "execution_status": "blocked",
            "blocked_reason": guard_reason,
            "owner_callable_surface": None,
        }
    if owner_route_block_reason is not None:
        return {
            "execution_status": "blocked",
            "blocked_reason": owner_route_block_reason,
            "owner_callable_surface": None,
            "owner_route_current": False,
            "current_owner_route": current_route,
        }
    if stall_block_reason is not None:
        return {
            "execution_status": "blocked",
            "blocked_reason": stall_block_reason,
            "owner_callable_surface": None,
            "paper_progress_stall_current": False,
        }
    if closeout_block_reason is not None:
        return {
            "execution_status": "blocked",
            "blocked_reason": closeout_block_reason,
            "owner_callable_surface": None,
            "progress_first_closeout_required": True,
        }
    if repeat_guard["repeat_suppressed"]:
        anti_loop_budget = _mapping(repeat_guard.get("anti_loop_budget"))
        if anti_loop_budget:
            blocker_reason = _text(anti_loop_budget.get("blocker_reason")) or repeat_suppression.ANTI_LOOP_BUDGET_EXHAUSTED_REASON
            return {
                "execution_status": "repeat_suppressed",
                "blocked_reason": repeat_suppression.ANTI_LOOP_BUDGET_EXHAUSTED_REASON,
                "owner_callable_surface": None,
                "repeat_suppressed": True,
                "why_not_applied": repeat_suppression.ANTI_LOOP_BUDGET_EXHAUSTED_REASON,
                "typed_blocker": {
                    "blocker_id": blocker_reason,
                    "owner": "one-person-lab",
                    "write_permitted": False,
                    "escalation_route": _text(anti_loop_budget.get("escalation_route")),
                },
                "anti_loop_budget": dict(anti_loop_budget),
            }
        return {
            "execution_status": "repeat_suppressed",
            "blocked_reason": repeat_suppression.REPEAT_SUPPRESSED_REASON,
            "owner_callable_surface": None,
            "repeat_suppressed": True,
            "why_not_applied": repeat_suppression.REPEAT_SUPPRESSED_REASON,
        }
    if apply and (
        _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE
        or developer_mode_payload.get("safe_actions_enabled") is not True
    ):
        return {
            "execution_status": "blocked",
            "blocked_reason": _github_block_reason(developer_mode_payload) or "developer_apply_safe_required",
            "owner_callable_surface": None,
        }
    return None


def _execute_owner_dispatch_action(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    return action_router.execute_owner_dispatch_action(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
        apply=apply,
        execute_publication_gate_specificity=_execute_publication_gate_specificity,
        execute_ai_reviewer_workflow=_execute_ai_reviewer_workflow,
        quest_root_resolver=action_execution.quest_root_from_status,
    )


def _dispatch_execution_payload(
    *,
    profile: WorkspaceProfile,
    generated_at: str,
    study_id: str,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
    action_type: str,
    guard_ok: bool,
    guard_reason: str | None,
    current_route: Mapping[str, Any] | None,
    owner_route_basis: str | None,
    owner_route_block_reason: str | None,
    prompt_contract: Mapping[str, Any],
    repeat_guard: Mapping[str, Any],
    action_fingerprint: str,
    action_cost: Mapping[str, Any],
    stall_handoff_allowed: bool,
    stall_diagnostic: Mapping[str, Any],
    apply: bool,
    developer_mode_payload: Mapping[str, Any],
    execution: Mapping[str, Any],
    ) -> dict[str, Any]:
    paper_work_unit_lifecycle = paper_work_unit_lifecycle_for_action(action_type)
    execution_payload = {
        "surface": "default_executor_dispatch_execution",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")),
        "action_type": action_type,
        "action_id": _text(dispatch.get("action_id")),
        "execution_id": f"execution::{study_id}::{action_type}::{generated_at}",
        "next_executable_owner": _text(dispatch.get("next_executable_owner")),
        "required_output_surface": _text(dispatch.get("required_output_surface")),
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")) or "consumer_default_executor_dispatch",
        "dispatch_contract_valid": guard_ok,
        "dispatch_contract_blocked_reason": guard_reason,
        "executor_boundary": _executor_boundary(dispatch),
        "owner_route": _dispatch_owner_route(dispatch) or None,
        "owner_route_current": owner_route_block_reason is None if guard_ok else None,
        "owner_route_basis": owner_route_basis,
        "current_owner_route": current_route,
        "prompt_contract": prompt_contract or None,
        "paper_progress_stall": _mapping(dispatch.get("paper_progress_stall"))
        or _mapping(prompt_contract.get("paper_progress_stall"))
        or None,
        "current_paper_progress_stall": persisted_dispatches.current_scan_stall(profile=profile, study_id=study_id) or None,
        "paper_progress_stall_handoff_allowed": bool(stall_handoff_allowed),
        "paper_progress_stall_diagnostic": dict(stall_diagnostic),
        "paper_work_unit_lifecycle": paper_work_unit_lifecycle,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "repeat_suppression_key": repeat_guard["repeat_suppression_key"],
        "repeat_suppression": repeat_guard,
        "action_fingerprint": action_fingerprint,
        "action_class": action_cost["action_class"],
        "will_start_llm": action_cost["will_start_llm"],
        "action_cost": action_cost,
        "dry_run": not apply,
        "developer_supervisor_mode": dict(developer_mode_payload),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        **execution,
    }
    progress_first_typed_blocker = _progress_first_typed_blocker(
        dispatch=dispatch,
        execution=execution_payload,
        generated_at=generated_at,
    )
    if progress_first_typed_blocker is not None:
        execution_payload["progress_first_typed_blocker"] = progress_first_typed_blocker
    if "paper_stage_log" not in execution_payload:
        execution_payload["paper_stage_log"] = paper_stage_log_for_default_executor_execution(
            study_id=study_id,
            action_type=action_type,
            next_executable_owner=_text(dispatch.get("next_executable_owner")),
            required_output_surface=_text(dispatch.get("required_output_surface")),
            dispatch_path=dispatch_path,
            dispatch=dispatch,
            execution=execution_payload,
        )
    return execution_payload


def _persist_study_executions(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    generated_at: str,
    study_executions: list[dict[str, Any]],
) -> list[str]:
    latest_path = _execution_latest_path(profile, study_id)
    history_path = _execution_history_path(profile, study_id)
    previous_payload = _read_json_object(latest_path)
    execution_ledger = _merged_execution_ledger(
        previous_payload=previous_payload,
        study_executions=study_executions,
    )
    study_payload = {
        "surface": "default_executor_dispatch_execution_study_latest",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "executions": study_executions,
        "execution_ledger": execution_ledger,
        "ledger_execution_count": len(execution_ledger),
        "ledger_retention_limit": EXECUTION_LEDGER_LIMIT,
        "executed_count": sum(item.get("execution_status") in {"executed", "handoff_ready"} for item in study_executions),
        "blocked_count": sum(item.get("execution_status") == "blocked" for item in study_executions),
        "codex_dispatch_count": sum(item.get("will_start_llm") is True for item in study_executions),
        "suppressed_dispatch_count": sum(
            item.get("execution_status") in {"repeat_suppressed", "blocked"} for item in study_executions
        ),
        "dispatch_budget_window": runtime_dispatch_cost.dispatch_budget_window(),
        "dry_run": False,
    }
    _write_json(latest_path, study_payload)
    _append_json_line(
        history_path,
        {
            "generated_at": generated_at,
            "study_id": study_id,
            "execution_statuses": [item.get("execution_status") for item in study_executions],
            "blocked_reasons": [item.get("blocked_reason") for item in study_executions if item.get("blocked_reason")],
        },
    )
    for execution in study_executions:
        quest_root = profile.runtime_root / (_text(execution.get("quest_id")) or study_id)
        execution["domain_authority_ref_index"] = domain_authority_refs_index.record_dispatch_receipt(
            quest_root=quest_root,
            receipt=execution,
            receipt_path=latest_path,
            db_path=domain_authority_refs_index.workspace_authority_refs_index_path(profile.workspace_root),
        )
    _write_json(latest_path, study_payload)
    return [str(latest_path), str(history_path)]


def _execution_summary(*, study_id: str, study_executions: list[dict[str, Any]]) -> dict[str, Any]:
    selected_dispatch_count = len(study_executions)
    executed_count = sum(item.get("execution_status") in {"executed", "handoff_ready"} for item in study_executions)
    blocked_count = sum(item.get("execution_status") == "blocked" for item in study_executions)
    repeat_suppressed_count = sum(item.get("execution_status") == "repeat_suppressed" for item in study_executions)
    dry_run_count = sum(item.get("execution_status") == "dry_run" for item in study_executions)
    codex_dispatch_count = sum(item.get("will_start_llm") is True for item in study_executions)
    return {
        "study_id": study_id,
        "selected_dispatch_count": selected_dispatch_count,
        "executed_count": executed_count,
        "blocked_count": blocked_count,
        "repeat_suppressed_count": repeat_suppressed_count,
        "dry_run_count": dry_run_count,
        "codex_dispatch_count": codex_dispatch_count,
        "suppressed_dispatch_count": sum(
            item.get("execution_status") in {"repeat_suppressed", "blocked"} for item in study_executions
        ),
        "zero_dispatch_reason": "no_selected_dispatch_for_requested_action_types"
        if selected_dispatch_count == 0
        else None,
        "action_fingerprints": list(
            dict.fromkeys(item.get("action_fingerprint") for item in study_executions if item.get("action_fingerprint"))
        ),
        "execution_statuses": [item.get("execution_status") for item in study_executions],
    }


def dispatch_domain_owner_actions(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    action_types: Iterable[str] = (),
    consumer_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="default_executor_dispatch_executor",
    )
    developer_mode_payload = developer_mode.to_dict()
    resolved_study_ids = _resolve_study_ids(profile, study_ids, consumer_payload=consumer_payload)
    resolved_action_types = tuple(action_type for item in action_types if (action_type := _text(item)) is not None)
    executions: list[dict[str, Any]] = []
    per_study_execution_summary: list[dict[str, Any]] = []
    written_files: list[str] = []
    for study_id in resolved_study_ids:
        for dispatch in _dispatches(
            profile,
            study_id,
            resolved_action_types,
            consumer_payload=consumer_payload,
        ):
            execution = _execute_dispatch(
                profile=profile,
                study_id=study_id,
                dispatch_payload=dispatch,
                developer_mode_payload=developer_mode_payload,
                apply=apply,
            )
            executions.append(execution)
        study_executions = [execution for execution in executions if execution["study_id"] == study_id]
        per_study_execution_summary.append(
            _execution_summary(study_id=study_id, study_executions=study_executions)
        )
        if apply and study_executions:
            written_files.extend(
                _persist_study_executions(
                    profile=profile,
                    study_id=study_id,
                    generated_at=generated_at,
                    study_executions=study_executions,
                )
            )
    payload = {
        "surface": "default_executor_dispatch_executor",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "requested_studies": list(resolved_study_ids),
        "requested_action_types": list(resolved_action_types),
        "execution_count": len(executions),
        "executed_count": sum(item.get("execution_status") in {"executed", "handoff_ready"} for item in executions),
        "blocked_count": sum(item.get("execution_status") == "blocked" for item in executions),
        "repeat_suppressed_count": sum(item.get("execution_status") == "repeat_suppressed" for item in executions),
        "dry_run_count": sum(item.get("execution_status") == "dry_run" for item in executions),
        "codex_dispatch_count": sum(item.get("will_start_llm") is True for item in executions),
        "suppressed_dispatch_count": sum(
            item.get("execution_status") in {"repeat_suppressed", "blocked"} for item in executions
        ),
        "dispatch_budget_window": runtime_dispatch_cost.dispatch_budget_window(),
        "per_study_execution_summary": per_study_execution_summary,
        "action_fingerprints": list(
            dict.fromkeys(item.get("action_fingerprint") for item in executions if item.get("action_fingerprint"))
        ),
        "executions": executions,
        "written_files": written_files,
    }
    return payload


__all__ = [
    "EXECUTION_LATEST_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "SUPPORTED_ACTION_TYPES",
    "dispatch_domain_owner_actions",
    "refresh_controller_decisions_for_current_publication_eval",
]
