from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_STUDY_ARCHETYPE_IDS = (
    "clinical_classifier",
    "clinical_subtype_reconstruction",
    "external_validation_model_update",
    "gray_zone_triage",
    "llm_agent_clinical_task",
    "mechanistic_sidecar_extension",
)
STUDY_ARCHETYPES_MARKDOWN_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "policies" / "study-workflow" / "study_archetypes.md"
)
_LIST_SECTIONS = {
    "When To Prefer": "when_to_prefer",
    "Expected Paper Package": "expected_paper_package",
    "Public Data Roles": "public_data_roles",
}


@dataclass(frozen=True)
class StudyArchetype:
    archetype_id: str
    title: str
    when_to_prefer: tuple[str, ...]
    expected_paper_package: tuple[str, ...]
    public_data_roles: tuple[str, ...]


def get_archetype(archetype_id: str) -> StudyArchetype:
    archetypes = _load_archetypes_by_id()
    try:
        return archetypes[archetype_id]
    except KeyError as exc:
        supported = ", ".join(sorted(archetypes))
        raise ValueError(f"Unsupported study archetype: {archetype_id}. Supported: {supported}") from exc


def resolve_archetypes(archetype_ids: tuple[str, ...] | list[str] | None = None) -> tuple[StudyArchetype, ...]:
    normalized = DEFAULT_STUDY_ARCHETYPE_IDS if archetype_ids is None else tuple(archetype_ids)
    return tuple(get_archetype(archetype_id) for archetype_id in normalized)


def render_archetype_block(archetype_ids: tuple[str, ...] | list[str] | None = None) -> str:
    archetypes = resolve_archetypes(archetype_ids)
    lines = [
        "## Preferred study archetypes",
        "",
        "Keep these high-yield paper packages in the serious frontier whenever the data contract supports them.",
    ]
    for archetype in archetypes:
        lines.extend(
            [
                "",
                f"### {archetype.title}",
                "",
                "Prefer when:",
                *[f"- {item}" for item in archetype.when_to_prefer],
                "",
                "Expected paper package:",
                *[f"- {item}" for item in archetype.expected_paper_package],
                "",
                "Public-data strengthening routes:",
                *[f"- {item}" for item in archetype.public_data_roles],
            ]
        )
    return "\n".join(lines) + "\n"


def _load_archetypes_by_id() -> dict[str, StudyArchetype]:
    return _parse_study_archetypes_markdown(STUDY_ARCHETYPES_MARKDOWN_PATH.read_text(encoding="utf-8"))


def _parse_study_archetypes_markdown(markdown: str) -> dict[str, StudyArchetype]:
    cards: dict[str, dict[str, object]] = {}
    current_id = ""
    current_section = ""
    section_lines: list[str] = []

    def flush_section() -> None:
        nonlocal section_lines
        if not current_id or not current_section:
            section_lines = []
            return
        field = _LIST_SECTIONS.get(current_section)
        if field:
            cards[current_id][field] = tuple(_markdown_list(section_lines))
        section_lines = []

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            flush_section()
            candidate_id = line[3:].strip()
            current_id = candidate_id if _is_archetype_id(candidate_id) else ""
            current_section = ""
            section_lines = []
            if current_id:
                cards[current_id] = {"archetype_id": current_id}
            continue
        if not current_id:
            continue
        if line.startswith("### "):
            flush_section()
            current_section = line[4:].strip()
            continue
        if current_section:
            section_lines.append(line)
            continue
        if line.startswith("Title:"):
            cards[current_id]["title"] = line.removeprefix("Title:").strip()

    flush_section()
    return {archetype_id: _normalize_archetype(archetype_id, payload) for archetype_id, payload in cards.items()}


def _normalize_archetype(archetype_id: str, payload: dict[str, object]) -> StudyArchetype:
    return StudyArchetype(
        archetype_id=archetype_id,
        title=_required_text(payload.get("title"), field=f"{archetype_id}.title"),
        when_to_prefer=_required_tuple(payload.get("when_to_prefer"), field=f"{archetype_id}.when_to_prefer"),
        expected_paper_package=_required_tuple(
            payload.get("expected_paper_package"),
            field=f"{archetype_id}.expected_paper_package",
        ),
        public_data_roles=_required_tuple(payload.get("public_data_roles"), field=f"{archetype_id}.public_data_roles"),
    )


def _is_archetype_id(value: str) -> bool:
    return bool(value) and value.replace("_", "").replace("-", "").isalnum()


def _markdown_list(lines: list[str]) -> list[str]:
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ") and line.strip()[2:].strip()]


def _required_text(value: object, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"study archetypes Markdown missing required field: {field}")
    return text


def _required_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"study archetypes Markdown missing required list: {field}")
    return value
