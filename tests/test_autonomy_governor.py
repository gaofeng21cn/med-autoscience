from __future__ import annotations

import importlib


def test_governor_blocks_external_runtime_failure_before_mas_work() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_governor")

    decision = module.build_autonomy_governor_decision(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "autonomy_slo": {
                "runtime_failure_classification": {
                    "diagnosis_code": "codex_upstream_quota_error",
                    "blocker_class": "external_provider_account_blocker",
                    "action_mode": "external_fix_required",
                    "auto_recovery_allowed": False,
                    "external_blocker": True,
                },
                "slo_execution_plan": {
                    "state": "blocked_by_external_runtime",
                    "steps": [
                        {
                            "action_type": "external_runtime_blocker",
                            "controller_surface": "runtime_watch",
                            "apply_mode": "human_required",
                        }
                    ],
                    "gate_relaxation_allowed": False,
                },
                "quality_constraint": {"gate_relaxation_allowed": False},
            },
            "study_soak_replay_case": {
                "case_family": "runtime_recovery_taxonomy",
                "required_truth_surfaces": ["study_runtime_status", "runtime_watch"],
            },
        }
    )

    assert decision["surface"] == "mas_autonomy_governor"
    assert decision["governor_state"] == "blocked_external_runtime"
    assert decision["execution_permission"] == {
        "auto_dispatch_allowed": False,
        "requires_human_or_external_fix": True,
        "gate_relaxation_allowed": False,
        "paper_body_edit_allowed": False,
    }
    assert decision["owner_boundary"] == {
        "product_owner": "MedAutoScience",
        "runtime_backend": "MedDeepScientist",
        "mds_role": "migration_runtime_oracle_only",
    }
    assert decision["next_control_action"]["action_type"] == "external_runtime_blocker"
    assert decision["operator_answer"] == {
        "what_is_blocking": "external_provider_account_blocker",
        "who_owns_next_step": "external_runtime_or_human",
        "can_mas_continue_automatically": False,
    }


def test_governor_allows_quality_preserving_fast_lane_dispatch() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_governor")

    decision = module.build_autonomy_governor_decision(
        {
            "study_id": "004-invasive-architecture",
            "quest_id": "quest-004",
            "autonomy_slo": {
                "runtime_failure_classification": {
                    "blocker_class": "none",
                    "action_mode": "continue_slo_policy",
                    "auto_recovery_allowed": True,
                },
                "slo_execution_plan": {
                    "state": "ready_for_controller_execution",
                    "steps": [
                        {
                            "action_type": "run_publication_work_unit",
                            "controller_surface": "gate_clearing_batch",
                            "apply_mode": "controller_only",
                            "next_work_unit_id": "create_submission_minimal_package",
                        }
                    ],
                    "gate_relaxation_allowed": False,
                },
                "quality_constraint": {
                    "gate_relaxation_allowed": False,
                    "must_preserve_authority_surfaces": [
                        "study_charter",
                        "evidence_ledger",
                        "review_ledger",
                        "publication_eval/latest.json",
                        "controller_decisions/latest.json",
                    ],
                },
            },
            "quality_ledger_enforcement": {
                "enforcement_state": "repairable_quality_gate",
                "fast_lane_allowed": True,
                "gate_relaxation_allowed": False,
            },
            "fast_lane_execution_manifest": {
                "manifest_state": "ready",
                "replay_required": True,
            },
            "study_soak_replay_case": {
                "case_family": "same_line_quality_gate_fast_lane",
                "required_truth_surfaces": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
        }
    )

    assert decision["governor_state"] == "dispatch_controller_fast_lane"
    assert decision["execution_permission"]["auto_dispatch_allowed"] is True
    assert decision["execution_permission"]["gate_relaxation_allowed"] is False
    assert decision["quality_floor"] == {
        "gate_relaxation_allowed": False,
        "authority_surfaces": [
            "study_charter",
            "evidence_ledger",
            "review_ledger",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
        ],
        "ledger_enforcement_state": "repairable_quality_gate",
    }
    assert decision["next_control_action"]["action_type"] == "run_publication_work_unit"
    assert decision["operator_answer"]["who_owns_next_step"] == "mas_controller"


def test_governor_routes_platform_protocol_failure_to_repo_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_governor")

    decision = module.build_autonomy_governor_decision(
        {
            "study_id": "003-dpcc",
            "autonomy_slo": {
                "runtime_failure_classification": {
                    "diagnosis_code": "provider_invalid_params",
                    "blocker_class": "platform_protocol_or_runner_bug",
                    "action_mode": "platform_repair_required",
                    "auto_recovery_allowed": False,
                },
                "slo_execution_plan": {
                    "state": "blocked_by_runtime_gate",
                    "steps": [{"action_type": "platform_runtime_repair", "apply_mode": "platform_repair"}],
                    "gate_relaxation_allowed": False,
                },
                "quality_constraint": {"gate_relaxation_allowed": False},
            },
        }
    )

    assert decision["governor_state"] == "blocked_platform_repair"
    assert decision["execution_permission"]["auto_dispatch_allowed"] is False
    assert decision["operator_answer"]["who_owns_next_step"] == "mas_mds_platform_repair"
