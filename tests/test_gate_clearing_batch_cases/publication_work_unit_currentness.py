from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_gate_clearing_batch_treats_explicit_gate_specificity_as_platform_terminal(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_id = "quest-004"
    quest_root = profile.managed_runtime_home / "quests" / quest_id
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["action_type"] = "return_to_controller"
    publication_eval_payload["recommended_actions"][0].pop("route_target", None)
    publication_eval_payload["recommended_actions"][0].pop("route_key_question", None)
    publication_eval_payload["recommended_actions"][0].pop("route_rationale", None)
    publication_eval_payload["recommended_actions"][0]["work_unit_fingerprint"] = "publication-blockers::vague"
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "study_delivery_status": "current",
        "gate_fingerprint": "publication-gate::generic",
        "submission_minimal_evaluated_source_signature": "source::same",
        "submission_minimal_authority_source_signature": "source::same",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: (_ for _ in ()).throw(AssertionError("specificity terminal must not repair live paths")),
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda **_: (_ for _ in ()).throw(AssertionError("specificity terminal must not materialize display")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: (_ for _ in ()).throw(AssertionError("specificity terminal must not replay the gate")),
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "platform_terminal"
    assert result["terminal_state"] == "gate_needs_specificity"
    assert result["platform_terminal"] is True
    assert result["unit_results"] == []
    assert result["selected_publication_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["selected_publication_work_unit"]["lifecycle_status"] == "needs_specificity"
    assert result["gate_replay_step"]["status"] == "not_run"
    saved = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "platform_terminal"
    assert saved["terminal_state"] == "gate_needs_specificity"


def test_gate_clearing_batch_does_not_reuse_stale_explicit_analysis_when_current_gate_needs_specificity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_id = "quest-004"
    quest_root = profile.managed_runtime_home / "quests" / quest_id
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "study_delivery_status": "current",
        "gate_fingerprint": "publication-gate::generic",
        "submission_minimal_evaluated_source_signature": "source::same",
        "submission_minimal_authority_source_signature": "source::same",
    }
    current_work_unit_fingerprint = publication_work_units.derive_publication_work_units(gate_report)["fingerprint"]
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["work_unit_fingerprint"] = current_work_unit_fingerprint
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence and paper-facing traceability blockers.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        module.stable_gate_clearing_batch_path(study_root=study_root),
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::previous",
            "status": "executed",
            "gate_fingerprint": "publication-gate::generic",
            "evaluated_source_signature": "source::same",
            "authority_source_signature": "source::same",
            "selected_publication_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
            },
            "explicit_publication_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
            },
            "work_unit_fingerprint": current_work_unit_fingerprint,
            "unit_results": [
                {"unit_id": "repair_paper_live_paths", "status": "updated"},
                {"unit_id": "materialize_display_surface", "status": "materialized"},
            ],
        },
    )

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: (_ for _ in ()).throw(AssertionError("stale analysis work unit must not run")),
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda **_: (_ for _ in ()).throw(AssertionError("stale analysis work unit must not run")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: (_ for _ in ()).throw(AssertionError("specificity terminal must not replay the gate")),
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "platform_terminal"
    assert result["terminal_state"] == "gate_needs_specificity"
    assert result["terminal_reason"] == "current_gate_requires_specific_blocker_object"
    assert result["unit_results"] == []
    assert result["selected_publication_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert result["explicit_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert result["work_unit_currentness"]["current_work_unit_fingerprint"] == current_work_unit_fingerprint
    assert result["work_unit_currentness"]["explicit_work_unit_fingerprint"] == current_work_unit_fingerprint
