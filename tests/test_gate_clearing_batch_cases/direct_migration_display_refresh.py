from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _write_current_transportability_governance_payload(
    paper_root: Path,
    *,
    max_shift: float = 0.122535630941,
    slope: float = 0.01,
) -> None:
    _write_json(
        paper_root / "center_transportability_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "center_transportability_governance_summary_panel_inputs_v1",
            "source_contract_path": "paper/medical_reporting_contract.json",
            "status": "materialized_from_current_transportability_layout",
            "displays": [
                {
                    "display_id": "transportability_governance",
                    "template_id": "fenggaolab.org.medical-display-core::center_transportability_governance_summary_panel",
                    "catalog_id": "F5",
                    "title": "China-US transportability governance summary",
                    "caption": "Current analysis owner materialized bounded transportability governance.",
                    "metric_family": "discrimination",
                    "metric_panel_title": "Cohort discrimination",
                    "metric_x_label": "C-index",
                    "metric_reference_value": 0.759985474506,
                    "batch_shift_threshold": 0.05,
                    "slope_acceptance_lower": 0.90,
                    "slope_acceptance_upper": 1.10,
                    "oe_ratio_acceptance_lower": 0.90,
                    "oe_ratio_acceptance_upper": 1.10,
                    "summary_panel_title": "Transportability action",
                    "centers": [
                        {
                            "center_id": "china_reference",
                            "center_label": "China",
                            "cohort_role": "Reference cohort",
                            "support_count": 15789,
                            "event_count": 321,
                            "metric_estimate": 0.759985474506,
                            "metric_lower": 0.759985474506,
                            "metric_upper": 0.759985474506,
                            "max_shift": 0.0,
                            "slope": 1.0,
                            "oe_ratio": 1.037291771376,
                            "verdict": "stable",
                            "action": "Use as the reference fit for transportability comparison",
                            "detail": "The China cohort anchors the current 5-year mortality risk surface.",
                        },
                        {
                            "center_id": "nhanes_external",
                            "center_label": "NHANES",
                            "cohort_role": "External comparative population",
                            "support_count": 5659,
                            "event_count": 704,
                            "metric_estimate": 0.564708523287,
                            "metric_lower": 0.564708523287,
                            "metric_upper": 0.564708523287,
                            "max_shift": max_shift,
                            "slope": slope,
                            "oe_ratio": 109.407514187,
                            "verdict": "recalibration_required",
                            "action": "Require recalibration and bounded reporting before any deployment claim",
                            "detail": "Current transportability analysis, not legacy feature-shift payload, owns this materialization.",
                        },
                    ],
                }
            ],
        },
    )


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
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
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

    monkeypatch.setattr(
        module.time_to_event_direct_migration,
        "run_time_to_event_direct_migration",
        fake_direct_migration,
    )
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


def test_run_gate_clearing_batch_routes_historical_feature_shift_f5_payload_to_current_direct_migration_owner(
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
        paper_framing_summary=(
            "China-US comparative transportability and attribution-shift paper with "
            "score compression and feature-shift explanation."
        ),
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
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
                    "collapse_metrics_path": str(
                        quest_root / ".ds" / "worktrees" / "analysis-run" / "outputs" / "collapse_attribution_metrics.json"
                    ),
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
        call_order.append("direct_migration")
        assert (paper_root / "multicenter_generalizability_inputs.json").exists()
        _write_current_transportability_governance_payload(paper_root)
        return {
            "status": "synced",
            "written_files": [str(paper_root / "center_transportability_governance_summary_panel_inputs.json")],
        }

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        call_order.append("materialize")
        reporting_contract = json.loads((paper_root / "medical_reporting_contract.json").read_text(encoding="utf-8"))
        display_registry = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
        current_payload = json.loads(
            (paper_root / "center_transportability_governance_summary_panel_inputs.json").read_text(
                encoding="utf-8"
            )
        )
        assert reporting_contract["display_shell_plan"][4]["display_id"] == "transportability_governance"
        assert reporting_contract["display_shell_plan"][4]["requirement_key"] == (
            "center_transportability_governance_summary_panel"
        )
        assert display_registry["displays"][4]["requirement_key"] == (
            "center_transportability_governance_summary_panel"
        )
        assert current_payload["input_schema_id"] == "center_transportability_governance_summary_panel_inputs_v1"
        current_display = current_payload["displays"][0]
        assert current_display["display_id"] == "transportability_governance"
        assert current_display["template_id"].endswith("::center_transportability_governance_summary_panel")
        assert current_display["centers"][1]["center_label"] == "NHANES"
        assert current_display["centers"][1]["detail"].startswith("Current transportability analysis")
        assert current_display["centers"][1]["verdict"] == "recalibration_required"
        return {"status": "materialized", "figures_materialized": ["F5"]}

    monkeypatch.setattr(
        module.time_to_event_direct_migration,
        "run_time_to_event_direct_migration",
        fake_direct_migration,
    )
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

    assert call_order == ["direct_migration", "materialize"]
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "sync_transportability_reporting_surface",
        "time_to_event_direct_migration",
        "materialize_display_surface",
    ]
    sync_result = result["unit_results"][1]
    assert sync_result["status"] == "updated"
    assert sync_result["result"]["materialization_owner"] == "time_to_event_direct_migration"
    assert not any(key.startswith("legacy_") for key in sync_result["result"])
    assert result["unit_results"][2]["status"] == "synced"
    assert result["repair_blocking_artifact_refs"] == []


def test_run_gate_clearing_batch_blocks_legacy_f3_cumulative_incidence_payload_before_materialize(
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
        paper_framing_summary="China-US transportability paper with risk-stratified cumulative incidence.",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    payload_path = paper_root / "time_to_event_grouped_inputs.json"
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                }
            ],
        },
    )
    _write_json(
        payload_path,
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "template_id": "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
                    "title": "Cumulative incidence by transferred risk quartile",
                    "caption": "Cumulative incidence curves by China-derived risk strata.",
                    "x_label": "Years from baseline",
                    "y_label": "Cumulative incidence",
                    "groups": [
                        {
                            "label": "China Q1 low",
                            "times": [0.0, 1.0, 3.0, 5.0],
                            "values": [0.0, 0.001, 0.003, 0.004],
                        },
                        {
                            "label": "China Q4 high",
                            "times": [0.0, 1.0, 3.0, 5.0],
                            "values": [0.0, 0.012, 0.031, 0.050],
                        },
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
            "medical_publication_surface_named_blockers": ["invalid_figure_semantics_manifest"],
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated"})
    monkeypatch.setattr(module, "_time_to_event_direct_migration_display_inputs_need_refresh", lambda **_: False)
    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "transportability_reporting_surface_needs_sync",
        lambda **_: True,
    )
    stale_sync_payload = {
        "schema_version": 1,
        "input_schema_id": "time_to_event_grouped_inputs_v1",
        "displays": [
            {
                "display_id": "km_risk_stratification",
                "template_id": "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
                "title": "Cumulative incidence by transferred risk quartile",
                "caption": "Cumulative incidence curves by China-derived risk strata.",
                "x_label": "Years from baseline",
                "y_label": "Cumulative incidence",
                "groups": [
                    {
                        "label": "China Q1 low",
                        "times": [0.0, 1.0, 3.0, 5.0],
                        "values": [0.0, 0.001, 0.003, 0.004],
                    },
                    {
                        "label": "China Q4 high",
                        "times": [0.0, 1.0, 3.0, 5.0],
                        "values": [0.0, 0.012, 0.031, 0.050],
                    },
                ],
            }
        ],
    }

    def fake_transportability_sync(**_: object) -> dict[str, object]:
        _write_json(payload_path, stale_sync_payload)
        return {"status": "updated", "written_files": [str(payload_path)]}

    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "sync_transportability_reporting_surface",
        fake_transportability_sync,
    )

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        raise AssertionError("stale legacy grouped payloads must block before display materialization")

    monkeypatch.setattr(module, "_materialize_display_surface", fake_materialize)
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
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        quest_id="quest-002",
        source="test-source",
    )

    assert call_order == []
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "sync_transportability_reporting_surface",
        "stale_time_to_event_grouped_payload_blocker",
        "materialize_display_surface",
    ]
    blocker_result = result["unit_results"][2]
    assert blocker_result["status"] == "failed"
    assert blocker_result["depends_on"] == ["repair_paper_live_paths", "sync_transportability_reporting_surface"]
    assert blocker_result["blocker"] == "stale_legacy_time_to_event_grouped_payload"
    assert blocker_result["blocking_artifact_refs"][0]["artifact_path"] == str(payload_path)
    assert blocker_result["blocking_artifact_refs"][0]["required_owner"] == "time_to_event_direct_migration"
    assert result["unit_results"][3]["status"] == "skipped_failed_dependency"
    assert result["repair_blocking_artifact_refs"] == blocker_result["blocking_artifact_refs"]


def test_run_gate_clearing_batch_syncs_legacy_table1_schema_before_materialize(
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
        paper_framing_summary="China-US transportability paper with baseline Table 1 shell.",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                },
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                },
            ],
        },
    )
    _write_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "steps": [
                {"cohort": "China", "label": "China development cohort", "n": 15789},
                {"cohort": "NHANES", "label": "US validation cohort", "n": 5659},
            ],
            "endpoint_inventory": [{"endpoint": "5-year all-cause mortality", "status": "frozen"}],
        },
    )
    _write_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "catalog_id": "T1",
            "group_columns": [{"label": "China (n=15789)"}, {"label": "NHANES (n=5659)"}],
            "variables": ["Age, years", "Male sex, n (%)"],
        },
    )
    table1_path = paper_root / "tables" / "T1_baseline_characteristics.csv"
    table1_path.parent.mkdir(parents=True, exist_ok=True)
    table1_path.write_text(
        "\n".join(
            [
                "Variable,China (n=15789),NHANES (n=5659)",
                "\"Age, years\",\"51.58 [42.19, 60.15]\",\"63.00 [53.00, 72.00]\"",
                "\"Male sex, n (%)\",9619 (60.9%),2933 (51.8%)",
            ]
        )
        + "\n",
        encoding="utf-8",
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
            "medical_publication_surface_named_blockers": ["invalid_table_shell_manifest"],
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated"})
    monkeypatch.setattr(module, "_time_to_event_direct_migration_display_inputs_need_refresh", lambda **_: False)
    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "transportability_reporting_surface_needs_sync",
        lambda **_: False,
    )

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        call_order.append("materialize")
        table1_payload = json.loads((paper_root / "baseline_characteristics_schema.json").read_text(encoding="utf-8"))
        assert [item["label"] for item in table1_payload["groups"]] == [
            "China (n=15789)",
            "NHANES (n=5659)",
        ]
        assert [item["label"] for item in table1_payload["variables"]] == ["Age, years", "Male sex, n (%)"]
        assert table1_payload["variables"][0]["values"] == ["51.58 [42.19, 60.15]", "63.00 [53.00, 72.00]"]
        return {"status": "materialized", "tables_materialized": ["T1"]}

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
        "sync_publication_shell_surface",
        "materialize_display_surface",
    ]
    sync_result = result["unit_results"][1]
    assert sync_result["status"] == "synced"
    assert sync_result["depends_on"] == ["repair_paper_live_paths"]
    assert sync_result["result"]["source_paths"]["table1_source"] == str(table1_path)
    assert result["repair_blocking_artifact_refs"] == []


def test_transportability_f5_ignores_historical_runtime_metrics_path_and_uses_current_direct_migration_payload(
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
        paper_framing_summary=(
            "China-US comparative transportability and attribution-shift paper with "
            "score compression and feature-shift explanation."
        ),
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    legacy_metrics_path = str(
        profile.workspace_root
        / "ops"
        / "med-the research workflow"
        / "runtime"
        / "quests"
        / "quest-002"
        / ".ds"
        / "worktrees"
        / "analysis-run"
        / "outputs"
        / "collapse_attribution_metrics.json"
    )
    assert not Path(legacy_metrics_path).exists()
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
                    "template_id": "fenggaolab.org.medical-display-core::multicenter_generalizability_overview",
                    "title": "Predictor distribution differences and transported score narrowing",
                    "caption": "Feature-shift attribution for transportability loss.",
                    "collapse_metrics_path": legacy_metrics_path,
                    "feature_shift_csv_path": "analysis/collapse_attribution/outputs/feature_shift_contributions.csv",
                    "risk_distribution_csv_path": (
                        "analysis/collapse_attribution/outputs/"
                        "predicted_risk_distribution_summary.csv"
                    ),
                    "primary_driver": "HDL",
                }
            ],
        },
    )
    _write_blocked_publication_eval(study_root, quest_id="quest-002")

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
        _write_current_transportability_governance_payload(paper_root, max_shift=0.122535630941, slope=0.01)
        return {
            "status": "synced",
            "written_files": [str(paper_root / "center_transportability_governance_summary_panel_inputs.json")],
        }

    monkeypatch.setattr(
        module.time_to_event_direct_migration,
        "run_time_to_event_direct_migration",
        fake_direct_migration,
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda *, paper_root: {"status": "materialized", "figures_materialized": ["F5"]},
    )
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

    sync_result = result["unit_results"][1]
    assert sync_result["unit_id"] == "sync_transportability_reporting_surface"
    assert sync_result["status"] == "updated"
    migrated_payload = json.loads(
        (paper_root / "center_transportability_governance_summary_panel_inputs.json").read_text(encoding="utf-8")
    )
    migrated_display = migrated_payload["displays"][0]
    assert migrated_display["centers"][1]["max_shift"] == 0.122535630941
    assert migrated_display["centers"][1]["slope"] == 0.01
    assert not any(key.startswith("legacy_") for key in sync_result["result"])
