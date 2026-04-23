from .shared import *
from .asset_scans import *

def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower().replace("&", "and"))


def parse_markdown_heading_blocks(text: str) -> list[MarkdownHeadingBlock]:
    lines = text.splitlines()
    headings: list[tuple[int, str, int]] = []
    in_front_matter = False
    in_code_block = False

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if line_number == 1 and stripped == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if stripped == "---":
                in_front_matter = False
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = MARKDOWN_HEADING_RE.match(raw_line)
        if match is None:
            continue
        headings.append((len(match.group(1)), match.group(2).strip(), line_number))

    blocks: list[MarkdownHeadingBlock] = []
    total_lines = len(lines)
    for index, (level, heading, start_line) in enumerate(headings):
        end_line = total_lines
        for next_level, _, next_start_line in headings[index + 1 :]:
            if next_level <= level:
                end_line = next_start_line - 1
                break
        body_start_index = start_line
        body_end_index = end_line
        body = "\n".join(lines[body_start_index:body_end_index]).strip()
        blocks.append(
            MarkdownHeadingBlock(
                level=level,
                heading=heading,
                start_line=start_line,
                end_line=end_line,
                body=body,
            )
        )
    return blocks


def find_heading_block(
    blocks: list[MarkdownHeadingBlock],
    *,
    level: int,
    headings: tuple[str, ...],
) -> MarkdownHeadingBlock | None:
    normalized_targets = {normalize_heading(item) for item in headings}
    for block in blocks:
        if block.level != level:
            continue
        if normalize_heading(block.heading) in normalized_targets:
            return block
    return None


def find_heading_block_with_fallback_levels(
    blocks: list[MarkdownHeadingBlock],
    *,
    levels: tuple[int, ...],
    headings: tuple[str, ...],
) -> MarkdownHeadingBlock | None:
    for level in levels:
        block = find_heading_block(blocks, level=level, headings=headings)
        if block is not None:
            return block
    return None


def child_heading_blocks(
    blocks: list[MarkdownHeadingBlock],
    *,
    parent: MarkdownHeadingBlock,
    level: int,
) -> list[MarkdownHeadingBlock]:
    return [
        block
        for block in blocks
        if block.level == level and parent.start_line < block.start_line <= parent.end_line
    ]


def first_subsection_heading_blocks(
    blocks: list[MarkdownHeadingBlock],
    *,
    parent: MarkdownHeadingBlock,
) -> list[MarkdownHeadingBlock]:
    descendant_blocks = [
        block
        for block in blocks
        if parent.start_line < block.start_line <= parent.end_line and block.level > parent.level
    ]
    if not descendant_blocks:
        return []
    subsection_level = min(block.level for block in descendant_blocks)
    return [block for block in descendant_blocks if block.level == subsection_level]


def extract_nonempty_paragraphs(text: str) -> list[str]:
    without_headings = re.sub(r"(?m)^#{1,6}\s+.+$", "", text)
    return [block.strip() for block in re.split(r"\n\s*\n", without_headings) if block.strip()]


def scan_manuscript_surface_sections_for_patterns(
    path: Path,
    *,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    hits: list[dict[str, Any]] = []
    for headings in (("Abstract",), ("Results",)):
        block = find_heading_block_with_fallback_levels(blocks, levels=(2, 1), headings=headings)
        if block is None or not block.body.strip():
            continue
        hits.extend(
            scan_string_value_for_patterns(path, f"line {block.start_line}", block.body, patterns=patterns)
        )
    return hits


def inspect_results_narrative_surface_language(
    *,
    path: Path,
    payload: object,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return []
    hits: list[dict[str, Any]] = []
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        for field in ("section_title", "research_question", "direct_answer", "clinical_meaning", "boundary"):
            value = str(section.get(field) or "").strip()
            if not value:
                continue
            hits.extend(
                scan_string_value_for_patterns(path, f"sections[{index}].{field}", value, patterns=patterns)
            )
    return hits


def inspect_claim_evidence_surface_language(
    *,
    path: Path,
    payload: object,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    claims = payload.get("claims")
    if not isinstance(claims, list):
        return []
    hits: list[dict[str, Any]] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        if str(claim.get("paper_role") or "").strip() != "main_text":
            continue
        statement = str(claim.get("statement") or "").strip()
        if statement:
            hits.extend(
                scan_string_value_for_patterns(path, f"claims[{index}].statement", statement, patterns=patterns)
            )
    return hits


def inspect_introduction_structure(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    introduction_block = find_heading_block_with_fallback_levels(
        blocks,
        levels=(2, 1),
        headings=("Introduction",),
    )
    if introduction_block is None:
        return [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": "introduction_structure",
                "phrase": "Introduction",
                "excerpt": "Manuscript is missing a second-level `Introduction` section.",
            }
        ]
    paragraphs = extract_nonempty_paragraphs(introduction_block.body)
    if len(paragraphs) >= medical_surface_policy.INTRODUCTION_REQUIRED_PARAGRAPH_COUNT:
        return []
    return [
        {
            "path": str(path),
            "location": f"line {introduction_block.start_line}",
            "pattern_id": "introduction_structure",
            "phrase": introduction_block.heading,
            "excerpt": (
                "Introduction must contain at least "
                f"{medical_surface_policy.INTRODUCTION_REQUIRED_PARAGRAPH_COUNT} formal paragraphs "
                "covering clinical context, current evidence gap, and present-study objective."
            ),
        }
    ]


def inspect_methods_section_structure(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    methods_block = find_heading_block_with_fallback_levels(
        blocks,
        levels=(2, 1),
        headings=("Materials and Methods", "Materials & Methods", "Methods"),
    )
    if methods_block is None:
        return [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": "methods_section_structure",
                "phrase": "Materials and Methods",
                "excerpt": "Manuscript is missing a second-level Methods section.",
            }
        ]
    subsection_blocks = first_subsection_heading_blocks(blocks, parent=methods_block)
    subsection_map = {normalize_heading(block.heading): block for block in subsection_blocks if block.body.strip()}
    missing_headings = [
        heading
        for heading in medical_surface_policy.METHODS_REQUIRED_SUBSECTION_HEADINGS
        if normalize_heading(heading) not in subsection_map
    ]
    if not missing_headings:
        return []
    return [
        {
            "path": str(path),
            "location": f"line {methods_block.start_line}",
            "pattern_id": "methods_section_structure",
            "phrase": methods_block.heading,
            "excerpt": (
                "Methods section must include the reviewer-facing subsections: "
                + ", ".join(medical_surface_policy.METHODS_REQUIRED_SUBSECTION_HEADINGS)
                + f". Missing: {', '.join(missing_headings)}."
            ),
        }
    ]


def inspect_results_section_structure(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    results_block = find_heading_block_with_fallback_levels(
        blocks,
        levels=(2, 1),
        headings=("Results",),
    )
    if results_block is None:
        return [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": "results_section_structure",
                "phrase": "Results",
                "excerpt": "Manuscript is missing a second-level `Results` section.",
            }
        ]
    subsection_blocks = [block for block in first_subsection_heading_blocks(blocks, parent=results_block) if block.body.strip()]
    if len(subsection_blocks) >= medical_surface_policy.RESULTS_MIN_SUBSECTION_COUNT:
        return []
    return [
        {
            "path": str(path),
            "location": f"line {results_block.start_line}",
            "pattern_id": "results_section_structure",
            "phrase": results_block.heading,
            "excerpt": (
                "Results section must be broken into at least "
                f"{medical_surface_policy.RESULTS_MIN_SUBSECTION_COUNT} subsection headings with non-empty prose."
            ),
        }
    ]


def scan_non_formal_question_sentences(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    in_front_matter = False
    in_code_block = False
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if line_number == 1 and stripped == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if stripped == "---":
                in_front_matter = False
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        sanitized = URL_RE.sub("", raw_line).strip()
        if not sanitized:
            continue
        for sentence in iter_non_formal_question_sentences(sanitized):
            if not sentence:
                continue
            hits.append(
                {
                    "path": str(path),
                    "location": f"line {line_number}",
                    "pattern_id": "non_formal_question_sentence",
                    "phrase": sentence,
                    "excerpt": sentence,
                }
            )
    return hits


def iter_non_formal_question_sentences(line: str) -> list[str]:
    sentences: list[str] = []
    sentence_start = 0
    for index, char in enumerate(line):
        if char not in SENTENCE_TERMINATOR_CHARS:
            continue
        if char in QUESTION_MARK_CHARS:
            excerpt_start = max(sentence_start, index - QUESTION_SENTENCE_CONTEXT_LIMIT)
            sentence = line[excerpt_start : index + 1].strip()
            if any(letter.isascii() and letter.isalpha() for letter in sentence):
                sentences.append(sentence)
        sentence_start = index + 1
    return sentences


