from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_receipt_consumption,
)
from med_autoscience.controllers.owner_route_reconcile_parts.current_controller_followthrough import (
    action_after_consumed_receipt,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
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
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_adapter_receipt",
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
    closeout_ref = "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_adapter_receipt",
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

    closeout_ref = "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    candidates = default_executor_execution_candidates(study_root=study_root)
    candidate = next(
        execution
        for execution, ref in candidates
        if ref == closeout_ref
    )
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["action_fingerprint"] == work_unit_fingerprint
    assert (
        candidate["source_eval_id"]
        == owner_route["source_refs"]["owner_route_currentness_basis"]["source_eval_id"]
    )
    assert candidate["owner_route_currentness_basis"] == owner_route["source_refs"]["owner_route_currentness_basis"]
    assert candidate["canonical_work_unit_identity"] == owner_route["source_refs"]["owner_route_currentness_basis"]

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


def test_stage_closeout_consumes_current_route_from_top_level_currentness_basis(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "publication-blockers::0915410f804b3697"
    currentness_basis = {
        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        "runtime_health_epoch": "runtime-health-event-006796-4692626fe074f277",
        "source_eval_id": (
            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
            "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-13T05:46:27+00:00"
        ),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
    }
    owner_route = {
        "route_epoch": work_unit_fingerprint,
        "truth_epoch": currentness_basis["truth_epoch"],
        "runtime_health_epoch": currentness_basis["runtime_health_epoch"],
        "source_eval_id": currentness_basis["source_eval_id"],
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_owner": "write",
        "owner_reason": work_unit_id,
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": currentness_basis,
            "study_truth_epoch": currentness_basis["truth_epoch"],
            "runtime_health_epoch": currentness_basis["runtime_health_epoch"],
            "source_eval_id": currentness_basis["source_eval_id"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        },
        "idempotency_key": f"provider-admission::{study_id}::{work_unit_fingerprint}",
    }
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_1285ddfc9dcac80a5dc1aa55.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_1285ddfc9dcac80a5dc1aa55",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "owner": "write",
            "owner_reason": work_unit_id,
            "status": "executed",
            "route_outcome": "progress_delta",
            "owner_route_currentness_basis": currentness_basis,
            "owner_receipt_ref": (
                f"studies/{study_id}/artifacts/controller/quality_repair_batch/latest.json"
            ),
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                "sat_1285ddfc9dcac80a5dc1aa55.closeout.json",
                f"studies/{study_id}/artifacts/supervision/consumer/stage_attempt_closeouts/"
                "sat_1285ddfc9dcac80a5dc1aa55.json",
                f"studies/{study_id}/artifacts/controller/quality_repair_batch/latest.json",
                f"studies/{study_id}/artifacts/controller/repair_execution_evidence/latest.json",
                f"studies/{study_id}/paper/draft.md",
                f"studies/{study_id}/paper/build/review_manuscript.md",
            ],
            "artifact_delta": {
                "status": "fresh",
                "meaningful_artifact_delta": True,
                "changed_artifact_refs": [
                    f"studies/{study_id}/paper/claim_evidence_map.json",
                    f"studies/{study_id}/paper/evidence_ledger.json",
                    f"studies/{study_id}/paper/draft.md",
                    f"studies/{study_id}/paper/build/review_manuscript.md",
                    f"studies/{study_id}/paper/review/review_ledger.json",
                ],
                "story_surface_delta_refs": [
                    f"studies/{study_id}/paper/draft.md",
                    f"studies/{study_id}/paper/build/review_manuscript.md",
                ],
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "run_quality_repair_batch",
                "current_owner": "write",
                "problem_summary": "The current owner route required write-owner repair.",
                "stage_goal": "Execute the owner-authorized medical prose repair work unit.",
                "stage_work_done": ["Ran the quality repair batch."],
                "paper_work_done": ["Recorded a canonical manuscript story-surface delta."],
                "changed_stage_surfaces": [],
                "changed_paper_surfaces": [
                    f"studies/{study_id}/paper/draft.md",
                    f"studies/{study_id}/paper/build/review_manuscript.md",
                ],
                "outcome": "progress_delta",
                "remaining_blockers": ["publication_gate_replay_blocked"],
                "duration": {"status": "not_available"},
                "token_usage": {"status": "not_available", "total_tokens": None},
                "cost": {"status": "not_available", "usd": None},
                "usage_refs": [],
                "cost_refs": [],
                "progress_delta_classification": "deliverable_progress",
                "deliverable_progress_delta": {"count": 5, "refs": []},
                "paper_progress_delta": {"count": 5, "refs": []},
                "platform_repair_delta": {"count": 0, "refs": []},
                "next_forced_delta": {
                    "owner": "review",
                    "action": "consume_ai_reviewer_recheck_request",
                    "currentness_basis": currentness_basis,
                },
                "evidence_refs": [],
            },
        },
    )

    candidates = [
        execution
        for execution, ref in default_executor_execution_candidates(study_root=study_root)
        if ref == "artifacts/supervision/consumer/default_executor_execution/sat_1285ddfc9dcac80a5dc1aa55.closeout.json"
    ]
    assert len(candidates) == 1
    assert candidates[0]["owner_route_currentness_source"] == "embedded_currentness_basis"
    assert candidates[0]["work_unit_id"] == work_unit_id
    assert candidates[0]["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidates[0]["source_eval_id"] == currentness_basis["source_eval_id"]
    for key, value in currentness_basis.items():
        assert candidates[0]["owner_route_currentness_basis"][key] == value

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["action_type"] == "run_quality_repair_batch"
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == work_unit_fingerprint
    assert receipt["changed_artifact_ref_count"] == 5
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"

