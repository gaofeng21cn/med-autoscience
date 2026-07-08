from __future__ import annotations

import os
import subprocess
from pathlib import Path


PDF_RENDERING_PROFILE_ID = "general_medical_reader_pdf_v1"
PDF_RENDERING_TEMPLATE_FAMILY = "mas_professional_medical_article"
PDF_RENDERING_ENGINE = "pandoc_xelatex"
PDF_ENGINE = "xelatex"
PDF_RENDER_VARIABLES = (
    "documentclass=article",
    "papersize=a4",
    "geometry:margin=0.82in",
    "fontsize=11pt",
    "linestretch=1.06",
)
SUBMISSION_PDF_LAYOUT_HEADER = r"""
\usepackage[T1]{fontenc}
\usepackage{newtxtext}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{array}
\usepackage{float}
\usepackage{placeins}
\usepackage{pdflscape}
\usepackage{caption}
\usepackage{etoolbox}
\usepackage{titlesec}
\usepackage{fancyhdr}
\definecolor{MASAccent}{HTML}{145C68}
\definecolor{MASText}{HTML}{202124}
\definecolor{MASMuted}{HTML}{5F6B72}
\AtBeginDocument{\color{MASText}}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\small\textcolor{MASMuted}{\thepage}}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\setlength{\headheight}{14pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.55em}
\setlength{\emergencystretch}{3em}
\raggedbottom
\titleformat{\section}{\Large\bfseries\color{MASAccent}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\large\bfseries\color{MASText}}{\thesubsection}{0.5em}{}
\titleformat{\subsubsection}{\normalsize\bfseries\color{MASText}}{\thesubsubsection}{0.45em}{}
\titlespacing*{\section}{0pt}{1.25em}{0.55em}
\titlespacing*{\subsection}{0pt}{1.1em}{0.45em}
\titlespacing*{\subsubsection}{0pt}{0.8em}{0.35em}
\captionsetup{font=small,labelfont=bf,justification=raggedright,singlelinecheck=false}
\renewcommand{\arraystretch}{1.16}
\floatplacement{figure}{H}
\AtBeginEnvironment{figure}{\FloatBarrier}
\AtEndEnvironment{figure}{\FloatBarrier}
\AtBeginEnvironment{longtable}{\small\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.16}}
"""


def default_pdf_rendering_profile() -> dict[str, object]:
    return {
        "profile_id": PDF_RENDERING_PROFILE_ID,
        "renderer_family": PDF_RENDERING_ENGINE,
        "pdf_engine": PDF_ENGINE,
        "template_family": PDF_RENDERING_TEMPLATE_FAMILY,
        "layout_role": "human_reading_default",
        "journal_specific": False,
    }


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
    command = [
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
    ]
    for variable in PDF_RENDER_VARIABLES:
        command.extend(["--variable", variable])
    command.extend(
        [
            f"--pdf-engine={PDF_ENGINE}",
            "-o",
            os.path.relpath(output_pdf_path.resolve(), compiled_markdown_path.parent.resolve()),
        ]
    )
    subprocess.run(
        command,
        cwd=compiled_markdown_path.parent,
        check=True,
    )
