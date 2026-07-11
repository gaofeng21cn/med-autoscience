from __future__ import annotations

from med_autoscience.controllers.ai_first_private_authority import (
    validate_ai_first_private_authority_gate,
)
def test_ai_first_gate_rejects_missing_reviewer_record() -> None:
    result = validate_ai_first_private_authority_gate(
        function_id="publication_quality_verdict",
        candidate_record={
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "ai_reviewer_required": True,
            }
        },
        executor_receipt={
            "agent_invocation_id": "exec-1",
            "task_record_ref": "tasks/exec-1.json",
            "context_record_ref": "contexts/exec-1.json",
            "receipt_ref": "receipts/exec-1.json",
        },
        reviewer_receipt=None,
    )

    assert result["status"] == "typed_blocker"
    assert result["can_close_quality_gate"] is False
    assert result["blocker_id"] == "missing_independent_reviewer_record"
    assert result["route_back"] == "route_back_to_review_or_revision_stage"


def test_ai_first_gate_rejects_self_review_context_reuse() -> None:
    shared_receipt = {
        "agent_invocation_id": "same-agent-task",
        "task_record_ref": "tasks/same.json",
        "context_record_ref": "contexts/same.json",
        "receipt_ref": "receipts/same.json",
    }

    result = validate_ai_first_private_authority_gate(
        function_id="source_readiness_verdict",
        candidate_record={
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
            },
            "quality_pack_evidence_refs": ["quality/source-readiness.json"],
        },
        executor_receipt=shared_receipt,
        reviewer_receipt=shared_receipt,
    )

    assert result["status"] == "typed_blocker"
    assert result["can_close_quality_gate"] is False
    assert result["blocker_id"] == "self_review_context_reuse"
    assert result["forbidden_mechanical_substitute"] == "file_presence_as_source_readiness_verdict"


def test_ai_first_gate_accepts_independent_reviewer_record_refs() -> None:
    result = validate_ai_first_private_authority_gate(
        function_id="ai_reviewer_quality_decision",
        candidate_record={
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
            },
            "ai_reviewer_record_ref": "reviews/latest.json",
            "reviewer_operating_system_trace_ref": "reviews/os-trace.json",
            "quality_pack_evidence_refs": ["quality/ai-reviewer.json"],
        },
        executor_receipt={
            "agent_invocation_id": "exec-1",
            "task_record_ref": "tasks/exec-1.json",
            "context_record_ref": "contexts/exec-1.json",
            "receipt_ref": "receipts/exec-1.json",
        },
        reviewer_receipt={
            "agent_role": "quality_gate_reviewer_or_auditor",
            "agent_invocation_id": "review-1",
            "task_record_ref": "tasks/review-1.json",
            "context_record_ref": "contexts/review-1.json",
            "receipt_ref": "receipts/review-1.json",
            "ai_reviewer_record_ref": "reviews/latest.json",
            "reviewed_executor_receipt_ref": "receipts/exec-1.json",
        },
    )

    assert result["status"] == "ai_first_record_validated"
    assert result["can_close_quality_gate"] is True
    assert result["judgment_mode"] == "ai_first_stage_gate"
    assert result["program_role"] == "validator"
    assert result["reviewer_receipt_ref"] == "receipts/review-1.json"
    assert result["independent_reviewer_or_auditor_evidence_refs"] == [
        "tasks/review-1.json",
        "contexts/review-1.json",
        "receipts/review-1.json",
        "reviews/latest.json",
    ]


def test_ai_first_gate_rejects_reviewer_receipt_not_bound_to_executor_receipt() -> None:
    result = validate_ai_first_private_authority_gate(
        function_id="publication_quality_verdict",
        candidate_record={
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
            },
            "ai_reviewer_record_ref": "reviews/latest.json",
            "quality_pack_evidence_refs": ["quality/publication.json"],
        },
        executor_receipt={
            "agent_invocation_id": "exec-1",
            "task_record_ref": "tasks/exec-1.json",
            "context_record_ref": "contexts/exec-1.json",
            "receipt_ref": "receipts/exec-1.json",
        },
        reviewer_receipt={
            "agent_role": "quality_gate_reviewer_or_auditor",
            "agent_invocation_id": "review-1",
            "task_record_ref": "tasks/review-1.json",
            "context_record_ref": "contexts/review-1.json",
            "receipt_ref": "receipts/review-1.json",
            "ai_reviewer_record_ref": "reviews/latest.json",
            "reviewed_executor_receipt_ref": "receipts/other-exec.json",
        },
    )

    assert result["status"] == "typed_blocker"
    assert result["can_close_quality_gate"] is False
    assert result["blocker_id"] == "reviewer_receipt_not_bound_to_executor_receipt"
    assert result["details"]["required_reviewer_field"] == "reviewed_executor_receipt_ref"
    assert result["details"]["executor_receipt_ref"] == "receipts/exec-1.json"


def test_ai_first_gate_rejects_reviewer_receipt_without_quality_record_ref() -> None:
    result = validate_ai_first_private_authority_gate(
        function_id="ai_reviewer_quality_decision",
        candidate_record={
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
            },
            "ai_reviewer_record_ref": "reviews/latest.json",
            "reviewer_operating_system_trace_ref": "reviews/os-trace.json",
            "quality_pack_evidence_refs": ["quality/ai-reviewer.json"],
        },
        executor_receipt={
            "agent_invocation_id": "exec-1",
            "task_record_ref": "tasks/exec-1.json",
            "context_record_ref": "contexts/exec-1.json",
            "receipt_ref": "receipts/exec-1.json",
        },
        reviewer_receipt={
            "agent_role": "quality_gate_reviewer_or_auditor",
            "agent_invocation_id": "review-1",
            "task_record_ref": "tasks/review-1.json",
            "context_record_ref": "contexts/review-1.json",
            "receipt_ref": "receipts/review-1.json",
        },
    )

    assert result["status"] == "typed_blocker"
    assert result["can_close_quality_gate"] is False
    assert result["blocker_id"] == "missing_independent_reviewer_quality_record_ref"


def test_mechanical_guard_surfaces_cannot_emit_medical_verdicts() -> None:
    result = validate_ai_first_private_authority_gate(
        function_id="owner_receipt_signer",
        candidate_record={"receipt_ref": "receipts/domain-owner.json"},
        executor_receipt={},
        reviewer_receipt=None,
    )

    assert result["status"] == "mechanical_guard_allowed"
    assert result["can_close_quality_gate"] is False
    assert result["program_may_emit_pass_ready_verdict"] is False
