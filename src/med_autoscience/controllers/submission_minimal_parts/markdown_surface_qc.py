from __future__ import annotations

from .shared import *


def parse_independent_figure_legend_map(figure_legends_section: str) -> dict[str, str]:
    from .markdown_surface import parse_figure_blocks, parse_figure_id_from_heading, strip_image_lines

    legend_by_figure_id: dict[str, str] = {}
    for heading, block_body in parse_figure_blocks(figure_legends_section):
        figure_id = parse_figure_id_from_heading(heading)
        legend = strip_image_lines(block_body).strip()
        if figure_id and legend:
            legend_by_figure_id[figure_id] = legend

    for paragraph in re.split(r"\n\s*\n", figure_legends_section.strip()):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        first_line = lines[0].lstrip("#").strip()
        figure_id = parse_figure_id_from_heading(first_line)
        if figure_id and figure_id not in legend_by_figure_id:
            legend_by_figure_id[figure_id] = "\n".join(lines)
    return legend_by_figure_id


def inspect_submission_source_markdown(source_markdown_path: Path) -> dict[str, Any]:
    from .markdown_surface import (
        collect_duplicate_manuscript_major_sections,
        collect_internal_instruction_hits,
        extract_image_lines,
        extract_top_level_markdown_block,
        parse_figure_blocks,
        parse_figure_id_from_heading,
        strip_image_lines,
    )

    if not source_markdown_path.exists():
        return {
            "exists": False,
            "figure_block_count": 0,
            "figure_blocks_with_images": 0,
            "figure_blocks_with_legends": 0,
            "duplicate_major_sections": [],
            "internal_instruction_hits": [],
        }
    markdown_text = source_markdown_path.read_text(encoding="utf-8")
    _, body = split_front_matter(markdown_text)
    figures_section = extract_top_level_markdown_block(
        body,
        "Main Figures",
        "Figures",
        "Main-text figures",
    )
    figure_legends_section = extract_top_level_markdown_block(body, "Figure Legends", "Figure Legend")
    independent_legend_by_figure_id = parse_independent_figure_legend_map(figure_legends_section)
    figure_blocks = parse_figure_blocks(figures_section) if figures_section.strip() else []
    figure_blocks_with_images = 0
    figure_blocks_with_legends = 0
    for heading, block_body in figure_blocks:
        figure_id = parse_figure_id_from_heading(heading)
        if extract_image_lines(block_body):
            figure_blocks_with_images += 1
        if strip_image_lines(block_body).strip() or (figure_id and independent_legend_by_figure_id.get(figure_id)):
            figure_blocks_with_legends += 1
    return {
        "exists": True,
        "mtime_ns": source_markdown_path.stat().st_mtime_ns,
        "figure_block_count": len(figure_blocks),
        "figure_blocks_with_images": figure_blocks_with_images,
        "figure_blocks_with_legends": figure_blocks_with_legends,
        "duplicate_major_sections": collect_duplicate_manuscript_major_sections(markdown_text),
        "internal_instruction_hits": collect_internal_instruction_hits(markdown_text),
    }


def inspect_submission_docx_surface(docx_path: Path) -> dict[str, Any]:
    if not docx_path.exists() or docx_path.is_dir():
        return {
            "exists": False,
            "embedded_image_count": 0,
            "drawing_count": 0,
        }
    try:
        with zipfile.ZipFile(docx_path) as archive:
            names = archive.namelist()
            document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except (KeyError, zipfile.BadZipFile):
        return {
            "exists": True,
            "mtime_ns": docx_path.stat().st_mtime_ns,
            "embedded_image_count": 0,
            "drawing_count": 0,
            "unreadable": True,
        }
    return {
        "exists": True,
        "mtime_ns": docx_path.stat().st_mtime_ns,
        "embedded_image_count": len([name for name in names if name.startswith("word/media/")]),
        "drawing_count": document_xml.count("<w:drawing"),
        "unreadable": False,
    }


def inspect_submission_pdf_surface(pdf_path: Path) -> dict[str, Any]:
    if not pdf_path.exists():
        return {
            "exists": False,
            "embedded_image_count": 0,
            "page_count": 0,
        }
    try:
        reader = PdfReader(str(pdf_path))
        embedded_image_count = sum(len(page.images) for page in reader.pages)
    except Exception:
        return {
            "exists": True,
            "mtime_ns": pdf_path.stat().st_mtime_ns,
            "embedded_image_count": 0,
            "page_count": 0,
            "unreadable": True,
        }
    return {
        "exists": True,
        "mtime_ns": pdf_path.stat().st_mtime_ns,
        "embedded_image_count": embedded_image_count,
        "page_count": len(reader.pages),
        "unreadable": False,
    }


def _submission_manuscript_freshness_failures(
    *,
    source_stats: dict[str, Any],
    docx_stats: dict[str, Any],
    pdf_stats: dict[str, Any],
) -> tuple[bool, bool]:
    source_mtime_ns = int(source_stats.get("mtime_ns") or 0)
    docx_older_than_source_markdown = bool(
        source_stats["exists"]
        and docx_stats["exists"]
        and source_mtime_ns > int(docx_stats.get("mtime_ns") or 0)
    )
    pdf_older_than_source_markdown = bool(
        source_stats["exists"]
        and pdf_stats["exists"]
        and source_mtime_ns > int(pdf_stats.get("mtime_ns") or 0)
    )
    return docx_older_than_source_markdown, pdf_older_than_source_markdown


def _failure_payload(
    *,
    item_id: str,
    descriptor: str,
    failure_reason: str,
    audit_classes: list[str],
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "collection": "manuscript",
        "item_id": item_id,
        "descriptor": descriptor,
        "qc_profile": "submission_manuscript_surface",
        "failure_reason": failure_reason,
        "audit_classes": audit_classes,
    }
    payload.update(extra)
    return payload


def _append_source_markdown_failures(
    failures: list[dict[str, Any]],
    *,
    source_stats: dict[str, Any],
    source_markdown_path: Path,
    expected_main_figure_count: int,
) -> None:
    if not source_stats["exists"]:
        failures.append(
            _failure_payload(
                item_id="source_markdown",
                descriptor=source_markdown_path.name,
                failure_reason="submission_source_markdown_missing",
                audit_classes=["manuscript_surface"],
            )
        )
        return
    if source_stats["figure_blocks_with_images"] < expected_main_figure_count:
        failures.append(
            _failure_payload(
                item_id="source_markdown",
                descriptor=source_markdown_path.name,
                failure_reason="submission_source_markdown_missing_inline_figures",
                audit_classes=["manuscript_surface"],
            )
        )
    if source_stats["figure_blocks_with_legends"] < expected_main_figure_count:
        failures.append(
            _failure_payload(
                item_id="source_markdown",
                descriptor=source_markdown_path.name,
                failure_reason="submission_source_markdown_missing_figure_legends",
                audit_classes=["manuscript_surface"],
            )
        )
    _append_source_hygiene_failures(failures, source_stats=source_stats, source_markdown_path=source_markdown_path)


def _append_source_hygiene_failures(
    failures: list[dict[str, Any]],
    *,
    source_stats: dict[str, Any],
    source_markdown_path: Path,
) -> None:
    if source_stats["duplicate_major_sections"]:
        failures.append(
            _failure_payload(
                item_id="source_markdown",
                descriptor=source_markdown_path.name,
                failure_reason="submission_source_markdown_duplicate_sections",
                audit_classes=["manuscript_surface", "hygiene"],
                duplicate_major_sections=source_stats["duplicate_major_sections"],
            )
        )
    if source_stats["internal_instruction_hits"]:
        failures.append(
            _failure_payload(
                item_id="source_markdown",
                descriptor=source_markdown_path.name,
                failure_reason="submission_source_markdown_internal_instruction_leakage",
                audit_classes=["manuscript_surface", "hygiene"],
                internal_instruction_hits=source_stats["internal_instruction_hits"],
            )
        )


def _append_rendered_surface_failures(
    failures: list[dict[str, Any]],
    *,
    docx_path: Path,
    pdf_path: Path,
    docx_stats: dict[str, Any],
    pdf_stats: dict[str, Any],
    expected_main_figure_count: int,
    docx_older_than_source_markdown: bool,
    pdf_older_than_source_markdown: bool,
) -> None:
    if docx_stats["embedded_image_count"] < expected_main_figure_count:
        failures.append(
            _failure_payload(
                item_id="docx",
                descriptor=docx_path.name,
                failure_reason="submission_docx_missing_embedded_figures",
                audit_classes=["manuscript_surface"],
            )
        )
    if docx_older_than_source_markdown:
        failures.append(
            _failure_payload(
                item_id="docx",
                descriptor=docx_path.name,
                failure_reason="submission_docx_older_than_source_markdown",
                audit_classes=["manuscript_surface", "freshness"],
            )
        )
    if pdf_stats["embedded_image_count"] < expected_main_figure_count:
        failures.append(
            _failure_payload(
                item_id="pdf",
                descriptor=pdf_path.name,
                failure_reason="submission_pdf_missing_embedded_figures",
                audit_classes=["manuscript_surface"],
            )
        )
    if pdf_older_than_source_markdown:
        failures.append(
            _failure_payload(
                item_id="pdf",
                descriptor=pdf_path.name,
                failure_reason="submission_pdf_older_than_source_markdown",
                audit_classes=["manuscript_surface", "freshness"],
            )
        )


def build_submission_manuscript_surface_qc(
    *,
    publication_profile: str,
    source_markdown_path: Path,
    docx_path: Path,
    pdf_path: Path,
    expected_main_figure_count: int,
) -> dict[str, Any]:
    qc_profile = "submission_manuscript_surface"
    if publication_profile != GENERAL_MEDICAL_JOURNAL_PROFILE:
        return {
            "qc_profile": qc_profile,
            "status": "not_applicable",
            "expected_main_figure_count": expected_main_figure_count,
            "failures": [],
        }

    source_stats = inspect_submission_source_markdown(source_markdown_path)
    docx_stats = inspect_submission_docx_surface(docx_path)
    pdf_stats = inspect_submission_pdf_surface(pdf_path)
    docx_stale, pdf_stale = _submission_manuscript_freshness_failures(
        source_stats=source_stats,
        docx_stats=docx_stats,
        pdf_stats=pdf_stats,
    )
    docx_stats["older_than_source_markdown"] = docx_stale
    pdf_stats["older_than_source_markdown"] = pdf_stale

    failures: list[dict[str, Any]] = []
    _append_source_markdown_failures(
        failures,
        source_stats=source_stats,
        source_markdown_path=source_markdown_path,
        expected_main_figure_count=expected_main_figure_count,
    )
    _append_rendered_surface_failures(
        failures,
        docx_path=docx_path,
        pdf_path=pdf_path,
        docx_stats=docx_stats,
        pdf_stats=pdf_stats,
        expected_main_figure_count=expected_main_figure_count,
        docx_older_than_source_markdown=docx_stale,
        pdf_older_than_source_markdown=pdf_stale,
    )
    return {
        "qc_profile": qc_profile,
        "status": "pass" if not failures else "fail",
        "expected_main_figure_count": expected_main_figure_count,
        "source_markdown": source_stats,
        "docx": docx_stats,
        "pdf": pdf_stats,
        "failures": failures,
    }


__all__ = [
    "parse_independent_figure_legend_map",
    "inspect_submission_source_markdown",
    "inspect_submission_docx_surface",
    "inspect_submission_pdf_surface",
    "build_submission_manuscript_surface_qc",
]
