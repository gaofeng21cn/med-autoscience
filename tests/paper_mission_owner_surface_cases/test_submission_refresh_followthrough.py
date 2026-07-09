from __future__ import annotations

import importlib
from pathlib import Path

from tests.paper_mission_owner_surface_cases.owner_route_test_helpers import write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def _dm003_context(monkeypatch, tmp_path: Path):
    scan = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    return scan, profile, study_id, quest_id, study_root, quest_root


def _route_for_action(
    *,
    study_id: str,
    quest_id: str,
    status: dict,
    progress: dict,
    action: dict,
    blocked_reason: str,
    next_owner: str,
) -> dict:
    owner_route = importlib.import_module("med_autoscience.runtime_control.owner_route")
    route, _actions = owner_route.route_and_decorate_actions(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        actions=[action],
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        active_run_id=None,
    )
    return route


def _submission_refresh_route(study_root: Path, publication_eval_payload: dict) -> dict:
    current_truth_owner = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.current_truth_owner"
    )
    route = current_truth_owner.current_gate_replay_submission_refresh_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    assert route is not None
    return route


def _current_package_route(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    status: dict,
    progress: dict,
    publication_eval_payload: dict,
) -> dict:
    artifact_freshness = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.artifact_freshness"
    )
    action = artifact_freshness.action_payload(
        reason=artifact_freshness.ACTION_TYPE,
        controller_route=_submission_refresh_route(study_root, publication_eval_payload),
    )
    return _route_for_action(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        action=action,
        blocked_reason=artifact_freshness.ACTION_TYPE,
        next_owner=artifact_freshness.OWNER,
    )


def _publication_gate_specificity_route(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    status: dict,
    progress: dict,
    publication_eval_payload: dict,
) -> dict:
    publication_gate_actions = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.publication_gate_actions"
    )
    refresh_route = _submission_refresh_route(study_root, publication_eval_payload)
    action = publication_gate_actions.action_payload(
        gate_specificity={"required": True, "gate_owner": "publication_gate"}
    )
    action["controller_route"] = dict(refresh_route)
    action["work_unit_fingerprint"] = refresh_route["work_unit_fingerprint"]
    action["required_output_surface"] = "artifacts/publication_eval/latest.json#specificity_targets"
    return _route_for_action(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        action=action,
        blocked_reason=publication_gate_actions.ACTION_TYPE,
        next_owner="publication_gate",
    )


def test_consumed_submission_refresh_gate_replay_without_specific_targets_routes_to_publication_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan, profile, study_id, quest_id, study_root, quest_root = _dm003_context(monkeypatch, tmp_path)
    eval_id = "publication-eval::dm003::post-submission-refresh-specificity"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    write_json(
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
    write_json(
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
        "reason": "opl_stage_attempt_admission_required",
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
    consumed_route = _current_package_route(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_dispatch_execution",
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
    scan, profile, study_id, quest_id, study_root, quest_root = _dm003_context(monkeypatch, tmp_path)
    eval_id = "publication-eval::dm003::ai-reviewer-current"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "specificity-refresh.json"
    write_json(
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
    write_json(
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
        "reason": "opl_stage_attempt_admission_required",
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
    specificity_route = _publication_gate_specificity_route(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_dispatch_execution",
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
    receipt = study["owner_callable_receipt_consumption"]
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


def test_specificity_followthrough_takes_precedence_over_older_package_freshness_receipt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan, profile, study_id, quest_id, study_root, quest_root = _dm003_context(monkeypatch, tmp_path)
    eval_id = "publication-eval::dm003::ai-reviewer-current"
    work_unit_fingerprint = "gate-replay-route-back::finalize::publication-blockers::submission-refresh"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "specificity-refresh.json"
    write_json(
        gate_report_path,
        {
            "gate_kind": "publishability_control",
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "gate_fingerprint": "publication-gate::specificity-refresh",
            "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
            "supervisor_phase": "bundle_stage_blocked",
            "current_required_action": "complete_bundle_stage",
        },
    )
    write_json(
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
                "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "opl_stage_attempt_admission_required",
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
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "claim_evidence_alignment": {"status": "ready"},
            "publication_quality_readiness": {"status": "blocked"},
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::finalize-refresh",
                "action_type": "route_back_same_line",
                "route_target": "finalize",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_minimal_refresh",
                    "lane": "finalize",
                    "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                },
            }
        ],
    }
    package_route = _current_package_route(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    specificity_route = _publication_gate_specificity_route(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::publication_gate_specificity_required::2026-05-28T07:19:41+00:00",
                    "idempotency_key": specificity_route["idempotency_key"],
                    "current_owner_route": specificity_route,
                    "prompt_contract": {"owner_route": specificity_route},
                    "owner_result": {
                        "status": "blocked",
                        "report_json": str(gate_report_path),
                        "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
                        "publication_eval": {
                            "eval_id": eval_id,
                            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        },
                    },
                }
            ],
            "execution_ledger": [
                {
                    "surface": "owner_callable_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "current_package_freshness_required",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::current_package_freshness_required::2026-05-28T06:20:33+00:00",
                    "idempotency_key": package_route["idempotency_key"],
                    "current_owner_route": package_route,
                    "prompt_contract": {"owner_route": package_route},
                    "owner_result": {"status": "executed", "ok": True},
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
    receipt = study["owner_callable_receipt_consumption"]
    assert receipt["action_type"] == "publication_gate_specificity_required"
    assert receipt["consumption_mode"] == "followthrough_action_transition"
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    assert study["owner_route"]["owner_reason"] == "current_package_freshness_required"


def test_current_package_freshness_receipt_takes_precedence_over_older_specificity_followthrough(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan, profile, study_id, quest_id, study_root, quest_root = _dm003_context(monkeypatch, tmp_path)
    eval_id = "publication-eval::dm003::ai-reviewer-current"
    truth_epoch = "truth-epoch-dm003-package-freshness"
    work_unit_fingerprint = "gate-replay-route-back::finalize::publication-blockers::submission-refresh"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "specificity-refresh.json"
    write_json(
        gate_report_path,
        {
            "gate_kind": "publishability_control",
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "gate_fingerprint": "publication-gate::specificity-refresh",
            "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
            "supervisor_phase": "bundle_stage_blocked",
            "current_required_action": "complete_bundle_stage",
        },
    )
    write_json(
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
                "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "opl_stage_attempt_admission_required",
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
            "runtime_health_epoch": "runtime-health-dm003-package-freshness",
            "canonical_runtime_action": "external_supervisor_required",
            "retry_budget_remaining": 0,
        },
        "study_truth_snapshot": {
            "truth_epoch": truth_epoch,
            "source_signature": "truth-source-dm003-package-freshness",
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
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "claim_evidence_alignment": {"status": "ready"},
            "publication_quality_readiness": {"status": "blocked"},
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::finalize-refresh",
                "action_type": "route_back_same_line",
                "route_target": "finalize",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_minimal_refresh",
                    "lane": "finalize",
                    "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                },
            }
        ],
    }
    package_route = _current_package_route(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    specificity_route = _publication_gate_specificity_route(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
    )
    write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 2,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "current_package_freshness_required",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::current_package_freshness_required::2026-05-28T08:49:44+00:00",
                    "idempotency_key": package_route["idempotency_key"],
                    "current_owner_route": package_route,
                    "prompt_contract": {"owner_route": package_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "gate_replay": {"status": "blocked"},
                    },
                }
            ],
            "execution_ledger": [
                {
                    "surface": "owner_callable_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::publication_gate_specificity_required::2026-05-28T08:22:30+00:00",
                    "idempotency_key": specificity_route["idempotency_key"],
                    "current_owner_route": specificity_route,
                    "prompt_contract": {"owner_route": specificity_route},
                    "owner_result": {
                        "status": "blocked",
                        "report_json": str(gate_report_path),
                        "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
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
    receipt = study["owner_callable_receipt_consumption"]
    assert receipt["action_type"] == "current_package_freshness_required"
    assert receipt.get("consumption_mode") != "followthrough_action_transition"
    assert [item["action_type"] for item in study["action_queue"]] == ["publication_gate_specificity_required"]
    assert study["owner_route"]["owner_reason"] == "publication_gate_specificity_required"
