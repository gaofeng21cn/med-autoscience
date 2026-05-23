from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_study_outer_loop_tick_dispatches_stop_runtime_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="stop_loss",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Stop the current runtime under the formal stop contract.",
        source="test-source",
        recorded_at="2026-04-05T06:12:00+00:00",
    )

    assert result["dispatch_status"] == "blocked"
    assert result["executed_controller_action"]["action_type"] == "stop_runtime"
    action_result = result["executed_controller_action"]["result"]
    assert action_result["status"] == "opl_runtime_human_gate_required"
    assert action_result["runtime_owner"] == "one-person-lab"
    assert action_result["mas_executes_runtime_attempt"] is False


def test_study_outer_loop_tick_materializes_runtime_escalation_ref_before_stop_runtime(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        {
            "recorded_at": "2026-04-05T06:10:00+00:00",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "noop",
            "reason": "quest_already_running",
            "execution": {
                "quest_id": "quest-001",
                "runtime_backend": "med_deepscientist",
                "entry_mode": "full_research",
                "auto_entry": "on_managed_research_intent",
            },
        },
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Human-review milestone reached; stop the live runtime and wait for explicit resume.",
        source="domain_health_diagnostic_outer_loop_wakeup",
        recorded_at="2026-04-05T06:12:00+00:00",
    )

    assert result["dispatch_status"] == "blocked"
    assert result["executed_controller_action"]["action_type"] == "stop_runtime"
    assert result["executed_controller_action"]["result"]["status"] == "opl_runtime_human_gate_required"
    runtime_escalation_ref = result["runtime_escalation_ref"]
    assert runtime_escalation_ref["record_id"] == (
        "runtime-escalation::001-risk::quest-001::quest_already_running::2026-04-05T06:12:00+00:00"
    )
    assert Path(runtime_escalation_ref["artifact_path"]).exists()
