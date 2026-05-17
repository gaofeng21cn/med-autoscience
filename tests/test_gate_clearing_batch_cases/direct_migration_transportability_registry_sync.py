from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_run_gate_clearing_batch_direct_migration_waits_for_transportability_registry_sync(
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
            "score compression and calibration drift."
        ),
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    payload_path = paper_root / "time_to_event_grouped_inputs.json"
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
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
                    "caption": "Legacy cumulative-incidence payload under the risk-group summary binding.",
                    "groups": [
                        {
                            "label": "China Q1 low",
                            "times": [0.0, 1.0, 3.0, 5.0],
                            "values": [0.0, 0.001, 0.003, 0.004],
                        }
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
    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "transportability_reporting_surface_needs_sync",
        lambda **_: True,
    )

    def fake_transportability_sync(**_: object) -> dict[str, object]:
        call_order.append("transportability_sync")
        _write_json(
            paper_root / "display_registry.json",
            {
                "schema_version": 1,
                "source_contract_path": "paper/medical_reporting_contract.json",
                "displays": [
                    {
                        "display_id": "km_risk_stratification",
                        "display_kind": "figure",
                        "requirement_key": "time_to_event_risk_group_summary",
                        "catalog_id": "F3",
                    },
                    {
                        "display_id": "transportability_governance",
                        "display_kind": "figure",
                        "requirement_key": "center_transportability_governance_summary_panel",
                        "catalog_id": "F5",
                    },
                ],
            },
        )
        return {"status": "updated", "written_files": [str(paper_root / "display_registry.json")]}

    def fake_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, object]:
        call_order.append("direct_migration")
        registry_payload = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
        requirement_keys = {item["requirement_key"] for item in registry_payload["displays"]}
        assert "center_transportability_governance_summary_panel" in requirement_keys
        assert "multicenter_generalizability_overview" not in requirement_keys
        _write_json(
            payload_path,
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "displays": [
                    {
                        "display_id": "km_risk_stratification",
                        "template_id": "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
                        "risk_group_summaries": [
                            {
                                "label": "Low risk",
                                "sample_size": 10,
                                "events_5y": 1,
                                "mean_predicted_risk_5y": 0.02,
                                "observed_km_risk_5y": 0.01,
                            }
                        ],
                    }
                ],
            },
        )
        return {"status": "synced", "written_files": [str(payload_path)]}

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        call_order.append("materialize")
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        assert payload["displays"][0]["risk_group_summaries"][0]["label"] == "Low risk"
        return {"status": "materialized", "figures_materialized": ["F3", "F5"]}

    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "sync_transportability_reporting_surface",
        fake_transportability_sync,
    )
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
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        quest_id="quest-002",
        source="test-source",
    )

    assert call_order == ["transportability_sync", "direct_migration", "materialize"], result["unit_results"]
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "sync_transportability_reporting_surface",
        "time_to_event_direct_migration",
        "materialize_display_surface",
    ]
    assert result["unit_results"][2]["depends_on"] == [
        "repair_paper_live_paths",
        "sync_transportability_reporting_surface",
    ]


def test_run_gate_clearing_batch_redrives_transportability_sync_when_previous_fingerprint_matches_but_f5_is_missing(
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
            "score compression and calibration drift."
        ),
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    payload_path = paper_root / "time_to_event_grouped_inputs.json"
    _write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                },
                {
                    "display_id": "discrimination_calibration",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                },
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                },
                {
                    "display_id": "decision_curve",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "catalog_id": "F4",
                },
            ],
        },
    )
    _write_json(
        paper_root / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_shell_plan": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                },
                {
                    "display_id": "discrimination_calibration",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                },
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                },
                {
                    "display_id": "decision_curve",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "catalog_id": "F4",
                },
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
                    "caption": "Legacy cumulative-incidence payload under the risk-group summary binding.",
                    "groups": [
                        {
                            "label": "China Q1 low",
                            "times": [0.0, 1.0, 3.0, 5.0],
                            "values": [0.0, 0.001, 0.003, 0.004],
                        }
                    ],
                }
            ],
        },
    )
    _write_blocked_publication_eval(study_root, quest_id="quest-002")
    stale_fingerprint = module._repair_unit_fingerprint(
        unit_id="sync_transportability_reporting_surface",
        paper_root=paper_root,
        gate_report={
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["invalid_figure_semantics_manifest"],
        },
        profile=profile,
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_eval_id": (
                f"publication-eval::{study_root.name}::quest-002::2026-04-21T12:42:39+00:00"
            ),
            "quest_id": "quest-002",
            "study_id": study_root.name,
            "unit_results": [
                {
                    "unit_id": "sync_transportability_reporting_surface",
                    "status": "skipped",
                    "last_success_status": "skipped",
                    "fingerprint": stale_fingerprint,
                }
            ],
            "unit_fingerprints": {"sync_transportability_reporting_surface": stale_fingerprint},
        },
    )
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
    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "transportability_reporting_surface_needs_sync",
        lambda **_: True,
    )

    def fake_transportability_sync(**_: object) -> dict[str, object]:
        call_order.append("transportability_sync")
        _write_json(
            paper_root / "display_registry.json",
            {
                "schema_version": 1,
                "source_contract_path": "paper/medical_reporting_contract.json",
                "displays": [
                    {
                        "display_id": "cohort_flow",
                        "display_kind": "figure",
                        "requirement_key": "cohort_flow_figure",
                        "catalog_id": "F1",
                    },
                    {
                        "display_id": "discrimination_calibration",
                        "display_kind": "figure",
                        "requirement_key": "time_to_event_discrimination_calibration_panel",
                        "catalog_id": "F2",
                    },
                    {
                        "display_id": "km_risk_stratification",
                        "display_kind": "figure",
                        "requirement_key": "time_to_event_risk_group_summary",
                        "catalog_id": "F3",
                    },
                    {
                        "display_id": "decision_curve",
                        "display_kind": "figure",
                        "requirement_key": "time_to_event_decision_curve",
                        "catalog_id": "F4",
                    },
                    {
                        "display_id": "transportability_governance",
                        "display_kind": "figure",
                        "requirement_key": "center_transportability_governance_summary_panel",
                        "catalog_id": "F5",
                    },
                ],
            },
        )
        return {"status": "updated", "written_files": [str(paper_root / "display_registry.json")]}

    def fake_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, object]:
        call_order.append("direct_migration")
        _write_json(
            payload_path,
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "displays": [
                    {
                        "display_id": "km_risk_stratification",
                        "template_id": "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
                        "risk_group_summaries": [
                            {
                                "label": "Low risk",
                                "sample_size": 10,
                                "events_5y": 1,
                                "mean_predicted_risk_5y": 0.02,
                                "observed_km_risk_5y": 0.01,
                            }
                        ],
                    }
                ],
            },
        )
        return {"status": "synced", "written_files": [str(payload_path)]}

    def fake_materialize(*, paper_root: Path) -> dict[str, object]:
        call_order.append("materialize")
        return {"status": "materialized", "figures_materialized": ["F3", "F5"]}

    monkeypatch.setattr(
        module.gate_clearing_batch_transportability,
        "sync_transportability_reporting_surface",
        fake_transportability_sync,
    )
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
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        quest_id="quest-002",
        source="test-source",
    )

    assert call_order == ["transportability_sync", "direct_migration", "materialize"], result["unit_results"]
    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert result_by_unit["sync_transportability_reporting_surface"]["status"] == "updated"
    assert result_by_unit["time_to_event_direct_migration"]["status"] == "synced"
    assert "stale_time_to_event_grouped_payload_blocker" not in result_by_unit
