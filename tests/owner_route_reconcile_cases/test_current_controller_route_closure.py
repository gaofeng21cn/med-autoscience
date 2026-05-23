from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
