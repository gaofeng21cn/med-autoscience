from __future__ import annotations

import importlib
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_managed_runtime_worker_executes_current_controller_authorization_when_dispatch_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    run_id = "mas-run-003-current"
    stale_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    fresh_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=stale_route,
    )
    _write_current_dispatch(dispatch_path, profile, stale_dispatch)
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": run_id,
            "worker_running": True,
            "last_controller_decision_authorization": {
                "decision_id": "fresh-ai-reviewer-decision",
                "authorization_basis": "controller_domain_transition",
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_recheck",
                "work_unit_fingerprint": fresh_fingerprint,
                "next_work_unit": {
                    "unit_id": "ai_reviewer_recheck",
                    "lane": "review",
                    "summary": "Return current manuscript and evidence refs to the AI reviewer workflow.",
                },
            },
        },
    )
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER", "1")
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT", str(quest_root))
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID", study_id)
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID", run_id)
    monkeypatch.setenv("HOME", str(quest_root / ".ds" / "codex_homes" / run_id))
    monkeypatch.setenv("CODEX_HOME", str(quest_root / ".ds" / "codex_homes" / run_id / ".codex"))
    monkeypatch.setattr(
        module,
        "resolve_developer_supervisor_mode",
        lambda **_: _DeveloperMode("external_observe", safe_actions_enabled=False, blocked_reason="github_user_lookup_failed"),
    )
    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        managed_runtime_worker=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["dispatch_authority"] == "managed_runtime_controller_authorization"
    assert execution["developer_supervisor_mode"]["mode"] == "external_observe"
    assert execution["managed_runtime_authorization"]["status"] == "authorized"
    assert execution["managed_runtime_authorization"]["work_unit_fingerprint"] == fresh_fingerprint
    assert execution["owner_route"]["work_unit_fingerprint"] == fresh_fingerprint
    assert execution["owner_route"]["source_fingerprint"] == fresh_fingerprint
    assert execution["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert execution["owner_route_current"] is True
    assert execution["repeat_suppression_key"] == fresh_fingerprint


def test_managed_runtime_worker_synthesizes_dispatch_when_consumer_latest_is_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    run_id = "mas-run-003-current"
    fresh_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatches": [],
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": run_id,
            "worker_running": True,
            "current_controller_authorization": {
                "decision_id": "fresh-ai-reviewer-decision",
                "authorization_basis": "controller_domain_transition",
                "active_run_id": run_id,
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_recheck",
                "work_unit_fingerprint": fresh_fingerprint,
                "next_work_unit": {
                    "unit_id": "ai_reviewer_recheck",
                    "lane": "review",
                    "summary": "Return current manuscript and evidence refs to the AI reviewer workflow.",
                },
            },
        },
    )
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER", "1")
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT", str(quest_root))
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID", study_id)
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID", run_id)
    monkeypatch.setenv("HOME", str(quest_root / ".ds" / "codex_homes" / run_id))
    monkeypatch.setenv("CODEX_HOME", str(quest_root / ".ds" / "codex_homes" / run_id / ".codex"))
    monkeypatch.setattr(
        module,
        "resolve_developer_supervisor_mode",
        lambda **_: _DeveloperMode(
            "external_observe",
            safe_actions_enabled=False,
            blocked_reason="github_user_lookup_failed",
        ),
    )
    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        managed_runtime_worker=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["dispatch_authority"] == "managed_runtime_controller_authorization"
    assert execution["developer_supervisor_mode"]["mode"] == "external_observe"
    assert execution["managed_runtime_authorization"]["status"] == "authorized"
    assert execution["managed_runtime_authorization"]["work_unit_fingerprint"] == fresh_fingerprint
    assert execution["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert execution["repeat_suppression_key"] == fresh_fingerprint


def test_managed_runtime_worker_prefers_current_authorization_over_stale_last_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    run_id = "mas-run-003-current"
    stale_fingerprint = "publication-blockers::stale-analysis"
    fresh_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatches": [],
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": run_id,
            "worker_running": True,
            "last_controller_decision_authorization": {
                "decision_id": "stale-analysis-decision",
                "controller_actions": ["run_quality_repair_batch"],
                "route_target": "analysis-campaign",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
            },
            "current_controller_authorization": {
                "decision_id": "fresh-ai-reviewer-decision",
                "authorization_basis": "controller_domain_transition",
                "active_run_id": run_id,
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_recheck",
                "work_unit_fingerprint": fresh_fingerprint,
                "next_work_unit": {"unit_id": "ai_reviewer_recheck", "lane": "review"},
            },
        },
    )
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER", "1")
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT", str(quest_root))
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID", study_id)
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID", run_id)
    monkeypatch.setenv("HOME", str(quest_root / ".ds" / "codex_homes" / run_id))
    monkeypatch.setenv("CODEX_HOME", str(quest_root / ".ds" / "codex_homes" / run_id / ".codex"))
    monkeypatch.setattr(
        module,
        "resolve_developer_supervisor_mode",
        lambda **_: _DeveloperMode(
            "external_observe",
            safe_actions_enabled=False,
            blocked_reason="github_user_lookup_failed",
        ),
    )
    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        managed_runtime_worker=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["managed_runtime_authorization"]["status"] == "authorized"
    assert execution["managed_runtime_authorization"]["work_unit_fingerprint"] == fresh_fingerprint
    assert execution["repeat_suppression_key"] == fresh_fingerprint
    assert stale_fingerprint not in result["action_fingerprints"]


class _DeveloperMode:
    def __init__(self, mode: str, *, safe_actions_enabled: bool, blocked_reason: str | None = None) -> None:
        self.mode = mode
        self.safe_actions_enabled = safe_actions_enabled
        self.blocked_reason = blocked_reason

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "requested_mode": "developer_apply_safe",
            "safe_actions_enabled": self.safe_actions_enabled,
            "blocked_reason": self.blocked_reason,
            "github_user_gate": {"allowed": self.safe_actions_enabled, "reason": self.blocked_reason},
        }


def test_non_managed_executor_still_blocks_stale_dispatch_even_when_runtime_authorization_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    current_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    stale_route = {
        **current_route,
        "truth_epoch": "truth-event-000004",
        "route_epoch": "truth-event-000004",
        "source_fingerprint": "truth-snapshot::old-write-route",
        "work_unit_fingerprint": "truth-snapshot::old-write-route",
        "idempotency_key": "owner-route::old-write-route",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=stale_route,
    )
    _write_current_dispatch(dispatch_path, profile, stale_dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": current_route}],
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": "mas-run-003-current",
            "worker_running": True,
            "last_controller_decision_authorization": {
                "decision_id": "fresh-ai-reviewer-decision",
                "authorization_basis": "controller_domain_transition",
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_recheck",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
                "next_work_unit": {"unit_id": "ai_reviewer_recheck", "lane": "review"},
            },
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_route_stale"
    assert execution["dispatch_authority"] == "consumer_default_executor_dispatch"


def test_managed_runtime_worker_blocks_authorization_for_different_active_run(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    run_id = "mas-run-003-current"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
            owner_route=_owner_route(
                study_id=study_id,
                action_type="return_to_ai_reviewer_workflow",
                owner="ai_reviewer",
            ),
        ),
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": run_id,
            "worker_running": True,
            "last_controller_decision_authorization": {
                "decision_id": "fresh-ai-reviewer-decision",
                "authorization_basis": "controller_domain_transition",
                "active_run_id": "mas-run-003-stale",
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_recheck",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
                "next_work_unit": {"unit_id": "ai_reviewer_recheck", "lane": "review"},
            },
        },
    )
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER", "1")
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT", str(quest_root))
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID", study_id)
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID", run_id)
    monkeypatch.setenv("HOME", str(quest_root / ".ds" / "codex_homes" / run_id))
    monkeypatch.setenv("CODEX_HOME", str(quest_root / ".ds" / "codex_homes" / run_id / ".codex"))
    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        lambda **_: (_ for _ in ()).throw(AssertionError("stale-run authorization must not execute")),
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        managed_runtime_worker=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "managed_runtime_authorization_run_mismatch"
    assert execution["managed_runtime_authorization"]["authorization_run_id"] == "mas-run-003-stale"


def test_managed_runtime_worker_blocks_authorization_for_different_study(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    run_id = "mas-run-003-current"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
            owner_route=_owner_route(
                study_id=study_id,
                action_type="return_to_ai_reviewer_workflow",
                owner="ai_reviewer",
            ),
        ),
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": run_id,
            "worker_running": True,
            "last_controller_decision_authorization": {
                "decision_id": "fresh-ai-reviewer-decision",
                "authorization_basis": "controller_domain_transition",
                "study_id": "002-dm-china-us-mortality-attribution",
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_recheck",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
                "next_work_unit": {"unit_id": "ai_reviewer_recheck", "lane": "review"},
            },
        },
    )
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER", "1")
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT", str(quest_root))
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID", study_id)
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID", run_id)
    monkeypatch.setenv("HOME", str(quest_root / ".ds" / "codex_homes" / run_id))
    monkeypatch.setenv("CODEX_HOME", str(quest_root / ".ds" / "codex_homes" / run_id / ".codex"))
    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        lambda **_: (_ for _ in ()).throw(AssertionError("wrong-study authorization must not execute")),
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        managed_runtime_worker=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "managed_runtime_authorization_study_mismatch"
    assert execution["managed_runtime_authorization"]["authorization_study_id"] == "002-dm-china-us-mortality-attribution"
