from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import paper_work_unit_lifecycle_for_action
from med_autoscience.runtime_control import repeat_suppression
from med_autoscience.runtime_protocol import domain_authority_refs_index

from . import runtime_dispatch_cost, domain_status_projection, progress_first_blocker_budget
from .owner_callable_adapter_projection import (
    domain_progress_transition_requests,
    owner_callable_adapters,
)
from .default_executor_stage_log import paper_stage_log_for_default_executor_execution
from .domain_owner_action_dispatch_parts import action_execution
from .domain_owner_action_dispatch_parts import action_router
from .domain_owner_action_dispatch_parts import controller_refresh
from .domain_owner_action_dispatch_parts import current_dispatch_materialization
from .domain_owner_action_dispatch_parts import developer_apply_gate
from .domain_owner_action_dispatch_parts import dispatch_contract
from .domain_owner_action_dispatch_parts import execution_io
from .domain_owner_action_dispatch_parts import execution_summary
from .domain_owner_action_dispatch_parts import output_readiness
from .domain_owner_action_dispatch_parts import opl_execution_preflight
from .domain_owner_action_dispatch_parts import opl_owner_callable_proof
from .domain_owner_action_dispatch_parts import owner_route_selection
from .domain_owner_action_dispatch_parts import paper_progress_stall_diagnostic
from .domain_owner_action_dispatch_parts import persisted_dispatches
from .domain_owner_action_dispatch_parts import record_only_handoff
from .domain_action_request_materializer import (
    CONSUMER_LATEST_RELATIVE_PATH,
    DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
    FORBIDDEN_SURFACES,
    current_owner_callable_adapters as transition_request_projection_producer,
)
from .default_executor_action_policy import SUPPORTED_ACTION_TYPES
from .opl_execution_boundary import (
    typed_blocker as opl_execution_authorization_typed_blocker,
)


SCHEMA_VERSION = 1
EXECUTION_RELATIVE_ROOT = execution_io.EXECUTION_RELATIVE_ROOT
EXECUTION_LATEST_RELATIVE_PATH = execution_io.EXECUTION_LATEST_RELATIVE_PATH
EXECUTION_HISTORY_RELATIVE_PATH = execution_io.EXECUTION_HISTORY_RELATIVE_PATH
EXECUTION_LEDGER_LIMIT = execution_io.EXECUTION_LEDGER_LIMIT
OWNER_CALLABLE_RECEIPT_SURFACE = execution_io.OWNER_CALLABLE_RECEIPT_SURFACE
OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE = execution_io.OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE
LEGACY_EXECUTION_SURFACE = execution_io.LEGACY_EXECUTION_SURFACE
LEGACY_EXECUTION_STUDY_LATEST_SURFACE = execution_io.LEGACY_EXECUTION_STUDY_LATEST_SURFACE
SUPERVISION_LATEST_RELATIVE_PATH = persisted_dispatches.SUPERVISION_LATEST_RELATIVE_PATH
_append_json_line = execution_io.append_json_line
_consumer_latest_path = execution_io.consumer_latest_path
_execution_history_path = execution_io.execution_history_path
_execution_latest_path = execution_io.execution_latest_path
_execution_latest_payload = execution_io.execution_latest_payload
_merged_execution_ledger = execution_io.merged_execution_ledger
_read_json_object = execution_io.read_json_object
_study_root = execution_io.study_root
_write_json = execution_io.write_json


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _scan_study(scan_payload: Mapping[str, Any] | None, study_id: str) -> dict[str, Any] | None:
    for study in _mapping(scan_payload).get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return None


def _dispatches(
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    *,
    consumer_payload: Mapping[str, Any] | None = None,
    scan_payload: Mapping[str, Any] | None = None,
    fresh_progress: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return persisted_dispatches.selected_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=action_types,
        consumer_payload=consumer_payload,
        consumer_latest_path=_consumer_latest_path(profile),
        scan_payload=scan_payload
        if scan_payload is not None
        else persisted_dispatches.scan_latest_payload(profile),
        fresh_progress=fresh_progress,
        supported_action_types=SUPPORTED_ACTION_TYPES,
        dispatch_relative_root=DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
    )


def _current_materialized_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    mode: str,
    apply: bool,
) -> list[dict[str, Any]]:
    return current_dispatch_materialization.current_materialized_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=action_types,
        mode=mode,
        apply=apply,
        transition_request_projection_producer=transition_request_projection_producer,
        text=_text,
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
    for dispatch in domain_progress_transition_requests(latest):
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


def _contract_guard(dispatch: Mapping[str, Any], *, apply: bool) -> tuple[bool, str | None]:
    if _is_domain_progress_transition_request_projection(dispatch):
        if not _has_trusted_opl_execution_authorization(dispatch):
            return False, "opl_execution_authorization_required"
        return _legacy_stage_packet_contract_guard(dispatch, apply=apply)
    if _text(dispatch.get("legacy_surface")) == "default_executor_dispatch_request":
        return False, "unsupported_dispatch_surface"
    return _legacy_stage_packet_contract_guard(dispatch, apply=apply)


def _legacy_stage_packet_contract_guard(dispatch: Mapping[str, Any], *, apply: bool) -> tuple[bool, str | None]:
    contract_dispatch = _dispatch_contract_payload(dispatch)
    dispatch_error = dispatch_contract.dispatch_contract_error(
        contract_dispatch,
        apply=apply,
        supported_action_types=SUPPORTED_ACTION_TYPES,
    )
    if dispatch_error is not None:
        return False, dispatch_error
    prompt_contract = _mapping(contract_dispatch.get("prompt_contract"))
    if not prompt_contract:
        return False, "prompt_contract_missing"
    prompt_contract_error = _prompt_contract_error(
        prompt_contract,
        dispatch_authority=_text(contract_dispatch.get("dispatch_authority")),
    )
    if prompt_contract_error is not None:
        return False, prompt_contract_error
    return True, None


def _dispatch_contract_payload(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(dispatch)
    if _is_domain_progress_transition_request_projection(payload):
        payload["surface"] = "default_executor_dispatch_request"
        if _text(payload.get("dispatch_status")) == "transition_request_pending":
            payload["dispatch_status"] = "ready"
    return payload


def _is_domain_progress_transition_request_projection(dispatch: Mapping[str, Any]) -> bool:
    return (
        _text(dispatch.get("surface")) == "mas_domain_progress_transition_request_projection"
        and _text(dispatch.get("legacy_surface")) == "default_executor_dispatch_request"
        and dispatch.get("projection_only") is True
        and dispatch.get("owner_callable_carrier_projection_only") is True
    )


def _has_trusted_opl_execution_authorization(dispatch: Mapping[str, Any]) -> bool:
    return opl_owner_callable_proof.trusted_owner_callable_opl_proof(dispatch) is not None


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


def _owner_callable_adapter_boundary() -> dict[str, Any]:
    return {
        "surface_role": "mas_owner_callable_adapter_receipt_projection",
        "mas_role": "owner_callable_adapter_and_authority_result_validator",
        "runtime_owner": "one-person-lab",
        "execution_authority_owner": "one-person-lab",
        "opl_proof_required": True,
        "missing_opl_proof_outcome": "opl_execution_authorization_required",
        "projection_authority": False,
        "execution_ledger_authority": False,
        "attempt_lifecycle_authority": False,
        "queue_authority": False,
        "retry_or_dead_letter_authority": False,
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "can_authorize_provider_admission": False,
        "can_create_provider_attempt": False,
        "can_generate_next_action": False,
        "legacy_default_executor_execution_path_role": "wire_compatibility_and_provenance_ref_only",
        "replacement_owner_surface": "OPL DomainProgressTransitionRuntime / StageRun",
    }


def _prompt_contract_error(prompt_contract: Mapping[str, Any], *, dispatch_authority: str | None) -> str | None:
    return dispatch_contract.prompt_contract_error(
        prompt_contract,
        forbidden_surfaces=FORBIDDEN_SURFACES,
        dispatch_authority=dispatch_authority,
    )


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
    owner_route = owner_route_selection.dispatch_owner_route(dispatch)
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
    return controller_refresh.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=study_ids,
        mode=mode,
        apply=apply,
        generated_at=_utc_now(),
        schema_version=SCHEMA_VERSION,
        resolve_study_ids=_resolve_study_ids,
        study_root=_study_root,
    )


def _execute_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch_payload: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
    scan_payload: Mapping[str, Any] | None = None,
    fresh_progress: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    generated_at = _utc_now()
    progress_payload = (
        fresh_progress
        if fresh_progress is not None
        else persisted_dispatches.read_fresh_study_progress(profile=profile, study_id=study_id)
    )
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
    dispatch = _canonical_provider_hosted_dispatch(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    action_type = _text(dispatch.get("action_type")) or "unknown_action"
    action_fingerprint = runtime_dispatch_cost.dispatch_action_fingerprint(
        dispatch=dispatch,
        dispatch_path=dispatch_path,
    )
    dispatch = opl_execution_preflight.with_provider_hosted_opl_authorization(dispatch)
    guard_ok, guard_reason = _contract_guard(dispatch, apply=apply)
    current_route, owner_route_basis = owner_route_selection.execution_owner_route(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
        scan_payload=scan_payload,
        fresh_progress=progress_payload,
    )
    owner_route_block_reason = owner_route_selection.owner_route_block_reason(
        dispatch=dispatch,
        current_route=current_route,
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    current_study = (
        _scan_study(scan_payload, study_id)
        if scan_payload is not None
        else persisted_dispatches.current_scan_study(profile=profile, study_id=study_id)
    )
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
        fresh_progress=progress_payload,
    )
    stall_block_reason, stall_handoff_allowed = paper_progress_stall_diagnostic.block_from_diagnostic(stall_diagnostic)
    repeat_guard = repeat_suppression.execution_repeat_suppression(
        dispatch={
            **dict(dispatch),
            "owner_route": owner_route_selection.dispatch_owner_route(dispatch),
            "prompt_contract": prompt_contract,
        },
        current_study=current_study,
        previous_execution_latest=_execution_latest_payload(profile, study_id),
        required_output_pending=required_output_pending,
    )
    closeout_block_reason = _progress_first_closeout_block_reason(dispatch)
    execution = _dispatch_pre_execution_block(
        guard_ok=guard_ok,
        guard_reason=guard_reason,
        owner_route_block_reason=owner_route_block_reason,
        current_route=current_route,
        owner_route_basis=owner_route_basis,
        current_study=current_study,
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
    execution = _block_transition_request_without_opl_readback(
        dispatch=dispatch,
        execution=execution,
        owner_route_basis=owner_route_basis,
        current_study=current_study,
    )
    if apply:
        execution = _materialize_post_gate_handoffs(execution)
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
        current_study=current_study,
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
    owner_route_basis: str | None,
    current_study: Mapping[str, Any],
    stall_block_reason: str | None,
    closeout_block_reason: str | None,
    repeat_guard: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any] | None:
    if not guard_ok:
        if guard_reason == "opl_execution_authorization_required":
            return _opl_execution_authorization_block_fields()
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
    if apply and developer_apply_gate.blocked(developer_mode_payload):
        return {
            "execution_status": "blocked",
            "blocked_reason": developer_apply_gate.block_reason(developer_mode_payload) or "developer_apply_safe_required",
            "owner_callable_surface": None,
        }
    opl_block = opl_execution_preflight.block_if_missing_authorization(
        dispatch=dispatch,
        owner_route_basis=owner_route_basis,
        current_study=current_study,
    )
    if opl_block is not None:
        return _blocked_dispatch_carrier(dispatch=dispatch, block=opl_block)
    return None


def _block_transition_request_without_opl_readback(
    *,
    dispatch: Mapping[str, Any],
    execution: Mapping[str, Any],
    owner_route_basis: str | None,
    current_study: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if execution.get("execution_status") == "blocked":
        return dict(execution)
    if not _domain_progress_transition_request_present(dispatch, execution):
        return dict(execution)
    if _domain_progress_transition_opl_proof_present(
        dispatch,
        execution,
        owner_route_basis=owner_route_basis,
        current_study=current_study,
    ):
        return dict(execution)
    return {
        **dict(execution),
        **_opl_execution_authorization_block_fields(),
    }


def _blocked_dispatch_carrier(
    *,
    dispatch: Mapping[str, Any],
    block: Mapping[str, Any],
) -> dict[str, Any]:
    carrier: dict[str, Any] = {}
    for key in (
        "ai_reviewer_record_production_request",
        "ai_reviewer_record_worker_handoff",
        "ai_reviewer_medical_prose_review_production_request",
        "ai_reviewer_medical_prose_review_worker_handoff",
        "writer_worker_handoff",
        "next_required_actions",
        "source_record_blocker_reason",
    ):
        if key in dispatch:
            carrier[key] = dispatch[key]
    for payload in _iter_transition_payloads(dispatch):
        for key in (
            "ai_reviewer_record_production_request",
            "ai_reviewer_record_worker_handoff",
            "ai_reviewer_medical_prose_review_production_request",
            "ai_reviewer_medical_prose_review_worker_handoff",
            "writer_worker_handoff",
            "source_record_blocker_reason",
        ):
            if key not in carrier and key in payload:
                carrier[key] = payload[key]
    if "next_required_actions" not in carrier:
        source_action = _mapping(dispatch.get("source_action"))
        if actions := _text_items(source_action.get("next_required_actions")):
            carrier["next_required_actions"] = actions
    if "next_required_actions" not in carrier:
        production_request = _mapping(dispatch.get("ai_reviewer_record_production_request"))
        if request_kind := _text(production_request.get("request_kind")):
            carrier["next_required_actions"] = [
                request_kind,
                "rematerialize_ai_reviewer_request",
                "return_to_ai_reviewer_workflow",
            ]
    return {
        **carrier,
        **dict(block),
        **_opl_execution_authorization_block_fields(),
    }


def _opl_execution_authorization_block_fields() -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "opl_execution_authorization_required",
        "typed_blocker": opl_execution_authorization_typed_blocker(),
        "owner_callable_surface": None,
        "adapter_kind": "opl_authorized_owner_callable_adapter",
        "target_runtime_owner": "one-person-lab",
        "mas_private_attempt_loop_forbidden": True,
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
        "provider_attempt_or_lease_required": False,
        "opl_transition_runtime_required": True,
        "owner_callable_adapter_boundary": _owner_callable_adapter_boundary(),
    }


def _materialize_post_gate_handoffs(execution: Mapping[str, Any]) -> dict[str, Any]:
    if _text(execution.get("execution_status")) != "handoff_ready":
        return dict(execution)
    result = dict(execution)
    record_handoff = _mapping(result.get("ai_reviewer_record_worker_handoff"))
    if record_handoff and "ai_reviewer_record_worker_handoff_path" not in result:
        result["ai_reviewer_record_worker_handoff_path"] = (
            action_execution.ai_reviewer_record_production.materialize_ai_reviewer_record_worker_handoff(
                handoff=record_handoff,
            )
        )
    prose_handoff = _mapping(result.get("ai_reviewer_medical_prose_review_worker_handoff"))
    if prose_handoff and "ai_reviewer_medical_prose_review_worker_handoff_path" not in result:
        result["ai_reviewer_medical_prose_review_worker_handoff_path"] = (
            action_execution.ai_reviewer_medical_prose_review_production.materialize_ai_reviewer_medical_prose_review_worker_handoff(
                handoff=prose_handoff,
            )
        )
    return result


def _domain_progress_transition_request_present(*values: object) -> bool:
    for payload in _iter_transition_payloads(*values):
        if _payload_has_domain_progress_transition_request(payload):
            return True
    return False


def _payload_has_domain_progress_transition_request(payload: Mapping[str, Any]) -> bool:
    if _text(payload.get("dispatch_status")) == "transition_request_pending":
        return True
    if _text(payload.get("execution_status")) == "transition_request_pending":
        return True
    request = _mapping(payload.get("opl_domain_progress_transition_request"))
    return bool(request and _text(request.get("target_runtime_kind")) == "DomainProgressTransitionRuntime")


def _domain_progress_transition_opl_proof_present(
    *values: object,
    owner_route_basis: str | None,
    current_study: Mapping[str, Any] | None,
) -> bool:
    for payload in _iter_transition_payloads(*values):
        if (
            not _payload_has_domain_progress_transition_request(payload)
            and not opl_owner_callable_proof.has_bound_opl_transition_readback(payload)
        ):
            continue
        if opl_owner_callable_proof.trusted_owner_callable_opl_proof(payload) is not None:
            return True
    return False


def _iter_transition_payloads(*values: object) -> list[Mapping[str, Any]]:
    payloads: list[Mapping[str, Any]] = []
    stack = list(values)
    seen: set[int] = set()
    while stack:
        value = stack.pop()
        if isinstance(value, Mapping):
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            payload = _mapping(value)
            payloads.append(payload)
            for key in (
                "prompt_contract",
                "owner_route",
                "source_action",
                "ai_reviewer_record_worker_handoff",
                "ai_reviewer_medical_prose_review_worker_handoff",
                "writer_worker_handoff",
                "opl_domain_progress_transition_request",
                "opl_domain_progress_transition_result",
                "opl_domain_progress_runtime_result",
                "opl_runtime_result",
                "paper_progress_policy_result",
                "state",
            ):
                nested = payload.get(key)
                if isinstance(nested, Mapping):
                    stack.append(nested)
            continue
        if isinstance(value, (list, tuple)):
            stack.extend(item for item in value if isinstance(item, Mapping))
    return payloads


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
    current_study: Mapping[str, Any] | None,
    apply: bool,
    developer_mode_payload: Mapping[str, Any],
    execution: Mapping[str, Any],
    ) -> dict[str, Any]:
    paper_work_unit_lifecycle = paper_work_unit_lifecycle_for_action(action_type)
    execution_payload = {
        "surface": OWNER_CALLABLE_RECEIPT_SURFACE,
        "canonical_surface": OWNER_CALLABLE_RECEIPT_SURFACE,
        "legacy_surface_alias": LEGACY_EXECUTION_SURFACE,
        "legacy_wire_surface": LEGACY_EXECUTION_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "adapter_kind": _text(dispatch.get("adapter_kind")) or "opl_authorized_owner_callable_adapter",
        "target_runtime_owner": _text(dispatch.get("target_runtime_owner")) or "one-person-lab",
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "source_dispatch_claimed_mas_authority": dispatch.get("mas_dispatch_authority") is True,
        "source_dispatch_claimed_opl_write": any(
            dispatch.get(key) is True
            for key in (
                "mas_creates_opl_outbox",
                "mas_creates_opl_event",
                "mas_creates_opl_stage_run",
            )
        ),
        "execution_requires_opl_authorization": True,
        "opl_execution_authorization_required": dispatch.get("opl_execution_authorization_required") is True
        or prompt_contract.get("opl_execution_authorization_required") is True,
        "opl_execution_authorization_present": bool(
            dispatch.get("opl_execution_authorization_present") is True
            or prompt_contract.get("opl_execution_authorization_present") is True
            or
            _mapping(dispatch.get("opl_execution_authorization"))
            or _mapping(prompt_contract.get("opl_execution_authorization"))
        ),
        "owner_callable_requires_opl_authorization": dispatch.get("owner_callable_requires_opl_authorization") is True
        or prompt_contract.get("owner_callable_requires_opl_authorization") is True,
        "provider_admission_pending": dispatch.get("provider_admission_pending") is True
        or prompt_contract.get("provider_admission_pending") is True,
        "mas_private_attempt_loop_forbidden": dispatch.get("mas_private_attempt_loop_forbidden") is True
        or prompt_contract.get("mas_private_attempt_loop_forbidden") is True,
        "projection_authority": False,
        "owner_callable_receipt_projection": True,
        "execution_ledger_authority": False,
        "attempt_lifecycle_authority": False,
        "queue_authority": False,
        "retry_or_dead_letter_authority": False,
        "legacy_default_executor_execution_path_role": "wire_compatibility_and_provenance_ref_only",
        "owner_callable_adapter_boundary": _owner_callable_adapter_boundary(),
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")),
        "action_type": action_type,
        "action_id": _text(dispatch.get("action_id")),
        "execution_id": f"execution::{study_id}::{action_type}::{generated_at}",
        "next_executable_owner": _text(dispatch.get("next_executable_owner")),
        "required_output_surface": _text(dispatch.get("required_output_surface")),
        "dispatch_path": str(dispatch_path),
        "dispatch_status": _text(dispatch.get("dispatch_status")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")) or "consumer_default_executor_dispatch",
        "provider_admission_requires_opl_runtime_result": (
            dispatch.get("provider_admission_requires_opl_runtime_result") is True
            or prompt_contract.get("provider_admission_requires_opl_runtime_result") is True
        ),
        "blocked_reason": None,
        "owner_callable_adapter_contract": _mapping(dispatch.get("owner_callable_adapter_contract")) or None,
        "domain_intent": _mapping(dispatch.get("domain_intent")) or None,
        "dispatch_contract_valid": guard_ok,
        "dispatch_contract_blocked_reason": guard_reason,
        "executor_boundary": _executor_boundary(dispatch),
        "owner_route": owner_route_selection.dispatch_owner_route(dispatch) or None,
        "owner_route_current": owner_route_block_reason is None if guard_ok else None,
        "owner_route_basis": owner_route_basis,
        "current_owner_route": current_route,
        "prompt_contract": prompt_contract or None,
        "paper_progress_stall": _mapping(dispatch.get("paper_progress_stall"))
        or _mapping(prompt_contract.get("paper_progress_stall"))
        or None,
        "current_paper_progress_stall": _mapping(current_study).get("paper_progress_stall") or None,
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
    if execution_status := _text(execution_payload.get("execution_status")):
        execution_payload["status"] = execution_status
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
    if isinstance(execution_payload.get("paper_stage_log"), Mapping):
        execution_payload.setdefault("user_stage_log", execution_payload["paper_stage_log"])
        execution_payload.setdefault("stage_log_summary", execution_payload["paper_stage_log"])
    return execution_payload


def _canonical_provider_hosted_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    canonical = opl_execution_preflight.provider_hosted_canonical_stage_packet_dispatch(
        dispatch=dispatch,
        workspace_root=profile.workspace_root,
        study_root=_study_root(profile, study_id),
    )
    return canonical if canonical is not None else dict(dispatch)


def _persist_study_executions(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    generated_at: str,
    study_executions: list[dict[str, Any]],
) -> list[str]:
    latest_path = _execution_latest_path(profile, study_id)
    history_path = _execution_history_path(profile, study_id)
    previous_payload = _execution_latest_payload(profile, study_id)
    execution_ledger = _merged_execution_ledger(
        previous_payload=previous_payload,
        study_executions=study_executions,
    )
    study_payload = {
        "surface": OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE,
        "canonical_surface": OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE,
        "legacy_surface_alias": LEGACY_EXECUTION_STUDY_LATEST_SURFACE,
        "legacy_wire_surface": LEGACY_EXECUTION_STUDY_LATEST_SURFACE,
        "legacy_wire_path": str(execution_io.LEGACY_EXECUTION_LATEST_RELATIVE_PATH),
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "projection_authority": False,
        "owner_callable_receipt_projection": True,
        "execution_ledger_authority": False,
        "attempt_lifecycle_authority": False,
        "queue_authority": False,
        "retry_or_dead_letter_authority": False,
        "target_runtime_owner": "one-person-lab",
        "legacy_default_executor_execution_path_role": "wire_compatibility_and_provenance_ref_only",
        "owner_callable_adapter_boundary": _owner_callable_adapter_boundary(),
        "executions": study_executions,
        "execution_ledger": execution_ledger,
        "ledger_execution_count": len(execution_ledger),
        "ledger_retention_limit": EXECUTION_LEDGER_LIMIT,
        "executed_count": sum(item.get("execution_status") == "executed" for item in study_executions),
        "handoff_ready_count": sum(item.get("execution_status") == "handoff_ready" for item in study_executions),
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
        scheduler_owner="opl_authorized_owner_callable_adapter_dispatcher",
    )
    developer_mode_payload = developer_mode.to_dict()
    resolved_study_ids = _resolve_study_ids(profile, study_ids, consumer_payload=consumer_payload)
    resolved_action_types = tuple(action_type for item in action_types if (action_type := _text(item)) is not None)
    executions: list[dict[str, Any]] = []
    per_study_execution_summary: list[dict[str, Any]] = []
    written_files: list[str] = []
    for study_id in resolved_study_ids:
        study_scan_payload = persisted_dispatches.scan_latest_payload(profile)
        study_fresh_progress = persisted_dispatches.read_fresh_study_progress(
            profile=profile,
            study_id=study_id,
        )
        selected_dispatches = _dispatches(
            profile,
            study_id,
            resolved_action_types,
            consumer_payload=consumer_payload,
            scan_payload=study_scan_payload,
            fresh_progress=study_fresh_progress,
        )
        if not selected_dispatches and consumer_payload is None and not apply:
            selected_dispatches = (
                _current_materialized_dispatches(
                    profile=profile,
                    study_id=study_id,
                    action_types=resolved_action_types,
                    mode=mode,
                    apply=False,
                )
            )
        for dispatch in selected_dispatches:
            execution = _execute_dispatch(
                profile=profile,
                study_id=study_id,
                dispatch_payload=dispatch,
                developer_mode_payload=developer_mode_payload,
                apply=apply,
                scan_payload=study_scan_payload,
                fresh_progress=study_fresh_progress,
            )
            executions.append(execution)
        study_executions = [execution for execution in executions if execution["study_id"] == study_id]
        per_study_execution_summary.append(
            execution_summary.execution_summary(study_id=study_id, study_executions=study_executions)
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
        "surface": "opl_authorized_owner_callable_adapter_dispatch",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "adapter_kind": "opl_authorized_owner_callable_adapter",
        "target_runtime_owner": "one-person-lab",
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "owner_callable_adapter_boundary": _owner_callable_adapter_boundary(),
        "requested_studies": list(resolved_study_ids),
        "requested_action_types": list(resolved_action_types),
        "execution_count": len(executions),
        "executed_count": sum(item.get("execution_status") == "executed" for item in executions),
        "handoff_ready_count": sum(item.get("execution_status") == "handoff_ready" for item in executions),
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
