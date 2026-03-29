from __future__ import annotations

from dataclasses import dataclass


DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID = "high_plasticity_medical"
SUPPORTED_STAGE_IDS = ("scout", "idea", "decision")


@dataclass(frozen=True)
class ResearchRouteBiasPolicy:
    policy_id: str
    title: str
    preferred_route_order: tuple[str, ...]
    candidate_scoring_dimensions: tuple[str, ...]
    downrank_patterns: tuple[str, ...]
    public_data_rules: tuple[str, ...]


_POLICIES = {
    DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID: ResearchRouteBiasPolicy(
        policy_id=DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID,
        title="High-plasticity medical publication bias",
        preferred_route_order=(
            "supervised prediction or risk-stratification routes with clinically interpretable downstream analyses",
            "subtype-reconstruction routes that can be converted into clinically legible subgroup stories or subtype recognizers",
            "routes that can absorb external public data for validation, extension, or mechanism/context support",
            "gray-zone triage routes when they can change workflow, testing, or follow-up decisions even without dramatic AUC gains",
            "LLM / agent tasks only when the task can be bounded, benchmarked fairly, and translated into a medical paper package",
            "routes that can naturally produce a full paper-facing evidence package rather than a single fragile association",
            "fixed-factor clinical association routes only when prior evidence or clinical importance is unusually strong",
        ),
        candidate_scoring_dimensions=(
            "clinical significance if the result is positive",
            "controllability of the downstream paper path",
            "room for iterative model/package refinement",
            "public-data extensibility",
            "likely figure/table depth for a Q2+ medical paper",
            "whether the route can survive a moderate rather than spectacular main effect",
        ),
        downrank_patterns=(
            "the main value would hinge on one fixed clinical factor being significant",
            "a negative result would leave little room for branching or rescue",
            "the likely paper would have weak clinical utility even if the analysis is technically clean",
            "the route cannot be expanded beyond a thin association table and discussion",
            "an LLM / agent route is framed too broadly to benchmark rigorously against clinician-relevant baselines",
        ),
        public_data_rules=(
            "Use public data when it can materially add external validation, cohort extension, or biological/context support.",
            "Do not add public data only as decorative workload.",
        ),
    )
}

_STAGE_OPENERS = {
    "scout": (
        "When the quest is a medical-data paper line, do not treat all reasonable frames as equally good scouting outputs. "
        "Prefer frames that are more controllable for publication and more extensible for downstream evidence-building."
    ),
    "idea": (
        "For medical-data quests, treat publishability controllability as a first-class selection criterion. "
        "Do not prefer a route merely because it is clinically familiar or easy to describe."
    ),
    "decision": (
        "For medical-data quests, route selection should explicitly favor lines with a more controllable path to a publishable paper. "
        "In practice, prefer routes that preserve room for meaningful iteration, richer paper packaging, and clinically legible utility."
    ),
}

_STAGE_QUESTIONS = {
    "decision": (
        "which route is most likely to support a clinically meaningful classifier / risk-stratification / utility package?",
        "which route could support a subtype-reconstruction or gray-zone triage story if the main discriminative gain is only moderate?",
        "which route leaves room for calibration, subgroup, explainability, and external-validation expansion?",
        "for LLM / agent tasks, is the task narrow enough to benchmark cleanly and clinically?",
        "which route can still branch productively if the first main result is only moderate rather than striking?",
        "which route is most likely to accumulate enough figure/table depth for a Q2+ medical manuscript?",
    ),
}


def get_policy(policy_id: str = DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID) -> ResearchRouteBiasPolicy:
    try:
        return _POLICIES[policy_id]
    except KeyError as exc:
        supported = ", ".join(sorted(_POLICIES))
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
    lines = [
        "## Medical publication route bias",
        "",
        _STAGE_OPENERS[stage_id],
        "",
        "Default priority order:",
        *[f"- {item}" for item in policy.preferred_route_order],
        "",
        "Candidate scoring dimensions:",
        *[f"- {item}" for item in policy.candidate_scoring_dimensions],
        "",
    ]
    stage_questions = _STAGE_QUESTIONS.get(stage_id, ())
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
