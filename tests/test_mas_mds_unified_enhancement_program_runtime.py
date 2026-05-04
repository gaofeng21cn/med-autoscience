from __future__ import annotations

import importlib


def test_unified_enhancement_program_board_materializes_lanes_mapping_and_absorb_order() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_unified_enhancement_program")

    board = module.build_unified_enhancement_program_board()

    assert board["surface"] == "mas_mds_unified_enhancement_program_board"
    assert board["program_id"] == "mas_mds_unified_enhancement_program"
    assert board["status_summary"] == {
        "lane_count": 5,
        "recommendation_count": 15,
        "completed_or_absorbed_count": 0,
        "blocked_count": 0,
        "usable_target_ready": False,
    }
    assert [lane["lane_id"] for lane in board["lanes"]] == [
        "L1_real_workspace_longitudinal_soak",
        "L2_pi_action_projection",
        "L3_outcome_calibration_and_provider_ops",
        "L4_delivery_and_legacy_upgrade_visibility",
        "L5_natural_boundary_and_audit_compaction",
    ]
    assert [item["lane_id"] for item in board["absorb_plan"]] == [
        "L1_real_workspace_longitudinal_soak",
        "L2_pi_action_projection",
        "L3_outcome_calibration_and_provider_ops",
        "L4_delivery_and_legacy_upgrade_visibility",
        "L5_natural_boundary_and_audit_compaction",
    ]
    assert [item["branch"] for item in board["parallel_worktree_landing"]] == [
        "codex/mas-soak-matrix-read-model",
        "codex/mas-pi-action-projection",
        "codex/mas-calibration-provider-ops",
        "codex/mas-delivery-legacy-visibility",
        "codex/mas-structure-audit-compaction",
    ]
    assert {item["basis_id"] for item in board["engineering_basis"]} == {
        "strangler_fig",
        "architecture_fitness_functions",
        "team_topologies_cognitive_load",
        "sre_toil_elimination_and_observability",
        "owner_private_truth_surfaces",
    }
    assert {item["recommendation_id"] for item in board["recommendation_mapping"]} == {
        "automatic_research_1",
        "automatic_research_2",
        "automatic_research_3",
        "automatic_research_4",
        "automatic_research_5",
        "automatic_research_6",
        "file_management_1",
        "file_management_2",
        "file_management_3",
        "file_management_4",
        "file_management_5",
        "control_plane_1",
        "control_plane_2",
        "control_plane_3",
        "control_plane_4",
    }
    assert module.validate_unified_enhancement_program_board(board)["ok"] is True


def test_unified_enhancement_program_board_accepts_progress_and_reports_usable_target() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_unified_enhancement_program")
    board = module.build_unified_enhancement_program_board(
        {
            "lane_progress": {
                "L1_real_workspace_longitudinal_soak": {"status": "absorbed", "commit": "c1"},
                "L2_pi_action_projection": {"status": "absorbed", "commit": "c2"},
                "L3_outcome_calibration_and_provider_ops": {"status": "absorbed", "commit": "c3"},
                "L4_delivery_and_legacy_upgrade_visibility": {"status": "absorbed", "commit": "c4"},
                "L5_natural_boundary_and_audit_compaction": {"status": "absorbed", "commit": "c5"},
            }
        }
    )

    assert board["status_summary"]["completed_or_absorbed_count"] == 5
    assert board["status_summary"]["usable_target_ready"] is True
    assert all(lane["blocks_usable_target"] is False for lane in board["lanes"])


def test_unified_enhancement_program_validation_fails_closed_on_missing_lane_or_recommendation() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_unified_enhancement_program")
    board = module.build_unified_enhancement_program_board()
    board["lanes"] = board["lanes"][:-1]
    board["recommendation_mapping"] = board["recommendation_mapping"][:-1]

    validation = module.validate_unified_enhancement_program_board(board)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "missing_lane",
        "missing_recommendation",
    }


def test_unified_enhancement_program_validation_rejects_projection_authority_and_unsafe_l5_compaction() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_unified_enhancement_program")
    board = module.build_unified_enhancement_program_board()
    board["lanes"][1]["authority_mode"] = "authority"
    board["lanes"][4]["compaction_gates"] = ["restore", "index"]

    validation = module.validate_unified_enhancement_program_board(board)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "projection_lane_claims_authority",
        "l5_missing_compaction_gate",
    }
