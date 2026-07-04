from .shared_base import *
from .markdown_surface_blocks import (
    normalize_markdown_heading_key,
    parse_second_level_blocks,
    parse_third_level_blocks,
    parse_top_level_blocks,
)


def _natural_table_sort_key(value: str) -> tuple[int, int, str]:
    normalized = str(value or "").strip()
    main_match = re.match(r"^(?:Table\s*|T)(\d+)$", normalized, flags=re.IGNORECASE)
    if main_match:
        return (0, int(main_match.group(1)), normalized)
    return (1, 0, normalized.casefold())


def parse_table_id_from_heading(heading: str) -> str | None:
    normalized = str(heading or "").strip()
    main_match = re.match(r"^Table\s*(\d+)\b", normalized, flags=re.IGNORECASE)
    if main_match:
        return f"T{main_match.group(1)}"
    main_short_match = re.match(r"^T(\d+)\b", normalized, flags=re.IGNORECASE)
    if main_short_match:
        return f"T{main_short_match.group(1)}"
    return None


def _heading_is_table(heading: str) -> bool:
    return bool(re.match(r"^(?:Table\s*|T)\d+\b", str(heading or "").strip(), flags=re.IGNORECASE))


def _split_pipe_table_row(line: str) -> list[str]:
    stripped = str(line or "").strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _is_pipe_table_separator(line: str) -> bool:
    cells = _split_pipe_table_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def normalize_wide_pipe_table_widths(block_body: str) -> str:
    lines = str(block_body or "").splitlines()
    for index in range(len(lines) - 1):
        headers = _split_pipe_table_row(lines[index])
        if len(headers) < 6 or not _is_pipe_table_separator(lines[index + 1]):
            continue
        widths = [max(3, min(34, len(header.strip()))) for header in headers]
        if widths:
            widths[0] = max(widths[0], 24)
        lines[index + 1] = "| " + " | ".join("-" * width for width in widths) + " |"
        break
    return "\n".join(lines).strip()


def _latex_escape_cell(value: str) -> str:
    text = str(value or "")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _parse_pipe_table(block_body: str) -> tuple[list[str], list[list[str]], list[str]]:
    lines = str(block_body or "").splitlines()
    for index in range(len(lines) - 1):
        headers = _split_pipe_table_row(lines[index])
        if not headers or not _is_pipe_table_separator(lines[index + 1]):
            continue
        rows: list[list[str]] = []
        trailing_lines: list[str] = []
        for line in lines[index + 2:]:
            cells = _split_pipe_table_row(line)
            if cells:
                rows.append(cells)
            else:
                trailing_lines.append(line)
        return headers, rows, trailing_lines
    return [], [], lines


def _wide_pipe_table_to_latex(block_body: str, *, caption: str) -> str | None:
    headers, rows, trailing_lines = _parse_pipe_table(block_body)
    if len(headers) < 8 or not rows:
        return None
    column_spec = "p{0.20\\linewidth}" + " ".join("p{0.085\\linewidth}" for _ in headers[1:])
    latex_lines = [
        r"\begin{landscape}",
        r"\begin{table}[p]",
        r"\centering",
        rf"\caption*{{{_latex_escape_cell(caption)}}}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2pt}",
        r"\renewcommand{\arraystretch}{1.15}",
        rf"\begin{{tabular}}{{{column_spec}}}",
        r"\toprule",
        " & ".join(_latex_escape_cell(header) for header in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        padded_row = [*row[: len(headers)], *([""] * max(0, len(headers) - len(row)))]
        latex_lines.append(" & ".join(_latex_escape_cell(cell) for cell in padded_row[: len(headers)]) + r" \\")
    latex_lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", r"\end{landscape}"])
    trailing = "\n".join(line for line in trailing_lines if line.strip()).strip()
    if trailing:
        latex_lines.extend(["", trailing])
    return "\n".join(latex_lines).strip()


def normalize_submission_table_body(block_body: str, *, heading: str) -> str:
    latex_table = _wide_pipe_table_to_latex(block_body, caption=heading)
    if latex_table is not None:
        return latex_table
    return normalize_wide_pipe_table_widths(block_body)


def _select_catalog_table_markdown_source(entry: dict[str, Any], *, allow_default: bool = False) -> str:
    source_paths = resolve_table_source_paths(entry)
    markdown_paths = [
        str(item).strip()
        for item in source_paths
        if str(item).strip().lower().endswith(".md")
    ]
    if not markdown_paths:
        return ""
    render_result = entry.get("render_result") if isinstance(entry.get("render_result"), dict) else {}
    layout_policy = str(render_result.get("table_layout_policy") or "").strip()
    if layout_policy == "long_measure_value_table_to_avoid_pdf_header_overlap":
        return markdown_paths[0]
    if entry.get("prefer_markdown_for_submission_pdf") is True:
        return markdown_paths[0]
    if allow_default:
        return markdown_paths[0]
    return ""


def _strip_catalog_table_markdown_heading(markdown_text: str) -> str:
    lines = str(markdown_text or "").strip().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^#{1,6}\s+\S", lines[0].strip()):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def build_catalog_backed_table_blocks(*, paper_root: Path, source_tables: str) -> dict[str, tuple[str, str]]:
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    if not table_catalog_path.exists():
        return {}
    payload = load_json(table_catalog_path)
    tables = payload.get("tables") if isinstance(payload, dict) else None
    if not isinstance(tables, list):
        return {}

    workspace_root = paper_root.parent
    source_blocks = {
        parse_table_id_from_heading(heading): heading
        for heading, block_body in _extract_table_blocks(source_tables)
        if parse_table_id_from_heading(heading)
    }
    catalog_blocks: dict[str, tuple[str, str]] = {}
    for entry in tables:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("paper_role") or "").strip().lower() != "main_text":
            continue
        table_id = str(entry.get("table_id") or "").strip()
        markdown_source_rel = _select_catalog_table_markdown_source(
            entry,
            allow_default=not source_tables.strip(),
        )
        if not table_id or not markdown_source_rel:
            continue
        markdown_source_path = resolve_relpath(workspace_root, markdown_source_rel)
        if not markdown_source_path.exists():
            continue
        heading = source_blocks.get(table_id) or _build_catalog_table_heading(
            table_id=table_id,
            title=str(entry.get("title") or ""),
        )
        catalog_blocks[table_id] = (
            heading,
            _strip_catalog_table_markdown_heading(markdown_source_path.read_text(encoding="utf-8")),
        )
    return catalog_blocks


def _build_catalog_table_heading(*, table_id: str, title: str) -> str:
    normalized_id = str(table_id or "").strip()
    normalized_title = str(title or "").strip()
    match = re.match(r"^T(\d+)$", normalized_id, flags=re.IGNORECASE)
    if match:
        heading = f"Table {match.group(1)}"
        if normalized_title:
            return f"{heading}. {normalized_title}"
        return heading
    if normalized_title:
        return normalized_title
    return normalized_id


def _extract_table_blocks(main_tables: str) -> list[tuple[str, str]]:
    parsed_blocks = [
        (heading, body)
        for heading, body in parse_third_level_blocks(main_tables)
        if _heading_is_table(heading)
    ]
    if parsed_blocks:
        return parsed_blocks
    parsed_blocks = [
        (heading, body)
        for heading, body in parse_second_level_blocks(main_tables)
        if _heading_is_table(heading)
    ]
    if parsed_blocks:
        return parsed_blocks
    return [
        (heading, body)
        for heading, body in parse_top_level_blocks(main_tables)
        if _heading_is_table(heading)
    ]
