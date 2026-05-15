from __future__ import annotations

import importlib
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_refresh_domain_transition_controller_decision_authorizes_runtime_without_publication_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {"owner": "ai_reviewer"},
            "recommended_actions": [],
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
            "last_controller_decision_authorization": {
                "decision_id": "stale-write-decision",
                "route_target": "write",
                "work_unit_id": "MAS/MDS-supervised revised manuscript package",
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
        "route_target": "review",
        "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
        "route_rationale": "Mechanical or stale publication projection cannot authorize quality closure.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "Return current manuscript and evidence refs to the AI reviewer workflow.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {
            "unit_id": "ai_reviewer_recheck",
            "lane": "review",
            "summary": "Return current manuscript and evidence refs to the AI reviewer workflow.",
        },
        "blocking_work_units": [{"unit_id": "ai_reviewer_recheck", "lane": "review"}],
    }
    resume_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-domain-transition-ai-reviewer-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "review",
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

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        resume_calls.append(dict(kwargs))
        runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "fresh-domain-transition-ai-reviewer-decision"
        assert authorization["controller_actions"] == ["return_to_ai_reviewer_workflow"]
        assert authorization["route_target"] == "review"
        assert authorization["work_unit_id"] == "ai_reviewer_recheck"
        assert authorization["work_unit_fingerprint"] == work_unit_fingerprint
        assert authorization["next_work_unit"]["unit_id"] == "ai_reviewer_recheck"
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "resume",
            "quest_status": "running",
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    refresh = result["refreshes"][0]
    runtime_authorization = refresh["runtime_authorization"]
    assert result["materialized_count"] == 1
    assert runtime_authorization["authorization_status"] == "written"
    assert runtime_authorization["runtime_resume_status"] == "requested"
    assert runtime_authorization["current_controller_authorization"]["decision_id"] == (
        "fresh-domain-transition-ai-reviewer-decision"
    )
    assert len(resume_calls) == 1


def test_refresh_bundle_stage_domain_transition_controller_decision_authorizes_finalize_runtime(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "status": "clear",
            "allow_write": True,
            "recommended_actions": [],
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
            "last_controller_decision_authorization": {
                "decision_id": "stale-rebuttal-coverage-decision",
                "route_target": "analysis-campaign",
                "work_unit_id": "paper/rebuttal/review_matrix.md and action_plan.md",
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
        "route_target": "finalize",
        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": "The publication gate is clear and bundle-stage work is now on the critical path.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "Synchronize submission authority and package closure for the bundle-stage.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
            "summary": "Synchronize submission authority and package closure for the bundle-stage.",
        },
        "blocking_work_units": [{"unit_id": "submission_authority_sync_closure", "lane": "controller"}],
    }
    resume_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-domain-transition-bundle-stage-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "finalize",
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

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        resume_calls.append(dict(kwargs))
        runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "fresh-domain-transition-bundle-stage-decision"
        assert authorization["controller_actions"] == ["ensure_study_runtime"]
        assert authorization["route_target"] == "finalize"
        assert authorization["work_unit_id"] == "submission_authority_sync_closure"
        assert authorization["work_unit_fingerprint"] == work_unit_fingerprint
        assert authorization["next_work_unit"]["unit_id"] == "submission_authority_sync_closure"
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "resume",
            "quest_status": "running",
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    runtime_authorization = result["refreshes"][0]["runtime_authorization"]
    assert result["materialized_count"] == 1
    assert runtime_authorization["authorization_status"] == "written"
    assert runtime_authorization["runtime_resume_status"] == "requested"
    assert runtime_authorization["current_controller_authorization"]["decision_id"] == (
        "fresh-domain-transition-bundle-stage-decision"
    )
    assert len(resume_calls) == 1


def test_refresh_domain_transition_forces_fresh_turn_when_live_prompt_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    stale_run_id = "mas-run-002-stale"
    fresh_run_id = "mas-run-002-fresh"
    work_unit_fingerprint = "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "status": "clear",
            "allow_write": True,
            "recommended_actions": [],
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": stale_run_id,
            "worker_running": True,
            "worker_pending": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "last_controller_decision_authorization": {
                "decision_id": "stale-rebuttal-coverage-decision",
                "route_target": "analysis-campaign",
                "work_unit_id": "paper/rebuttal/review_matrix.md and action_plan.md",
                "work_unit_fingerprint": "publication-blockers::old",
            },
        },
    )
    stale_prompt = quest_root / ".ds" / "runs" / stale_run_id / "prompt.md"
    stale_prompt.parent.mkdir(parents=True, exist_ok=True)
    stale_prompt.write_text(
        "Active MAS controller work unit: paper/rebuttal/review_matrix.md and action_plan.md\n",
        encoding="utf-8",
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "decision": "noop",
        "quest_status": "running",
        "active_run_id": stale_run_id,
        "worker_running": True,
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
        "route_target": "finalize",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "Synchronize submission authority and package closure for the bundle-stage.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
            "summary": "Synchronize submission authority and package closure for the bundle-stage.",
        },
        "blocking_work_units": [{"unit_id": "submission_authority_sync_closure", "lane": "controller"}],
    }
    calls: list[str] = []

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-domain-transition-bundle-stage-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "finalize",
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

    def fake_pause_study_runtime(**_: object) -> dict[str, object]:
        calls.append("pause")
        runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
        assert runtime_state["active_run_id"] == stale_run_id
        assert runtime_state["worker_running"] is True
        runtime_state["status"] = "paused"
        runtime_state["active_run_id"] = None
        runtime_state["worker_running"] = False
        module._write_json(quest_root / ".ds" / "runtime_state.json", runtime_state)
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "pause",
            "quest_status": "paused",
            "active_run_id": None,
        }

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        calls.append("resume")
        runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
        assert runtime_state["active_run_id"] is None
        assert runtime_state["worker_running"] is False
        assert runtime_state["last_controller_decision_authorization"]["work_unit_fingerprint"] == work_unit_fingerprint
        fresh_prompt = quest_root / ".ds" / "runs" / fresh_run_id / "prompt.md"
        fresh_prompt.parent.mkdir(parents=True, exist_ok=True)
        fresh_prompt.write_text(
            f"Active MAS controller work unit: {work_unit_fingerprint}\n"
            '"work_unit_id": "submission_authority_sync_closure"\n',
            encoding="utf-8",
        )
        runtime_state["status"] = "running"
        runtime_state["active_run_id"] = fresh_run_id
        runtime_state["worker_running"] = True
        module._write_json(quest_root / ".ds" / "runtime_state.json", runtime_state)
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "resume",
            "quest_status": "running",
            "active_run_id": fresh_run_id,
            "worker_running": True,
            "started": True,
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )
    monkeypatch.setattr(module.study_runtime_router, "pause_study_runtime", fake_pause_study_runtime)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    runtime_authorization = result["refreshes"][0]["runtime_authorization"]
    prompt_refresh = runtime_authorization["active_prompt_refresh"]
    runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
    assert calls == ["pause", "resume"]
    assert runtime_authorization["runtime_resume_status"] == "requested"
    assert prompt_refresh["status"] == "fresh_turn_forced"
    assert prompt_refresh["stale_active_run_id"] == stale_run_id
    assert prompt_refresh["expected_work_unit_fingerprint"] == work_unit_fingerprint
    assert runtime_state["active_run_id"] == fresh_run_id


def test_refresh_domain_transition_does_not_restart_when_live_prompt_matches_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    live_run_id = "mas-run-002-live"
    work_unit_fingerprint = "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "status": "clear",
            "allow_write": True,
            "recommended_actions": [],
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
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
        },
    )
    live_prompt = quest_root / ".ds" / "runs" / live_run_id / "prompt.md"
    live_prompt.parent.mkdir(parents=True, exist_ok=True)
    live_prompt.write_text(
        f"Active MAS controller work unit: {work_unit_fingerprint}\n"
        '"work_unit_id": "submission_authority_sync_closure"\n',
        encoding="utf-8",
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "decision": "noop",
        "quest_status": "running",
        "active_run_id": live_run_id,
        "worker_running": True,
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
        "route_target": "finalize",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "Synchronize submission authority and package closure for the bundle-stage.",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
            "summary": "Synchronize submission authority and package closure for the bundle-stage.",
        },
        "blocking_work_units": [{"unit_id": "submission_authority_sync_closure", "lane": "controller"}],
    }
    calls: list[str] = []

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {
                "schema_version": 1,
                "decision_id": "fresh-domain-transition-bundle-stage-decision",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": tick_request["controller_actions"],
                "route_target": "finalize",
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

    def fail_pause_study_runtime(**_: object) -> dict[str, object]:
        raise AssertionError("aligned live prompt must not be paused")

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        calls.append("resume")
        runtime_state = module._read_json_object(quest_root / ".ds" / "runtime_state.json") or {}
        assert runtime_state["active_run_id"] == live_run_id
        assert runtime_state["worker_running"] is True
        assert runtime_state["last_controller_decision_authorization"]["work_unit_fingerprint"] == work_unit_fingerprint
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "resume",
            "quest_status": "running",
            "active_run_id": live_run_id,
            "worker_running": True,
            "queued": True,
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )
    monkeypatch.setattr(module.study_runtime_router, "pause_study_runtime", fail_pause_study_runtime)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    runtime_authorization = result["refreshes"][0]["runtime_authorization"]
    assert calls == ["resume"]
    assert runtime_authorization["runtime_resume_status"] == "requested"
    assert "active_prompt_refresh" not in runtime_authorization
