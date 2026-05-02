from __future__ import annotations

from typing import Any


AI_REVIEWER_OS_INPUT_SURFACES = (
    "manuscript",
    "study_charter",
    "evidence_ledger",
    "review_ledger",
    "medical_manuscript_blueprint",
    "claim_evidence_map",
    "medical_prose_review",
    "publication_gate_projection",
)
AI_REVIEWER_OS_DECISION_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)


DEFAULT_PUBLICATION_CRITIQUE_POLICY: dict[str, Any] = {
    "policy_id": "medical_publication_critique_v1",
    "persona": {
        "role": "medical publication reviewer",
        "style": "diagnostic, evidence-first, manuscript-safe",
    },
    "weighted_dimensions": [
        {
            "field": "clinical_significance",
            "weight": 25,
            "focus": "judge whether the manuscript states a clinician-facing question and conclusion honestly",
        },
        {
            "field": "evidence_strength",
            "weight": 30,
            "focus": "judge whether claim-to-evidence support is strong enough for paper-facing statements",
        },
        {
            "field": "novelty_positioning",
            "weight": 20,
            "focus": "judge whether contribution boundaries and explanation targets are explicit and defensible",
        },
        {
            "field": "medical_journal_prose_quality",
            "weight": 15,
            "focus": "judge whether the draft reads as medical journal prose with clinical framing, restrained claims, and reader-facing result interpretation",
        },
        {
            "field": "human_review_readiness",
            "weight": 10,
            "focus": "judge whether the human-facing package is stable enough to release for review",
        },
    ],
    "hard_rules": [
        "clearly separate scientific weakness from delivery-only refresh debt",
        "never release a human review package while publication gate remains blocked",
        "only claim what the current manuscript-safe evidence surface can support",
    ],
    "ai_reviewer_operating_system": {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "owner": "ai_reviewer",
        "mechanical_projection_can_authorize_quality": False,
        "required_input_surfaces": list(AI_REVIEWER_OS_INPUT_SURFACES),
        "rubric_dimensions": list(AI_REVIEWER_OS_DECISION_DIMENSIONS),
        "required_trace_fields": [
            "input_bundle",
            "rubric_scores",
            "decision_matrix",
            "provenance_checks",
            "route_back_decision",
        ],
        "required_provenance": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "fail_closed_when_missing": "return_to_ai_reviewer",
        "mechanical_evidence_role": "context_and_blocker_snippets_only",
    },
    "required_outputs": [
        {"field": "overall_diagnosis", "description": "global diagnosis of the current publication-quality state"},
        {"field": "top_priority_issue", "description": "the single issue that should be repaired first"},
        {"field": "style_diagnosis", "description": "diagnosis of whether the manuscript voice reads as a medical journal article rather than a work report"},
        {"field": "revision_items", "description": "ordered revision items with explicit done criteria"},
        {"field": "next_review_focus", "description": "what the next re-review pass must verify"},
    ],
    "executable_revision_action_types": [
        "tighten_clinical_framing",
        "close_evidence_gap",
        "tighten_novelty_framing",
        "refresh_review_surface",
        "stabilize_submission_bundle",
    ],
}


def build_ai_reviewer_operating_system_contract(policy: dict[str, Any]) -> dict[str, Any]:
    contract = policy.get("ai_reviewer_operating_system")
    if not isinstance(contract, dict):
        raise ValueError("publication critique policy 缺少 ai_reviewer_operating_system 合同。")
    required_input_surfaces = contract.get("required_input_surfaces")
    if not isinstance(required_input_surfaces, list):
        raise ValueError("AI reviewer operating system required_input_surfaces 必须是列表。")
    normalized_inputs = tuple(_require_non_empty_text(item, "required_input_surfaces") for item in required_input_surfaces)
    missing_inputs = sorted(set(AI_REVIEWER_OS_INPUT_SURFACES) - set(normalized_inputs))
    if missing_inputs:
        raise ValueError("AI reviewer operating system 缺少输入面: " + ", ".join(missing_inputs))

    rubric_dimensions = contract.get("rubric_dimensions")
    if not isinstance(rubric_dimensions, list):
        raise ValueError("AI reviewer operating system rubric_dimensions 必须是列表。")
    normalized_dimensions = tuple(_require_non_empty_text(item, "rubric_dimensions") for item in rubric_dimensions)
    missing_dimensions = sorted(set(AI_REVIEWER_OS_DECISION_DIMENSIONS) - set(normalized_dimensions))
    if missing_dimensions:
        raise ValueError("AI reviewer operating system 缺少 rubric 维度: " + ", ".join(missing_dimensions))

    trace_fields = contract.get("required_trace_fields")
    if not isinstance(trace_fields, list):
        raise ValueError("AI reviewer operating system required_trace_fields 必须是列表。")
    normalized_trace_fields = tuple(_require_non_empty_text(item, "required_trace_fields") for item in trace_fields)
    for required_field in (
        "input_bundle",
        "rubric_scores",
        "decision_matrix",
        "provenance_checks",
        "route_back_decision",
    ):
        if required_field not in normalized_trace_fields:
            raise ValueError(f"AI reviewer operating system 缺少 trace 字段: {required_field}")

    provenance = contract.get("required_provenance")
    if not isinstance(provenance, dict):
        raise ValueError("AI reviewer operating system required_provenance 必须是 object。")
    if provenance.get("assessment_owner") != "ai_reviewer":
        raise ValueError("AI reviewer operating system assessment_owner 必须是 ai_reviewer。")
    if provenance.get("policy_id") != policy.get("policy_id"):
        raise ValueError("AI reviewer operating system policy_id 必须与 critique policy 对齐。")
    if provenance.get("ai_reviewer_required") is not False:
        raise ValueError("AI reviewer operating system ai_reviewer_required 必须是 false。")
    if contract.get("mechanical_projection_can_authorize_quality") is not False:
        raise ValueError("AI reviewer operating system 必须禁止 mechanical projection 授权质量。")

    return {
        **contract,
        "required_input_surfaces": list(normalized_inputs),
        "rubric_dimensions": list(normalized_dimensions),
        "required_trace_fields": list(normalized_trace_fields),
        "required_provenance": dict(provenance),
    }


def _require_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"AI reviewer operating system {field_name} 必须都是非空字符串。")
    return value.strip()


def build_weight_contract(policy: dict[str, Any]) -> dict[str, int]:
    weighted_dimensions = policy.get("weighted_dimensions")
    if not isinstance(weighted_dimensions, list):
        raise ValueError("publication critique policy 缺少 weighted_dimensions 列表。")
    contract: dict[str, int] = {}
    for item in weighted_dimensions:
        if not isinstance(item, dict):
            raise ValueError("publication critique policy weighted_dimensions 必须是 object 列表。")
        field = item.get("field")
        weight = item.get("weight")
        if not isinstance(field, str) or not field.strip():
            raise ValueError("publication critique policy weighted_dimensions.field 必须是非空字符串。")
        if not isinstance(weight, int):
            raise ValueError("publication critique policy weighted_dimensions.weight 必须是整数。")
        contract[field] = weight
    return contract


def build_revision_action_contract(policy: dict[str, Any]) -> tuple[str, ...]:
    action_types = policy.get("executable_revision_action_types")
    if not isinstance(action_types, list):
        raise ValueError("publication critique policy 缺少 executable_revision_action_types 列表。")
    normalized: list[str] = []
    for item in action_types:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("publication critique policy executable_revision_action_types 必须都是非空字符串。")
        normalized.append(item.strip())
    return tuple(normalized)
