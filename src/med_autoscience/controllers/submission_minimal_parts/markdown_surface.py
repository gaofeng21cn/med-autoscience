from .shared import *

def extract_block_between_markers(
    text: str,
    *,
    start_marker: str,
    end_markers: list[str],
    label: str,
) -> str:
    start_index = text.find(start_marker)
    if start_index == -1:
        raise ValueError(f"missing section `{label}` in compiled manuscript")
    content_start = start_index + len(start_marker)
    content_end = len(text)
    for marker in end_markers:
        marker_index = text.find(marker, content_start)
        if marker_index != -1:
            content_end = min(content_end, marker_index)
    return text[content_start:content_end].strip()


def extract_markdown_block(body: str, start_heading: str, end_headings: list[str]) -> str:
    return extract_block_between_markers(
        body,
        start_marker=f"# {start_heading}\n",
        end_markers=[f"\n# {heading}\n" for heading in end_headings],
        label=start_heading,
    )


def extract_optional_block_between_markers(
    text: str,
    *,
    start_marker: str,
    end_markers: list[str],
    label: str,
) -> str:
    try:
        return extract_block_between_markers(
            text,
            start_marker=start_marker,
            end_markers=end_markers,
            label=label,
        )
    except ValueError:
        return ""


def extract_optional_markdown_block(body: str, start_heading: str, end_headings: list[str]) -> str:
    try:
        return extract_markdown_block(body, start_heading, end_headings)
    except ValueError:
        return ""


def build_frontiers_required_sections() -> str:
    return (
        "# Data Availability Statement\n\n"
        "Patient-level clinical data were analyzed in this study. Because the source dataset was derived from hospital "
        "records, public deposition is subject to institutional and privacy approval. "
        "Author-approved data-availability wording remains an administrative closeout item before formal submission.\n\n"
        "# Ethics Statement\n\n"
        "This study was approved by the Clinical Research Ethics Committee of the First Affiliated Hospital of "
        "Sun Yat-sen University (approval `[2024]576`). "
        "Consent or waiver statement pending author confirmation before formal submission.\n\n"
        "# Author Contributions\n\n"
        "Author contributions pending author confirmation before formal submission.\n\n"
        "# Funding\n\n"
        "Funding statement pending author confirmation before formal submission.\n\n"
        "# Acknowledgments\n\n"
        "Acknowledgments pending author confirmation before formal submission, if applicable.\n\n"
        "# Conflict of Interest\n\n"
        "Conflict-of-interest statement pending author confirmation before formal submission.\n"
    )


def parse_heading_blocks(text: str, heading_prefix: str) -> list[tuple[str, str]]:
    pattern = re.compile(rf"(?ms)^## ({re.escape(heading_prefix)}[^\n]*)\n\n(.*?)(?=^# |^## |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def parse_top_level_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^# ([^\n]+)\n\n(.*?)(?=^# |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def normalize_markdown_heading_key(heading: str) -> str:
    return re.sub(r"\s+", " ", str(heading or "").strip()).casefold()


MANUSCRIPT_MAJOR_SECTION_ALIASES = {
    "abstract": {"abstract"},
    "introduction": {"introduction"},
    "methods": {
        "methods",
        "materials and methods",
        "patients and methods",
        "methods and materials",
    },
    "results": {"results"},
    "discussion": {"discussion"},
    "conclusion": {"conclusion", "conclusions"},
    "appendix": {"appendix"},
    "figures": {"figures", "main figures", "main-text figures"},
    "figure_legends": {"figure legends", "figure legend"},
    "tables": {"tables", "main tables"},
}
MANUSCRIPT_MAJOR_SECTION_LOOKUP = {
    alias: section
    for section, aliases in MANUSCRIPT_MAJOR_SECTION_ALIASES.items()
    for alias in aliases
}
MANUSCRIPT_MAJOR_HEADING_PATTERN = re.compile(r"(?m)^(#{1,2})\s+([^\n]+?)\s*$")
INTERNAL_MANUSCRIPT_INSTRUCTION_PATTERNS = (
    (
        "manuscript_directive",
        re.compile(r"\b(?:the|this)\s+manuscript\s+(?:should|must|can)\b", flags=re.IGNORECASE),
    ),
    (
        "paper_directive",
        re.compile(r"\bthe\s+paper\s+(?:should|must|can)\b", flags=re.IGNORECASE),
    ),
    (
        "imperative_use_as",
        re.compile(r"(?:^|[.;]\s+)use\s+as\b", flags=re.IGNORECASE),
    ),
    (
        "imperative_reframe_guard",
        re.compile(r"(?:^|[.;]\s+)do\s+not\s+(?:recast|reframe|promote|soften)\b", flags=re.IGNORECASE),
    ),
    (
        "figure_must_not_directive",
        re.compile(
            r"\b(?:this\s+figure|the\s+figure|figure\s+\d+[^\n.;]*)\b[^\n.;]*\bmust\s+not\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "must_not_reframe_directive",
        re.compile(
            r"\bmust\s+not\s+be\s+(?:reframed|recast|softened|promoted)\b",
            flags=re.IGNORECASE,
        ),
    ),
)


def canonicalize_manuscript_major_heading(heading: str) -> str:
    normalized = normalize_markdown_heading_key(heading)
    if not normalized:
        return ""
    prefix = re.split(r"[:.]", normalized, maxsplit=1)[0].strip()
    return MANUSCRIPT_MAJOR_SECTION_LOOKUP.get(prefix, "")


def collect_duplicate_manuscript_major_sections(markdown_text: str) -> list[dict[str, Any]]:
    occurrences_by_section: dict[str, list[dict[str, Any]]] = {}
    for match in MANUSCRIPT_MAJOR_HEADING_PATTERN.finditer(markdown_text):
        section_key = canonicalize_manuscript_major_heading(match.group(2))
        if not section_key:
            continue
        line_number = markdown_text.count("\n", 0, match.start()) + 1
        occurrences_by_section.setdefault(section_key, []).append(
            {
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "line": line_number,
            }
        )
    return [
        {
            "section": section_key,
            "count": len(occurrences),
            "occurrences": occurrences,
        }
        for section_key, occurrences in occurrences_by_section.items()
        if len(occurrences) > 1
    ]


def collect_internal_instruction_hits(markdown_text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        stripped_line = line.strip()
        if not stripped_line:
            continue
        for marker, pattern in INTERNAL_MANUSCRIPT_INSTRUCTION_PATTERNS:
            if not pattern.search(stripped_line):
                continue
            key = (line_number, marker)
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                {
                    "line": line_number,
                    "marker": marker,
                    "text": stripped_line[:240],
                }
            )
    return hits


def contains_internal_instruction_text(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return False
    if collect_internal_instruction_hits(stripped):
        return True
    return bool(re.search(r"\b(?:should|must)\s+not\b|^do\s+not\b", stripped, flags=re.IGNORECASE))


MANUSCRIPT_SHAPED_AUXILIARY_TOP_LEVEL_HEADINGS = (
    "Main Tables",
    "Tables",
    "Main Figures",
    "Figures",
    "Main-text figures",
    "Figure Legends",
    "Figure Legend",
    "Appendix",
)


def collect_named_top_level_blocks(text: str, *headings: str) -> dict[str, str]:
    heading_keys = {normalize_markdown_heading_key(heading) for heading in headings}
    blocks: dict[str, str] = {}
    for heading, block_body in parse_top_level_blocks(text):
        key = normalize_markdown_heading_key(heading)
        if key in heading_keys and block_body.strip() and key not in blocks:
            blocks[key] = block_body.strip()
    return blocks


def extract_top_level_markdown_block(body: str, *headings: str) -> str:
    heading_keys = {normalize_markdown_heading_key(heading) for heading in headings}
    for heading, block_body in parse_top_level_blocks(body):
        if normalize_markdown_heading_key(heading) in heading_keys:
            return block_body.strip()
    return ""


def collect_named_second_level_blocks(text: str, *headings: str) -> dict[str, str]:
    heading_keys = {normalize_markdown_heading_key(heading) for heading in headings}
    blocks: dict[str, str] = {}
    for heading, block_body in parse_second_level_blocks(text):
        key = normalize_markdown_heading_key(heading)
        if key in heading_keys and block_body.strip() and key not in blocks:
            blocks[key] = block_body.strip()
    return blocks


def parse_second_level_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^## ([^\n]+)\n\n(.*?)(?=^# |^## |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def parse_third_level_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^### ([^\n]+)\n\n(.*?)(?=^# |^## |^### |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def parse_manuscript_shaped_draft(text: str) -> tuple[str | None, dict[str, str], dict[str, str]]:
    stripped = text.strip()
    metadata, front_matter_body = split_front_matter(stripped)
    front_matter_title = str(metadata.get("title") or "").strip()
    if front_matter_title and front_matter_title.lower() != "draft":
        body = front_matter_body.strip()
        block_pairs = parse_second_level_blocks(body)
        section_keys = {
            canonicalize_manuscript_major_heading(heading)
            for heading, block_body in block_pairs
            if block_body.strip()
        }
        manuscript_section_count = len(
            section_keys.intersection({"abstract", "introduction", "methods", "results", "discussion"})
        )
        if manuscript_section_count >= 3:
            blocks = {heading: block_body for heading, block_body in block_pairs}
            auxiliary_blocks = collect_named_top_level_blocks(body, *MANUSCRIPT_SHAPED_AUXILIARY_TOP_LEVEL_HEADINGS)
            auxiliary_blocks.update(
                collect_named_second_level_blocks(body, *MANUSCRIPT_SHAPED_AUXILIARY_TOP_LEVEL_HEADINGS)
            )
            return front_matter_title, blocks, auxiliary_blocks

    title_match = re.match(r"(?ms)^# ([^\n]+)\n+(.*)$", stripped)
    if title_match is None:
        return None, {}, {}
    title = title_match.group(1).strip()
    if not title or title.lower() == "draft":
        return None, {}, {}
    body = title_match.group(2).strip()
    blocks = {heading: block_body for heading, block_body in parse_second_level_blocks(body)}
    auxiliary_blocks = collect_named_top_level_blocks(body, *MANUSCRIPT_SHAPED_AUXILIARY_TOP_LEVEL_HEADINGS)
    return title, blocks, auxiliary_blocks


def first_nonempty_block(section_blocks: dict[str, str], *headings: str) -> str:
    for heading in headings:
        value = section_blocks.get(heading, "")
        if value.strip():
            return value.strip()
    return ""


def first_nonempty_named_block(named_blocks: dict[str, str], *headings: str) -> str:
    for heading in headings:
        value = named_blocks.get(normalize_markdown_heading_key(heading), "")
        if value.strip():
            return value.strip()
    return ""


def parse_figure_id_from_heading(heading: str) -> str | None:
    supplementary_match = re.match(r"^Supplementary Figure S(\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if supplementary_match:
        return f"FS{supplementary_match.group(1)}"
    supplementary_short_match = re.match(r"^FS(\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"FS{supplementary_short_match.group(1)}"
    main_match = re.match(r"^Figure (\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if main_match:
        return f"F{main_match.group(1)}"
    main_short_match = re.match(r"^F(\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if main_short_match:
        return f"F{main_short_match.group(1)}"
    return None


def normalize_materialized_figure_heading(heading: str) -> str | None:
    normalized = heading.strip()
    if not normalized:
        return None
    if re.match(r"^Figure \d+\b", normalized, flags=re.IGNORECASE):
        return normalized
    if re.match(r"^Supplementary Figure S\d+\b", normalized, flags=re.IGNORECASE):
        return normalized

    supplementary_match = re.match(r"^FS(\d+)(?:\.\s*(.+))?$", normalized, flags=re.IGNORECASE)
    if supplementary_match:
        suffix = f". {supplementary_match.group(2).strip()}" if supplementary_match.group(2) else ""
        return f"Supplementary Figure S{supplementary_match.group(1)}{suffix}"

    main_match = re.match(r"^F(\d+)(?:\.\s*(.+))?$", normalized, flags=re.IGNORECASE)
    if main_match:
        suffix = f". {main_match.group(2).strip()}" if main_match.group(2) else ""
        return f"Figure {main_match.group(1)}{suffix}"
    return None


def extract_main_figure_blocks(main_figures: str) -> list[tuple[str, str]]:
    figure_blocks = parse_figure_blocks(main_figures)
    if figure_blocks:
        return figure_blocks

    normalized_blocks: list[tuple[str, str]] = []
    for heading, block_body in parse_third_level_blocks(main_figures):
        normalized_heading = normalize_materialized_figure_heading(heading)
        if normalized_heading and normalized_heading.lower().startswith("figure "):
            normalized_blocks.append((normalized_heading, block_body))
    return normalized_blocks


def parse_figure_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for heading, body in parse_second_level_blocks(text):
        if parse_figure_id_from_heading(heading):
            blocks.append((heading, body))
    return blocks


def normalize_submission_figure_heading(heading: str) -> str:
    normalized_heading = str(heading or "").strip()
    if not normalized_heading:
        return normalized_heading
    supplementary_short_match = re.match(r"^FS(\d+)(\b.*)$", normalized_heading, flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"Supplementary Figure S{supplementary_short_match.group(1)}{supplementary_short_match.group(2)}"
    main_short_match = re.match(r"^F(\d+)(\b.*)$", normalized_heading, flags=re.IGNORECASE)
    if main_short_match:
        return f"Figure {main_short_match.group(1)}{main_short_match.group(2)}"
    return normalized_heading


def figure_id_aliases(figure_id: str) -> set[str]:
    normalized = str(figure_id or "").strip()
    if not normalized:
        return set()
    aliases = {normalized}
    supplementary_match = re.match(r"^SupplementaryFigureS(\d+)$", normalized, flags=re.IGNORECASE)
    if supplementary_match:
        aliases.add(f"FS{supplementary_match.group(1)}")
        return aliases
    supplementary_short_match = re.match(r"^FS(\d+)$", normalized, flags=re.IGNORECASE)
    if supplementary_short_match:
        aliases.add(f"SupplementaryFigureS{supplementary_short_match.group(1)}")
        return aliases
    main_match = re.match(r"^Figure(\d+)$", normalized, flags=re.IGNORECASE)
    if main_match:
        aliases.add(f"F{main_match.group(1)}")
        return aliases
    main_short_match = re.match(r"^F(\d+)$", normalized, flags=re.IGNORECASE)
    if main_short_match:
        aliases.add(f"Figure{main_short_match.group(1)}")
    return aliases


def load_figure_semantics_map(paper_root: Path) -> dict[str, dict[str, Any]]:
    path = paper_root / "figure_semantics_manifest.json"
    payload = load_json(path) if path.exists() else {}
    figures = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(figures, list):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for item in figures:
        if not isinstance(item, dict):
            continue
        figure_id = str(item.get("figure_id") or "").strip()
        for alias in figure_id_aliases(figure_id):
            normalized[alias] = item
    return normalized


def _build_catalog_figure_heading(*, figure_id: str, title: str) -> str:
    normalized_id = str(figure_id or "").strip()
    normalized_title = str(title or "").strip()
    match = re.match(r"^F(\d+)$", normalized_id, flags=re.IGNORECASE)
    if match:
        heading = f"Figure {match.group(1)}"
        if normalized_title:
            return f"{heading}. {normalized_title}"
        return heading
    if normalized_title:
        return normalized_title
    return normalized_id


def _select_submission_markdown_figure_source(entry: dict[str, Any]) -> str:
    source_paths = resolve_figure_source_paths(entry)
    if not source_paths:
        return ""
    preferred_suffixes = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf")
    normalized_paths = [str(item).strip() for item in source_paths if str(item).strip()]
    for suffix in preferred_suffixes:
        for candidate in normalized_paths:
            if candidate.lower().endswith(suffix):
                return candidate
    return normalized_paths[0] if normalized_paths else ""


def build_catalog_backed_main_figures(*, paper_root: Path, submission_root: Path) -> str:
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    if not figure_catalog_path.exists():
        return ""
    payload = load_json(figure_catalog_path)
    figures = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(figures, list):
        return ""

    workspace_root = paper_root.parent
    figure_blocks: list[str] = []
    for entry in figures:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("paper_role") or "").strip().lower() != "main_text":
            continue
        figure_id = str(entry.get("figure_id") or "").strip()
        image_source_rel = _select_submission_markdown_figure_source(entry)
        if not figure_id or not image_source_rel:
            continue
        image_source_path = resolve_relpath(workspace_root, image_source_rel)
        if not image_source_path.exists():
            continue
        image_rel = os.path.relpath(image_source_path.resolve(), submission_root.resolve())
        heading = _build_catalog_figure_heading(
            figure_id=figure_id,
            title=str(entry.get("title") or ""),
        )
        legend = str(entry.get("caption") or "").strip()
        block_parts: list[str] = []
        if legend:
            block_parts.append(legend)
        block_parts.append(f"![]({image_rel})")
        figure_blocks.append(f"## {heading}\n\n" + "\n\n".join(block_parts))
    return "\n\n".join(figure_blocks).strip()


def build_catalog_backed_submission_figure_image_map(*, paper_root: Path, submission_root: Path) -> dict[str, str]:
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    if not figure_catalog_path.exists():
        return {}
    payload = load_json(figure_catalog_path)
    figures = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(figures, list):
        return {}

    workspace_root = paper_root.parent
    image_map: dict[str, str] = {}
    for entry in figures:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("paper_role") or "").strip().lower() != "main_text":
            continue
        figure_id = str(entry.get("figure_id") or "").strip()
        image_source_rel = _select_submission_markdown_figure_source(entry)
        if not figure_id or not image_source_rel:
            continue
        image_source_path = resolve_relpath(workspace_root, image_source_rel)
        if not image_source_path.exists():
            continue
        image_map[figure_id] = os.path.relpath(image_source_path.resolve(), submission_root.resolve())
    return image_map


def merge_legend_with_figure_semantics(*, base_legend: str, figure_semantics: dict[str, Any] | None) -> str:
    legend_parts = [base_legend.strip()] if base_legend.strip() else []
    if not figure_semantics:
        return "\n\n".join(legend_parts).strip()

    overall_sentences: list[str] = []
    panel_sentences: list[str] = []
    glossary_sentence = ""
    boundary_sentences: list[str] = []

    def normalize_sentence(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if contains_internal_instruction_text(text):
            return ""
        if text[-1] not in ".!?":
            return f"{text}."
        return text

    def append_sentence(target: list[str], value: str) -> None:
        sentence = normalize_sentence(value)
        if sentence:
            target.append(sentence)

    append_sentence(overall_sentences, str(figure_semantics.get("direct_message") or ""))
    append_sentence(overall_sentences, str(figure_semantics.get("clinical_implication") or ""))
    append_sentence(overall_sentences, str(figure_semantics.get("interpretation_boundary") or ""))

    panel_messages = figure_semantics.get("panel_messages")
    if isinstance(panel_messages, list) and panel_messages:
        for panel in panel_messages:
            if not isinstance(panel, dict):
                continue
            panel_id = str(panel.get("panel_id") or "").strip()
            message = str(panel.get("message") or "").strip()
            if panel_id and message:
                if re.match(rf"(?i)^panel\s+{re.escape(panel_id)}\b", message):
                    panel_sentences.append(normalize_sentence(message))
                else:
                    panel_sentences.append(normalize_sentence(f"Panel {panel_id}: {message}"))

    legend_glossary = figure_semantics.get("legend_glossary")
    if isinstance(legend_glossary, list) and legend_glossary:
        glossary_parts: list[str] = []
        for item in legend_glossary:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term") or "").strip()
            explanation = str(item.get("explanation") or "").strip().rstrip(".; ")
            if term and explanation:
                glossary_parts.append(f"{term}, {explanation}")
        if glossary_parts:
            glossary_sentence = normalize_sentence(f"Abbreviations: {'; '.join(glossary_parts)}")

    append_sentence(boundary_sentences, str(figure_semantics.get("threshold_semantics") or ""))
    append_sentence(boundary_sentences, str(figure_semantics.get("stratification_basis") or ""))
    append_sentence(boundary_sentences, str(figure_semantics.get("recommendation_boundary") or ""))

    existing_legend = " ".join(legend_parts)
    prose_blocks = [
        " ".join(sentence for sentence in overall_sentences if sentence),
        " ".join(sentence for sentence in panel_sentences if sentence),
        " ".join(
            sentence
            for sentence in [glossary_sentence, *boundary_sentences]
            if sentence
        ),
    ]
    deduped_semantic_lines = [block for block in prose_blocks if block and block not in existing_legend]
    if deduped_semantic_lines:
        legend_parts.extend(deduped_semantic_lines)
    return "\n\n".join(part for part in legend_parts if part).strip()


def build_figure_legend_blocks(
    *,
    main_figures: str,
    figure_semantics_map: dict[str, dict[str, Any]],
) -> list[str]:
    figure_legend_blocks: list[str] = []
    for heading, block_body in extract_main_figure_blocks(main_figures):
        figure_id = parse_figure_id_from_heading(heading)
        legend = merge_legend_with_figure_semantics(
            base_legend=strip_image_lines(block_body),
            figure_semantics=figure_semantics_map.get(figure_id or ""),
        )
        if legend:
            normalized_heading = normalize_submission_figure_heading(heading)
            figure_legend_blocks.append(f"## {normalized_heading}\n\n{legend}")
    return figure_legend_blocks


MARKDOWN_IMAGE_LINE_PATTERN = re.compile(r"^!\[[^\]]*]\([^)]+\)(?:\s*\{[^}]+\})?$")


def is_markdown_image_line(line: str) -> bool:
    return bool(MARKDOWN_IMAGE_LINE_PATTERN.match(line.strip()))


def extract_image_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if is_markdown_image_line(line)]


def rewrite_submission_surface_image_lines(*, image_lines: list[str], figure_id: str | None) -> list[str]:
    normalized_figure_id = str(figure_id or "").strip()
    if not normalized_figure_id:
        return image_lines

    figure_aliases = figure_id_aliases(normalized_figure_id)
    target_basename = build_figure_basename(normalized_figure_id)
    image_pattern = re.compile(r"(!\[[^\]]*]\()([^)]+)(\))")
    rewritten_lines: list[str] = []

    for line in image_lines:
        def replace(match: re.Match[str]) -> str:
            raw_path = match.group(2).strip()
            if raw_path.startswith(("http://", "https://", "/", "../")):
                return match.group(0)
            if "figures/" not in raw_path and not raw_path.startswith("figures"):
                return match.group(0)
            path_obj = Path(raw_path)
            if path_obj.stem not in figure_aliases:
                return match.group(0)
            rewritten_path = path_obj.with_name(f"{target_basename}{path_obj.suffix}").as_posix()
            return f"{match.group(1)}{rewritten_path}{match.group(3)}"

        rewritten_lines.append(image_pattern.sub(replace, line))
    return rewritten_lines


def build_submission_figure_blocks(
    *,
    main_figures: str,
    figure_semantics_map: dict[str, dict[str, Any]],
    catalog_image_map: dict[str, str] | None = None,
) -> list[str]:
    figure_blocks: list[str] = []
    resolved_catalog_image_map = catalog_image_map or {}
    for heading, block_body in extract_main_figure_blocks(main_figures):
        figure_id = parse_figure_id_from_heading(heading)
        image_lines = rewrite_submission_surface_image_lines(
            image_lines=extract_image_lines(block_body),
            figure_id=figure_id,
        )
        if not image_lines and figure_id:
            fallback_image_rel = resolved_catalog_image_map.get(figure_id)
            if fallback_image_rel:
                image_lines = [f"![]({fallback_image_rel})"]
        legend = merge_legend_with_figure_semantics(
            base_legend=strip_image_lines(block_body),
            figure_semantics=figure_semantics_map.get(figure_id or ""),
        )
        content_parts: list[str] = []
        if image_lines:
            content_parts.append("\n".join(image_lines))
        if legend:
            content_parts.append(legend)
        if content_parts:
            normalized_heading = normalize_submission_figure_heading(heading)
            figure_blocks.append(f"## {normalized_heading}\n\n{'\n\n'.join(content_parts)}")
    return figure_blocks


def build_table_blocks(*, main_tables: str) -> list[str]:
    table_blocks: list[str] = []
    for heading, block_body in parse_top_level_blocks(main_tables):
        table_blocks.append(f"## {heading}\n\n{block_body}")
    if not table_blocks and main_tables.strip():
        table_blocks.append(f"## Table 1\n\n{main_tables.strip()}")
    return table_blocks


def strip_image_lines(text: str) -> str:
    cleaned_lines = [line for line in text.splitlines() if not is_markdown_image_line(line)]
    return "\n".join(cleaned_lines).strip()


def rewrite_image_paths(*, markdown_text: str, source_markdown_dir: Path, target_markdown_dir: Path) -> str:
    image_pattern = re.compile(r"(!\[[^\]]*]\()([^)]+)(\))")

    def replace(match: re.Match[str]) -> str:
        image_path = match.group(2).strip()
        if image_path.startswith(("http://", "https://")) or os.path.isabs(image_path):
            return match.group(0)
        resolved_path = (source_markdown_dir / image_path).resolve()
        relative_path = os.path.relpath(resolved_path, target_markdown_dir.resolve())
        return f"{match.group(1)}{relative_path}{match.group(3)}"

    return image_pattern.sub(replace, markdown_text)


def count_main_text_figures_in_catalog(figure_catalog: dict[str, Any]) -> int:
    count = 0
    for item in figure_catalog.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("paper_role") or "").strip().lower() == "main_text":
            count += 1
    return count


def parse_independent_figure_legend_map(figure_legends_section: str) -> dict[str, str]:
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
    failures: list[dict[str, Any]] = []
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
    docx_stats["older_than_source_markdown"] = docx_older_than_source_markdown
    pdf_stats["older_than_source_markdown"] = pdf_older_than_source_markdown

    if not source_stats["exists"]:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "source_markdown",
                "descriptor": source_markdown_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_source_markdown_missing",
                "audit_classes": ["manuscript_surface"],
            }
        )
    else:
        if source_stats["figure_blocks_with_images"] < expected_main_figure_count:
            failures.append(
                {
                    "collection": "manuscript",
                    "item_id": "source_markdown",
                    "descriptor": source_markdown_path.name,
                    "qc_profile": qc_profile,
                    "failure_reason": "submission_source_markdown_missing_inline_figures",
                    "audit_classes": ["manuscript_surface"],
                }
            )
        if source_stats["figure_blocks_with_legends"] < expected_main_figure_count:
            failures.append(
                {
                    "collection": "manuscript",
                    "item_id": "source_markdown",
                    "descriptor": source_markdown_path.name,
                    "qc_profile": qc_profile,
                    "failure_reason": "submission_source_markdown_missing_figure_legends",
                    "audit_classes": ["manuscript_surface"],
                }
            )
        if source_stats["duplicate_major_sections"]:
            failures.append(
                {
                    "collection": "manuscript",
                    "item_id": "source_markdown",
                    "descriptor": source_markdown_path.name,
                    "qc_profile": qc_profile,
                    "failure_reason": "submission_source_markdown_duplicate_sections",
                    "audit_classes": ["manuscript_surface", "hygiene"],
                    "duplicate_major_sections": source_stats["duplicate_major_sections"],
                }
            )
        if source_stats["internal_instruction_hits"]:
            failures.append(
                {
                    "collection": "manuscript",
                    "item_id": "source_markdown",
                    "descriptor": source_markdown_path.name,
                    "qc_profile": qc_profile,
                    "failure_reason": "submission_source_markdown_internal_instruction_leakage",
                    "audit_classes": ["manuscript_surface", "hygiene"],
                    "internal_instruction_hits": source_stats["internal_instruction_hits"],
                }
            )

    if docx_stats["embedded_image_count"] < expected_main_figure_count:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "docx",
                "descriptor": docx_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_docx_missing_embedded_figures",
                "audit_classes": ["manuscript_surface"],
            }
        )
    if docx_older_than_source_markdown:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "docx",
                "descriptor": docx_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_docx_older_than_source_markdown",
                "audit_classes": ["manuscript_surface", "freshness"],
            }
        )
    if pdf_stats["embedded_image_count"] < expected_main_figure_count:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "pdf",
                "descriptor": pdf_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_pdf_missing_embedded_figures",
                "audit_classes": ["manuscript_surface"],
            }
        )
    if pdf_older_than_source_markdown:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "pdf",
                "descriptor": pdf_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_pdf_older_than_source_markdown",
                "audit_classes": ["manuscript_surface", "freshness"],
            }
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
