from __future__ import annotations

import os
import subprocess
from pathlib import Path


SUBMISSION_PDF_LAYOUT_HEADER = r"""
\usepackage{float}
\usepackage{placeins}
\usepackage{pdflscape}
\usepackage{caption}
\usepackage{etoolbox}
\floatplacement{figure}{H}
\AtBeginEnvironment{figure}{\FloatBarrier}
\AtEndEnvironment{figure}{\FloatBarrier}
\AtBeginEnvironment{longtable}{\footnotesize\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.12}}
"""


def export_docx(
    *,
    compiled_markdown_path: Path,
    paper_root: Path,
    output_docx_path: Path,
    csl_path: Path,
    reference_doc_path: Path | None = None,
) -> None:
    output_docx_path.parent.mkdir(parents=True, exist_ok=True)
    resource_candidates = [
        ".",
        os.path.relpath(paper_root.resolve(), compiled_markdown_path.parent.resolve()),
    ]
    resource_path = os.pathsep.join(dict.fromkeys(resource_candidates))
    command = [
        "pandoc",
        compiled_markdown_path.name,
        "--standalone",
        "--citeproc",
        "--csl",
        str(csl_path.resolve()),
        "--resource-path",
        resource_path,
    ]
    if reference_doc_path is not None:
        command.extend(["--reference-doc", str(reference_doc_path.resolve())])
    command.extend(
        [
            "-o",
            os.path.relpath(output_docx_path.resolve(), compiled_markdown_path.parent.resolve()),
        ]
    )
    subprocess.run(
        command,
        cwd=compiled_markdown_path.parent,
        check=True,
    )


def export_pdf(
    *,
    compiled_markdown_path: Path,
    paper_root: Path,
    output_pdf_path: Path,
    csl_path: Path,
) -> None:
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    header_path = compiled_markdown_path.parent / "submission_pdf_layout.tex"
    header_path.write_text(SUBMISSION_PDF_LAYOUT_HEADER.strip() + "\n", encoding="utf-8")
    resource_candidates = [
        ".",
        os.path.relpath(paper_root.resolve(), compiled_markdown_path.parent.resolve()),
    ]
    resource_path = os.pathsep.join(dict.fromkeys(resource_candidates))
    subprocess.run(
        [
            "pandoc",
            compiled_markdown_path.name,
            "--standalone",
            "--citeproc",
            "--csl",
            str(csl_path.resolve()),
            "--resource-path",
            resource_path,
            "--include-in-header",
            header_path.name,
            "--variable",
            "tables=true",
            "--variable",
            "longtable=true",
            "--pdf-engine=xelatex",
            "-o",
            os.path.relpath(output_pdf_path.resolve(), compiled_markdown_path.parent.resolve()),
        ],
        cwd=compiled_markdown_path.parent,
        check=True,
    )
