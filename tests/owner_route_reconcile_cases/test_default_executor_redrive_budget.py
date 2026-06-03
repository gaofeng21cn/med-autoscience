from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_receipt_consumption,
)
from med_autoscience.controllers.owner_route_reconcile_parts.controller_followthrough_actions import (
    action_from_controller_route,
)

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _quality_repair_owner_route(study_id: str = "002-dm-china-us-mortality-attribution") -> dict:
    source_eval_id = "publication-eval::dm002::current-inputs::20260531T192047Z"
    return {
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::current-write-repair",
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
                "source_eval_id": source_eval_id,
                "work_unit_fingerprint": "domain-transition::route_back_same_line::current-write-repair",
                "work_unit_id": f"{study_id}::current-write-repair",
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
            },
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
            "source_eval_id": source_eval_id,
            "work_unit_fingerprint": "domain-transition::route_back_same_line::current-write-repair",
            "work_unit_id": f"{study_id}::current-write-repair",
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
        },
        "idempotency_key": f"owner-route::{study_id}::current-write-repair",
    }


def test_controller_followthrough_action_mapper_accepts_structured_controller_actions() -> None:
    action = action_from_controller_route(
        {
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "route_target": "review",
            "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::current",
        }
    )

    assert action is not None
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["owner"] == "ai_reviewer"
    assert action["publication_eval_latest_write_allowed"] is False
    assert action["paper_package_mutation_allowed"] is False


def _nonconsumable_execution(*, study_root: Path, owner_route: dict, execution_id: str) -> dict:
    return {
        "surface": "default_executor_dispatch_execution",
        "schema_version": 1,
        "study_id": study_root.name,
        "quest_id": study_root.name,
        "action_type": "run_quality_repair_batch",
        "execution_status": "executed",
        "execution_id": execution_id,
        "idempotency_key": owner_route["idempotency_key"],
        "current_owner_route": owner_route,
        "prompt_contract": {"owner_route": owner_route},
        "owner_result": {
            "status": "executed",
            "ok": True,
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                },
                "changed_artifact_refs": [{"path": str(study_root / "paper" / "claim_evidence_map.json")}],
            },
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
        },
    }


def _write_repeated_nonconsumable_execution(study_root: Path, owner_route: dict) -> None:
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executions": [],
            "execution_ledger": [
                _nonconsumable_execution(
                    study_root=study_root,
                    owner_route=owner_route,
                    execution_id=f"execution::{study_root.name}::run_quality_repair_batch::first",
                ),
                _nonconsumable_execution(
                    study_root=study_root,
                    owner_route=owner_route,
                    execution_id=f"execution::{study_root.name}::run_quality_repair_batch::second",
                ),
            ],
        },
    )


def test_default_executor_repeated_nonconsumable_closeout_consumes_typed_stop_loss(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = _quality_repair_owner_route()
    _write_repeated_nonconsumable_execution(study_root, owner_route)

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["blocked_reason"] == "progress_first_owner_redrive_budget_exhausted"
    assert receipt["nonconsumable_closeout_repeat_count"] == 2
    assert receipt["nonconsumable_closeout_reason"] == "manuscript_story_surface_delta_missing"
    assert receipt["typed_blocker"]["next_escalation"] == "mechanism_repair_owner"
    assert receipt["typed_blocker"]["next_owner"] == "med-autoscience"
    assert receipt["next_action"] == "honor_typed_blocker_without_redrive"


def test_default_executor_paper_review_story_surface_closeout_preempts_redrive_budget(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = _quality_repair_owner_route()
    _write_repeated_nonconsumable_execution(study_root, owner_route)
    stage_packet_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/stage-packet.json"
    )
    _write_json(
        study_root / "paper" / "review" / "domain_stage_closeout_sat_story_20260601T015622Z.json",
        {
            "surface_kind": "domain_stage_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_story",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": stage_packet_ref,
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "action_type": "run_quality_repair_batch",
            "action_id": "quality-repair-writer-handoff::dm002::current-inputs",
            "owner": "write",
            "status": "completed_for_write_owner_idempotent",
            "required_output_surface": "canonical manuscript story-surface delta",
            "owner_route_basis": owner_route["source_refs"]["owner_route_currentness_basis"],
            "domain_completion_claimed": False,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "artifact_delta": {
                "status": "already_materialized_for_stage_packet",
                "story_surface_delta_present": True,
                "meaningful_artifact_delta_this_attempt": False,
                "changed_artifact_refs": [
                    {
                        "path": (
                            "studies/002-dm-china-us-mortality-attribution/paper/review/"
                            "manuscript_story_repair_story_surface_sat_story.json"
                        ),
                        "artifact_role": "write_owner_story_surface_delta_idempotency_receipt",
                    },
                    {
                        "path": (
                            "studies/002-dm-china-us-mortality-attribution/paper/review/"
                            "domain_stage_closeout_sat_story_20260601T015622Z.json"
                        ),
                        "artifact_role": "domain_stage_closeout_packet",
                    },
                ],
                "current_story_surface_refs": [
                    {"path": "studies/002-dm-china-us-mortality-attribution/paper/draft.md"},
                    {"path": "studies/002-dm-china-us-mortality-attribution/paper/build/review_manuscript.md"},
                ],
                "manuscript_surface_hygiene": {
                    "status": "clear_for_current_story_surface_delta",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "blockers": [],
                },
            },
            "domain_owner_evidence": {
                "this_attempt_resolution": "idempotent_closeout_over_current_story_surface_delta",
                "manuscript_surface_hygiene_status": "clear",
                "story_surface_delta_present": True,
                "gate_replay_done": True,
                "ai_reviewer_recheck_required": True,
                "ai_reviewer_recheck_done": True,
            },
            "closeout_refs": [
                "studies/002-dm-china-us-mortality-attribution/paper/review/"
                "domain_stage_closeout_sat_story_20260601T015622Z.json",
                "studies/002-dm-china-us-mortality-attribution/paper/review/"
                "manuscript_story_repair_story_surface_sat_story.json",
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["action_type"] == "run_quality_repair_batch"
    assert receipt["execution_status"] == "executed"
    assert receipt["owner_result_status"] == "completed_for_write_owner_idempotent"
    assert receipt["repair_execution_evidence_status"] == "already_materialized_for_stage_packet"
    assert receipt["changed_artifact_ref_count"] == 2
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"
    assert "blocked_reason" not in receipt


def test_consumed_write_closeout_projects_current_ai_reviewer_controller_followthrough(
    monkeypatch,
    tmp_path: Path,
) -> None:
    followthrough = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_controller_followthrough"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    source_eval_id = "publication-eval::dm002::current-inputs::20260601"
    writer_publication_eval = {
        "schema_version": 1,
        "eval_id": source_eval_id,
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::current-write-repair",
                "next_work_unit": {
                    "unit_id": "current-write-repair",
                    "lane": "write",
                    "summary": "Repair the current manuscript story surface.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", writer_publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "source_eval_id": source_eval_id,
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
            },
        },
    )
    status = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": writer_publication_eval,
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {"unit_id": "current-write-repair", "lane": "write"},
            "typed_blocker": None,
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-dm002-followthrough",
            "canonical_runtime_action": "request_opl_stage_attempt",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-followthrough",
            "source_signature": "truth-source-dm002-followthrough",
        },
    }
    progress = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status["study_truth_snapshot"],
    }
    ai_work_unit = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "dm002-current-ai-reviewer-route",
            "decision_type": "continue_same_line",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{ai_work_unit}",
            "next_work_unit": {
                "unit_id": ai_work_unit,
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record.",
            },
        },
    )

    action = followthrough.action_after_consumed_receipt(
        study_id=study_id,
        quest_id=study_id,
        study_root=study_root,
        publication_eval_payload=writer_publication_eval,
        consumed_receipt={
            "status": "consumed",
            "receipt_kind": "default_executor_execution",
            "action_type": "run_quality_repair_batch",
            "execution_status": "executed",
            "next_action": "do_not_redrive_consumed_owner_route",
        },
    )

    assert action is not None
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["owner"] == "ai_reviewer"
    assert action["next_work_unit"] == ai_work_unit
    assert action["controller_work_unit_id"] == ai_work_unit
    assert action["request_owner"] == "ai_reviewer"
    assert action["reason"] == "domain_transition_ai_reviewer_re_eval"


def test_scan_consumed_write_closeout_projects_current_ai_reviewer_followthrough(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    source_eval_id = "publication-eval::dm002::current-inputs::20260601"
    publication_eval = {
        "schema_version": 1,
        "eval_id": source_eval_id,
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::current-write-repair",
                "next_work_unit": {
                    "unit_id": "current-write-repair",
                    "lane": "write",
                    "summary": "Repair the current manuscript story surface.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    ai_work_unit = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    status = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {"unit_id": "current-write-repair", "lane": "write"},
            "typed_blocker": None,
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-dm002-followthrough",
            "canonical_runtime_action": "request_opl_stage_attempt",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-followthrough",
            "source_signature": "truth-source-dm002-followthrough",
        },
    }
    progress = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status, progress, study_id, publication_eval),
    )

    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    owner_route = before_receipt["studies"][0]["action_queue"][0]["owner_route"]
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "dm002-current-ai-reviewer-route",
            "decision_type": "continue_same_line",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{ai_work_unit}",
            "next_work_unit": {
                "unit_id": ai_work_unit,
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record.",
            },
        },
    )
    _write_repeated_nonconsumable_execution(study_root, owner_route)
    _write_json(
        study_root / "paper" / "review" / "domain_stage_closeout_sat_story_20260601T015622Z.json",
        {
            "surface_kind": "domain_stage_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_story",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "status": "completed_for_write_owner_idempotent",
            "required_output_surface": "canonical manuscript story-surface delta",
            "owner_route_basis": owner_route["source_refs"]["owner_route_currentness_basis"],
            "artifact_delta": {
                "status": "already_materialized_for_stage_packet",
                "story_surface_delta_present": True,
                "changed_artifact_refs": [
                    {
                        "path": (
                            "studies/002-dm-china-us-mortality-attribution/paper/review/"
                            "manuscript_story_repair_story_surface_sat_story.json"
                        )
                    }
                ],
                "manuscript_surface_hygiene": {
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "blockers": [],
                },
            },
        },
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["status"] == "consumed"
    assert receipt["consumption_mode"] == "current_controller_followthrough"
    assert receipt["followthrough_to_action_type"] == "return_to_ai_reviewer_workflow"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["next_work_unit"] == ai_work_unit
    assert action["controller_work_unit_id"] == ai_work_unit
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def test_default_executor_missing_closeout_refs_consumes_typed_blocker_without_redrive(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = _quality_repair_owner_route()
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_missing_refs.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "action_type": "run_quality_repair_batch",
            "stage_attempt_id": "sat_missing_refs",
            "closeout_id": "stage-attempt-closeout::sat_missing_refs::completed-without-refs",
            "status": "completed",
            "owner_route_basis": owner_route["source_refs"]["owner_route_currentness_basis"],
            "required_closeout_packet": {"required_ref_field": "closeout_refs"},
            "closeout_refs": [],
            "artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
                "story_surface_delta_present": False,
                "changed_artifact_refs": [],
            },
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["blocked_reason"] == "typed_closeout_packet_required"
    assert receipt["typed_blocker"]["next_owner"] == "one-person-lab"
    assert receipt["next_action"] == "honor_typed_blocker_without_redrive"
    assert redrive == {}


def test_scan_routes_repeated_nonconsumable_quality_repair_to_mechanism_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::ai-reviewer-routeback",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [
            {
                "action_id": "route-back-same-line-write-paper-repair-dm002",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dm002_write_repair",
                "next_work_unit": {"unit_id": "dm002_write_repair", "lane": "write"},
            }
        ],
    }
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(publication_eval_path, publication_eval)
    status = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-after-repeated-nonconsumable",
            "canonical_runtime_action": "observe_runtime",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "source_signature": "truth-snapshot::dm002-repeated-nonconsumable",
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {"unit_id": "dm002_write_repair", "lane": "write"},
            "typed_blocker": None,
        },
    }
    progress = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status["study_truth_snapshot"],
    }
    monkeypatch.setattr(scan, "_read_study_projection_inputs", lambda **_: (status, progress, study_id, publication_eval))
    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    owner_route = before_receipt["studies"][0]["action_queue"][0]["owner_route"]
    _write_repeated_nonconsumable_execution(study_root, owner_route)

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["blocked_reason"] == "progress_first_owner_redrive_budget_exhausted"
    assert study["next_owner"] == "med-autoscience"
    assert study["default_executor_execution_receipt_consumption"]["typed_blocker"]["next_escalation"] == (
        "mechanism_repair_owner"
    )


def test_scan_routes_stale_redrive_blocker_after_deliverable_delta_keeps_owner_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::current-inputs::after-delta",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [
            {
                "action_id": "route-back-current-write-after-delta",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::current-write-after-delta",
                "next_work_unit": {
                    "unit_id": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                    "lane": "write",
                },
            }
        ],
    }
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(publication_eval_path, publication_eval)
    truth_snapshot = {
        "truth_epoch": "truth-event-000035-after-delta",
        "source_signature": "truth-snapshot::after-deliverable-delta",
    }
    status = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "active",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-after-delta",
            "canonical_runtime_action": "recover_runtime",
            "attempt_state": "recovering",
            "blocking_reasons": ["quest_marked_running_but_no_live_session"],
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": truth_snapshot,
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                "lane": "write",
            },
            "typed_blocker": None,
        },
    }
    progress = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": truth_snapshot,
        "progress_first_monitoring_summary": {
            "surface": "progress_first_monitoring_summary",
            "schema_version": 1,
            "authority": "refs_only_observability",
            "study_id": study_id,
            "running_provider_attempt": False,
            "execution_state_kind": "typed_blocker",
            "owner_action_current": True,
            "next_owner": "write",
            "route_target": "review",
            "controller_action": "run_quality_repair_batch",
            "next_work_unit": {
                "unit_id": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                "lane": "review",
            },
            "typed_blocker": {
                "blocker_type": "progress_first_owner_redrive_budget_exhausted",
                "owner": "med-autoscience",
            },
            "current_blockers": ["progress_first_owner_redrive_budget_exhausted"],
            "latest_terminal_stage": {
                "stage_id": "domain_owner/default-executor-dispatch",
                "action_type": "run_quality_repair_batch",
                "status": "executed",
                "stage_name": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                "problem_summary": "run_quality_repair_batch produced manuscript review ledgers.",
                "stage_goal": "Produce canonical manuscript story-surface delta.",
                "outcome": "executed",
                "progress_delta_classification": "deliverable_progress",
                "stage_work_done": ["Updated the evidence ledger."],
                "changed_stage_surfaces": [
                    str(study_root / "paper" / "claim_evidence_map.json"),
                    str(study_root / "paper" / "evidence_ledger.json"),
                    str(study_root / "paper" / "review" / "review_ledger.json"),
                ],
                "changed_paper_surfaces": [
                    str(study_root / "paper" / "claim_evidence_map.json"),
                    str(study_root / "paper" / "evidence_ledger.json"),
                    str(study_root / "paper" / "review" / "review_ledger.json"),
                ],
                "remaining_blockers": [],
                "evidence_refs": [
                    "artifacts/controller/quality_repair_batch/latest.json",
                    "artifacts/publication_eval/latest.json",
                ],
                "semantic_completeness": {"status": "complete", "missing_fields": []},
                "terminal_closeout_semantic_completeness": {
                    "status": "complete",
                    "progress_delta_classification": "deliverable_progress",
                },
            },
        },
    }
    monkeypatch.setattr(scan, "_read_study_projection_inputs", lambda **_: (status, progress, study_id, publication_eval))
    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    owner_route = before_receipt["studies"][0]["action_queue"][0]["owner_route"]
    _write_repeated_nonconsumable_execution(study_root, owner_route)

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["blocked_reason"] == "progress_first_owner_redrive_budget_exhausted"
    assert receipt["stale_blocker_resolution"]["status"] == "superseded"
    assert study["blocked_reason"] != "progress_first_owner_redrive_budget_exhausted"
    assert study["next_owner"] == "write"
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    assert study["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert study["current_execution_envelope"]["typed_blocker"] is None


def test_scan_routes_live_provider_attempt_supersedes_stale_redrive_handoff_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::current-inputs::live-attempt",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::live-current-write",
                "next_work_unit": {"unit_id": "live-current-write", "lane": "write"},
            }
        ],
    }
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(publication_eval_path, publication_eval)
    status = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "active",
        "active_run_id": "opl-stage-attempt://sat-live",
        "publication_eval": publication_eval,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-live-attempt",
            "canonical_runtime_action": "observe_runtime",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-live-attempt",
            "source_signature": "truth-snapshot::live-attempt",
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {"unit_id": "live-current-write", "lane": "write"},
            "typed_blocker": None,
        },
    }
    progress = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "current_stage": "managed_runtime_recovering",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": "opl-stage-attempt://sat-live", "health_status": "running"},
        "study_truth_snapshot": status["study_truth_snapshot"],
    }
    live_attempt = {
        "surface_kind": "opl_current_control_state_provider_attempt",
        "source": "opl_family_runtime_attempt_inspect",
        "active_run_id": "opl-stage-attempt://sat-live",
        "active_stage_attempt_id": "sat-live",
        "active_workflow_id": "wf-live",
        "running_provider_attempt": True,
        "task_kind": "domain_owner/default-executor-dispatch",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": f"{study_id}::current-write-repair",
        "runtime_health": {
            "health_status": "running",
            "runtime_liveness_status": "live",
            "provider_status": "running",
        },
    }
    monkeypatch.setattr(scan, "_read_study_projection_inputs", lambda **_: (status, progress, study_id, publication_eval))
    monkeypatch.setattr(scan.opl_provider_attempts, "current_provider_readiness", lambda **_: {})
    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    owner_route = before_receipt["studies"][0]["action_queue"][0]["owner_route"]
    _write_repeated_nonconsumable_execution(study_root, owner_route)
    live_attempt["work_unit_id"] = owner_route["source_refs"]["work_unit_id"]
    monkeypatch.setattr(scan.opl_provider_attempts, "live_provider_attempt_for_study", lambda **_: live_attempt)

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["blocked_reason"] == "progress_first_owner_redrive_budget_exhausted"
    assert receipt["stale_blocker_resolution"]["status"] == "superseded"
    assert receipt["stale_blocker_resolution"]["basis"] == "live_provider_attempt_running"
    assert study["blocked_reason"] is None
    assert study["next_owner"] == "supervisor_only/live_provider_attempt"
    assert study["domain_authority_handoff"]["status"] == "owner_route_ready"
    assert study["domain_authority_handoff"]["typed_blocker"] is None
    assert study["current_execution_envelope"]["state_kind"] == "running_provider_attempt"
    assert study["current_execution_envelope"]["typed_blocker"] is None
