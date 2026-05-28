from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_consumed_submission_refresh_gate_replay_without_specific_targets_routes_to_publication_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::post-submission-refresh-specificity"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    _write_json(
        gate_report_path,
        {
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "gate_fingerprint": "gate-fingerprint-dm003-post-submission-refresh",
            "blockers": [
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_eval_id": eval_id,
            "current_publication_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
            },
            "work_unit_fingerprint": "publication-blockers::dm003-submission-refresh",
            "gate_replay": {
                "status": "blocked",
                "allow_write": False,
                "report_json": str(gate_report_path),
                "blockers": [
                    "medical_publication_surface_blocked",
                    "submission_hardening_incomplete",
                ],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "finalize",
            "owner": "publication_gate",
            "controller_action": "run_gate_clearing_batch",
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-post-submission-refresh",
            "canonical_runtime_action": "external_supervisor_required",
            "retry_budget_remaining": 0,
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-post-submission-refresh",
            "source_signature": "truth-source-dm003-post-submission-refresh",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "autonomy_slo": {"breach_types": ["same_fingerprint_loop"]},
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "reviewer_operating_system": {
            "claim_evidence_alignment": {
                "surface_kind": "claim_evidence_alignment_gate_v1",
                "status": "ready",
                "missing_required_fields": [],
                "blockers": [],
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
    }
    consumed_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-epoch-dm003-post-submission-refresh",
        "route_epoch": "truth-epoch-dm003-post-submission-refresh",
        "runtime_health_epoch": "runtime-health-dm003-post-submission-refresh",
        "work_unit_fingerprint": "gate-replay-route-back::finalize::publication-blockers::dm003-submission-refresh",
        "source_fingerprint": "truth-source-dm003-post-submission-refresh",
        "next_owner": "artifact_os",
        "owner_reason": "current_package_freshness_required",
        "allowed_actions": ["current_package_freshness_required"],
        "source_refs": {
            "study_truth_epoch": "truth-epoch-dm003-post-submission-refresh",
            "runtime_health_epoch": "runtime-health-dm003-post-submission-refresh",
            "work_unit_id": "submission_minimal_refresh",
            "work_unit_fingerprint": (
                "gate-replay-route-back::finalize::publication-blockers::dm003-submission-refresh"
            ),
            "blocked_reason": "current_package_freshness_required",
            "publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "idempotency_key": "owner-route::dm003::post-submission-refresh",
    }
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
                    "action_type": "current_package_freshness_required",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::current_package_freshness_required::2026-05-28T06:20:41+00:00",
                    "idempotency_key": consumed_route["idempotency_key"],
                    "current_owner_route": consumed_route,
                    "prompt_contract": {"owner_route": consumed_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "gate_replay": {"status": "blocked"},
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["publication_gate_specificity_required"]
    assert study["owner_route"]["next_owner"] == "publication_gate"
    assert study["owner_route"]["owner_reason"] == "publication_gate_specificity_required"
    assert study["blocked_reason"] == "publication_gate_specificity_required"
    assert study["paper_progress_stall"]["terminal"] is True


def test_consumed_publication_gate_specificity_with_blocked_gate_routes_to_finalize_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::ai-reviewer-current"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "specificity-refresh.json"
    _write_json(
        gate_report_path,
        {
            "gate_kind": "publishability_control",
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "gate_fingerprint": "publication-gate::specificity-refresh",
            "blockers": [
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
            ],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
            "supervisor_phase": "bundle_stage_blocked",
            "current_required_action": "complete_bundle_stage",
            "study_delivery_status": "current",
            "submission_minimal_authority_status": "current",
            "submission_minimal_manifest_path": str(
                study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"
            ),
            "blocking_artifact_refs": [
                {
                    "blocker": "submission_hardening_incomplete",
                    "artifact_path": str(
                        study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"
                    ),
                    "artifact_role": "submission_minimal_authority",
                    "source_path": str(
                        study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"
                    ),
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_eval_id": eval_id,
            "current_publication_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
            },
            "work_unit_fingerprint": "publication-blockers::submission-refresh",
            "gate_replay": {
                "status": "blocked",
                "allow_write": False,
                "report_json": str(gate_report_path),
                "blockers": [
                    "medical_publication_surface_blocked",
                    "submission_hardening_incomplete",
                ],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "finalize",
            "owner": "publication_gate",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-specificity-refresh",
            "canonical_runtime_action": "external_supervisor_required",
            "retry_budget_remaining": 0,
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-specificity-refresh",
            "source_signature": "truth-source-dm003-specificity-refresh",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "bundle_stage_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "autonomy_slo": {"breach_types": ["same_fingerprint_loop"]},
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-28T05:04:20+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "claim_evidence_alignment": {
                "surface_kind": "claim_evidence_alignment_gate_v1",
                "status": "ready",
                "missing_required_fields": [],
                "blockers": [],
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::finalize-refresh",
                "action_type": "route_back_same_line",
                "route_target": "finalize",
                "work_unit_fingerprint": "gate-replay-route-back::finalize::publication-blockers::submission-refresh",
                "next_work_unit": {
                    "unit_id": "submission_minimal_refresh",
                    "lane": "finalize",
                    "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                },
            }
        ],
    }
    specificity_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-epoch-dm003-specificity-refresh",
        "route_epoch": "truth-epoch-dm003-specificity-refresh",
        "runtime_health_epoch": "runtime-health-dm003-specificity-refresh",
        "work_unit_fingerprint": "gate-replay-route-back::finalize::publication-blockers::submission-refresh",
        "source_fingerprint": "truth-source-dm003-specificity-refresh",
        "next_owner": "publication_gate",
        "owner_reason": "publication_gate_specificity_required",
        "allowed_actions": ["publication_gate_specificity_required"],
        "source_refs": {
            "study_truth_epoch": "truth-epoch-dm003-specificity-refresh",
            "runtime_health_epoch": "runtime-health-dm003-specificity-refresh",
            "work_unit_id": "submission_minimal_refresh",
            "work_unit_fingerprint": (
                "gate-replay-route-back::finalize::publication-blockers::submission-refresh"
            ),
            "blocked_reason": "publication_gate_specificity_required",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm003-specificity-refresh",
                "runtime_health_epoch": "runtime-health-dm003-specificity-refresh",
                "work_unit_id": "submission_minimal_refresh",
                "work_unit_fingerprint": (
                    "gate-replay-route-back::finalize::publication-blockers::submission-refresh"
                ),
                "owner_reason": "publication_gate_specificity_required",
            },
        },
        "idempotency_key": "owner-route::dm003::publication-gate-specificity",
    }
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
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::publication_gate_specificity_required::2026-05-28T07:11:06+00:00",
                    "idempotency_key": specificity_route["idempotency_key"],
                    "current_owner_route": specificity_route,
                    "prompt_contract": {"owner_route": specificity_route},
                    "owner_result": {
                        "status": "blocked",
                        "report_json": str(gate_report_path),
                        "blockers": [
                            "medical_publication_surface_blocked",
                            "submission_hardening_incomplete",
                        ],
                        "publication_eval": {
                            "eval_id": eval_id,
                            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        },
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["status"] == "consumed"
    assert receipt["action_type"] == "publication_gate_specificity_required"
    assert receipt["owner_result_status"] == "blocked"
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "artifact_os"
    assert action["reason"] == "current_package_freshness_required"
    assert action["controller_route"]["work_unit_id"] == "submission_minimal_refresh"
    assert study["owner_route"]["next_owner"] == "artifact_os"
    assert study["owner_route"]["owner_reason"] == "current_package_freshness_required"
