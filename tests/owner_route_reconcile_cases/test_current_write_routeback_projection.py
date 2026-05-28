from __future__ import annotations

from pathlib import Path
import json

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_projects_current_write_routeback_despite_stale_progress_active_run(monkeypatch, tmp_path: Path) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    opl_attempts = __import__(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts",
        fromlist=["opl_provider_attempts"],
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002-write-route",
            "canonical_runtime_action": "continue_supervising_runtime",
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Controller-authorized paper repair and package rebuild from latest evidence.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-write-route",
            "source_signature": "truth-source-dm002-write-route",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": "mas-run-stale-progress-only",
        "supervision": {"active_run_id": "mas-run-stale-progress-only", "health_status": "stale"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )
    seen_preferred_actions: list[dict[str, object]] = []

    def fake_live_provider_attempt_for_study(**kwargs: object) -> None:
        seen_preferred_actions.extend(dict(action) for action in kwargs.get("preferred_actions") or [])
        return None

    monkeypatch.setattr(
        opl_attempts,
        "live_provider_attempt_for_study",
        fake_live_provider_attempt_for_study,
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    macro_source = study["owner_route"]["source_refs"]["study_macro_state"]
    assert macro_source["writer_state"] == "queued"
    assert macro_source["user_next"] == "repair"
    assert macro_source["reason"] == "quality"
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    assert [item["action_type"] for item in result["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["next_work_unit"] == "dm002_same_line_publication_paper_repair"
    assert study["active_run_id"] is None
    assert study["owner_route"]["active_run_id"] is None
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["blocked_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["next_owner"] == "write"
    assert [action["action_type"] for action in seen_preferred_actions] == ["run_quality_repair_batch"]
    assert seen_preferred_actions[0]["next_work_unit"] == "dm002_same_line_publication_paper_repair"


def test_fresh_ai_reviewer_write_routeback_supersedes_stale_reviewer_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
            "runtime_health_epoch": "runtime-health-dm003-ai-reviewer-write-route",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-ai-reviewer-write-route",
            "source_signature": "truth-source-dm003-ai-reviewer-write-route",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::medical-prose-routeback::sha256-current",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "blocked"},
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "write",
                    "overall_style_verdict": "revise",
                }
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "reason": "Repair current AI reviewer manuscript-quality concerns.",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair Methods, n/N reporting, tables, and journal prose.",
                },
            }
        ],
    }
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
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "domain-transition::route_back_same_line::medical_prose_write_repair"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["source_refs"]["source_eval_id"] == publication_eval_payload["eval_id"]


def test_current_ai_reviewer_claim_evidence_write_routeback_preempts_gate_replay_loop(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::current-manuscript-claim-evidence-routeback"
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "publication_gate_blocker",
            "route_target": "review",
            "controller_action": "run_gate_clearing_batch",
            "owner": "publication_gate",
            "next_work_unit": {
                "unit_id": "publication_gate_replay",
                "lane": "review",
                "summary": "Replay the MAS publication gate and route blockers to a bounded repair unit.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-gate-replay-blocked",
            "canonical_runtime_action": "external_supervisor_required",
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-gate-replay-blocked",
            "source_signature": "truth-source-dm003-gate-replay-blocked",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
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
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "write",
                    "overall_style_verdict": "revise",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                },
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "reason": "Reconcile current manuscript claim-evidence provenance before gate replay.",
                "work_unit_fingerprint": (
                    "current-manuscript-ai-reviewer-routeback::write::sha256:manuscript-current"
                ),
                "next_work_unit": {
                    "unit_id": "current_manuscript_claim_evidence_alignment_repair",
                    "lane": "write",
                    "summary": "Repair or explicitly reconcile the boundary-metric evidence path before gate replay.",
                },
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "status": "blocked",
            "work_unit": {"unit_id": "publication_gate_replay", "lane": "review"},
            "unit_statuses": [
                {"unit_id": "repair_paper_live_paths", "status": "current"},
                {"unit_id": "materialize_display_surface", "status": "materialized"},
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
            ],
            "gate_replay_status": "blocked",
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
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["next_work_unit"] == "current_manuscript_claim_evidence_alignment_repair"
    assert action["required_output_surface"] == (
        "claim-evidence map and evidence ledger alignment or "
        "typed blocker:claim_evidence_alignment_required"
    )
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
