from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_quality_repair_batch_route_context_preempts_current_submission_refresh_selection(
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
        manuscript_family="primary_care_gap",
    )
    quest_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_root = profile.managed_runtime_home / "quests" / quest_id
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-003" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    publication_eval_payload["recommended_actions"][0]["specificity_targets"] = [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "table_catalog",
            "source_path": str(study_root / "paper" / "tables" / "table_catalog.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
        ],
        "current_required_action": "return_to_publishability_gate",
        "medical_publication_surface_status": "blocked",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
        "bundle_tasks_downstream_only": True,
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated", "repaired_files": []})
    materialize_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda *, paper_root: (materialize_calls.append(paper_root), {"status": "materialized"})[1],
    )
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(AssertionError("analysis repair must not materialize submission package")),
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("analysis repair must not sync delivery package")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_submission_minimal_authority"],
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context={
            "control_plane_snapshot": {
                "surface": "control_plane_snapshot",
                "control_state": "supervisor_gated",
                "canonical_next_action": "resume_same_study_line",
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
                "dispatch_gate": {
                    "state": "blocked",
                    "blocking_reasons": ["publication_supervisor_state.bundle_tasks_downstream_only"],
                },
                "route_authorization": {
                    "authorized": False,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": False,
                    "runtime_recovery_allowed": False,
                },
            },
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "requires_human_confirmation": False,
                "source_eval_id": publication_eval_payload["eval_id"],
                "work_unit_fingerprint": "publication-blockers::quality-repair",
            },
        },
    )

    assert materialize_calls == [paper_root]
    assert result["selected_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "materialize_display_surface",
    ]
