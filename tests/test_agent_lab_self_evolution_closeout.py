from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from med_autoscience.authority_handlers.self_evolution_closeout import (
    evaluate_agent_lab_self_evolution_closeout,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "contracts/agent_lab_self_evolution_policy.json"


def _policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _receipt() -> dict:
    return {
        "surface_kind": "opl_work_order_codex_execution_receipt",
        "status": "executed_absorbed_and_cleaned",
        "work_order_id": "oma_developer_patch_work_order_test",
        "target_agent": {"domain_id": "med-autoscience"},
        "source_execution_receipt_ref": "receipt:opl/work-order/test",
        "patch": {"changed_files": ["contracts/agent_lab_handoff.json"]},
        "verification": {
            "all_passed": True,
            "required_verification_refs": ["tests:test-self-evolution"],
            "command_results": [{"exit_code": 0}],
        },
        "absorption": {"absorbed": True, "absorbed_head": "a" * 40},
        "cleanup": {"worktree_removed": True, "branch_removed": True},
        "no_forbidden_write_proof": {
            "proof_refs": ["no-forbidden-write:mas/test"],
            "can_write_target_domain_truth": False,
            "can_write_target_domain_memory_body": False,
            "can_mutate_target_domain_artifact_body": False,
            "can_authorize_target_domain_quality_or_export": False,
        },
        "agent_lab_re_evaluation": {
            "suite_result": {
                "result_id": "oals_fresh_test",
                "status": "blocked",
                "missing_observations": [],
                "observations": {
                    "domain_stage_completion_policies_observed": True,
                    "promotion_gates_observed": True,
                },
                "runs": [
                    {
                        "status": "blocked",
                        "failure_taxonomy": ["domain_scorecard_blocked"],
                        "scorecard": {"passed": False},
                        "stage_completion_policy_assessment": {
                            "status": "passed",
                            "blockers": [],
                        },
                        "promotion_safety_assessment": {
                            "safety_status": "owner_or_human_gate_required",
                            "missing_required_refs": [],
                            "automatic_mechanism_promotion_ready": False,
                        },
                    }
                ],
            }
        },
    }


def test_absorbed_verified_patch_returns_mechanism_only_domain_receipt() -> None:
    result = evaluate_agent_lab_self_evolution_closeout(_receipt(), _policy())

    assert result["return_shape"] == "domain_receipt"
    assert result["status"] == "mechanism_change_accepted"
    assert result["receipt_scope"] == "target_agent_mechanism_change_only"
    assert result["automatic_mechanism_promotion_ready"] is False
    assert result["authorizes_quality_or_export"] is False
    assert result["authorizes_publication_or_submission"] is False
    assert result["authorizes_domain_ready"] is False
    assert result["refs_only"] is True


def test_no_source_delta_returns_no_regression_waiver() -> None:
    receipt = _receipt()
    receipt["patch"]["changed_files"] = []

    result = evaluate_agent_lab_self_evolution_closeout(receipt, _policy())

    assert result["return_shape"] == "no_regression_evidence"
    assert result["status"] == "mechanism_change_waived"
    assert "no_regression_evidence_ref" in result


def test_missing_promotion_observation_returns_typed_blocker() -> None:
    receipt = _receipt()
    receipt["agent_lab_re_evaluation"]["suite_result"]["observations"][
        "promotion_gates_observed"
    ] = False

    result = evaluate_agent_lab_self_evolution_closeout(receipt, _policy())

    assert result["return_shape"] == "typed_blocker"
    assert result["status"] == "mechanism_change_blocked"
    assert (
        "fresh_observation_missing:promotion_gates_observed"
        in result["reason_codes"]
    )


def test_missing_worktree_cleanup_returns_typed_blocker() -> None:
    receipt = _receipt()
    receipt.pop("cleanup")

    result = evaluate_agent_lab_self_evolution_closeout(receipt, _policy())

    assert result["return_shape"] == "typed_blocker"
    assert "worktree_cleanup_incomplete" in result["reason_codes"]


def test_domain_scorecard_cannot_be_upgraded_by_mechanism_closeout() -> None:
    receipt = _receipt()
    receipt["agent_lab_re_evaluation"]["suite_result"]["runs"][0]["scorecard"][
        "passed"
    ] = True

    result = evaluate_agent_lab_self_evolution_closeout(receipt, _policy())

    assert result["return_shape"] == "typed_blocker"
    assert "domain_scorecard_boundary_not_preserved" in result["reason_codes"]


def test_cli_consumes_opl_receipt_draft_and_returns_allowed_shape() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "med_autoscience.authority_handlers.self_evolution_closeout",
        ],
        cwd=ROOT,
        input=json.dumps(_receipt()),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["return_shape"] == "domain_receipt"


def test_declarative_policy_is_sha_bound_to_canonical_stage_pack() -> None:
    policy = _policy()
    stage_projection = policy["stage_completion_policy_projection"]
    stage_pack = ROOT / "agent/stages/stage_native_semantic_pack.yaml"
    digest = hashlib.sha256(stage_pack.read_bytes()).hexdigest()

    assert stage_projection["source_file_sha256"] == f"sha256:{digest}"
    assert stage_projection["policy"]["policy_ref"] == "stage-completion-policy:mas/write"
    assert stage_projection["policy"]["completion_judgment_owner"] == "domain_stage"
    assert stage_projection["policy"]["provider_completion_is_domain_completion"] is False
    assert policy["mechanism_promotion_gate"]["allowed_change_scope"] == "manual_review_required"
    assert policy["mechanism_promotion_gate"]["automatic_mechanism_promotion_ready"] is False
    assert "dm003_submission_ready" in policy["forbidden_claims"]
    assert policy["target_owner_closeout_hook"]["command"] == [
        "env",
        "PYTHONPATH=src",
        "PYTHONDONTWRITEBYTECODE=1",
        "python3",
        "-m",
        "med_autoscience.authority_handlers.self_evolution_closeout",
    ]
    assert (
        policy["target_owner_closeout_hook"]["working_directory"]
        == "target_agent_repo_root"
    )


def test_owner_handler_registry_binds_closeout_callable() -> None:
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    handler = next(
        entry
        for entry in registry["handlers"]
        if entry["handler_id"] == "mas.agent-lab-self-evolution-closeout"
    )

    assert handler["binding"] == {
        "kind": "python_callable",
        "module": "med_autoscience.authority_handlers.self_evolution_closeout",
        "callable": "evaluate_agent_lab_self_evolution_closeout",
    }
