from __future__ import annotations

from tests.display_surface_materialization_cases.shared import *


def test_display_layout_qc_rejects_v2_participant_flow_with_legacy_summary_cards() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
            "layout_boxes": [
                {
                    "box_id": "participant_step_china",
                    "box_type": "main_step",
                    "x0": 0.10,
                    "y0": 0.70,
                    "x1": 0.40,
                    "y1": 0.82,
                },
                {
                    "box_id": "participant_step_nhanes",
                    "box_type": "main_step",
                    "x0": 0.10,
                    "y0": 0.50,
                    "x1": 0.40,
                    "y1": 0.62,
                },
                {
                    "box_id": "participant_endpoint_summary",
                    "box_type": "summary_panel",
                    "x0": 0.50,
                    "y0": 0.56,
                    "x1": 0.96,
                    "y1": 0.80,
                },
            ],
            "panel_boxes": [
                {
                    "box_id": "participant_flow_main",
                    "box_type": "subfigure_panel",
                    "x0": 0.06,
                    "y0": 0.42,
                    "x1": 0.98,
                    "y1": 0.86,
                }
            ],
            "guide_boxes": [
                {
                    "box_id": "flow_spine_china_to_nhanes",
                    "box_type": "flow_connector",
                    "x0": 0.40,
                    "y0": 0.62,
                    "x1": 0.42,
                    "y1": 0.70,
                }
            ],
            "metrics": {
                "layout_mode": "participant_flow",
                "layout_generation": "scholarskills_cohort_flow_v2",
                "flow_visual_policy": "purpose_first_reporting_flow_no_legacy_card_shell",
                "steps": [{"step_id": "china"}, {"step_id": "nhanes"}],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_china",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74,
                        "rendered_width_pt": 260,
                        "padding_pt": 10,
                    },
                    {
                        "box_id": "participant_step_nhanes",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74,
                        "rendered_width_pt": 260,
                        "padding_pt": 10,
                    },
                    {
                        "box_id": "participant_endpoint_summary",
                        "box_type": "summary_panel",
                        "line_count": 3,
                        "max_line_chars": 30,
                        "rendered_height_pt": 96,
                        "rendered_width_pt": 210,
                        "padding_pt": 9,
                    },
                ],
            },
        },
    )

    rule_ids = {issue["rule_id"] for issue in result["issues"]}
    assert result["status"] == "fail"
    assert "participant_flow_legacy_summary_panel_shell" in rule_ids
    assert "participant_flow_content_horizontally_compressed" in rule_ids
