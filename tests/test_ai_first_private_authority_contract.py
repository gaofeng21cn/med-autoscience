from __future__ import annotations

from med_autoscience.controllers.ai_first_private_authority import (
    validate_ai_first_private_authority_gate,
)
from med_autoscience.controllers.domain_slo_scheduler_projection_parts.consumer_migration import (
    build_functional_consumer_boundary,
)


AI_FIRST_GATE_IDS = {
    "publication_quality_verdict",
    "ai_reviewer_quality_decision",
    "source_readiness_verdict",
    "publication_route_memory_accept_reject",
}


def test_private_authority_manifest_classifies_judgment_modes() -> None:
    authority = build_functional_consumer_boundary()["minimal_authority_function_manifest"]

    assert authority["allowed_judgment_modes"] == [
        "ai_first_stage_gate",
        "ai_first_record_validator",
        "mechanical_guard",
        "refs_only_adapter",
    ]
    assert authority["verdict_function_model_retired"] is True
    assert authority["gate_validator_ref"] == (
        "src/med_autoscience/controllers/ai_first_private_authority.py::"
        "validate_ai_first_private_authority_gate"
    )
    assert authority["runtime_enforcement_status"] == "contract_validator_landed"
    assert authority["program_output_policy"] == (
        "programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only"
    )

    by_id = {item["function_id"]: item for item in authority["functions"]}
    for function_id in AI_FIRST_GATE_IDS:
        item = by_id[function_id]
        assert item["judgment_mode"] == "ai_first_stage_gate"
        assert item["decision_output_owner"] == "independent_reviewer_auditor_agent"
        assert item["program_may_emit_pass_ready_verdict"] is False
        assert item["missing_ai_first_record_policy"] == "typed_blocker_or_route_back"
        assert item["standard_stage_output"] is True

    assert by_id["artifact_mutation_authorization"]["judgment_mode"] == "ai_first_record_validator"
    assert by_id["artifact_mutation_authorization"]["program_may_emit_pass_ready_verdict"] is False
    assert by_id["owner_receipt_signer"]["judgment_mode"] == "mechanical_guard"
    assert by_id["medical_helper_implementation"]["judgment_mode"] == "mechanical_guard"


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
            "agent_invocation_id": "review-1",
            "task_record_ref": "tasks/review-1.json",
            "context_record_ref": "contexts/review-1.json",
            "receipt_ref": "receipts/review-1.json",
        },
    )

    assert result["status"] == "ai_first_record_validated"
    assert result["can_close_quality_gate"] is True
    assert result["judgment_mode"] == "ai_first_stage_gate"
    assert result["program_role"] == "validator"


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
