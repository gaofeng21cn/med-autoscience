from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_owner_route_allows_quality_repair_batch_for_write_route() -> None:
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "truth_epoch": "truth-epoch-dm003-medical-prose",
        "runtime_health_epoch": "runtime-health-dm003-medical-prose",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "failure_signature": "opl_stage_attempt_admission_required",
        "trace_id": "owner-route-trace::dm003::medical-prose",
        "route_epoch": "truth-epoch-dm003-medical-prose",
        "source_fingerprint": "truth-source-dm003-medical-prose",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "opl_stage_attempt_admission_required",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "idempotency_key": "owner-route::dm003::medical-prose",
    }
    action = {
        "action_type": "run_quality_repair_batch",
        "next_executable_owner": "write",
        "owner_route": owner_route,
    }

    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    assert owner_route_module.route_allows_action(action=action, owner_route=owner_route) is True


def test_owner_route_registers_domain_transition_publication_gate_blocker() -> None:
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "truth_epoch": "truth-epoch-dm003-publication-gate",
        "runtime_health_epoch": "runtime-health-dm003-publication-gate",
        "work_unit_fingerprint": "domain-transition::publication_gate_blocker::publication_gate_replay",
        "failure_signature": "domain_transition_publication_gate_blocker",
        "trace_id": "owner-route-trace::dm003::publication-gate",
        "route_epoch": "truth-epoch-dm003-publication-gate",
        "source_fingerprint": "truth-source-dm003-publication-gate",
        "current_owner": "mas_controller",
        "next_owner": "gate_clearing_batch",
        "owner_reason": "domain_transition_publication_gate_blocker",
        "active_run_id": None,
        "allowed_actions": ["run_gate_clearing_batch"],
        "blocked_actions": [],
        "source_refs": {"work_unit_id": "publication_gate_replay"},
        "idempotency_key": "owner-route::dm003::publication-gate",
    }
    protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")

    decorated = protocol.decorate_owner_route(owner_route)

    assert decorated["allowed_actions"] == ["run_gate_clearing_batch"]
    assert decorated["owner_reason_contract"]["registered"] is True
    assert decorated["owner_reason_contract"]["owner"] == "gate_clearing_batch"
    assert decorated["owner_reason_contract"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert decorated["owner_route_attempt_protocol"]["dispatchable"] is True


def test_scan_domain_routes_projects_parked_macro_state_as_current_truth_owner_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    cases = {
        "001-submit-info": {
            "reason": "quest_waiting_for_submission_metadata",
            "quality_state": {},
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "external_metadata_pending",
                "auto_execution_complete": True,
            },
            "expected_reason": "external_info",
            "expected_user_next": "submit_info",
        },
        "002-stop-loss": {
            "reason": "publishability_stop_loss_recommended",
            "quality_state": {"state": "stop_loss_recommended"},
            "auto_runtime_parked": {"parked": False, "auto_execution_complete": False},
            "expected_reason": "stop_loss",
            "expected_user_next": "none",
        },
        "003-user-stop": {
            "reason": "manual_stop",
            "quality_state": {"state": "user_stopped"},
            "auto_runtime_parked": {"parked": False, "auto_execution_complete": False},
            "expected_reason": "user_stop",
            "expected_user_next": "none",
        },
    }
    statuses: dict[str, dict] = {}
    progresses: dict[str, dict] = {}
    quest_ids: dict[str, str] = {}
    publication_evals: dict[str, dict] = {}
    for study_id, case in cases.items():
        quest_id = f"quest-{study_id}"
        study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
        quest_root = profile.runtime_root / quest_id
        publication_eval = {
            "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            "recommended_actions": [],
        }
        statuses[study_id] = {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "quest_status": "paused",
            "decision": "resume",
            "reason": case["reason"],
            "active_run_id": None,
            "auto_runtime_parked": case["auto_runtime_parked"],
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": f"truth-epoch-{study_id}",
                "source_signature": f"truth-source-{study_id}",
                "quality_state": case["quality_state"],
            },
        }
        progresses[study_id] = {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "auto_runtime_parked": case["auto_runtime_parked"],
            "supervision": {"active_run_id": None, "health_status": "escalated"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
            },
        }
        quest_ids[study_id] = quest_id
        publication_evals[study_id] = publication_eval

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda *, study_id, **_: (
            statuses[study_id],
            progresses[study_id],
            quest_ids[study_id],
            publication_evals[study_id],
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=tuple(cases),
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    for study in result["studies"]:
        case = cases[study["study_id"]]
        macro_source = study["owner_route"]["source_refs"]["study_macro_state"]
        assert macro_source["writer_state"] == "parked"
        assert macro_source["user_next"] == case["expected_user_next"]
        assert macro_source["reason"] == case["expected_reason"]
        assert macro_source["source_fingerprint"].startswith("study-macro-state::")
        assert study["action_queue"] == []
        assert study["ai_repair_lifecycle"] is None
        assert study["why_not_applied"] is None
        assert study["blocked_reason"] is None
        assert study["next_owner"] is None
        assert study["external_supervisor_required"] is False
        assert study["owner_route"]["current_owner"] == "controller_stop"
        assert study["owner_route"]["next_owner"] is None
        assert study["owner_route"]["owner_reason"] is None


def test_owner_route_fallback_source_fingerprint_tracks_action_payload_targets() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_route")
    base = {
        "action_type": "publication_gate_specificity_required",
        "owner": "publication_gate",
        "reason": "publication_gate_specificity_required",
        "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
    }
    common_kwargs = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "quest_id": "quest-dm002",
        "status": {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "running",
            "reason": "publication_gate_specificity_required",
            "active_run_id": "run-dm002",
        },
        "progress": {
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
        },
        "blocked_reason": "publication_gate_specificity_required",
        "next_owner": "publication_gate",
        "active_run_id": "run-dm002",
    }

    claim_route = module.build_owner_route(
        **common_kwargs,
        actions=[{**base, "missing_target_kinds": ["claim"]}],
    )
    metric_route = module.build_owner_route(
        **common_kwargs,
        actions=[{**base, "missing_target_kinds": ["metric"]}],
    )

    assert claim_route["route_epoch"] == metric_route["route_epoch"]
    assert claim_route["source_fingerprint"] != metric_route["source_fingerprint"]
    assert claim_route["idempotency_key"] != metric_route["idempotency_key"]


def test_owner_route_requires_explicit_allowed_action_for_dispatch_execution() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_route")
    action = {
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_assessment_required",
    }
    route = {
        "next_owner": "ai_reviewer",
        "owner_reason": "return_to_ai_reviewer_workflow",
        "allowed_actions": [],
    }

    assert module.route_allows_action(action=action, owner_route=route) is False
    assert module.route_allows_action(
        action=action,
        owner_route={**route, "allowed_actions": ["return_to_ai_reviewer_workflow"]},
    ) is True


def test_registered_owner_route_decorator_keeps_missing_allowed_action_non_dispatchable() -> None:
    protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "truth_epoch": "truth-event-000010-4ddbf4400d949140",
        "runtime_health_epoch": "runtime-health-event-006183-d2a90e5b59194b50",
        "work_unit_fingerprint": "truth-snapshot::17370fc349aa055738904f6a",
        "route_epoch": "truth-event-000010-4ddbf4400d949140",
        "source_fingerprint": "truth-snapshot::17370fc349aa055738904f6a",
        "current_owner": "mas_controller",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
        "failure_signature": "ai_reviewer_record_stale_after_current_manuscript",
        "allowed_actions": [],
        "blocked_actions": [
            "return_to_ai_reviewer_workflow",
            "run_quality_repair_batch",
            "run_gate_clearing_batch",
        ],
        "source_refs": {
            "study_truth_epoch": "truth-event-000010-4ddbf4400d949140",
            "runtime_health_epoch": "runtime-health-event-006183-d2a90e5b59194b50",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "truth-snapshot::17370fc349aa055738904f6a",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
        },
    }

    decorated = protocol.decorate_owner_route(route)

    assert decorated["allowed_actions"] == []
    assert "return_to_ai_reviewer_workflow" in decorated["blocked_actions"]
    assert decorated["owner_reason_contract"]["registered"] is True
    assert decorated["owner_reason_contract"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert decorated["owner_route_attempt_protocol"]["dispatchable"] is False


def test_owner_route_scan_consumer_and_executor_share_contract_import() -> None:
    shared = importlib.import_module("med_autoscience.runtime_control.owner_route")
    modules = [importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")]

    for module in modules:
        assert module.owner_route_part.build_owner_route is shared.build_owner_route
        assert module.owner_route_part.owner_route_matches is shared.owner_route_matches
        assert module.owner_route_part.route_allows_action is shared.route_allows_action

    stage_outcome_authority = importlib.import_module(
        "med_autoscience.controllers.stage_outcome_authority"
    )
    assert not hasattr(stage_outcome_authority, "owner_route_part")
    assert not hasattr(stage_outcome_authority, "_execute_ai_reviewer_workflow")


def test_scan_domain_routes_routes_incomplete_completion_contract_to_completion_evidence_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": "002-risk",
                "study_root": str(study_root),
                "quest_id": "quest-002",
                "quest_root": str(profile.managed_runtime_home / "quests" / "quest-002"),
                "quest_status": "completed",
                "decision": "blocked",
                "reason": "study_completion_contract_not_ready",
                "study_completion_contract": {
                    "ready": False,
                    "status": "incomplete",
                    "completion_status": "completed",
                    "summary": "Study delivery declared complete.",
                    "missing_evidence_paths": ["manuscript/submission_package.zip"],
                },
            },
            {
                "study_id": "002-risk",
                "quest_id": "quest-002",
                "current_stage": "runtime_blocked",
                "intervention_lane": {
                    "lane_id": "completion_evidence_required",
                    "recommended_action_id": "sync_completion_evidence",
                },
                "current_blockers": ["study-level 完成声明已存在，但 final submission 证据还未补齐。"],
                "study_completion_contract": {
                    "ready": False,
                    "status": "incomplete",
                    "missing_evidence_paths": ["manuscript/submission_package.zip"],
                },
            },
            "quest-002",
            {},
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=["002-risk"],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["next_owner"] == "completion_evidence"
    assert study["blocked_reason"] == "study_completion_contract_not_ready"
    assert study["external_supervisor_required"] is False
    assert study["action_queue"] == []
    assert study["owner_route"]["next_owner"] == "completion_evidence"
    assert study["owner_route"]["owner_reason"] == "study_completion_contract_not_ready"


def test_scan_domain_routes_completed_truth_suppresses_stale_repair_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": "002-risk",
                "study_root": str(study_root),
                "quest_id": "quest-002",
                "quest_root": str(profile.managed_runtime_home / "quests" / "quest-002"),
                "quest_status": "completed",
                "decision": "completed",
                "reason": "quest_already_completed",
                "study_completion_contract": {
                    "ready": True,
                    "status": "resolved",
                    "completion_status": "completed",
                    "summary": "Study delivery declared complete.",
                    "missing_evidence_paths": [],
                },
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-completed",
                    "source_signature": "completion-source",
                },
            },
            {
                "study_id": "002-risk",
                "quest_id": "quest-002",
                "current_stage": "study_completed",
                "intervention_lane": {
                    "lane_id": "completed",
                    "recommended_action_id": "inspect_progress",
                },
                "ai_repair_lifecycle": {
                    "state": "blocked",
                    "blocked_reason": "runtime_recovery_not_authorized",
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                },
                "quality_review_loop": {
                    "closure_state": "quality_repair_required",
                },
            },
            "quest-002",
            {
                "assessment_provenance": {
                    "owner": "mechanical_projection",
                    "ai_reviewer_required": True,
                },
            },
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=["002-risk"],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["next_owner"] is None
    assert study["blocked_reason"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] is None
    assert study["owner_route"]["owner_reason"] is None
