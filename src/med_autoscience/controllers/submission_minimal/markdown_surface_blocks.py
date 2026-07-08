import re


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
        "display_directive",
        re.compile(
            r"\b(?:the\s+)?(?:first|second|third|main)?\s*display\s+(?:should|must)\b",
            flags=re.IGNORECASE,
        ),
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
