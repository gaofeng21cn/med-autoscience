from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


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
        "owner_callable_surface": "publication materialize-ai-reviewer-eval-record",
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


__all__ = ["build_ai_reviewer_record_production_request"]
