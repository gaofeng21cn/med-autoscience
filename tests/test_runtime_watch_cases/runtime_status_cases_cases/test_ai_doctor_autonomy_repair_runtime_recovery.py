from __future__ import annotations

from .ai_doctor_autonomy_repair_helpers import *  # noqa: F403,F401

def test_watch_runtime_applies_ai_doctor_ready_recovery_action_for_no_live_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
    )
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(study_id="001-risk", quest_id="quest-001"),
    )

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_autonomy_repair_actions"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "applied",
            "action_type": "controller_repair",
            "repair_kind": "bounded_work_unit_redrive",
            "owner": "mas_controller",
            "auto_apply_allowed": True,
            "quality_gate_relaxation_allowed": False,
            "dispatch_status": "executed",
            "source": "runtime_watch_ai_doctor_repair",
        }
    ]
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "applied"
    assert repair_latest["applied_action"]["repair_kind"] == "bounded_work_unit_redrive"

def test_watch_runtime_does_not_auto_apply_ai_doctor_platform_repair_action(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(
            study_id="001-risk",
            quest_id="quest-001",
            action_type="platform_repair",
            repair_kind="repo_worktree_repair_proposal",
            owner="mas_mds_platform_repair",
            risk="high",
            auto_apply_allowed=False,
        ),
    )
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
    )

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_autonomy_repair_actions"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "blocked",
            "action_type": "platform_repair",
            "repair_kind": "repo_worktree_repair_proposal",
            "owner": "mas_mds_platform_repair",
            "auto_apply_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "dispatch_status": "not_dispatched",
            "source": "runtime_watch_ai_doctor_repair",
            "reason": "ai_doctor_platform_repair_requires_repo_level_fix",
        }
    ]
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "ready_for_repair"

def test_watch_runtime_blocks_ai_doctor_unknown_repair_kind_without_touching_package(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    package_root = study_root / "manuscript" / "current_package"
    submission_root = study_root / "paper" / "submission_minimal"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(
            study_id="001-risk",
            quest_id="quest-001",
            repair_kind="publication_gate_replay_or_authority_sync",
        ),
    )
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
    )
    ensure_calls: list[str] = []

    def fake_ensure(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or ""))
        return status_payload

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert ensure_calls == ["runtime_watch"]
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == (
        "ai_doctor_repair_action_not_in_runtime_recovery_allowlist"
    )
    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert not package_root.exists()
    assert not submission_root.exists()
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "ready_for_repair"

def test_watch_runtime_blocks_ai_doctor_repair_without_controller_authorization(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(study_id="001-risk", quest_id="quest-001"),
    )
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
        repair_authorized=False,
    )
    ensure_calls: list[str] = []

    def fake_ensure(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or ""))
        return status_payload

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert ensure_calls == ["runtime_watch"]
    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "controller_repair_authorization_missing"
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "ready_for_repair"
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "blocked"
    assert lifecycle_latest["blocked_reason"] == "controller_repair_authorization_missing"
    assert lifecycle_latest["last_apply_attempt"]["dispatch_status"] == "not_dispatched"
    assert lifecycle_latest["next_owner"] == "mas_controller"
    assert lifecycle_latest["external_supervisor_required"] is False

def test_watch_runtime_marks_retry_exhausted_ai_doctor_repair_as_external_supervisor_required(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(study_id="001-risk", quest_id="quest-001"),
    )
    status_payload = {
        **_runtime_recovery_status(
            study_root=study_root,
            quest_root=quest_root,
            study_id="001-risk",
            quest_id="quest-001",
            repair_authorized=True,
        ),
        "control_plane_snapshot": {
            "control_state": "blocked_runtime_escalation",
            "canonical_runtime_action": "external_supervisor_required",
            "dispatch_gate": {
                "state": "blocked",
                "dispatch_allowed": False,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "route_authorization": {"runtime_recovery_allowed": False},
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
    }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "runtime_recovery_not_authorized"
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "external_supervisor_required"
    assert lifecycle_latest["blocked_reason"] == "runtime_recovery_not_authorized"
    assert lifecycle_latest["external_supervisor_required"] is True
    assert lifecycle_latest["next_owner"] == "external_supervisor"

def test_watch_runtime_consumes_ai_doctor_repair_materialized_in_same_tick(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    status_payload = _runtime_recovery_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
    )

    def materialize_slo(*, profile, study_root):
        dump_json(
            study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
            _ready_repair_payload(study_id="001-risk", quest_id="quest-001"),
        )
        return {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "breach",
            "repair_recommendation": {"state": "ready_for_repair"},
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module, "_materialize_managed_study_autonomy_slo", materialize_slo)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "applied"
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "applied"
