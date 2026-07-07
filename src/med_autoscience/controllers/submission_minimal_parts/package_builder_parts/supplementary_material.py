from collections.abc import Mapping
from pathlib import Path
import textwrap
from typing import Any

from ..shared_base import *


def supplementary_material_payload(
    *,
    supplementary_source_markdown_path: Path | None,
    supplementary_output_docx_path: Path | None,
    supplementary_output_pdf_path: Path | None,
    supplementary_tables_workbook_path: Path | None,
    supplementary_tables_pdf_path: Path | None,
    combined_review_docx_path: Path | None,
    combined_review_pdf_path: Path | None,
    profile_config: Any,
    staging_submission_root: Path,
    target_submission_root: Path,
    workspace_root: Path,
) -> dict[str, str] | None:
    if supplementary_source_markdown_path is None:
        return None
    if supplementary_output_docx_path is None and supplementary_output_pdf_path is None:
        return None

    def rel_remapped(path: Path) -> str:
        return relpath_from_workspace(
            remap_staging_path_to_target(
                path=path,
                staging_root=staging_submission_root,
                target_root=target_submission_root,
            ),
            workspace_root,
        )

    payload = {
        "source_markdown_path": relpath_from_workspace(
            remap_staging_path_to_target(
                path=supplementary_source_markdown_path,
                staging_root=staging_submission_root,
                target_root=target_submission_root,
            ),
            workspace_root,
        ),
    }
    if supplementary_output_docx_path is not None:
        payload["docx_path"] = rel_remapped(supplementary_output_docx_path)
    if supplementary_output_pdf_path is not None:
        payload["pdf_path"] = rel_remapped(supplementary_output_pdf_path)
    if supplementary_tables_workbook_path is not None:
        payload["tables_workbook_path"] = rel_remapped(supplementary_tables_workbook_path)
    if supplementary_tables_pdf_path is not None:
        payload["tables_pdf_path"] = rel_remapped(supplementary_tables_pdf_path)
    if combined_review_docx_path is not None:
        payload["combined_review_docx_path"] = rel_remapped(combined_review_docx_path)
    if combined_review_pdf_path is not None:
        payload["combined_review_pdf_path"] = rel_remapped(combined_review_pdf_path)
    if profile_config.supplementary_reference_doc_path is not None:
        payload["reference_doc_path"] = str(profile_config.supplementary_reference_doc_path.resolve())
    return payload


def is_supplementary_table(entry: Mapping[str, Any]) -> bool:
    return str(entry.get("paper_role") or "").strip().lower() == "supplementary"


def is_supplementary_figure(entry: Mapping[str, Any]) -> bool:
    return str(entry.get("paper_role") or "").strip().lower() == "supplementary"


def paper_relative_figure_path(*, source_path: Path, paper_root: Path) -> str:
    return f"paper/{source_path.resolve().relative_to(paper_root.resolve()).as_posix()}"


def resolve_deferred_figure_export_paths(
    *,
    entry: Mapping[str, Any],
    paper_root: Path,
) -> list[str]:
    figure_id = str(entry.get("figure_id") or "").strip()
    if not figure_id:
        return []

    render_request_path = paper_root / "build" / "display_pack_render_requests" / f"{figure_id}.render_request.json"
    if render_request_path.exists():
        render_request = load_json(render_request_path)
        request_paths: list[str] = []
        for key in ("output_svg_path", "output_png_path", "output_pdf_path"):
            value = render_request.get(key)
            if not isinstance(value, str) or not value.strip():
                continue
            candidate_path = Path(value).expanduser()
            if candidate_path.exists():
                request_paths.append(
                    paper_relative_figure_path(source_path=candidate_path, paper_root=paper_root)
                )
        if request_paths:
            return request_paths

    generated_dir = paper_root / "figures" / "generated"
    if not generated_dir.is_dir():
        return []

    fallback_paths: list[str] = []
    for suffix in (".svg", ".png", ".pdf"):
        for candidate_path in sorted(generated_dir.glob(f"{figure_id}_*{suffix}")):
            if candidate_path.is_file():
                fallback_paths.append(
                    paper_relative_figure_path(source_path=candidate_path, paper_root=paper_root)
                )
    return fallback_paths


def resolve_submission_figure_export_paths(
    *,
    entry: Mapping[str, Any],
    paper_root: Path,
) -> list[str]:
    export_paths = resolve_figure_source_paths(dict(entry))
    if export_paths:
        return export_paths
    return resolve_deferred_figure_export_paths(entry=entry, paper_root=paper_root)


def materialize_submission_figure_entry(
    *,
    entry: Mapping[str, Any],
    paper_root: Path,
    workspace_root: Path,
    label_root: Path,
    figures_output_dir: Path,
    pack_summary_by_id: Mapping[str, Any],
) -> dict[str, Any] | None:
    export_paths = resolve_submission_figure_export_paths(
        entry=entry,
        paper_root=paper_root,
    )
    if not export_paths:
        return None
    existing_export_paths = filter_existing_source_paths(
        workspace_root=workspace_root,
        paper_root=paper_root,
        source_paths=export_paths,
    )
    if existing_export_paths:
        export_paths = existing_export_paths
    missing_paths = find_missing_source_paths(
        workspace_root=workspace_root,
        paper_root=paper_root,
        source_paths=export_paths,
    )
    if missing_paths:
        if is_planned_catalog_entry(dict(entry)):
            return None
        missing_paths_text = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(
            f"missing submission asset(s) for figure `{entry.get('figure_id')}`: {missing_paths_text}"
        )
    basename = build_figure_basename(str(entry["figure_id"]))
    output_paths = copy_with_renamed_targets(
        workspace_root=workspace_root,
        paper_root=paper_root,
        source_paths=export_paths,
        output_dir=figures_output_dir,
        basename=basename,
        label_root=label_root,
    )
    pack_id = _resolve_pack_id(dict(entry), id_field="template_id")
    figure_entry = {
        "figure_id": entry["figure_id"],
        "template_id": entry.get("template_id"),
        "pack_id": pack_id,
        "renderer_family": entry.get("renderer_family"),
        "paper_role": entry.get("paper_role"),
        "display_role": entry.get("display_role"),
        "title": entry.get("title"),
        "caption": entry.get("caption"),
        "input_schema_id": entry.get("input_schema_id"),
        "qc_profile": entry.get("qc_profile"),
        "qc_result": entry.get("qc_result"),
        "source_paths": export_paths,
        "output_paths": output_paths,
    }
    _attach_pack_provenance(
        figure_entry,
        pack_id=pack_id,
        pack_summary_by_id=pack_summary_by_id,
    )
    return figure_entry


def build_supplementary_figures_markdown(
    *,
    figure_entries: list[dict[str, Any]],
    submission_root: Path,
    label_root: Path,
) -> Path | None:
    supplementary_entries = [entry for entry in figure_entries if is_supplementary_figure(entry)]
    if not supplementary_entries:
        return None

    lines = [
        "---",
        'title: "Supplementary Figures"',
        "bibliography: references.bib",
        "link-citations: true",
        "---",
        "",
        "# Supplementary Figures",
        "",
        "This file contains supplementary figures generated with the manuscript review package.",
        "",
    ]
    for index, entry in enumerate(supplementary_entries, start=1):
        title = str(entry.get("title") or "").strip()
        heading = f"## Supplementary Figure S{index}"
        if title:
            heading += f". {title}"
        lines.extend([heading, ""])
        caption = str(entry.get("caption") or "").strip()
        if caption:
            lines.extend([caption, ""])
        image_path = figure_markdown_image_path(
            entry=entry,
            label_root=label_root,
            submission_root=submission_root,
        )
        if image_path:
            lines.extend([f"![]({image_path}){{width=100%}}", ""])

    output_path = submission_root / "supplementary_figures.md"
    write_text(output_path, "\n".join(lines).rstrip() + "\n")
    return output_path


def build_supplementary_tables_markdown(
    *,
    table_entries: list[dict[str, Any]],
    submission_root: Path,
    label_root: Path,
) -> Path | None:
    supplementary_entries = [entry for entry in table_entries if is_supplementary_table(entry)]
    if not supplementary_entries:
        return None

    lines = [
        "---",
        'title: "Supplementary Tables"',
        "bibliography: references.bib",
        "link-citations: true",
        "---",
        "",
        "# Supplementary Tables",
        "",
        "This file contains supplementary tables generated with the manuscript review package.",
        "",
    ]
    for entry in supplementary_entries:
        table_id = str(entry.get("table_id") or "").strip()
        title = str(entry.get("title") or "").strip()
        label = supplementary_table_label(table_id)
        heading = f"## {label}"
        if title:
            heading += f". {title}"
        lines.extend([heading, ""])
        caption = str(entry.get("caption") or "").strip()
        if caption:
            lines.extend([caption, ""])
        markdown_path = markdown_output_path_for_table_entry(
            entry=entry,
            label_root=label_root,
        )
        if markdown_path is not None and markdown_path.exists():
            lines.extend([table_markdown_body(markdown_path.read_text(encoding="utf-8")), ""])

    output_path = submission_root / "supplementary_tables.md"
    write_text(output_path, "\n".join(lines).rstrip() + "\n")
    return output_path


def build_supplementary_tables_workbook(
    *,
    supplementary_tables_markdown_path: Path | None,
    submission_root: Path,
) -> Path | None:
    if supplementary_tables_markdown_path is None or not supplementary_tables_markdown_path.exists():
        return None

    sections = _supplementary_markdown_table_sections(
        markdown_without_front_matter(supplementary_tables_markdown_path.read_text(encoding="utf-8"))
    )
    if not sections:
        return None

    import xlsxwriter

    output_path = submission_root / "supplementary_tables.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(str(output_path))
    title_format = workbook.add_format({"bold": True, "text_wrap": True, "valign": "top"})
    header_format = workbook.add_format({"bold": True, "text_wrap": True, "valign": "top"})
    body_format = workbook.add_format({"text_wrap": True, "valign": "top"})
    used_sheet_names: set[str] = set()
    sheet_count = 0
    for fallback_index, section in enumerate(sections, start=1):
        title = section["title"] or f"Supplementary Table {fallback_index}"
        rows = section["rows"]
        if not rows:
            continue
        sheet_name = _unique_excel_sheet_name(
            _supplementary_table_sheet_name(title, fallback_index=fallback_index),
            used_sheet_names,
        )
        sheet = workbook.add_worksheet(sheet_name)
        sheet_count += 1
        max_columns = max(len(row) for row in rows)
        if max_columns:
            sheet.merge_range(0, 0, 0, max_columns - 1, title, title_format)
        for column_index in range(max_columns):
            values = [
                str(row[column_index] if column_index < len(row) else "")
                for row in rows
            ]
            max_width = min(max([len(value) for value in values] + [10]) + 2, 48)
            sheet.set_column(column_index, column_index, max_width)
        sheet.write_blank(1, 0, None)
        for row_index, row in enumerate(rows, start=2):
            row_format = header_format if row_index == 2 else body_format
            for column_index, value in enumerate(row):
                sheet.write(row_index, column_index, value, row_format)
        sheet.freeze_panes(3, 0)

    workbook.close()
    if sheet_count == 0:
        output_path.unlink(missing_ok=True)
        return None
    return output_path


def build_supplementary_tables_pdf(
    *,
    supplementary_tables_markdown_path: Path | None,
    submission_root: Path,
) -> Path | None:
    if supplementary_tables_markdown_path is None or not supplementary_tables_markdown_path.exists():
        return None

    sections = _supplementary_markdown_table_sections(
        markdown_without_front_matter(supplementary_tables_markdown_path.read_text(encoding="utf-8"))
    )
    if not sections:
        return None

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    output_path = submission_root / "supplementary_tables.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_count = 0
    with PdfPages(output_path) as pdf:
        for fallback_index, section in enumerate(sections, start=1):
            title = section["title"] or f"Supplementary Table {fallback_index}"
            rows = section["rows"]
            if not rows:
                continue
            chunks = _pdf_table_chunks(rows)
            for chunk_index, chunk_rows in enumerate(chunks, start=1):
                page_title = title if len(chunks) == 1 else f"{title} (continued {chunk_index}/{len(chunks)})"
                wrapped_rows = _wrap_table_rows_for_pdf(chunk_rows)
                column_widths = _pdf_table_column_widths(wrapped_rows)
                row_height_weights = _pdf_table_row_height_weights(wrapped_rows)
                row_height_total = sum(row_height_weights)
                figure_width = max(8.0, sum(column_widths) + 1.2)
                figure_height = max(5.0, 1.4 + 0.30 * row_height_total)
                figure, axis = plt.subplots(figsize=(figure_width, figure_height))
                axis.axis("off")
                axis.text(
                    0.0,
                    1.0,
                    page_title,
                    transform=axis.transAxes,
                    fontsize=11,
                    fontweight="bold",
                    va="top",
                )
                table = axis.table(
                    cellText=wrapped_rows[1:],
                    colLabels=wrapped_rows[0],
                    colWidths=[width / sum(column_widths) for width in column_widths],
                    loc="upper left",
                    bbox=[0.0, 0.0, 1.0, 0.93],
                    cellLoc="left",
                )
                table.auto_set_font_size(False)
                table.set_fontsize(7)
                table_bbox_height = 0.93
                for (row_index, _column_index), cell in table.get_celld().items():
                    cell.set_edgecolor("#bdbdbd")
                    cell.set_linewidth(0.3)
                    cell.set_text_props(ha="left", va="top", wrap=True)
                    if 0 <= row_index < len(row_height_weights):
                        cell.set_height(table_bbox_height * row_height_weights[row_index] / row_height_total)
                    if row_index == 0:
                        cell.set_facecolor("#f2f2f2")
                        cell.set_text_props(weight="bold")
                pdf.savefig(figure, bbox_inches="tight")
                plt.close(figure)
                page_count += 1
    if page_count == 0:
        output_path.unlink(missing_ok=True)
        return None
    return output_path


def build_combined_supplementary_markdown(
    *,
    supplementary_markdown_paths: list[Path],
    submission_root: Path,
    force_combined_output: bool = False,
) -> Path | None:
    paths = [path for path in supplementary_markdown_paths if path.exists()]
    if not paths:
        return None
    if len(paths) == 1 and not force_combined_output:
        return paths[0]
    body = "\n\n".join(markdown_without_front_matter(path.read_text(encoding="utf-8")) for path in paths)
    output_path = submission_root / "supplementary_material.md"
    write_text(
        output_path,
        "\n".join(
            [
                "---",
                'title: "Supplementary Material"',
                "bibliography: references.bib",
                "link-citations: true",
                "---",
                "",
                body.strip(),
                "",
            ]
        ),
    )
    return output_path


def build_combined_review_markdown(
    *,
    manuscript_markdown_path: Path,
    supplementary_markdown_path: Path,
    submission_root: Path,
    output_name: str = "manuscript_with_supplementary.md",
) -> Path:
    combined_text = (
        manuscript_markdown_path.read_text(encoding="utf-8").rstrip()
        + "\n\n# Supplementary Material\n\n"
        + markdown_without_front_matter(supplementary_markdown_path.read_text(encoding="utf-8"))
        + "\n"
    )
    output_path = submission_root / output_name
    write_text(output_path, combined_text)
    return output_path


def write_combined_review_pdf(
    *,
    manuscript_pdf_path: Path,
    supplementary_pdf_path: Path | None,
    output_pdf_path: Path,
) -> Path | None:
    if supplementary_pdf_path is None or not supplementary_pdf_path.exists():
        return None
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for source_path in (manuscript_pdf_path, supplementary_pdf_path):
        reader = PdfReader(str(source_path))
        for page in reader.pages:
            writer.add_page(page)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf_path.open("wb") as handle:
        writer.write(handle)
    return output_pdf_path


def supplementary_table_label(table_id: str) -> str:
    normalized = table_id.strip()
    if normalized.upper().startswith("S"):
        return f"Supplementary Table {normalized.upper()}"
    return f"Supplementary Table {normalized}"


def markdown_output_path_for_table_entry(
    *,
    entry: Mapping[str, Any],
    label_root: Path,
) -> Path | None:
    for output_path in entry.get("output_paths") or []:
        normalized = str(output_path or "").strip()
        if normalized and Path(normalized).suffix.lower() == ".md":
            return resolve_relpath(label_root, normalized)
    return None


def table_markdown_body(markdown_text: str) -> str:
    lines = markdown_text.strip().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    leading_control_lines: list[str] = []
    while lines and lines[0].strip() in {"\\newpage", "\\pagebreak"}:
        leading_control_lines.append(lines.pop(0))
        while lines and not lines[0].strip():
            lines.pop(0)
    if lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    elif leading_control_lines:
        lines = leading_control_lines + [""] + lines
    return "\n".join(lines).strip()


def markdown_without_front_matter(markdown_text: str) -> str:
    lines = markdown_text.strip().splitlines()
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "\n".join(lines[index + 1 :]).strip()
    return markdown_text.strip()


def _supplementary_markdown_table_sections(markdown_text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_title = ""
    pending_table_lines: list[str] = []
    for raw_line in markdown_text.splitlines() + [""]:
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if pending_table_lines:
                rows = _parse_markdown_table(pending_table_lines)
                if rows:
                    sections.append({"title": current_title, "rows": rows})
                pending_table_lines = []
            current_title = stripped.removeprefix("## ").strip()
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            pending_table_lines.append(stripped)
            continue
        if pending_table_lines:
            rows = _parse_markdown_table(pending_table_lines)
            if rows:
                sections.append({"title": current_title, "rows": rows})
            pending_table_lines = []
    return sections


def _parse_markdown_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(_is_markdown_separator_cell(cell) for cell in cells):
            continue
        if cells:
            rows.append(cells)
    return rows


def _wrap_table_rows_for_pdf(rows: list[list[str]]) -> list[list[str]]:
    max_columns = max(len(row) for row in rows)
    normalized_rows: list[list[str]] = []
    for row in rows:
        normalized = [str(value) for value in row] + [""] * (max_columns - len(row))
        normalized_rows.append([
            "\n".join(textwrap.wrap(value, width=28, break_long_words=False) or [""])
            for value in normalized
        ])
    return normalized_rows


def _pdf_table_chunks(rows: list[list[str]], *, max_body_rows: int = 35) -> list[list[list[str]]]:
    if len(rows) <= max_body_rows + 1:
        return [rows]
    header = rows[0]
    body = rows[1:]
    return [
        [header] + body[index : index + max_body_rows]
        for index in range(0, len(body), max_body_rows)
    ]


def _pdf_table_column_widths(rows: list[list[str]]) -> list[float]:
    column_count = max(len(row) for row in rows)
    widths: list[float] = []
    for column_index in range(column_count):
        values = [row[column_index] if column_index < len(row) else "" for row in rows]
        longest_line = max(
            [len(line) for value in values for line in str(value).splitlines()] + [8]
        )
        widths.append(min(max(0.9, longest_line * 0.09), 3.2))
    return widths


def _pdf_table_row_height_weights(rows: list[list[str]]) -> list[float]:
    weights: list[float] = []
    for row in rows:
        line_count = max([len(str(value).splitlines()) for value in row] + [1])
        weights.append(max(1.0, 1.0 + line_count))
    return weights


def _is_markdown_separator_cell(cell: str) -> bool:
    normalized = cell.replace(":", "").replace("-", "").strip()
    return normalized == ""


def _supplementary_table_sheet_name(title: str, *, fallback_index: int) -> str:
    match = re.search(r"\bSupplementary\s+Table\s+([A-Za-z]?\d+[A-Za-z]?)\b", title, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return f"S{fallback_index}"


def _unique_excel_sheet_name(base_name: str, used_sheet_names: set[str]) -> str:
    clean_name = re.sub(r"[\[\]:*?/\\]", "_", base_name).strip() or "Table"
    candidate = clean_name[:31]
    suffix = 1
    while candidate in used_sheet_names:
        tail = f"_{suffix}"
        candidate = f"{clean_name[:31 - len(tail)]}{tail}"
        suffix += 1
    used_sheet_names.add(candidate)
    return candidate


def figure_markdown_image_path(
    *,
    entry: Mapping[str, Any],
    label_root: Path,
    submission_root: Path,
) -> str:
    preferred_suffixes = (".png", ".jpg", ".jpeg", ".webp", ".pdf", ".svg")
    output_paths = [str(path or "").strip() for path in entry.get("output_paths") or [] if str(path or "").strip()]
    for suffix in preferred_suffixes:
        for raw_path in output_paths:
            if not raw_path.lower().endswith(suffix):
                continue
            resolved = resolve_relpath(label_root, raw_path)
            if not resolved.exists():
                continue
            try:
                return resolved.resolve().relative_to(submission_root.resolve()).as_posix()
            except ValueError:
                return relpath_from_workspace(resolved, label_root)
    return ""
