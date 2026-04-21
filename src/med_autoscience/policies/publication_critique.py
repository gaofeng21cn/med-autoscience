from __future__ import annotations

from typing import Any


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
            "weight": 35,
            "focus": "judge whether claim-to-evidence support is strong enough for paper-facing statements",
        },
        {
            "field": "novelty_positioning",
            "weight": 20,
            "focus": "judge whether contribution boundaries and explanation targets are explicit and defensible",
        },
        {
            "field": "human_review_readiness",
            "weight": 20,
            "focus": "judge whether the human-facing package is stable enough to release for review",
        },
    ],
    "hard_rules": [
        "clearly separate scientific weakness from delivery-only refresh debt",
        "never release a human review package while publication gate remains blocked",
        "only claim what the current manuscript-safe evidence surface can support",
    ],
    "required_outputs": [
        {"field": "overall_diagnosis", "description": "global diagnosis of the current publication-quality state"},
        {"field": "top_priority_issue", "description": "the single issue that should be repaired first"},
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
