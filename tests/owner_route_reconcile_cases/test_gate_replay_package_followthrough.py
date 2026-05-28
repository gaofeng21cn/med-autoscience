from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_consumed_gate_clearing_batch_routes_blocked_gate_replay_to_next_work_unit(
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
    eval_id = "publication-eval::dm003::current-ai-reviewer-finalize-replay"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "gate-replay.json"
    _write_json(
        gate_report_path,
        _gate_replay_report("publication-gate::dm003-finalize-replay"),
    )
    _write_gate_clearing_batch(
        study_root=study_root,
        eval_id=eval_id,
        gate_report_path=gate_report_path,
        work_unit_fingerprint="publication-blockers::dm003-submission-refresh",
    )
    status_payload = _status_payload(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        quest_root=quest_root,
        truth_epoch="truth-epoch-dm003-gate-clearing-consumed",
        source_signature="truth-source-dm003-gate-clearing-consumed",
        runtime_epoch="runtime-health-dm003-gate-clearing-consumed",
        eval_id=eval_id,
        include_domain_transition=True,
    )
    progress_payload = _progress_payload(
        study_id=study_id,
        quest_id=quest_id,
        quest_root=quest_root,
        study_root=study_root,
        truth_snapshot=status_payload["study_truth_snapshot"],
    )
    progress_payload["autonomy_slo"] = {"breach_types": ["same_fingerprint_loop"]}
    publication_eval_payload = _publication_eval_payload(study_id=study_id, quest_id=quest_id, study_root=study_root, eval_id=eval_id)
    gate_route = _gate_replay_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        truth_epoch="truth-epoch-dm003-gate-clearing-consumed",
        runtime_epoch="runtime-health-dm003-gate-clearing-consumed",
        source_fingerprint="truth-source-dm003-gate-clearing-consumed",
        publication_eval_path=(
            study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses" / "current.json"
        ),
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "execution_ledger": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::run_gate_clearing_batch::2026-05-28T11:16:07+00:00",
                    "idempotency_key": gate_route["idempotency_key"],
                    "current_owner_route": gate_route,
                    "prompt_contract": {"owner_route": gate_route},
                    "owner_result": {
                        "status": "executed",
                        "gate_replay": {"status": "blocked", "allow_write": False},
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
    assert receipt["action_type"] == "run_gate_clearing_batch"
    assert receipt["consumption_mode"] == "followthrough_action_transition"
    _assert_package_freshness_action(study)


def test_existing_gate_clearing_batch_followthrough_preempts_ai_reviewer_gate_replay(
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
    eval_id = "publication-eval::dm003::current-ai-reviewer-finalize-replay"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "gate-replay.json"
    _write_json(
        gate_report_path,
        _gate_replay_report("publication-gate::dm003-existing-replay"),
    )
    _write_gate_clearing_batch(
        study_root=study_root,
        eval_id=eval_id,
        gate_report_path=gate_report_path,
        work_unit_fingerprint="publication-blockers::existing-submission-refresh",
    )
    status_payload = _status_payload(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        quest_root=quest_root,
        truth_epoch="truth-epoch-dm003-existing-gate-replay",
        source_signature="truth-source-dm003-existing-gate-replay",
        runtime_epoch="runtime-health-dm003-existing-gate-replay",
        eval_id=eval_id,
        include_domain_transition=False,
    )
    progress_payload = _progress_payload(
        study_id=study_id,
        quest_id=quest_id,
        quest_root=quest_root,
        study_root=study_root,
        truth_snapshot=status_payload["study_truth_snapshot"],
    )
    publication_eval_payload = _publication_eval_payload(study_id=study_id, quest_id=quest_id, study_root=study_root, eval_id=eval_id)
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

    _assert_package_freshness_action(result["studies"][0])


def test_current_delivery_reporting_checklist_gate_replay_routes_to_write_owner(
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
    eval_id = "publication-eval::dm003::current-reporting-checklist-replay"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "gate-replay.json"
    _write_json(
        gate_report_path,
        _gate_replay_report_with_reporting_checklist("publication-gate::dm003-reporting-checklist"),
    )
    _write_gate_clearing_batch(
        study_root=study_root,
        eval_id=eval_id,
        gate_report_path=gate_report_path,
        work_unit_fingerprint="publication-blockers::dm003-reporting-checklist",
    )
    status_payload = _status_payload(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        quest_root=quest_root,
        truth_epoch="truth-epoch-dm003-reporting-checklist",
        source_signature="truth-source-dm003-reporting-checklist",
        runtime_epoch="runtime-health-dm003-reporting-checklist",
        eval_id=eval_id,
        include_domain_transition=False,
    )
    progress_payload = _progress_payload(
        study_id=study_id,
        quest_id=quest_id,
        quest_root=quest_root,
        study_root=study_root,
        truth_snapshot=status_payload["study_truth_snapshot"],
    )
    publication_eval_payload = _publication_eval_payload(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        eval_id=eval_id,
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
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["controller_route"]["work_unit_id"] == "medical_prose_write_repair"
    assert action["reason"] == "publication_gate_route_back_write_required"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["owner_reason"] == "publication_gate_route_back_write_required"


def _gate_replay_report(gate_fingerprint: str) -> dict:
    return {
        "gate_kind": "publishability_control",
        "schema_version": 1,
        "status": "blocked",
        "allow_write": False,
        "gate_fingerprint": gate_fingerprint,
        "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
        "medical_publication_surface_route_back_recommendation": "return_to_finalize",
        "supervisor_phase": "bundle_stage_blocked",
        "current_required_action": "complete_bundle_stage",
        "study_delivery_status": "current",
        "submission_minimal_authority_status": "current",
    }


def _gate_replay_report_with_reporting_checklist(gate_fingerprint: str) -> dict:
    report = _gate_replay_report(gate_fingerprint)
    report.update(
        {
            "publication_reporting_checklist": {
                "status": "blocked",
                "blockers": [
                    "manuscript_voice_reporting_incomplete",
                    "treatment_gap_reporting_incomplete",
                    "phenotype_derivation_reporting_incomplete",
                    "baseline_characteristics_reporting_incomplete",
                    "data_quality_reporting_incomplete",
                ],
            },
            "submission_minimal_evaluated_source_signature": "source-signature",
            "submission_minimal_authority_source_signature": "source-signature",
            "study_delivery_evaluated_source_signature": "delivery-signature",
            "study_delivery_authority_source_signature": "delivery-signature",
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
        }
    )
    return report


def _write_gate_clearing_batch(
    *,
    study_root: Path,
    eval_id: str,
    gate_report_path: Path,
    work_unit_fingerprint: str,
) -> None:
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
            "work_unit_fingerprint": work_unit_fingerprint,
            "gate_replay": {
                "status": "blocked",
                "allow_write": False,
                "report_json": str(gate_report_path),
                "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            },
        },
    )


def _status_payload(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    quest_root: Path,
    truth_epoch: str,
    source_signature: str,
    runtime_epoch: str,
    eval_id: str,
    include_domain_transition: bool,
) -> dict:
    payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "runtime_health_snapshot": {
            "runtime_health_epoch": runtime_epoch,
            "canonical_runtime_action": "external_supervisor_required",
            "retry_budget_remaining": 0,
        },
        "study_truth_snapshot": {
            "truth_epoch": truth_epoch,
            "source_signature": source_signature,
        },
    }
    if include_domain_transition:
        payload["domain_transition"] = {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "finalize",
            "owner": "publication_gate",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": _gate_replay_work_unit(),
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                "eval_id": eval_id,
            },
        }
    return payload


def _progress_payload(
    *,
    study_id: str,
    quest_id: str,
    quest_root: Path,
    study_root: Path,
    truth_snapshot: dict,
) -> dict:
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "bundle_stage_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": truth_snapshot,
    }


def _publication_eval_payload(*, study_id: str, quest_id: str, study_root: Path, eval_id: str) -> dict:
    return {
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
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:" + "b" * 64,
                    "route_back_required": True,
                    "route_target": "finalize",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:" + "b" * 64,
                },
            },
            "claim_evidence_alignment": {"status": "ready"},
            "publication_quality_readiness": {"status": "blocked"},
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::owner-authorized-gate-replay",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "finalize",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::owner_authorized_publication_gate_replay"
                ),
                "next_work_unit": _gate_replay_work_unit(),
            }
        ],
    }


def _gate_replay_work_unit() -> dict:
    return {
        "unit_id": "owner_authorized_publication_gate_replay",
        "lane": "finalize",
        "summary": "Replay the MAS publication gate against current manuscript and evidence surfaces.",
    }


def _gate_replay_owner_route(
    *,
    study_id: str,
    quest_id: str,
    eval_id: str,
    truth_epoch: str,
    runtime_epoch: str,
    source_fingerprint: str,
    publication_eval_path: Path,
) -> dict:
    work_unit_fingerprint = "domain-transition::route_back_same_line::owner_authorized_publication_gate_replay"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": source_fingerprint,
        "next_owner": "gate_clearing_batch",
        "owner_reason": "owner_authorized_publication_gate_replay",
        "allowed_actions": ["run_gate_clearing_batch"],
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_epoch,
            "source_eval_id": eval_id,
            "work_unit_id": "owner_authorized_publication_gate_replay",
            "work_unit_fingerprint": work_unit_fingerprint,
            "blocked_reason": "owner_authorized_publication_gate_replay",
            "publication_eval_path": str(publication_eval_path),
            "owner_route_currentness_basis": {
                "truth_epoch": truth_epoch,
                "runtime_health_epoch": runtime_epoch,
                "work_unit_id": "owner_authorized_publication_gate_replay",
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_reason": "owner_authorized_publication_gate_replay",
            },
        },
        "idempotency_key": "owner-route::dm003::owner-authorized-gate-replay",
    }


def _assert_package_freshness_action(study: dict) -> None:
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "artifact_os"
    assert action["reason"] == "current_package_freshness_required"
    assert action["controller_route"]["work_unit_id"] == "submission_minimal_refresh"
    assert study["owner_route"]["next_owner"] == "artifact_os"
    assert study["owner_route"]["owner_reason"] == "current_package_freshness_required"
