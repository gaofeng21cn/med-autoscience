from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_followthrough_receipt_consumption,
    default_executor_execution_receipt_consumption,
)
from med_autoscience.controllers.owner_route_reconcile_parts.current_controller_followthrough import (
    action_after_consumed_receipt,
)

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_current_controller_decision(
    study_root: Path,
    *,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    action_type: str = "run_quality_repair_batch",
) -> None:
    controller_action = "request_opl_stage_attempt" if action_type == "run_quality_repair_batch" else action_type
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": f"decision::{study_id}::{work_unit_id}",
            "decision_type": "route_back_same_line",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": controller_action}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "write",
                "summary": "Repair the current manuscript story surface.",
            },
        },
    )


def test_scan_consumes_executed_default_executor_receipt_for_current_write_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::ai-reviewer-routeback",
        "study_id": study_id,
        "quest_id": quest_id,
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
                "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript story surface from current analysis evidence.",
                },
            }
        ],
    }
    _write_json(publication_eval_path, publication_eval_payload)
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-after-execution",
            "canonical_runtime_action": "observe_runtime",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "publication_eval": publication_eval_payload,
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "source_signature": "truth-snapshot::81af14f0dc383498de375e6c",
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Repair the manuscript story surface from current analysis evidence.",
            },
            "typed_blocker": None,
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    queued_action = before_receipt["studies"][0]["action_queue"][0]
    consumed_owner_route = queued_action["owner_route"]
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::run_quality_repair_batch::2026-05-22T09:36:26+00:00",
                    "idempotency_key": consumed_owner_route["idempotency_key"],
                    "repeat_suppression_key": consumed_owner_route["source_fingerprint"],
                    "current_owner_route": consumed_owner_route,
                    "prompt_contract": {"owner_route": consumed_owner_route},
                    "owner_result": {
                        "status": "executed",
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "gate_replay_done": True,
                            "ai_reviewer_recheck_required": True,
                            "ai_reviewer_recheck_done": True,
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "draft.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
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
    assert study["action_queue"] == []
    assert result["action_queue"] == []
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["status"] == "consumed"
    assert receipt["receipt_kind"] == "default_executor_execution"
    assert receipt["action_type"] == "run_quality_repair_batch"
    consumed_basis = consumed_owner_route["source_refs"]["owner_route_currentness_basis"]
    assert receipt["work_unit_id"] == "dm002_same_line_publication_paper_repair"
    assert receipt["work_unit_fingerprint"] == consumed_basis["work_unit_fingerprint"]
    assert receipt["owner_route_currentness_basis"]["work_unit_id"] == "dm002_same_line_publication_paper_repair"
    assert receipt["owner_route_currentness_basis"]["work_unit_fingerprint"] == consumed_basis["work_unit_fingerprint"]
    assert receipt["consumed_owner_route_idempotency_key"] == consumed_owner_route["idempotency_key"]
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"
    assert receipt["quality_authorized"] is False
    assert receipt["submission_authorized"] is False
    assert receipt["current_package_write_authorized"] is False


def test_default_executor_consumed_receipt_identity_prevents_same_current_controller_followthrough(
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "dm002_same_line_publication_paper_repair"
    work_unit_fingerprint = "dm002_same_line_publication_paper_repair_20260521"
    owner_route = {
        "route_epoch": "truth-event-000017-bac190eb1c889a78",
        "truth_epoch": "truth-event-000017-bac190eb1c889a78",
        "runtime_health_epoch": "runtime-health-after-execution",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000017-bac190eb1c889a78",
                "runtime_health_epoch": "runtime-health-after-execution",
                "source_eval_id": "publication-eval::dm002::ai-reviewer-routeback",
                "work_unit_fingerprint": work_unit_fingerprint,
                "work_unit_id": work_unit_id,
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
            },
            "study_truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "runtime_health_epoch": "runtime-health-after-execution",
            "source_eval_id": "publication-eval::dm002::ai-reviewer-routeback",
            "work_unit_fingerprint": work_unit_fingerprint,
            "work_unit_id": work_unit_id,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
        },
        "idempotency_key": f"owner-route::{study_id}::{work_unit_id}",
    }
    _write_current_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::run_quality_repair_batch::identity",
                    "idempotency_key": owner_route["idempotency_key"],
                    "repeat_suppression_key": owner_route["work_unit_fingerprint"],
                    "current_owner_route": owner_route,
                    "prompt_contract": {"owner_route": owner_route},
                    "owner_result": {
                        "status": "executed",
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "gate_replay_done": True,
                            "ai_reviewer_recheck_required": True,
                            "ai_reviewer_recheck_done": True,
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "draft.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == work_unit_fingerprint
    assert receipt["owner_route_currentness_basis"]["work_unit_id"] == work_unit_id
    assert receipt["owner_route_currentness_basis"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert (
        action_after_consumed_receipt(
            study_id=study_id,
            quest_id=quest_id,
            study_root=study_root,
            publication_eval_payload={
                "schema_version": 1,
                "eval_id": "publication-eval::dm002::ai-reviewer-routeback",
                "study_id": study_id,
                "quest_id": quest_id,
                "recommended_actions": [
                    {
                        "action_id": "route-back-same-line-write-paper-repair-dm002",
                        "action_type": "route_back_same_line",
                        "route_target": "write",
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "next_work_unit": {"unit_id": work_unit_id, "lane": "write"},
                    }
                ],
            },
            consumed_receipt=receipt,
        )
        is None
    )


def test_scan_does_not_consume_quality_repair_receipt_without_story_surface_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::ai-reviewer-routeback",
        "study_id": study_id,
        "quest_id": quest_id,
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
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_current_publication_hardening_after_ai_reviewer_eval"
                ),
                "next_work_unit": {
                    "unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                    "lane": "write",
                    "summary": "Harden current manuscript story, displays, scope alignment, and citations.",
                },
            }
        ],
    }
    _write_json(publication_eval_path, publication_eval_payload)
    claim_map = study_root / "paper" / "claim_evidence_map.json"
    evidence_ledger = study_root / "paper" / "evidence_ledger.json"
    review_ledger = study_root / "paper" / "review" / "review_ledger.json"
    _write_json(claim_map, {"schema_version": 1})
    _write_json(evidence_ledger, {"schema_version": 1})
    _write_json(review_ledger, {"schema_version": 1})
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-after-ledger-only-execution",
            "canonical_runtime_action": "observe_runtime",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "publication_eval": publication_eval_payload,
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "source_signature": "truth-snapshot::dm002-ledger-only",
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                "lane": "write",
                "summary": "Harden current manuscript story, displays, scope alignment, and citations.",
            },
            "typed_blocker": None,
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    queued_action = before_receipt["studies"][0]["action_queue"][0]
    current_owner_route = queued_action["owner_route"]
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::run_quality_repair_batch::ledger-only",
                    "idempotency_key": current_owner_route["idempotency_key"],
                    "repeat_suppression_key": current_owner_route["source_fingerprint"],
                    "current_owner_route": current_owner_route,
                    "prompt_contract": {"owner_route": current_owner_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "gate_replay_done": True,
                            "ai_reviewer_recheck_required": True,
                            "ai_reviewer_recheck_done": True,
                            "canonical_artifact_delta": {
                                "status": "fresh",
                                "meaningful_artifact_delta": True,
                            },
                            "changed_artifact_refs": [
                                {"path": str(claim_map)},
                                {"path": str(evidence_ledger)},
                                {"path": str(review_ledger)},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
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
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    assert result["action_queue"][0]["action_type"] == "run_quality_repair_batch"
    assert study["default_executor_execution_receipt_consumption"] is None
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]


def test_consumes_provider_hosted_story_surface_closeout_when_stage_packet_route_missing_truth_epoch(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = tmp_path / "studies" / study_id
    source_eval_id = f"publication-eval::{study_id}::ai-reviewer-record::20260602T184032Z"
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "publication-blockers::44f6dbc06c23c5fc"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": source_eval_id,
        "route_epoch": f"quality-repair-writer-handoff::{study_id}::{source_eval_id}",
        "runtime_health_epoch": None,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "current_owner": "quality_repair_batch",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": f"quality-repair-writer-handoff::{study_id}::{work_unit_fingerprint}",
        "source_refs": {
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "blocked_reason": "manuscript_story_surface_delta_missing",
        },
    }
    dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/dd76a2fe47b4c2bcc0771490.json"
    )
    _write_json(
        tmp_path / dispatch_ref,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "next_executable_owner": "write",
            "executor_kind": "codex_cli_default",
            "owner_route": owner_route,
            "prompt_contract": {
                "owner_route": owner_route,
            },
        },
    )
    _write_json(
        study_root / "paper" / "review" / "domain_stage_closeout_sat_story_delta_20260602T202258Z.json",
        {
            "surface_kind": "domain_stage_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "status": "completed_for_write_owner_delta",
            "route_outcome": "write_repair_delta_recorded",
            "stage_attempt_id": "sat_story_delta",
            "stage_packet_ref": dispatch_ref,
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "owner_receipt": {
                "status": "executed",
                "owner": "write",
                "typed_blocker": None,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "artifact_delta": {
                "status": "materialized",
                "meaningful_artifact_delta": True,
                "story_surface_delta_present": True,
                "changed_artifact_refs": [
                    {"path": f"studies/{study_id}/paper/draft.md"},
                    {"path": f"studies/{study_id}/paper/build/review_manuscript.md"},
                ],
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "blockers": [],
                },
            },
            "closeout_refs": [
                f"studies/{study_id}/paper/review/domain_stage_closeout_sat_story_delta_20260602T202258Z.json",
                f"studies/{study_id}/paper/draft.md",
                f"studies/{study_id}/paper/build/review_manuscript.md",
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["receipt_kind"] == "default_executor_execution"
    assert receipt["receipt_ref"] == (
        "paper/review/domain_stage_closeout_sat_story_delta_20260602T202258Z.json"
    )
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == work_unit_fingerprint
    assert receipt["changed_artifact_ref_count"] == 2
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"


def test_default_executor_nonconsumable_closeout_reports_missing_story_surface_delta(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = {
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
        ),
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
            ),
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::ledger-only",
                    "idempotency_key": "owner-route::same-work-unit",
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
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "claim_evidence_map.json")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    assert default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    ) == {}
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert redrive["status"] == "non_consumable_closeout"
    assert redrive["execution_id"] == "execution::dm002::run_quality_repair_batch::ledger-only"
    assert redrive["reason"] == "manuscript_story_surface_delta_missing"
    assert redrive["next_action"] == "redrive_owner_route_with_closeout_context"


def test_default_executor_zero_execution_blocked_closeout_does_not_consume_owner_route(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = {
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
        ),
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
                ),
                "work_unit_id": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
            },
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
            ),
            "work_unit_id": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
        },
    }
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_zero_execution.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "stage_attempt_id": "sat_zero_execution",
            "closeout_id": "stage-attempt-closeout::sat_zero_execution::dispatch-zero",
            "status": "blocked_with_domain_owner_refs",
            "blocked_reason": "domain_owner_action_dispatch_execution_count_zero",
            "owner_route_basis": owner_route["source_refs"]["owner_route_currentness_basis"],
            "artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
                "story_surface_delta_present": False,
                "changed_artifact_refs": [],
            },
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "execution_status": "blocked",
                "domain_owner": "write",
                "dispatcher_result": {
                    "dry_run": False,
                    "execution_count": 0,
                    "executed_count": 0,
                    "blocked_count": 0,
                    "reason": (
                        "no current executable run_quality_repair_batch dispatch was visible "
                        "to domain-owner-action-dispatch for the requested study/action filter"
                    ),
                },
            },
            "owner_receipt": {
                "status": "blocked",
                "typed_blocker": "manuscript_story_surface_delta_missing",
                "blocked_reasons": [
                    "canonical_artifact_delta_missing",
                    "run_quality_repair_batch_not_visible_in_current_opl_control_state",
                    "domain_owner_action_dispatch_execution_count_zero",
                ],
            },
        },
    )

    assert default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    ) == {}
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert redrive["status"] == "non_consumable_closeout"
    assert redrive["execution_id"] == "stage-attempt-closeout::sat_zero_execution::dispatch-zero"
    assert redrive["reason"] == "domain_owner_action_dispatch_execution_count_zero"
    assert redrive["next_action"] == "redrive_owner_route_with_closeout_context"


def test_scan_consumes_quality_repair_receipt_with_review_manuscript_story_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::ai-reviewer-routeback",
        "study_id": study_id,
        "quest_id": quest_id,
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
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_current_publication_hardening_after_ai_reviewer_eval"
                ),
                "next_work_unit": {
                    "unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                    "lane": "write",
                    "summary": "Harden current manuscript story, displays, scope alignment, and citations.",
                },
            }
        ],
    }
    _write_json(publication_eval_path, publication_eval_payload)
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-after-review-manuscript-execution",
            "canonical_runtime_action": "observe_runtime",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "publication_eval": publication_eval_payload,
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "source_signature": "truth-snapshot::dm002-review-manuscript-delta",
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                "lane": "write",
                "summary": "Harden current manuscript story, displays, scope alignment, and citations.",
            },
            "typed_blocker": None,
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    queued_action = before_receipt["studies"][0]["action_queue"][0]
    current_owner_route = queued_action["owner_route"]
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::run_quality_repair_batch::review-manuscript",
                    "idempotency_key": current_owner_route["idempotency_key"],
                    "repeat_suppression_key": current_owner_route["source_fingerprint"],
                    "current_owner_route": current_owner_route,
                    "prompt_contract": {"owner_route": current_owner_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
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
    assert study["action_queue"] == []
    assert result["action_queue"] == []
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["status"] == "consumed"
    assert receipt["consumed_owner_route_idempotency_key"] == current_owner_route["idempotency_key"]
