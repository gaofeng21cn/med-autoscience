from __future__ import annotations

import importlib

from .test_publication_work_units_cases.delivery_specificity_cases import *  # noqa: F403,F401


def test_blocked_claim_evidence_route_requires_specificity_when_gate_only_names_generic_claim_label() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "medical_publication_surface_named_blockers": [
                "claim_evidence_consistency_failed",
            ],
            "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
        }
    )

    assert result["fingerprint"].startswith("publication-blockers::")
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["next_work_unit"]["lane"] == "controller"
    assert (
        result["next_work_unit"]["summary"]
        == "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets."
    )
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["controller_work_unit_executable"] is False
    assert result["next_work_unit"]["non_executable_reason"] == "gate_needs_specificity_without_targets"
    assert result["next_work_unit"]["required_target_kinds"] == [
        "claim",
        "display",
        "evidence_source",
        "citation",
        "metric",
        "package_artifact",
        "authorization_provenance",
    ]


def test_blocked_claim_evidence_route_produces_analysis_campaign_work_unit_for_specific_contract_gaps() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "medical_publication_surface_named_blockers": [
                "claim_evidence_consistency_failed",
                "storyline_evidence_map_missing",
                "figure_results_trace_incomplete",
            ],
            "blocking_artifact_refs": [{"source_path": "paper/contracts/storyline_evidence_map.json"}],
            "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
        }
    )

    assert result["next_work_unit"] == {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
    }
    assert result["next_work_unit"].get("controller_work_unit_executable") is not False
    assert "non_executable_reason" not in result["next_work_unit"]


def test_generic_claim_label_with_only_artifact_path_still_requires_specificity() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "medical_publication_surface_named_blockers": [
                "claim_evidence_consistency_failed",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "artifact_path": "/tmp/study/paper/claim_evidence_map.json",
                    "artifact_role": "claim_evidence_map",
                }
            ],
        }
    )

    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"


def test_generic_claim_label_with_package_artifact_is_specific_enough_for_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "medical_publication_surface_named_blockers": [
                "claim_evidence_consistency_failed",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "package_artifact": "current_package/tables/table_2.docx",
                }
            ],
        }
    )

    assert result["actionability_status"] == "actionable"
    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


def test_generic_claim_label_with_provenance_source_path_is_specific_enough_for_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "medical_publication_surface_named_blockers": [
                "claim_evidence_consistency_failed",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "provenance_source_path": "paper/evidence_ledger.md",
                }
            ],
        }
    )

    assert result["actionability_status"] == "actionable"
    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


def test_generic_surface_blocker_with_complete_specificity_targets_routes_to_claim_evidence_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "bundle_tasks_downstream_only": True,
        },
        specificity_targets=[
            {
                "target_kind": "claim",
                "target_id": "claim_evidence_map",
                "source_path": "/tmp/study/paper/claim_evidence_map.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "figure",
                "target_id": "figure_catalog",
                "source_path": "/tmp/study/paper/figures/figure_catalog.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "metric",
                "target_id": "main_result_metrics",
                "source_path": "/tmp/quest/artifacts/results/main_result.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "table",
                "target_id": "submission_table_or_manifest",
                "source_path": "/tmp/study/paper/submission_minimal/audit/submission_manifest.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "source_path",
                "target_id": "publication_gate_source_path",
                "source_path": "/tmp/quest/artifacts/reports/medical_publication_surface/latest.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
        ],
    )

    assert result["actionability_status"] == "actionable"
    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert "non_executable_reason" not in result["next_work_unit"]
    assert {ref["target_id"] for ref in result["blocking_artifact_refs"]} == {
        "claim_evidence_map",
        "figure_catalog",
        "main_result_metrics",
        "publication_gate_source_path",
        "submission_table_or_manifest",
    }


def test_unit_harmonization_specificity_target_routes_to_hard_methodology_owner() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "bundle_tasks_downstream_only": True,
        },
        specificity_targets=[
            {
                "target_kind": "claim",
                "target_id": "transported_score_claim",
                "source_path": "/tmp/study/paper/claim_evidence_map.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "figure",
                "target_id": "risk_distribution_collapse_figure",
                "source_path": "/tmp/study/paper/figures/figure_catalog.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "table",
                "target_id": "table_2_validation_performance",
                "source_path": "/tmp/study/paper/tables/table_catalog.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "metric",
                "target_id": "hdl_unit_standardized_sensitivity",
                "source_path": "/tmp/quest/artifacts/analysis/harmonization_route_back/latest.md",
                "blocking_reason": "unit_standardized_model_application_or_sensitivity",
            },
            {
                "target_kind": "source_path",
                "target_id": "publication_gate_source_path",
                "source_path": "/tmp/quest/artifacts/publication_eval/latest.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
        ],
    )

    assert result["actionability_status"] == "hard_methodology_route_required"
    assert result["next_work_unit"] == {
        "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
        "lane": "analysis-campaign",
        "summary": (
            "Materialize a unit-harmonized external-validation rerun or a typed methodology blocker "
            "before prose, gate, or package clearance."
        ),
        "hard_methodology": True,
        "required_owner": "analysis_harmonization_owner",
        "required_next_work_unit": "unit_harmonized_external_validation_rerun",
        "typed_blocker": "unit_harmonized_rerun_required",
    }
    assert result["hard_methodology_target"]["required_owner"] == "analysis_harmonization_owner"
    assert result["hard_methodology_target"]["required_next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert result["hard_methodology_target"]["typed_blocker"] == "unit_harmonized_rerun_required"


def test_unit_harmonization_target_does_not_require_complete_specificity_kinds() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "bundle_tasks_downstream_only": True,
        },
        specificity_targets=[
            {
                "target_kind": "metric",
                "target_id": "c_index_confidence_intervals",
                "source_path": "/tmp/study/artifacts/results/main_result.json",
                "blocking_reason": "Prediction-model validation reporting is incomplete without uncertainty.",
            },
            {
                "target_kind": "source_path",
                "target_id": "hdL_unit_standardized_sensitivity",
                "source_path": "/tmp/study/paper/claim_evidence_map.json",
                "blocking_reason": "The HDL shift cannot be interpreted without unit checks.",
            },
        ],
    )

    assert result["actionability_status"] == "hard_methodology_route_required"
    assert result["hard_methodology_target"]["target_id"] == "hdL_unit_standardized_sensitivity"
    assert result["hard_methodology_target"]["required_owner"] == "analysis_harmonization_owner"


def test_generic_surface_blocker_specificity_targets_preempt_downstream_delivery_churn() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": [
                "medical_publication_surface_blocked",
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
            ],
            "medical_publication_surface_status": "blocked",
            "study_delivery_status": "stale_source_changed",
            "study_delivery_stale_reason": "delivery_manifest_source_changed",
        },
        specificity_targets=[
            {
                "target_kind": "claim",
                "target_id": "claim_evidence_map",
                "source_path": "paper/claim_evidence_map.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "figure",
                "target_id": "figure_catalog",
                "source_path": "paper/figures/figure_catalog.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "table",
                "target_id": "submission_table_or_manifest",
                "source_path": "paper/submission_minimal/audit/submission_manifest.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "metric",
                "target_id": "main_result_metrics",
                "source_path": "artifacts/results/main_result.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
            {
                "target_kind": "source_path",
                "target_id": "publication_gate_source_path",
                "source_path": "artifacts/reports/medical_publication_surface/latest.json",
                "blocking_reason": "medical_publication_surface_blocked",
            },
        ],
    )

    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert [unit["unit_id"] for unit in result["blocking_work_units"]] == [
        "analysis_claim_evidence_repair",
        "figure_results_trace_repair",
        "submission_minimal_refresh",
    ]


def test_generic_display_label_with_display_ref_is_specific_enough_for_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "medical_publication_surface_named_blockers": [
                "reviewer_first_concerns_unresolved",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "reviewer_first_concerns_unresolved",
                    "display_ref": "Figure 2",
                    "provenance_source_path": "paper/review/review_ledger.json",
                }
            ],
        }
    )

    assert result["actionability_status"] == "actionable"
    assert result["next_work_unit"]["unit_id"] == "manuscript_story_repair"


def test_current_delivery_status_does_not_make_generic_gate_labels_actionable() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": [
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": [
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "study_delivery_status": "current",
            "submission_minimal_authority_status": "current",
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "artifact_path": "/tmp/paper/claim_evidence_map.json",
                    "artifact_role": "claim_evidence_map",
                },
                {
                    "blocker": "reviewer_first_concerns_unresolved",
                    "artifact_path": "/tmp/paper/review/review_ledger.json",
                    "artifact_role": "review_ledger",
                },
                {
                    "blocker": "submission_hardening_incomplete",
                    "artifact_path": "/tmp/paper/submission_minimal/submission_manifest.json",
                    "artifact_role": "submission_minimal_authority",
                },
            ],
        }
    )

    assert "current" not in result["blockers"]
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"


def test_missing_required_display_input_routes_to_display_contract_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "medical_publication_surface_named_blockers": [
                "missing_multicenter_generalizability_inputs",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "missing_multicenter_generalizability_inputs",
                    "artifact_path": "/tmp/study/paper/multicenter_generalizability_inputs.json",
                    "artifact_role": "display_input_payload",
                }
            ],
        }
    )

    assert result["next_work_unit"] == {
        "unit_id": "display_reporting_contract_repair",
        "lane": "finalize",
        "summary": "Repair display registry and local architecture reporting contracts.",
    }


def test_bundle_stage_stale_submission_package_produces_finalize_refresh_work_unit() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "complete_bundle_stage",
            "blockers": ["submission_minimal_stale", "current_package_outdated"],
            "study_delivery_status": "stale_submission_package",
        }
    )

    assert result["next_work_unit"] == {
        "unit_id": "submission_minimal_refresh",
        "lane": "finalize",
        "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
    }


def test_bundle_stage_submission_hardening_surface_label_routes_to_finalize_refresh() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "complete_bundle_stage",
            "supervisor_phase": "bundle_stage_blocked",
            "blockers": [
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
            ],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": [
                "submission_hardening_incomplete",
            ],
            "study_delivery_status": "current",
            "submission_minimal_authority_status": "current",
            "blocking_artifact_refs": [
                {
                    "blocker": "submission_hardening_incomplete",
                    "artifact_path": "/tmp/paper/submission_minimal/audit/submission_manifest.json",
                    "artifact_role": "submission_minimal_authority",
                    "source_path": "/tmp/paper/submission_minimal/audit/submission_manifest.json",
                },
            ],
        }
    )

    assert result["actionability_status"] == "actionable"
    assert result["fingerprint_blockers"] == [
        "complete_bundle_stage",
        "submission_hardening_incomplete",
    ]
    assert result["next_work_unit"] == {
        "unit_id": "submission_minimal_refresh",
        "lane": "finalize",
        "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
    }


def test_clear_current_bundle_stage_package_routes_to_terminal_handoff_not_sync_work_unit() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "clear",
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
            "study_delivery_status": "current",
            "submission_minimal_authority_status": "current",
            "medical_publication_surface_status": "clear",
            "submission_minimal_evaluated_source_signature": "source::ready",
            "submission_minimal_authority_source_signature": "source::ready",
            "study_delivery_evaluated_source_signature": "source::ready",
            "study_delivery_authority_source_signature": "source::ready",
            "current_package_freshness": {
                "status": "current",
                "proof_path": "/tmp/study/artifacts/controller/current_package_freshness/latest.json",
                "current_package_root": "/tmp/study/manuscript/current_package",
                "current_package_zip": "/tmp/study/manuscript/current_package.zip",
                "submission_manifest_path": "/tmp/study/paper/submission_minimal/submission_manifest.json",
                "source_signature": "source::ready",
                "authority_source_signature": "source::ready",
            },
        }
    )

    assert result["blockers"] == []
    assert result["fingerprint_blockers"] == []
    assert result["actionability_status"] == "terminal_package_ready_handoff"
    assert result["next_work_unit"] == {
        "unit_id": "package_ready_handoff",
        "lane": "human_gate",
        "summary": "Submission package is current; park automation until explicit user resume.",
        "controller_work_unit_executable": False,
        "non_executable_reason": "package_ready_waiting_for_explicit_resume",
    }


def test_clear_continue_bundle_stage_without_package_freshness_proof_still_syncs_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "clear",
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
            "study_delivery_status": "current",
            "submission_minimal_authority_status": "current",
            "medical_publication_surface_status": "clear",
        }
    )

    assert result["blockers"] == []
    assert result["fingerprint_blockers"] == []
    assert result["actionability_status"] == "controller_bundle_stage_required"
    assert result["next_work_unit"] == {
        "unit_id": "submission_authority_sync_closure",
        "lane": "controller",
        "summary": "Regenerate submission authority signatures, then replay the publication gate.",
        "control_surface": "gate_clearing_batch",
    }


def test_stale_submission_authority_with_matching_signatures_routes_to_gate_replay() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "submission_minimal_authority_status": "current",
            "submission_minimal_evaluated_source_signature": "source::abc",
            "submission_minimal_authority_source_signature": "source::abc",
            "gate_fingerprint": "publication-gate::stale-authority",
            "blocking_artifact_refs": [
                {
                    "blocker": "stale_submission_minimal_authority",
                    "artifact_path": "/tmp/study/paper/submission_minimal/submission_manifest.json",
                }
            ],
        }
    )

    assert result["next_work_unit"] == {
        "unit_id": "publication_gate_replay",
        "lane": "controller",
        "summary": "Replay the publication gate against current authority signatures before dispatching new work.",
        "control_surface": "publication_gate",
    }
    assert result["actionability_status"] == "controller_gate_replay_required"
    assert result["gate_fingerprint"] == "publication-gate::stale-authority"
    assert result["blocking_artifact_refs"] == [
        {
            "blocker": "stale_submission_minimal_authority",
            "artifact_path": "/tmp/study/paper/submission_minimal/submission_manifest.json",
        }
    ]


def test_stale_delivery_mirror_with_current_authority_routes_to_gate_replay() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "complete_bundle_stage",
            "blockers": ["stale_study_delivery_mirror"],
            "study_delivery_status": "stale_source_changed",
            "study_delivery_stale_reason": "delivery_manifest_source_changed",
            "submission_minimal_authority_status": "current",
            "submission_minimal_evaluated_source_signature": "source::abc",
            "submission_minimal_authority_source_signature": "source::abc",
            "current_package_status": "fresh",
            "current_package_source_signature": "source::abc",
            "current_package_authority_source_signature": "source::abc",
            "current_package_freshness": {
                "status": "fresh",
                "source_unit_id": "sync_submission_minimal_delivery",
                "source_signature": "source::abc",
                "authority_source_signature": "source::abc",
                "submission_manifest_path": "/tmp/quest/paper/submission_minimal/submission_manifest.json",
                "current_package_root": "/tmp/study/manuscript/current_package",
                "proof_path": "/tmp/study/artifacts/controller/current_package_freshness/latest.json",
            },
            "gate_fingerprint": "publication-gate::stale-delivery",
        }
    )

    assert result["next_work_unit"] == {
        "unit_id": "submission_delivery_sync_closure",
        "lane": "controller",
        "summary": "Refresh the study delivery mirror from the current package, then replay the publication gate.",
        "control_surface": "gate_clearing_batch",
    }
    assert result["actionability_status"] == "controller_sync_closure_required"


def test_stale_delivery_mirror_without_current_package_proof_is_terminal_delivery_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "complete_bundle_stage",
            "blockers": ["stale_study_delivery_mirror"],
            "study_delivery_status": "stale_source_changed",
            "study_delivery_stale_reason": "delivery_manifest_source_changed",
            "submission_minimal_authority_status": "current",
            "submission_minimal_evaluated_source_signature": "source::abc",
            "submission_minimal_authority_source_signature": "source::abc",
            "current_package_status": "fresh",
            "current_package_source_signature": "source::abc",
            "current_package_authority_source_signature": "source::abc",
            "gate_fingerprint": "publication-gate::stale-delivery",
        }
    )

    assert result["actionability_status"] == "controller_delivery_blocked"
    assert result["next_work_unit"] == {
        "unit_id": "submission_delivery_terminal_blocker",
        "lane": "controller",
        "summary": "Record a controller-owned actionable blocker for downstream study delivery closure.",
        "control_surface": "gate_clearing_batch",
        "controller_work_unit_executable": False,
        "non_executable_reason": "current_package_freshness_proof_missing",
    }


def test_claim_story_figure_submission_hardening_cluster_starts_with_analysis_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "blockers": [
                "stale_submission_minimal_authority",
                "submission_hardening_incomplete",
                "claim_evidence_consistency_failed",
                "missing_medical_story_contract",
                "figure_semantics_manifest_missing_or_incomplete",
            ],
        }
    )

    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert [unit["unit_id"] for unit in result["blocking_work_units"]] == [
        "analysis_claim_evidence_repair",
        "manuscript_story_repair",
        "figure_results_trace_repair",
        "submission_minimal_refresh",
    ]


def test_registry_and_local_architecture_blockers_produce_display_reporting_contract_work_unit() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": [
                "display_registry_contract_missing",
                "local_architecture_overview_shell_missing",
                "local_architecture_input_missing",
            ],
        }
    )

    assert result["next_work_unit"] == {
        "unit_id": "display_reporting_contract_repair",
        "lane": "finalize",
        "summary": "Repair display registry and local architecture reporting contracts.",
    }
    assert [unit["unit_id"] for unit in result["blocking_work_units"]] == [
        "display_reporting_contract_repair",
        "local_architecture_overview_repair",
    ]


def test_current_003_and_004_blocker_names_map_to_narrow_work_units() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    dpcc = module.derive_publication_work_units(
        {
            "blockers": [
                "stale_submission_minimal_authority",
                "medical_publication_surface_blocked",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
            "medical_publication_surface_named_blockers": [
                "missing_medical_story_contract",
                "figure_catalog_missing_or_incomplete",
                "results_narrative_map_missing_or_incomplete",
                "claim_evidence_map_missing_or_incomplete",
                "treatment_gap_reporting_incomplete",
            ],
        }
    )
    pituitary = module.derive_publication_work_units(
        {
            "blockers": [
                "stale_submission_minimal_authority",
                "submission_surface_qc_failure_present",
                "registry_contract_mismatch",
                "missing_local_architecture_overview_shell",
                "missing_local_architecture_overview_inputs",
            ],
        }
    )

    assert dpcc["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert "treatment_gap_reporting_repair" in [unit["unit_id"] for unit in dpcc["blocking_work_units"]]
    assert pituitary["next_work_unit"]["unit_id"] == "submission_minimal_refresh"
    assert "display_reporting_contract_repair" in [unit["unit_id"] for unit in pituitary["blocking_work_units"]]
    assert "local_architecture_overview_repair" in [unit["unit_id"] for unit in pituitary["blocking_work_units"]]


def test_same_blocker_set_has_stable_order_independent_fingerprint() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    first = module.derive_publication_work_units(
        {
            "blockers": ["submission_minimal_stale", "current_package_outdated"],
            "medical_publication_surface_named_blockers": ["display_registry_contract_missing"],
        }
    )
    second = module.derive_publication_work_units(
        {
            "medical_publication_surface_named_blockers": ["display_registry_contract_missing"],
            "blockers": ["current_package_outdated", "submission_minimal_stale"],
        }
    )

    assert first["fingerprint"] == second["fingerprint"]


def test_generic_analysis_labels_with_downstream_delivery_churn_require_specificity_before_dispatch() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    with_delivery_churn = module.derive_publication_work_units(
        {
            "blockers": [
                "claim_evidence_consistency_failed",
                "medical_publication_surface_blocked",
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
                "submission_surface_qc_failure_present",
            ],
        }
    )
    claim_only = module.derive_publication_work_units(
        {
            "blockers": [
                "claim_evidence_consistency_failed",
                "medical_publication_surface_blocked",
            ],
        }
    )

    assert with_delivery_churn["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert with_delivery_churn["fingerprint"] == claim_only["fingerprint"]
    assert with_delivery_churn["fingerprint_blockers"] == [
        "claim_evidence_consistency_failed",
        "medical_publication_surface_blocked",
    ]


def test_generic_science_blockers_ignore_delivery_artifact_refs_for_specificity() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "blockers": [
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "medical_publication_surface_named_blockers": [
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "stale_submission_minimal_authority",
                    "artifact_path": "/tmp/paper/submission_minimal/submission_manifest.json",
                    "artifact_role": "submission_minimal_authority",
                    "stale_reason": "submission_source_newer_than_manifest",
                },
                {
                    "blocker": "stale_study_delivery_mirror",
                    "artifact_path": "/tmp/study/manuscript/delivery_manifest.json",
                    "artifact_role": "study_delivery_mirror",
                    "stale_reason": "delivery_manifest_sources_missing",
                },
            ],
            "paper_line_blocking_reasons": [
                "MAS medical manuscript blueprint lacks AI authorization/provenance",
                "MAS medical journal style corpus is incomplete",
                "MAS AI medical prose review request is incomplete or not AI reviewer-targeted",
                "MAS AI medical prose review is incomplete or not AI reviewer-owned",
            ],
        }
    )

    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert "analysis_claim_evidence_repair" not in [
        unit["unit_id"] for unit in result["blocking_work_units"]
    ]


def test_generic_science_blockers_with_missing_delivery_source_require_specificity() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "blockers": [
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "study_delivery_status": "stale_source_missing",
            "study_delivery_stale_reason": "delivery_manifest_sources_missing",
            "study_delivery_missing_source_paths": [
                "/tmp/runtime/paper/submission_minimal/manuscript_source.md",
            ],
            "medical_publication_surface_named_blockers": [
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "stale_submission_minimal_authority",
                    "artifact_path": "/tmp/paper/submission_minimal/submission_manifest.json",
                },
                {
                    "blocker": "stale_study_delivery_mirror",
                    "artifact_path": "/tmp/study/manuscript/delivery_manifest.json",
                },
            ],
        }
    )

    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["fingerprint_blockers"] == [
        "claim_evidence_consistency_failed",
        "medical_publication_surface_blocked",
        "reviewer_first_concerns_unresolved",
    ]


def test_non_actionable_gate_labels_require_specificity_before_dispatch() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "blockers": [
                "publication_gate_blocked",
                "submission_hardening_needed",
            ],
        }
    )

    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["next_work_unit"]["lane"] == "controller"
    assert (
        result["next_work_unit"]["summary"]
        == "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets."
    )
    assert result["specificity_questions"] == [
        "Which exact claim, figure, table, metric, citation, evidence row, or package artifact is blocking the gate?",
        "Which durable source path proves the blocker and which controller surface should own the repair?",
    ]


def test_mixed_generic_publication_blockers_require_specificity_before_analysis_dispatch() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "status": "blocked",
            "blockers": [
                "medical_publication_surface_blocked",
                "claim_evidence_consistency_failed",
                "reviewer_first_concerns_unresolved",
            ],
        }
    )

    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["next_work_unit"]["lane"] == "controller"
    assert (
        result["next_work_unit"]["summary"]
        == "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets."
    )
    assert "analysis_claim_evidence_repair" not in [
        unit["unit_id"] for unit in result["blocking_work_units"]
    ]
