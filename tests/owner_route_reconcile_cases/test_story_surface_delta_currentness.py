from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_owner_route_reconcile_keeps_writer_handoff_blocker_after_quality_batch_handoff_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm002::current-write-route-back"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "verdict": {"overall_verdict": "blocked", "primary_claim_status": "partial"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "recommended_actions": [
            {
                "action_id": "return-to-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_same_line_publication_paper_repair"
                ),
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript body against current AI reviewer prose findings.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "handoff_ready",
            "ok": True,
            "study_id": study_id,
            "quest_id": quest_id,
            "blocked_reason": None,
            "next_owner": "write",
            "writer_worker_handoff": {
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
            },
            "repair_execution_evidence": {
                "status": "blocked",
                "progress_delta_candidate": False,
                "blockers": ["manuscript_story_surface_delta_missing"],
                "canonical_artifact_delta": {
                    "status": "blocked",
                    "meaningful_artifact_delta": False,
                },
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "completed",
        "decision": "completed",
        "reason": "completed",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_completion_contract": {"ready": True, "status": "resolved"},
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-write-handoff",
            "source_signature": "truth-source-dm002-write-handoff",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_completion_contract": {"ready": True, "status": "resolved"},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "manuscript_story_surface_delta_missing"
    assert action["next_work_unit"] == "dm002_same_line_publication_paper_repair"
    assert action["quality_repair_batch_ref"] == str(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    assert action["paper_package_mutation_allowed"] is False
    assert action["current_package_write_allowed"] is False
    assert action["medical_claim_authoring_allowed"] is False
    assert study["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]


def test_dm003_analysis_lane_story_work_unit_handoff_keeps_write_owner_ahead_of_reviewer_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::medical-prose-routeback::sha256-current"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "verdict": {"overall_verdict": "mixed", "primary_claim_status": "partial"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "analysis",
                }
            }
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::medical-prose-routeback",
                "action_type": "route_back_same_line",
                "priority": "now",
                "requires_controller_decision": True,
                "route_target": "analysis-campaign",
                "work_unit_fingerprint": "medical-prose-routeback::analysis-campaign::sha256-current",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair manuscript methods and journal prose against AI reviewer findings.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "handoff_ready",
            "ok": True,
            "study_id": study_id,
            "quest_id": quest_id,
            "blocked_reason": None,
            "next_owner": "write",
            "writer_worker_handoff": {
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
                "owner_route": {
                    "next_owner": "write",
                    "owner_reason": "manuscript_story_surface_delta_missing",
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "canonical_artifact_delta": {
                    "status": "blocked",
                    "meaningful_artifact_delta": False,
                },
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
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
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer after canonical manuscript story repair.",
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-story-handoff",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-story-handoff",
            "source_signature": "truth-source-dm003-story-handoff",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
    }
    ai_reviewer_assessment = {
        "missing": True,
        "request_state": "requested",
        "blocked_reason": "ai_reviewer_assessment_required",
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )
    monkeypatch.setattr(
        reconcile.ai_reviewer,
        "assessment",
        lambda **_: ai_reviewer_assessment,
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "manuscript_story_surface_delta_missing"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["original_route_target"] == "analysis-campaign"
    assert action["quality_repair_batch_ref"] == str(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    assert study["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]


def test_dm003_quality_batch_writer_handoff_stays_current_without_publication_eval_write_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::post-gate-replay-mixed"
    source_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    repair_evidence_path = (
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "verdict": {"overall_verdict": "mixed", "primary_claim_status": "partial"},
        "reviewer_operating_system": {
            "claim_evidence_alignment": {"status": "ready", "missing": [], "blockers": []},
            "publication_quality_readiness": {
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
        "recommended_actions": [],
    }
    _write_json(source_eval_path, publication_eval)
    _write_json(
        repair_evidence_path,
        {
            "schema_version": 1,
            "status": "blocked",
            "blockers": ["manuscript_story_surface_delta_missing"],
            "repair_work_unit": {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Repair canonical manuscript story surfaces.",
            },
            "canonical_artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
            },
            "manuscript_surface_hygiene": {
                "status": "blocked",
                "story_surface_delta_required": True,
                "story_surface_delta_present": False,
                "blockers": ["manuscript_story_surface_delta_missing"],
            },
            "review_finding": {"source_eval_id": eval_id},
        },
    )
    writer_owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": eval_id,
        "runtime_health_epoch": "runtime-health-dm003-writer-handoff",
        "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::dm003",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "route_epoch": f"quality-repair-writer-handoff::{study_id}::{eval_id}",
        "source_fingerprint": "gate-replay-route-back::write::publication-blockers::dm003",
        "current_owner": "quality_repair_batch",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "idempotency_scope": "study_quest_owner_route",
        "source_refs": {
            "source_eval_id": eval_id,
            "work_unit_id": "manuscript_story_repair",
            "blocked_reason": "manuscript_story_surface_delta_missing",
        },
    }
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "handoff_ready",
            "ok": True,
            "study_id": study_id,
            "quest_id": quest_id,
            "next_owner": "write",
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": quest_id,
                "action_type": "run_quality_repair_batch",
                "next_executable_owner": "write",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
                "dispatch_status": "ready",
                "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
                "dispatch_authority": "quality_repair_batch_writer_handoff",
                "owner_route": writer_owner_route,
                "medical_claim_authoring_allowed": True,
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "source_action": {
                    "surface": "quality_repair_batch",
                    "blocked_reason": "manuscript_story_surface_delta_missing",
                    "source_eval_id": eval_id,
                    "repair_execution_evidence_ref": str(repair_evidence_path),
                    "next_work_unit": {
                        "unit_id": "manuscript_story_repair",
                        "lane": "write",
                    },
                },
                "refs": {
                    "source_eval_path": str(source_eval_path),
                    "repair_execution_evidence_path": str(repair_evidence_path),
                },
                "prompt_contract": {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "next_executable_owner": "write",
                    "owner_route": writer_owner_route,
                    "idempotency_key": "quality-repair-writer-handoff::dm003",
                },
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
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
            "domain_transition": {
                "study_id": study_id,
                "decision_type": "route_back_same_line",
                "route_target": "finalize",
                "owner": "publication_gate",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "owner_authorized_publication_gate_replay",
                    "lane": "finalize",
                "summary": "Replay the owner-authorized publication gate.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-writer-handoff",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm003-stale-gate",
            "source_signature": "truth-snapshot::dm003-stale-gate",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(source_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "manuscript_story_surface_delta_missing"
    assert action["next_work_unit"] == "manuscript_story_repair"
    assert action["quality_repair_batch_ref"] == str(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    assert study["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["currentness_contract"]["missing_required_fields"] == []


def test_dm003_quality_batch_writer_handoff_preempts_consumed_finalize_gate_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::current-manuscript-gate-replay"
    source_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    repair_evidence_path = (
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "verdict": {"overall_verdict": "mixed", "primary_claim_status": "partial"},
        "reviewer_operating_system": {
            "claim_evidence_alignment": {"status": "ready", "missing": [], "blockers": []},
            "publication_quality_readiness": {
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::gate-replay-after-current-manuscript",
                "action_type": "route_back_same_line",
                "priority": "now",
                "requires_controller_decision": True,
                "route_target": "finalize",
                "work_unit_fingerprint": "ai-reviewer-current-manuscript::sha256:current",
                "next_work_unit": {
                    "unit_id": "owner_authorized_publication_gate_replay",
                    "lane": "finalize",
                    "summary": "Replay the MAS publication gate against current manuscript and evidence surfaces.",
                },
            }
        ],
    }
    _write_json(source_eval_path, publication_eval)
    _write_json(
        repair_evidence_path,
        {
            "schema_version": 1,
            "status": "blocked",
            "blockers": ["manuscript_story_surface_delta_missing"],
            "repair_work_unit": {"unit_id": "manuscript_story_repair"},
            "canonical_artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
            },
            "manuscript_surface_hygiene": {
                "required": True,
                "status": "blocked",
                "story_surface_delta_required": True,
                "story_surface_delta_present": False,
                "blockers": ["manuscript_story_surface_delta_missing"],
            },
            "review_finding": {"source_eval_id": eval_id},
        },
    )
    writer_owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": eval_id,
        "runtime_health_epoch": "runtime-health-dm003-writer-handoff",
        "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::dm003",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "route_epoch": f"quality-repair-writer-handoff::{study_id}::{eval_id}",
        "source_fingerprint": "gate-replay-route-back::write::publication-blockers::dm003",
        "current_owner": "quality_repair_batch",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "source_refs": {
            "source_eval_id": eval_id,
            "work_unit_id": "manuscript_story_repair",
            "blocked_reason": "manuscript_story_surface_delta_missing",
        },
    }
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "handoff_ready",
            "ok": True,
            "study_id": study_id,
            "quest_id": quest_id,
            "next_owner": "write",
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": quest_id,
                "action_type": "run_quality_repair_batch",
                "next_executable_owner": "write",
                "dispatch_status": "ready",
                "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
                "dispatch_authority": "quality_repair_batch_writer_handoff",
                "owner_route": writer_owner_route,
                "medical_claim_authoring_allowed": True,
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "source_action": {
                    "surface": "quality_repair_batch",
                    "blocked_reason": "manuscript_story_surface_delta_missing",
                    "source_eval_id": eval_id,
                    "repair_execution_evidence_ref": str(repair_evidence_path),
                },
                "refs": {
                    "source_eval_path": str(source_eval_path),
                    "repair_execution_evidence_path": str(repair_evidence_path),
                },
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
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
            "domain_transition": {
                "study_id": study_id,
                "decision_type": "route_back_same_line",
                "route_target": "finalize",
                "owner": "publication_gate",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "owner_authorized_publication_gate_replay",
                    "lane": "finalize",
                "summary": "Replay the owner-authorized publication gate.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-writer-handoff",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm003-current-gate-replay",
            "source_signature": "truth-snapshot::dm003-current-gate-replay",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(source_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "manuscript_story_surface_delta_missing"
    assert action["next_work_unit"] == "manuscript_story_repair"
    assert action["work_unit_fingerprint"] == "gate-replay-route-back::write::publication-blockers::dm003"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
