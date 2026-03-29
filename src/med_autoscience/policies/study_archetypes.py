from __future__ import annotations

from dataclasses import dataclass


DEFAULT_STUDY_ARCHETYPE_IDS = ("clinical_classifier", "llm_agent_clinical_task")


@dataclass(frozen=True)
class StudyArchetype:
    archetype_id: str
    title: str
    when_to_prefer: tuple[str, ...]
    expected_paper_package: tuple[str, ...]
    public_data_roles: tuple[str, ...]


_ARCHETYPES = {
    "clinical_classifier": StudyArchetype(
        archetype_id="clinical_classifier",
        title="Clinical classifier / risk stratification",
        when_to_prefer=(
            "the cohort supports a supervised endpoint with clinical decision relevance",
            "there is room to define clinically interpretable high-risk versus low-risk groups",
            "the paper can benefit from calibration, threshold tuning, and utility analysis rather than discrimination alone",
        ),
        expected_paper_package=(
            "discrimination metrics with internal validation",
            "calibration assessment and recalibration discussion",
            "decision-curve / threshold / net-benefit analysis",
            "subgroup comparison and clinically interpretable risk-group analysis",
            "explainability surfaces or case-level attribution review",
            "external validation or public-data-supported extension when feasible",
        ),
        public_data_roles=(
            "external validation",
            "cohort extension",
            "mechanistic or contextual support for the classifier-defined groups",
        ),
    ),
    "llm_agent_clinical_task": StudyArchetype(
        archetype_id="llm_agent_clinical_task",
        title="LLM agent for a clinical task",
        when_to_prefer=(
            "the clinical problem can be framed as a bounded task such as diagnosis support, report abstraction, triage, or structured decision support",
            "a strong non-agent baseline exists and can be compared fairly",
            "there is enough case material to study variation across prompt, reasoning, and agent-architecture choices",
        ),
        expected_paper_package=(
            "task-level performance against conventional baselines",
            "prompt / reasoning / agent-architecture variants",
            "subgroup comparison across clinically meaningful strata",
            "error taxonomy or failure-mode review",
            "case-level interpretability or trajectory review",
            "external validation, temporal split validation, or public benchmark transfer",
            "calibration and utility analysis when the task is a clinical classification decision",
        ),
        public_data_roles=(
            "public benchmark extension",
            "external validation",
            "case-mix broadening beyond the local dataset",
        ),
    ),
}


def get_archetype(archetype_id: str) -> StudyArchetype:
    try:
        return _ARCHETYPES[archetype_id]
    except KeyError as exc:
        supported = ", ".join(sorted(_ARCHETYPES))
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
