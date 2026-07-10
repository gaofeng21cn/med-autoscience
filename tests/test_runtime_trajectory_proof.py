from __future__ import annotations

import pytest

from med_autoscience.controllers.runtime_trajectory_proof import (
    build_runtime_trajectory_proof,
    validate_runtime_trajectory_proof,
)


@pytest.mark.parametrize(
    ("side_effect_class", "idempotency_key", "artifact_delta_refs", "expected_policy", "reason"),
    (
        ("none", None, [], "observation_only", None),
        ("workspace_write", None, ["paper/manuscript.md"], "non_replayable", "side_effect_missing_idempotency_key"),
        (
            "artifact_write",
            "study-001:publication-eval",
            ["artifacts/publication_eval/latest.json"],
            "non_replayable",
            "authority_surface_replay_blocked",
        ),
    ),
)
def test_runtime_trajectory_replay_policy_is_fail_closed(
    side_effect_class: str,
    idempotency_key: str | None,
    artifact_delta_refs: list[str],
    expected_policy: str,
    reason: str | None,
) -> None:
    proof = build_runtime_trajectory_proof(
        active_run_id="run-trajectory",
        steps=[
            {
                "step_id": "step-001",
                "action_type": "tool_call",
                "action_ref": "runtime/events/step-001/action.json",
                "observation_ref": "runtime/events/step-001/observation.json",
                "artifact_delta_refs": artifact_delta_refs,
                "side_effect_class": side_effect_class,
                "idempotency_key": idempotency_key,
                "replay_policy": "auto_replay_allowed",
                "status": "observed",
            }
        ],
    )

    assert proof["trajectory_role"] == {
        "read_model_only": True,
        "can_be_study_truth_owner": False,
        "can_be_publication_quality_owner": False,
        "truth_authority_surface": "StudyTruthKernel",
        "publication_quality_authority_surface": "publication_eval/latest.json",
    }
    step = proof["steps"][0]
    assert set(step) == set(
        "step_id active_run_id action_type action_ref observation_ref artifact_delta_refs "
        "side_effect_class idempotency_key replay_policy status".split()
    )
    assert step["active_run_id"] == "run-trajectory"
    assert step["replay_policy"] == expected_policy
    summary = proof["replay_summary"]
    assert summary["non_replayable_step_count"] == int(reason is not None)
    assert summary["blocked_replay_reasons"] == (
        [{"step_id": "step-001", "code": reason}] if reason else []
    )


def test_validator_rejects_truth_or_quality_authority_overreach() -> None:
    proof = build_runtime_trajectory_proof(active_run_id="run-trajectory", steps=[])
    proof["trajectory_role"]["can_be_study_truth_owner"] = True
    proof["trajectory_role"]["can_be_publication_quality_owner"] = True

    assert validate_runtime_trajectory_proof(proof) == {
        "ok": False,
        "issues": [
            {"code": "trajectory_claims_study_truth_authority"},
            {"code": "trajectory_claims_publication_quality_authority"},
        ],
    }
