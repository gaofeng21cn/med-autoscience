from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generalizability_subgroup_composite_panel_preserves_ch_bounded_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure34",
                    "display_kind": "figure",
                    "requirement_key": "generalizability_subgroup_composite_panel",
                    "catalog_id": "F34",
                    "shell_path": "paper/figures/Figure34.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure34",
                    "template_id": "generalizability_subgroup_composite_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure34",
                    "template_id": "fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel",
                    "title": "Generalizability and subgroup discrimination composite for external validation",
                    "caption": "Regression lock for bounded generalizability plus subgroup robustness evidence.",
                    "metric_family": "discrimination",
                    "primary_label": "Locked model",
                    "comparator_label": "Derivation cohort",
                    "overview_panel_title": "External cohort discrimination overview",
                    "overview_x_label": "AUROC",
                    "overview_rows": [
                        {
                            "cohort_id": "external_a",
                            "cohort_label": "External A",
                            "support_count": 184,
                            "event_count": 29,
                            "metric_value": 0.82,
                            "comparator_metric_value": 0.79,
                        },
                        {
                            "cohort_id": "external_b",
                            "cohort_label": "External B",
                            "support_count": 163,
                            "event_count": 21,
                            "metric_value": 0.78,
                            "comparator_metric_value": 0.79,
                        },
                    ],
                    "subgroup_panel_title": "Prespecified subgroup discrimination stability",
                    "subgroup_x_label": "AUROC",
                    "subgroup_reference_value": 0.80,
                    "subgroup_rows": [
                        {
                            "subgroup_id": "age_ge_65",
                            "subgroup_label": "Age ≥65 years",
                            "group_n": 201,
                            "estimate": 0.82,
                            "lower": 0.78,
                            "upper": 0.86,
                        },
                        {
                            "subgroup_id": "female",
                            "subgroup_label": "Female",
                            "group_n": 173,
                            "estimate": 0.79,
                            "lower": 0.75,
                            "upper": 0.83,
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert [item["cohort_label"] for item in layout_sidecar["metrics"]["overview_rows"]] == ["External A", "External B"]
    assert [item["subgroup_label"] for item in layout_sidecar["metrics"]["subgroup_rows"]] == [
        "Age ≥65 years",
        "Female",
    ]
    assert layout_sidecar["metrics"]["subgroup_reference_value"] == 0.80
    assert layout_sidecar["metrics"]["legend_labels"] == ["Locked model", "Derivation cohort"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "legend" for box in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
