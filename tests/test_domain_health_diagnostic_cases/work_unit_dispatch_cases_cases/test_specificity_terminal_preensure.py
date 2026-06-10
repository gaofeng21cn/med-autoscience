from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_does_not_preensure_paused_specificity_terminal_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "paused",
    }
    next_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit=next_work_unit,
    )
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": "controller",
        "route_key_question": (
            "gate_needs_specificity: Which exact claim, figure, table, metric, source path, or package artifact "
            "is blocking the publication gate?"
        ),
        "route_rationale": "Publication gate needs concrete blocker targets before dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Publication gate needs concrete blocker targets before dispatch.",
        "work_unit_fingerprint": "publication-blockers::vague",
        "next_work_unit": next_work_unit,
    }
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "paused",
            "active_run_id": None,
            "worker_running": False,
        },
    )
    outer_loop_calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        outer_loop_calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

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
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    authorization = wakeup_latest["controller_authorization_ref"]

    assert outer_loop_calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "needs_specificity"
    assert runtime_state["status"] == "paused"
    assert runtime_state["active_run_id"] is None
    assert runtime_state["worker_running"] is False
    assert "last_controller_decision_authorization" not in runtime_state
    assert authorization["work_unit_id"] == "gate_needs_specificity"
    assert authorization["mas_writes_runtime_state"] is False
    assert authorization["controller_work_unit_lifecycle"][
        "lifecycle_state"
    ] == "needs_specificity"


def test_watch_runtime_projects_specificity_terminal_as_blocked_action(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_paused",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "paused",
    }
    next_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit=next_work_unit,
    )
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": "controller",
        "route_key_question": "gate_needs_specificity: Which exact claim is blocking the publication gate?",
        "route_rationale": "Publication gate needs concrete blocker targets before dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Publication gate needs concrete blocker targets before dispatch.",
        "work_unit_fingerprint": "publication-blockers::vague",
        "next_work_unit": next_work_unit,
    }
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "paused",
            "active_run_id": None,
            "worker_running": False,
        },
    )

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "needs_specificity",
            "controller_work_unit_lifecycle": {
                "lifecycle_state": "needs_specificity",
                "latest_event_type": "needs_specificity",
                "delivery_blocked": True,
                "block_reason": "needs_specificity",
                "terminal_consumed": True,
            },
            "work_unit_id": "gate_needs_specificity",
            "work_unit_fingerprint": "publication-blockers::vague",
        }
    ]


def test_watch_runtime_applies_specificity_action_override_by_study_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    first_study_root = helpers.write_study(profile.workspace_root, "001-risk")
    second_study_root = helpers.write_study(profile.workspace_root, "002-risk")
    first_quest_root = profile.runtime_root / "quest-001"
    second_quest_root = profile.runtime_root / "quest-002"
    _write_charter(first_study_root)
    _write_charter(second_study_root)
    next_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    first_publication_eval_ref = _write_publication_eval(
        first_study_root,
        first_quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit=next_work_unit,
    )
    first_status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_paused",
        ),
        "study_root": str(first_study_root),
        "quest_id": "quest-001",
        "quest_root": str(first_quest_root),
        "quest_status": "paused",
    }
    second_status_payload = {
        **make_progress_projection_payload(
            study_id="002-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(second_study_root),
        "quest_id": "quest-002",
        "quest_root": str(second_quest_root),
        "quest_status": "stopped",
    }
    tick_request = {
        "study_root": first_study_root,
        "charter_ref": _write_charter(first_study_root),
        "publication_eval_ref": first_publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": "controller",
        "route_key_question": "gate_needs_specificity: Which exact claim is blocking the publication gate?",
        "route_rationale": "Publication gate needs concrete blocker targets before dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str((first_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Publication gate needs concrete blocker targets before dispatch.",
        "work_unit_fingerprint": "publication-blockers::vague",
        "next_work_unit": next_work_unit,
    }
    dump_json(
        first_quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "paused",
            "active_run_id": None,
            "worker_running": False,
        },
    )

    def fake_status(*, profile, study_root, **kwargs):
        if Path(study_root).name == "001-risk":
            return first_status_payload
        return second_status_payload

    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda *, study_root, status_payload: tick_request if Path(study_root).name == "001-risk" else None,
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", fake_status)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_actions"][0]["study_id"] == "001-risk"
    assert result["managed_study_actions"][0]["decision"] == "blocked"
    assert result["managed_study_actions"][0]["reason"] == "needs_specificity"
    assert result["managed_study_actions"][0]["work_unit_id"] == "gate_needs_specificity"
    assert result["managed_study_actions"][1]["study_id"] == "002-risk"
    assert result["managed_study_actions"][1]["decision"] == "blocked"
    assert result["managed_study_actions"][1]["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["managed_study_actions"][1]["resume_postcondition"]["typed_blocker"]["owner"] == "one-person-lab"
