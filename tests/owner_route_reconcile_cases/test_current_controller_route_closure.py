from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_projects_current_controller_ai_reviewer_route_over_runtime_recovery_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    work_unit_id = "ai_reviewer_medical_prose_quality_review"
    work_unit_fingerprint = f"domain-transition::ai_reviewer_re_eval::{work_unit_id}"
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "dm002-current-ai-reviewer-route",
            "decision_type": "continue_same_line",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review against the current package.",
            },
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-dm002-recovery",
            "canonical_runtime_action": "recover_runtime",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "execution_owner_guard": {"supervisor_only": True},
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-current-review",
            "source_signature": "truth-source-dm002-current-review",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": None,
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "external_supervisor_required",
            "blocked_reason": "runtime_recovery_not_authorized",
            "next_owner": "one-person-lab",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert action["next_work_unit"] == work_unit_id
    assert action["executable_work_unit"] == work_unit_id
    assert action["controller_work_unit_id"] == work_unit_id
    assert action["controller_route"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert study["why_not_applied"] == "domain_transition_ai_reviewer_re_eval"
    assert study["blocked_reason"] == "domain_transition_ai_reviewer_re_eval"
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["owner_reason"] == "domain_transition_ai_reviewer_re_eval"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["owner_route"]["owner_route_attempt_protocol"]["dispatchable"] is True


def test_current_controller_route_stays_open_for_unsettled_authority_lifecycle(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    work_unit_fingerprint = "publication-blockers::authority-sync"
    source_eval_id = f"publication-eval::{study_id}::{quest_id}::2026-05-12T10:36:52+00:00"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": source_eval_id,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                    "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                },
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "authority-sync-route",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_opl_stage_attempt"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Regenerate submission authority signatures, then replay the publication gate.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "status": "done",
            "work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
            },
            "unit_statuses": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "skipped_authority_not_settled"},
            ],
            "gate_replay_status": "clear",
        },
    )

    route = module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["work_unit_id"] == "submission_authority_sync_closure"
    assert route["work_unit_fingerprint"] == work_unit_fingerprint


def test_current_controller_route_accepts_domain_transition_without_publication_action(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    work_unit_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "domain-transition-ai-reviewer-route",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "ai_reviewer_recheck",
                "lane": "review",
                "summary": "Return current manuscript and evidence refs to the AI reviewer workflow.",
            },
        },
    )

    route = module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["route_target"] == "review"
    assert route["work_unit_id"] == "ai_reviewer_recheck"
    assert route["work_unit_fingerprint"] == work_unit_fingerprint


def test_current_controller_route_ignores_non_json_turn_closeout_artifact_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    work_unit_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    workspace_root = study_root.parent.parent
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "study_id": study_id,
        "quest_id": quest_id,
        "runtime_context_refs": {
            "runtime_escalation_ref": str(
                quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
            ),
        },
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "domain-transition-ai-reviewer-route",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "ai_reviewer_recheck",
                "lane": "review",
                "summary": "Return current manuscript and evidence refs to the AI reviewer workflow.",
            },
        },
    )
    figure_ref = "../../../studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/figures/generated/F1_cohort_flow.png"
    figure_path = quest_root / figure_ref
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    _write_json(
        quest_root / "artifacts" / "runtime" / "turn_closeouts" / "mas-run-003-ai-reviewer.json",
        {
            "schema_version": 1,
            "quest_id": quest_id,
            "run_id": "mas-run-003-ai-reviewer",
            "status": "completed",
            "completed_at": "2026-05-15T15:20:00Z",
            "meaningful_artifact_delta": True,
            "artifact_refs": [figure_ref],
            "blocked_reason": None,
            "next_owner": None,
        },
    )

    route = module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["route_target"] == "review"
    assert route["work_unit_id"] == "ai_reviewer_recheck"
    assert route["work_unit_fingerprint"] == work_unit_fingerprint


def test_current_controller_route_accepts_bundle_stage_domain_transition_without_publication_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    work_unit_fingerprint = "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "domain-transition-bundle-stage-route",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_opl_stage_attempt"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Synchronize submission authority and package closure for the bundle-stage.",
            },
        },
    )

    route = module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["route_target"] == "finalize"
    assert route["work_unit_id"] == "submission_authority_sync_closure"
    assert route["work_unit_fingerprint"] == work_unit_fingerprint


def test_current_controller_route_canonicalizes_publication_gate_replay_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "dm003-stale-writer-action-gate-replay",
            "decision_type": "route_back_same_line",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "publication_gate",
                "summary": "Replay the publication gate after the current AI reviewer record.",
            },
        },
    )

    route = module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["work_unit_id"] == work_unit_id
    assert route["work_unit_fingerprint"] == work_unit_fingerprint
    assert route["controller_actions"] == ["run_gate_clearing_batch"]


def test_current_controller_route_ignores_successfully_closed_publication_work_unit(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    work_unit_fingerprint = "publication-blockers::authority-sync"
    source_eval_id = f"publication-eval::{study_id}::{quest_id}::2026-05-12T10:36:52+00:00"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": source_eval_id,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                    "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                },
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "authority-sync-route",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_opl_stage_attempt"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Regenerate submission authority signatures, then replay the publication gate.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "status": "done",
            "work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
            },
            "unit_statuses": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "updated"},
            ],
            "gate_replay_status": "clear",
        },
    )

    assert module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    ) is None


def test_current_controller_route_closes_bundle_stage_work_unit_from_package_closure_evidence(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    work_unit_fingerprint = "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    source_eval_id = f"publication-eval::{study_id}::{quest_id}::2026-05-13T16:15:21+00:00"
    decision_id = f"study-decision::{study_id}::{quest_id}::continue_same_line::2026-05-15T05:28:48+00:00"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    workspace_root = study_root.parent.parent
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": source_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "runtime_context_refs": {
            "runtime_escalation_ref": str(
                quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
            ),
        },
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": decision_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_opl_stage_attempt"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Synchronize submission authority and package closure for the bundle-stage.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "status": "skipped",
            "work_unit": {
                "unit_id": "publication_gate_blocker_review",
                "lane": "review",
            },
            "unit_statuses": [],
            "gate_replay_status": "clear",
        },
    )
    package_closure_ref = (
        "artifacts/reports/package_closure/"
        "20260515T075324Z.submission_authority_sync_closure.json"
    )
    _write_json(
        quest_root / package_closure_ref,
        {
            "schema_version": 1,
            "artifact_kind": "submission_authority_sync_closure",
            "study_id": study_id,
            "quest_id": quest_id,
            "run_id": "mas-run-002-finalize",
            "controller_decision_id": decision_id,
            "work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "fingerprint": work_unit_fingerprint,
            },
            "authority_closure": {
                "status": "closed_for_bundle_stage",
                "publication_gate_status": "clear",
                "publication_gate_allow_write": True,
                "publication_gate_blockers": [],
                "current_required_action": "continue_bundle_stage",
            },
            "submission_minimal_authority": {
                "status": "current",
                "docx_present": True,
                "pdf_present": True,
            },
            "human_facing_delivery": {
                "status": "current",
                "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
            },
        },
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "turn_closeouts" / "mas-run-002-finalize.json",
        {
            "schema_version": 1,
            "quest_id": quest_id,
            "run_id": "mas-run-002-finalize",
            "status": "completed",
            "completed_at": "2026-05-15T07:56:12Z",
            "meaningful_artifact_delta": True,
            "artifact_refs": [package_closure_ref],
            "blocked_reason": None,
            "next_owner": None,
        },
    )

    assert module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    ) is None
