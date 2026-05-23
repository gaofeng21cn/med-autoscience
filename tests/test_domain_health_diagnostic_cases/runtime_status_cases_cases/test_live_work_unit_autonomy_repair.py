from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _ready_live_work_unit_repair_payload(*, study_id: str, quest_id: str) -> dict[str, object]:
    return {
        "surface": "autonomy_repair_orchestration",
        "schema_version": 1,
        "state": "ready_for_repair",
        "study_id": study_id,
        "quest_id": quest_id,
        "action_count": 1,
        "actions": [
            {
                "action_type": "controller_repair",
                "repair_kind": "analysis_claim_evidence_redrive",
                "owner": "mas_controller",
                "risk": "medium",
                "auto_apply_allowed": True,
            }
        ],
        "quality_gate_relaxation_allowed": False,
    }


def _live_controller_work_unit_status(
    *,
    study_root: Path,
    quest_root: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, object]:
    active_run_id = f"run-{study_id}"
    return {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "running",
        "active_run_id": active_run_id,
        "execution_owner_guard": {"supervisor_only": True, "active_run_id": active_run_id},
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": active_run_id,
            "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": active_run_id},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "continue_supervising_runtime",
            "attempt_state": "live",
            "retry_budget_remaining": 3,
            "blocking_reasons": [],
            "worker_liveness_state": {
                "state": "live",
                "worker_running": True,
                "active_run_id": active_run_id,
            },
        },
        "authority_snapshot": {
            "dispatch_gate": {
                "state": "open",
                "dispatch_allowed": True,
                "blocking_reasons": ["execution_owner_guard.supervisor_only"],
            },
            "blocking_reasons": ["execution_owner_guard.supervisor_only"],
        },
        "last_controller_decision_authorization": {
            "source": "domain_health_diagnostic",
            "delivery_mode": "managed_runtime_chat",
            "active_run_id": active_run_id,
            "route_target": "analysis-campaign",
            "work_unit_id": "analysis_claim_evidence_repair",
            "controller_actions": ["run_quality_repair_batch"],
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "MAS controller-owned live work unit.",
            },
        },
    }


def _write_ready_live_work_unit_repair(study_root: Path, *, study_id: str, quest_id: str) -> None:
    dump_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        _ready_live_work_unit_repair_payload(study_id=study_id, quest_id=quest_id),
    )


def _patch_domain_health_diagnostic_for_status(monkeypatch, module, status_payload: dict[str, object]) -> None:
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_cycle_profiler, "profile_study_cycle", lambda **_: {})
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])


def test_watch_runtime_applies_mas_controller_live_work_unit_repair_under_supervisor_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "obesity-study", quest_id="quest-obesity")
    quest_root = profile.runtime_root / "quest-obesity"
    publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="bounded_analysis",
        work_unit_fingerprint="publication-blockers::obesity",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
    )
    _write_ready_live_work_unit_repair(study_root, study_id="obesity-study", quest_id="quest-obesity")
    status_payload = _live_controller_work_unit_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="obesity-study",
        quest_id="quest-obesity",
    )
    status_payload["last_controller_decision_authorization"]["publication_eval_ref"] = publication_eval_ref
    status_payload["last_controller_decision_authorization"]["work_unit_fingerprint"] = "publication-blockers::obesity"
    _patch_domain_health_diagnostic_for_status(monkeypatch, module, status_payload)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_autonomy_repair_actions"] == [
        {
            "study_id": "obesity-study",
            "quest_id": "quest-obesity",
            "state": "blocked",
            "action_type": "controller_repair",
            "repair_kind": "analysis_claim_evidence_redrive",
            "owner": "mas_controller",
            "auto_apply_allowed": True,
            "quality_gate_relaxation_allowed": False,
            "dispatch_status": "not_dispatched",
            "source": "domain_health_diagnostic_ai_doctor_repair",
            "reason": "runtime_recovery_not_authorized",
        }
    ]
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "external_supervisor_required"
    assert lifecycle_latest["blocked_reason"] == "runtime_recovery_not_authorized"
    assert lifecycle_latest["next_owner"] == "external_supervisor"


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

    monkeypatch.setattr(module, "_materialize_managed_study_autonomy_slo", materialize_slo)
    _patch_domain_health_diagnostic_for_status(monkeypatch, module, status_payload)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_autonomy_repair_actions"] == []
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "monitor_only"
    assert lifecycle_latest["blocked_reason"] is None
    assert lifecycle_latest["next_owner"] is None
    assert lifecycle_latest["external_supervisor_required"] is False


def test_watch_runtime_blocks_live_work_unit_repair_when_controller_authorization_targets_other_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "obesity-study", quest_id="quest-obesity")
    quest_root = profile.runtime_root / "quest-obesity"
    _write_ready_live_work_unit_repair(study_root, study_id="obesity-study", quest_id="quest-obesity")
    status_payload = _live_controller_work_unit_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="obesity-study",
        quest_id="quest-obesity",
    )
    status_payload["last_controller_decision_authorization"]["active_run_id"] = "run-other-study"
    _patch_domain_health_diagnostic_for_status(monkeypatch, module, status_payload)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "runtime_recovery_not_authorized"
    repair_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json").read_text(encoding="utf-8")
    )
    assert repair_latest["state"] == "ready_for_repair"


def test_watch_runtime_blocks_live_work_unit_repair_when_controller_lifecycle_consumed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "obesity-study", quest_id="quest-obesity")
    quest_root = profile.runtime_root / "quest-obesity"
    _write_ready_live_work_unit_repair(study_root, study_id="obesity-study", quest_id="quest-obesity")
    status_payload = _live_controller_work_unit_status(
        study_root=study_root,
        quest_root=quest_root,
        study_id="obesity-study",
        quest_id="quest-obesity",
    )
    status_payload["last_controller_decision_authorization"]["controller_work_unit_lifecycle"] = {
        "lifecycle_state": "completed",
        "terminal_consumed": True,
    }
    _patch_domain_health_diagnostic_for_status(monkeypatch, module, status_payload)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "runtime_recovery_not_authorized"
    lifecycle_latest = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert lifecycle_latest["state"] == "external_supervisor_required"
    assert lifecycle_latest["next_owner"] == "external_supervisor"
