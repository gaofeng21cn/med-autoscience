from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_refresh_controller_decisions_for_current_publication_eval_materializes_non_dispatching_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {"owner": "ai_reviewer"},
            "verdict": {"overall_verdict": "blocked"},
        },
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "decision": "resume",
        "reason": "quest_drifting_into_write_without_gate_approval",
        "quest_status": "running",
        "authority_snapshot": {
            "dispatch_gate": {
                "state": "blocked",
                "dispatch_allowed": False,
                "blocking_reasons": ["execution_owner_guard.supervisor_only"],
            }
        },
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "Which claim-evidence repair is still blocking the paper?",
        "route_rationale": "AI reviewer current eval blocks on claim-evidence consistency.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer current eval blocks on claim-evidence consistency.",
        "work_unit_fingerprint": "publication-blockers::current",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    calls: dict[str, object] = {}

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(
        outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **kwargs: (calls.setdefault("tick_request_kwargs", kwargs), tick_request)[1],
    )

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs) -> dict[str, object]:
        calls["materialize_kwargs"] = kwargs
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["surface"] == "domain_owner_action_controller_decision_refresh"
    assert result["refresh_count"] == 1
    assert result["materialized_count"] == 1
    refresh = result["refreshes"][0]
    assert refresh["refresh_status"] == "materialized"
    assert refresh["dispatch_status"] == "recorded_non_dispatching"
    assert calls["tick_request_kwargs"] == {
        "study_root": study_root,
        "status_payload": status_payload,
    }
    assert calls["materialize_kwargs"]["profile"] == profile
    assert calls["materialize_kwargs"]["study_id"] == study_id
    assert calls["materialize_kwargs"]["study_root"] == study_root
    assert calls["materialize_kwargs"]["publication_eval_ref"] == tick_request["publication_eval_ref"]
    assert calls["materialize_kwargs"]["source"] == "domain_owner_action_controller_decision_refresh"

def test_refresh_controller_decision_prepares_opl_runtime_owner_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {"owner": "ai_reviewer"},
            "recommended_actions": [
                {
                    "action_type": "route_back_same_line",
                    "work_unit_fingerprint": work_unit_fingerprint,
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
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 4,
            "retry_state": {"terminal": True},
            "blocked_turn_closeout": {
                "run_id": "old-blocked-run",
                "blocked_reason": "controller_callable_surface_failed_path_normalization",
                "next_owner": "MAS/controller",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "last_controller_decision_authorization": {
                "decision_id": "stale-ai-reviewer-decision",
                "route_target": "write",
                "work_unit_id": "old_work_unit",
                "work_unit_fingerprint": "publication-blockers::old",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "decision": "noop",
        "reason": "controller_work_unit_evidence_adopted",
        "quest_status": "waiting_for_user",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "continue_same_line",
        "route_target": "write",
        "route_key_question": "What paper repair should run next?",
        "route_rationale": "AI reviewer refreshed the current publication blockers.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer refreshed the current publication blockers.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    ensure_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-ai-reviewer-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "write",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": tick_request["next_work_unit"],
            },
        )
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
        }

    def fail_request_opl_stage_attempt(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        raise AssertionError("MAS must not resume OPL-owned runtime workers")

    monkeypatch.setattr(outer_loop, "materialize_non_dispatching_outer_loop_decision", fake_materialize_non_dispatching_outer_loop_decision)
    monkeypatch.setattr(module.domain_status_projection, "request_opl_stage_attempt", fail_request_opl_stage_attempt)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    refresh = result["refreshes"][0]
    runtime_authorization = refresh["runtime_authorization"]
    current_authorization = runtime_authorization["current_controller_authorization"]
    runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
    assert result["materialized_count"] == 1
    assert runtime_authorization["authorization_status"] == "owner_handoff_ready"
    assert runtime_authorization["runtime_resume_status"] == "owner_route_required"
    assert runtime_authorization["queue_owner"] == "one-person-lab"
    assert runtime_authorization["runtime_state_mutated"] is False
    assert runtime_authorization["runtime_owner_handoff"]["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert current_authorization["written"] is False
    assert current_authorization["handoff_ready"] is True
    assert current_authorization["runtime_state_mutated"] is False
    assert current_authorization["decision_id"] == "fresh-ai-reviewer-decision"
    assert current_authorization["cleared_keys"] == [
        "retry_state",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ]
    assert current_authorization["proposed_runtime_state"]["same_fingerprint_auto_turn_count"] == 0
    assert current_authorization["proposed_runtime_state"]["last_controller_decision_authorization"]["decision_id"] == (
        "fresh-ai-reviewer-decision"
    )
    assert runtime_state["same_fingerprint_auto_turn_count"] == 4
    assert "retry_state" in runtime_state
    assert "blocked_turn_closeout" in runtime_state
    assert "last_liveness_reconcile_reason" in runtime_state
    assert ensure_calls == []


def test_refresh_controller_decision_redrives_existing_pending_user_messages(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::obesity-current"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::obesity::current",
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [str(study_root / "paper")],
                "ai_reviewer_required": False,
            },
            "recommended_actions": [
                {
                    "action_type": "route_back_same_line",
                    "work_unit_fingerprint": work_unit_fingerprint,
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
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 9,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "retry_state": {"terminal": True},
            "blocked_turn_closeout": {
                "run_id": "old-obesity-run",
                "blocked_reason": "owner_callable_surface_missing",
                "next_owner": "MAS/controller",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "quest_status": "waiting_for_user",
        "continuation_state": {
            "pending_user_message_count": 9,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
        },
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::obesity::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "continue_same_line",
        "route_target": "analysis-campaign",
        "route_key_question": "Repair claim-evidence before package delivery.",
        "route_rationale": "AI reviewer refreshed publication blockers.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer refreshed publication blockers.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    ensure_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-obesity-ai-reviewer-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "analysis-campaign",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": tick_request["next_work_unit"],
            },
        )
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
        }

    def fail_request_opl_stage_attempt(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        raise AssertionError("MAS must not redrive pending user messages through provider runtime")

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )
    monkeypatch.setattr(module.domain_status_projection, "request_opl_stage_attempt", fail_request_opl_stage_attempt)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    runtime_authorization = result["refreshes"][0]["runtime_authorization"]
    pending_handoff = runtime_authorization["existing_pending_user_message_resume"]
    runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
    assert runtime_authorization["authorization_status"] == "pending_user_message_owner_handoff_ready"
    assert runtime_authorization["current_controller_authorization"]["reason"] == "pending_user_messages_present"
    assert pending_handoff["marked"] is True
    assert pending_handoff["runtime_state_mutated"] is False
    assert pending_handoff["delegated_runtime_owner"] == "one-person-lab"
    assert pending_handoff["proposed_runtime_state"]["continuation_anchor"] == "user_message_queue"
    assert runtime_authorization["runtime_resume_status"] == "owner_route_required"
    assert runtime_authorization["queue_owner"] == "one-person-lab"
    assert runtime_state["continuation_policy"] == "wait_for_user_or_resume"
    assert runtime_state["pending_user_message_count"] == 9
    assert "retry_state" in runtime_state
    assert "blocked_turn_closeout" in runtime_state
    assert ensure_calls == []


def test_refresh_controller_decision_preserves_live_worker_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    live_run_id = "mas-run-003-live"
    work_unit_fingerprint = "publication-blockers::fresh"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {"owner": "ai_reviewer"},
            "recommended_actions": [
                {
                    "action_type": "route_back_same_line",
                    "work_unit_fingerprint": work_unit_fingerprint,
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
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": live_run_id,
            "worker_running": True,
            "worker_pending": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 2,
            "retry_state": {"attempt": 1},
        },
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "decision": "noop",
        "quest_status": "running",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "continue_same_line",
        "route_target": "write",
        "route_key_question": "What paper repair should run next?",
        "route_rationale": "AI reviewer refreshed the current publication blockers.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer refreshed the current publication blockers.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    ensure_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-ai-reviewer-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "write",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": tick_request["next_work_unit"],
            },
        )
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
        }

    def fail_request_opl_stage_attempt(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        raise AssertionError("MAS must not touch a live OPL-owned worker")

    monkeypatch.setattr(outer_loop, "materialize_non_dispatching_outer_loop_decision", fake_materialize_non_dispatching_outer_loop_decision)
    monkeypatch.setattr(module.domain_status_projection, "request_opl_stage_attempt", fail_request_opl_stage_attempt)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
    runtime_authorization = result["refreshes"][0]["runtime_authorization"]
    authorization = runtime_authorization["current_controller_authorization"]
    assert runtime_state["active_run_id"] == live_run_id
    assert runtime_state["worker_running"] is True
    assert runtime_state["worker_pending"] is False
    assert "retry_state" in runtime_state
    assert authorization["runtime_state_mutated"] is False
    assert authorization["proposed_runtime_state"]["last_controller_decision_authorization"]["decision_id"] == (
        "fresh-ai-reviewer-decision"
    )
    assert "worker_state_preserved" not in authorization
    assert "preserved_active_run_id" not in authorization
    assert runtime_authorization["runtime_owner_handoff"]["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert ensure_calls == []


def test_refresh_controller_decisions_for_current_publication_eval_dry_run_does_not_materialize(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    status_payload = {"study_id": study_id, "quest_id": study_id, "quest_status": "running"}
    tick_request = {
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "bounded_analysis",
        "reason": "AI reviewer current eval blocks on claim-evidence consistency.",
    }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        lambda **_: (_ for _ in ()).throw(AssertionError("dry run must not materialize controller decision")),
    )

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["dry_run"] is True
    assert result["materialized_count"] == 0
    assert result["refreshes"][0]["refresh_status"] == "dry_run"
    assert result["refreshes"][0]["publication_eval_ref"]["eval_id"] == "publication-eval::current"


def test_execute_dispatch_refreshes_controller_decision_after_ai_reviewer_materializes_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    input_refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
        "review_ledger": {
            "path": str(study_root / "paper" / "review" / "review_ledger.json"),
            "present": True,
            "valid": True,
        },
        "study_charter": {
            "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "present": True,
            "valid": True,
        },
        "medical_manuscript_blueprint": {
            "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "present": True,
            "valid": True,
        },
        "claim_evidence_map": {
            "path": str(study_root / "paper" / "claim_evidence_map.json"),
            "present": True,
            "valid": True,
        },
        "medical_prose_review": {
            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "present": True,
            "valid": True,
        },
        "publication_gate_projection": {
            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "present": True,
            "valid": True,
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": {
                "eval_id": "publication-eval::stale",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
                "future_facing_limitations_plan": [
                    {
                        "limitation": "The manuscript requires current AI reviewer materialization before route-back.",
                        "impact_on_claim": "Claims must remain tied to reviewer-authorized evidence.",
                        "required_future_analysis_data_or_design": "Use the refreshed publication evaluation.",
                        "current_manuscript_wording_must_be_restrained": True,
                    }
                ],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)

    def fake_run_ai_reviewer_publication_eval_workflow(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "eval_id": "publication-eval::current",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "assessment_provenance": {"owner": "ai_reviewer"},
            },
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval::current",
        }

    status_payload = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "decision": "resume",
        "reason": "runtime_active",
        "quest_status": "running",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "continue_same_line",
        "route_target": "write",
        "route_key_question": "What manuscript repair should run next?",
        "route_rationale": "AI reviewer refreshed the current publication blockers.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer refreshed the current publication blockers.",
        "work_unit_fingerprint": "work-unit::current",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    refresh_called: dict[str, object] = {}

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(
        outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **kwargs: (refresh_called.setdefault("tick_request_kwargs", kwargs), tick_request)[1],
    )

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs) -> dict[str, object]:
        refresh_called["materialize_kwargs"] = kwargs
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    refresh = execution["owner_result"]["controller_decision_refresh"]
    assert refresh["refresh_status"] == "materialized"
    assert refresh["dispatch_status"] == "recorded_non_dispatching"
    assert refresh_called["tick_request_kwargs"] == {
        "study_root": study_root,
        "status_payload": status_payload,
    }
    assert refresh_called["materialize_kwargs"]["profile"] == profile
    assert refresh_called["materialize_kwargs"]["study_id"] == study_id
    assert refresh_called["materialize_kwargs"]["study_root"] == study_root
    assert refresh_called["materialize_kwargs"]["status_payload"] == status_payload
    assert refresh_called["materialize_kwargs"]["publication_eval_ref"] == tick_request["publication_eval_ref"]
    assert refresh_called["materialize_kwargs"]["next_work_unit"] == tick_request["next_work_unit"]
    assert refresh_called["materialize_kwargs"]["blocking_work_units"] == tick_request["blocking_work_units"]
    assert refresh_called["materialize_kwargs"]["source"] == "ai_reviewer_publication_eval_workflow"
