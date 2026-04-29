from __future__ import annotations

import importlib


def test_blocked_claim_evidence_route_produces_analysis_campaign_work_unit() -> None:
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
            "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
        }
    )

    assert result["fingerprint"].startswith("publication-blockers::")
    assert result["next_work_unit"] == {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
    }
    assert [unit["unit_id"] for unit in result["blocking_work_units"]] == [
        "analysis_claim_evidence_repair",
        "manuscript_story_repair",
        "figure_results_trace_repair",
    ]


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


def test_analysis_work_unit_fingerprint_ignores_downstream_delivery_blocker_churn() -> None:
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

    assert with_delivery_churn["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert with_delivery_churn["fingerprint"] == claim_only["fingerprint"]
    assert with_delivery_churn["fingerprint_blockers"] == ["claim_evidence_consistency_failed"]


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
    assert result["next_work_unit"] == {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets.",
    }
    assert result["specificity_questions"] == [
        "Which exact claim, figure, table, metric, citation, evidence row, or package artifact is blocking the gate?",
        "Which durable source path proves the blocker and which controller surface should own the repair?",
    ]
