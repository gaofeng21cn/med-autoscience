from __future__ import annotations

from typing import Any

METHODS_COMPLETENESS_ITEMS = (
    "study_design",
    "cohort",
    "variables",
    "model",
    "validation",
    "statistical_analysis",
)
STATISTICAL_REPORTING_ITEMS = ("summary_format", "p_values", "subgroup_tests")
CLINICAL_ACTIONABILITY_ITEMS = ("treatment_gap", "follow_up_or_outcome_relevance")
TREATMENT_GAP_REPORTING_ITEMS = (
    "explicit_numerator_denominator_rules",
    "overall_burden_and_group_rates",
    "table_role_consistency",
    "figure_legend_uniqueness",
    "non_causal_claim_guardrail",
)
PHENOTYPE_ARCHETYPE_TOKENS = ("phenotype", "subtype", "cluster", "real_world")

REPORTING_CHECKLIST_BLOCKER_KEYS = frozenset(
    {
        "methods_completeness_incomplete",
        "statistical_reporting_incomplete",
        "table_figure_claim_map_missing_or_incomplete",
        "clinical_actionability_incomplete",
        "treatment_gap_reporting_incomplete",
    }
)


def _truthy_mapping_item(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if isinstance(value, dict):
        status = str(value.get("status") or "").strip().lower()
        return status in {"complete", "clear", "present", "closed"} or value.get("present") is True
    if isinstance(value, str):
        return value.strip().lower() in {"complete", "clear", "present", "closed", "yes", "true"}
    return value is True


def _section_status(payload: object, required_items: tuple[str, ...]) -> dict[str, Any]:
    section = payload if isinstance(payload, dict) else {}
    missing_items = [item for item in required_items if not _truthy_mapping_item(section, item)]
    return {
        "status": "blocked" if missing_items else "clear",
        "required_items": list(required_items),
        "missing_items": missing_items,
    }


def _claim_map_status(payload: object) -> dict[str, Any]:
    items = payload if isinstance(payload, list) else []
    complete_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim") or item.get("claim_id") or "").strip()
        displays = item.get("displays") or item.get("tables_figures") or item.get("table_figure_refs")
        if claim and isinstance(displays, list) and displays:
            complete_items.append(item)
    return {
        "status": "clear" if complete_items else "blocked",
        "mapped_claim_count": len(complete_items),
        "missing_items": [] if complete_items else ["claim_to_table_or_figure_links"],
    }


def _phenotype_actionability_required(contract: dict[str, Any]) -> bool:
    explicit = contract.get("clinical_actionability_required")
    if explicit is not None:
        return explicit is True
    surfaces = (
        contract.get("paper_archetype"),
        contract.get("study_archetype"),
        contract.get("manuscript_family"),
        contract.get("endpoint_type"),
    )
    text = " ".join(str(item or "").strip().lower() for item in surfaces)
    return any(token in text for token in PHENOTYPE_ARCHETYPE_TOKENS)


def _structured_contract_source(contract: dict[str, Any]) -> dict[str, Any]:
    nested = contract.get("structured_reporting_contract")
    if isinstance(nested, dict):
        merged = dict(contract)
        merged.update(nested)
        return merged
    return contract


def build_structured_reporting_checklist(contract: dict[str, Any]) -> dict[str, Any]:
    contract = _structured_contract_source(contract)
    actionability_required = _phenotype_actionability_required(contract)
    explicit_structured_contract = any(
        key in contract
        for key in (
            "methods_completeness",
            "statistical_reporting",
            "table_figure_claim_map",
            "clinical_actionability",
            "treatment_gap_reporting",
        )
    )
    if not actionability_required and not explicit_structured_contract:
        return {
            "status": "not_required",
            "blockers": [],
            "methods_completeness": {
                "status": "not_required",
                "required_items": list(METHODS_COMPLETENESS_ITEMS),
                "missing_items": [],
            },
            "statistical_reporting": {
                "status": "not_required",
                "required_items": list(STATISTICAL_REPORTING_ITEMS),
                "missing_items": [],
            },
            "table_figure_claim_map": {
                "status": "not_required",
                "mapped_claim_count": 0,
                "missing_items": [],
            },
            "clinical_actionability": {
                "status": "not_required",
                "required_items": list(CLINICAL_ACTIONABILITY_ITEMS),
                "missing_items": [],
            },
            "treatment_gap_reporting": {
                "status": "not_required",
                "required_items": list(TREATMENT_GAP_REPORTING_ITEMS),
                "missing_items": [],
            },
        }
    methods = _section_status(contract.get("methods_completeness"), METHODS_COMPLETENESS_ITEMS)
    statistics = _section_status(contract.get("statistical_reporting"), STATISTICAL_REPORTING_ITEMS)
    claim_map = _claim_map_status(contract.get("table_figure_claim_map"))
    actionability = (
        _section_status(contract.get("clinical_actionability"), CLINICAL_ACTIONABILITY_ITEMS)
        if actionability_required
        else {
            "status": "not_required",
            "required_items": list(CLINICAL_ACTIONABILITY_ITEMS),
            "missing_items": [],
        }
    )
    treatment_gap_reporting = (
        _section_status(contract.get("treatment_gap_reporting"), TREATMENT_GAP_REPORTING_ITEMS)
        if actionability_required
        else {
            "status": "not_required",
            "required_items": list(TREATMENT_GAP_REPORTING_ITEMS),
            "missing_items": [],
        }
    )
    blockers: list[str] = []
    if methods["status"] == "blocked":
        blockers.append("methods_completeness_incomplete")
    if statistics["status"] == "blocked":
        blockers.append("statistical_reporting_incomplete")
    if claim_map["status"] == "blocked":
        blockers.append("table_figure_claim_map_missing_or_incomplete")
    if actionability["status"] == "blocked":
        blockers.append("clinical_actionability_incomplete")
    if treatment_gap_reporting["status"] == "blocked":
        blockers.append("treatment_gap_reporting_incomplete")
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "methods_completeness": methods,
        "statistical_reporting": statistics,
        "table_figure_claim_map": claim_map,
        "clinical_actionability": actionability,
        "treatment_gap_reporting": treatment_gap_reporting,
    }


def normalize_structured_reporting_checklist(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("structured_reporting_checklist"), dict):
        return dict(payload["structured_reporting_checklist"])
    return None
