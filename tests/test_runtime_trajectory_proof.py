from __future__ import annotations

import importlib


def test_action_observation_trajectory_steps_have_fixed_read_model_fields() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_trajectory_proof")

    proof = module.build_runtime_trajectory_proof(
        active_run_id="run-trajectory-001",
        steps=[
            {
                "step_id": "step-001",
                "action_type": "tool_call",
                "action_ref": "runtime/events/step-001/action.json",
                "observation_ref": "runtime/events/step-001/observation.json",
                "artifact_delta_refs": ["paper/results/table1.json"],
                "side_effect_class": "artifact_write",
                "idempotency_key": "study-001:step-001:table1",
                "replay_policy": "idempotent_replay_allowed",
                "status": "observed",
            }
        ],
    )

    assert proof["surface"] == "action_observation_trajectory"
    assert proof["schema_version"] == 1
    assert proof["active_run_id"] == "run-trajectory-001"
    assert proof["trajectory_role"] == {
        "read_model_only": True,
        "can_be_study_truth_owner": False,
        "can_be_publication_quality_owner": False,
        "truth_authority_surface": "StudyTruthKernel",
        "publication_quality_authority_surface": "publication_eval/latest.json",
    }
    assert proof["steps"] == [
        {
            "step_id": "step-001",
            "active_run_id": "run-trajectory-001",
            "action_type": "tool_call",
            "action_ref": "runtime/events/step-001/action.json",
            "observation_ref": "runtime/events/step-001/observation.json",
            "artifact_delta_refs": ["paper/results/table1.json"],
            "side_effect_class": "artifact_write",
            "idempotency_key": "study-001:step-001:table1",
            "replay_policy": "idempotent_replay_allowed",
            "status": "observed",
        }
    ]


def test_side_effect_action_without_idempotency_key_is_non_replayable() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_trajectory_proof")

    proof = module.build_runtime_trajectory_proof(
        active_run_id="run-trajectory-002",
        steps=[
            {
                "step_id": "step-unsafe",
                "action_type": "shell_exec",
                "action_ref": "runtime/events/step-unsafe/action.json",
                "observation_ref": "runtime/events/step-unsafe/observation.json",
                "artifact_delta_refs": ["paper/manuscript.md"],
                "side_effect_class": "workspace_write",
                "replay_policy": "auto_replay_allowed",
                "status": "observed",
            }
        ],
    )

    assert proof["steps"][0]["idempotency_key"] is None
    assert proof["steps"][0]["replay_policy"] == "non_replayable"
    assert proof["replay_summary"] == {
        "auto_replayable_step_count": 0,
        "non_replayable_step_count": 1,
        "blocked_replay_reasons": [
            {
                "step_id": "step-unsafe",
                "code": "side_effect_missing_idempotency_key",
            }
        ],
    }


def test_read_only_actions_without_idempotency_key_remain_non_mutating_observations() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_trajectory_proof")

    proof = module.build_runtime_trajectory_proof(
        active_run_id="run-trajectory-003",
        steps=[
            {
                "step_id": "step-read",
                "action_type": "read_file",
                "action_ref": "runtime/events/step-read/action.json",
                "observation_ref": "runtime/events/step-read/observation.json",
                "side_effect_class": "none",
                "status": "observed",
            }
        ],
    )

    assert proof["steps"][0] == {
        "step_id": "step-read",
        "active_run_id": "run-trajectory-003",
        "action_type": "read_file",
        "action_ref": "runtime/events/step-read/action.json",
        "observation_ref": "runtime/events/step-read/observation.json",
        "artifact_delta_refs": [],
        "side_effect_class": "none",
        "idempotency_key": None,
        "replay_policy": "observation_only",
        "status": "observed",
    }
    assert proof["replay_summary"]["auto_replayable_step_count"] == 0
    assert proof["replay_summary"]["non_replayable_step_count"] == 0


def test_validator_rejects_truth_or_quality_authority_overreach() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_trajectory_proof")
    proof = module.build_runtime_trajectory_proof(
        active_run_id="run-trajectory-004",
        steps=[],
    )
    proof["trajectory_role"]["can_be_study_truth_owner"] = True
    proof["trajectory_role"]["can_be_publication_quality_owner"] = True

    validation = module.validate_runtime_trajectory_proof(proof)

    assert validation["ok"] is False
    assert validation["issues"] == [
        {"code": "trajectory_claims_study_truth_authority"},
        {"code": "trajectory_claims_publication_quality_authority"},
    ]


def test_authority_surface_delta_refs_are_non_replayable_even_with_idempotency_key() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_trajectory_proof")

    proof = module.build_runtime_trajectory_proof(
        active_run_id="run-trajectory-005",
        steps=[
            {
                "step_id": "step-authority-surface",
                "action_type": "artifact_write",
                "action_ref": "runtime/events/step-authority-surface/action.json",
                "observation_ref": "runtime/events/step-authority-surface/observation.json",
                "artifact_delta_refs": [
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                    "progress_projection",
                    "study_truth",
                    "submission_minimal/readiness",
                ],
                "side_effect_class": "artifact_write",
                "idempotency_key": "study-001:step-authority-surface",
                "replay_policy": "auto_replay_allowed",
                "status": "observed",
            }
        ],
    )

    assert proof["authority_guard"] == {
        "role": "observability_only",
        "authority_surface_replay_policy": "non_replayable",
        "guarded_refs": [
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
            "progress_projection",
            "study_truth",
            "submission readiness",
        ],
    }
    assert proof["steps"][0]["replay_policy"] == "non_replayable"
    assert proof["replay_summary"] == {
        "auto_replayable_step_count": 0,
        "non_replayable_step_count": 1,
        "blocked_replay_reasons": [
            {
                "step_id": "step-authority-surface",
                "code": "authority_surface_replay_blocked",
            }
        ],
    }
