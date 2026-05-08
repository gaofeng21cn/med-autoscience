from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_run_gate_clearing_batch_normalizes_f3_payload_rewritten_by_transport_sync(
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
                    "title": "Risk-group summary",
                    "caption": "Current payload before transport sync.",
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
        payload = json.loads((paper_root / "time_to_event_grouped_inputs.json").read_text(encoding="utf-8"))
        display = payload["displays"][0]
        assert display["template_id"] == "fenggaolab.org.medical-display-core::cumulative_incidence_grouped"
        assert display["legacy_requested_template_id"] == (
            "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
        )
        return {"status": "materialized", "figures_materialized": ["F3"]}

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

    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "sync_transportability_reporting_surface",
        "normalize_legacy_time_to_event_grouped_payloads",
        "materialize_display_surface",
    ]
    assert result["unit_results"][2]["status"] == "updated"
    assert result["repair_blocking_artifact_refs"] == []
