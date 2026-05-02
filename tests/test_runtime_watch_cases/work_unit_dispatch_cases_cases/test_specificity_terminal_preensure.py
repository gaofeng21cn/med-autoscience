from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_does_not_preensure_paused_specificity_terminal_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    status_payload = {
        **make_study_runtime_status_payload(
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
    ensure_calls: list[str] = []
    outer_loop_calls: list[str] = []

    def fail_if_preensure_runs(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or ""))
        pytest.fail("runtime watch must not resume a paused quest before gate specificity terminal projection")

    def fake_outer_loop_tick(**kwargs):
        outer_loop_calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.study_runtime_router, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_preensure_runs)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert ensure_calls == []
    assert outer_loop_calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "needs_specificity"
    assert runtime_state["status"] == "paused"
    assert runtime_state["active_run_id"] is None
    assert runtime_state["worker_running"] is False
    assert runtime_state["last_controller_decision_authorization"]["work_unit_id"] == "gate_needs_specificity"
    assert runtime_state["last_controller_decision_authorization"]["controller_work_unit_lifecycle"][
        "lifecycle_state"
    ] == "needs_specificity"
