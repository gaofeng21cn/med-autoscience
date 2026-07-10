from __future__ import annotations

from tests.test_gate_clearing_batch_cases.shared import _write_json, importlib


def test_stale_time_to_event_grouped_payload_candidates_detects_registry_display_id_drift(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch.display_refresh")
    paper_root = tmp_path / "paper"
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                }
            ],
        },
    )
    _write_json(
        paper_root / "time_to_event_grouped_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [
                {
                    "display_id": "grouped_calibration",
                    "template_id": "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
                    "risk_group_summaries": [
                        {
                            "label": "NHANES D1",
                            "sample_size": 566,
                            "events_5y": 13,
                            "mean_predicted_risk_5y": 0.016,
                            "observed_km_risk_5y": 0.023,
                        }
                    ],
                }
            ],
        },
    )

    payload_path, candidate_ids, expected_template_id = module.stale_time_to_event_grouped_payload_candidates(
        paper_root=paper_root,
        display_surface_materialization_controller=object(),
    )

    assert payload_path == paper_root / "time_to_event_grouped_inputs.json"
    assert candidate_ids == ["km_risk_stratification"]
    assert expected_template_id == "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
