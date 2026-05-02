from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_run_gate_clearing_batch_rematerializes_stale_direct_migration_display_inputs_before_display_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm-cvd-mortality-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "display_kind": "figure",
                    "requirement_key": "multicenter_generalizability_overview",
                    "catalog_id": "F5",
                }
            ],
        },
    )
    _write_json(
        paper_root / "multicenter_generalizability_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "multicenter_generalizability_inputs_v1",
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "template_id": "fenggaolab.org.medical-display-core::multicenter_generalizability_overview",
                    "overview_mode": "center_support_counts",
                    "center_event_y_label": "5-year CVD events",
                    "coverage_y_label": "Patient count",
                    "center_event_counts": [
                        {"center_label": "Center 01", "split_bucket": "validation", "event_count": 2}
                    ],
                    "coverage_panels": [
                        {
                            "panel_id": "region",
                            "title": "Region coverage",
                            "layout_role": "wide_left",
                            "bars": [{"label": "Central China", "count": 1}],
                        },
                        {
                            "panel_id": "north_south",
                            "title": "North vs South coverage",
                            "layout_role": "top_right",
                            "bars": [{"label": "South", "count": 1}],
                        },
                        {
                            "panel_id": "urban_rural",
                            "title": "Urban/rural coverage",
                            "layout_role": "bottom_right",
                            "bars": [{"label": "Urban", "count": 1}],
                        },
                    ],
                    "source_paths": [
                        "ops/med-the research workflow/runtime/quests/quest-002/paper/multicenter_generalizability_inputs.json"
                    ],
                }
            ],
        },
    )
    _write_blocked_publication_eval(study_root, quest_id="quest-002")
    call_order: list[str] = []

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
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated"})

    def fake_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, object]:
        call_order.append("direct_migration")
        _write_json(
            paper_root / "multicenter_generalizability_inputs.json",
            {
                "schema_version": 1,
                "input_schema_id": "multicenter_generalizability_inputs_v1",
                "displays": [
                    {
                        "display_id": "multicenter_generalizability",
                        "template_id": "fenggaolab.org.medical-display-core::multicenter_generalizability_overview",
                        "title": "Internal multicenter heterogeneity summary",
                        "caption": "Center-level event support with coverage context under the frozen split.",
                        "overview_mode": "center_support_counts",
                        "center_event_y_label": "5-year CVD events",
                        "coverage_y_label": "Patient count",
                        "center_event_counts": [
                            {"center_label": "Center 01", "split_bucket": "validation", "event_count": 2}
                        ],
                        "coverage_panels": [
                            {
                                "panel_id": "region",
                                "title": "Region coverage",
                                "layout_role": "wide_left",
                                "bars": [{"label": "Central China", "count": 1}],
                            },
                            {
                                "panel_id": "north_south",
                                "title": "North vs South coverage",
                                "layout_role": "top_right",
                                "bars": [{"label": "South", "count": 1}],
                            },
                            {
                                "panel_id": "urban_rural",
                                "title": "Urban/rural coverage",
                                "layout_role": "bottom_right",
                                "bars": [{"label": "Urban", "count": 1}],
                            },
                        ],
                    }
                ],
            },
        )
        return {
            "status": "synced",
            "study_root": str(study_root),
            "paper_root": str(paper_root),
            "written_files": [str(paper_root / "multicenter_generalizability_inputs.json")],
            "blockers": [],
        }

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        payload = json.loads((paper_root / "multicenter_generalizability_inputs.json").read_text(encoding="utf-8"))
        display = payload["displays"][0]
        assert display["title"] == "Internal multicenter heterogeneity summary"
        assert display["caption"] == "Center-level event support with coverage context under the frozen split."
        assert "source_paths" not in display
        call_order.append("materialize")
        return {"status": "materialized", "figures_materialized": ["F5"]}

    monkeypatch.setattr(module, "_run_time_to_event_direct_migration", fake_direct_migration)
    monkeypatch.setattr(module, "_materialize_display_surface", fake_materialize)
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
        study_id="002-dm-cvd-mortality-risk",
        study_root=study_root,
        quest_id="quest-002",
        source="test-source",
    )

    assert call_order == ["direct_migration", "materialize"]
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "time_to_event_direct_migration",
        "materialize_display_surface",
    ]
    assert result["unit_results"][1]["result"]["status"] == "synced"


def test_run_gate_clearing_batch_does_not_direct_migrate_legacy_feature_shift_f5_payload(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    payload_path = paper_root / "multicenter_generalizability_inputs.json"
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "display_kind": "figure",
                    "requirement_key": "multicenter_generalizability_overview",
                    "catalog_id": "F5",
                }
            ],
        },
    )
    _write_json(
        payload_path,
        {
            "schema_version": 1,
            "input_schema_id": "multicenter_generalizability_inputs_v1",
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "template_id": (
                        "fenggaolab.org.medical-display-core::"
                        "multicenter_generalizability_overview"
                    ),
                    "title": "Predictor distribution differences and transported score narrowing",
                    "caption": "Feature-shift attribution for transportability loss.",
                    "claim_note": "HDL dominated feature shift and score compression.",
                    "collapse_metrics_path": "analysis/collapse_attribution/outputs/collapse_attribution_metrics.json",
                    "feature_shift_csv_path": "analysis/collapse_attribution/outputs/feature_shift_contributions.csv",
                    "risk_distribution_csv_path": (
                        "analysis/collapse_attribution/outputs/"
                        "predicted_risk_distribution_summary.csv"
                    ),
                    "primary_driver": "hdl_cholesterol",
                }
            ],
        },
    )
    _write_blocked_publication_eval(study_root, quest_id="quest-002")
    call_order: list[str] = []

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
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["invalid_figure_semantics_manifest"],
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated"})

    def fake_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, object]:
        raise AssertionError("legacy feature-shift F5 payloads must not be direct-migration refreshed")

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        call_order.append("materialize")
        raise ValueError(
            "multicenter_generalizability_inputs.json display `multicenter_generalizability` "
            "must contain a non-empty center_event_counts list"
        )

    monkeypatch.setattr(module, "_run_time_to_event_direct_migration", fake_direct_migration)
    monkeypatch.setattr(module, "_materialize_display_surface", fake_materialize)
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        quest_id="quest-002",
        source="test-source",
    )

    assert call_order == ["materialize"]
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "materialize_display_surface",
    ]
    materialize_result = result["unit_results"][1]
    assert materialize_result["status"] == "failed"
    assert materialize_result["terminal_state"] == "gate_needs_specificity"
    assert materialize_result["blocking_artifact_refs"] == [
        {
            "blocker": "display_surface_materialization_failed",
            "artifact_path": str(payload_path.resolve()),
            "artifact_role": "display_input_payload",
            "failure_reason": (
                "multicenter_generalizability_inputs.json display `multicenter_generalizability` "
                "must contain a non-empty center_event_counts list"
            ),
            "terminal_state": "gate_needs_specificity",
        }
    ]
    assert result["repair_blocking_artifact_refs"] == materialize_result["blocking_artifact_refs"]
