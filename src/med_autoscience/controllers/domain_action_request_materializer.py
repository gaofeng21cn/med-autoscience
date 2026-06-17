from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers import progress_first_closeout
from med_autoscience.controllers.runtime_ai_repair_policy import (
    default_executor_policy,
    two_layer_ai_repair_policy_payload,
)
from med_autoscience.controllers.owner_callable_adapter_projection import (
    with_owner_callable_adapter_projection,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    has_opl_transition_readback,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries import (
    domain_progress_transition_request_transport_fields,
)
from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    ai_reviewer_record_handoff,
    current_default_executor_dispatches as current_default_executor_dispatches_part,
    current_action_selection,
    current_writer_handoff,
    default_executor_prompt,
    execution_gate,
    persistence,
    publication_owner_materialization,
    supervisor_request_packets,
    writer_handoff_preservation,
)
from med_autoscience.controllers import medical_paper_readiness_payload_authoring
from med_autoscience.controllers.domain_owner_action_dispatch_parts import output_readiness
from med_autoscience.controllers.default_executor_action_policy import (
    ALLOWED_WRITE_SURFACES,
    FORBIDDEN_SURFACES,
    RETIRED_ABSENT_SURFACES,
    SOURCE_ACTION_REF_FIELDS,
    SOURCE_HANDOFF_REF_FIELDS,
    SUPPORTED_ACTION_TYPES as SUPPORTED_REQUEST_ACTION_TYPES,
    default_executor_search_discipline,
    request_output_surface_for_action_type,
    request_output_target_surface_for_action_type,
    request_owner_for_action_type,
    request_packet_ref_for_action_type,
    request_packet_ref_for_dispatch,
)
from med_autoscience.controllers.owner_route_reconcile import SUPERVISION_LATEST_RELATIVE_PATH
from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import repeat_suppression


SCHEMA_VERSION = 1
CONSUMER_LATEST_RELATIVE_PATH = Path("runtime/artifacts/supervision/consumer/latest.json")
CONSUMER_HISTORY_RELATIVE_PATH = Path("runtime/artifacts/supervision/consumer/history.jsonl")
DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT = Path(
    "artifacts/supervision/consumer/default_executor_dispatches"
)
OWNER_CALLABLE_ADAPTER_KIND = "opl_authorized_owner_callable_adapter"
TARGET_RUNTIME_OWNER = "one-person-lab"
SUPPORTED_MODE = "developer_apply_safe"
RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS = frozenset(
    {
        "provider_completion",
        "running_worker",
        "queue_status",
        "retry_budget_remaining",
        "domain_completion",
        "stage_state",
        "provider_completion_is_domain_completion",
        "provider_completion_is_stage_state",
        "queue_succeeded_is_domain_completion",
        "retry_budget_is_domain_completion",
        "running_worker_is_stage_state",
    }
)
READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
MERGE_CLEANUP_CHECKLIST = [
    "focused pytest green",
    "git diff --check green",
    "review diff touches only owned files",
    "merge branch into main after parallel worker coordination",
    "remove worktree after absorb",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _nested_mapping(value: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    payload: Mapping[str, Any] = value
    for key in keys:
        payload = _mapping(payload.get(key))
    return dict(payload)


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _request_packet_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    if action_type not in SUPPORTED_REQUEST_ACTION_TYPES:
        raise ValueError(f"unsupported supervisor request action_type: {action_type}")
    return _study_root(profile, study_id) / _request_packet_ref_for_action_type(action_type)


def _default_executor_dispatch_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    return _study_root(profile, study_id) / DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT / f"{action_type}.json"


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def _consumer_history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_HISTORY_RELATIVE_PATH


def _current_scan_study(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any] | None:
    for study in scan_payload.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return None


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


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _request_owner_for_action_type(action_type: str) -> str:
    return request_owner_for_action_type(action_type)


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _request_owner_for_action_type(action_type)
    )


def _request_output_surface_for_action_type(action_type: str) -> str:
    return request_output_surface_for_action_type(action_type)


def _request_output_target_surface_for_action_type(action_type: str) -> dict[str, object] | None:
    return request_output_target_surface_for_action_type(action_type)


def _request_packet_ref_for_action_type(action_type: str) -> str:
    return request_packet_ref_for_action_type(action_type)


def _request_packet_ref_for_dispatch(action_type: str) -> str | None:
    return request_packet_ref_for_dispatch(action_type)


def _source_action_ref(action: Mapping[str, Any]) -> dict[str, Any]:
    source_ref = {key: action[key] for key in SOURCE_ACTION_REF_FIELDS if key in action}
    for key in ("work_unit_id", "work_unit_fingerprint", "action_fingerprint", "required_delta_kind"):
        if key in action and key not in source_ref:
            source_ref[key] = action[key]
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
        or _request_output_surface_for_action_type(action_type)
    )


def _default_executor_forbidden_surfaces(owner_route: Mapping[str, Any]) -> list[str]:
    forbidden = list(FORBIDDEN_SURFACES)
    for item in _mapping(owner_route.get("owner_reason_contract")).get("forbidden_surfaces") or []:
        if (surface := _text(item)) is not None and surface not in forbidden:
            forbidden.append(surface)
    return forbidden


def _readiness_dispatch_enrichment(
    action: Mapping[str, Any],
    action_type: str,
    *,
    profile: WorkspaceProfile | None = None,
) -> dict[str, Any]:
    if action_type != READINESS_ACTION_TYPE:
        return {}
    handoff_packet = _mapping(action.get("handoff_packet"))
    surface_key = (
        _text(action.get("surface_key"))
        or _text(handoff_packet.get("surface_key"))
        or _text(_mapping(action.get("next_action")).get("surface_key"))
        or _text(_mapping(handoff_packet.get("next_action")).get("surface_key"))
    )
    if surface_key is None:
        return {}
    readiness_surface_identity = {
        "action_type": READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "source": _text(action.get("source"))
        or _text(handoff_packet.get("source"))
        or "current_owner_action",
    }
    operator_payload = (
        _mapping(action.get("operator_payload"))
        or _mapping(action.get("medical_paper_readiness_payload"))
        or _mapping(handoff_packet.get("operator_payload"))
        or _mapping(handoff_packet.get("medical_paper_readiness_payload"))
    )
    if not operator_payload and profile is not None:
        study_id = _text(action.get("study_id")) or _text(handoff_packet.get("study_id"))
        if study_id:
            authored = medical_paper_readiness_payload_authoring.author_operator_payload(
                study_root=_study_root(profile, study_id),
                surface_key=surface_key,
            )
            if _text(authored.get("status")) != "blocked":
                operator_payload = authored
    payload_authoring_target = {
        "surface": "medical_paper_readiness_operator_payload_authoring_target",
        "schema_version": SCHEMA_VERSION,
        "study_id": _text(action.get("study_id")),
        "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
        "action_type": READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "operator_payload": operator_payload or None,
        "operator_payload_contract": {
            "required": ["operator_payload"],
            "payload_owner": "MedAutoScience",
            "surface_key": surface_key,
            "payload_must_be_domain_authored": True,
            "empty_payload_is_not_success_evidence": True,
        },
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    request_packet_ref = _request_packet_ref_for_action_type(READINESS_ACTION_TYPE)
    return {
        "readiness_surface_identity": readiness_surface_identity,
        "surface_key": surface_key,
        "operator_payload_ref": request_packet_ref,
        "medical_paper_readiness_payload_ref": request_packet_ref,
        "operator_payload_present": bool(operator_payload),
        "operator_payload": operator_payload if operator_payload else None,
        "medical_paper_readiness_payload": operator_payload if operator_payload else None,
        "payload_authoring_target": payload_authoring_target,
    }


def _default_executor_dispatch(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    required_output_surface: str,
    apply: bool,
    developer_mode_payload: Mapping[str, Any],
    scan_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    dispatch_path = _default_executor_dispatch_path(profile, study_id, action_type)
    executor_policy = default_executor_policy()
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
    typed_closeout_contract = default_executor_typed_closeout_contract(action_type=action_type)
    forbidden_surfaces = _default_executor_forbidden_surfaces(owner_route)
    required_output_target_surface = _request_output_target_surface_for_action_type(action_type)
    readiness_dispatch = _readiness_dispatch_enrichment(action, action_type, profile=profile)
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
        "tool_discipline": default_executor_search_discipline(),
        "search_boundaries": default_executor_search_discipline(),
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
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
    owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(
        dispatch=dispatch_shell
    )
    execution_ready_dispatch_requested = developer_mode_payload.get("dry_run_executor_dispatch") is True
    dispatch_status = (
        "ready"
        if (apply or execution_ready_dispatch_requested)
        and _text(developer_mode_payload.get("mode")) == SUPPORTED_MODE
        and developer_mode_payload.get("safe_actions_enabled") is True
        and owner_route_attempt_envelope.get("dispatchable") is True
        and owner_route_allows_action
        else "dry_run" if not apply else "blocked"
    )
    blocked_reason = _default_executor_dispatch_blocked_reason(
        dispatch_status=dispatch_status,
        developer_mode_payload=developer_mode_payload,
        action=action,
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        owner_route=owner_route,
        owner_route_attempt_envelope=owner_route_attempt_envelope,
    )
    current_study = _current_scan_study(scan_payload, study_id)
    repeat_guard = repeat_suppression.dispatch_repeat_suppression(
        dispatch={"prompt_contract": prompt_contract, "owner_route": owner_route, "dispatch_status": dispatch_status},
        current_study=current_study,
        existing_dispatch=persistence.read_json_object(dispatch_path),
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
    return _default_executor_dispatch_payload(
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
        developer_mode_payload=developer_mode_payload,
        readiness_dispatch=readiness_dispatch,
        progress_first_closeout_admission=closeout_admission,
        generated_at=generated_at,
    )


def _with_transition_request_projection(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(dispatch)
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _transition_request_for_owner_callable_adapter(payload)
    if transition_request:
        payload["opl_domain_progress_transition_request"] = transition_request
    payload["provider_admission_pending"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    payload.update(domain_progress_transition_request_transport_fields())

    prompt_contract = dict(_mapping(payload.get("prompt_contract")))
    if transition_request:
        prompt_contract["opl_domain_progress_transition_request"] = transition_request
    prompt_contract["provider_admission_pending"] = False
    prompt_contract["provider_admission_requires_opl_runtime_result"] = True
    prompt_contract.update(domain_progress_transition_request_transport_fields())
    payload["prompt_contract"] = prompt_contract

    if _text(payload.get("dispatch_status")) == "ready" and not _has_opl_execution_proof(payload):
        payload["dispatch_status"] = "transition_request_pending"
        payload["blocked_reason"] = "opl_execution_authorization_required"
        payload["owner_callable_surface"] = None
        payload["dispatch_ready_for_execution_authority"] = False
        payload["mas_dispatch_authority"] = False
        payload["mas_local_dispatch_carrier_persistence"] = "forbidden"
        payload["opl_transition_runtime_required_for_durable_carrier"] = True
        prompt_contract["dispatch_status"] = "transition_request_pending"
        prompt_contract["owner_callable_surface"] = None
    return payload


def _transition_request_for_owner_callable_adapter(payload: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _text(payload.get("study_id")) or "unknown-study"
    action_type = _text(payload.get("action_type")) or "unknown_action"
    owner_route = _mapping(payload.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    work_unit_id = (
        _text(payload.get("work_unit_id"))
        or _text(source_refs.get("materialized_work_unit_id"))
        or _text(source_refs.get("work_unit_id"))
        or _text(_mapping(payload.get("source_action")).get("next_work_unit"))
    )
    work_unit_fingerprint = (
        _text(payload.get("work_unit_fingerprint"))
        or _text(payload.get("action_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(payload.get("repeat_suppression_key"))
    )
    return paper_progress_policy_adapter.build_transition_request(
        study_id=study_id,
        quest_id=_text(payload.get("quest_id")) or study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        next_owner=_text(payload.get("next_executable_owner")),
        source_generation=_text(owner_route.get("source_fingerprint")) or work_unit_fingerprint,
        expected_version=work_unit_fingerprint,
        dispatch_ref=_text(_mapping(payload.get("refs")).get("dispatch_path")),
        dispatch_authority=_text(payload.get("dispatch_authority")),
        required_output_surface=_text(payload.get("required_output_surface")),
        currentness_basis=currentness_basis,
        idempotency_context={
            "action_id": _text(payload.get("action_id")),
            "idempotency_key": _text(payload.get("idempotency_key")),
            "dispatch_authority": _text(payload.get("dispatch_authority")),
        },
    )


def _has_opl_execution_proof(payload: Mapping[str, Any]) -> bool:
    if any(has_opl_transition_readback(item) for item in _iter_payloads(payload)):
        return True
    return any(
        first_trusted_opl_execution_authorization(
            item.get("opl_execution_authorization"),
            item.get("opl_provider_attempt"),
            item.get("stage_attempt"),
        )
        is not None
        for item in _iter_payloads(payload)
    )


def _iter_payloads(value: object) -> list[Mapping[str, Any]]:
    payloads: list[Mapping[str, Any]] = []
    stack = [value]
    seen: set[int] = set()
    while stack:
        item = stack.pop()
        if isinstance(item, Mapping):
            identity = id(item)
            if identity in seen:
                continue
            seen.add(identity)
            payload = _mapping(item)
            payloads.append(payload)
            for key in (
                "prompt_contract",
                "owner_route",
                "source_action",
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
        if isinstance(item, (list, tuple)):
            stack.extend(candidate for candidate in item if isinstance(candidate, Mapping))
    return payloads


def _default_executor_dispatch_payload(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    dispatch_path: Path,
    executor_policy: Mapping[str, Any],
    next_executable_owner: str,
    required_output_surface: str,
    owner_route: Mapping[str, Any],
    idempotency_key: str | None,
    repeat_key: str | None,
    dispatch_status: str,
    blocked_reason: str | None,
    repeat_guard: Mapping[str, Any],
    typed_closeout_contract: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    readiness_dispatch: Mapping[str, Any],
    progress_first_closeout_admission: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    adapter_contract = _owner_callable_adapter_contract(
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        required_output_surface=required_output_surface,
    )
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": SCHEMA_VERSION,
        "adapter_kind": OWNER_CALLABLE_ADAPTER_KIND,
        "adapter_status": "intent_materialized",
        "domain_intent_kind": "mas_owner_callable_transition_request",
        "target_runtime_owner": TARGET_RUNTIME_OWNER,
        "target_runtime_owner_authority_required": True,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "mas_dispatch_authority": False,
        "dispatch_ready_for_execution_authority": False,
        "owner_callable_adapter_contract": adapter_contract,
        "authority_boundary": {
            "mas_materializes_domain_intent": True,
            "mas_creates_owner_callable_carrier": True,
            "mas_creates_opl_outbox": False,
            "mas_creates_opl_event": False,
            "mas_creates_opl_stage_run": False,
            "target_runtime_owner": TARGET_RUNTIME_OWNER,
            "execution_requires_opl_authorization": True,
        },
        **dict(executor_policy),
        "study_id": study_id,
        "quest_id": prompt_contract["quest_id"],
        "generated_at": generated_at,
        "action_type": action_type,
        "action_id": _text(action.get("action_id")),
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "work_unit_id": _text(action.get("work_unit_id")) or _text(action.get("next_work_unit")),
        "work_unit_fingerprint": _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint")),
        **dict(readiness_dispatch),
        **(
            {"required_output_target_surface": dict(prompt_contract["required_output_target_surface"])}
            if "required_output_target_surface" in prompt_contract
            else {}
        ),
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": _text(action.get("action_fingerprint")),
        "paper_progress_stall": _mapping(action.get("paper_progress_stall")) or None,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "execution_gate": execution_gate.projection(
            dispatch_status=dispatch_status,
            blocked_reason=blocked_reason,
            developer_mode_payload=developer_mode_payload,
            supported_mode=SUPPORTED_MODE,
        ),
        "provider_admission_effect": execution_gate.provider_admission_effect(
            dispatch_status=dispatch_status,
            blocked_reason=blocked_reason,
        ),
        "repeat_suppressed": bool(repeat_guard["repeat_suppressed"]),
        "why_not_applied": repeat_guard["why_not_applied"],
        "repeat_suppression": dict(repeat_guard),
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": dict(typed_closeout_contract),
        "owner_route_attempt_envelope": dict(owner_route_attempt_envelope),
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "default_executor_policy": dict(executor_policy),
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "prompt_contract": dict(prompt_contract),
        "domain_intent": _domain_intent(
            action=action,
            action_type=action_type,
            study_id=study_id,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
            owner_route=owner_route,
            adapter_contract=adapter_contract,
        ),
        "progress_first_closeout_admission": dict(progress_first_closeout_admission),
        "executor_prompt": default_executor_prompt.executor_prompt(
            action_type=action_type,
            study_id=study_id,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
            typed_closeout_contract=default_executor_typed_closeout_contract,
        ),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "source_action": _source_action_ref(action),
        "source_action_runtime_completion_fields_omitted": sorted(
            key for key in action if key in RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS
        ),
        "refs": {
            "scan_latest": str(_scan_latest_path(profile)),
            "dispatch_path": str(dispatch_path),
        },
    }


def _owner_callable_adapter_contract(
    *,
    action_type: str,
    next_executable_owner: str,
    required_output_surface: str,
) -> dict[str, Any]:
    return {
        "surface": "mas_owner_callable_adapter_contract",
        "schema_version": SCHEMA_VERSION,
        "adapter_kind": OWNER_CALLABLE_ADAPTER_KIND,
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "target_runtime_owner": TARGET_RUNTIME_OWNER,
        "execution_authority_owner": TARGET_RUNTIME_OWNER,
        "required_opl_proof": [
            "opl_execution_authorization",
            "opl_provider_attempt",
            "attempt_lease",
            "closeout_binding",
            "accepted_owner_gate_authority",
        ],
        "mas_private_outbox_forbidden": True,
        "mas_private_dispatch_authority_forbidden": True,
        "mas_stage_run_creation_forbidden": True,
        "provider_completion_is_domain_completion": False,
    }


def _domain_intent(
    *,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    next_executable_owner: str,
    required_output_surface: str,
    owner_route: Mapping[str, Any],
    adapter_contract: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface": "mas_domain_intent",
        "schema_version": SCHEMA_VERSION,
        "intent_kind": "owner_callable_transition_request",
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(_mapping(action.get("handoff_packet")).get("quest_id")),
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "work_unit_id": _text(action.get("work_unit_id")) or _text(action.get("next_work_unit")),
        "work_unit_fingerprint": _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint")),
        "target_runtime_owner": TARGET_RUNTIME_OWNER,
        "target_runtime_transition": "OPL Command/Event/Outbox/StageRun",
        "expected_domain_answer": "MAS OwnerAnswer",
        "expected_projection": "Derived Projection",
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "owner_route": dict(owner_route) if owner_route else None,
        "adapter_contract": dict(adapter_contract),
    }


def _default_executor_dispatch_blocked_reason(
    *,
    dispatch_status: str,
    developer_mode_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    owner_route: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
) -> str | None:
    if dispatch_status != "blocked":
        return None
    if reason := _github_block_reason(developer_mode_payload):
        return reason
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
        return None
    return "owner_route_next_owner_mismatch"


def _request_task(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    action_type = _text(action.get("action_type")) or "unknown_action"
    action_payload = {**dict(action), "study_root": str(_study_root(profile, study_id))}
    return supervisor_request_packets.request_task(
        action=action_payload,
        schema_version=SCHEMA_VERSION,
        developer_mode_payload=developer_mode_payload,
        apply=apply,
        supported_mode=SUPPORTED_MODE,
        packet_path=_request_packet_path(profile, study_id, action_type),
        scan_latest_path=_scan_latest_path(profile),
        forbidden_surfaces=FORBIDDEN_SURFACES,
        allowed_write_surfaces=ALLOWED_WRITE_SURFACES,
    )


def _with_transition_request_task_semantics(task: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(task)
    if _text(payload.get("dispatch_status")) == "applied":
        payload["dispatch_status"] = "transition_request_pending"
        payload["blocked_reason"] = "opl_execution_authorization_required"
    payload["mas_local_request_packet_persistence"] = "forbidden"
    payload["opl_transition_runtime_required_for_durable_carrier"] = True
    payload["provider_admission_pending"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    handoff = dict(_mapping(payload.get("handoff_packet")))
    handoff["dispatch_status"] = "transition_request_pending"
    handoff["provider_admission_pending"] = False
    handoff["provider_admission_requires_opl_runtime_result"] = True
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


def _ai_reviewer_request_refresh(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any] | None:
    study_root = _study_root(profile, study_id)
    request_path = domain_action_request_lifecycle.stable_ai_reviewer_request_path(study_root=study_root)
    packet = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    if packet is None:
        return None
    refreshed = domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=packet,
    )
    changed = refreshed != packet
    if apply and changed:
        request_path.parent.mkdir(parents=True, exist_ok=True)
        persistence.write_json(request_path, refreshed)
    return {
        "surface": "ai_reviewer_request_refresh",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "request_path": str(request_path),
        "refresh_status": "refreshed" if changed else "unchanged",
        "written": bool(apply and changed),
        "publication_eval_record_ref": _text(refreshed.get("publication_eval_record_ref")),
        "attached_eval_id": _text(_mapping(refreshed.get("ai_reviewer_record")).get("eval_id")),
        "blocked_reason": _text(_mapping(refreshed.get("request_lifecycle")).get("blocked_reason")),
    }


def _ai_reviewer_request_refreshes(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    apply: bool,
) -> list[dict[str, Any]]:
    refreshes: list[dict[str, Any]] = []
    for study_id in study_ids:
        refresh = _ai_reviewer_request_refresh(profile=profile, study_id=study_id, apply=apply)
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


def current_default_executor_dispatches(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    dispatch_ready_for_execution: bool = False,
) -> dict[str, Any]:
    return current_default_executor_dispatches_part.current_default_executor_dispatches(
        profile=profile,
        study_ids=study_ids,
        mode=mode,
        apply=apply,
        generated_at=_utc_now(),
        supported_mode=SUPPORTED_MODE,
        dispatch_ready_for_execution=dispatch_ready_for_execution,
        read_json_object=persistence.read_json_object,
        scan_latest_path=_scan_latest_path,
        resolve_study_ids_from_scan=_resolve_study_ids_from_scan,
        selected_actions=_selected_actions,
        default_executor_dispatch=_default_executor_dispatch,
        owner_from_action=_owner_from_action,
        required_output_surface=_required_output_surface,
        text=_text,
    )


def current_owner_callable_adapters(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    dispatch_ready_for_execution: bool = False,
) -> dict[str, Any]:
    return current_default_executor_dispatches(
        profile=profile,
        study_ids=study_ids,
        mode=mode,
        apply=apply,
        dispatch_ready_for_execution=dispatch_ready_for_execution,
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
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="external_queue_consumer",
    )
    developer_mode_payload = developer_mode.to_dict()
    scan_payload = persistence.read_json_object(_scan_latest_path(profile)) or {}
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
                developer_mode_payload=developer_mode_payload,
                apply=apply,
            )
        )
        for action in selected_request_actions
    ]
    owner_callable_adapters = [
        _with_transition_request_projection(
            _default_executor_dispatch(
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
                developer_mode_payload=(
                    {
                        **developer_mode_payload,
                        "mode": SUPPORTED_MODE,
                        "safe_actions_enabled": True,
                        "dry_run_executor_dispatch": True,
                    }
                    if dispatch_ready_for_execution and not apply
                    else developer_mode_payload
                ),
                scan_payload=scan_payload,
                generated_at=generated_at,
            )
        )
        for action in selected_request_actions
    ]
    ready_owner_callable_adapter_count = _dispatch_status_count(owner_callable_adapters, "ready")
    blocked_owner_callable_adapter_count = _dispatch_status_count(owner_callable_adapters, "blocked")
    transition_request_pending_owner_callable_adapter_count = _dispatch_status_count(
        owner_callable_adapters,
        "transition_request_pending",
    )
    _apply_progress_first_closeout_to_request_tasks(
        request_tasks=request_tasks,
        owner_callable_adapters=owner_callable_adapters,
    )
    ai_reviewer_request_refreshes: list[dict[str, Any]] = []
    written_files: list[str] = []
    ai_reviewer_request_refreshes = _ai_reviewer_request_refreshes(
        profile=profile,
        study_ids=resolved_study_ids,
        apply=False,
    )

    payload = with_owner_callable_adapter_projection({
        "surface": "domain_action_request_materializer",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "source_surface": str(_scan_latest_path(profile)),
        "dry_run": not apply,
        "requested_studies": list(resolved_study_ids),
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "github_gate": dict(developer_mode.github_user_gate),
        "developer_supervisor_mode": developer_mode_payload,
        "apply_allowed": bool(apply and developer_mode.safe_actions_enabled),
        "apply_writes_domain_intent_projection_only": False,
        "apply_writes_disabled_reason": "opl_domain_progress_transition_runtime_owns_durable_carrier",
        "mas_local_dispatch_carrier_persistence": "forbidden",
        "mas_local_request_packet_persistence": "forbidden",
        "opl_transition_runtime_required_for_durable_carrier": True,
        "dispatch_ready_for_execution_preview": bool(dispatch_ready_for_execution and not apply),
        "runtime_control_owner": "one-person-lab",
        "target_runtime_owner": TARGET_RUNTIME_OWNER,
        "adapter_kind": OWNER_CALLABLE_ADAPTER_KIND,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "mas_dispatch_authority": False,
        "request_task_count": len(request_tasks),
        "request_tasks": request_tasks,
        "ai_reviewer_request_refresh_count": len(ai_reviewer_request_refreshes),
        "ai_reviewer_request_refreshes": ai_reviewer_request_refreshes,
        "owner_callable_adapter_count": len(owner_callable_adapters),
        "ready_owner_callable_adapter_count": ready_owner_callable_adapter_count,
        "blocked_owner_callable_adapter_count": blocked_owner_callable_adapter_count,
        "transition_request_pending_owner_callable_adapter_count": (
            transition_request_pending_owner_callable_adapter_count
        ),
        "owner_callable_adapters": owner_callable_adapters,
        "repeat_suppressed_count": sum(item.get("repeat_suppressed") is True for item in owner_callable_adapters),
        "ignored_actions": ignored_actions,
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "merge_cleanup_checklist": list(MERGE_CLEANUP_CHECKLIST),
        "written_files": written_files,
        "refs": {
            "latest_path": str(_consumer_latest_path(profile)),
            "history_path": str(_consumer_history_path(profile)),
        },
    })
    return payload


__all__ = [
    "CONSUMER_LATEST_RELATIVE_PATH",
    "FORBIDDEN_SURFACES",
    "RETIRED_ABSENT_SURFACES",
    "SCHEMA_VERSION",
    "SUPPORTED_REQUEST_ACTION_TYPES",
    "current_default_executor_dispatches",
    "current_owner_callable_adapters",
    "materialize_domain_action_requests",
]
