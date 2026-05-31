from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_quality_repair_writer_handoff_requires_typed_closeout_packet(tmp_path: Path) -> None:
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"

    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=f"quest-{study_id}",
        schema_version=1,
        source_eval_id="publication-eval::dm003",
        source_eval_artifact_path="artifacts/publication_eval/latest.json",
        source_summary_artifact_path="artifacts/eval_hygiene/evaluation_summary/latest.json",
        repair_execution_evidence_path=profile.studies_root / study_id / "artifacts/controller/repair_execution_evidence/latest.json",
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "controller_route_context": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            },
        },
    )

    closeout_contract = handoff["required_closeout_packet"]
    assert closeout_contract["typed_closeout_required_for_completion"] is True
    assert closeout_contract["free_text_closeout_accepted"] is False
    assert "stage_attempt_closeout_packet" in closeout_contract["accepted_surface_kinds"]
    assert closeout_contract["required_user_stage_log_field"] == "paper_stage_log"
    assert closeout_contract["accepted_user_stage_log_fields"] == [
        "paper_stage_log",
        "user_stage_log",
        "stage_log_summary",
    ]
    assert closeout_contract["required_user_stage_log_fields"] == [
        "stage_name",
        "problem_summary",
        "stage_goal",
        "stage_work_done",
        "paper_work_done",
        "changed_stage_surfaces",
        "changed_paper_surfaces",
        "outcome",
        "remaining_blockers",
        "duration",
        "token_usage",
        "cost",
        "usage_refs",
        "cost_refs",
        "evidence_refs",
    ]
    assert closeout_contract["user_stage_log_policy"] == {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "summary_scope": "stage_log_read_model_only",
        "paper_body_included": False,
        "paper_body_target": False,
        "internal_review_language_allowed_in_paper_body": False,
        "quality_verdict_authorized": False,
        "submission_readiness_authorized": False,
    }
    assert handoff["prompt_contract"]["required_closeout_packet"] == closeout_contract
    assert "exactly one JSON object" in handoff["terminal_output_instruction"]
    assert "Include paper_stage_log" in handoff["terminal_output_instruction"]
    assert "stage_progress_log.user_stage_log" in handoff["terminal_output_instruction"]
    assert handoff["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/quality_repair_batch/latest.json"
    )
    assert handoff["refs"]["request_path"].endswith(
        "artifacts/supervision/requests/quality_repair_batch/latest.json"
    )


def test_execute_dispatch_treats_quality_repair_writer_handoff_as_dispatchable_not_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["work_unit_fingerprint"] = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route["source_fingerprint"] = "truth-source::dm003::medical-prose"
    route["idempotency_key"] = "owner-route::dm003::medical-prose"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_work_unit": {
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
        },
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}
    closeout_contract = importlib.import_module(
        "med_autoscience.controllers.default_executor_closeout_contract"
    ).default_executor_typed_closeout_contract(action_type="run_quality_repair_batch")

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "next_owner": "write",
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "required_closeout_packet": closeout_contract,
                    "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
                },
            }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1, result
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["paper_work_unit_lifecycle"]["owner"] == "quality_repair_batch"
    assert execution["paper_work_unit_lifecycle"]["allowed_writes"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "artifacts/controller/quality_repair_batch/latest.json",
        "artifacts/controller/repair_execution_evidence/latest.json",
        "artifacts/supervision/requests/ai_reviewer/latest.json",
        "artifacts/controller/gate_replay_requests/latest.json",
    ]
    assert "artifacts/publication_eval/latest.json" in execution["paper_work_unit_lifecycle"]["forbidden_writes"]
    assert execution["paper_work_unit_lifecycle"]["completion_proof"][
        "requires_owner_receipt_or_typed_blocker"
    ] is True
    assert execution["writer_worker_handoff"]["next_executable_owner"] == "write"
    assert execution["paper_stage_log"]["surface_kind"] == "mas_paper_facing_stage_log_summary"
    assert execution["paper_stage_log"]["stage_name"] == "medical_prose_write_repair"
    assert execution["paper_stage_log"]["current_owner"] == "write"
    assert execution["paper_stage_log"]["status"] == "available"
    assert execution["paper_stage_log"]["language_boundary"]["paper_body_included"] is False
    assert execution["paper_stage_log"]["authority"]["can_write_paper"] is False
    assert execution["paper_stage_log"]["authority"]["can_authorize_quality_verdict"] is False
    closeout_contract = execution["writer_worker_handoff"]["required_closeout_packet"]
    assert closeout_contract["typed_closeout_required_for_completion"] is True
    assert closeout_contract["free_text_closeout_accepted"] is False
    assert "stage_attempt_closeout_packet" in closeout_contract["accepted_surface_kinds"]
    assert closeout_contract["required_user_stage_log_field"] == "paper_stage_log"
    assert "paper_work_done" in closeout_contract["required_user_stage_log_fields"]
    assert "terminal_output_instruction" in execution["writer_worker_handoff"]
    assert "exactly one JSON object" in execution["writer_worker_handoff"]["terminal_output_instruction"]
    assert called["study_id"] == study_id
    assert called["quest_id"] == f"quest-{study_id}"
    route_context = called["authority_route_context"]
    assert route_context["controller_action_type"] == "run_quality_repair_batch"
    assert route_context["work_unit_id"] == "medical_prose_write_repair"


def test_execute_dispatch_wraps_claim_alignment_route_as_controller_context(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route.update(
        {
            "failure_signature": "claim_evidence_alignment_required",
            "owner_reason": "claim_evidence_alignment_required",
            "work_unit_fingerprint": "claim_evidence_alignment_repair::C1_missing",
            "idempotency_key": "owner-route::dm002::claim-evidence-alignment",
            "source_refs": {
                "work_unit_id": "claim_evidence_alignment_repair",
                "blocked_reason": "claim_evidence_alignment_required",
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "claim-evidence map and evidence ledger alignment or "
            "typed blocker:claim_evidence_alignment_required"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "reason": "claim_evidence_alignment_required",
        "route_target": "write",
        "work_unit_fingerprint": "claim_evidence_alignment_repair::C1_missing",
        "next_work_unit": "claim_evidence_alignment_repair",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    route_context = called["authority_route_context"]
    assert route_context["controller_route_context"]["work_unit_id"] == "claim_evidence_alignment_repair"
    assert route_context["controller_route_context"]["controller_action_type"] == "run_quality_repair_batch"
    assert route_context["controller_route_context"]["source_eval_id"] is None
    assert route_context["current_owner_route"]["owner_reason"] == "claim_evidence_alignment_required"


def test_execute_dispatch_wraps_current_manuscript_claim_alignment_route_as_controller_context(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    work_unit_id = "current_manuscript_claim_evidence_alignment_repair"
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route.update(
        {
            "failure_signature": "claim_evidence_alignment_required",
            "owner_reason": "claim_evidence_alignment_required",
            "work_unit_fingerprint": f"{work_unit_id}::dm003",
            "idempotency_key": "owner-route::dm003::current-manuscript-claim-evidence",
            "source_refs": {
                "work_unit_id": work_unit_id,
                "blocked_reason": "claim_evidence_alignment_required",
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "current manuscript claim-evidence map and evidence ledger alignment or "
            "typed blocker:claim_evidence_alignment_required"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "reason": "claim_evidence_alignment_required",
        "route_target": "write",
        "work_unit_fingerprint": f"{work_unit_id}::dm003",
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "next_work_unit": work_unit_id,
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    route_context = called["authority_route_context"]
    assert route_context["controller_route_context"]["work_unit_id"] == work_unit_id
    assert route_context["controller_route_context"]["controller_action_type"] == "run_quality_repair_batch"
    assert route_context["controller_route_context"]["source_eval_id"] is None
    assert route_context["current_owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
