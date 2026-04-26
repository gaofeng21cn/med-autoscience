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
