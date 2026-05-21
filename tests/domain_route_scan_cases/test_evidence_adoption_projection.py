from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_route_scan_cases.owner_route_test_helpers import assert_owner_route_required
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_routes_adopted_work_unit_evidence_to_publication_gate_recheck(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            }
        ],
    }

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("adopted work unit evidence must not relaunch the runtime worker")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_called)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "active",
                "decision": "noop",
                "reason": "controller_work_unit_evidence_adopted",
                "active_run_id": None,
                "runtime_liveness_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": [
                        "quest_marked_running_but_no_live_session",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "controller_work_unit_next_route": {
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "owner": "publication_gate",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": False,
                },
                "controller_work_unit_evidence_adoption": {
                    "already_recorded": True,
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "route_target": "analysis-campaign",
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "result": {
                        "local_traceability_repair_complete": True,
                        "unresolved_local_defect_count": 0,
                    },
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-adopted-work-unit",
                    "source_signature": "truth-source-adopted-work-unit",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "analysis-campaign",
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "ai_repair_lifecycle": {
                    "state": "blocked",
                    "authority": "external_supervisor",
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "projection_only": True,
                },
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )
    previous_scan_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    previous_scan_path.parent.mkdir(parents=True, exist_ok=True)
    previous_scan_path.write_text(
        """
{
  "surface": "portable_domain_route_scan",
  "schema_version": 1,
  "studies": [
    {
      "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
      "meaningful_artifact_delta": false,
      "owner_route": {
        "work_unit_fingerprint": "truth-source-analysis-handoff"
      }
    }
  ],
  "action_queue": []
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["runtime_platform_repair_apply"] is None
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] == "publication_gate_recheck_required"
    assert study["blocked_reason"] == "publication_gate_recheck_required"
    assert study["next_owner"] == "publication_gate"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "publication_gate"
    assert study["owner_route"]["owner_reason"] == "publication_gate_recheck_required"
    assert study["owner_route"]["allowed_actions"] == []
    assert result["queue_history"]["latest_action_count"] == 0


def test_scan_domain_routes_routes_analysis_handoff_to_next_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            }
        ],
    }

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("analysis handoff must not redrive the exhausted analysis lane")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_called)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "noop",
                "reason": "controller_work_unit_evidence_adopted",
                "active_run_id": "run-analysis-handoff",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-analysis-handoff",
                    "runtime_audit": {
                        "status": "live",
                        "worker_running": True,
                        "active_run_id": "run-analysis-handoff",
                    },
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "recover_runtime",
                    "attempt_state": "recovering",
                    "retry_budget_remaining": 3,
                    "worker_liveness_state": {
                        "state": "activity_timeout",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "run-analysis-handoff",
                    },
                    "blocking_reasons": [
                        "live_worker_meaningful_artifact_delta_timeout",
                        "same_fingerprint_loop",
                    ],
                },
                "controller_work_unit_next_route": {
                    "recommended_next_route": "handoff_to_next_owner",
                    "owner": "write/ai_reviewer",
                    "next_work_unit": "manuscript_story_repair",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": False,
                },
                "controller_work_unit_evidence_adoption": {
                    "already_recorded": True,
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "route_target": "analysis-campaign",
                    "recommended_next_route": "handoff_to_next_owner",
                    "analysis_lane_status": "exhausted_for_current_fingerprint",
                    "next_owner": "write/ai_reviewer",
                    "next_work_unit": "manuscript_story_repair",
                    "result": {
                        "local_traceability_repair_complete": True,
                        "analysis_lane_status": "exhausted_for_current_fingerprint",
                        "meaningful_artifact_delta": True,
                    },
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-analysis-handoff",
                    "source_signature": "truth-source-analysis-handoff",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "supervision": {"active_run_id": "run-analysis-handoff", "health_status": "live"},
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["reason"] == "controller_work_unit_owner_handoff_required"
    assert action["owner"] == "write/ai_reviewer"
    assert action["request_owner"] == "write/ai_reviewer"
    assert action["recommended_owner"] == "write/ai_reviewer"
    assert action["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert action["next_work_unit"] == "manuscript_story_repair"
    assert action["paper_package_mutation_allowed"] is False
    assert action["medical_claim_authoring_allowed"] is False
    assert study["runtime_platform_repair_apply"] is None
    assert study["why_not_applied"] == "controller_work_unit_owner_handoff_required"
    assert study["blocked_reason"] == "controller_work_unit_owner_handoff_required"
    assert study["next_owner"] == "write/ai_reviewer"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "write/ai_reviewer"
    assert study["owner_route"]["owner_reason"] == "controller_work_unit_owner_handoff_required"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert result["queue_history"]["latest_action_count"] == 1
    request_packet = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "requests"
            / "ai_reviewer"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert request_packet["source_workflow_ref"]["next_work_unit"] == "manuscript_story_repair"
    assert request_packet["source_workflow_ref"]["route_back_target"] == "write/ai_reviewer"
    assert request_packet["blockers"] == ["controller_work_unit_owner_handoff_required"]


def test_scan_domain_routes_preserves_owner_handoff_when_platform_redrive_adopts_evidence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            }
        ],
    }

    def fake_apply_runtime_platform_repair(**_: object) -> dict[str, object]:
        return {
            "action_type": "runtime_platform_repair",
            "dispatch_status": "blocked",
            "reason": "runtime_relaunch_no_live_run_started",
            "repair_kind": "pending_runtime_platform_repair_redrive",
            "domain_owner_result": {
                "decision": "noop",
                "reason": "controller_work_unit_evidence_adopted",
                "quest_status": "waiting_for_user",
                "controller_work_unit_next_route": {
                    "recommended_next_route": "handoff_to_next_owner",
                    "owner": "write/ai_reviewer",
                    "next_work_unit": "manuscript_story_repair",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": False,
                },
                "controller_work_unit_evidence_adoption": {
                    "already_recorded": True,
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "route_target": "analysis-campaign",
                    "recommended_next_route": "handoff_to_next_owner",
                    "analysis_lane_status": "exhausted_for_current_fingerprint",
                    "next_owner": "write/ai_reviewer",
                    "next_work_unit": "manuscript_story_repair",
                    "result": {
                        "local_traceability_repair_complete": True,
                        "analysis_lane_status": "exhausted_for_current_fingerprint",
                        "meaningful_artifact_delta": True,
                    },
                },
            },
        }

    monkeypatch.setattr(module.platform_repair, "apply_runtime_platform_repair", fake_apply_runtime_platform_repair)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "waiting_for_user",
                "decision": "resume",
                "reason": "quest_waiting_platform_repair_redrive",
                "active_run_id": None,
                "runtime_liveness_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
                },
                "continuation_state": {
                    "active_run_id": None,
                    "status": "waiting_for_user",
                    "continuation_policy": "auto",
                    "continuation_anchor": "decision",
                    "continuation_reason": "controller_work_unit_pending",
                    "pending_user_message_count": 0,
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": [
                        "quest_marked_running_but_no_live_session",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-platform-handoff",
                    "source_signature": "truth-source-platform-handoff",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "blocked"
    assert study["why_not_applied"] == "controller_work_unit_owner_handoff_required"
    assert study["blocked_reason"] == "controller_work_unit_owner_handoff_required"
    assert study["next_owner"] == "write/ai_reviewer"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "write/ai_reviewer"
    assert study["owner_route"]["owner_reason"] == "controller_work_unit_owner_handoff_required"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def test_scan_domain_routes_redrives_adopted_handoff_when_progress_activity_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::497d1260db522f01"
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": str(
                            quest_root
                            / "artifacts"
                            / "reports"
                            / "medical_publication_surface"
                            / "latest.json"
                        ),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "decision-adopted-handoff-timeout-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": "run-adopted-timeout",
            "worker_running": True,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 5,
        },
    )

    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "decision-adopted-handoff-timeout-redrive"
        assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
        assert runtime_state["active_run_id"] is None
        assert runtime_state["worker_running"] is False
        assert runtime_state["same_fingerprint_auto_turn_count"] == 0
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "resume_postcondition": {
                "effective": True,
                "active_run_id": "run-adopted-timeout-redriven",
                "scheduled": True,
                "started": True,
                "queued": False,
            },
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "noop",
                "reason": "controller_work_unit_evidence_adopted",
                "active_run_id": "run-adopted-timeout",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-adopted-timeout",
                    "runtime_audit": {
                        "status": "live",
                        "worker_running": True,
                        "active_run_id": "run-adopted-timeout",
                    },
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                    "attempt_state": "live",
                    "retry_budget_remaining": 3,
                    "worker_liveness_state": {
                        "state": "live",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "run-adopted-timeout",
                    },
                    "blocking_reasons": [],
                },
                "controller_work_unit_next_route": {
                    "recommended_next_route": "handoff_to_next_owner",
                    "owner": "write/ai_reviewer",
                    "next_work_unit": "manuscript_story_repair",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": False,
                },
                "controller_work_unit_evidence_adoption": {
                    "already_recorded": True,
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "route_target": "analysis-campaign",
                    "recommended_next_route": "handoff_to_next_owner",
                    "analysis_lane_status": "exhausted_for_current_fingerprint",
                    "next_owner": "write/ai_reviewer",
                    "next_work_unit": "manuscript_story_repair",
                    "result": {
                        "local_traceability_repair_complete": True,
                        "analysis_lane_status": "exhausted_for_current_fingerprint",
                        "meaningful_artifact_delta": True,
                    },
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "supervision": {"active_run_id": "run-adopted-timeout", "health_status": "live"},
                "progress_freshness": {
                    "activity_timeout": {
                        "state": "timed_out",
                        "active_run_id": "run-adopted-timeout",
                        "breach_types": ["same_fingerprint_loop"],
                    }
                },
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason="runtime_controller_redrive_required",
    )
    assert apply_result["repair_kind"] == "live_activity_timeout_current_controller_redrive"
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == (
        "decision-adopted-handoff-timeout-redrive"
    )
    assert study["blocked_reason"] == "controller_work_unit_owner_handoff_required"
    assert study["next_owner"] == "write/ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_keeps_runtime_redrive_when_adopted_work_unit_did_not_clear_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "blocking_reason": "claim_evidence_consistency_failed",
                    }
                ],
            }
        ],
    }
    (study_root / "artifacts" / "publication_eval").mkdir(parents=True, exist_ok=True)
    (study_root / "artifacts" / "publication_eval" / "latest.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (study_root / "artifacts" / "controller_decisions").mkdir(parents=True, exist_ok=True)
    (study_root / "artifacts" / "controller_decisions" / "latest.json").write_text(
        """
{
  "schema_version": 1,
  "decision_id": "decision-current-redrive",
  "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
  "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
  "requires_human_confirmation": false,
  "controller_actions": [{"action_type": "run_quality_repair_batch"}],
  "route_target": "write",
  "work_unit_fingerprint": "publication-blockers::current",
  "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"}
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "active",
                "decision": "noop",
                "reason": "controller_work_unit_evidence_adopted",
                "active_run_id": None,
                "runtime_liveness_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": [
                        "quest_marked_running_but_no_live_session",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "controller_work_unit_next_route": {
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "owner": "publication_gate",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": True,
                },
                "controller_work_unit_evidence_adoption": {
                    "already_recorded": True,
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "route_target": "analysis-campaign",
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "result": {
                        "local_traceability_repair_complete": True,
                        "specificity_targets_repaired_or_classified": 5,
                        "missing_target_files_after_repair": 0,
                        "targets_with_repair_markers": 5,
                        "publication_gate_cleared": False,
                        "writing_ready_after_repair": False,
                        "finalize_ready_after_repair": False,
                    },
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-adopted-work-unit",
                    "source_signature": "truth-source-adopted-work-unit",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=False,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    assert study["action_queue"][0]["owner"] == "mas_controller"
    assert study["action_queue"][0]["reason"] == "runtime_controller_redrive_required"
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "mas_controller"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]


def test_scan_domain_routes_projects_live_activity_timeout_current_controller_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            }
        ],
    }
    (study_root / "artifacts" / "controller_decisions").mkdir(parents=True, exist_ok=True)
    (study_root / "artifacts" / "controller_decisions" / "latest.json").write_text(
        """
{
  "schema_version": 1,
  "decision_id": "decision-live-timeout-redrive",
  "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
  "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
  "requires_human_confirmation": false,
  "controller_actions": [{"action_type": "run_quality_repair_batch"}],
  "route_target": "write",
  "work_unit_fingerprint": "publication-blockers::current",
  "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"}
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "noop",
                "reason": "quest_already_running",
                "active_run_id": "run-live-timeout",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-live-timeout",
                    "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-live-timeout"},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "recover_runtime",
                    "attempt_state": "recovering",
                    "retry_budget_remaining": 3,
                    "worker_liveness_state": {
                        "state": "activity_timeout",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "run-live-timeout",
                    },
                    "blocking_reasons": [
                        "live_worker_meaningful_artifact_delta_timeout",
                        "same_fingerprint_loop",
                    ],
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-live-timeout",
                    "source_signature": "truth-source-live-timeout",
                    "canonical_next_action": "resume_same_study_line",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "supervision": {"active_run_id": "run-live-timeout", "health_status": "recovering"},
                "quality_review_loop": {"closure_state": "review_required"},
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=False,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    assert study["action_queue"][0]["owner"] == "mas_controller"
    assert study["action_queue"][0]["reason"] == "runtime_controller_redrive_required"
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "mas_controller"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["current_owner"] == "managed_runtime"
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]
