from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_routes_ai_reviewer_package_freshness_mismatch_to_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    current_eval_id = "publication-eval::dm002::current-ai-reviewer"
    stale_eval_id = "publication-eval::dm002::stale-package"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "continue_same_line",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck::continue_bundle_stage",
                "next_work_unit": {
                    "unit_id": "bundle_stage_continuation",
                    "lane": "controller",
                    "summary": "Continue downstream bundle-stage handling after AI reviewer recheck.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": stale_eval_id,
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "schema_version": 1,
            "study_id": study_id,
            "generated_at": "2026-05-17T09:08:45+00:00",
            "executions": [
                {
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_workflow_failed",
                    "error": "current_package_freshness_source_eval_id_mismatch",
                    "next_owner": "ai_reviewer",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "return-to-ai-reviewer",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
            "next_work_unit": {
                "unit_id": "ai_reviewer_recheck",
                "lane": "review",
                "summary": "Return current manuscript and evidence refs to AI reviewer.",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {"unit_id": "ai_reviewer_recheck"},
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-ai-reviewer",
            "source_signature": "truth-source-ai-reviewer",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "artifact_os"
    assert action["source_blocked_reason"] == "ai_reviewer_workflow_failed"
    assert action["source_error"] == "current_package_freshness_source_eval_id_mismatch"
    assert action["current_package_freshness"]["source_eval_id"] == stale_eval_id
    assert action["current_package_freshness"]["expected_source_eval_id"] == current_eval_id
    assert study["why_not_applied"] == "current_package_freshness_required"
    assert study["blocked_reason"] == "current_package_freshness_required"
    assert study["next_owner"] == "artifact_os"
    assert study["owner_route"]["allowed_actions"] == ["current_package_freshness_required"]


def test_scan_domain_routes_routes_ai_reviewer_claim_alignment_blocker_to_quality_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    current_eval_id = "publication-eval::dm002::current-ai-reviewer"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [{"action_type": "continue_same_line"}],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "schema_version": 1,
            "study_id": study_id,
            "generated_at": "2026-05-24T20:19:00+00:00",
            "executions": [
                {
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "claim_evidence_alignment_required",
                    "error": "claim_evidence_alignment.status must be ready",
                    "next_owner": "write",
                    "owner_result": {
                        "surface_kind": "claim_evidence_alignment_dispatch_blocker",
                        "blocked_reason": "claim_evidence_alignment_required",
                        "missing_evidence_item_refs": ["C1_main_result_observed_gap"],
                        "claim_evidence_alignment": {
                            "surface_kind": "claim_evidence_alignment_gate_v1",
                            "status": "blocked",
                            "claim_count": 1,
                            "aligned_claim_count": 0,
                            "blockers": ["C1.C1_main_result_observed_gap_missing_from_evidence_ledger"],
                        },
                    },
                }
            ],
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {"unit_id": "ai_reviewer_recheck"},
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-ai-reviewer",
            "source_signature": "truth-source-ai-reviewer",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "publication_supervision",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "claim_evidence_alignment_required"
    assert action["source_blocked_reason"] == "claim_evidence_alignment_required"
    assert action["missing_evidence_item_refs"] == ["C1_main_result_observed_gap"]
    assert study["why_not_applied"] == "claim_evidence_alignment_required"
    assert study["blocked_reason"] == "claim_evidence_alignment_required"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["owner_reason_contract"]["registered"] is True


def test_scan_domain_routes_preserves_pending_claim_alignment_request_after_execution_latest_is_superseded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    current_eval_id = "publication-eval::dm002::current-ai-reviewer"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "route_back_required": True,
                    "route_target": "write",
                    "request_digest": "digest-request",
                    "manuscript_ref": "paper/draft.md",
                    "manuscript_digest": "digest-manuscript",
                }
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::manuscript_story_repair",
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Repair manuscript story surface before AI reviewer recheck.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Claim one.",
                    "status": "active",
                    "paper_role": "primary",
                    "display_bindings": ["table_1"],
                    "sections": ["results"],
                    "evidence_items": [
                        {
                            "item_id": "C1_main_result_observed_gap",
                            "support_level": "primary",
                            "source_paths": ["analysis/results.csv"],
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Claim one.",
                    "status": "active",
                    "submission_scope": "main_text",
                    "evidence": [
                        {
                            "evidence_id": "legacy-c1",
                            "kind": "analysis_result",
                            "source_paths": ["analysis/results.csv"],
                            "support_level": "primary",
                            "summary": "Observed result.",
                        }
                    ],
                    "gaps": [{"gap_id": "G1", "description": "Alignment pending.", "submission_impact": "blocked"}],
                    "recommended_actions": [
                        {"action_id": "A1", "priority": "high", "description": "Align evidence id."}
                    ],
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "run_quality_repair_batch.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "request_kind": "run_quality_repair_batch",
            "action_type": "run_quality_repair_batch",
            "reason": "claim_evidence_alignment_required",
            "authority": "observability_only",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "required_output_surface": (
                "claim-evidence map and evidence ledger alignment or "
                "typed blocker:claim_evidence_alignment_required"
            ),
            "owner_route": {
                "surface": "domain_route_owner_route",
                "schema_version": 2,
                "study_id": study_id,
                "quest_id": quest_id,
                "truth_epoch": "truth-epoch-ai-reviewer",
                "runtime_health_epoch": "runtime-health-epoch-ai-reviewer",
                "work_unit_fingerprint": "fingerprint-claim-alignment",
                "failure_signature": "claim_evidence_alignment_required",
                "current_owner": "ai_reviewer",
                "next_owner": "write",
                "owner_reason": "claim_evidence_alignment_required",
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "owner_route_currentness_basis": {
                        "work_unit_fingerprint": "fingerprint-claim-alignment",
                        "truth_epoch": "truth-epoch-ai-reviewer",
                        "runtime_health_epoch": "runtime-health-epoch-ai-reviewer",
                        "owner_reason": "claim_evidence_alignment_required",
                    }
                },
                "owner_reason_contract": {
                    "registered": True,
                    "reason": "claim_evidence_alignment_required",
                    "owner": "write",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "required_output": (
                        "claim-evidence map and evidence ledger alignment or "
                        "typed blocker:claim_evidence_alignment_required"
                    ),
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "schema_version": 1,
            "study_id": study_id,
            "generated_at": "2026-05-24T20:46:52+00:00",
            "executions": [
                {
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "manuscript_story_surface_delta_missing",
                    "dispatch_authority": "quality_repair_batch_writer_handoff",
                    "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
                }
            ],
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "controller_action": "run_quality_repair_batch",
            "owner": "write",
            "next_work_unit": {"unit_id": "manuscript_story_repair"},
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-ai-reviewer",
            "source_signature": "truth-source-ai-reviewer",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "publication_supervision",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["reason"] == "claim_evidence_alignment_required"
    assert action["next_work_unit"] == "claim_evidence_alignment_repair"
    assert action["claim_evidence_alignment"]["blockers"] == [
        "C1.C1_main_result_observed_gap_missing_from_evidence_ledger"
    ]
    assert study["blocked_reason"] == "claim_evidence_alignment_required"
    assert study["owner_route"]["owner_reason_contract"]["reason"] == "claim_evidence_alignment_required"
