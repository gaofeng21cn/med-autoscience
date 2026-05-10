from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _stub_submission_hardening_gate(module: Any, monkeypatch: Any, *, study_root: Path, paper_root: Path) -> None:
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
                "stale_submission_minimal_authority",
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: (_ for _ in ()).throw(AssertionError("submission hardening should not repair live paths")),
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
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )


def test_run_gate_clearing_batch_refreshes_submission_hardening_without_live_path_repair(
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    _stub_submission_hardening_gate(module, monkeypatch, study_root=study_root, paper_root=paper_root)

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "clear"


def test_run_gate_clearing_batch_closes_submission_authority_sync_with_delivery_sync(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_home / "quests" / quest_id
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-003" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_submission_minimal_fingerprint_inputs(paper_root)
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "publication_gate_replay",
        "lane": "controller",
        "summary": "Replay the publication gate after controller work.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "continue_bundle_stage",
        ],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
        "submission_minimal_authority_status": "stale_source_changed",
        "submission_minimal_evaluated_source_signature": "source::new",
        "submission_minimal_authority_source_signature": "source::old",
        "gate_fingerprint": "publication-gate::authority-sync",
    }
    seen: dict[str, dict[str, Any]] = {}

    def create_submission_minimal_package(*, control_plane_route_context=None, **_: object) -> dict[str, object]:
        seen["submission_context"] = dict(control_plane_route_context or {})
        return {
            "output_root": "paper/submission_minimal",
            "status": "ready",
            "control_plane_route_gate": {
                "controller_route_gate": {"authorized": True},
            },
        }

    def sync_study_delivery(*, control_plane_route_context=None, **_: object) -> dict[str, object]:
        seen["delivery_context"] = dict(control_plane_route_context or {})
        return {
            "status": "synced",
            "current_package_root": "studies/003-dpcc-primary-care-phenotype-treatment-gap/manuscript/current_package",
            "source_signature": "source::new",
            "authority_source_signature": "source::new",
        }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module.submission_minimal, "create_submission_minimal_package", create_submission_minimal_package)
    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", sync_study_delivery)
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_study_delivery_mirror"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["selected_publication_work_unit"]["unit_id"] == "submission_authority_sync_closure"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert seen["submission_context"]["controller_route_context"]["work_unit_id"] == "submission_authority_sync_closure"
    assert seen["delivery_context"]["controller_route_context"]["work_unit_id"] == "submission_authority_sync_closure"
    assert result["unit_results"][0]["result"]["control_plane_route_gate"]["controller_route_gate"]["authorized"] is True


def test_run_gate_clearing_batch_reruns_same_eval_after_failed_submission_hardening_batch(
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    _write_json(
        module.stable_gate_clearing_batch_path(study_root=study_root),
        {
            "schema_version": 1,
            "source_eval_id": publication_eval_payload["eval_id"],
            "status": "executed",
            "unit_results": [
                {
                    "unit_id": "repair_paper_live_paths",
                    "status": "failed",
                    "error": "[Errno 2] No such file or directory: '/ABS/PATH/TO/ds'",
                },
                {
                    "unit_id": "create_submission_minimal_package",
                    "status": "skipped_failed_dependency",
                    "failed_dependencies": ["repair_paper_live_paths"],
                },
            ],
            "gate_replay": {
                "status": "blocked",
                "blockers": [
                    "stale_submission_minimal_authority",
                    "submission_hardening_incomplete",
                ],
            },
        },
    )
    _stub_submission_hardening_gate(module, monkeypatch, study_root=study_root, paper_root=paper_root)

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "clear"
