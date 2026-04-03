from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+aRX0AAAAASUVORK5CYII="
)


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(PNG_1X1_BASE64))


def make_workspace(tmp_path: Path) -> Path:
    paper_root = tmp_path / "workspace" / "paper"
    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Display Surface Manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Test citation [@ref1].

# Main Figures

## Figure 1. Main figure

Caption.

![](../figures/F1_main.png)

# Main Tables

| Characteristic | Value |
| --- | --- |
| Age | 52 |
""",
    )
    write_text(
        paper_root / "references.bib",
        """@article{ref1,
  title={A primary source},
  author={Author, A.},
  journal={Journal},
  year={2024}
}
""",
    )
    write_png(paper_root / "figures" / "F1_main.png")
    write_text(paper_root / "figures" / "F1_main.pdf", "%PDF-1.4\n")
    write_text(paper_root / "tables" / "T1_summary.csv", "Characteristic,Value\nAge,52\n")
    write_text(paper_root / "tables" / "T1_summary.md", "| Characteristic | Value |\n| --- | --- |\n| Age | 52 |\n")
    write_text(paper_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown": "paper/build/review_manuscript.md",
            "output_pdf": "paper/paper.pdf",
        },
    )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "roc_curve_binary",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "binary_prediction_curve_inputs_v1",
                    "qc_profile": "publication_evidence_curve",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Main figure",
                    "export_paths": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "paper_role": "main_text",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Summary table",
                    "asset_paths": ["paper/tables/T1_summary.csv", "paper/tables/T1_summary.md"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )
    return paper_root


def test_create_submission_minimal_package_preserves_display_surface_metadata(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["figures"][0]["template_id"] == "roc_curve_binary"
    assert manifest["figures"][0]["renderer_family"] == "r_ggplot2"
    assert manifest["figures"][0]["qc_profile"] == "publication_evidence_curve"
    assert manifest["tables"][0]["table_shell_id"] == "table1_baseline_characteristics"
    assert manifest["tables"][0]["qc_profile"] == "publication_table_baseline"
