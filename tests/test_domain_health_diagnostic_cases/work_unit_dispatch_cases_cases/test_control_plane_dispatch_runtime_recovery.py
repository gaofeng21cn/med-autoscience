from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared
from tests.test_domain_health_diagnostic_cases.work_unit_dispatch_cases_cases.control_plane_dispatch_shared import (
    _authority_snapshot,
)

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_recovery_authorization_false_suppresses_runtime_recovery_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(profile.runtime_root / "quest-001"),
        "quest_status": "running",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=["runtime_recovery_retry_budget_exhausted"],
            ),
            "canonical_runtime_action": "escalate_runtime",
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        },
    }
    monkeypatch.setattr(module.domain_health_diagnostic_recovery_policy, "hold_for_flapping_circuit_breaker", lambda **_: None)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_actions"][0]["decision"] == "blocked"
    assert result["managed_study_actions"][0]["reason"] == "resume_request_failed"
    assert result["managed_study_actions"][0]["authority_snapshot"]["route_authorization"][
        "runtime_recovery_allowed"
    ] is False


def test_watch_runtime_blocks_retry_budget_exhausted_even_if_snapshot_was_marked_open(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    recovery_work_unit = {
        "unit_id": "runtime_recovery",
        "lane": "runtime",
        "summary": "Recover missing live worker.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(study_root, quest_root, action_type="bounded_analysis"),
        "decision_type": "bounded_analysis",
        "route_target": "runtime",
        "route_key_question": "Recover the missing live worker before paper work continues.",
        "route_rationale": "Runtime retry budget was exhausted, but MAS controller owns a bounded recovery action.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Recover the missing live worker.",
        "work_unit_fingerprint": "runtime-recovery::retry-budget-exhausted",
        "next_work_unit": recovery_work_unit,
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "authority_snapshot": {
            "schema_version": 1,
            "surface": "authority_snapshot",
            "control_state": "ready",
            "canonical_next_action": "resume_same_study_line",
            "canonical_runtime_action": "recover_runtime",
            "dispatch_gate": {
                "state": "open",
                "dispatch_allowed": True,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "route_authorization": {
                "authorized": True,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
    }
    dispatch_calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        dispatch_calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {"action_type": "request_opl_stage_attempt", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert dispatch_calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["outcome"] == "control_plane_dispatch_blocked"
    assert "runtime_recovery_retry_budget_exhausted" in wakeup_latest["control_plane_blocking_reasons"]
