from __future__ import annotations

from dataclasses import dataclass


DEFAULT_STUDY_ARCHETYPE_IDS = (
    "clinical_classifier",
    "clinical_subtype_reconstruction",
    "external_validation_model_update",
    "gray_zone_triage",
    "llm_agent_clinical_task",
    "mechanistic_sidecar_extension",
)


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
    "clinical_subtype_reconstruction": StudyArchetype(
        archetype_id="clinical_subtype_reconstruction",
        title="Clinical subtype reconstruction",
        when_to_prefer=(
            "the disease shows visible heterogeneity that can be reorganized into clinically legible subgroups",
            "the paper can compare subtype-specific prognosis, treatment response, or biological differences rather than relying on one fixed factor",
            "there is room to derive a subtype recognizer or transfer the subtype system to another cohort",
        ),
        expected_paper_package=(
            "subtype derivation with explicit feature set and modeling contract",
            "cluster stability or reproducibility assessment",
            "clinical characterization across subtype groups",
            "outcome or treatment-response comparison across subtypes",
            "subtype recognizer or assignment model when feasible",
            "external cohort transfer or public-data-supported subtype contextualization",
        ),
        public_data_roles=(
            "external subtype transfer",
            "cohort broadening",
            "biological or functional contextualization of the reconstructed groups",
        ),
    ),
    "external_validation_model_update": StudyArchetype(
        archetype_id="external_validation_model_update",
        title="External validation / model update",
        when_to_prefer=(
            "a usable clinical prediction model already exists locally or in the literature",
            "the key value is to show transportability, recalibration, or model updating rather than inventing a new model family",
            "public or collaborative cohorts can materially strengthen evidence beyond a single-center story",
        ),
        expected_paper_package=(
            "baseline model reproduction or registry",
            "external validation with discrimination and calibration assessment",
            "transportability / recalibration / model-updating analysis",
            "clinical subgroup heterogeneity across sites, periods, or case mix",
            "decision-utility comparison before and after updating when feasible",
            "manuscript-safe reproducibility manifest for the transferred model path",
        ),
        public_data_roles=(
            "external validation",
            "temporal or geographic transport testing",
            "model updating or recalibration support",
        ),
    ),
    "gray_zone_triage": StudyArchetype(
        archetype_id="gray_zone_triage",
        title="Gray-zone triage / reflex-testing support",
        when_to_prefer=(
            "the clinical task is not simply yes-versus-no but involves rule-in, rule-out, and indeterminate zones",
            "the paper can change downstream workflow such as who needs extra imaging, testing, follow-up, or expert review",
            "the gray-zone design can improve safety, resource allocation, or clinician workload even when discrimination gains are moderate",
        ),
        expected_paper_package=(
            "triage-zone definition with explicit operating thresholds",
            "rule-in / rule-out / gray-zone yield analysis",
            "net-benefit or resource-utilization comparison against current workflow",
            "subgroup comparison across clinically relevant strata",
            "error review for unsafe triage patterns",
            "simplified bedside pathway or reflex-testing recommendation",
        ),
        public_data_roles=(
            "threshold robustness checking",
            "workflow transfer testing in external cohorts",
            "case-mix expansion for safety analysis",
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
    "mechanistic_sidecar_extension": StudyArchetype(
        archetype_id="mechanistic_sidecar_extension",
        title="Mechanistic sidecar extension",
        when_to_prefer=(
            "a stronger primary clinical route already exists and needs biological, pathway, regulator, or public-dataset support",
            "the paper benefits from linking classifier- or subtype-defined groups to plausible biological interpretation",
            "public omics or knowledge resources can materially deepen the story rather than decorate it",
        ),
        expected_paper_package=(
            "primary clinical grouping or model-defined contrast",
            "functional / pathway / regulator-level interpretation",
            "cross-dataset consistency check for the mechanistic signal when feasible",
            "subgroup-aware biological interpretation rather than one pooled enrichment table",
            "clear separation between primary clinical claim and sidecar mechanistic support",
        ),
        public_data_roles=(
            "omics or functional extension",
            "knowledge-base or regulator inference support",
            "independent contextual support for clinically defined groups",
        ),
    ),
    "survey_trend_analysis": StudyArchetype(
        archetype_id="survey_trend_analysis",
        title="Survey trend / guideline correspondence",
        when_to_prefer=(
            "the primary asset is one or more clinician or patient surveys rather than a labeled prediction endpoint",
            "the paper value comes from trend comparison across timepoints, respondent groups, or stakeholder perspectives",
            "the manuscript needs to map observed uptake or preference patterns onto guideline-aligned treatment axes without drifting into causal effectiveness claims",
        ),
        expected_paper_package=(
            "cross-timepoint prevalence / uptake / preference trend tables",
            "explicit survey harmonization and denominator contract",
            "trend comparison across timepoints",
            "pre-draft asset upgrade scan across timepoint, stakeholder, center/geography, and guideline axes",
            "field-verified multicenter or geography coverage before national or multicenter framing",
            "subgroup comparison across clinically legible respondent strata",
            "prespecified subgroup or association analyses when verified variables support them",
            "guideline-correspondence matrix on mechanism or family axes",
            "practice or preference drift interpretation with access, reimbursement, and safety context",
            "guideline-to-reality constraint discussion covering price, reimbursement, access, safety, and clinician recommendation gaps",
            "transparent separation between current-use, future-preference, and clinician-adoption surfaces",
        ),
        public_data_roles=(
            "guideline or policy context for interpretation",
            "practice or preference drift",
            "external survey triangulation",
            "market-access or reimbursement context that explains observed adoption gaps",
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
