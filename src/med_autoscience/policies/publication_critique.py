from __future__ import annotations

import json
from pathlib import Path
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
TARGET_JOURNAL_WRITING_LAYER_REQUIRED_FIELDS = (
    "target_journal_family",
    "near_neighbor_style_corpus",
    "section_plan",
    "claim_to_paragraph_map",
    "display_to_claim_map",
    "restrained_language_strategy",
)
FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS = (
    "limitation",
    "impact_on_claim",
    "required_future_analysis_data_or_design",
    "current_manuscript_wording_must_be_restrained",
)
AI_NATIVE_EXPERT_JUDGMENT_REQUIRED_FIELDS = (
    "role",
    "contracts_are_floor_not_ceiling",
    "may_raise_unlisted_quality_concerns",
    "must_compare_against_high_quality_medical_journal_expectations",
    "mechanical_checks_can_only_block_or_route",
)
TARGET_JOURNAL_WRITING_LAYER_RELATIVE_PATH = Path("paper/target_journal_writing_layer.json")


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
        "for prediction-model external validation, route back when HDL/unit harmonization, model reproducibility, visible Table 1/Table 2, uncertainty intervals, calibration/risk-distribution displays, or NHANES weighting/framing are missing from durable evidence",
        "treat accepted-analysis-record, verified-output, source-documentation-gap, and submission-readiness wording in article body as internal quality-record leakage, not medical journal prose",
        "do not let corrected data-processing mistakes, raw-scale contaminated runs, or debugging history become the main manuscript story; they belong in provenance or minimal methods caveats when needed",
    ],
    "ai_reviewer_operating_system": {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "owner": "ai_reviewer",
        "mechanical_projection_can_authorize_quality": False,
        "required_input_surfaces": list(AI_REVIEWER_OS_INPUT_SURFACES),
        "rubric_dimensions": list(AI_REVIEWER_OS_DECISION_DIMENSIONS),
        "target_journal_writing_layer": {
            "surface": "target_journal_writing_layer",
            "role": "ai_reviewer_quality_context",
            "mechanical_projection_can_authorize_quality": False,
            "required_fields": list(TARGET_JOURNAL_WRITING_LAYER_REQUIRED_FIELDS),
            "near_neighbor_style_corpus": {
                "role": "style_and_structure_calibration_only",
                "can_supply_claims": False,
                "can_override_evidence_ledger": False,
            },
            "restrained_language_strategy": {
                "requires_claim_evidence_alignment": True,
                "forbids_overstatement_from_style_examples": True,
            },
        },
        "required_trace_fields": [
            "input_bundle",
            "rubric_scores",
            "decision_matrix",
            "currentness_checks",
            "provenance_checks",
            "route_back_decision",
            "future_facing_limitations_plan",
        ],
        "future_facing_limitations_plan": {
            "surface": "future_facing_limitations_plan",
            "role": "prescriptive_limitations_review_contract",
            "mechanical_projection_can_authorize_quality": False,
            "required_fields": list(FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS),
            "discipline": {
                "requires_limitation_to_claim_impact_mapping": True,
                "requires_future_analysis_data_or_design": True,
                "requires_current_manuscript_restraint_decision": True,
                "forbids_weakness_disclosure_only": True,
            },
        },
        "ai_native_expert_judgment": {
            "role": "primary_quality_signal",
            "contracts_are_floor_not_ceiling": True,
            "may_raise_unlisted_quality_concerns": True,
            "must_compare_against_high_quality_medical_journal_expectations": True,
            "mechanical_checks_can_only_block_or_route": True,
        },
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
        {"field": "future_facing_limitations_plan", "description": "limitations mapped to claim impact, required future analysis/data/design, and current wording restraint"},
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
        "future_facing_limitations_plan",
        "currentness_checks",
    ):
        if required_field not in normalized_trace_fields:
            raise ValueError(f"AI reviewer operating system 缺少 trace 字段: {required_field}")
    _require_future_facing_limitations_output(policy)

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
    _require_ai_native_expert_judgment(contract)

    writing_layer = contract.get("target_journal_writing_layer")
    if not isinstance(writing_layer, dict):
        raise ValueError("AI reviewer operating system 缺少 target_journal_writing_layer。")
    if writing_layer.get("mechanical_projection_can_authorize_quality") is not False:
        raise ValueError("target_journal_writing_layer 必须禁止 mechanical projection 授权质量。")
    writing_layer_fields = writing_layer.get("required_fields")
    if not isinstance(writing_layer_fields, list):
        raise ValueError("target_journal_writing_layer required_fields 必须是列表。")
    normalized_writing_layer_fields = tuple(
        _require_non_empty_text(item, "target_journal_writing_layer.required_fields")
        for item in writing_layer_fields
    )
    missing_writing_fields = sorted(set(TARGET_JOURNAL_WRITING_LAYER_REQUIRED_FIELDS) - set(normalized_writing_layer_fields))
    if missing_writing_fields:
        raise ValueError("target_journal_writing_layer 缺少字段: " + ", ".join(missing_writing_fields))

    future_limitations_plan = contract.get("future_facing_limitations_plan")
    if not isinstance(future_limitations_plan, dict):
        raise ValueError("AI reviewer operating system 缺少 future_facing_limitations_plan。")
    if future_limitations_plan.get("mechanical_projection_can_authorize_quality") is not False:
        raise ValueError("future_facing_limitations_plan 必须禁止 mechanical projection 授权质量。")
    future_limitations_fields = future_limitations_plan.get("required_fields")
    if not isinstance(future_limitations_fields, list):
        raise ValueError("future_facing_limitations_plan required_fields 必须是列表。")
    normalized_future_limitations_fields = tuple(
        _require_non_empty_text(item, "future_facing_limitations_plan.required_fields")
        for item in future_limitations_fields
    )
    missing_future_limitations_fields = sorted(
        set(FUTURE_FACING_LIMITATIONS_PLAN_REQUIRED_FIELDS) - set(normalized_future_limitations_fields)
    )
    if missing_future_limitations_fields:
        raise ValueError("future_facing_limitations_plan 缺少字段: " + ", ".join(missing_future_limitations_fields))
    future_limitations_discipline = future_limitations_plan.get("discipline")
    if not isinstance(future_limitations_discipline, dict):
        raise ValueError("future_facing_limitations_plan discipline 必须是 object。")
    for discipline_field in (
        "requires_limitation_to_claim_impact_mapping",
        "requires_future_analysis_data_or_design",
        "requires_current_manuscript_restraint_decision",
        "forbids_weakness_disclosure_only",
    ):
        if future_limitations_discipline.get(discipline_field) is not True:
            raise ValueError(f"future_facing_limitations_plan discipline 必须启用 {discipline_field}。")

    return {
        **contract,
        "required_input_surfaces": list(normalized_inputs),
        "rubric_dimensions": list(normalized_dimensions),
        "required_trace_fields": list(normalized_trace_fields),
        "required_provenance": dict(provenance),
        "target_journal_writing_layer": {
            **writing_layer,
            "required_fields": list(normalized_writing_layer_fields),
        },
        "future_facing_limitations_plan": {
            **future_limitations_plan,
            "required_fields": list(normalized_future_limitations_fields),
            "discipline": dict(future_limitations_discipline),
        },
    }


def _require_future_facing_limitations_output(policy: dict[str, Any]) -> None:
    required_outputs = policy.get("required_outputs")
    if not isinstance(required_outputs, list):
        raise ValueError("publication critique policy required_outputs 必须是列表。")
    output_fields: list[str] = []
    for item in required_outputs:
        if not isinstance(item, dict):
            raise ValueError("publication critique policy required_outputs 必须是 object 列表。")
        output_fields.append(_require_non_empty_text(item.get("field"), "required_outputs.field"))
    if "future_facing_limitations_plan" not in output_fields:
        raise ValueError("publication critique policy 缺少 required output: future_facing_limitations_plan。")


def _require_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"AI reviewer operating system {field_name} 必须都是非空字符串。")
    return value.strip()


def stable_target_journal_writing_layer_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / TARGET_JOURNAL_WRITING_LAYER_RELATIVE_PATH).resolve()


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"target_journal_writing_layer {field_name} must be an object")
    return dict(value)


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"target_journal_writing_layer {field_name} must be a list")
    return list(value)


def _normalize_target_journal_writing_layer(payload: dict[str, Any]) -> dict[str, Any]:
    for field_name in TARGET_JOURNAL_WRITING_LAYER_REQUIRED_FIELDS:
        if field_name not in payload:
            raise ValueError(f"target_journal_writing_layer missing {field_name}")
    target_journal_family = _require_non_empty_text(
        payload.get("target_journal_family"),
        "target_journal_family",
    )
    near_neighbor_style_corpus = _require_list(
        payload.get("near_neighbor_style_corpus"),
        "near_neighbor_style_corpus",
    )
    if not near_neighbor_style_corpus:
        raise ValueError("target_journal_writing_layer near_neighbor_style_corpus must not be empty")
    for item in near_neighbor_style_corpus:
        neighbor = _require_mapping(item, "near_neighbor_style_corpus item")
        _require_non_empty_text(neighbor.get("journal"), "near_neighbor_style_corpus.journal")
        _require_non_empty_text(neighbor.get("style_ref"), "near_neighbor_style_corpus.style_ref")

    section_plan = _require_mapping(payload.get("section_plan"), "section_plan")
    for section_name in ("Introduction", "Methods", "Results", "Discussion"):
        _require_non_empty_text(section_plan.get(section_name), f"section_plan.{section_name}")

    claim_to_paragraph_map = _require_list(
        payload.get("claim_to_paragraph_map"),
        "claim_to_paragraph_map",
    )
    if not claim_to_paragraph_map:
        raise ValueError("target_journal_writing_layer claim_to_paragraph_map must not be empty")
    for item in claim_to_paragraph_map:
        claim_map = _require_mapping(item, "claim_to_paragraph_map item")
        _require_non_empty_text(claim_map.get("claim_id"), "claim_to_paragraph_map.claim_id")
        _require_non_empty_text(claim_map.get("section"), "claim_to_paragraph_map.section")
        _require_list(claim_map.get("evidence_refs"), "claim_to_paragraph_map.evidence_refs")

    display_to_claim_map = _require_list(
        payload.get("display_to_claim_map"),
        "display_to_claim_map",
    )
    if not display_to_claim_map:
        raise ValueError("target_journal_writing_layer display_to_claim_map must not be empty")
    for item in display_to_claim_map:
        display_map = _require_mapping(item, "display_to_claim_map item")
        _require_non_empty_text(display_map.get("display_id"), "display_to_claim_map.display_id")
        _require_non_empty_text(display_map.get("claim_id"), "display_to_claim_map.claim_id")

    restrained_language_strategy = _require_mapping(
        payload.get("restrained_language_strategy"),
        "restrained_language_strategy",
    )

    return {
        "surface": "target_journal_writing_layer",
        "schema_version": 1,
        "role": "ai_reviewer_quality_context",
        "target_journal_family": target_journal_family,
        "near_neighbor_style_corpus": near_neighbor_style_corpus,
        "section_plan": section_plan,
        "claim_to_paragraph_map": claim_to_paragraph_map,
        "display_to_claim_map": display_to_claim_map,
        "restrained_language_strategy": {
            **restrained_language_strategy,
            "requires_claim_evidence_alignment": True,
            "forbids_overstatement_from_style_examples": True,
        },
        "mechanical_projection_can_authorize_quality": False,
        "quality_claim_authorized": False,
    }


def materialize_target_journal_writing_layer(
    *,
    study_root: Path,
    payload: dict[str, Any],
) -> dict[str, str]:
    normalized = _normalize_target_journal_writing_layer(payload)
    path = stable_target_journal_writing_layer_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "target_journal_writing_layer",
        "artifact_path": str(path),
    }


def read_target_journal_writing_layer(*, study_root: Path) -> dict[str, Any]:
    path = stable_target_journal_writing_layer_path(study_root=study_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("target_journal_writing_layer artifact must be an object")
    return _normalize_target_journal_writing_layer(payload)


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


def _require_ai_native_expert_judgment(contract: dict[str, Any]) -> None:
    expert_judgment = contract.get("ai_native_expert_judgment")
    if not isinstance(expert_judgment, dict):
        raise ValueError("AI reviewer operating system 缺少 ai_native_expert_judgment。")
    missing_fields = [
        field
        for field in AI_NATIVE_EXPERT_JUDGMENT_REQUIRED_FIELDS
        if field not in expert_judgment
    ]
    if missing_fields:
        raise ValueError("ai_native_expert_judgment 缺少字段: " + ", ".join(missing_fields))
    if expert_judgment.get("role") != "primary_quality_signal":
        raise ValueError("ai_native_expert_judgment role 必须是 primary_quality_signal。")
    for field in AI_NATIVE_EXPERT_JUDGMENT_REQUIRED_FIELDS[1:]:
        if expert_judgment.get(field) is not True:
            raise ValueError(f"ai_native_expert_judgment {field} 必须是 true。")


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
