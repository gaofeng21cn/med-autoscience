from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


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
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
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
]
