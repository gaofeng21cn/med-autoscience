from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_callable_closeout_contract import (
    owner_callable_typed_closeout_contract,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
)
from med_autoscience.controllers.opl_domain_progress_transition_contract import (
    mas_request_transport_fields as domain_progress_transition_request_transport_fields,
)
from med_autoscience.controllers.stage_outcome_authority import owner_route_attempt_policy
from med_autoscience.controllers.runtime_ai_repair_policy import owner_callable_policy
from med_autoscience.medical_prose_review import stable_medical_prose_review_path
from med_autoscience.policies.publication_critique import (
    FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS,
)
from med_autoscience.publication_eval_latest import canonicalize_ai_reviewer_publication_eval_record
from med_autoscience.publication_eval_record.validation import (
    _ALLOWED_GAP_GATE_KINDS,
    _ALLOWED_GAP_SEVERITIES,
    _ALLOWED_GAP_TYPES,
    _REQUIRED_DELIVERY_CONTEXT_REF_KEYS,
    _REQUIRED_RUNTIME_CONTEXT_REF_KEYS,
)

AI_REVIEWER_RECORD_OWNER_TARGET = (
    "med_autoscience.controllers.ai_reviewer_publication_eval:"
    "materialize_ai_reviewer_publication_eval_record"
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.stage_outcome_authority import owner_route_policy as owner_route_part
from med_autoscience.controllers.stage_outcome_authority import owner_route_attempt_policy

RECORD_OUTPUT_SURFACE = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
REQUEST_PACKET_REF = "artifacts/supervision/requests/ai_reviewer/latest.json"
ACTION_TYPE = "return_to_ai_reviewer_workflow"
RECORD_PRODUCTION_PAYLOAD_REF = (
    "artifacts/supervision/requests/ai_reviewer/record_production_payloads/"
    f"{ACTION_TYPE}_payload.json"
)
RECORD_PAYLOAD_AUTHORING_SURFACE = "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json"
RECORD_PAYLOAD_TARGET_GUARD_METADATA_FIELDS = [
    "stale_record_ref",
    "required_input_refs",
    "required_currentness_refs",
]
RECORD_PAYLOAD_TARGET_OWNER_EDITABLE_FIELDS = [
    *RECORD_PAYLOAD_TARGET_GUARD_METADATA_FIELDS,
    "record_payload",
]
DISPATCH_AUTHORITY = "ai_reviewer_record_production_handoff"
ALLOWED_WRITE_SURFACES = [RECORD_PAYLOAD_AUTHORING_SURFACE, RECORD_OUTPUT_SURFACE]
FORBIDDEN_SURFACES = [
    "paper/**",
    "manuscript/**",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    ".ds/**",
]
STALENESS_HANDOFF_REASONS = {
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
}
RECORD_PRODUCTION_HANDOFF_REASONS = {
    *STALENESS_HANDOFF_REASONS,
    "ai_reviewer_record_invalid",
    "ai_reviewer_record_incomplete",
}


def _publication_eval_record_contract_shape() -> dict[str, Any]:
    return {
        "runtime_context_refs_required_exact_keys": sorted(_REQUIRED_RUNTIME_CONTEXT_REF_KEYS),
        "delivery_context_refs_required_exact_keys": sorted(_REQUIRED_DELIVERY_CONTEXT_REF_KEYS),
        "gap_type_allowed_values": sorted(_ALLOWED_GAP_TYPES),
        "gap_severity_allowed_values": sorted(_ALLOWED_GAP_SEVERITIES),
        "gap_gate_kind_allowed_values": sorted(_ALLOWED_GAP_GATE_KINDS),
        "unexpected_ref_keys_forbidden": True,
        "unexpected_record_fields_forbidden": True,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_existing_record_payload_target(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI reviewer record payload target is not valid JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"AI reviewer record payload target must be a JSON object: {path}")
    payload = dict(payload)
    if _text(payload.get("surface")) != "ai_reviewer_record_payload_authoring_target":
        return {}
    return payload


def _record_production_payload_path(*, profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id / RECORD_PRODUCTION_PAYLOAD_REF


def _profile_ref(profile: WorkspaceProfile) -> str | None:
    ref = getattr(profile, "profile_ref", None)
    return str(Path(ref).expanduser().resolve()) if ref is not None else None


def _owner_callable_request(*, profile: WorkspaceProfile, study_id: str, payload_ref: str) -> dict[str, Any]:
    return {
        "profile_ref": _profile_ref(profile),
        "study_id": study_id,
        "record_payload_ref": payload_ref,
        "source": "ai_reviewer_record_production_handoff",
        "build_production_trace": True,
    }


def _current_medical_prose_review_ref(
    *,
    request: Mapping[str, Any],
    study_root: Path,
) -> str | None:
    lifecycle = _mapping(request.get("request_lifecycle"))
    for item in lifecycle.get("required_currentness_refs") or []:
        currentness_ref = _text(item)
        if currentness_ref is None or Path(currentness_ref).name != "medical_prose_review.json":
            continue
        currentness_path = Path(currentness_ref).expanduser()
        if currentness_path.exists():
            return str(currentness_path.resolve())
    declared_ref = _text(
        _mapping(
            _mapping(_mapping(request.get("input_contract")).get("required_refs")).get("medical_prose_review")
        ).get("path")
    )
    if declared_ref:
        declared_path = Path(declared_ref).expanduser()
        if declared_path.exists():
            return str(declared_path.resolve())
    stable_prose_review = stable_medical_prose_review_path(study_root=study_root)
    if stable_prose_review.exists():
        return str(stable_prose_review)
    return None


def _production_request_with_owner_callable_payload_ref(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    request: Mapping[str, Any],
    production_request: Mapping[str, Any],
) -> dict[str, Any]:
    payload_ref = str(_record_production_payload_path(profile=profile, study_id=study_id).resolve())
    result = dict(production_request)
    request_lifecycle = _mapping(request.get("request_lifecycle"))
    current_stale_record_ref = _text(request_lifecycle.get("stale_record_ref")) or _text(
        request.get("publication_eval_record_ref")
    )
    if current_stale_record_ref is not None:
        result["stale_record_ref"] = current_stale_record_ref
    currentness_refs = [
        text
        for item in request_lifecycle.get("required_currentness_refs") or []
        if (text := _text(item)) is not None
    ]
    if currentness_refs:
        result["required_currentness_refs"] = currentness_refs
    current_prose_review = _current_medical_prose_review_ref(
        request=request,
        study_root=profile.studies_root / study_id,
    )
    if current_prose_review:
        result["required_input_refs"] = {
            **_mapping(result.get("required_input_refs")),
            "medical_prose_review": current_prose_review,
        }
    result["owner_callable_payload_ref"] = payload_ref
    result["owner_callable_payload_role"] = "ai_reviewer_record_payload_authoring_target"
    result["owner_callable_profile_ref"] = _profile_ref(profile)
    result["owner_callable_target"] = AI_REVIEWER_RECORD_OWNER_TARGET
    result["owner_callable_request"] = _owner_callable_request(
        profile=profile,
        study_id=study_id,
        payload_ref=payload_ref,
    )
    result["owner_callable_payload_contract"] = {
        "surface": "ai_reviewer_record_payload_authoring_target",
        "record_payload_field": "record_payload",
        "record_payload_required_before_owner_callable": True,
        "record_payload_must_be_publication_eval_record": True,
        "record_payload_must_be_authored_by_ai_reviewer": True,
        "payload_target_guard_metadata_fields": list(RECORD_PAYLOAD_TARGET_GUARD_METADATA_FIELDS),
        "payload_target_owner_editable_fields": list(RECORD_PAYLOAD_TARGET_OWNER_EDITABLE_FIELDS),
        "payload_target_guard_metadata_must_match_current_request": True,
        "record_payload_must_consume_refs": list(result.get("required_currentness_refs") or []),
        "record_payload_ref_is_materialized_by_mas": True,
        "record_payload_body_is_not_prefilled_by_mas": True,
        "publication_eval_record_contract_shape": _publication_eval_record_contract_shape(),
    }
    return result


def _record_payload_authoring_target(
    *,
    handoff: Mapping[str, Any],
    production_request: Mapping[str, Any],
    existing_target: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    existing_payload = _mapping(existing_target).get("record_payload")
    if existing_payload:
        try:
            existing_payload = canonicalize_ai_reviewer_publication_eval_record(existing_payload).to_dict()
        except (TypeError, ValueError):
            existing_payload = None
    return {
        "surface": "ai_reviewer_record_payload_authoring_target",
        "schema_version": 1,
        "study_id": _text(handoff.get("study_id")),
        "quest_id": _text(handoff.get("quest_id")),
        "action_type": ACTION_TYPE,
        "request_kind": _text(production_request.get("request_kind")),
        "request_owner": "ai_reviewer",
        "stale_record_ref": _text(production_request.get("stale_record_ref")),
        "required_currentness_refs": list(production_request.get("required_currentness_refs") or []),
        "required_input_refs": dict(_mapping(production_request.get("required_input_refs"))),
        "guard_consumed_metadata_fields": list(RECORD_PAYLOAD_TARGET_GUARD_METADATA_FIELDS),
        "owner_editable_fields": list(RECORD_PAYLOAD_TARGET_OWNER_EDITABLE_FIELDS),
        "record_payload": existing_payload,
        "record_payload_contract": dict(_mapping(production_request.get("owner_callable_payload_contract"))),
        "owner_callable_surface": _text(production_request.get("owner_callable_surface")),
        "owner_callable_target": _text(production_request.get("owner_callable_target")),
        "owner_callable_request": dict(_mapping(production_request.get("owner_callable_request"))),
        "owner_callable_runtime": _text(production_request.get("owner_callable_runtime")),
        "owner_callable_profile_ref": _text(production_request.get("owner_callable_profile_ref")),
        "owner_callable_payload_ref": _text(production_request.get("owner_callable_payload_ref")),
        "required_output_surface": RECORD_OUTPUT_SURFACE,
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "authority_contract": dict(_mapping(production_request.get("authority_contract"))),
        "reviewer_operating_system_contract": dict(
            _mapping(production_request.get("reviewer_operating_system_contract"))
        ),
        "publication_eval_record_contract": dict(
            _mapping(production_request.get("publication_eval_record_contract"))
        ),
        "generated_at": _utc_now(),
    }


def build_ai_reviewer_record_production_request(
    *,
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    stale_record_ref: str | None,
    required_currentness_refs: list[str],
    request_kind: str = "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
) -> dict[str, Any]:
    study_id = _text(request.get("study_id"))
    quest_id = _text(request.get("quest_id")) or study_id
    required_inputs = {surface: ref for surface, ref in required_refs.items() if ref is not None}
    return {
        "surface": "ai_reviewer_record_production_request",
        "schema_version": 1,
        "request_kind": request_kind,
        "request_owner": "ai_reviewer",
        "study_id": study_id,
        "quest_id": quest_id,
        "stale_record_ref": stale_record_ref,
        "required_currentness_refs": required_currentness_refs,
        "required_input_refs": required_inputs,
        "required_output_surface": RECORD_OUTPUT_SURFACE,
        "owner_callable_surface": "publication materialize-ai-reviewer-record",
        "owner_callable_target": AI_REVIEWER_RECORD_OWNER_TARGET,
        "owner_callable_request_contract": {
            "profile_ref": "required_profile_locator",
            "study_id": "required_study_locator",
            "record_payload_ref": "required_ai_reviewer_authored_payload_ref",
            "source": "ai_reviewer_record_production_handoff",
            "build_production_trace": True,
        },
        "owner_callable_runtime": "repo_local_python_module",
        "owner_callable_profile_required": True,
        "reviewer_operating_system_contract": {
            "contract_id": "medical_publication_ai_reviewer_os_v1",
            "production_trace_builder": "ai_reviewer_publication_eval_workflow.build_ai_reviewer_publication_eval_record_with_workflow_trace",
            "executor_must_not_hand_author_diagnostic_trace": True,
            "diagnostic_trace_fields_forbidden": [
                "authority_contract",
                "claim_boundary_review",
                "request_kind",
            ],
        },
        "publication_eval_record_contract": {
            **_publication_eval_record_contract_shape(),
            "future_facing_limitations_plan_required_fields": list(
                FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS
            ),
            "future_facing_limitations_plan_item_only_shape_forbidden": True,
            "record_payload_must_validate_before_owner_callable": True,
        },
        "record_must_consume_refs": required_currentness_refs,
        "followup_actions": [
            "refresh owner_callable_payload_ref guard metadata from the current production request",
            "fill owner_callable_payload_ref.record_payload with an AI-reviewer-authored publication eval record",
            "invoke owner_callable_target with owner_callable_request through the OPL owner-callable adapter",
            "record owner callable result refs for OPL DomainProgressTransitionRuntime intake",
            "wait for OPL current_owner_delta or DomainProgressTransitionRuntime live readback",
        ],
        "authority_contract": {
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
            "record_only_surface": True,
        },
        "forbidden_surfaces": [
            "paper/**",
            "manuscript/**",
            "paper/submission_minimal/**",
            "manuscript/current_package/**",
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
            ".ds/**",
        ],
}


def build_ai_reviewer_record_worker_handoff(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    request: Mapping[str, Any],
    dispatch: Mapping[str, Any] | None,
    production_request: Mapping[str, Any],
) -> dict[str, Any]:
    from med_autoscience.controllers.paper_progress_policy_adapter import build_transition_request

    quest_id = _text(request.get("quest_id")) or study_id
    enriched_production_request = _production_request_with_owner_callable_payload_ref(
        profile=profile,
        study_id=study_id,
        request=request,
        production_request=production_request,
    )
    production_request = enriched_production_request
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(_mapping(dispatch).get("owner_route"))
        or _mapping(_mapping(_mapping(dispatch).get("prompt_contract")).get("owner_route"))
    )
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / f"{ACTION_TYPE}.json"
    )
    closeout_contract = owner_callable_typed_closeout_contract(action_type=ACTION_TYPE)
    work_unit_fingerprint = _text(owner_route.get("work_unit_fingerprint")) if owner_route else None
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = owner_route_attempt_policy.currentness_basis(owner_route)
    work_unit_id = (
        _text(source_refs.get("work_unit_id"))
        or _text(production_request.get("request_kind"))
        or _text(owner_route.get("owner_reason"))
    )
    source_generation = work_unit_fingerprint or _text(owner_route.get("idempotency_key"))
    transition_request = build_transition_request(
        study_id=study_id,
        quest_id=quest_id,
        action_type=ACTION_TYPE,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        next_owner="ai_reviewer",
        source_generation=source_generation,
        expected_version=source_generation,
        dispatch_authority=DISPATCH_AUTHORITY,
        required_output_surface=RECORD_OUTPUT_SURFACE,
        currentness_basis=currentness_basis,
        idempotency_context={
            "kind": "ai-reviewer-record-transition-request",
            "request_kind": _text(production_request.get("request_kind")),
        },
    )
    transition_authority_fields = domain_progress_transition_request_transport_fields()
    owner_route_currentness_basis = currentness_basis
    prompt_contract = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": ACTION_TYPE,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": RECORD_OUTPUT_SURFACE,
        "owner_route": owner_route or None,
        "idempotency_key": _text(owner_route.get("idempotency_key")) if owner_route else None,
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{ACTION_TYPE}.json",
        "request_packet_ref": REQUEST_PACKET_REF,
        "owner_route_currentness_basis": owner_route_currentness_basis or None,
        "owner_callable_payload_ref": _text(production_request.get("owner_callable_payload_ref")),
        "owner_callable_target": _text(production_request.get("owner_callable_target")),
        "owner_callable_request": dict(_mapping(production_request.get("owner_callable_request"))),
        "owner_callable_runtime": _text(production_request.get("owner_callable_runtime")),
        "owner_callable_profile_ref": _text(production_request.get("owner_callable_profile_ref")),
        "record_payload_authoring_target_surface": RECORD_PAYLOAD_AUTHORING_SURFACE,
        "record_payload_target_guard_metadata_fields": list(RECORD_PAYLOAD_TARGET_GUARD_METADATA_FIELDS),
        "record_payload_target_owner_editable_fields": list(RECORD_PAYLOAD_TARGET_OWNER_EDITABLE_FIELDS),
        "execution_steps": [
            "Read owner_callable_payload_ref, refresh its guard-consumed metadata fields from ai_reviewer_record_production_request, and fill record_payload with the AI reviewer publication eval record.",
            "Invoke owner_callable_target with owner_callable_request through the OPL owner-callable adapter so MAS can rebuild the production reviewer_operating_system trace and write the record-only archive.",
            "Do not invent a CLI spelling or write artifacts/publication_eval/latest.json.",
            "Emit the required typed closeout packet with the materialized record ref.",
        ],
        "ai_reviewer_record_production_request": {
            **dict(production_request),
            "owner_callable_runtime": _text(production_request.get("owner_callable_runtime")),
        },
        "required_closeout_packet": closeout_contract,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "opl_domain_progress_transition_request": transition_request,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        **transition_authority_fields,
    }
    return {
        "surface": "mas_domain_progress_transition_request_projection",
        "schema_version": 1,
        **owner_callable_policy(),
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": ACTION_TYPE,
        "action_id": f"ai-reviewer-record-production::{study_id}::{_text(production_request.get('request_kind')) or 'record'}",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": RECORD_OUTPUT_SURFACE,
        "dispatch_status": "ready",
        "dispatch_authority": DISPATCH_AUTHORITY,
        "owner_route": owner_route or None,
        "idempotency_key": _text(owner_route.get("idempotency_key")) if owner_route else None,
        "action_fingerprint": work_unit_fingerprint,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": closeout_contract,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "prompt_contract": prompt_contract,
        "executor_prompt": _executor_prompt(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "opl_domain_progress_transition_request": transition_request,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        **transition_authority_fields,
        "ai_reviewer_record_production_request": dict(production_request),
        "source_action": {
            "surface": "ai_reviewer_record_production_request",
            "request_kind": _text(production_request.get("request_kind")),
            "stale_record_ref": _text(production_request.get("stale_record_ref")),
            "required_currentness_refs": list(production_request.get("required_currentness_refs") or []),
            "record_only_surface": True,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
            "record_payload_target_guard_metadata_fields": list(RECORD_PAYLOAD_TARGET_GUARD_METADATA_FIELDS),
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "request_path": str(profile.studies_root / study_id / REQUEST_PACKET_REF),
            "owner_callable_payload_ref": _text(production_request.get("owner_callable_payload_ref")),
            "owner_callable_profile_ref": _text(production_request.get("owner_callable_profile_ref")),
        },
        "handoff_semantics": {
            "status": "ai_reviewer_record_production_handoff_ready",
            "terminal_blocker": False,
            "expected_next_effect": "ai_reviewer emits a current record-only publication-eval response",
        },
        "generated_at": _utc_now(),
    }


def _executor_prompt() -> str:
    closeout_contract = owner_callable_typed_closeout_contract(action_type=ACTION_TYPE)
    return (
        "Use Codex CLI as the default MAS repair executor. "
        "Handle action `return_to_ai_reviewer_workflow` as owner `ai_reviewer`. "
        "Read the referenced MAS durable truth surfaces, fill only the AI reviewer record payload target, "
        "and run the rendered owner callable command. Do not write artifacts/publication_eval/latest.json, "
        "controller decisions, paper/current_package, manuscript/current_package, publication gates, "
        "or medical conclusions outside the owner workflow. "
        f"{closeout_contract['terminal_output_instruction']}"
    )


def materialize_ai_reviewer_record_worker_handoff(
    *,
    handoff: Mapping[str, Any],
) -> str:
    dispatch_path_text = _text(_mapping(handoff.get("refs")).get("dispatch_path"))
    if dispatch_path_text is None:
        raise ValueError("ai_reviewer_record_worker_handoff_dispatch_path_missing")
    production_request = _mapping(handoff.get("ai_reviewer_record_production_request"))
    payload_ref = _text(production_request.get("owner_callable_payload_ref")) or _text(
        _mapping(handoff.get("refs")).get("owner_callable_payload_ref")
    )
    if payload_ref is None:
        raise ValueError("ai_reviewer_record_worker_handoff_payload_ref_missing")
    payload_path = Path(payload_ref).expanduser()
    existing_target = _read_existing_record_payload_target(payload_path)
    _write_json(
        payload_path,
        _record_payload_authoring_target(
            handoff=handoff,
            production_request=production_request,
            existing_target=existing_target,
        ),
    )
    dispatch_path = Path(dispatch_path_text).expanduser()
    _write_json(dispatch_path, handoff)
    return str(dispatch_path)


def record_production_handoff_execution(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    request: Mapping[str, Any],
    dispatch: Mapping[str, Any] | None,
    record_blocker: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any] | None:
    if _text(record_blocker.get("reason")) not in RECORD_PRODUCTION_HANDOFF_REASONS:
        return None
    payload = _mapping(record_blocker.get("payload"))
    production_request = _mapping(payload.get("ai_reviewer_record_production_request"))
    if not production_request:
        return None
    handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request,
        dispatch=dispatch,
        production_request=production_request,
    )
    result = {
        "execution_status": "handoff_ready" if apply else "dry_run",
        "blocked_reason": None,
        "source_record_blocker_reason": _text(record_blocker.get("reason")),
        "owner_callable_surface": "publication materialize-ai-reviewer-record",
        "next_owner": "ai_reviewer",
        **payload,
        "ai_reviewer_record_production_request": dict(
            _mapping(handoff.get("ai_reviewer_record_production_request"))
        ),
        "ai_reviewer_record_worker_handoff": handoff,
    }
    return result


def attach_invalid_ai_reviewer_record_handoff(
    *,
    record_blocker: dict[str, Any],
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    record: Mapping[str, Any],
) -> None:
    if _text(record_blocker.get("reason")) != "ai_reviewer_record_invalid":
        return
    payload = _mapping(record_blocker.get("payload"))
    required_currentness_refs, request_kind = _record_production_currentness(
        record=record,
        required_refs=required_refs,
    )
    payload["stale_record_ref"] = _text(request.get("publication_eval_record_ref")) or _text(record.get("eval_id"))
    payload["required_currentness_refs"] = required_currentness_refs
    payload["ai_reviewer_record_production_request"] = build_ai_reviewer_record_production_request(
        request=request,
        required_refs=required_refs,
        stale_record_ref=payload["stale_record_ref"],
        required_currentness_refs=required_currentness_refs,
        request_kind=request_kind,
    )
    payload["next_required_actions"] = [
        request_kind,
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]
    record_blocker["payload"] = payload


def attach_incomplete_ai_reviewer_record_handoff(
    *,
    record_blocker: dict[str, Any],
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    record: Mapping[str, Any],
) -> None:
    if _text(record_blocker.get("reason")) != "ai_reviewer_record_incomplete":
        return
    payload = _mapping(record_blocker.get("payload"))
    missing_fields = [field for field in payload.get("missing_record_fields") or [] if _text(field)]
    if missing_fields != ["reviewer_operating_system"]:
        return
    required_currentness_refs, request_kind = _record_production_currentness(
        record=record,
        required_refs=required_refs,
    )
    payload["stale_record_ref"] = _text(request.get("publication_eval_record_ref")) or _text(record.get("eval_id"))
    payload["required_currentness_refs"] = required_currentness_refs
    payload["ai_reviewer_record_production_request"] = build_ai_reviewer_record_production_request(
        request=request,
        required_refs=required_refs,
        stale_record_ref=payload["stale_record_ref"],
        required_currentness_refs=required_currentness_refs,
        request_kind=request_kind,
    )
    payload["next_required_actions"] = [
        request_kind,
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]
    record_blocker["payload"] = payload


def _record_production_currentness(
    *,
    record: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
) -> tuple[list[str], str]:
    checks = _mapping(_mapping(record.get("reviewer_operating_system")).get("currentness_checks"))
    refs: list[str] = []
    for key in ("analysis_harmonization_latest", "unit_harmonized_external_validation_rerun"):
        if ref := _text(_mapping(checks.get(key)).get("ref")):
            refs.append(ref)
    if refs:
        return list(dict.fromkeys(refs)), (
            "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
        )
    manuscript_ref = _text(_mapping(checks.get("current_manuscript")).get("manuscript_ref")) or required_refs.get(
        "manuscript"
    )
    return [manuscript_ref] if manuscript_ref else [], (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )


__all__ = [
    "attach_incomplete_ai_reviewer_record_handoff",
    "attach_invalid_ai_reviewer_record_handoff",
    "build_ai_reviewer_record_production_request",
    "build_ai_reviewer_record_worker_handoff",
    "materialize_ai_reviewer_record_worker_handoff",
    "record_production_handoff_execution",
]
