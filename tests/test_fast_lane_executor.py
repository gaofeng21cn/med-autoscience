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


def _dependent_repair_units() -> list[GateClearingRepairUnit]:
    return [
        GateClearingRepairUnit(
            unit_id="repair_paper_live_paths",
            label="Repair runtime-owned paper live paths",
            parallel_safe=True,
            run=lambda: {"status": "updated"},
        ),
        GateClearingRepairUnit(
            unit_id="workspace_display_repair_script",
            label="Run workspace-authored display repair script",
            parallel_safe=True,
            depends_on=("repair_paper_live_paths",),
            run=lambda: {"status": "updated"},
        ),
        GateClearingRepairUnit(
            unit_id="create_submission_minimal_package",
            label="Regenerate submission-minimal assets",
            parallel_safe=False,
            depends_on=("workspace_display_repair_script",),
            run=lambda: {"status": "ready"},
        ),
    ]


def _quality_ledger_enforcement(*, allowed: bool = True) -> dict[str, object]:
    return {
        "surface": "quality_gate_ledger_enforcement",
        "fast_lane_execution_allowed": allowed,
        "fast_lane_execution_state": "repairable" if allowed else "blocked",
        "gate_relaxation_allowed": False,
        "repairable_blockers": ["publication_eval_must_fix_gap"] if allowed else [],
        "hard_blockers": [] if allowed else ["review_ledger_charter_expectation_not_closed"],
    }


def _replay_case() -> dict[str, object]:
    return {
        "case_id": "study-soak-replay::004-invasive-architecture::same_line_quality_gate_fast_lane",
        "case_family": "same_line_quality_gate_fast_lane",
        "required_truth_surfaces": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "artifacts/controller/gate_clearing_batch/latest.json",
        ],
        "gate_relaxation_allowed": False,
        "edits_paper_body": False,
    }


def test_fast_lane_manifest_requires_quality_enforcement_and_replay() -> None:
    module = importlib.import_module("med_autoscience.controllers.fast_lane_executor")

    manifest = module.build_fast_lane_execution_manifest(
        study_id="004-invasive-architecture",
        quest_id="quest-004",
        repair_units=_repair_units(),
        quality_ledger_enforcement=_quality_ledger_enforcement(),
        replay_case=_replay_case(),
    )

    assert manifest["surface"] == "fast_lane_execution_manifest"
    assert manifest["manifest_type"] == "gate_clearing_fast_lane_execution"
    assert manifest["schema_version"] == 2
    assert manifest["manifest_state"] == "ready"
    assert manifest["gate_relaxation_allowed"] is False
    assert manifest["paper_body_edit_allowed"] is False
    assert manifest["idempotency_scope"] == "study_quest_work_unit_dag"
    assert manifest["idempotency_key"].startswith("fast-lane::sha256:")
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
    assert manifest["quality_gate_policy"] == {
        "mode": "quality_preserving_fast_lane",
        "gate_relaxation_allowed": False,
        "requires_publication_gate_replay": True,
        "requires_authority_surface_refresh": True,
        "requires_successful_replay_before_completion": True,
    }
    assert manifest["fast_lane_v2_contract"]["allowed_work_unit_classes"] == [
        "authority_surface_refresh",
        "ledger_closure_repair",
        "reporting_guideline_checklist_repair",
        "display_or_package_manifest_repair",
        "publication_gate_replay",
        "controller_decision_recording",
    ]
    assert manifest["fast_lane_v2_contract"]["forbidden_scientific_changes"] == [
        "primary_question_change",
        "primary_endpoint_change",
        "new_primary_claim",
        "cohort_boundary_redefinition",
        "statistical_method_replacement",
        "unreviewed_subgroup_or_sensitivity_analysis",
        "paper_body_claim_rewrite",
        "quality_gate_relaxation",
    ]
    assert manifest["fast_lane_v2_contract"]["rollback_requirements"] == {
        "checkpoint_before_each_action_batch": True,
        "rollback_on_failed_replay": True,
        "rollback_on_quality_gate_regression": True,
        "rollback_scope": "touched_authority_surfaces_and_generated_package_assets",
    }
    assert manifest["fast_lane_v2_contract"]["refingerprint_requirements"] == {
        "before_execute": True,
        "after_each_action_batch": True,
        "after_replay": True,
        "fingerprint_scope": [
            "study_charter",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "artifacts/publication_eval/latest.json",
            "reporting_guideline_checklist.json",
            "submission_package_assets",
        ],
    }
    assert manifest["fast_lane_v2_contract"]["completion_claim_policy"] == {
        "mechanical_repair_complete_equals_scientific_quality_complete": False,
        "mechanical_repair_completion_claim": "mechanical_work_units_complete",
        "scientific_quality_completion_claim": "scientific_quality_complete_after_quality_gates_replayed_and_closed",
        "requires_closed_surfaces": [
            "study_charter.paper_quality_contract",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "artifacts/publication_eval/latest.json",
            "reporting_guideline_checklist.json",
        ],
        "requires_successful_publication_gate_replay": True,
        "allows_completion_claim_without_review_ledger": False,
    }
    assert manifest["replay_requirements"] == {
        "publication_gate_replay_required": True,
        "controller_apply_required": True,
        "replay_after_action_batches": True,
        "quality_gate_relaxation_allowed": False,
    }


def test_fast_lane_manifest_records_dependency_dag_idempotency_and_durable_checkpoints() -> None:
    module = importlib.import_module("med_autoscience.controllers.fast_lane_executor")

    manifest = module.build_fast_lane_execution_manifest(
        study_id="004-invasive-architecture",
        quest_id="quest-004",
        repair_units=_dependent_repair_units(),
        quality_ledger_enforcement=_quality_ledger_enforcement(),
        replay_case=_replay_case(),
    )
    rebuilt_manifest = module.build_fast_lane_execution_manifest(
        study_id="004-invasive-architecture",
        quest_id="quest-004",
        repair_units=_dependent_repair_units(),
        quality_ledger_enforcement=_quality_ledger_enforcement(),
        replay_case=_replay_case(),
    )

    assert manifest["idempotency_key"] == rebuilt_manifest["idempotency_key"]
    assert manifest["durable_checkpoint_requirements"] == {
        "before_execute": [
            "publication_eval/latest.json",
            "gate_report",
            "latest_gate_clearing_batch",
        ],
        "after_each_action_batch": [
            "unit_results",
            "unit_fingerprints",
            "batch_status",
        ],
        "after_replay": [
            "gate_replay_step",
            "publication_work_unit_lifecycle",
            "current_package_freshness_proof",
        ],
        "requires_durable_record": True,
    }
    assert manifest["dependency_dag"]["edges"] == [
        {
            "from_unit_id": "repair_paper_live_paths",
            "to_unit_id": "workspace_display_repair_script",
        },
        {
            "from_unit_id": "workspace_display_repair_script",
            "to_unit_id": "create_submission_minimal_package",
        },
    ]
    assert manifest["action_batches"] == [
        {
            "batch_index": 1,
            "dispatch_mode": "parallel",
            "unit_ids": ["repair_paper_live_paths"],
            "depends_on_batch_indices": [],
            "unit_idempotency_keys": {
                "repair_paper_live_paths": manifest["dependency_dag"]["nodes"][0]["idempotency_key"],
            },
            "quality_gate_relaxation_allowed": False,
            "idempotency_key": manifest["action_batches"][0]["idempotency_key"],
        },
        {
            "batch_index": 2,
            "dispatch_mode": "parallel",
            "unit_ids": ["workspace_display_repair_script"],
            "depends_on_batch_indices": [1],
            "unit_idempotency_keys": {
                "workspace_display_repair_script": manifest["dependency_dag"]["nodes"][1]["idempotency_key"],
            },
            "quality_gate_relaxation_allowed": False,
            "idempotency_key": manifest["action_batches"][1]["idempotency_key"],
        },
        {
            "batch_index": 3,
            "dispatch_mode": "sequential",
            "unit_ids": ["create_submission_minimal_package"],
            "depends_on_batch_indices": [2],
            "unit_idempotency_keys": {
                "create_submission_minimal_package": manifest["dependency_dag"]["nodes"][2]["idempotency_key"],
            },
            "quality_gate_relaxation_allowed": False,
            "idempotency_key": manifest["action_batches"][2]["idempotency_key"],
        },
    ]


def test_scheduler_embeds_fast_lane_manifest_in_repair_unit_execution_plan() -> None:
    scheduler = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_scheduler")

    execution_plan = scheduler.build_repair_unit_execution_plan(_dependent_repair_units())
    manifest = execution_plan["fast_lane_execution_manifest"]

    assert manifest["status"] == "planned"
    assert manifest["quality_gate_policy"]["gate_relaxation_allowed"] is False
    assert manifest["dependency_dag"]["edges"] == [
        {
            "from_unit_id": "repair_paper_live_paths",
            "to_unit_id": "workspace_display_repair_script",
        },
        {
            "from_unit_id": "workspace_display_repair_script",
            "to_unit_id": "create_submission_minimal_package",
        },
    ]
    assert manifest["action_batches"][0]["quality_gate_relaxation_allowed"] is False
    assert manifest["replay_requirements"]["publication_gate_replay_required"] is True


def test_fast_lane_manifest_blocks_when_quality_enforcer_blocks() -> None:
    module = importlib.import_module("med_autoscience.controllers.fast_lane_executor")

    manifest = module.build_fast_lane_execution_manifest(
        study_id="003-dpcc",
        quest_id="quest-003",
        repair_units=_repair_units(),
        quality_ledger_enforcement=_quality_ledger_enforcement(allowed=False),
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
