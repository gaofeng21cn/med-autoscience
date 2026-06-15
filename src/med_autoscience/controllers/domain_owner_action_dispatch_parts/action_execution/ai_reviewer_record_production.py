from __future__ import annotations

import json
import shlex
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import default_executor_dispatch_packets
from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries import (
    provider_admission_authority_transport_fields,
)
from med_autoscience.controllers.runtime_ai_repair_policy import default_executor_policy
from med_autoscience.medical_prose_review import stable_medical_prose_review_path
from med_autoscience.policies.publication_critique import (
    FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol

RECORD_OUTPUT_SURFACE = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
REQUEST_PACKET_REF = "artifacts/supervision/requests/ai_reviewer/latest.json"
ACTION_TYPE = "return_to_ai_reviewer_workflow"
RECORD_PRODUCTION_PAYLOAD_REF = (
    "artifacts/supervision/requests/ai_reviewer/record_production_payloads/"
    f"{ACTION_TYPE}_payload.json"
)
RECORD_PAYLOAD_AUTHORING_SURFACE = "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json"
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


def _record_production_payload_path(*, profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id / RECORD_PRODUCTION_PAYLOAD_REF


def _profile_ref(profile: WorkspaceProfile) -> str | None:
    ref = getattr(profile, "profile_ref", None)
    return str(Path(ref).expanduser().resolve()) if ref is not None else None


def _repo_local_cli_prefix() -> str:
    repo_root = Path(__file__).resolve().parents[5]
    python_path = f"{repo_root / 'src'}:{repo_root}"
    return f"PYTHONPATH={shlex.quote(python_path)} python3 -m med_autoscience.cli"


def _command_for_payload_ref(*, profile: WorkspaceProfile, study_id: str, payload_ref: str) -> str:
    profile_ref = _profile_ref(profile)
    profile_arg = f"--profile {shlex.quote(profile_ref)} " if profile_ref is not None else "--profile <profile.toml> "
    return (
        f"{_repo_local_cli_prefix()} publication materialize-ai-reviewer-record "
        f"{profile_arg}"
        f"--study-id {shlex.quote(study_id)} "
        f"--payload-file {shlex.quote(payload_ref)} "
        "--build-production-trace"
    )


def _production_request_with_owner_callable_payload_ref(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    production_request: Mapping[str, Any],
) -> dict[str, Any]:
    payload_ref = str(_record_production_payload_path(profile=profile, study_id=study_id).resolve())
    result = dict(production_request)
    stable_prose_review = stable_medical_prose_review_path(study_root=profile.studies_root / study_id)
    if stable_prose_review.exists():
        result["required_input_refs"] = {
            **_mapping(result.get("required_input_refs")),
            "medical_prose_review": str(stable_prose_review),
        }
    result["owner_callable_payload_ref"] = payload_ref
    result["owner_callable_payload_role"] = "ai_reviewer_record_payload_authoring_target"
    result["owner_callable_profile_ref"] = _profile_ref(profile)
    result["owner_callable_command"] = _command_for_payload_ref(
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
        "record_payload_must_consume_refs": list(result.get("required_currentness_refs") or []),
        "record_payload_ref_is_materialized_by_mas": True,
        "record_payload_body_is_not_prefilled_by_mas": True,
    }
    return result


def _record_payload_authoring_target(
    *,
    handoff: Mapping[str, Any],
    production_request: Mapping[str, Any],
) -> dict[str, Any]:
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
        "record_payload": None,
        "record_payload_contract": dict(_mapping(production_request.get("owner_callable_payload_contract"))),
        "owner_callable_surface": _text(production_request.get("owner_callable_surface")),
        "owner_callable_command": _text(production_request.get("owner_callable_command")),
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


def _authorization_fields(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _mapping(dispatch)
    prompt_contract = _mapping(source.get("prompt_contract"))
    owner_route = _mapping(source.get("owner_route"))
    fields: dict[str, Any] = {}
    for key in ("opl_execution_authorization", "opl_provider_attempt", "stage_attempt"):
        if key in source:
            fields[key] = _mapping(source.get(key)) or source.get(key)
        elif key in prompt_contract:
            fields[key] = _mapping(prompt_contract.get(key)) or prompt_contract.get(key)
        elif key in owner_route:
            fields[key] = _mapping(owner_route.get(key)) or owner_route.get(key)
    return fields


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
        "owner_callable_command": (
            f"{_repo_local_cli_prefix()} publication materialize-ai-reviewer-record --profile <profile.toml> "
            "--study-id <study-id> --payload-file <ai_reviewer_record_payload.json> "
            "--build-production-trace"
        ),
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
            "future_facing_limitations_plan_required_fields": list(
                FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS
            ),
            "future_facing_limitations_plan_item_only_shape_forbidden": True,
            "record_payload_must_validate_before_owner_callable": True,
        },
        "record_must_consume_refs": required_currentness_refs,
        "followup_actions": [
            "fill owner_callable_payload_ref.record_payload with an AI-reviewer-authored publication eval record",
            "run owner_callable_command exactly as rendered",
            "domain-action-request-materialize",
            "domain-owner-action-dispatch --action-types return_to_ai_reviewer_workflow",
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
    quest_id = _text(request.get("quest_id")) or study_id
    enriched_production_request = _production_request_with_owner_callable_payload_ref(
        profile=profile,
        study_id=study_id,
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
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    )
    closeout_contract = default_executor_typed_closeout_contract(action_type=ACTION_TYPE)
    repeat_key = _text(owner_route.get("work_unit_fingerprint")) if owner_route else None
    if repeat_key is None and owner_route:
        repeat_key = _text(owner_route.get("idempotency_key"))
    provider_admission_identity = _provider_admission_identity(
        study_id=study_id,
        quest_id=quest_id,
        owner_route=owner_route,
        production_request=production_request,
        work_unit_fingerprint=repeat_key,
    )
    provider_admission_fields = provider_admission_authority_transport_fields(
        provider_admission_identity
    )
    authorization_fields = _authorization_fields(dispatch)
    owner_route_currentness_basis = _mapping(_mapping(owner_route.get("source_refs")).get("owner_route_currentness_basis"))
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
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "request_packet_ref": REQUEST_PACKET_REF,
        "owner_route_currentness_basis": owner_route_currentness_basis or None,
        "owner_callable_payload_ref": _text(production_request.get("owner_callable_payload_ref")),
        "owner_callable_command": _text(production_request.get("owner_callable_command")),
        "owner_callable_runtime": _text(production_request.get("owner_callable_runtime")),
        "owner_callable_profile_ref": _text(production_request.get("owner_callable_profile_ref")),
        "record_payload_authoring_target_surface": RECORD_PAYLOAD_AUTHORING_SURFACE,
        "execution_steps": [
            "Read owner_callable_payload_ref and fill only its record_payload field with the AI reviewer publication eval record.",
            "Run owner_callable_command exactly as rendered to let MAS rebuild the production reviewer_operating_system trace and write the record-only archive.",
            "Do not inspect MAS source code to discover alternate CLI spellings or write artifacts/publication_eval/latest.json.",
            "Emit the required typed closeout packet with the materialized record ref.",
        ],
        "ai_reviewer_record_production_request": dict(production_request),
        "required_closeout_packet": closeout_contract,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "provider_admission_identity": provider_admission_identity,
        **provider_admission_fields,
        **authorization_fields,
    }
    dispatch_shell = {
        "action_type": ACTION_TYPE,
        "next_executable_owner": "ai_reviewer",
        "owner_route": owner_route or None,
        "prompt_contract": prompt_contract,
        "required_closeout_packet": closeout_contract,
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "provider_admission_identity": provider_admission_identity,
        **provider_admission_fields,
    }
    owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(
        dispatch=dispatch_shell
    )
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        **default_executor_policy(),
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
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": repeat_key,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": closeout_contract,
        "owner_route_attempt_envelope": owner_route_attempt_envelope,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "prompt_contract": prompt_contract,
        "executor_prompt": _executor_prompt(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "provider_admission_identity": provider_admission_identity,
        **provider_admission_fields,
        **authorization_fields,
        "ai_reviewer_record_production_request": dict(production_request),
        "source_action": {
            "surface": "ai_reviewer_record_production_request",
            "request_kind": _text(production_request.get("request_kind")),
            "stale_record_ref": _text(production_request.get("stale_record_ref")),
            "required_currentness_refs": list(production_request.get("required_currentness_refs") or []),
            "record_only_surface": True,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
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


def _provider_admission_identity(
    *,
    study_id: str,
    quest_id: str | None,
    owner_route: Mapping[str, Any],
    production_request: Mapping[str, Any],
    work_unit_fingerprint: str | None,
) -> dict[str, Any]:
    source_refs = _mapping(owner_route.get("source_refs"))
    work_unit_id = (
        _text(source_refs.get("work_unit_id"))
        or _text(production_request.get("request_kind"))
        or _text(owner_route.get("owner_reason"))
    )
    return {
        "surface": "provider_admission_current_control_handoff",
        "study_id": study_id,
        "quest_id": quest_id or study_id,
        "action_type": ACTION_TYPE,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "dispatch_authority": DISPATCH_AUTHORITY,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": RECORD_OUTPUT_SURFACE,
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }


def _executor_prompt() -> str:
    closeout_contract = default_executor_typed_closeout_contract(action_type=ACTION_TYPE)
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
    _write_json(
        payload_path,
        _record_payload_authoring_target(
            handoff=handoff,
            production_request=production_request,
        ),
    )
    dispatch_path = Path(dispatch_path_text).expanduser()
    packet_handoff = default_executor_dispatch_packets.dispatch_with_immutable_packet_ref(
        dispatch=handoff,
        dispatch_path=dispatch_path,
    )
    _write_json(dispatch_path, packet_handoff)
    immutable_dispatch_path = default_executor_dispatch_packets.dispatch_stage_packet_path(
        packet_handoff,
        fallback_dispatch_path=dispatch_path,
    )
    if immutable_dispatch_path != dispatch_path:
        _write_json(immutable_dispatch_path, packet_handoff)
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
    if apply:
        result["ai_reviewer_record_worker_handoff_path"] = materialize_ai_reviewer_record_worker_handoff(
            handoff=handoff,
        )
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
