from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_study_outer_loop_tick_writes_decision_record_and_executes_next_controller_action(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: (
            seen.setdefault("ensure_kwargs", kwargs),
            {
                "decision": "resume",
                "reason": "quest_paused",
            },
        )[1],
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
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Publication eval keeps the study on the same line.",
        source="test-source",
        recorded_at="2026-04-05T06:00:00+00:00",
    )

    assert seen["ensure_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "force": False,
        "source": "test-source",
    }
    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["runtime_status"] == {
        "decision": "blocked",
        "reason": "startup_boundary_not_ready_for_resume",
    }
    assert result["runtime_escalation_ref"] == runtime_escalation_ref
    assert result["controller_confirmation_summary_ref"] is None
    assert result["executed_controller_action"]["action_type"] == "ensure_study_runtime"
    assert result["executed_controller_action"]["result"] == {
        "decision": "resume",
        "reason": "quest_paused",
    }

    artifact_path = Path(result["study_decision_ref"]["artifact_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    latest_payload = json.loads((artifact_path.parent / "latest.json").read_text(encoding="utf-8"))
    assert payload["charter_ref"] == charter_ref
    assert payload["publication_eval_ref"] == publication_eval_ref
    assert payload["runtime_escalation_ref"] == runtime_escalation_ref
    assert payload["decision_type"] == "continue_same_line"
    assert payload["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        }
    ]
    assert payload["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert payload["family_event_envelope"]["target_domain_id"] == "medautoscience"
    assert payload["family_event_envelope"]["session"]["study_id"] == "001-risk"
    assert payload["family_event_envelope"]["session"]["quest_id"] == "quest-001"
    assert payload["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert payload["family_checkpoint_lineage"]["producer"]["event_envelope_id"] == payload["family_event_envelope"]["envelope_id"]
    assert payload["family_human_gates"] == []
    assert latest_payload == payload
    assert not (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").exists()
def test_study_outer_loop_tick_fails_closed_when_managed_runtime_status_lacks_runtime_escalation_ref(
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
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, profile.med_deepscientist_runtime_root / "quests" / "quest-001")

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "reason": "quest_paused",
        },
    )

    with pytest.raises(ValueError, match="runtime_escalation_ref"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )
def test_study_outer_loop_tick_reads_runtime_escalation_ref_from_runtime_event_contract(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "runtime_event_ref": runtime_event_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "reason": "quest_paused",
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
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Publication eval keeps the study on the same line.",
    )

    assert result["runtime_escalation_ref"] == runtime_escalation_ref
    assert result["runtime_status"]["runtime_event_id"] == runtime_event_ref["event_id"]
def test_study_outer_loop_tick_falls_back_to_status_surface_when_runtime_event_ref_is_missing(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "decision": "resume",
            "reason": "publication_quality_gap",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "reason": "quest_paused",
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
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Publication eval keeps the study on the same line.",
    )

    assert result["runtime_escalation_ref"] == runtime_escalation_ref
    assert result["runtime_status"] == {
        "decision": "resume",
        "reason": "publication_quality_gap",
    }
def test_study_outer_loop_tick_fails_closed_when_runtime_event_quest_identity_mismatches_status(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        quest_id="quest-other",
        runtime_escalation_ref=runtime_escalation_ref,
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "runtime_event_ref": runtime_event_ref,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="quest_id mismatch"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )
def test_study_outer_loop_tick_fails_closed_when_runtime_event_supervisor_tick_is_not_fresh(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        supervisor_tick_status="stale",
        runtime_escalation_ref=runtime_escalation_ref,
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "runtime_event_ref": runtime_event_ref,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="supervisor_tick_status"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )
def test_study_outer_loop_tick_rejects_publication_eval_ref_outside_eval_owned_latest_surface(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref={
                "eval_id": "publication-eval::external-surface",
                "artifact_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval must stay on the eval-owned latest artifact surface.",
        )
def test_study_outer_loop_tick_accepts_freshened_publication_eval_id_on_stable_latest_artifact(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    current_publication_eval_ref = _write_publication_eval(study_root, quest_root)
    stale_publication_eval_ref = dict(current_publication_eval_ref)
    stale_publication_eval_ref["eval_id"] = "publication-eval::001-risk::quest-001::stale"
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: (
            seen.setdefault("ensure_kwargs", kwargs),
            {
                "decision": "resume",
                "reason": "quest_paused",
            },
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=stale_publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Use the latest publication eval on the stable eval-owned surface.",
        source="test-source",
        recorded_at="2026-04-05T06:07:00+00:00",
    )

    payload = json.loads(Path(result["study_decision_ref"]["artifact_path"]).read_text(encoding="utf-8"))
    assert payload["publication_eval_ref"] == current_publication_eval_ref
    assert seen["ensure_kwargs"]["study_id"] == "001-risk"
def test_study_outer_loop_tick_fails_closed_when_runtime_escalation_artifact_mismatches_status_ref(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_escalation_ref["record_id"] = "runtime-escalation::mismatch"
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="record_id mismatch"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )
def test_study_outer_loop_tick_reexports_from_router(monkeypatch) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    sentinel = {"status": "delegated"}

    monkeypatch.setattr(outer_loop, "study_outer_loop_tick", lambda **kwargs: {**sentinel, **kwargs})

    result = router.study_outer_loop_tick(test_key="value")

    assert result == {"status": "delegated", "test_key": "value"}
def test_study_outer_loop_tick_blocks_dispatch_when_human_confirmation_is_required(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router.managed_runtime_transport,
        "stop_quest",
        lambda **kwargs: pytest.fail("stop_quest should not run before human confirmation"),
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="stop_loss",
        requires_human_confirmation=True,
        controller_actions=[
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Controller requires human confirmation before stopping the quest.",
        source="test-source",
        recorded_at="2026-04-05T06:05:00+00:00",
    )

    assert result["dispatch_status"] == "pending_human_confirmation"
    assert result["executed_controller_action"] is None
    assert result["controller_confirmation_summary_ref"] == {
        "summary_id": "controller-confirmation::001-risk::study-decision::001-risk::quest-001::stop_loss::2026-04-05T06:05:00+00:00",
        "artifact_path": str(
            (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").resolve()
        ),
    }
    assert result["human_confirmation_request"] == {
        "category": "controller_decision_confirmation",
        "summary": "Controller requires human confirmation before stopping the quest.",
        "runtime_blockers": [
            {
                "decision": "blocked",
                "reason": "startup_boundary_not_ready_for_resume",
                "record_id": runtime_escalation_ref["record_id"],
                "summary_ref": runtime_escalation_ref["summary_ref"],
            }
        ],
        "publication_blockers": [
            {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Primary claim is ready to continue on the same line.",
                "gap_summaries": ["External validation can still improve robustness."],
            }
        ],
        "current_required_action": "human_confirmation_required",
        "controller_actions": [
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "question_for_user": "Approve controller action `stop_runtime` for study `001-risk`?",
    }
    artifact_path = Path(result["study_decision_ref"]["artifact_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["requires_human_confirmation"] is True
    assert payload["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        }
    ]
    assert payload["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert payload["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert payload["family_human_gates"][0]["version"] == "family-human-gate.v1"
    assert payload["family_human_gates"][0]["status"] == "requested"
    assert payload["family_human_gates"][0]["gate_kind"] == "controller_human_confirmation"
    assert payload["family_human_gates"][0]["decision_options"] == ["approve", "request_changes", "reject"]
    confirmation_payload = json.loads(
        (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").read_text(encoding="utf-8")
    )
    assert confirmation_payload["status"] == "pending"
    assert confirmation_payload["question_for_user"] == "请确认是否允许 MAS 停止当前研究运行。"
    assert confirmation_payload["next_action_if_approved"] == "停止当前研究运行"
def test_study_outer_loop_tick_rejects_human_gate_for_autonomous_scientific_decision(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publishability_gate_blocked",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: pytest.fail("ordinary scientific decisions must stay autonomous"),
    )

    with pytest.raises(ValueError, match="major direction pivots"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=True,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="MAS should autonomously decide whether to continue the current evidence repair line.",
            source="test-source",
            recorded_at="2026-04-05T06:06:00+00:00",
        )

    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").exists()
