from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from med_autoscience.stable_json import write_stable_json
from med_autoscience.controllers.medical_reporting_guidelines import build_guideline_quality_gate_expectation
from med_autoscience.policies.medical_manuscript_draft_quality import (
    build_medical_manuscript_blueprint_contract,
    build_medical_prose_style_contract,
    build_medical_prose_review_contract,
    build_pre_draft_writing_readiness_contract,
)
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
DEFAULT_PROTOCOL_SAP_REQUIRED_UPDATES = (
    "study_charter",
    "analysis_campaign_plan",
    "evidence_ledger",
    "review_ledger",
    "publication_eval",
)
DEFAULT_PROTOCOL_SAP_ROUTE_BACK_POLICY = {
    "missing_required_item": "decision",
    "changed_primary_question_or_endpoint": "human_gate",
    "changed_analysis_plan_within_locked_direction": "analysis-campaign",
}
PROTOCOL_SAP_FREEZE_INPUT_KEYS = (
    "study_design",
    "target_population",
    "cohort_boundary",
    "population_or_cohort_boundary",
    "endpoint_type",
    "primary_endpoint",
    "primary_analysis",
    "secondary_analyses",
    "statistical_methods",
    "missing_data_plan",
    "subgroup_plan",
    "multiplicity_guardrails",
    "power_precision_rationale",
    "power_precision_or_feasibility_rationale",
    "reporting_guideline_family",
    "protocol_ref",
    "sap_ref",
    "freeze_ref",
)

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
    "imrad_section_contract": {
        "article_body": ["Title", "Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion"],
        "abstract": [
            "clinical_context",
            "objective",
            "design_setting_participants",
            "exposures_or_predictors",
            "main_outcome",
            "results",
            "conclusion_and_boundary",
        ],
        "introduction": ["clinical_problem", "specific_gap", "study_objective_and_contribution"],
        "discussion": ["principal_findings", "relation_to_prior_work", "clinical_interpretation", "limitations", "conclusion"],
    },
    "manuscript_native_prose": {
        "required": True,
        "forbidden_modes": [
            "work_report_question_answer_frame",
            "figure_table_anchor_section",
            "author_confirmation_placeholder",
            "figure_self_explanation_paragraph",
            "analysis_or_controller_jargon",
            "claim_boundary_meta_language_in_body",
        ],
        "result_section_rule": "answer the clinical finding directly, then cite supporting figures or tables",
        "scope_boundary_rule": "state limits as clinical interpretation and limitations, not as controller notes",
    },
    "medical_prose_style_contract": build_medical_prose_style_contract(),
    "medical_manuscript_blueprint_contract": build_medical_manuscript_blueprint_contract(),
    "pre_draft_writing_readiness_contract": build_pre_draft_writing_readiness_contract(),
    "medical_prose_review_contract": build_medical_prose_review_contract(),
    "first_draft_generation_model": {
        "pre_draft_inputs": [
            "clinical_problem",
            "study_design",
            "target_population",
            "prediction_timepoint_or_exposure_window",
            "outcome_definition_and_horizon",
            "analysis_plan",
            "display_to_claim_map",
            "reader_facing_contribution",
            "medical_manuscript_blueprint",
            "pre_draft_writing_readiness",
            "medical_prose_style_contract",
            "medical_prose_review",
        ],
        "writer_obligations": [
            "convert research questions into clinical findings rather than question-answer prose",
            "separate manuscript body from submission metadata, author confirmations, and operations notes",
            "write figure legends as reader interpretation aids rather than reviewer instructions",
            "stage Results from cohort and endpoint profile to main finding, validation, clinical utility, and sensitivity or subgroup evidence",
            "stage Discussion from principal finding to prior literature, interpretation, limitations, and practical next step",
        ],
        "route_back_if_missing": "return_to_outline_or_analysis_campaign_before_first_full_draft",
    },
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


def _materialize_first_draft_quality_contract(raw_contract: dict[str, Any]) -> dict[str, Any]:
    contract = deepcopy(DEFAULT_FIRST_DRAFT_QUALITY_CONTRACT)
    contract.update(raw_contract)
    contract["pre_draft_writing_readiness_contract"] = _mapping(
        raw_contract.get("pre_draft_writing_readiness_contract")
    ) or build_pre_draft_writing_readiness_contract()
    contract["quality_proxy_exclusion_policy"] = _mapping(
        raw_contract.get("quality_proxy_exclusion_policy")
    ) or {
        "controller_or_progress_surfaces_can_authorize_body_quality": False,
        "forbidden_quality_proxies": [
            "controller_checklist",
            "run_log_or_execution_transcript",
            "progress_prose",
            "generic_completion_checklist",
            "packaging_metadata",
        ],
    }
    generation_model = _mapping(contract.get("first_draft_generation_model"))
    pre_draft_inputs = _string_list(generation_model.get("pre_draft_inputs"))
    if "pre_draft_writing_readiness" not in pre_draft_inputs:
        pre_draft_inputs.append("pre_draft_writing_readiness")
    generation_model["pre_draft_inputs"] = pre_draft_inputs
    contract["first_draft_generation_model"] = generation_model
    return contract


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
        "first_draft_quality_contract": _materialize_first_draft_quality_contract(
            _mapping(raw_contract.get("first_draft_quality_contract"))
            or _mapping(study_payload.get("first_draft_quality_contract"))
        ),
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


def _materialize_protocol_sap_freeze_contract(
    study_payload: dict[str, Any],
    *,
    structured_reporting_contract: dict[str, Any],
) -> dict[str, Any]:
    raw_contract = _mapping(study_payload.get("protocol_sap_freeze"))
    raw_contract = {**raw_contract}

    def _field(name: str) -> Any:
        if name in raw_contract:
            return raw_contract.get(name)
        return study_payload.get(name)

    has_freeze_inputs = bool(raw_contract) or any(
        _field(key) not in (None, "", []) for key in PROTOCOL_SAP_FREEZE_INPUT_KEYS
    )
    reporting_guideline_family = (
        _non_empty_string(_field("reporting_guideline_family"))
        or _non_empty_string(structured_reporting_contract.get("reporting_guideline_family"))
    )
    status = _non_empty_string(_field("status")) or (
        "frozen_at_startup" if has_freeze_inputs else "requires_freeze_before_analysis"
    )
    return {
        "surface": "protocol_sap_freeze",
        "status": status,
        "required_before_routes": ["analysis-campaign", "write", "finalize"],
        "gate_relaxation_allowed": False,
        "owner": _non_empty_string(_field("freeze_owner")) or _non_empty_string(_field("owner")) or "mas",
        "freeze_ref": _non_empty_string(_field("freeze_ref")),
        "protocol_ref": _non_empty_string(_field("protocol_ref")),
        "sap_ref": _non_empty_string(_field("sap_ref")),
        "study_design": _non_empty_string(_field("study_design")),
        "population_or_cohort_boundary": (
            _non_empty_string(_field("population_or_cohort_boundary"))
            or _non_empty_string(_field("cohort_boundary"))
        ),
        "target_population": _non_empty_string(_field("target_population")),
        "endpoint_type": _non_empty_string(_field("endpoint_type")),
        "primary_endpoint": _non_empty_string(_field("primary_endpoint")),
        "primary_analysis": _non_empty_string(_field("primary_analysis")),
        "secondary_analyses": _string_list(_field("secondary_analyses")),
        "statistical_methods": _string_list(_field("statistical_methods")),
        "missing_data_plan": _non_empty_string(_field("missing_data_plan")),
        "subgroup_plan": _string_list(_field("subgroup_plan")),
        "multiplicity_guardrails": _string_list(_field("multiplicity_guardrails")),
        "power_precision_or_feasibility_rationale": (
            _non_empty_string(_field("power_precision_or_feasibility_rationale"))
            or _non_empty_string(_field("power_precision_rationale"))
        ),
        "reporting_guideline_family": reporting_guideline_family.upper()
        if reporting_guideline_family is not None
        else None,
        "required_updates_when_changed": list(DEFAULT_PROTOCOL_SAP_REQUIRED_UPDATES),
        "route_back_policy": dict(DEFAULT_PROTOCOL_SAP_ROUTE_BACK_POLICY),
    }


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
    structured_reporting_contract = _materialize_structured_reporting_contract(study_payload)
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
            "protocol_sap_freeze": _materialize_protocol_sap_freeze_contract(
                study_payload,
                structured_reporting_contract=structured_reporting_contract,
            ),
            "bounded_analysis": _materialize_bounded_analysis_contract(study_payload),
            "structured_reporting_contract": structured_reporting_contract,
            "downstream_contract_roles": dict(DOWNSTREAM_CONTRACT_ROLES),
        },
    }
    write_stable_json(charter_path, payload)
    return {
        "charter_id": str(payload["charter_id"]),
        "artifact_path": str(charter_path),
    }
