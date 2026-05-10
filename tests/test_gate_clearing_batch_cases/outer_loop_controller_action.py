from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_study_outer_loop_executes_gate_clearing_batch_controller_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    runtime_protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"

    _write_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-21T12:42:39+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_resolve_runtime_escalation_record",
        lambda **_: (
            runtime_protocol.RuntimeEscalationRecordRef(
                record_id="runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-21T12:42:39+00:00",
                artifact_path=str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            ),
            None,
        ),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("batch_kwargs", kwargs),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref={
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        publication_eval_ref={
            "eval_id": publication_eval_payload["eval_id"],
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        decision_type="bounded_analysis",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Gate-clearing batch should run before resuming the same study line.",
        source="test-source",
        recorded_at="2026-04-21T12:45:00+00:00",
    )

    assert seen["batch_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["executed_controller_action"]["action_type"] == "run_gate_clearing_batch"
    assert result["executed_controller_action"]["result"] == {"ok": True, "status": "executed"}
