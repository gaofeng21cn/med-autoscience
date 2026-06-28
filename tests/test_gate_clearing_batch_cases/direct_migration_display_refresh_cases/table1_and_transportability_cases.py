from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_gate_clearing_batch_cases.direct_migration_display_refresh import (
    _write_blocked_publication_eval,
    _write_current_transportability_governance_payload,
    _write_json,
    make_profile,
    write_study,
)

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
            "written_files": [str(paper_root / "generalizability_subgroup_composite_inputs.json")],
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
        (paper_root / "generalizability_subgroup_composite_inputs.json").read_text(encoding="utf-8")
    )
    migrated_display = migrated_payload["displays"][0]
    assert migrated_display["source_context"]["calibration_shift"] == 0.122535630941
    assert migrated_display["subgroup_rows"][2]["estimate"] == 0.01
    assert not any(key.startswith("legacy_") for key in sync_result["result"])
