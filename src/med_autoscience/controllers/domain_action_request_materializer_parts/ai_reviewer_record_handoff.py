from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries import (
    domain_progress_transition_request_transport_fields,
)
from med_autoscience.controllers.paper_progress_policy_adapter import build_transition_request
from med_autoscience.controllers.domain_owner_action_dispatch_parts.action_execution.ai_reviewer_record_production import (
    build_ai_reviewer_record_production_request,
    build_ai_reviewer_record_worker_handoff,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import currentness_identity
from med_autoscience.medical_prose_review import stable_medical_prose_review_path
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import repeat_suppression


AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS = frozenset(
    domain_action_request_lifecycle.AI_REVIEWER_RECORD_PRODUCTION_BLOCKED_REASONS_BY_WORK_UNIT
)
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


def ai_reviewer_record_production_handoff_dispatch(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    dispatch_path: Path,
    owner_route: Mapping[str, Any],
    source_action_ref: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> dict[str, Any] | None:
    if action_type != "return_to_ai_reviewer_workflow":
        return None
    work_unit_id = _record_production_work_unit_id(action=action, owner_route=owner_route)
    reason = _record_production_reason(action=action, owner_route=owner_route, work_unit_id=work_unit_id)
    if reason is None:
        return None
    study_root = profile.studies_root / study_id
    request = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root) or {
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or study_id,
        "request_kind": action_type,
        "request_owner": "ai_reviewer",
    }
    request_kind = work_unit_id if work_unit_id in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS else reason
    required_currentness_refs = _record_production_required_currentness_refs(action=action, request=request)
    stale_record_ref = _text(action.get("stale_record_ref")) or _text(
        _mapping(request.get("request_lifecycle")).get("stale_record_ref")
    )
    production_request = build_ai_reviewer_record_production_request(
        request=request,
        required_refs=_record_production_required_input_refs(request, study_root=study_root),
        stale_record_ref=stale_record_ref,
        required_currentness_refs=required_currentness_refs,
        request_kind=request_kind,
    )
    production_request["request_blocked_reason"] = reason
    dispatch = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request,
        dispatch={"owner_route": owner_route, "prompt_contract": {"owner_route": owner_route}},
        production_request=production_request,
    )
    transition_owner_route = _with_route_currentness_basis(
        _mapping(dispatch.get("owner_route")) or dict(owner_route),
        source_route=owner_route,
        action=action,
    )
    dispatch["owner_route"] = transition_owner_route
    owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(dispatch=dispatch)
    work_unit_fingerprint = _record_production_route_fingerprint(transition_owner_route)
    source_generation = work_unit_fingerprint or _text(dispatch.get("source_fingerprint"))
    transition_request = build_transition_request(
        study_id=study_id,
        quest_id=_text(dispatch.get("quest_id")) or study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        next_owner=_text(dispatch.get("next_executable_owner")),
        source_generation=source_generation,
        expected_version=source_generation,
        dispatch_authority=_text(dispatch.get("dispatch_authority")),
        required_output_surface=_text(dispatch.get("required_output_surface")),
        currentness_basis=_record_production_route_basis(transition_owner_route),
        idempotency_context={
            "kind": "ai-reviewer-record-transition-request",
            "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        },
    )
    dispatch["action_id"] = _text(action.get("action_id")) or dispatch.get("action_id")
    dispatch["blocked_reason"] = None
    dispatch["owner_route_attempt_envelope"] = dict(owner_route_attempt_envelope)
    dispatch["repeat_suppressed"] = False
    dispatch["why_not_applied"] = None
    dispatch["opl_domain_progress_transition_request"] = transition_request
    dispatch["provider_admission_pending"] = False
    dispatch["provider_admission_requires_opl_runtime_result"] = True
    dispatch.update(domain_progress_transition_request_transport_fields())
    dispatch["refs"] = {**_mapping(dispatch.get("refs")), "dispatch_path": str(dispatch_path)}
    dispatch["source_action"] = {
        **source_action_ref(action),
        **_mapping(dispatch.get("source_action")),
        "reason": reason,
        "next_work_unit": request_kind,
        "controller_work_unit_id": _text(action.get("controller_work_unit_id")) or request_kind,
        "executable_work_unit": _text(action.get("executable_work_unit")) or request_kind,
        "required_currentness_refs": list(required_currentness_refs),
        "record_only_surface": True,
        "publication_eval_latest_write_allowed": False,
        "controller_decision_write_allowed": False,
    }
    dispatch["source_action_runtime_completion_fields_omitted"] = sorted(
        key for key in action if key in RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS
    )
    satisfaction = _record_production_satisfaction(
        study_root=study_root,
        request=request,
        owner_route=owner_route,
        required_currentness_refs=required_currentness_refs,
    )
    if satisfaction is not None:
        dispatch["dispatch_status"] = "repeat_suppressed"
        dispatch["blocked_reason"] = repeat_suppression.REPEAT_SUPPRESSED_REASON
        dispatch["repeat_suppressed"] = True
        dispatch["why_not_applied"] = repeat_suppression.REPEAT_SUPPRESSED_REASON
        dispatch["repeat_suppression"] = {
            "repeat_suppressed": True,
            "why_not_applied": repeat_suppression.REPEAT_SUPPRESSED_REASON,
            "work_unit_fingerprint": work_unit_fingerprint,
            "repeat_suppression_key": work_unit_fingerprint,
            "suppression_source": "ai_reviewer_record_production_output_satisfied",
        }
        dispatch["record_production_satisfaction"] = satisfaction
    return dispatch


def _record_production_satisfaction(
    *,
    study_root: Path,
    request: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    required_currentness_refs: list[str],
) -> dict[str, Any] | None:
    refreshed = domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=request,
    )
    lifecycle = _mapping(refreshed.get("request_lifecycle"))
    record = _mapping(refreshed.get("ai_reviewer_record"))
    record_ref = _text(refreshed.get("publication_eval_record_ref"))
    eval_id = _text(record.get("eval_id"))
    if not record or record_ref is None or eval_id is None:
        latest = _latest_record_matching_owner_route_basis(
            study_root=study_root,
            owner_route=owner_route,
        )
        if latest is not None:
            record, record_ref = latest
            eval_id = _text(record.get("eval_id"))
    if not record or record_ref is None or eval_id is None:
        return None
    route_basis_matched = _record_matches_owner_route_basis(record=record, owner_route=owner_route)
    if _text(lifecycle.get("blocked_reason")) is not None and not route_basis_matched:
        return None
    if not required_currentness_refs and not route_basis_matched:
        return None
    return {
        "status": "satisfied",
        "reason": "ai_reviewer_record_production_output_satisfied",
        "record_ref": record_ref,
        "eval_id": eval_id,
        "required_currentness_refs": list(required_currentness_refs),
        "owner_route_basis": _record_production_route_basis(owner_route) or None,
    }


def _latest_record_matching_owner_route_basis(
    *,
    study_root: Path,
    owner_route: Mapping[str, Any],
) -> tuple[dict[str, Any], str] | None:
    for path in sorted(
        (
            candidate
            for candidate in (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").glob(
                "*_publication_eval_record.json"
            )
            if candidate.is_file()
        ),
        key=lambda candidate: candidate.name,
        reverse=True,
    ):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        record = dict(payload)
        if _text(record.get("eval_id")) is None:
            continue
        if _record_matches_owner_route_basis(record=record, owner_route=owner_route):
            return record, str(path.resolve())
    return None


def _record_matches_owner_route_basis(
    *,
    record: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    basis = _record_production_route_basis(owner_route)
    if not basis:
        return False
    record_basis = _record_production_record_basis(record)
    expected_fingerprint = _text(basis.get("work_unit_fingerprint"))
    actual_fingerprint = _text(record_basis.get("work_unit_fingerprint"))
    if expected_fingerprint is not None:
        if actual_fingerprint != expected_fingerprint:
            return False
        identity_matched = True
    else:
        identity_matched = False
    expected_work_unit = _text(basis.get("work_unit_id"))
    actual_work_unit = _text(record_basis.get("work_unit_id"))
    if expected_work_unit is not None:
        if actual_work_unit is not None and actual_work_unit != expected_work_unit:
            return False
        if actual_work_unit == expected_work_unit:
            identity_matched = True
    if not identity_matched:
        return False
    for field in ("runtime_health_epoch", "source_eval_id"):
        expected = _text(basis.get(field))
        actual = _text(record_basis.get(field))
        if expected is not None and actual is not None and actual != expected:
            return False
    return True


def _record_production_record_basis(record: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(record.get("assessment_provenance"))
    reviewer_os = _mapping(record.get("reviewer_operating_system"))
    input_bundle = _mapping(reviewer_os.get("input_bundle"))
    provenance_basis = _mapping(provenance.get("owner_route_currentness_basis"))
    input_basis = _mapping(input_bundle.get("owner_route_currentness_basis"))
    record_basis = _mapping(record.get("owner_route_currentness_basis"))
    return {
        field: (
            _text(provenance_basis.get(field))
            or _text(provenance.get(field))
            or _text(input_basis.get(field))
            or _text(input_bundle.get(field))
            or _text(record_basis.get(field))
            or _text(record.get(field))
        )
        for field in (
            "source_eval_id",
            "work_unit_id",
            "work_unit_fingerprint",
            "truth_epoch",
            "runtime_health_epoch",
        )
    }


def _record_production_route_basis(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    return currentness_identity.owner_route_basis(owner_route)


def _with_route_currentness_basis(
    owner_route: Mapping[str, Any],
    *,
    source_route: Mapping[str, Any],
    action: Mapping[str, Any],
) -> dict[str, Any]:
    route = dict(owner_route)
    basis = currentness_identity.currentness_basis(
        _record_production_route_basis(route),
        _record_production_route_basis(source_route),
        currentness_identity.action_basis(action),
    )
    if not basis:
        return route
    return currentness_identity.with_owner_route_basis(route, basis=basis)


def _record_production_route_fingerprint(owner_route: Mapping[str, Any]) -> str | None:
    basis = _record_production_route_basis(owner_route)
    source_refs = _mapping(owner_route.get("source_refs"))
    return (
        _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(owner_route.get("idempotency_key"))
    )


def _record_production_work_unit_id(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> str | None:
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(_mapping(owner_route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    return (
        _text(action.get("controller_work_unit_id"))
        or _text(action.get("executable_work_unit"))
        or _work_unit_id(action.get("next_work_unit"))
        or _text(source_refs.get("work_unit_id"))
        or _text(basis.get("work_unit_id"))
    )


def _record_production_reason(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    work_unit_id: str | None,
) -> str | None:
    if work_unit_id in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS:
        return domain_action_request_lifecycle.AI_REVIEWER_RECORD_PRODUCTION_BLOCKED_REASONS_BY_WORK_UNIT[
            work_unit_id
        ]
    reason = _text(action.get("reason")) or _text(owner_route.get("owner_reason"))
    if reason in set(domain_action_request_lifecycle.AI_REVIEWER_RECORD_PRODUCTION_BLOCKED_REASONS_BY_WORK_UNIT.values()):
        return reason
    owner_contract = _mapping(owner_route.get("owner_reason_contract"))
    required_output = _text(action.get("required_output_surface")) or _text(owner_contract.get("required_output"))
    if required_output != "artifacts/publication_eval/latest.json":
        return None
    forbidden_surfaces = {
        surface for item in owner_contract.get("forbidden_surfaces") or [] if (surface := _text(item)) is not None
    }
    if "artifacts/publication_eval/latest.json" not in forbidden_surfaces:
        return None
    return reason or "ai_reviewer_record_production_required"


def _record_production_required_currentness_refs(
    *,
    action: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    refs = _string_items(action.get("required_currentness_refs"))
    if refs:
        return refs
    lifecycle = _mapping(request.get("request_lifecycle"))
    return _string_items(lifecycle.get("required_currentness_refs"))


def _record_production_required_input_refs(
    request: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, str | None]:
    required = _mapping(_mapping(request.get("input_contract")).get("required_refs"))
    refs: dict[str, str | None] = {}
    for surface, payload in required.items():
        if text := _text(_mapping(payload).get("path")) or _text(payload):
            refs[str(surface)] = text
    stable_prose_review = stable_medical_prose_review_path(study_root=study_root)
    if stable_prose_review.exists():
        refs["medical_prose_review"] = str(stable_prose_review)
    return refs


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["ai_reviewer_record_production_handoff_dispatch"]
