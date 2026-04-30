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
        "P7_incident_learning_loop",
    ]
    assert board["status_summary"] == {
        "lane_count": 8,
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
                    "P7_incident_learning_loop",
                ),
                start=1,
            )
        }
    }

    board = module.build_program_board(progress)

    assert board["status_summary"]["completed_or_absorbed_count"] == 8
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


def test_program_board_freezes_one_shot_learning_rules_and_parallel_lanes() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_operating_system_program")

    board = module.build_program_board()
    learning = board["learning_program"]

    assert learning["mode"] == "one_shot_long_line_learning_and_landing"
    assert learning["decision_types"] == ["adopt_contract", "adopt_template", "watch_only", "reject"]
    assert learning["external_scheduler_owner_allowed"] is False
    assert learning["generic_persona_library_allowed"] is False
    assert learning["quality_gate_relaxation_allowed"] is False
    assert "mark_saturated_when_mas_equivalent_contract_exists" in learning["stop_rules"]
    assert "new_source_must_change_runtime_controller_eval_hygiene_operator_projection_or_tests" in learning["stop_rules"]
    assert [lane["branch"] for lane in learning["parallel_landing_lanes"]] == [
        "codex/mas-program-board-one-shot",
        "codex/mas-work-unit-runtime-registry",
        "codex/mas-medical-quality-os",
        "codex/mas-learning-incident-loop",
        "codex/mas-product-truth-projection",
    ]
    assert {item["source_family"] for item in learning["source_taxonomy"]} == {
        "orchestration_systems",
        "research_agent_systems",
        "evaluation_systems",
        "safety_runtime_systems",
        "product_ops_systems",
    }
