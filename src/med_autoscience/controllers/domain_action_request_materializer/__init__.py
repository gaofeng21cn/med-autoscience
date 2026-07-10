from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_callable_closeout_contract import (
    owner_callable_typed_closeout_contract,
)
from med_autoscience.controllers import progress_first_closeout
from med_autoscience.controllers.runtime_ai_repair_policy import (
    owner_callable_policy,
    two_layer_ai_repair_policy_payload,
)
from med_autoscience.controllers.owner_callable_adapter_projection import (
    legacy_owner_callable_adapter_diagnostics,
    with_owner_callable_adapter_projection,
)
from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
)
from med_autoscience.controllers.domain_action_request_materializer import (
    current_action_selection,
    current_owner_callable_adapters as current_owner_callable_adapters_part,
    current_writer_handoff,
    evidence_gap_decision as evidence_gap_decision_part,
    materializer_core,
    owner_callable_dispatch_payload,
    publication_owner_materialization,
    readiness_dispatch_enrichment,
    request_refresh,
    request_task_projection,
    supervisor_request_packets,
    transition_request_projection,
    transition_projection_boundary,
    writer_handoff_preservation,
)
from med_autoscience.controllers.stage_outcome_authority import output_readiness
from med_autoscience.controllers.owner_callable_action_policy import (
    ALLOWED_WRITE_SURFACES,
    FORBIDDEN_SURFACES,
    RETIRED_ABSENT_SURFACES,
    SOURCE_ACTION_REF_FIELDS,
    SOURCE_HANDOFF_REF_FIELDS,
    SUPPORTED_ACTION_TYPES as SUPPORTED_REQUEST_ACTION_TYPES,
    owner_callable_search_discipline,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control.owner_callable_registry import owner_callable_for_action
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import repeat_suppression


SCHEMA_VERSION = 1
CONSUMER_LATEST_RELATIVE_PATH = materializer_core.CONSUMER_LATEST_RELATIVE_PATH
CONSUMER_HISTORY_RELATIVE_PATH = materializer_core.CONSUMER_HISTORY_RELATIVE_PATH
OWNER_CALLABLE_ADAPTER_KIND = materializer_core.OWNER_CALLABLE_ADAPTER_KIND
TARGET_RUNTIME_OWNER = transition_projection_boundary.TARGET_RUNTIME_OWNER
READINESS_ACTION_TYPE = readiness_dispatch_enrichment.READINESS_ACTION_TYPE
MERGE_CLEANUP_CHECKLIST = [
    "focused pytest green",
    "git diff --check green",
    "review diff touches only owned files",
    "merge branch into main after parallel worker coordination",
    "remove worktree after absorb",
]


def _utc_now() -> str:
    return materializer_core.utc_now()


def _text(value: object) -> str | None:
    return materializer_core.text(value)


def _mapping(value: object) -> dict[str, Any]:
    return materializer_core.mapping(value)


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return materializer_core.study_root(profile, study_id)


def _request_packet_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    return materializer_core.request_packet_path(profile, study_id, action_type)


def _owner_callable_adapter_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    return materializer_core.owner_callable_adapter_path(profile, study_id, action_type)


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return materializer_core.scan_latest_path(profile)


def _current_scan_study(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any] | None:
    return materializer_core.current_scan_study(scan_payload, study_id)


def _progress_first_closeout_admission(
    *,
    scan_payload: Mapping[str, Any],
    study_id: str,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    study = _current_scan_study(scan_payload, study_id) or {}
    source_refs = _mapping(owner_route.get("source_refs"))
    running_attempt = _mapping(study.get("running_attempt")) or _mapping(study.get("current_running_attempt"))
    packet = (
        _mapping(running_attempt.get("immutable_dispatch_packet"))
        or _mapping(running_attempt.get("stage_packet"))
        or _mapping(study.get("immutable_dispatch_packet"))
    )
    identity = {
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(study.get("quest_id")),
        "work_unit_id": _text(source_refs.get("work_unit_id")) or _text(owner_route.get("work_unit_id")),
        "stage_attempt_id": _text(running_attempt.get("stage_attempt_id"))
        or _text(study.get("active_stage_attempt_id")),
    }
    return progress_first_closeout.closeout_first_admission(
        identity=identity,
        immutable_dispatch_packet=packet,
        running_attempt=running_attempt,
        owner_receipt=_mapping(study.get("owner_receipt")),
        stage_closeout=_mapping(study.get("stage_closeout")) or _mapping(study.get("latest_stage_closeout")),
        stable_typed_blocker=_mapping(study.get("stable_typed_blocker")),
    )


def _required_output_pending(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    current_study: Mapping[str, Any] | None,
) -> bool:
    return output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        current_study=current_study,
    )


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    return materializer_core.owner_from_action(action, action_type)


def _request_output_target_surface_for_action_type(action_type: str) -> dict[str, object] | None:
    return materializer_core.request_output_target_surface(action_type)


def _request_packet_ref_for_dispatch(action_type: str) -> str | None:
    return materializer_core.request_packet_ref_for_dispatch_action(action_type)


def _source_action_ref(action: Mapping[str, Any]) -> dict[str, Any]:
    source_ref = {key: action[key] for key in SOURCE_ACTION_REF_FIELDS if key in action}
    for key in (
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "required_delta_kind",
        "materialized_from_action_type",
    ):
        if key in action and key not in source_ref:
            source_ref[key] = action[key]
    supervisor_decision = _mapping(source_ref.get("supervisor_decision"))
    if supervisor_decision and "supervisor_policy_projection" not in source_ref:
        source_ref["supervisor_policy_projection"] = "paper_autonomy_supervisor_policy_projection"
        source_ref["supervisor_authority"] = "paper_autonomy_supervisor_policy_projection"
        source_ref["supervisor_authority_boundary"] = "policy_projection_requires_opl_readback"
        source_ref["supervisor_policy_projection_boundary"] = {
            "surface_kind": "paper_autonomy_supervisor_policy_projection_boundary",
            "decision_field_role": "policy_recommendation_label",
            "decision_field_is_authority": False,
            "mas_can_authorize_provider_admission": False,
            "mas_can_run_supervisor_decision_engine": False,
            "mas_can_store_recovery_obligation": False,
            "mas_can_run_fixed_point_runtime": False,
            "requires_opl_supervisor_decision_engine_readback": True,
        }
    handoff = _mapping(action.get("handoff_packet"))
    handoff_ref = {key: handoff[key] for key in SOURCE_HANDOFF_REF_FIELDS if key in handoff}
    if handoff_ref:
        source_ref["handoff_packet"] = handoff_ref
    return source_ref


def _required_output_surface(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("required_output_surface"))
        or _text(handoff_packet.get("required_output_surface"))
        or materializer_core.request_output_surface({}, action_type)
    )


def _owner_callable_forbidden_surfaces(owner_route: Mapping[str, Any]) -> list[str]:
    forbidden = list(FORBIDDEN_SURFACES)
    for item in _mapping(owner_route.get("owner_reason_contract")).get("forbidden_surfaces") or []:
        if (surface := _text(item)) is not None and surface not in forbidden:
            forbidden.append(surface)
    return forbidden


def _owner_callable_dispatch(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    required_output_surface: str,
    apply: bool,
    scan_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    dispatch_path = _owner_callable_adapter_path(profile, study_id, action_type)
    executor_policy = owner_callable_policy()
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    owner_route_allows_action = owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": next_executable_owner,
            "action_type": action_type,
        },
        owner_route=owner_route,
    )
    is_mas_foreground_owner_callable = _mas_foreground_owner_callable_action(action)
    if not is_mas_foreground_owner_callable:
        from med_autoscience.controllers.domain_action_request_materializer import (
            ai_reviewer_record_handoff,
        )

        record_only_handoff = (
            ai_reviewer_record_handoff.ai_reviewer_record_production_handoff_dispatch(
                profile=profile,
                action=action,
                action_type=action_type,
                study_id=study_id,
                dispatch_path=dispatch_path,
                owner_route=owner_route,
                source_action_ref=_source_action_ref,
            )
            if owner_route_allows_action
            else None
        )
        if record_only_handoff is not None:
            return record_only_handoff
    closeout_admission = _progress_first_closeout_admission(
        scan_payload=scan_payload,
        study_id=study_id,
        action=action,
        owner_route=owner_route,
    )
    preserved_writer_handoff = writer_handoff_preservation.preserved_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        action=action,
        dispatch_path=dispatch_path,
        owner_route=owner_route,
        apply=apply,
        forbidden_surfaces=FORBIDDEN_SURFACES,
    )
    if preserved_writer_handoff is not None:
        return preserved_writer_handoff
    idempotency_key = _text(owner_route.get("idempotency_key"))
    repeat_key = repeat_suppression.repeat_key(owner_route)
    typed_closeout_contract = owner_callable_typed_closeout_contract(action_type=action_type)
    forbidden_surfaces = _owner_callable_forbidden_surfaces(owner_route)
    required_output_target_surface = _request_output_target_surface_for_action_type(action_type)
    readiness_dispatch = readiness_dispatch_enrichment.readiness_dispatch_enrichment(
        action,
        action_type,
        schema_version=SCHEMA_VERSION,
        profile=profile,
        study_root=_study_root,
    )
    evidence_gap_projection = evidence_gap_decision_part.projection_for_action(
        action,
        text=_text,
        mapping=_mapping,
    )
    prompt_contract = {
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(_mapping(action.get("handoff_packet")).get("quest_id")),
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "owner_route": owner_route or None,
        "owner_reason_contract": _mapping(owner_route.get("owner_reason_contract")) or None,
        "owner_route_attempt_protocol": _mapping(owner_route.get("owner_route_attempt_protocol")) or None,
        "owner_route_currentness_basis": _mapping(_mapping(owner_route.get("source_refs")).get("owner_route_currentness_basis")) or None,
        "idempotency_key": idempotency_key,
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "request_packet_ref": _request_packet_ref_for_dispatch(action_type),
        "paper_progress_stall": _mapping(action.get("paper_progress_stall")) or None,
        "source_scan_latest": str(_scan_latest_path(profile)),
        "required_closeout_packet": typed_closeout_contract,
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "tool_discipline": owner_callable_search_discipline(),
        "search_boundaries": owner_callable_search_discipline(),
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    prompt_contract.update(evidence_gap_decision_part.prompt_fields(evidence_gap_projection, mapping=_mapping))
    prompt_contract.update(readiness_dispatch)
    if required_output_target_surface is not None:
        prompt_contract["required_output_target_surface"] = required_output_target_surface
    dispatch_shell = {
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "owner_route": owner_route or None,
        "prompt_contract": prompt_contract,
        **readiness_dispatch,
        "required_closeout_packet": typed_closeout_contract,
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
    }
    owner_route_attempt_envelope = owner_route_attempt_protocol.owner_callable_attempt_envelope(
        dispatch=dispatch_shell
    )
    opl_execution_authorization = first_trusted_opl_execution_authorization(
        action.get("opl_execution_authorization"),
        prompt_contract.get("opl_execution_authorization"),
        owner_route.get("opl_execution_authorization"),
        _mapping(owner_route.get("source_refs")).get("opl_execution_authorization"),
    )
    if is_mas_foreground_owner_callable:
        return owner_callable_dispatch_payload.mas_foreground_owner_callable_dispatch_payload(
            profile=profile,
            action=action,
            action_type=action_type,
            study_id=study_id,
            dispatch_path=dispatch_path,
            executor_policy=executor_policy,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
            owner_route=owner_route,
            idempotency_key=idempotency_key,
            repeat_key=repeat_key,
            typed_closeout_contract=typed_closeout_contract,
            owner_route_attempt_envelope=owner_route_attempt_envelope,
            prompt_contract=prompt_contract,
            readiness_dispatch=readiness_dispatch,
            evidence_gap_projection=evidence_gap_projection,
            progress_first_closeout_admission=closeout_admission,
            generated_at=generated_at,
            schema_version=SCHEMA_VERSION,
            owner_callable_adapter_kind=OWNER_CALLABLE_ADAPTER_KIND,
            target_runtime_owner=TARGET_RUNTIME_OWNER,
            source_action_ref=_source_action_ref,
            owner_callable_surface=_owner_callable_surface,
            scan_latest_path=_scan_latest_path,
        )
    dispatch_status = (
        "ready"
        if (apply or opl_execution_authorization is not None)
        and opl_execution_authorization is not None
        and owner_route_attempt_envelope.get("dispatchable") is True
        and owner_route_allows_action
        else "dry_run" if not apply else "blocked"
    )
    blocked_reason = _owner_callable_dispatch_blocked_reason(
        dispatch_status=dispatch_status,
        opl_execution_authorization=opl_execution_authorization,
        action=action,
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        owner_route=owner_route,
        owner_route_attempt_envelope=owner_route_attempt_envelope,
    )
    hard_evidence_gap_reason = evidence_gap_decision_part.blocked_reason(
        evidence_gap_projection,
        mapping=_mapping,
    )
    if hard_evidence_gap_reason is not None:
        dispatch_status = "blocked"
        blocked_reason = hard_evidence_gap_reason
    current_study = _current_scan_study(scan_payload, study_id)
    repeat_guard = repeat_suppression.dispatch_repeat_suppression(
        dispatch={"prompt_contract": prompt_contract, "owner_route": owner_route, "dispatch_status": dispatch_status},
        current_study=current_study,
        existing_dispatch=request_refresh.read_json_object(dispatch_path),
        required_output_pending=_required_output_pending(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            current_study=current_study,
        ),
    )
    if dispatch_status == "ready" and repeat_guard["repeat_suppressed"]:
        dispatch_status = "repeat_suppressed"
        blocked_reason = repeat_suppression.REPEAT_SUPPRESSED_REASON
    if dispatch_status == "ready" and closeout_admission.get("admission_status") == "blocked":
        dispatch_status = "blocked"
        blocked_reason = _text(closeout_admission.get("blocked_reason"))
    return owner_callable_dispatch_payload.owner_callable_dispatch_payload(
        profile=profile,
        action=action,
        action_type=action_type,
        study_id=study_id,
        dispatch_path=dispatch_path,
        executor_policy=executor_policy,
        next_executable_owner=next_executable_owner,
        required_output_surface=required_output_surface,
        owner_route=owner_route,
        idempotency_key=idempotency_key,
        repeat_key=repeat_key,
        dispatch_status=dispatch_status,
        blocked_reason=blocked_reason,
        repeat_guard=repeat_guard,
        typed_closeout_contract=typed_closeout_contract,
        owner_route_attempt_envelope=owner_route_attempt_envelope,
        prompt_contract=prompt_contract,
        readiness_dispatch=readiness_dispatch,
        evidence_gap_projection=evidence_gap_projection,
        progress_first_closeout_admission=closeout_admission,
        generated_at=generated_at,
        schema_version=SCHEMA_VERSION,
        owner_callable_adapter_kind=OWNER_CALLABLE_ADAPTER_KIND,
        target_runtime_owner=TARGET_RUNTIME_OWNER,
        source_action_ref=_source_action_ref,
        scan_latest_path=_scan_latest_path,
    )


def _mas_foreground_owner_callable_action(action: Mapping[str, Any]) -> bool:
    if _ai_reviewer_record_production_action(action):
        return False
    target_surface = _mapping(action.get("target_surface"))
    owner_callable_surface = _owner_callable_surface(action)
    if owner_callable_surface is None:
        return False
    ref_kind = _text(target_surface.get("ref_kind"))
    current_owner_action = (
        _text(action.get("authority")) == "study_progress.current_executable_owner_action"
        or _text(action.get("source_surface")) == "current_executable_owner_action"
        or _text(action.get("source")) == "current_executable_owner_action"
    )
    if (
        ref_kind != "mas_owner_callable"
        and not (ref_kind == "paper_recovery_successor_owner_action" and current_owner_action)
        and _paper_recovery_successor_owner_callable_surface(action) is None
    ):
        return False
    for key in (
        "provider_admission_pending",
        "transition_request_pending",
        "provider_attempt_or_lease_required",
        "provider_admission_requires_opl_runtime_result",
        "opl_transition_runtime_required",
        "opl_transition_runtime_required_for_durable_carrier",
    ):
        if action.get(key) is True:
            return False
    return True


def _ai_reviewer_record_production_action(action: Mapping[str, Any]) -> bool:
    if _text(action.get("action_type")) != "return_to_ai_reviewer_workflow":
        return False
    from med_autoscience.controllers.domain_action_request_materializer.ai_reviewer_record_handoff import (
        AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS,
    )

    work_unit_id = (
        _text(action.get("work_unit_id"))
        or _text(action.get("next_work_unit"))
        or _text(action.get("controller_work_unit_id"))
        or _text(action.get("reason"))
    )
    return work_unit_id in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS


def _owner_callable_surface(action: Mapping[str, Any]) -> str | None:
    target_surface = _mapping(action.get("target_surface"))
    return (
        _text(action.get("owner_callable_surface"))
        or _text(target_surface.get("owner_callable_surface"))
        or _paper_recovery_successor_owner_callable_surface(action)
    )


def _paper_recovery_successor_owner_callable_surface(action: Mapping[str, Any]) -> str | None:
    for container_key in (
        "next_safe_action",
        "paper_autonomy_supervisor_decision",
        "paper_progress_policy_result_projection",
        "supervisor_decision",
    ):
        if surface := _owner_callable_surface_from_next_safe_action(_mapping(action.get(container_key))):
            return surface
    supervisor = _mapping(action.get("paper_autonomy_supervisor_decision"))
    if surface := _owner_callable_surface_from_next_safe_action(
        _mapping(supervisor.get("paper_progress_policy_result_projection"))
    ):
        return surface
    return None


def _owner_callable_surface_from_next_safe_action(payload: Mapping[str, Any]) -> str | None:
    next_safe_action = _mapping(payload.get("next_safe_action")) or payload
    source_action = _mapping(next_safe_action.get("source_next_safe_action"))
    owner_callable = _mapping(source_action.get("owner_callable"))
    return _text(owner_callable.get("callable_surface"))


def _owner_callable_dispatch_blocked_reason(
    *,
    dispatch_status: str,
    opl_execution_authorization: Mapping[str, Any] | None,
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    owner_route: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
) -> str | None:
    if dispatch_status != "blocked":
        return None
    if owner_route_attempt_envelope.get("dispatchable") is not True:
        return "owner_route_currentness_basis_missing"
    if owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": next_executable_owner,
            "action_type": action_type,
        },
        owner_route=owner_route,
    ):
        return (
            "opl_execution_authorization_required"
            if opl_execution_authorization is None
            else None
        )
    return "owner_route_next_owner_mismatch"


def _request_task(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    action_type = _text(action.get("action_type")) or "unknown_action"
    action_payload = {**dict(action), "study_root": str(_study_root(profile, study_id))}
    task = supervisor_request_packets.request_task(
        action=action_payload,
        schema_version=SCHEMA_VERSION,
        packet_path=_request_packet_path(profile, study_id, action_type),
        scan_latest_path=_scan_latest_path(profile),
        forbidden_surfaces=FORBIDDEN_SURFACES,
        allowed_write_surfaces=ALLOWED_WRITE_SURFACES,
    )
    evidence_gap_projection = evidence_gap_decision_part.projection_for_action(
        action,
        text=_text,
        mapping=_mapping,
    )
    task.update(evidence_gap_decision_part.prompt_fields(evidence_gap_projection, mapping=_mapping))
    hard_evidence_gap_reason = evidence_gap_decision_part.blocked_reason(
        evidence_gap_projection,
        mapping=_mapping,
    )
    if hard_evidence_gap_reason is not None:
        task["dispatch_status"] = "blocked"
        task["blocked_reason"] = hard_evidence_gap_reason
    handoff = dict(_mapping(task.get("handoff_packet")))
    handoff.update(evidence_gap_decision_part.prompt_fields(evidence_gap_projection, mapping=_mapping))
    if hard_evidence_gap_reason is not None:
        handoff["blocked_reason"] = hard_evidence_gap_reason
    task["handoff_packet"] = handoff
    return task


def _with_transition_request_task_semantics(task: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(task)
    if _text(payload.get("dispatch_status")) == "applied":
        payload["dispatch_status"] = "transition_request_pending"
        payload["blocked_reason"] = "opl_execution_authorization_required"
    payload["mas_local_request_packet_persistence"] = "forbidden"
    payload["opl_transition_runtime_required_for_durable_carrier"] = True
    transition_projection_boundary.apply_boundary(payload)
    handoff = dict(_mapping(payload.get("handoff_packet")))
    handoff["dispatch_status"] = "transition_request_pending"
    transition_projection_boundary.apply_boundary(handoff)
    handoff["mas_local_request_packet_persistence"] = "forbidden"
    payload["handoff_packet"] = handoff
    return payload


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def _selected_actions(
    *,
    profile: WorkspaceProfile,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    request_selected: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    allowed_studies = set(study_ids)
    current_writer_handoff_actions: dict[str, dict[str, Any]] = {}
    for study_id in study_ids:
        current_action = current_writer_handoff.current_quality_repair_writer_handoff_action(
            profile=profile,
            study_id=study_id,
        )
        if current_action is not None:
            current_writer_handoff_actions[study_id] = current_action
    request_selected.extend(current_writer_handoff_actions.values())
    actions, preignored = _current_actions_for_studies(
        profile=profile,
        scan_payload=scan_payload,
        study_ids=study_ids,
    )
    ignored.extend(
        _ignored_action(item, "superseded_by_current_quality_repair_writer_handoff")
        if _text(item.get("study_id")) in current_writer_handoff_actions
        else item
        for item in preignored
    )
    if not isinstance(actions, list):
        return request_selected, ignored
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        study_id = _text(action.get("study_id"))
        if study_id not in allowed_studies:
            ignored.append(_ignored_action(action, "study_not_requested"))
            continue
        if study_id in current_writer_handoff_actions:
            ignored.append(_ignored_action(action, "superseded_by_current_quality_repair_writer_handoff"))
            continue
        if action.get("default_dispatch_allowed") is False:
            ignored.append(
                _ignored_action(
                    action,
                    _text(action.get("default_dispatch_blocked_reason"))
                    or "default_dispatch_not_allowed",
                )
            )
            continue
        selected_action = publication_owner_materialization.materialization_action(
            profile=profile,
            action=action,
        ) or dict(action)
        action_type = _text(selected_action.get("action_type"))
        if action_type in SUPPORTED_REQUEST_ACTION_TYPES:
            request_selected.append(selected_action)
            continue
        else:
            ignored.append(_ignored_action(selected_action, "unsupported_action_type"))
            continue
    return request_selected, ignored


def _current_actions_for_studies(
    *,
    profile: WorkspaceProfile,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]:
    return current_action_selection.current_actions_for_studies(
        profile=profile,
        scan_payload=scan_payload,
        study_ids=study_ids,
    )


def _resolve_study_ids_from_scan(scan_payload: Mapping[str, Any], study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    resolved: list[str] = []
    for action in scan_payload.get("action_queue") or []:
        if isinstance(action, Mapping) and (study_id := _text(action.get("study_id"))) is not None:
            resolved.append(study_id)
    for study in scan_payload.get("studies") or []:
        if isinstance(study, Mapping) and (study_id := _text(study.get("study_id"))) is not None:
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _ai_reviewer_request_refreshes(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    apply: bool,
) -> list[dict[str, Any]]:
    refreshes: list[dict[str, Any]] = []
    for study_id in study_ids:
        refresh = request_refresh.ai_reviewer_request_refresh(
            study_root=_study_root(profile, study_id),
            study_id=study_id,
            apply=apply,
        )
        if refresh is not None:
            refreshes.append(refresh)
    return refreshes


def _apply_progress_first_closeout_to_request_tasks(
    *,
    request_tasks: list[dict[str, Any]],
    owner_callable_adapters: list[dict[str, Any]],
) -> None:
    admissions_by_identity: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    for dispatch in owner_callable_adapters:
        admission = _mapping(dispatch.get("progress_first_closeout_admission"))
        if _text(admission.get("admission_status")) != "blocked":
            continue
        identity = (_text(dispatch.get("study_id")), _text(dispatch.get("action_type")))
        admissions_by_identity[identity] = admission
    if not admissions_by_identity:
        return
    for task in request_tasks:
        admission = admissions_by_identity.get((_text(task.get("study_id")), _text(task.get("action_type"))))
        if admission is None:
            continue
        task["dispatch_status"] = "blocked"
        task["blocked_reason"] = _text(admission.get("blocked_reason"))
        task["progress_first_closeout_admission"] = dict(admission)
        handoff = dict(_mapping(task.get("handoff_packet")))
        handoff["progress_first_closeout_admission"] = dict(admission)
        handoff["blocked_reason"] = _text(admission.get("blocked_reason"))
        task["handoff_packet"] = handoff


def _dispatch_status_count(dispatches: list[dict[str, Any]], status: str) -> int:
    return sum(_text(dispatch.get("dispatch_status")) == status for dispatch in dispatches)


def current_owner_callable_adapters(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    dispatch_ready_for_execution: bool = False,
) -> dict[str, Any]:
    return current_owner_callable_adapters_part.current_owner_callable_adapters(
        profile=profile,
        study_ids=study_ids,
        mode=mode,
        apply=apply,
        generated_at=_utc_now(),
        dispatch_ready_for_execution=dispatch_ready_for_execution,
        read_json_object=request_refresh.read_json_object,
        scan_latest_path=_scan_latest_path,
        resolve_study_ids_from_scan=_resolve_study_ids_from_scan,
        selected_actions=_selected_actions,
        owner_callable_dispatch=lambda **kwargs: transition_projection_boundary.with_transition_request_projection(
            _owner_callable_dispatch(**kwargs)
        ),
        domain_progress_transition_request_projection=transition_request_projection.domain_progress_transition_request_projection,
        owner_from_action=_owner_from_action,
        required_output_surface=_required_output_surface,
        text=_text,
    )


def materialize_domain_action_requests(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    dispatch_ready_for_execution: bool = False,
) -> dict[str, Any]:
    generated_at = _utc_now()
    scan_payload = request_refresh.read_json_object(_scan_latest_path(profile)) or {}
    resolved_study_ids = _resolve_study_ids_from_scan(scan_payload, study_ids)
    selected_request_actions, ignored_actions = _selected_actions(
        profile=profile,
        scan_payload=scan_payload,
        study_ids=resolved_study_ids,
    )
    request_tasks = [
        _with_transition_request_task_semantics(
            _request_task(
                profile=profile,
                action=action,
            )
        )
        for action in selected_request_actions
    ]
    owner_callable_adapters = [
        transition_projection_boundary.with_transition_request_projection(
            _owner_callable_dispatch(
                profile=profile,
                action=action,
                action_type=_text(action.get("action_type")) or "unknown_action",
                next_executable_owner=_owner_from_action(
                    action,
                    _text(action.get("action_type")) or "unknown_action",
                ),
                required_output_surface=_required_output_surface(
                    action,
                    _text(action.get("action_type")) or "unknown_action",
                ),
                apply=apply,
                scan_payload=scan_payload,
                generated_at=generated_at,
            )
        )
        for action in selected_request_actions
    ]
    _apply_progress_first_closeout_to_request_tasks(
        request_tasks=request_tasks,
        owner_callable_adapters=owner_callable_adapters,
    )
    request_task_refs = request_task_projection.request_task_ref_projections(
        request_tasks,
        schema_version=SCHEMA_VERSION,
        target_runtime_owner=TARGET_RUNTIME_OWNER,
        transition_runtime_postcondition=transition_projection_boundary.runtime_postcondition(),
        authority_boundary=transition_projection_boundary.authority_boundary(),
    )
    legacy_request_task_diagnostics = request_task_projection.legacy_request_task_diagnostics(
        request_task_refs,
        schema_version=SCHEMA_VERSION,
    )
    transition_requests = transition_request_projection.domain_progress_transition_request_projection(owner_callable_adapters)
    ai_reviewer_request_refreshes: list[dict[str, Any]] = []
    written_files: list[str] = []
    ai_reviewer_request_refreshes = _ai_reviewer_request_refreshes(
        profile=profile,
        study_ids=resolved_study_ids,
        apply=False,
    )
    written_files = [
        refresh["request_path"]
        for refresh in ai_reviewer_request_refreshes
        if refresh.get("written") is True and _text(refresh.get("request_path"))
    ]

    payload = with_owner_callable_adapter_projection({
        "surface": "domain_action_request_materializer",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "source_surface": str(_scan_latest_path(profile)),
        "dry_run": not apply,
        "requested_studies": list(resolved_study_ids),
        "requested_mode": mode,
        "effective_mode": "opl_execution_authorization",
        "execution_authorization_owner": "one-person-lab",
        "execution_authorization_contract_ref": (
            "one-person-lab:contracts/opl-framework/stage-run-kernel-contract.json"
            "#execution_authorization_policy"
        ),
        "apply_allowed": False,
        "apply_writes_domain_intent_projection_only": True,
        "apply_writes_disabled_reason": "opl_domain_progress_transition_runtime_owns_durable_carrier",
        "mas_local_dispatch_carrier_persistence": "forbidden",
        "mas_local_request_packet_persistence": "forbidden",
        "opl_transition_runtime_required_for_durable_carrier": True,
        "opl_transition_runtime_postcondition": transition_projection_boundary.runtime_postcondition(),
        "dispatch_ready_for_execution_preview": False,
        "dispatch_ready_for_execution_preview_requested": bool(dispatch_ready_for_execution and not apply),
        "dispatch_ready_for_execution_preview_blocked_reason": (
            "opl_execution_authorization_required"
            if dispatch_ready_for_execution and not apply
            else None
        ),
        "mas_creates_owner_callable_carrier": False,
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "domain_progress_transition_request_count": len(transition_requests),
        "ready_domain_progress_transition_request_count": _dispatch_status_count(
            transition_requests,
            "ready",
        ),
        "blocked_domain_progress_transition_request_count": _dispatch_status_count(
            transition_requests,
            "blocked",
        ),
        "transition_request_pending_domain_progress_transition_request_count": (
            _dispatch_status_count(transition_requests, "transition_request_pending")
        ),
        "domain_progress_transition_requests": transition_requests,
        "runtime_control_owner": "one-person-lab",
        "target_runtime_owner": TARGET_RUNTIME_OWNER,
        "adapter_kind": OWNER_CALLABLE_ADAPTER_KIND,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "mas_dispatch_authority": False,
        "authority_boundary": transition_projection_boundary.authority_boundary(),
        "request_task_count": len(request_task_refs),
        "request_task_projection_scope": "legacy_diagnostic_identity_refs_only",
        "request_task_body_omitted": True,
        "request_task_counts_authority": False,
        "request_task_readiness_authority": False,
        "request_tasks_alias_retired": True,
        "request_tasks_retired_reason": "legacy_top_level_alias_removed_use_legacy_request_task_diagnostics_refs",
        "request_tasks_replacement": "legacy_request_task_diagnostics.legacy_request_task_refs",
        "legacy_request_task_diagnostics": legacy_request_task_diagnostics,
        "ai_reviewer_request_refresh_count": len(ai_reviewer_request_refreshes),
        "ai_reviewer_request_refreshes": ai_reviewer_request_refreshes,
        "legacy_owner_callable_adapter_diagnostics": legacy_owner_callable_adapter_diagnostics(
            {"owner_callable_adapters": owner_callable_adapters}
        ),
        "repeat_suppressed_count": sum(item.get("repeat_suppressed") is True for item in owner_callable_adapters),
        "ignored_actions": ignored_actions,
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "merge_cleanup_checklist": list(MERGE_CLEANUP_CHECKLIST),
        "written_files": written_files,
        "refs": {
            "latest_path": str(materializer_core.consumer_latest_path(profile)),
            "history_path": str(materializer_core.consumer_history_path(profile)),
        },
    })
    return payload


__all__ = [
    "CONSUMER_LATEST_RELATIVE_PATH",
    "FORBIDDEN_SURFACES",
    "RETIRED_ABSENT_SURFACES",
    "SCHEMA_VERSION",
    "SUPPORTED_REQUEST_ACTION_TYPES",
    "current_owner_callable_adapters",
    "materialize_domain_action_requests",
]
