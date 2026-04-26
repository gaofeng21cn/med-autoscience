from __future__ import annotations

import importlib

from med_autoscience.controllers.gate_clearing_batch_execution import GateClearingRepairUnit


def _repair_units() -> list[GateClearingRepairUnit]:
    return [
        GateClearingRepairUnit(
            unit_id="repair_paper_live_paths",
            label="repair paper live paths",
            parallel_safe=True,
            run=lambda: {"status": "updated"},
        ),
        GateClearingRepairUnit(
            unit_id="create_submission_minimal_package",
            label="create submission minimal package",
            parallel_safe=False,
            depends_on=("repair_paper_live_paths",),
            run=lambda: {"status": "ready"},
        ),
    ]


def test_fast_lane_manifest_requires_quality_enforcement_and_replay() -> None:
    module = importlib.import_module("med_autoscience.controllers.fast_lane_executor")

    manifest = module.build_fast_lane_execution_manifest(
        study_id="004-invasive-architecture",
        quest_id="quest-004",
        repair_units=_repair_units(),
        quality_ledger_enforcement={
            "surface": "quality_gate_ledger_enforcement",
            "fast_lane_execution_allowed": True,
            "fast_lane_execution_state": "repairable",
            "gate_relaxation_allowed": False,
            "repairable_blockers": ["publication_eval_must_fix_gap"],
            "hard_blockers": [],
        },
        replay_case={
            "case_id": "study-soak-replay::004-invasive-architecture::same_line_quality_gate_fast_lane",
            "case_family": "same_line_quality_gate_fast_lane",
            "required_truth_surfaces": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "gate_relaxation_allowed": False,
            "edits_paper_body": False,
        },
    )

    assert manifest["surface"] == "fast_lane_execution_manifest"
    assert manifest["manifest_state"] == "ready"
    assert manifest["gate_relaxation_allowed"] is False
    assert manifest["paper_body_edit_allowed"] is False
    assert manifest["idempotency_scope"] == "study_quest_work_unit_dag"
    assert manifest["execution_plan"]["status"] == "planned"
    assert manifest["execution_plan"]["dispatch_batches"] == [
        {
            "batch_index": 1,
            "dispatch_mode": "parallel",
            "unit_ids": ["repair_paper_live_paths"],
            "quality_gate_relaxation_allowed": False,
        },
        {
            "batch_index": 2,
            "dispatch_mode": "sequential",
            "unit_ids": ["create_submission_minimal_package"],
            "quality_gate_relaxation_allowed": False,
        },
    ]
    assert manifest["checkpoint_requirements"] == {
        "write_gate_clearing_batch_record": True,
        "replay_publication_gate": True,
        "refresh_authority_surfaces": True,
        "record_controller_decision": True,
    }
    assert manifest["replay_contract"]["case_family"] == "same_line_quality_gate_fast_lane"
    assert manifest["quality_enforcement"]["fast_lane_execution_state"] == "repairable"


def test_fast_lane_manifest_blocks_when_quality_enforcer_blocks() -> None:
    module = importlib.import_module("med_autoscience.controllers.fast_lane_executor")

    manifest = module.build_fast_lane_execution_manifest(
        study_id="003-dpcc",
        quest_id="quest-003",
        repair_units=_repair_units(),
        quality_ledger_enforcement={
            "fast_lane_execution_allowed": False,
            "fast_lane_execution_state": "blocked",
            "gate_relaxation_allowed": False,
            "hard_blockers": ["review_ledger_charter_expectation_not_closed"],
            "repairable_blockers": [],
        },
        replay_case={},
    )

    assert manifest["manifest_state"] == "blocked_by_quality_ledger"
    assert manifest["execution_permission"]["auto_dispatch_allowed"] is False
    assert manifest["blocking_reasons"] == ["review_ledger_charter_expectation_not_closed"]


def test_fast_lane_manifest_blocks_gate_relaxation_even_if_allowed_flag_is_true() -> None:
    module = importlib.import_module("med_autoscience.controllers.fast_lane_executor")

    manifest = module.build_fast_lane_execution_manifest(
        study_id="bad-relaxation",
        quest_id="quest-bad",
        repair_units=_repair_units(),
        quality_ledger_enforcement={
            "fast_lane_execution_allowed": True,
            "fast_lane_execution_state": "repairable",
            "gate_relaxation_allowed": True,
            "hard_blockers": [],
            "repairable_blockers": ["publication_eval_must_fix_gap"],
        },
        replay_case={},
    )

    assert manifest["manifest_state"] == "blocked_by_quality_ledger"
    assert manifest["gate_relaxation_allowed"] is False
    assert "quality_gate_relaxation_requested" in manifest["blocking_reasons"]
