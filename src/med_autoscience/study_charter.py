from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.medical_reporting_guidelines import build_guideline_quality_gate_expectation
from med_autoscience.policies.medical_reporting_checklist import build_default_structured_reporting_contract
from med_autoscience.policies.medical_reporting_contract import SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES

__all__ = [
    "STABLE_STUDY_CHARTER_RELATIVE_PATH",
    "materialize_study_charter",
    "read_study_charter",
    "resolve_study_charter_ref",
    "stable_study_charter_path",
]


STABLE_STUDY_CHARTER_RELATIVE_PATH = Path("artifacts/controller/study_charter.json")
AUTONOMOUS_SCIENTIFIC_DECISIONS = (
    "analysis_plan_within_locked_direction",
    "evidence_generation_and_sufficiency_judgment",
    "manuscript_argumentation_and_revision",
    "journal_target_tradeoffs_within_frozen_quality_contract",
)
HUMAN_GATE_DECISIONS = (
    "direction_reset_or_primary_question_change",
    "major_claim_boundary_expansion",
    "external_release_or_submission_authorization",
)
FINAL_SCIENTIFIC_AUDIT_CHECKS = (
    "claim_traceability_to_evidence_ledger",
    "review_closure_against_review_ledger",
    "submission_readiness_against_paper_quality_contract",
)
DOWNSTREAM_CONTRACT_ROLES = {
    "evidence_ledger": "records evidence against evidence_expectations",
    "review_ledger": "records review closure against review_expectations",
    "final_audit": "audits scientific and paper-quality readiness against this charter",
}
DEFAULT_BOUNDED_ANALYSIS_ALLOWED_SCENARIOS = (
    "close_predeclared_evidence_gap_within_locked_direction",
    "close_predeclared_review_gap_within_locked_direction",
    "close_predeclared_submission_gap_within_locked_direction",
)
DEFAULT_BOUNDED_ANALYSIS_ALLOWED_TARGETS = (
    "minimum_sci_ready_evidence_package",
    "scientific_followup_questions",
    "manuscript_conclusion_redlines",
)
DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY = {
    "max_analysis_rounds_per_gate_window": 2,
    "max_targets_per_round": 3,
    "max_new_primary_claims": 0,
}
DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY = {
    "return_to_main_gate": "publication_eval",
    "return_to_mainline_action": "return_to_controller",
    "completion_criteria": [
        "all_requested_targets_closed",
        "budget_boundary_reached",
        "major_boundary_signal_detected",
    ],
    "required_updates": [
        "evidence_ledger",
        "review_ledger",
        "publication_eval",
    ],
}

DEFAULT_METHODS_COMPLETENESS_CONTRACT = {
    "study_design": {"status": "required_before_first_full_draft"},
    "cohort": {"status": "required_before_first_full_draft"},
    "variables": {"status": "required_before_first_full_draft"},
    "model": {"status": "required_before_first_full_draft"},
    "validation": {"status": "required_before_first_full_draft"},
    "statistical_analysis": {"status": "required_before_first_full_draft"},
}
DEFAULT_STATISTICAL_REPORTING_CONTRACT = {
    "summary_format": {"status": "required_before_first_full_draft"},
    "p_values": {"status": "required_before_first_full_draft"},
    "subgroup_tests": {"status": "required_before_first_full_draft"},
}
DEFAULT_CLINICAL_ACTIONABILITY_CONTRACT = {
    "treatment_gap": {"status": "required_before_first_full_draft"},
    "follow_up_or_outcome_relevance": {"status": "required_before_first_full_draft"},
}
DEFAULT_DRAFT_PREVENTION_GATES = (
    "introduction_three_paragraph_medical_narrative",
    "methods_subsections_complete_before_first_full_draft",
    "statistical_reporting_plan_before_results_prose",
    "table_figure_claim_map_before_results_prose",
    "first_draft_asset_upgrade_scan_before_full_draft",
    "phenotype_clinical_actionability_before_submission_package",
    "human_metadata_todo_separated_from_scientific_blockers",
)
DEFAULT_FIRST_DRAFT_QUALITY_CONTRACT = {
    "status": "required_before_first_full_draft",
    "pre_draft_upgrade_scan": {
        "status": "required_before_first_full_draft",
        "required_axes": [
            "timepoint_or_temporal_depth",
            "stakeholder_or_role_contrast",
            "center_geography_or_site_coverage",
            "guideline_correspondence",
            "clinically_legible_subgroup_or_association_plan",
            "real_world_adoption_constraints",
        ],
    },
    "field_verification_policy": {
        "multicenter_or_national_claims": "verify supporting fields before using multicenter or national framing",
        "subgroup_or_association_analyses": "predeclare bounded analyses only when verified variables support them",
    },
    "too_light_draft_route_back": {
        "route": "analysis-campaign",
        "trigger": "verified data dimensions can support a stronger paper than the current descriptive draft",
        "claim_boundary": "no_new_primary_claims_without_human_gate",
    },
    "discussion_floor": [
        "guideline_logic",
        "price_or_cost",
        "reimbursement",
        "access",
        "safety",
        "clinician_recommendation",
    ],
}


def stable_study_charter_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_STUDY_CHARTER_RELATIVE_PATH).resolve()


def _non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _extract_target_journals(study_payload: dict[str, Any]) -> list[str]:
    shortlist = _string_list(study_payload.get("journal_shortlist"))
    if shortlist:
        return _dedupe_preserve_order(shortlist)

    raw_submission_targets = study_payload.get("submission_targets")
    if not isinstance(raw_submission_targets, list):
        return []

    names: list[str] = []
    for item in raw_submission_targets:
        if isinstance(item, dict):
            for key in ("journal_name", "journal", "name", "target"):
                text = _non_empty_string(item.get(key))
                if text is not None:
                    names.append(text)
                    break
            continue
        text = str(item).strip()
        if text:
            names.append(text)
    return _dedupe_preserve_order(names)


def _mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return dict(value)


def _non_negative_int(value: object, *, default: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return default
    return value


def _materialize_bounded_analysis_contract(study_payload: dict[str, Any]) -> dict[str, Any]:
    raw_contract = _mapping(study_payload.get("bounded_analysis"))
    raw_budget_boundary = _mapping(raw_contract.get("budget_boundary"))
    raw_completion_boundary = _mapping(raw_contract.get("completion_boundary"))
    allowed_scenarios = _string_list(raw_contract.get("allowed_scenarios")) or list(
        DEFAULT_BOUNDED_ANALYSIS_ALLOWED_SCENARIOS
    )
    allowed_targets = _string_list(raw_contract.get("allowed_targets")) or list(
        DEFAULT_BOUNDED_ANALYSIS_ALLOWED_TARGETS
    )
    completion_criteria = _string_list(raw_completion_boundary.get("completion_criteria")) or list(
        DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["completion_criteria"]
    )
    required_updates = _string_list(raw_completion_boundary.get("required_updates")) or list(
        DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["required_updates"]
    )
    return {
        "default_owner": "mas",
        "allowed_scenarios": allowed_scenarios,
        "allowed_targets": allowed_targets,
        "budget_boundary": {
            "max_analysis_rounds_per_gate_window": _non_negative_int(
                raw_budget_boundary.get("max_analysis_rounds_per_gate_window"),
                default=DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY["max_analysis_rounds_per_gate_window"],
            ),
            "max_targets_per_round": _non_negative_int(
                raw_budget_boundary.get("max_targets_per_round"),
                default=DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY["max_targets_per_round"],
            ),
            "max_new_primary_claims": _non_negative_int(
                raw_budget_boundary.get("max_new_primary_claims"),
                default=DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY["max_new_primary_claims"],
            ),
        },
        "completion_boundary": {
            "return_to_main_gate": _non_empty_string(raw_completion_boundary.get("return_to_main_gate"))
            or str(DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["return_to_main_gate"]),
            "return_to_mainline_action": _non_empty_string(
                raw_completion_boundary.get("return_to_mainline_action")
            )
            or str(DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["return_to_mainline_action"]),
            "completion_criteria": completion_criteria,
            "required_updates": required_updates,
        },
    }


def _materialize_structured_reporting_contract(study_payload: dict[str, Any]) -> dict[str, Any]:
    raw_contract = _mapping(study_payload.get("structured_reporting_contract"))
    actionability_required = raw_contract.get("clinical_actionability_required")
    if actionability_required is None:
        actionability_required = study_payload.get("clinical_actionability_required")
    manuscript_family = _non_empty_string(raw_contract.get("manuscript_family")) or _non_empty_string(
        study_payload.get("manuscript_family")
    )
    endpoint_type = _non_empty_string(raw_contract.get("endpoint_type")) or _non_empty_string(
        study_payload.get("endpoint_type")
    )
    reporting_guideline_family = (
        _non_empty_string(raw_contract.get("reporting_guideline_family"))
        or _non_empty_string(study_payload.get("reporting_guideline_family"))
        or (
            SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES.get(manuscript_family)
            if manuscript_family is not None
            else None
        )
    )
    archetype = (
        _non_empty_string(raw_contract.get("paper_archetype"))
        or _non_empty_string(study_payload.get("paper_archetype"))
        or _non_empty_string(study_payload.get("study_archetype"))
    )
    contract = {
        "draft_prevention_gates": list(DEFAULT_DRAFT_PREVENTION_GATES),
        "methods_completeness": _mapping(raw_contract.get("methods_completeness"))
        or dict(DEFAULT_METHODS_COMPLETENESS_CONTRACT),
        "statistical_reporting": _mapping(raw_contract.get("statistical_reporting"))
        or dict(DEFAULT_STATISTICAL_REPORTING_CONTRACT),
        "first_draft_quality_contract": _mapping(raw_contract.get("first_draft_quality_contract"))
        or _mapping(study_payload.get("first_draft_quality_contract"))
        or deepcopy(DEFAULT_FIRST_DRAFT_QUALITY_CONTRACT),
        "table_figure_claim_map_required": raw_contract.get("table_figure_claim_map_required") is not False,
        "human_metadata_admin_todos": [
            "authors",
            "affiliations",
            "corresponding_author",
            "ethics",
            "funding",
            "conflict_of_interest",
            "data_availability",
        ],
    }
    if archetype is not None:
        contract["paper_archetype"] = archetype
    if actionability_required is True:
        contract["clinical_actionability_required"] = True
        contract["clinical_actionability"] = _mapping(raw_contract.get("clinical_actionability")) or dict(
            DEFAULT_CLINICAL_ACTIONABILITY_CONTRACT
        )
    prediction_defaults = build_default_structured_reporting_contract(
        study_archetype=_non_empty_string(study_payload.get("study_archetype")),
        paper_archetype=archetype,
        manuscript_family=manuscript_family,
        endpoint_type=endpoint_type,
    )
    if prediction_defaults.get("prediction_model_reporting_required") is True:
        for key in (
            "study_archetype",
            "paper_archetype",
            "manuscript_family",
            "endpoint_type",
            "prediction_model_reporting_required",
            "prediction_methods",
            "time_to_event_prediction_reporting",
            "decision_curve_clinical_utility",
            "prediction_performance_reporting",
            "baseline_balance_reporting",
            "competing_risk_reporting_required",
            "competing_risk_reporting",
        ):
            if key not in prediction_defaults:
                continue
            raw_value = raw_contract.get(key)
            if isinstance(raw_value, dict):
                contract[key] = raw_value
            elif raw_value not in (None, "", []):
                contract[key] = raw_value
            elif key not in contract:
                contract[key] = deepcopy(prediction_defaults[key])
    if reporting_guideline_family is not None:
        contract["reporting_guideline_family"] = reporting_guideline_family.strip().upper()
        contract["quality_gate_expectation"] = build_guideline_quality_gate_expectation(
            reporting_guideline_family
        )
    return contract


def resolve_study_charter_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_study_charter_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("study charter reader only accepts the stable controller artifact")
    return stable_path


def read_study_charter(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    charter_path = resolve_study_charter_ref(study_root=study_root, ref=ref)
    payload = json.loads(charter_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"study charter payload must be a JSON object: {charter_path}")
    return payload


def materialize_study_charter(
    *,
    study_root: Path,
    study_id: str,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
    required_first_anchor: str | None = None,
) -> dict[str, str]:
    charter_path = stable_study_charter_path(study_root=study_root)
    title = _non_empty_string(study_payload.get("title")) or study_id
    paper_framing_summary = _non_empty_string(study_payload.get("paper_framing_summary"))
    minimum_sci_ready_evidence_package = _string_list(study_payload.get("minimum_sci_ready_evidence_package"))
    scientific_followup_questions = _string_list(study_payload.get("scientific_followup_questions"))
    explanation_targets = _string_list(study_payload.get("explanation_targets"))
    manuscript_conclusion_redlines = _string_list(study_payload.get("manuscript_conclusion_redlines"))
    publication_objective = (
        _non_empty_string(study_payload.get("primary_question"))
        or paper_framing_summary
        or title
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "charter_id": f"charter::{study_id}::v1",
        "study_id": study_id,
        "title": title,
        "publication_objective": publication_objective,
        "paper_framing_summary": paper_framing_summary,
        "minimum_sci_ready_evidence_package": minimum_sci_ready_evidence_package,
        "scientific_followup_questions": scientific_followup_questions,
        "explanation_targets": explanation_targets,
        "manuscript_conclusion_redlines": manuscript_conclusion_redlines,
        "autonomy_envelope": {
            "decision_policy": _non_empty_string(execution.get("decision_policy")) or "autonomous",
            "launch_profile": _non_empty_string(execution.get("launch_profile")) or "continue_existing_state",
            "required_first_anchor": _non_empty_string(required_first_anchor),
            "direction_lock_state": "startup_frozen",
            "autonomous_scientific_decision_scope": {
                "phase": "post_direction_lock",
                "default_owner": "mas",
                "covered_decisions": list(AUTONOMOUS_SCIENTIFIC_DECISIONS),
            },
            "human_gate_boundary": {
                "policy": "major_boundary_only",
                "required_human_decisions": list(HUMAN_GATE_DECISIONS),
            },
            "final_scientific_audit_boundary": {
                "audit_surfaces": ["evidence_ledger", "review_ledger", "final_audit"],
                "required_checks": list(FINAL_SCIENTIFIC_AUDIT_CHECKS),
            },
        },
        "paper_quality_contract": {
            "frozen_at_startup": True,
            "target_journals": _extract_target_journals(study_payload),
            "reporting_expectations": {
                "paper_framing_summary": paper_framing_summary,
                "explanation_targets": explanation_targets,
            },
            "evidence_expectations": {
                "minimum_sci_ready_evidence_package": minimum_sci_ready_evidence_package,
            },
            "review_expectations": {
                "scientific_followup_questions": scientific_followup_questions,
                "manuscript_conclusion_redlines": manuscript_conclusion_redlines,
            },
            "bounded_analysis": _materialize_bounded_analysis_contract(study_payload),
            "structured_reporting_contract": _materialize_structured_reporting_contract(study_payload),
            "downstream_contract_roles": dict(DOWNSTREAM_CONTRACT_ROLES),
        },
    }
    charter_path.parent.mkdir(parents=True, exist_ok=True)
    charter_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "charter_id": str(payload["charter_id"]),
        "artifact_path": str(charter_path),
    }
