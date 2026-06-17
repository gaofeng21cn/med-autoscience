from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import (
    disable_progress_projection as _disable_progress_projection,
)
from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import sha256_text as _sha256_text
from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import write_json as _write_json
from tests.domain_action_request_materializer_cases.ai_reviewer_request_refresh_cases import *  # noqa: F403,F401
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def test_materialize_domain_action_requests_keeps_current_prose_routeback_dispatch_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = "quest-dpcc"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_assessment_required",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": str(study_root / "paper" / "draft.md"),
                "manuscript_digest": "sha256:" + "b" * 64,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Repair medical manuscript prose against current evidence.",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::003::stale",
            "assessment_provenance": {"owner": "ai_reviewer"},
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "repeat_suppressed",
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_contract": {
                "do_not_repeat": True,
                "repeat_suppression_key": route["source_fingerprint"],
            },
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["repeat_suppressed"] is False
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert result["repeat_suppressed_count"] == 0


def test_materialize_domain_action_requests_honors_consumed_transition_owner_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": stale_route,
                    "action_queue": [],
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "lane": "publication_gate",
                            "summary": "MAS publication-gate/currentness replay after current AI reviewer archive.",
                        },
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                        },
                    },
                    "runtime_health_snapshot": {
                        "runtime_health_epoch": "runtime-health-current-write-route",
                    },
                    "study_truth_snapshot": {
                        "truth_epoch": "truth-epoch-current-write-route",
                        "source_signature": "truth-source-current-write-route",
                    },
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["ignored_actions"] == []
    assert result["owner_callable_adapter_count"] == 1
    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["next_executable_owner"] == "gate_clearing_batch"
    assert dispatch["source_action"]["controller_work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    route = dispatch["owner_route"]
    assert route["next_owner"] == "gate_clearing_batch"
    assert route["owner_reason"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert route["allowed_actions"] == ["run_gate_clearing_batch"]
    assert route["source_refs"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert dispatch["prompt_contract"]["owner_route"]["source_refs"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )


def test_materialize_domain_action_requests_prefers_fresh_progress_action_when_ticket_action_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="old_write_repair_from_stage_next_action",
        allowed_actions=["run_quality_repair_batch"],
    )
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
            "target_surface": "artifacts/controller/quality_repair_batch/latest.json",
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": stale_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "authority": "stage_native_workspace_next_action",
                            "reason": "old_write_repair_from_stage_next_action",
                            "owner_route": stale_route,
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "authority": "stage_native_workspace_next_action",
                    "reason": "old_write_repair_from_stage_next_action",
                    "owner_route": stale_route,
                }
            ],
        },
    )
    fresh_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "generated_at": "2026-06-08T04:37:17+00:00",
            "active_run_id": None,
            "actual_write_active": False,
            "owner_route": fresh_route,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "ai_reviewer",
                "work_unit": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "action_type": "return_to_ai_reviewer_workflow",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "source_ref": (
                    "studies/002-dm-china-us-mortality-attribution/"
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "source_fingerprint": "repair-progress-current-ai-reviewer",
                "work_unit_fingerprint": "repair-progress-current-ai-reviewer-work-unit",
            },
        }

    monkeypatch.setattr(study_progress_module, "read_study_progress", fake_read_study_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["owner_callable_adapter_count"] == 1
    request = result["request_tasks"][0]
    dispatch = result["owner_callable_adapters"][0]
    assert request["action_type"] == "return_to_ai_reviewer_workflow"
    assert request["request_owner"] == "ai_reviewer"
    assert request["reason"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    ignored_reasons = {item["reason"] for item in result["ignored_actions"]}
    assert "superseded_by_fresh_study_progress_current_owner_ticket" in ignored_reasons


def test_materialize_domain_action_requests_prefers_current_ai_reviewer_queue_over_stale_stage_native_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
            "target_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "action_id": f"supervisor-action::{study_id}::return_to_ai_reviewer_workflow::repair_progress",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "repair_progress_ai_reviewer_recheck_required",
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "ai_reviewer",
                        "next_work_unit": (
                            "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                        ),
                    },
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["owner_callable_adapter_count"] == 1
    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["source_action"]["authority"] == "observability_only"
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "run_quality_repair_batch": "stage_native_workspace_next_action_requires_authority_binding",
    }


def test_materialize_domain_action_requests_prefers_canonical_current_work_unit_over_stale_stage_native_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
            "target_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    current_fingerprint = "sha256:canonical-current-ai-reviewer-recheck"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route["work_unit_fingerprint"] = current_fingerprint
    route["source_refs"] = {
        **dict(route["source_refs"]),
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": current_fingerprint,
        "owner_route_currentness_basis": {
            "truth_epoch": f"truth-epoch::{study_id}",
            "runtime_health_epoch": f"runtime-health::{study_id}",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": current_fingerprint,
        },
    }
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="old_stage_native_write",
        allowed_actions=["run_quality_repair_batch"],
    )
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "source": "canonical_current_work_unit",
        "status": "executable_owner_action",
        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": current_fingerprint,
        "next_owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "state": {"state_kind": "executable_owner_action"},
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "ai_reviewer",
                        "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    },
                    "current_work_unit": current_work_unit,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "authority": "stage_native_workspace_next_action",
                            "reason": "old_stage_native_write",
                            "owner_route": stale_route,
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "authority": "stage_native_workspace_next_action",
                    "reason": "old_stage_native_write",
                    "owner_route": stale_route,
                }
            ],
        },
    )
    monkeypatch.setattr(study_progress_module, "read_study_progress", lambda **_: {})

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["owner_callable_adapter_count"] == 1
    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["action_fingerprint"] == current_fingerprint
    assert dispatch["owner_route"]["source_refs"]["work_unit_fingerprint"] == current_fingerprint
    assert dispatch["source_action"]["authority"] == "canonical_current_work_unit"
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "run_quality_repair_batch": "superseded_by_canonical_current_work_unit",
    }


def test_materialize_domain_action_requests_keeps_repair_progress_recheck_queue_over_old_routeback_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript after repair progress.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260608T060000Z_publication_eval_record.json",
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            study_id=study_id,
            quest_id=quest_id,
            eval_id="publication-eval::dm002::old-routeback::2026-06-08T06:00:00+00:00",
            emitted_at="2026-06-08T06:00:00+00:00",
        ),
    )
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="repair_progress_ai_reviewer_recheck_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route["source_refs"] = {
        **dict(route["source_refs"]),
        "owner_route_currentness_basis": {
            "truth_epoch": f"truth-epoch::{study_id}",
            "runtime_health_epoch": f"runtime-health::{study_id}",
            "source_eval_id": "publication-eval::dm002::current-mechanical-projection",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:repair-progress-current-ai-reviewer",
        },
    }
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "action_id": f"supervisor-action::{study_id}::return_to_ai_reviewer_workflow::repair_progress",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "repair_progress_ai_reviewer_recheck_required",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "controller_work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "executable_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["owner_callable_adapter_count"] == 1
    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["source_action"]["reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert dispatch["source_action"]["next_work_unit"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert "materialization_decision" not in dispatch["source_action"]


def test_materialize_ai_reviewer_request_preserves_current_manuscript_record_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent story.\n", encoding="utf-8")
    review_manuscript_path.write_text("# Draft\n\nCurrent story.\n", encoding="utf-8")
    source_ref = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    stale_record_ref = study_root / "artifacts" / "publication_eval" / "latest.json"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "work_unit_fingerprint": "dm002-current-manuscript-record",
        "source_ref": str(source_ref.resolve()),
        "stale_record_ref": str(stale_record_ref.resolve()),
        "required_currentness_refs": [
            str(manuscript_path.resolve()),
            str(review_manuscript_path.resolve()),
        ],
        "record_only_surface": True,
        "publication_eval_latest_write_allowed": False,
        "controller_decision_write_allowed": False,
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}::{quest_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_ref.resolve()),
                "required_currentness_refs": [
                    str(manuscript_path.resolve()),
                    str(review_manuscript_path.resolve()),
                ],
                "source_ref": str(source_ref.resolve()),
            },
            "source_workflow_ref": {
                "surface": "owner_route_reconcile",
                "route_back_target": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {
                        "path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                        "present": True,
                        "valid": True,
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "present": True,
                        "valid": True,
                    },
                }
            },
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T010000Z_publication_eval_record.json",
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_path.read_text(encoding="utf-8"),
            study_id=study_id,
            quest_id=quest_id,
            eval_id="publication-eval::002::quest::2026-05-24T01:00:00+00:00::ai-reviewer",
            emitted_at="2026-05-24T01:00:00+00:00",
        ),
    )
    stale_response_record_ref = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T010000Z_publication_eval_record.json"
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "requests"
            / "ai_reviewer"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    )
    assert not dispatch_path.exists()
    dispatch = result["owner_callable_adapters"][0]
    expected_refs = [str(manuscript_path.resolve()), str(review_manuscript_path.resolve())]
    assert result["request_tasks"][0]["dispatch_status"] == "transition_request_pending"
    assert request["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert request["request_lifecycle"]["required_currentness_refs"] == expected_refs
    assert request["request_lifecycle"]["stale_record_ref"] == str(
        (study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
    )
    assert request["request_lifecycle"]["source_ref"] == str(source_ref.resolve())
    assert request["source_workflow_ref"]["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert dispatch["source_action"]["required_currentness_refs"] == expected_refs
    assert dispatch["source_action"]["stale_record_ref"] == str(stale_record_ref.resolve())
    assert dispatch["source_action"]["record_only_surface"] is True
    assert dispatch["source_action"]["publication_eval_latest_write_allowed"] is False
    assert dispatch["source_action"]["controller_decision_write_allowed"] is False
    assert dispatch["surface"] == "mas_domain_progress_transition_request_projection"
    assert dispatch["mas_creates_owner_callable_carrier"] is False
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )
