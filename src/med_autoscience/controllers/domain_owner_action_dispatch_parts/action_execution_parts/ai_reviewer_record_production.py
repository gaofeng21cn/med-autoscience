from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
)
from med_autoscience.controllers.runtime_ai_repair_policy import default_executor_policy
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part

RECORD_OUTPUT_SURFACE = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
REQUEST_PACKET_REF = "artifacts/supervision/requests/ai_reviewer/latest.json"
ACTION_TYPE = "return_to_ai_reviewer_workflow"
DISPATCH_AUTHORITY = "ai_reviewer_record_production_handoff"
ALLOWED_WRITE_SURFACES = [RECORD_OUTPUT_SURFACE]
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
        "record_must_consume_refs": required_currentness_refs,
        "followup_actions": [
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
        "ai_reviewer_record_production_request": dict(production_request),
        "required_closeout_packet": closeout_contract,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
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
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "prompt_contract": prompt_contract,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
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
        },
        "handoff_semantics": {
            "status": "ai_reviewer_record_production_handoff_ready",
            "terminal_blocker": False,
            "expected_next_effect": "ai_reviewer emits a current record-only publication-eval response",
        },
        "generated_at": _utc_now(),
    }


def materialize_ai_reviewer_record_worker_handoff(
    *,
    handoff: Mapping[str, Any],
) -> str:
    dispatch_path_text = _text(_mapping(handoff.get("refs")).get("dispatch_path"))
    if dispatch_path_text is None:
        raise ValueError("ai_reviewer_record_worker_handoff_dispatch_path_missing")
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
    if _text(record_blocker.get("reason")) not in STALENESS_HANDOFF_REASONS:
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
        "owner_callable_surface": "publication materialize-ai-reviewer-record",
        "next_owner": "ai_reviewer",
        **payload,
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
    "attach_invalid_ai_reviewer_record_handoff",
    "build_ai_reviewer_record_production_request",
    "build_ai_reviewer_record_worker_handoff",
    "materialize_ai_reviewer_record_worker_handoff",
    "record_production_handoff_execution",
]
