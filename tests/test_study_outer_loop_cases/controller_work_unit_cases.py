from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_study_outer_loop_tick_persists_controller_work_unit_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    next_work_unit = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {"decision": "noop", "reason": "quest_already_running"},
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="bounded_analysis",
        route_target="analysis-campaign",
        route_key_question=(
            "analysis_claim_evidence_repair: Repair claim-evidence, story, figure, and results traceability blockers."
        ),
        source_route_key_question="Broad reviewer revision checklist.",
        route_rationale="Publication gate selected controller-owned work unit `analysis_claim_evidence_repair`.",
        work_unit_fingerprint="publication-blockers::claim-story-figure",
        next_work_unit=next_work_unit,
        blocking_work_units=[
            next_work_unit,
            {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
            },
        ],
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Run the controller-owned publication work unit.",
        source="test-source",
        recorded_at="2026-04-05T06:10:00+00:00",
    )

    payload = json.loads(Path(result["study_decision_ref"]["artifact_path"]).read_text(encoding="utf-8"))
    assert payload["source_route_key_question"] == "Broad reviewer revision checklist."
    assert payload["work_unit_fingerprint"] == "publication-blockers::claim-story-figure"
    assert payload["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert payload["blocking_work_units"][1]["unit_id"] == "submission_minimal_refresh"
