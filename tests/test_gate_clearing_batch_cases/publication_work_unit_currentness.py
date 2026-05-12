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


def test_publication_work_unit_selection_keeps_explicit_upstream_repair_ahead_of_delivery_redrive() -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_currentness")
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
            "stale_study_delivery_mirror",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_map_missing_or_incomplete"],
        "study_delivery_status": "stale_source_changed",
        "blocking_artifact_refs": [
            {
                "blocker": "claim_evidence_consistency_failed",
                "source_path": "paper/claim_evidence_map.json",
            }
        ],
    }
    work_unit_fingerprint = publication_work_units.derive_publication_work_units(gate_report)["fingerprint"]
    publication_eval_payload = {
        "recommended_actions": [
            {
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence and paper-facing traceability blockers.",
                },
            }
        ]
    }

    selection = module.publication_work_unit_selection(
        publication_eval_payload=publication_eval_payload,
        latest_batch={},
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=True,
    )

    assert selection["explicit_next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert selection["current_next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert selection["selected_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


def test_publication_work_unit_selection_supersedes_gate_specificity_after_targets_are_complete() -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_currentness")
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["missing_publication_anchor"],
        "anchor_kind": "missing",
        "bundle_tasks_downstream_only": True,
        "blocking_artifact_refs": [
            {
                "blocker": "missing_publication_anchor",
                "target_kind": "claim",
                "target_id": "claim_evidence_map",
                "source_path": "/tmp/study/paper/claim_evidence_map.json",
            },
            {
                "blocker": "missing_publication_anchor",
                "target_kind": "figure",
                "target_id": "figure_catalog",
                "source_path": "/tmp/study/paper/figures/figure_catalog.json",
            },
            {
                "blocker": "missing_publication_anchor",
                "target_kind": "table",
                "target_id": "submission_manifest",
                "source_path": "/tmp/study/paper/submission_minimal/submission_manifest.json",
            },
            {
                "blocker": "missing_publication_anchor",
                "target_kind": "metric",
                "target_id": "main_result_metrics",
                "source_path": "/tmp/study/artifacts/results/main_result.json",
            },
            {
                "blocker": "missing_publication_anchor",
                "target_kind": "source_path",
                "target_id": "publishability_gate",
                "source_path": "/tmp/study/artifacts/publication_eval/latest.json",
            },
        ],
    }
    work_unit_fingerprint = publication_work_units.derive_publication_work_units(gate_report)["fingerprint"]
    publication_eval_payload = {
        "recommended_actions": [
            {
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the publication gate to identify concrete blocker targets.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": "/tmp/study/paper/claim_evidence_map.json",
                        "blocking_reason": "missing_publication_anchor",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": "/tmp/study/paper/figures/figure_catalog.json",
                        "blocking_reason": "missing_publication_anchor",
                    },
                    {
                        "target_kind": "table",
                        "target_id": "submission_manifest",
                        "source_path": "/tmp/study/paper/submission_minimal/submission_manifest.json",
                        "blocking_reason": "missing_publication_anchor",
                    },
                    {
                        "target_kind": "metric",
                        "target_id": "main_result_metrics",
                        "source_path": "/tmp/study/artifacts/results/main_result.json",
                        "blocking_reason": "missing_publication_anchor",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publishability_gate",
                        "source_path": "/tmp/study/artifacts/publication_eval/latest.json",
                        "blocking_reason": "missing_publication_anchor",
                    },
                ],
            }
        ]
    }

    selection = module.publication_work_unit_selection(
        publication_eval_payload=publication_eval_payload,
        latest_batch={},
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=False,
    )

    assert selection["explicit_next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert selection["current_next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert selection["selected_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert selection["terminal_reason"] is None


def test_publication_gate_replay_selects_current_submission_authority_closure() -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_currentness")
    gate_report = {
        "status": "blocked",
        "current_required_action": "complete_bundle_stage",
        "blockers": [
            "stale_submission_minimal_authority",
            "continue_bundle_stage",
        ],
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
        "submission_minimal_authority_status": "stale_source_changed",
        "submission_minimal_evaluated_source_signature": "source::new",
        "submission_minimal_authority_source_signature": "source::old",
        "gate_fingerprint": "publication-gate::authority-sync",
    }
    publication_eval_payload = {
        "recommended_actions": [
            {
                "work_unit_fingerprint": "publication-gate-replay::old",
                "next_work_unit": {
                    "unit_id": "publication_gate_replay",
                    "lane": "controller",
                    "summary": "Replay the publication gate after controller work.",
                },
            }
        ]
    }

    selection = module.publication_work_unit_selection(
        publication_eval_payload=publication_eval_payload,
        latest_batch={},
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=False,
    )

    assert selection["explicit_next_work_unit"]["unit_id"] == "publication_gate_replay"
    assert selection["current_next_work_unit"]["unit_id"] == "submission_authority_sync_closure"
    assert selection["selected_publication_work_unit"]["unit_id"] == "submission_authority_sync_closure"


def test_clear_gate_replay_closes_transient_authority_settle_skip() -> None:
    currentness = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_currentness")
    lifecycle = importlib.import_module("med_autoscience.controllers.publication_work_unit_lifecycle")
    source_eval_id = "publication-eval::004-invasive-architecture::quest-004::2026-05-12T12:00:00+00:00"
    unit_results = [
        {"unit_id": "create_submission_minimal_package", "status": "ok"},
        {
            "unit_id": "sync_submission_minimal_delivery",
            "status": "skipped_authority_not_settled",
            "retry_reason": "authority_not_settled",
            "retry_after": "2026-05-12T12:00:30+00:00",
            "retry_after_seconds": 5,
        },
    ]
    gate_replay = {"status": "clear", "allow_write": True, "blockers": []}

    lifecycle_record = lifecycle.build_lifecycle_record(
        source_eval_id=source_eval_id,
        study_id="004-invasive-architecture",
        quest_id="quest-004",
        selected_work_unit={
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
        },
        unit_results=unit_results,
        gate_replay=gate_replay,
    )

    assert lifecycle_record["status"] == "done"
    assert "retry" not in lifecycle_record
    assert currentness.batch_closed_for_source_eval(
        {
            "source_eval_id": source_eval_id,
            "status": "executed",
            "unit_results": unit_results,
            "gate_replay": gate_replay,
        },
        source_eval_id=source_eval_id,
    )
