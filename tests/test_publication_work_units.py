from __future__ import annotations

import importlib


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
    assert result["next_work_unit"] == {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets.",
    }
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"


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
    assert result["next_work_unit"] == {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets.",
    }
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
    assert result["next_work_unit"] == {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets.",
    }
    assert "analysis_claim_evidence_repair" not in [
        unit["unit_id"] for unit in result["blocking_work_units"]
    ]
