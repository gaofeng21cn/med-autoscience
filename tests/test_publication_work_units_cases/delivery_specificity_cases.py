from __future__ import annotations

import importlib


def _delivery_specificity_targets() -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": "/tmp/study/paper/claim_evidence_map.json",
            "blocking_reason": "stale_submission_minimal_authority",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": "/tmp/study/paper/figures/figure_catalog.json",
            "blocking_reason": "stale_submission_minimal_authority",
        },
        {
            "target_kind": "table",
            "target_id": "submission_minimal_authority",
            "source_path": "/tmp/study/paper/submission_minimal/submission_manifest.json",
            "blocking_reason": "stale_submission_minimal_authority",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": "/tmp/quest/artifacts/results/main_result.json",
            "blocking_reason": "stale_submission_minimal_authority",
        },
        {
            "target_kind": "source_path",
            "target_id": "publication_gate_source_path",
            "source_path": "/tmp/quest/artifacts/reports/medical_publication_surface/latest.json",
            "blocking_reason": "stale_submission_minimal_authority",
        },
    ]


def test_delivery_specificity_targets_do_not_route_to_analysis_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "blockers": [
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
        },
        specificity_targets=_delivery_specificity_targets(),
    )

    work_unit_ids = [unit["unit_id"] for unit in result["blocking_work_units"]]
    assert result["next_work_unit"]["unit_id"] == "submission_minimal_refresh"
    assert "analysis_claim_evidence_repair" not in work_unit_ids
    assert "figure_results_trace_repair" not in work_unit_ids


def test_delivery_specificity_targets_do_not_close_generic_publication_surface_specificity() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(
        {
            "blockers": [
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
        },
        specificity_targets=_delivery_specificity_targets(),
    )

    work_unit_ids = [unit["unit_id"] for unit in result["blocking_work_units"]]
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert "analysis_claim_evidence_repair" not in work_unit_ids
    assert "figure_results_trace_repair" not in work_unit_ids
