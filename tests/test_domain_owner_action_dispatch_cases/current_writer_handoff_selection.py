from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_defaults_to_current_writer_handoff_after_consumed_reviewer_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True, exist_ok=True)
    source_eval_id = "publication-eval::003::current-writer-handoff"
    work_unit_id = "dpcc_medical_journal_quality_story_surface_repair"
    writer_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    writer_route.update(
        {
            "truth_epoch": source_eval_id,
            "route_epoch": source_eval_id,
            "runtime_health_epoch": "runtime-health::003::current-writer-handoff",
            "work_unit_fingerprint": "domain-transition::dm003::current-writer-handoff",
            "source_fingerprint": "truth-source::003::current-writer-handoff",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "idempotency_key": "quality-repair-writer-handoff::003::current",
            "source_refs": {
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": "domain-transition::dm003::current-writer-handoff",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=writer_route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["required_closeout_packet"] = {
        "schema_version": 1,
        "action_type": "run_quality_repair_batch",
        "required": True,
        "terminal_output_instruction": "Emit a typed default executor closeout packet.",
    }
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": source_eval_id,
        "next_work_unit": {"unit_id": work_unit_id, "lane": "write"},
    }
    dispatch_payload["prompt_contract"].update(
        {
            "medical_claim_authoring_allowed": True,
            "required_closeout_packet": dispatch_payload["required_closeout_packet"],
            "next_work_unit": {"unit_id": work_unit_id, "lane": "write"},
            "allowed_write_surfaces": [
                "paper/draft.md",
                "paper/build/review_manuscript.md",
                "paper/claim_evidence_map.json",
                "paper/evidence_ledger.json",
                "paper/review/**",
            ],
            "forbidden_surfaces": [
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": source_eval_id, "study_id": study_id, "quest_id": quest_id},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "handoff_ready",
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "next_owner": "write",
            "writer_worker_handoff": dispatch_payload,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "request_kind": "run_quality_repair_batch",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "owner_route": writer_route,
        },
    )
    stale_reviewer_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    stale_reviewer_route.update(
        {
            "truth_epoch": source_eval_id,
            "route_epoch": source_eval_id,
            "runtime_health_epoch": "runtime-health::003::stale-reviewer",
            "work_unit_fingerprint": "domain-transition::dm003::stale-reviewer",
            "source_fingerprint": "truth-source::003::stale-reviewer",
            "idempotency_key": "owner-route::003::stale-reviewer",
            "source_refs": {
                "source_eval_id": source_eval_id,
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            },
        }
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": stale_reviewer_route,
                    "domain_transition": {
                        "decision_type": "ai_reviewer_re_eval",
                        "route_target": "review",
                        "controller_action": "return_to_ai_reviewer_workflow",
                        "next_work_unit": {
                            "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "lane": "review",
                        },
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "eval_id": source_eval_id,
                        },
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
        consumer_payload={
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [dispatch_payload],
        },
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "current_writer_handoff"
    assert execution["writer_worker_handoff"]["action_type"] == "run_quality_repair_batch"


def test_explicit_writer_handoff_is_rejected_when_fresh_progress_ticket_points_to_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    persisted = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.persisted_dispatches"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    source_eval_id = "publication-eval::003::stale-writer-handoff"
    writer_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    writer_route.update(
        {
            "truth_epoch": source_eval_id,
            "route_epoch": source_eval_id,
            "runtime_health_epoch": "runtime-health::003::stale-writer-handoff",
            "work_unit_fingerprint": "domain-transition::003::stale-writer-handoff",
            "source_fingerprint": "truth-source::003::stale-writer-handoff",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "idempotency_key": "quality-repair-writer-handoff::003::stale",
            "source_refs": {
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "domain-transition::003::stale-writer-handoff",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=writer_route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": source_eval_id,
        "next_work_unit": {"unit_id": "medical_prose_write_repair", "lane": "write"},
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "handoff_ready",
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "next_owner": "write",
            "writer_worker_handoff": dispatch_payload,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "request_kind": "run_quality_repair_batch",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "owner_route": writer_route,
        },
    )
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "finalize",
                "allowed_action": "run_gate_clearing_batch",
                "work_unit": {
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                },
            },
        },
    )

    dispatches = persisted.explicit_action_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=("run_quality_repair_batch",),
        supported_action_types=frozenset({"run_quality_repair_batch"}),
        dispatch_relative_root=module.DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
        require_current_authority=True,
    )

    assert dispatches == []
