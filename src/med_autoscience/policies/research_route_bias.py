from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID = "high_plasticity_medical"
SUPPORTED_STAGE_IDS = (
    "intake-audit",
    "scout",
    "baseline",
    "idea",
    "decision",
    "experiment",
    "analysis-campaign",
)
RESEARCH_ROUTE_BIAS_MARKDOWN_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "policies"
    / "study-workflow"
    / "research_route_bias_policy.md"
)
_LIST_SECTIONS = {
    "Preferred Route Order": "preferred_route_order",
    "Candidate Scoring Dimensions": "candidate_scoring_dimensions",
    "Downrank Patterns": "downrank_patterns",
    "Public Data Rules": "public_data_rules",
}


@dataclass(frozen=True)
class ResearchRouteBiasPolicy:
    policy_id: str
    title: str
    preferred_route_order: tuple[str, ...]
    candidate_scoring_dimensions: tuple[str, ...]
    downrank_patterns: tuple[str, ...]
    public_data_rules: tuple[str, ...]
    stage_openers: dict[str, str]
    stage_questions: dict[str, tuple[str, ...]]


def get_policy(policy_id: str = DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID) -> ResearchRouteBiasPolicy:
    policies = _load_policies_by_id()
    try:
        return policies[policy_id]
    except KeyError as exc:
        supported = ", ".join(sorted(policies))
        raise ValueError(f"Unsupported research route bias policy: {policy_id}. Supported: {supported}") from exc


def render_policy_block(
    *,
    stage_id: str,
    policy_id: str = DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID,
) -> str:
    if stage_id not in SUPPORTED_STAGE_IDS:
        supported = ", ".join(SUPPORTED_STAGE_IDS)
        raise ValueError(f"Unsupported stage id: {stage_id}. Supported: {supported}")

    policy = get_policy(policy_id)
    opener = policy.stage_openers.get(stage_id)
    if not opener:
        raise ValueError(f"research route bias Markdown missing opener for stage: {stage_id}")
    lines = [
        "## Medical publication route bias",
        "",
        opener,
        "",
        "Default priority order:",
        *[f"- {item}" for item in policy.preferred_route_order],
        "",
        "Candidate scoring dimensions:",
        *[f"- {item}" for item in policy.candidate_scoring_dimensions],
        "",
    ]
    stage_questions = policy.stage_questions.get(stage_id, ())
    if stage_questions:
        lines.extend(
            [
                "Route-level questions:",
                *[f"- {item}" for item in stage_questions],
                "",
            ]
        )
    lines.extend(
        [
            "Down-rank routes with these failure patterns:",
            *[f"- {item}" for item in policy.downrank_patterns],
            "",
            "Public-data use rules:",
            *[f"- {item}" for item in policy.public_data_rules],
        ]
    )
    return "\n".join(lines) + "\n"


def _load_policies_by_id() -> dict[str, ResearchRouteBiasPolicy]:
    return _parse_research_route_bias_markdown(RESEARCH_ROUTE_BIAS_MARKDOWN_PATH.read_text(encoding="utf-8"))


def _parse_research_route_bias_markdown(markdown: str) -> dict[str, ResearchRouteBiasPolicy]:
    policies: dict[str, dict[str, object]] = {}
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
            policies[current_id][field] = tuple(_markdown_list(section_lines))
        elif current_section == "Stage Openers":
            policies[current_id]["stage_openers"] = _markdown_keyed_text(section_lines)
        elif current_section == "Stage Questions":
            policies[current_id]["stage_questions"] = _markdown_keyed_lists(section_lines)
        section_lines = []

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            flush_section()
            candidate_id = line[3:].strip()
            current_id = candidate_id if _is_policy_id(candidate_id) else ""
            current_section = ""
            section_lines = []
            if current_id:
                policies[current_id] = {"policy_id": current_id}
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
            policies[current_id]["title"] = line.removeprefix("Title:").strip()

    flush_section()
    return {policy_id: _normalize_policy(policy_id, payload) for policy_id, payload in policies.items()}


def _normalize_policy(policy_id: str, payload: dict[str, object]) -> ResearchRouteBiasPolicy:
    return ResearchRouteBiasPolicy(
        policy_id=policy_id,
        title=_required_text(payload.get("title"), field=f"{policy_id}.title"),
        preferred_route_order=_required_tuple(
            payload.get("preferred_route_order"),
            field=f"{policy_id}.preferred_route_order",
        ),
        candidate_scoring_dimensions=_required_tuple(
            payload.get("candidate_scoring_dimensions"),
            field=f"{policy_id}.candidate_scoring_dimensions",
        ),
        downrank_patterns=_required_tuple(payload.get("downrank_patterns"), field=f"{policy_id}.downrank_patterns"),
        public_data_rules=_required_tuple(payload.get("public_data_rules"), field=f"{policy_id}.public_data_rules"),
        stage_openers=_required_stage_openers(payload.get("stage_openers"), field=f"{policy_id}.stage_openers"),
        stage_questions=_stage_questions(payload.get("stage_questions")),
    )


def _markdown_list(lines: list[str]) -> list[str]:
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ") and line.strip()[2:].strip()]


def _markdown_keyed_text(lines: list[str]) -> dict[str, str]:
    keyed: dict[str, str] = {}
    for item in _markdown_list(lines):
        key, separator, value = item.partition(":")
        if separator and key.strip() and value.strip():
            keyed[key.strip()] = value.strip()
    return keyed


def _markdown_keyed_lists(lines: list[str]) -> dict[str, tuple[str, ...]]:
    keyed: dict[str, list[str]] = {}
    for item in _markdown_list(lines):
        key, separator, value = item.partition(":")
        if not separator or not key.strip() or not value.strip():
            continue
        keyed.setdefault(key.strip(), []).append(value.strip())
    return {key: tuple(values) for key, values in keyed.items()}


def _is_policy_id(value: str) -> bool:
    return bool(value) and value.replace("_", "").replace("-", "").isalnum()


def _required_text(value: object, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"research route bias Markdown missing required field: {field}")
    return text


def _required_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"research route bias Markdown missing required list: {field}")
    return value


def _required_stage_openers(value: object, *, field: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"research route bias Markdown missing required mapping: {field}")
    missing = [stage_id for stage_id in SUPPORTED_STAGE_IDS if not str(value.get(stage_id) or "").strip()]
    if missing:
        raise ValueError(f"research route bias Markdown missing stage openers: {', '.join(missing)}")
    return {str(key): str(item).strip() for key, item in value.items() if str(item).strip()}


def _stage_questions(value: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return {}
    return {str(key): tuple(str(item).strip() for item in items if str(item).strip()) for key, items in value.items()}
