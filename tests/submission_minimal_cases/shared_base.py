from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import shutil
import zipfile
import zlib

from pypdf import PdfReader


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_scanline = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw_scanline)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return len(data).to_bytes(4, "big") + chunk_type + data + crc.to_bytes(4, "big")

    png_bytes = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"),
            chunk(b"IDAT", compressed),
            chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png_bytes)


def write_docx(path: Path, text: str) -> None:
    from docx import Document

    path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    document.add_paragraph(text)
    document.sections[0].footer.paragraphs[0].text = f"{text} footer"
    document.save(path)


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


def make_current_draft_workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "paper"

    write_text(
        paper_root / "draft.md",
        """# Draft

## Title

Current Draft Title

## Abstract

### Aims

Draft abstract aim with evidence [@ref1].

### Methods

Draft abstract methods.

### Results

Draft abstract results.

### Conclusions

Draft abstract conclusions.

## Introduction

Intro paragraph with citation [@ref1].

## Methods

Methods paragraph.

## Results

Results paragraph.

## Discussion

Discussion paragraph.

## Conclusion

Conclusion paragraph.
""",
        )
    write_text(
        paper_root / "references.bib",
        """@article{ref1,
  title={A primary source},
  author={Author, A. and Author, B.},
  journal={Journal},
  year={2024}
}
""",
    )
    write_png(paper_root / "figures" / "F1_main.png")
    write_text(paper_root / "figures" / "F1_main.pdf", "%PDF-1.4\n%main figure\n")
    write_text(paper_root / "tables" / "T1_summary.md", "| Characteristic | Value |\n| --- | --- |\n| Age | 52 |\n")
    write_text(paper_root / "paper.pdf", "%PDF-1.4\n%paper bundle\n")

    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "pdf_path": "paper/paper.pdf",
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
                    "planned_exports": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
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
                    "paper_role": "main_text",
                    "path": "paper/tables/T1_summary.md",
                }
            ],
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/draft.md",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "included_assets": [
                {"path": "paper/paper.pdf", "kind": "compiled_pdf", "status": "present"},
            ],
        },
    )
    return paper_root


def make_manuscript_shaped_draft_workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "paper"

    write_text(
        paper_root / "draft.md",
        """# Manuscript-Shaped Draft Title

## Abstract

### Background

Draft abstract background with evidence [@ref1].

### Methods

Draft abstract methods.

### Results

Draft abstract results.

### Conclusions

Draft abstract conclusions.

## Introduction

Intro paragraph with citation [@ref1].

## Materials and Methods

Study methods paragraph.

## Results

Results paragraph.

## Discussion

Discussion paragraph.
""",
    )
    write_text(
        paper_root / "references.bib",
        """@article{ref1,
  title={A primary source},
  author={Author, A. and Author, B.},
  journal={Journal},
  year={2024}
}
""",
    )
    write_png(paper_root / "figures" / "F1_main.png")
    write_text(paper_root / "figures" / "F1_main.pdf", "%PDF-1.4\n%main figure\n")
    write_text(paper_root / "tables" / "T1_summary.md", "| Characteristic | Value |\n| --- | --- |\n| Age | 52 |\n")
    write_text(paper_root / "paper.pdf", "%PDF-1.4\n%paper bundle\n")

    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "pdf_path": "paper/paper.pdf",
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
                    "planned_exports": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
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
                    "paper_role": "main_text",
                    "path": "paper/tables/T1_summary.md",
                }
            ],
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/draft.md",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "included_assets": [
                {"path": "paper/paper.pdf", "kind": "compiled_pdf", "status": "present"},
            ],
        },
    )
    return paper_root


def make_materialized_submission_source_workspace(tmp_path: Path) -> Path:
    paper_root = make_current_draft_workspace(tmp_path)
    write_png(paper_root / "submission_minimal" / "figures" / "F1.png")

    write_text(
        paper_root / "submission_minimal" / "manuscript_source.md",
        """# Materialized Submission Title

## Abstract

Materialized abstract with evidence [@ref1].

## Introduction

Materialized introduction with evidence [@ref1].

## Methods

Materialized methods paragraph.

## Results

Materialized results paragraph.

## Discussion

Materialized discussion paragraph.

## Conclusion

Materialized conclusion paragraph.

## Main-text figures

### F1. Main figure

![F1](figures/F1.png)

Materialized figure caption.
""",
    )
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "pdf_path": "paper/paper.pdf",
        },
    )
    return paper_root


def make_authoritative_worktree_source_workspace(tmp_path: Path) -> Path:
    seed_paper_root = make_paper_workspace(tmp_path / "seed")
    paper_root = tmp_path / "quest" / ".ds" / "worktrees" / "paper-run-123" / "paper"
    shutil.copytree(seed_paper_root, paper_root, dirs_exist_ok=True)

    write_png(paper_root / "figures" / "generated" / "F1.png")
    write_text(paper_root / "figures" / "generated" / "F1.pdf", "%PDF-1.4\n%authoritative figure\n")
    write_text(paper_root / "tables" / "generated" / "T1.csv", "Characteristic,Value\nAge,99\n")
    write_text(
        paper_root / "tables" / "generated" / "T1.md",
        "| Characteristic | Value |\n| --- | --- |\n| Age | 99 |\n",
    )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "title": "Authoritative figure",
                    "export_paths": [
                        "../../../paper/figures/generated/F1.pdf",
                        "../../../paper/figures/generated/F1.png",
                    ],
                    "planned_exports": [
                        "paper/figures/generated/F1.pdf",
                        "paper/figures/generated/F1.png",
                    ],
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
                    "paper_role": "main_text",
                    "title": "Authoritative table",
                    "asset_paths": [
                        "../../../paper/tables/generated/T1.csv",
                        "../../../paper/tables/generated/T1.md",
                    ],
                }
            ],
        },
    )
    return paper_root


