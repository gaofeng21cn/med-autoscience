from __future__ import annotations

import importlib


def test_program_board_freezes_eight_lanes_and_owner_boundary() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_operating_system_program")

    board = module.build_program_board()

    assert board["surface"] == "mas_mds_autonomy_operating_system_program"
    assert board["target_state"] == {
        "product_owner": "MedAutoScience",
        "runtime_backend": "MedDeepScientist",
        "mds_role": "controlled_backend_behavior_oracle_upstream_intake_buffer",
        "physical_monorepo_absorb": "post_gate_only",
    }
    assert [lane["lane_id"] for lane in board["lanes"]] == [
        "P0_baseline_freeze",
        "P1_autonomy_reliability_core",
        "P2_observability_and_profiling",
        "P3_medical_quality_os",
        "P4_quality_preserving_fast_lane",
        "P5_mas_mds_strangler_program",
        "P6_natural_boundary_refactor",
        "P7_delivery_metrics_and_forecasting",
        "P8_autonomy_incident_learning_loop",
    ]
    assert board["status_summary"] == {
        "lane_count": 9,
        "completed_or_absorbed_count": 0,
        "blocked_count": 0,
        "ready_for_program_release": False,
    }
    assert "study_charter" in board["quality_authority_surfaces"]
    assert "artifacts/publication_eval/latest.json" in board["quality_authority_surfaces"]
    assert "study_runtime_status" in board["runtime_truth_surfaces"]


def test_program_board_accepts_lane_progress_and_only_releases_when_all_absorbed() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_operating_system_program")
    progress = {
        "lane_progress": {
            lane_id: {
                "status": "absorbed",
                "commit": f"commit-{index}",
                "verification": ["targeted pytest"],
            }
            for index, lane_id in enumerate(
                (
                    "P0_baseline_freeze",
                    "P1_autonomy_reliability_core",
                    "P2_observability_and_profiling",
                    "P3_medical_quality_os",
                    "P4_quality_preserving_fast_lane",
                    "P5_mas_mds_strangler_program",
                    "P6_natural_boundary_refactor",
                    "P7_delivery_metrics_and_forecasting",
                    "P8_autonomy_incident_learning_loop",
                ),
                start=1,
            )
        }
    }

    board = module.build_program_board(progress)

    assert board["status_summary"]["completed_or_absorbed_count"] == 9
    assert board["status_summary"]["ready_for_program_release"] is True
    assert all(lane["blocks_release"] is False for lane in board["lanes"])


def test_program_board_validation_fails_closed_on_owner_or_quality_surface_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_operating_system_program")
    board = module.build_program_board()
    board["target_state"]["product_owner"] = "MedDeepScientist"
    board["quality_authority_surfaces"] = ["study_charter"]
    board["lanes"][0]["primary_surfaces"] = []

    validation = module.validate_program_board(board)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "wrong_product_owner",
        "missing_quality_authority_surface",
        "lane_missing_primary_surfaces",
    }
