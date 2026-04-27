from .shared import *


def _contract_backed_test_layout_sidecar(figure_id: str) -> dict[str, object]:
    if figure_id == "F3":
        return {
            "template_id": "binary_calibration_decision_curve_panel",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {
                    "box_id": "calibration_x_axis_title",
                    "box_type": "subplot_x_axis_title",
                    "x0": 0.18,
                    "y0": 0.88,
                    "x1": 0.35,
                    "y1": 0.93,
                },
                {
                    "box_id": "calibration_y_axis_title",
                    "box_type": "subplot_y_axis_title",
                    "x0": 0.02,
                    "y0": 0.35,
                    "x1": 0.06,
                    "y1": 0.62,
                },
            ],
            "panel_boxes": [
                {
                    "box_id": "calibration_panel",
                    "box_type": "calibration_panel",
                    "x0": 0.10,
                    "y0": 0.20,
                    "x1": 0.45,
                    "y1": 0.82,
                },
                {
                    "box_id": "decision_panel",
                    "box_type": "decision_panel",
                    "x0": 0.55,
                    "y0": 0.20,
                    "x1": 0.90,
                    "y1": 0.82,
                },
            ],
            "guide_boxes": [
                {
                    "box_id": "decision_focus_window",
                    "box_type": "focus_window",
                    "x0": 0.62,
                    "y0": 0.32,
                    "x1": 0.80,
                    "y1": 0.64,
                },
            ],
            "metrics": {
                "calibration_axis_window": {"xmin": 0.0, "xmax": 1.0, "ymin": 0.0, "ymax": 1.0},
                "calibration_series": [{"label": "Model", "x": [0.1, 0.8], "y": [0.12, 0.78]}],
                "decision_series": [{"label": "Model", "x": [0.0, 0.5], "y": [0.10, 0.18]}],
                "decision_focus_window": {"xmin": 0.05, "xmax": 0.50},
            },
        }
    return {
        "template_id": "risk_layering_monotonic_bars",
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": [
            {
                "box_id": "risk_y_axis_title",
                "box_type": "y_axis_title",
                "x0": 0.03,
                "y0": 0.30,
                "x1": 0.07,
                "y1": 0.70,
            },
            {
                "box_id": "left_low_bar",
                "box_type": "risk_bar",
                "x0": 0.15,
                "y0": 0.65,
                "x1": 0.22,
                "y1": 0.78,
            },
            {
                "box_id": "right_high_bar",
                "box_type": "risk_bar",
                "x0": 0.70,
                "y0": 0.36,
                "x1": 0.77,
                "y1": 0.78,
            },
        ],
        "panel_boxes": [
            {
                "box_id": "left_panel",
                "box_type": "panel",
                "x0": 0.10,
                "y0": 0.20,
                "x1": 0.45,
                "y1": 0.84,
            },
            {
                "box_id": "right_panel",
                "box_type": "panel",
                "x0": 0.55,
                "y0": 0.20,
                "x1": 0.90,
                "y1": 0.84,
            },
        ],
        "guide_boxes": [],
        "metrics": {
            "left_bars": [
                {"label": "Low", "cases": 20, "events": 2, "risk": 0.10},
                {"label": "High", "cases": 20, "events": 6, "risk": 0.30},
            ],
            "right_bars": [
                {"label": "Low", "cases": 25, "events": 3, "risk": 0.12},
                {"label": "High", "cases": 25, "events": 8, "risk": 0.32},
            ],
        },
    }


def _contract_backed_renderer_script_source(*, sidecar_mode: str) -> str:
    return f"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _layout_sidecar(figure_id: str) -> dict[str, object]:
    if {sidecar_mode!r} == "invalid":
        return {{"figure_id": figure_id, "layout_boxes": [], "panel_boxes": [], "guide_boxes": [], "metrics": {{}}}}
    if figure_id == "F3":
        return {json.dumps(_contract_backed_test_layout_sidecar("F3"), ensure_ascii=False)}
    return {json.dumps(_contract_backed_test_layout_sidecar("F1"), ensure_ascii=False)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--contract-path", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract_path.read_text(encoding="utf-8"))
    for raw_export_path in contract.get("planned_export_paths") or []:
        export_path = Path(raw_export_path)
        if export_path.parts and export_path.parts[0] == args.output_root.name:
            output_path = args.output_root.parent / export_path
        else:
            output_path = args.output_root / export_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() == ".pdf":
            output_path.write_text("%PDF-1.4\\n", encoding="utf-8")
        else:
            output_path.write_bytes(b"png")
    png_export_paths = [Path(item) for item in contract.get("planned_export_paths") or [] if str(item).endswith(".png")]
    if png_export_paths:
        layout_path = png_export_paths[0].with_suffix(".layout.json")
        if layout_path.parts and layout_path.parts[0] == args.output_root.name:
            layout_output_path = args.output_root.parent / layout_path
        else:
            layout_output_path = args.output_root / layout_path
        layout_output_path.parent.mkdir(parents=True, exist_ok=True)
        layout_output_path.write_text(
            json.dumps(_layout_sidecar(str(contract.get("figure_id") or "")), ensure_ascii=False),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".lstrip()


def test_materialize_display_surface_restores_contract_backed_and_shell_mapped_figures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)
    write_default_publication_display_contracts(paper_root)
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    reporting_contract = (
        json.loads(reporting_contract_path.read_text(encoding="utf-8"))
        if reporting_contract_path.exists()
        else {"schema_version": 1}
    )
    reporting_contract["display_shell_plan"] = [
        {
            "display_id": "local_architecture_overview",
            "display_kind": "figure",
            "requirement_key": "local_architecture_overview_figure",
            "catalog_id": "F1",
        },
        {
            "display_id": "figure3_non_gtr_extension",
            "display_kind": "figure",
            "requirement_key": "binary_calibration_decision_curve_panel",
            "catalog_id": "F3",
        },
    ]
    dump_json(reporting_contract_path, reporting_contract)

    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "figure1_local_architecture",
                    "display_kind": "figure",
                    "requirement_key": "figure1_local_architecture",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/figure1_local_architecture.shell.json",
                },
                {
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "legacy_alias_for_figure2",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                },
                {
                    "display_id": "figure3_non_gtr_extension",
                    "display_kind": "figure",
                    "requirement_key": "figure3_non_gtr_extension",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/figure3_non_gtr_extension.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "figures" / "figure1_local_architecture.shell.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/figures/figure1_local_architecture.contract.json",
            "display_id": "figure1_local_architecture",
            "display_kind": "figure",
            "requirement_key": "figure1_local_architecture_contract",
            "catalog_id": "F1",
        },
    )
    dump_json(
        paper_root / "figures" / "figure3_non_gtr_extension.shell.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "display_id": "figure3_non_gtr_extension",
            "display_kind": "figure",
            "requirement_key": "binary_calibration_decision_curve_panel",
            "catalog_id": "F3",
        },
    )
    dump_json(
        paper_root / "figures" / "figure1_local_architecture.contract.json",
        {
            "schema_version": 1,
            "figure_id": "F1",
            "display_id": "figure1_local_architecture",
            "paper_role": "main_text",
            "claim_ids": ["C1"],
            "title": "Local architecture overview",
            "caption": "Contract-backed local architecture figure.",
            "renderer_script_path": "paper/build/render_contract_figure.py",
            "planned_export_paths": [
                "paper/figures/generated/F1_local_architecture_overview.pdf",
                "paper/figures/generated/F1_local_architecture_overview.png",
            ],
            "source_paths": ["paper/figures/figure1_local_architecture.contract.json"],
        },
    )
    dump_json(
        paper_root / "figures" / "figure3_non_gtr_extension.contract.json",
        {
            "schema_version": 1,
            "figure_id": "F3",
            "display_id": "figure3_non_gtr_extension",
            "paper_role": "main_text",
            "claim_ids": ["C3"],
            "title": "Non-GTR extension",
            "caption": "Sibling contract-backed non-GTR extension figure.",
            "renderer_script_path": "paper/build/render_contract_figure.py",
            "planned_export_paths": [
                "paper/figures/generated/F3_non_gtr_extension_summary.pdf",
                "paper/figures/generated/F3_non_gtr_extension_summary.png",
            ],
            "source_paths": ["paper/figures/figure3_non_gtr_extension.contract.json"],
        },
    )
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "render_contract_figure.py").write_text(
        _contract_backed_renderer_script_source(sidecar_mode="valid"),
        encoding="utf-8",
    )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "figure1_local_architecture_contract",
                    "paper_role": "main_text",
                    "title": "Stale local architecture entry",
                    "export_paths": [
                        "paper/figures/generated/F1_local_architecture_overview.pdf",
                        "paper/figures/generated/F1_local_architecture_overview.png",
                    ],
                    "source_paths": ["paper/figures/figure1_local_architecture.contract.json"],
                }
            ],
        },
    )

    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_evidence_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        render_calls.append(template_id)
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_bytes(b"png")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("roc_curve_binary"):
            return fake_evidence_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1", "F2", "F3"]
    assert (paper_root / "figures" / "generated" / "F1_local_architecture_overview.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F1_local_architecture_overview.png").exists()
    assert (paper_root / "figures" / "generated" / "F3_non_gtr_extension_summary.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F3_non_gtr_extension_summary.png").exists()
    assert render_calls == [full_id("roc_curve_binary")]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F1"]["export_paths"] == [
        "paper/figures/generated/F1_local_architecture_overview.pdf",
        "paper/figures/generated/F1_local_architecture_overview.png",
    ]
    assert figures_by_id["F1"]["caption"] == "Contract-backed local architecture figure."
    assert figures_by_id["F2"]["template_id"] == full_id("roc_curve_binary")
    assert figures_by_id["F3"]["caption"] == "Sibling contract-backed non-GTR extension figure."
    expected_contract_catalog = {
        "F1": {
            "template_id": full_id("risk_layering_monotonic_bars"),
            "input_schema_id": "risk_layering_monotonic_inputs_v1",
            "qc_profile": "publication_risk_layering_bars",
            "layout_sidecar_path": "paper/figures/generated/F1_local_architecture_overview.layout.json",
        },
        "F3": {
            "template_id": full_id("binary_calibration_decision_curve_panel"),
            "input_schema_id": "binary_calibration_decision_curve_panel_inputs_v1",
            "qc_profile": "publication_binary_calibration_decision_curve",
            "layout_sidecar_path": "paper/figures/generated/F3_non_gtr_extension_summary.layout.json",
        },
    }
    for figure_id, expected in expected_contract_catalog.items():
        entry = figures_by_id[figure_id]
        assert entry["template_id"] == expected["template_id"]
        assert entry["pack_id"] == "fenggaolab.org.medical-display-core"
        assert entry["renderer_family"] == "python"
        assert entry["input_schema_id"] == expected["input_schema_id"]
        assert entry["qc_profile"] == expected["qc_profile"]
        assert entry["qc_result"]["status"] == "pass"
        assert entry["qc_result"]["engine_id"] == "display_layout_qc_v1"
        assert entry["qc_result"]["qc_profile"] == expected["qc_profile"]
        assert entry["qc_result"]["layout_sidecar_path"] == expected["layout_sidecar_path"]
        assert entry["qc_result"]["metrics"]
        layout_sidecar = json.loads(
            (paper_root.parent / expected["layout_sidecar_path"]).read_text(encoding="utf-8")
        )
        assert layout_sidecar["layout_boxes"]
        assert layout_sidecar["metrics"]


def test_materialize_display_surface_rejects_invalid_contract_backed_layout_sidecar(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "figure1_local_architecture",
                    "display_kind": "figure",
                    "requirement_key": full_id("risk_layering_monotonic_bars"),
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/figure1_local_architecture.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "figures" / "figure1_local_architecture.shell.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/figures/figure1_local_architecture.contract.json",
            "display_id": "figure1_local_architecture",
            "display_kind": "figure",
            "requirement_key": full_id("risk_layering_monotonic_bars"),
            "catalog_id": "F1",
        },
    )
    dump_json(
        paper_root / "figures" / "figure1_local_architecture.contract.json",
        {
            "schema_version": 1,
            "figure_id": "F1",
            "display_id": "figure1_local_architecture",
            "template_id": full_id("risk_layering_monotonic_bars"),
            "paper_role": "main_text",
            "title": "Local architecture overview",
            "caption": "Contract-backed local architecture figure.",
            "renderer_script_path": "paper/build/render_contract_figure.py",
            "planned_export_paths": [
                "paper/figures/generated/F1_local_architecture_overview.pdf",
                "paper/figures/generated/F1_local_architecture_overview.png",
            ],
        },
    )
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "render_contract_figure.py").write_text(
        _contract_backed_renderer_script_source(sidecar_mode="invalid"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="layout QC failed"):
        module.materialize_display_surface(paper_root=paper_root)
