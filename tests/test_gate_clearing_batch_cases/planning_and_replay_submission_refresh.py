from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_gate_clearing_batch_executes_bundle_stage_submission_refresh_then_replays_gate(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "submission_surface_qc_failure_present",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "blocked"
    assert result["gate_blockers"] == ["submission_surface_qc_failure_present"]

def test_run_gate_clearing_batch_refreshes_stale_submission_minimal_authority_without_bundle_stage_override(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "continue_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "clear"
    assert result["gate_blockers"] == ["stale_submission_minimal_authority"]

def test_run_gate_clearing_batch_replays_gate_when_stale_authority_signature_is_current(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_submission_minimal_authority"],
        "current_required_action": "continue_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
        "submission_minimal_authority_status": "current",
        "submission_minimal_evaluated_source_signature": "source::abc",
        "submission_minimal_authority_source_signature": "source::abc",
        "gate_fingerprint": "publication-gate::stale-authority",
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
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(AssertionError("current authority signature must not regenerate package")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["unit_results"] == []
    assert result["selected_publication_work_unit"]["unit_id"] == "publication_gate_replay"
    assert result["selected_publication_work_unit"]["lane"] == "controller"
    assert result["gate_fingerprint"] == "publication-gate::stale-authority"
    assert result["evaluated_source_signature"] == "source::abc"
    assert result["authority_source_signature"] == "source::abc"
    assert result["gate_replay"]["status"] == "clear"
    assert result["gate_blockers"] == ["stale_submission_minimal_authority"]

    marker = result["stale_gate_replay_closure"]
    assert marker["status"] == "closed"
    assert marker["handshake"] == {
        "gate_fingerprint": "publication-gate::stale-authority",
        "evaluated_source_signature": "source::abc",
        "authority_source_signature": "source::abc",
        "blocking_artifact_refs": [],
    }

    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::followup"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: (_ for _ in ()).throw(AssertionError("closed stale gate replay must not run again")),
    )

    skipped = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert skipped["ok"] is True
    assert skipped["status"] == "skipped_stale_gate_replay_closed"
    assert skipped["selected_publication_work_unit"]["unit_id"] == "publication_gate_replay"
    assert skipped["stale_gate_replay_closure"] == marker

def test_run_gate_clearing_batch_executes_bundle_stage_workspace_refresh_before_submission_replay(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "generate_display_exports.py").write_text("print('ok')\n", encoding="utf-8")
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "submission_surface_qc_failure_present",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module,
        "_run_workspace_display_repair_script",
        lambda **_: {"status": "updated", "script_path": str(paper_root / "build" / "generate_display_exports.py")},
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "workspace_display_repair_script",
        "create_submission_minimal_package",
    ]
    assert result["gate_replay"]["status"] == "blocked"
    assert result["gate_blockers"] == ["submission_surface_qc_failure_present"]

def test_run_gate_clearing_batch_syncs_stale_submission_delivery_after_bundle_refresh(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_source_changed",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **_: {"status": "synced", "current_package_root": "studies/004-invasive-architecture/manuscript/current_package"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert result["unit_results"][1]["status"] == "synced"
    assert result["gate_replay"]["status"] == "clear"

def test_run_gate_clearing_batch_reuses_embedded_submission_delivery_sync_after_bundle_refresh(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_source_changed",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {
            "output_root": "paper/submission_minimal",
            "status": "ready",
            "delivery_sync": {
                "status": "synced",
                "current_package_root": "studies/004-invasive-architecture/manuscript/current_package",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("embedded delivery_sync should be reused instead of re-running study_delivery_sync")
        ),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert result["unit_results"][1]["status"] == "synced"
    assert result["unit_results"][1]["result"]["current_package_root"] == (
        "studies/004-invasive-architecture/manuscript/current_package"
    )
