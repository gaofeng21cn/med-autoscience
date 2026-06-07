from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def _complete_soak_evidence_map() -> dict[str, list[str]]:
    return {
        "literature_scout": ["studies/dpcc-003/artifacts/literature_scout/latest.json"],
        "line_selection": ["studies/dpcc-003/artifacts/line_selection/latest.json"],
        "main_analysis": ["studies/dpcc-003/artifacts/main_analysis/latest.json"],
        "bounded_analysis": ["studies/dpcc-003/artifacts/bounded_analysis/latest.json"],
        "route_back": ["studies/dpcc-003/artifacts/quality/route_back_trace.json"],
        "stop_loss": ["studies/dpcc-003/runtime_escalation_record.json"],
        "revision_reopen": ["studies/dpcc-003/controller_decisions/latest.json"],
        "runtime_recovery": ["studies/dpcc-003/progress_projection.json"],
        "finalize_rebuild": ["studies/dpcc-003/artifacts/finalize_rebuild/latest.json"],
        "final_pre_submission_audit": [
            "studies/dpcc-003/artifacts/publication_eval/latest.json"
        ],
    }


def _write_sanitized_soak_fixture(study_root: Path, stage_evidence: dict[str, list[str]]) -> Path:
    matrix_path = study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(
        json.dumps(
            {
                "fixture_kind": "sanitized_real_study_soak_fixture",
                "study_id": "fixture-dpcc-003",
                "contains_phi": False,
                "stage_evidence": stage_evidence,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return matrix_path


def test_real_paper_ai_first_soak_contract_freezes_observational_schema() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    contract = module.build_real_paper_ai_first_soak_contract()

    assert contract["surface"] == "real_paper_ai_first_soak"
    assert contract["schema_version"] == 1
    assert contract["purpose"] == "measure_ai_first_flow_rework_and_quality"
    assert contract["manual_study_artifact_patch_allowed"] is False
    assert contract["canonical_flow_only"] is True
    assert contract["observational_evidence_only"] is True
    assert contract["quality_gate_relaxation_allowed"] is False
    assert contract["mechanical_ready_can_authorize_quality"] is False
    assert contract["artifact_patch_targets"] == []
    assert [line["paper_id"] for line in contract["paper_lines"]] == [
        "nf-pitnet-003",
        "dpcc-003",
        "dpcc-004",
    ]
    assert contract["evidence_schema"]["required_fields"] == [
        "paper_id",
        "quality_authorization_source",
        "artifact_rebuild_source",
        "route_back_count",
        "route_back_reasons",
        "ai_reviewer_intervention_points",
        "mechanical_ready_overreach_detected",
        "final_blockers",
        "manual_gate",
    ]
    assert contract["authority_requirements"] == {
        "quality_authorization_source": "ai_reviewer_backed_publication_eval_or_manual_gate",
        "artifact_rebuild_source": "canonical_sources_and_ai_reviewer_quality_decision",
        "route_back_reasons": "structured_rework_taxonomy",
        "ai_reviewer_intervention_points": "reviewer_operating_system_trace",
        "manual_gate": "explicit_human_decision",
    }


def test_real_study_soak_matrix_evidence_marks_complete_only_with_every_required_stage() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    result = module.build_real_study_soak_matrix_evidence(
        evidence_map=_complete_soak_evidence_map()
    )

    assert result["surface"] == "real_study_soak_matrix_evidence"
    assert result["schema_version"] == 1
    assert result["overall_status"] == "complete"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False

    by_stage = {stage["stage"]: stage for stage in result["required_stages"]}
    assert by_stage["literature_scout"] == {
        "stage": "literature_scout",
        "status": "complete",
        "evidence_refs": ["studies/dpcc-003/artifacts/literature_scout/latest.json"],
        "missing_reason": "",
    }
    assert all(stage["status"] == "complete" for stage in result["required_stages"])


def test_real_study_soak_matrix_evidence_fails_closed_when_a_required_stage_lacks_durable_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")
    evidence_map = _complete_soak_evidence_map()
    evidence_map["route_back"] = []
    evidence_map.pop("runtime_recovery")

    result = module.build_real_study_soak_matrix_evidence(evidence_map=evidence_map)

    assert result["surface"] == "real_study_soak_matrix_evidence"
    assert result["overall_status"] == "partial"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False

    by_stage = {stage["stage"]: stage for stage in result["required_stages"]}
    assert by_stage["route_back"] == {
        "stage": "route_back",
        "status": "missing",
        "evidence_refs": [],
        "missing_reason": "missing_durable_evidence_ref",
    }
    assert by_stage["runtime_recovery"] == {
        "stage": "runtime_recovery",
        "status": "missing",
        "evidence_refs": [],
        "missing_reason": "missing_durable_evidence_ref",
    }


def test_real_study_soak_matrix_evidence_reads_study_root_stage_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")
    study_root = tmp_path / "dpcc-003"
    matrix_path = study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(
        json.dumps({"stage_evidence": _complete_soak_evidence_map()}),
        encoding="utf-8",
    )

    result = module.build_real_study_soak_matrix_evidence(study_roots=[study_root])

    assert result["surface"] == "real_study_soak_matrix_evidence"
    assert result["overall_status"] == "complete"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False
    assert result["evidence_sources"] == [
        str(matrix_path),
    ]


def test_real_study_soak_matrix_evidence_accepts_sanitized_full_real_study_fixture(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")
    study_root = tmp_path / "sanitized-study-root"
    matrix_path = _write_sanitized_soak_fixture(study_root, _complete_soak_evidence_map())

    result = module.build_real_study_soak_matrix_evidence(study_roots=[study_root])

    assert result["overall_status"] == "complete"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False
    assert result["evidence_sources"] == [str(matrix_path)]
    by_stage = {stage["stage"]: stage for stage in result["required_stages"]}
    assert set(by_stage) == {
        "literature_scout",
        "line_selection",
        "main_analysis",
        "bounded_analysis",
        "route_back",
        "stop_loss",
        "revision_reopen",
        "runtime_recovery",
        "finalize_rebuild",
        "final_pre_submission_audit",
    }
    assert by_stage["final_pre_submission_audit"]["evidence_refs"] == [
        "studies/dpcc-003/artifacts/publication_eval/latest.json"
    ]


def test_real_study_soak_matrix_evidence_lists_missing_stage_gaps_for_sanitized_fixture(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")
    evidence_map = _complete_soak_evidence_map()
    evidence_map.pop("bounded_analysis")
    evidence_map["final_pre_submission_audit"] = []
    _write_sanitized_soak_fixture(tmp_path / "sanitized-study-root", evidence_map)

    result = module.build_real_study_soak_matrix_evidence(
        study_roots=[tmp_path / "sanitized-study-root"]
    )

    assert result["overall_status"] == "partial"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False
    assert result["missing_stage_gaps"] == [
        {
            "stage": "bounded_analysis",
            "missing_reason": "missing_durable_evidence_ref",
        },
        {
            "stage": "final_pre_submission_audit",
            "missing_reason": "missing_durable_evidence_ref",
        },
    ]


def test_real_paper_ai_first_soak_recording_entry_is_observational_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    observation = module.build_real_paper_ai_first_soak_observation(
        paper_id="nf-pitnet-003",
        quality_authorization_source="artifacts/publication_eval/latest.json",
        artifact_rebuild_source="canonical_sources_and_ai_reviewer_quality_decision",
        route_back_reasons=["medical_prose_review_route_back", "claim_evidence_alignment"],
        ai_reviewer_intervention_points=["pre_draft_readiness", "publication_eval"],
        mechanical_ready_overreach_detected=True,
        final_blockers=["manual_gate_waiting"],
        manual_gate={"required": True, "state": "waiting_for_human_authorization"},
    )

    assert observation["surface"] == "real_paper_ai_first_soak_observation"
    assert observation["paper_id"] == "nf-pitnet-003"
    assert observation["route_back_count"] == 2
    assert observation["manual_study_artifact_patch_allowed"] is False
    assert observation["canonical_flow_only"] is True
    assert observation["observational_evidence_only"] is True
    assert observation["artifact_write_paths"] == []

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_real_paper_ai_first_soak_observation_from_runtime_snapshot_extracts_observability_evidence() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    observation = module.build_real_paper_ai_first_soak_observation_from_runtime_snapshot(
        paper_id="dpcc-003",
        runtime_snapshot_bundle={
            "progress_snapshot": {
                "current_blockers": ["manual_gate_waiting"],
                "manual_gate": {"required": True, "state": "waiting_for_human_authorization"},
            },
            "quality_snapshot": {
                "quality_authorization_source": "ai_reviewer_backed_publication_eval_or_manual_gate",
                "route_back_count": 2,
                "route_back_reasons": [
                    "medical_prose_review_route_back",
                    "claim_evidence_alignment",
                ],
                "ai_reviewer_intervention_points": [
                    "pre_draft_readiness",
                    "publication_eval",
                ],
                "mechanical_ready_overreach_detected": True,
                "final_blockers": ["manual_gate_waiting"],
            },
            "artifact_snapshot": {
                "artifact_rebuild_source": "canonical_sources_and_ai_reviewer_quality_decision",
                "current_package_from_canonical_source": True,
            },
            "operations_dashboard_summary": {
                "surface": "ai_first_operations_dashboard_summary",
                "user_view": {
                    "blockers": ["manual_gate_waiting"],
                    "human_review_required": True,
                },
                "maintainer_view": {
                    "ai_reviewer_trace": {"complete": True},
                    "route_back": {"count": 2, "target": "write"},
                    "artifact_stale": {"current_package_from_canonical_source": True},
                },
                "authority": {
                    "observability_can_authorize_quality": False,
                    "observability_can_mutate_runtime": False,
                },
            },
        },
    )

    assert observation["surface"] == "real_paper_ai_first_soak_observation"
    assert observation["paper_id"] == "dpcc-003"
    assert observation["quality_authorization_source"] == (
        "ai_reviewer_backed_publication_eval_or_manual_gate"
    )
    assert observation["artifact_rebuild_source"] == (
        "canonical_sources_and_ai_reviewer_quality_decision"
    )
    assert observation["route_back_count"] == 2
    assert observation["route_back_reasons"] == [
        "medical_prose_review_route_back",
        "claim_evidence_alignment",
    ]
    assert observation["ai_reviewer_intervention_points"] == [
        "pre_draft_readiness",
        "publication_eval",
    ]
    assert observation["mechanical_ready_overreach_detected"] is True
    assert observation["final_blockers"] == ["manual_gate_waiting"]
    assert observation["manual_gate"] == {
        "required": True,
        "state": "waiting_for_human_authorization",
    }
    assert observation["manual_study_artifact_patch_allowed"] is False
    assert observation["canonical_flow_only"] is True
    assert observation["observational_evidence_only"] is True
    assert observation["artifact_write_paths"] == []

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_real_paper_ai_first_soak_observation_from_snapshot_fails_closed_when_authority_is_missing() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    observation = module.build_real_paper_ai_first_soak_observation_from_runtime_snapshot(
        paper_id="dpcc-004",
        operations_dashboard_summary={
            "surface": "ai_first_operations_dashboard_summary",
            "user_view": {
                "blockers": ["publication_eval_stale"],
                "human_review_required": True,
            },
            "maintainer_view": {
                "ai_reviewer_trace": {"complete": False},
                "route_back": {"count": 1, "target": "ai_reviewer"},
                "artifact_stale": {
                    "stale_artifact_count": 1,
                    "current_package_from_canonical_source": False,
                },
            },
            "authority": {
                "observability_can_authorize_quality": False,
                "observability_can_mutate_runtime": False,
            },
        },
    )

    assert observation["quality_authorization_source"] == "missing_ai_reviewer_quality_authorization"
    assert observation["artifact_rebuild_source"] == "missing_canonical_artifact_rebuild_source"
    assert observation["route_back_count"] == 1
    assert observation["route_back_reasons"] == []
    assert observation["ai_reviewer_intervention_points"] == []
    assert observation["mechanical_ready_overreach_detected"] is False
    assert observation["final_blockers"] == ["publication_eval_stale"]
    assert observation["manual_gate"] == {
        "required": True,
        "state": "human_review_required",
    }

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "quality_authorization_source_missing",
        "artifact_rebuild_source_not_canonical",
        "route_back_reasons_missing",
        "ai_reviewer_intervention_points_missing",
    }


def test_real_paper_ai_first_soak_validation_rejects_bypass_and_schema_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")
    observation = module.build_real_paper_ai_first_soak_observation(
        paper_id="dpcc-003",
        quality_authorization_source="current_package.zip",
        artifact_rebuild_source="submission_minimal",
        route_back_reasons=[],
        ai_reviewer_intervention_points=[],
        mechanical_ready_overreach_detected=False,
        final_blockers=[],
        manual_gate={},
    )
    observation["manual_study_artifact_patch_allowed"] = True
    observation["canonical_flow_only"] = False
    observation["observational_evidence_only"] = False
    observation["artifact_write_paths"] = ["submission_minimal/"]

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "manual_artifact_patching_enabled",
        "canonical_flow_not_required",
        "observational_evidence_not_enforced",
        "artifact_write_path_present",
        "quality_authority_uses_derived_artifact",
        "artifact_rebuild_source_not_canonical",
        "route_back_reasons_missing",
        "ai_reviewer_intervention_points_missing",
        "manual_gate_missing",
    }


def test_paper_soak_memory_apply_proof_links_opl_attempt_domain_handler_closeout_receipt_and_progress_guard() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    proof = module.build_paper_soak_memory_apply_proof(
        opl_attempt={
            "attempt_id": "opl-attempt-001",
            "provider": "temporal",
            "status": "completed",
        },
        domain_handler_task={
            "task_id": "domain-handler-task-001",
            "task_kind": "stage_memory/apply-closeout",
        },
        typed_closeout={
            "surface": "stage_memory_closeout_packet",
            "idempotency_key": "closeout-001",
            "proposed_writes": [{"write_id": "lesson-1"}],
        },
        mas_receipt={
            "surface": "memory_write_router_receipt",
            "status": "applied",
            "idempotency_key": "closeout-001",
            "receipt_ref": "memory/portfolio/research_memory/publication_route_memory/writeback_receipts/closeout-001.json",
        },
        progress_delta={
            "delta_id": "progress-delta-001",
            "delta_kind": "memory_writeback_applied",
            "progress_changed": True,
        },
    )

    assert proof["surface"] == "paper_soak_memory_apply_proof"
    assert proof["proof_mode"] == "read_only_or_guarded_apply"
    assert proof["overall_status"] == "complete"
    assert [step["step"] for step in proof["proof_steps"]] == [
        "opl_attempt",
        "codex_or_domain_handler",
        "typed_stage_closeout",
        "mas_memory_router_receipt",
        "progress_delta_or_guard",
    ]
    assert all(step["status"] == "present" for step in proof["proof_steps"])
    assert proof["authority_boundary"]["can_write_real_paper_package"] is False
    assert proof["authority_boundary"]["can_authorize_publication_quality"] is False
    assert {ref["role"] for ref in proof["source_refs"]} == {
        "opl_attempt",
        "domain_handler_task",
        "typed_stage_closeout",
        "mas_memory_router_receipt",
        "progress_delta",
    }


def test_paper_soak_memory_apply_proof_requires_progress_delta_human_gate_or_stop_loss() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    proof = module.build_paper_soak_memory_apply_proof(
        opl_attempt={"attempt_id": "opl-attempt-001"},
        domain_handler_task={"task_id": "domain-handler-task-001"},
        typed_closeout={"surface": "stage_memory_closeout_packet", "idempotency_key": "closeout-001"},
        mas_receipt={"surface": "memory_write_router_receipt", "status": "applied", "idempotency_key": "closeout-001"},
    )

    assert proof["overall_status"] == "partial"
    by_step = {step["step"]: step for step in proof["proof_steps"]}
    assert by_step["progress_delta_or_guard"] == {
        "step": "progress_delta_or_guard",
        "status": "missing",
        "ref": "missing_progress_delta_human_gate_or_stop_loss",
        "role": "Proof must end in progress delta, human gate, or stop-loss.",
    }
