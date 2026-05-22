from __future__ import annotations

from .ai_doctor_autonomy_repair_helpers import *  # noqa: F403,F401

def test_watch_runtime_keeps_submission_milestone_parked_instead_of_external_supervisor_lifecycle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    _write_bundle_only_publication_surfaces(
        study_root=study_root,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
    )
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
        "quest_status": "stopped",
        "active_run_id": None,
        "reason": "quest_stopped_requires_explicit_rerun",
        "continuation_state": {
            "quest_status": "stopped",
            "active_run_id": None,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
        },
        "control_plane_snapshot": {
            "control_state": "ready",
            "dispatch_gate": {"state": "open", "dispatch_allowed": True, "blocking_reasons": []},
            "route_authorization": {"runtime_recovery_allowed": False},
            "blocking_reasons": [],
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "awaiting_explicit_resume",
            "retry_budget_remaining": 0,
            "blocking_reasons": [],
        },
    }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "parked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "submission_milestone_parked"
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "parked"
    assert lifecycle_latest["blocked_reason"] is None
    assert lifecycle_latest["external_supervisor_required"] is False
    assert lifecycle_latest["next_owner"] is None
    assert lifecycle_latest["paper_package_mutation_allowed"] is False
    assert lifecycle_latest["manual_study_patch_allowed"] is False
    assert lifecycle_latest["medical_claim_authoring_allowed"] is False

def test_watch_runtime_reconciles_stale_repair_lifecycle_when_ai_doctor_returns_monitor_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "obesity-study", quest_id="quest-obesity")
    quest_root = profile.runtime_root / "quest-obesity"
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json",
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": "obesity-study",
            "quest_id": "quest-obesity",
            "state": "external_supervisor_required",
            "top_action": {
                "action_type": "controller_repair",
                "repair_kind": "analysis_claim_evidence_redrive",
                "owner": "mas_controller",
                "auto_apply_allowed": True,
            },
            "auto_apply_allowed": True,
            "last_apply_attempt_at": "2026-05-13T03:18:23+00:00",
            "applied_at": None,
            "blocked_reason": "runtime_recovery_not_authorized",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "quality_gate_relaxation_allowed": False,
        },
    )
    status_payload = _live_controller_work_unit_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="obesity-study",
        quest_id="quest-obesity",
        repair_kind="analysis_claim_evidence_redrive",
    )

    def materialize_slo(*, profile, study_root):
        dump_json(
            study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
            {
                "surface": "autonomy_repair_orchestration",
                "schema_version": 1,
                "state": "monitor_only",
                "study_id": "obesity-study",
                "quest_id": "quest-obesity",
                "action_count": 0,
                "actions": [],
                "quality_gate_relaxation_allowed": False,
            },
        )
        return {
            "study_id": "obesity-study",
            "quest_id": "quest-obesity",
            "state": "ok",
            "ai_doctor_request_required": False,
            "ai_doctor_state": "not_required",
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module, "_materialize_managed_study_autonomy_slo", materialize_slo)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_autonomy_repair_actions"] == []
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "monitor_only"
    assert lifecycle_latest["blocked_reason"] is None
    assert lifecycle_latest["next_owner"] is None
    assert lifecycle_latest["external_supervisor_required"] is False

def test_watch_runtime_closes_ai_doctor_repair_after_preensure_recovery_even_with_other_study_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    first_study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    second_study_root = helpers.write_study(profile.workspace_root, "002-risk", quest_id="quest-002")
    first_quest_root = profile.runtime_root / "quest-001"
    second_quest_root = profile.runtime_root / "quest-002"
    dump_json(
        second_study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_repair_payload(study_id="002-risk", quest_id="quest-002"),
    )
    first_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(first_study_root),
        "quest_id": "quest-001",
        "quest_root": str(first_quest_root),
        "quest_status": "running",
        "control_plane_snapshot": {
            "dispatch_gate": {"state": "open", "dispatch_allowed": True, "blocking_reasons": []},
            "route_authorization": {"authorized": True, "runtime_recovery_allowed": True},
            "blocking_reasons": [],
        },
    }
    second_recovery = _runtime_recovery_status(
        study_root=second_study_root,
        quest_root=second_quest_root,
        study_id="002-risk",
        quest_id="quest-002",
    )
    second_live = {
        **make_progress_projection_payload(
            study_id="002-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(second_study_root),
        "quest_id": "quest-002",
        "quest_root": str(second_quest_root),
        "quest_status": "running",
        "runtime_liveness_status": "live",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-002",
            "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-002"},
        },
        "control_plane_snapshot": {
            "dispatch_gate": {"state": "open", "dispatch_allowed": True, "blocking_reasons": []},
            "route_authorization": {"runtime_recovery_allowed": True},
            "blocking_reasons": [],
        },
        "controller_repair_authorization_ref": {
            "surface": "controller_repair_authorization",
            "authorized": True,
            "action": "runtime_recovery",
            "work_unit_id": "runtime_recovery",
            "controller_action_type": "ensure_study_runtime",
            "control_surface": "domain_health_diagnostic",
        },
    }
    tick_request = {
        "study_root": first_study_root,
        "charter_ref": _write_charter(first_study_root),
        "publication_eval_ref": _write_publication_eval(
            first_study_root,
            first_quest_root,
            action_type="bounded_analysis",
        ),
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "Run bounded repair for the first study.",
        "route_rationale": "First study needs an outer-loop dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str((first_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Dispatch first study.",
        "work_unit_fingerprint": "first-study::dispatch",
        "next_work_unit": {"unit_id": "runtime_recovery", "lane": "runtime", "summary": "Recover first study."},
    }

    def fake_ensure(*, study_root, **kwargs):
        return first_status if Path(study_root).name == "001-risk" else second_recovery

    def fake_status(*, study_root, **kwargs):
        return first_status if Path(study_root).name == "001-risk" else second_live

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", fake_status)
    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda *, study_root, status_payload: tick_request if Path(study_root).name == "001-risk" else None,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_outer_loop_tick",
        lambda **kwargs: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "dispatch_status": "executed",
        },
    )
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_autonomy_repair_actions"] == [
        {
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "state": "applied",
            "action_type": "controller_repair",
            "repair_kind": "bounded_work_unit_redrive",
            "owner": "mas_controller",
            "auto_apply_allowed": True,
            "quality_gate_relaxation_allowed": False,
            "dispatch_status": "executed",
            "source": "domain_health_diagnostic_ai_doctor_repair",
        }
    ]
