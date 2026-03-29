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


def make_paper_workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "paper"

    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Test Medical Manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

This is a manuscript citation [@ref1].

# Main Figures

## Figure 1. Main figure

Caption.

![](../figures/F1_main.png)

## Supplementary Figure S1. Supplementary figure

Caption.

![](../figures/FS1_supp.png)

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
    write_text(paper_root / "figures" / "F1_main.pdf", "%PDF-1.4\n%main figure\n")
    write_png(paper_root / "figures" / "FS1_supp.png")
    write_text(paper_root / "figures" / "FS1_supp.pdf", "%PDF-1.4\n%supp figure\n")
    write_text(paper_root / "tables" / "T1_summary.csv", "Characteristic,Value\nAge,52\n")
    write_text(paper_root / "tables" / "T1_summary.md", "| Characteristic | Value |\n| --- | --- |\n| Age | 52 |\n")
    write_text(paper_root / "paper.pdf", "%PDF-1.4\n%paper bundle\n")

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
                    "paper_role": "main_text",
                    "title": "Main figure",
                    "export_paths": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
                },
                {
                    "figure_id": "FS1",
                    "paper_role": "supplementary",
                    "title": "Supplementary figure",
                    "export_paths": ["paper/figures/FS1_supp.pdf", "paper/figures/FS1_supp.png"],
                },
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
                    "paper_role": "main_text",
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
            "included_assets": [
                {"path": "paper/paper.pdf", "kind": "compiled_pdf", "status": "present"},
                {"path": "paper/figures/F1_main.pdf", "kind": "figure_export", "status": "present"},
                {"path": "paper/figures/FS1_supp.pdf", "kind": "supplementary_figure_export", "status": "present"},
                {"path": "paper/tables/T1_summary.csv", "kind": "table_asset", "status": "present"},
            ],
        },
    )

    return paper_root


def test_create_submission_minimal_package_creates_output_directory_and_copies_pdf(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert submission_root.exists()
    assert (submission_root / "paper.pdf").exists()
    assert manifest["output_root"] == str(submission_root)


def test_create_submission_minimal_package_writes_manifest_and_docx_path(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "submission_manifest.json"
    docx_path = submission_root / "manuscript.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["publication_profile"] == "general_medical_journal"
    assert manifest_payload["citation_style"] == "AMA"
    assert manifest_payload["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"
    assert manifest_payload["manuscript"]["docx_path"] == "paper/submission_minimal/manuscript.docx"
    assert manifest_payload["naming_map"]["figures"] == {
        "F1": "Figure1",
        "FS1": "SupplementaryFigureS1",
    }
    assert manifest_payload["naming_map"]["tables"] == {
        "T1": "Table1",
    }
    assert manifest_payload == manifest


def test_create_submission_minimal_package_defaults_to_ama_citation_style(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["citation_style"] == "AMA"


def test_create_submission_minimal_package_copies_figures_and_tables(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    expected_paths = [
        submission_root / "figures" / "Figure1.pdf",
        submission_root / "figures" / "Figure1.png",
        submission_root / "figures" / "SupplementaryFigureS1.pdf",
        submission_root / "figures" / "SupplementaryFigureS1.png",
        submission_root / "tables" / "Table1.csv",
        submission_root / "tables" / "Table1.md",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_create_submission_minimal_package_syncs_study_delivery_when_context_is_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    called: dict[str, object] = {}

    def fake_can_sync(*, paper_root: Path) -> bool:
        called["can_sync_paper_root"] = paper_root
        return True

    def fake_sync(*, paper_root: Path, stage: str) -> dict:
        called["sync_paper_root"] = paper_root
        called["sync_stage"] = stage
        return {"stage": stage}

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", fake_can_sync)
    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert called["can_sync_paper_root"] == paper_root
    assert called["sync_paper_root"] == paper_root
    assert called["sync_stage"] == "submission_minimal"
