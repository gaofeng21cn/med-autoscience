from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_feedbackops_dispatch_consumes_request_and_blocks_on_missing_ai_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        dispatch_reviewer_revision_feedbackops,
    )

    request_path = tmp_path / "feedbackops_dispatch_request.json"
    suite_path = tmp_path / "latest_suite.json"
    suite_path.write_text('{"suite_id":"suite:mas/test"}\n', encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_request",
                "status": "ready_for_opl_feedbackops",
                "study_id": "001-risk",
                "suite_path": str(suite_path),
                "opl_feedback_submit": {
                    "argv": [
                        "--target-agent",
                        "mas",
                        "--delivery-ref",
                        str(suite_path),
                        "--feedback-ref",
                        "task-intake:latest",
                        "--json",
                    ]
                },
                "authority_boundary": {"can_write_owner_receipt": False},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def fake_run(argv, *, text, capture_output, check):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, '{"ok":true}', "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = dispatch_reviewer_revision_feedbackops(request_path=request_path, opl_bin="opl")

    assert result["status"] == "blocked_missing_structured_ai_reviewer_evaluation"
    assert result["writes_study_truth"] is False
    assert result["writes_owner_receipt"] is False
    assert calls == [
        [
            "opl",
            "feedback",
            "submit",
            "--target-agent",
            "mas",
            "--delivery-ref",
            str(suite_path),
            "--feedback-ref",
            "task-intake:latest",
            "--json",
        ],
        ["opl", "feedback", "read", "--json"],
        ["opl", "feedback", "reconcile", "--json"],
        ["opl", "agent-lab", "run", "--suite", str(suite_path), "--json"],
    ]
    readback = json.loads((tmp_path / "feedbackops_execution_readback.json").read_text())
    assert readback["status"] == "blocked_missing_structured_ai_reviewer_evaluation"
    assert readback["structured_ai_reviewer_evaluation_request_ref"].endswith(
        "structured_ai_reviewer_evaluation_request.json"
    )
    eval_request = json.loads(
        (tmp_path / "structured_ai_reviewer_evaluation_request.json").read_text(encoding="utf-8")
    )
    assert eval_request["status"] == "needs_independent_ai_reviewer_evaluation"
    assert "critique" in eval_request["required_fields"]
    assert "direct_evidence_refs" in eval_request["required_fields"]
    assert readback["feedbackops_read"]["stdout_summary"] == {"top_level_keys": ["ok"]}


def test_feedbackops_dispatch_normalizes_agent_lab_structured_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        dispatch_reviewer_revision_feedbackops,
    )

    request_path = tmp_path / "feedbackops_dispatch_request.json"
    suite_path = tmp_path / "latest_suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "suite_id": "mas-agent-lab-suite:001-risk:high-quality-medical-manuscript",
                "structured_independent_ai_reviewer_evaluation": {
                    "surface_kind": "mas_structured_independent_ai_reviewer_evaluation",
                    "schema_version": 1,
                    "evaluation_ref": "structured-ai-reviewer-evaluation:mas/001-risk/publication_eval_latest",
                    "study_id": "001-risk",
                    "target_agent_id": "med-autoscience",
                    "source_publication_eval_ref": "artifacts/publication_eval/latest.json",
                    "critique": [
                        {
                            "critique_id": "quality_assessment:medical_journal_prose_quality",
                            "summary": "The draft needs a finding-led clinical story.",
                        }
                    ],
                    "suggestions": [
                        {
                            "suggestion_id": "route_to_write_repair",
                            "summary": "Route reviewer critique through MAS owner write repair.",
                        }
                    ],
                    "direct_evidence_refs": [
                        "artifacts/publication_eval/latest.json",
                        "studies/001-risk/paper/manuscript.md",
                    ],
                    "provenance": {
                        "owner": "med-autoscience",
                        "source_kind": "publication_eval_ai_reviewer_projection",
                        "projection_role": "oma_structured_reviewer_input",
                        "candidate_is_authority": False,
                    },
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    request_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_request",
                "status": "ready_for_opl_feedbackops",
                "study_id": "001-risk",
                "suite_path": str(suite_path),
                "feedback_ref": "task-intake:latest",
                "opl_feedback_submit": {
                    "argv": [
                        "--target-agent",
                        "mas",
                        "--delivery-ref",
                        str(suite_path),
                        "--feedback-ref",
                        "task-intake:latest",
                        "--json",
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_run(argv, *, text, capture_output, check):
        return subprocess.CompletedProcess(argv, 0, '{"ok":true}', "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = dispatch_reviewer_revision_feedbackops(request_path=request_path, opl_bin="opl")

    normalized_ref = tmp_path / "ai_reviewer_evaluation_independent.json"
    normalized = json.loads(normalized_ref.read_text(encoding="utf-8"))
    assert result["status"] == "ready_for_oma_work_order_materialization"
    assert result["ai_reviewer_evaluation_ref"] == str(normalized_ref)
    assert normalized["reviewer_kind"] == "independent_ai_medical_manuscript_quality_reviewer"
    assert normalized["no_shared_context"] is True
    assert normalized["independent_attempt"] is True
    assert normalized["execution_attempt_ref"] != normalized["review_attempt_ref"]
    assert "The draft needs a finding-led clinical story" in normalized["critique"]
    assert normalized["suggestions"] == [
        "route_to_write_repair: Route reviewer critique through MAS owner write repair."
    ]
    assert "artifacts/publication_eval/latest.json" in normalized["direct_evidence_refs"]
    assert normalized["provenance"]["normalized_from_surface_kind"] == (
        "mas_structured_independent_ai_reviewer_evaluation"
    )
    assert not (tmp_path / "structured_ai_reviewer_evaluation_request.json").exists()


def test_feedbackops_dispatch_discovers_structured_ai_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        dispatch_reviewer_revision_feedbackops,
    )

    request_path = tmp_path / "feedbackops_dispatch_request.json"
    suite_path = tmp_path / "latest_suite.json"
    suite_path.write_text('{"suite_id":"suite:mas/test"}\n', encoding="utf-8")
    ai_eval = tmp_path / "ai_reviewer_evaluation_independent.json"
    ai_eval.write_text(
        json.dumps(
            {
                "reviewer_kind": "independent_ai_medical_manuscript_quality_reviewer",
                "model_or_provider": "test-model",
                "run_ref": "run:mas/test",
                "execution_attempt_ref": "execution-attempt:test",
                "review_attempt_ref": "review-attempt:test",
                "no_shared_context": True,
                "independent_attempt": True,
                "critique": "The draft needs a finding-led clinical story.",
                "suggestions": ["Require denominator and sensitivity evidence before headline claims."],
                "source_refs": ["reviewer-feedback.md"],
                "direct_evidence_refs": ["publication_eval/latest.json"],
                "verdict": "valid_refs_only_independent_reviewer_input",
                "predicted_impact": "Better first-draft quality.",
                "provenance": {"created_by": "unit-test"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    request_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_request",
                "status": "ready_for_opl_feedbackops",
                "study_id": "001-risk",
                "suite_path": str(suite_path),
                "opl_feedback_submit": {
                    "argv": [
                        "--target-agent",
                        "mas",
                        "--delivery-ref",
                        str(suite_path),
                        "--feedback-ref",
                        "task-intake:latest",
                        "--json",
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_run(argv, *, text, capture_output, check):
        return subprocess.CompletedProcess(argv, 0, '{"ok":true}', "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = dispatch_reviewer_revision_feedbackops(request_path=request_path, opl_bin="opl")

    assert result["status"] == "ready_for_oma_work_order_materialization"
    assert result["ai_reviewer_evaluation_ref"] == str(ai_eval)
    assert result["ai_reviewer_evaluation_status"] == "valid"
    assert result["next_owner"] == "opl-meta-agent"


def test_feedbackops_execution_readback_reader_compacts_command_outputs(tmp_path: Path) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        read_reviewer_revision_feedbackops_execution_readback,
    )

    readback_path = (
        tmp_path
        / "artifacts"
        / "agent_lab"
        / "medical_manuscript_quality"
        / "feedbackops_execution_readback.json"
    )
    readback_path.parent.mkdir(parents=True)
    readback_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_readback",
                "schema_version": 1,
                "study_id": "001-risk",
                "status": "blocked_missing_structured_ai_reviewer_evaluation",
                "next_owner": "opl-meta-agent",
                "blocked_reason": "missing structured reviewer evaluation",
                "writes_study_truth": False,
                "writes_owner_receipt": False,
                "writes_typed_blocker": False,
                "feedbackops_read": {
                    "argv": ["opl", "feedback", "read", "--json"],
                    "returncode": 0,
                    "stdout_bytes": 100000,
                    "stdout_json": None,
                    "stdout_summary": {"feedbackops": {"status": "ready"}},
                    "stderr": "",
                },
                "agent_lab_run": {
                    "argv": ["opl", "agent-lab", "run", "--suite", "suite.json", "--json"],
                    "returncode": 0,
                    "stdout_bytes": 200000,
                    "stdout_json": None,
                    "stdout_summary": {"agent_lab": {"status": "blocked"}},
                    "stderr": "",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    compact = read_reviewer_revision_feedbackops_execution_readback(study_root=tmp_path)

    assert compact is not None
    assert compact["status"] == "blocked_missing_structured_ai_reviewer_evaluation"
    assert compact["commands"]["feedbackops_read"]["stdout_summary"] == {"feedbackops": {"status": "ready"}}
    assert compact["commands"]["agent_lab_run"]["stdout_bytes"] == 200000


def test_feedbackops_execution_readback_reader_supersedes_old_missing_eval_blocker(
    tmp_path: Path,
) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        read_reviewer_revision_feedbackops_execution_readback,
    )

    readback_path = (
        tmp_path
        / "artifacts"
        / "agent_lab"
        / "medical_manuscript_quality"
        / "feedbackops_execution_readback.json"
    )
    readback_path.parent.mkdir(parents=True)
    readback_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_readback",
                "schema_version": 1,
                "study_id": "001-risk",
                "status": "blocked_missing_structured_ai_reviewer_evaluation",
                "next_owner": "opl-meta-agent",
                "blocked_reason": "missing structured reviewer evaluation",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    ai_eval = readback_path.parent / "ai_reviewer_evaluation_independent.json"
    ai_eval.write_text(
        json.dumps(
            {
                "reviewer_kind": "independent_ai_medical_manuscript_quality_reviewer",
                "model_or_provider": "test-model",
                "run_ref": "run:mas/test",
                "execution_attempt_ref": "execution-attempt:test",
                "review_attempt_ref": "review-attempt:test",
                "no_shared_context": True,
                "independent_attempt": True,
                "critique": "The draft needs a finding-led clinical story.",
                "suggestions": ["Require denominator and sensitivity evidence."],
                "source_refs": ["reviewer-feedback.md"],
                "direct_evidence_refs": ["publication_eval/latest.json"],
                "verdict": "valid_refs_only_independent_reviewer_input",
                "predicted_impact": "Better first-draft quality.",
                "provenance": {"created_by": "unit-test"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    work_order = (
        readback_path.parent
        / "oma_external_suite_20260707"
        / "developer-patch-work-order.json"
    )
    work_order.parent.mkdir()
    work_order.write_text(
        json.dumps(
            {
                "surface_kind": "opl_meta_agent_developer_patch_work_order",
                "status": "ready_for_target_agent_source_patch",
                "ai_reviewer_evaluation_ref": str(ai_eval),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    compact = read_reviewer_revision_feedbackops_execution_readback(study_root=tmp_path)

    assert compact is not None
    assert compact["status"] == "superseded_by_oma_work_order_materialization"
    assert compact["superseded_status"] == (
        "blocked_missing_structured_ai_reviewer_evaluation"
    )
    assert compact["blocked_reason"] is None
    assert compact["ai_reviewer_evaluation_ref"] == str(ai_eval)
    assert compact["oma_work_order_or_receipt_ref"] == str(work_order)


def test_feedbackops_execution_readback_reader_supersedes_ready_status_with_executed_work_order(
    tmp_path: Path,
) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        read_reviewer_revision_feedbackops_execution_readback,
    )

    readback_path = (
        tmp_path
        / "artifacts"
        / "agent_lab"
        / "medical_manuscript_quality"
        / "feedbackops_execution_readback.json"
    )
    readback_path.parent.mkdir(parents=True)
    readback_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_readback",
                "schema_version": 1,
                "study_id": "001-risk",
                "status": "ready_for_oma_work_order_materialization",
                "next_owner": "opl-meta-agent",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(readback_path, (1_700_000_000, 1_700_000_000))
    ai_eval = readback_path.parent / "ai_reviewer_evaluation_independent.json"
    ai_eval.write_text(
        json.dumps(
            {
                "reviewer_kind": "independent_ai_medical_manuscript_quality_reviewer",
                "model_or_provider": "test-model",
                "run_ref": "run:mas/test",
                "execution_attempt_ref": "execution-attempt:test",
                "review_attempt_ref": "review-attempt:test",
                "no_shared_context": True,
                "independent_attempt": True,
                "critique": "The draft needs a finding-led clinical story.",
                "suggestions": ["Require denominator and sensitivity evidence."],
                "source_refs": ["reviewer-feedback.md"],
                "direct_evidence_refs": ["publication_eval/latest.json"],
                "verdict": "valid_refs_only_independent_reviewer_input",
                "predicted_impact": "Better first-draft quality.",
                "provenance": {"created_by": "unit-test"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    suite_dir = readback_path.parent / "oma_external_suite_20260707"
    work_order = suite_dir / "developer-patch-work-order.json"
    delegation = suite_dir / "external-work-order-delegation.json"
    receipt = suite_dir / "opl_work_order_execute" / "work-order-execution-receipt.json"
    receipt.parent.mkdir(parents=True)
    work_order.write_text(
        json.dumps(
            {
                "surface_kind": "opl_meta_agent_developer_patch_work_order",
                "status": "ready_for_target_agent_source_patch",
                "work_order_id": "oma_developer_patch_work_order_test",
                "ai_reviewer_evaluation_ref": str(ai_eval),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    delegation.write_text(
        json.dumps(
            {
                "surface_kind": "opl_meta_agent_external_work_order_execution_delegation",
                "status": "delegated_to_opl_work_order_primitive",
                "work_order_ref": "oma_developer_patch_work_order_test",
                "work_order_path": str(work_order),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    receipt.write_text(
        json.dumps(
            {
                "surface_kind": "opl_work_order_codex_execution_receipt",
                "status": "executed_absorbed_and_cleaned",
                "work_order_id": "oma_developer_patch_work_order_test",
                "source_work_order_path": str(work_order),
                "absorption": {"absorbed": True, "absorbed_head": "abc123"},
                "cleanup": {"worktree_removed": True, "branch_removed": True},
                "target_owner_receipt_or_typed_blocker": {"status": "typed_blocker_recorded"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(work_order, (1_700_000_010, 1_700_000_010))
    os.utime(receipt, (1_700_000_020, 1_700_000_020))
    os.utime(delegation, (1_700_000_030, 1_700_000_030))

    compact = read_reviewer_revision_feedbackops_execution_readback(study_root=tmp_path)

    assert compact is not None
    assert compact["status"] == "superseded_by_oma_work_order_execution"
    assert compact["superseded_status"] == "ready_for_oma_work_order_materialization"
    assert compact["oma_work_order_or_receipt_ref"] == str(receipt)
    assert compact["oma_work_order_or_receipt_status"] == "executed_absorbed_and_cleaned"
    assert compact["oma_work_order_id"] == "oma_developer_patch_work_order_test"
    assert compact["oma_patch_absorbed"] is True
    assert compact["oma_absorbed_head"] == "abc123"
    assert compact["oma_worktree_removed"] is True
    assert compact["oma_branch_removed"] is True
    assert compact["oma_target_owner_result_status"] == "typed_blocker_recorded"
