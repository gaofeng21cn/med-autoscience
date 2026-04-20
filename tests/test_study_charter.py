from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.study_charter"
EXPECTED_ROUTE_DISCIPLINE = {
    "named_routes": [
        "scout",
        "baseline",
        "analysis-campaign",
        "write",
        "finalize",
        "decision",
    ],
    "controller_first_required": True,
    "memory_reuse_required": True,
    "prefer_lightest_honest_route": True,
    "write_back_required": True,
    "startup_blockers_route_to": "required_first_anchor",
    "quality_or_route_gaps_route_through": "decision",
    "review_loop": [
        "verify_stage_contract_before_expanding_scope",
        "record_gap_in_durable_artifacts_before_reroute",
    ],
}
EXPECTED_STAGE_EXPECTATIONS = {
    "scout": {
        "route_name": "scout",
        "stage_purpose": "lock framing and name the next honest route",
        "minimum_outputs": [
            "task_and_evaluation_contract_locked",
            "local_reference_and_baseline_neighborhood_recorded",
            "next_route_or_blocker_named",
        ],
        "stop_conditions": [
            "next_route_is_obvious_and_recorded",
            "blocking_unknowns_are_explicit",
        ],
        "route_back_targets": ["baseline", "decision"],
    },
    "baseline": {
        "route_name": "baseline",
        "stage_purpose": "establish a trustworthy comparator surface for the paper route",
        "minimum_outputs": [
            "baseline_route_and_scope_named",
            "cohort_endpoint_time_horizon_checked",
            "methods_and_configuration_surface_recorded",
        ],
        "stop_conditions": [
            "comparator_is_trustworthy_enough_for_decision",
            "baseline_blocker_or_low_yield_expansion_is_explicit",
        ],
        "route_back_targets": ["decision"],
    },
    "analysis-campaign": {
        "route_name": "analysis-campaign",
        "stage_purpose": "close a named publication-relevant evidence gap with bounded follow-up work",
        "minimum_outputs": [
            "target_gap_and_campaign_scope_recorded",
            "publication_relevant_slice_completed",
            "write_back_surface_updated",
        ],
        "stop_conditions": [
            "named_gap_is_closed",
            "budget_boundary_or_major_boundary_signal_is_hit",
        ],
        "route_back_targets": ["decision", "write"],
    },
    "write": {
        "route_name": "write",
        "stage_purpose": "test whether the accepted evidence supports a stable manuscript narrative",
        "minimum_outputs": [
            "outline_or_section_contract_selected",
            "claim_evidence_bindings_recorded",
            "active_writing_contract_recorded",
        ],
        "stop_conditions": [
            "draft_or_bundle_reaches_stable_review_state",
            "missing_evidence_requires_route_back",
        ],
        "route_back_targets": ["decision", "analysis-campaign", "scout"],
    },
    "finalize": {
        "route_name": "finalize",
        "stage_purpose": "materialize an honest closure, publish, or continue-later surface",
        "minimum_outputs": [
            "final_claim_ledger_updated",
            "closure_recommendation_recorded",
            "resume_or_handoff_surface_refreshed",
        ],
        "stop_conditions": [
            "closure_surface_is_auditable",
            "reopen_blocker_or_route_back_is_named",
        ],
        "route_back_targets": ["decision", "write"],
    },
    "decision": {
        "route_name": "decision",
        "stage_purpose": "choose the smallest honest next route from durable evidence",
        "minimum_outputs": [
            "decision_question_named",
            "decision_relevant_evidence_summarized",
            "verdict_action_and_next_route_recorded",
        ],
        "stop_conditions": [
            "next_route_is_durably_selected",
            "blocking_gap_is_rerouted_to_a_named_stage",
        ],
        "route_back_targets": ["scout", "baseline", "analysis-campaign", "write", "finalize"],
    },
}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_resolve_study_charter_ref_defaults_to_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_study_charter_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "controller" / "study_charter.json").resolve()


def test_read_study_charter_reads_stable_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    _write_json(
        charter_path,
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
    )

    payload = module.read_study_charter(study_root=study_root)

    assert payload == {
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "risk stratification external validation",
    }


def test_resolve_study_charter_ref_rejects_runtime_backflow_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_ref = study_root / "runtime" / "quests" / "001-risk" / "quest.yaml"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_study_charter_ref(study_root=study_root, ref=runtime_ref)


def test_resolve_study_charter_ref_rejects_status_root_pollution_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    status_ref = study_root / "artifacts" / "status" / "study_charter.json"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_study_charter_ref(study_root=study_root, ref=status_ref)


def test_resolve_study_charter_ref_rejects_cross_repo_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "repo-a" / "studies" / "001-risk"
    cross_repo_ref = tmp_path / "repo-b" / "studies" / "001-risk" / "artifacts" / "controller" / "study_charter.json"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_study_charter_ref(study_root=study_root, ref=cross_repo_ref)


def test_read_study_charter_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    _write_json(charter_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_study_charter(study_root=study_root)


def test_materialize_study_charter_writes_stable_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    written_ref = module.materialize_study_charter(
        study_root=study_root,
        study_id="001-risk",
        study_payload={
            "title": "Diabetes mortality risk paper",
            "primary_question": "Build a submission-ready survival-risk study.",
            "paper_framing_summary": "Clinical survival framing is fixed around CVD-related mortality.",
            "journal_shortlist": ["The BMJ", "JAMA Internal Medicine"],
            "minimum_sci_ready_evidence_package": ["external_validation", "decision_curve_analysis"],
            "scientific_followup_questions": [
                "Why is the 5-year all-cause mortality gap between China and the US so large?",
            ],
            "explanation_targets": [
                "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
            ],
            "manuscript_conclusion_redlines": [
                "Do not conclude only that a China-trained absolute risk model is non-transportable.",
            ],
            "bounded_analysis": {
                "allowed_scenarios": [
                    "close_survival_calibration_gap_within_locked_direction",
                    "answer_predeclared_reviewer_method_question",
                ],
                "allowed_targets": [
                    "minimum_sci_ready_evidence_package",
                    "scientific_followup_questions",
                ],
                "budget_boundary": {
                    "max_analysis_rounds_per_gate_window": 3,
                    "max_targets_per_round": 2,
                    "max_new_primary_claims": 0,
                },
                "completion_boundary": {
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
                },
            },
        },
        execution={
            "decision_policy": "autonomous",
            "launch_profile": "continue_existing_state",
        },
        required_first_anchor="write",
    )

    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    payload = json.loads(charter_path.read_text(encoding="utf-8"))

    assert written_ref == {
        "charter_id": "charter::001-risk::v1",
        "artifact_path": str(charter_path.resolve()),
    }
    assert payload["schema_version"] == 1
    assert payload["charter_id"] == "charter::001-risk::v1"
    assert payload["study_id"] == "001-risk"
    assert payload["title"] == "Diabetes mortality risk paper"
    assert payload["publication_objective"] == "Build a submission-ready survival-risk study."
    assert payload["paper_framing_summary"] == "Clinical survival framing is fixed around CVD-related mortality."
    assert payload["minimum_sci_ready_evidence_package"] == ["external_validation", "decision_curve_analysis"]
    assert payload["scientific_followup_questions"] == [
        "Why is the 5-year all-cause mortality gap between China and the US so large?",
    ]
    assert payload["explanation_targets"] == [
        "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
    ]
    assert payload["manuscript_conclusion_redlines"] == [
        "Do not conclude only that a China-trained absolute risk model is non-transportable.",
    ]
    assert payload["autonomy_envelope"] == {
        "decision_policy": "autonomous",
        "launch_profile": "continue_existing_state",
        "required_first_anchor": "write",
        "direction_lock_state": "startup_frozen",
        "autonomous_scientific_decision_scope": {
            "phase": "post_direction_lock",
            "default_owner": "mas",
            "covered_decisions": [
                "analysis_plan_within_locked_direction",
                "evidence_generation_and_sufficiency_judgment",
                "manuscript_argumentation_and_revision",
                "journal_target_tradeoffs_within_frozen_quality_contract",
            ],
        },
        "human_gate_boundary": {
            "policy": "major_boundary_only",
            "required_human_decisions": [
                "direction_reset_or_primary_question_change",
                "major_claim_boundary_expansion",
                "external_release_or_submission_authorization",
            ],
        },
        "final_scientific_audit_boundary": {
            "audit_surfaces": ["evidence_ledger", "review_ledger", "final_audit"],
            "required_checks": [
                "claim_traceability_to_evidence_ledger",
                "review_closure_against_review_ledger",
                "submission_readiness_against_paper_quality_contract",
            ],
        },
    }
    assert payload["paper_quality_contract"] == {
        "frozen_at_startup": True,
        "target_journals": ["The BMJ", "JAMA Internal Medicine"],
        "reporting_expectations": {
            "paper_framing_summary": "Clinical survival framing is fixed around CVD-related mortality.",
            "explanation_targets": [
                "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
            ],
        },
        "evidence_expectations": {
            "minimum_sci_ready_evidence_package": ["external_validation", "decision_curve_analysis"],
        },
        "review_expectations": {
            "scientific_followup_questions": [
                "Why is the 5-year all-cause mortality gap between China and the US so large?",
            ],
            "manuscript_conclusion_redlines": [
                "Do not conclude only that a China-trained absolute risk model is non-transportable.",
            ],
        },
        "bounded_analysis": {
            "default_owner": "mas",
            "allowed_scenarios": [
                "close_survival_calibration_gap_within_locked_direction",
                "answer_predeclared_reviewer_method_question",
            ],
            "allowed_targets": [
                "minimum_sci_ready_evidence_package",
                "scientific_followup_questions",
            ],
            "budget_boundary": {
                "max_analysis_rounds_per_gate_window": 3,
                "max_targets_per_round": 2,
                "max_new_primary_claims": 0,
            },
            "completion_boundary": {
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
            },
        },
        "route_discipline": EXPECTED_ROUTE_DISCIPLINE,
        "stage_expectations": EXPECTED_STAGE_EXPECTATIONS,
        "downstream_contract_roles": {
            "evidence_ledger": "records evidence against evidence_expectations",
            "review_ledger": "records review closure against review_expectations",
            "final_audit": "audits scientific and paper-quality readiness against this charter",
        },
    }


def test_materialize_study_charter_sets_default_contract_boundaries(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "002-minimal"

    module.materialize_study_charter(
        study_root=study_root,
        study_id="002-minimal",
        study_payload={
            "title": "Minimal charter",
        },
        execution={},
        required_first_anchor=None,
    )

    payload = json.loads((study_root / "artifacts" / "controller" / "study_charter.json").read_text(encoding="utf-8"))

    assert payload["autonomy_envelope"]["decision_policy"] == "autonomous"
    assert payload["autonomy_envelope"]["launch_profile"] == "continue_existing_state"
    assert payload["autonomy_envelope"]["required_first_anchor"] is None
    assert payload["autonomy_envelope"]["direction_lock_state"] == "startup_frozen"
    assert payload["autonomy_envelope"]["human_gate_boundary"]["policy"] == "major_boundary_only"
    assert payload["autonomy_envelope"]["final_scientific_audit_boundary"]["audit_surfaces"] == [
        "evidence_ledger",
        "review_ledger",
        "final_audit",
    ]
    assert payload["paper_quality_contract"] == {
        "frozen_at_startup": True,
        "target_journals": [],
        "reporting_expectations": {
            "paper_framing_summary": None,
            "explanation_targets": [],
        },
        "evidence_expectations": {
            "minimum_sci_ready_evidence_package": [],
        },
        "review_expectations": {
            "scientific_followup_questions": [],
            "manuscript_conclusion_redlines": [],
        },
        "bounded_analysis": {
            "default_owner": "mas",
            "allowed_scenarios": [
                "close_predeclared_evidence_gap_within_locked_direction",
                "close_predeclared_review_gap_within_locked_direction",
                "close_predeclared_submission_gap_within_locked_direction",
            ],
            "allowed_targets": [
                "minimum_sci_ready_evidence_package",
                "scientific_followup_questions",
                "manuscript_conclusion_redlines",
            ],
            "budget_boundary": {
                "max_analysis_rounds_per_gate_window": 2,
                "max_targets_per_round": 3,
                "max_new_primary_claims": 0,
            },
            "completion_boundary": {
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
            },
        },
        "route_discipline": EXPECTED_ROUTE_DISCIPLINE,
        "stage_expectations": EXPECTED_STAGE_EXPECTATIONS,
        "downstream_contract_roles": {
            "evidence_ledger": "records evidence against evidence_expectations",
            "review_ledger": "records review closure against review_expectations",
            "final_audit": "audits scientific and paper-quality readiness against this charter",
        },
    }
