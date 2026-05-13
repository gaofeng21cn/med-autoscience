# Study Archetypes

Status: `active first-generation route memory seed`
Owner: `MedAutoScience`
Purpose: Markdown-first canonical body for first-generation study archetype prose used by MAS overlay prompt/context rendering.
State: first-generation route bias / contract input; full publication-route domain memory lives in `publication_route_memory_library.md`.
Machine boundary: Python loads and validates this Markdown for overlay rendering and profile archetype validation. This document does not authorize study truth, route decisions, quality verdicts, publication readiness, or workspace memory writeback.

默认 `preferred_study_archetypes`：

- `clinical_classifier`
- `clinical_subtype_reconstruction`
- `external_validation_model_update`
- `gray_zone_triage`
- `llm_agent_clinical_task`
- `mechanistic_sidecar_extension`

这些 archetype 是旧 MAS 已实现的第一代 route bias / contract input。它们会从 profile 或 study payload 进入 `study_archetype` 解析，然后影响 medical analysis contract、medical reporting contract、medical paper readiness、statistical discipline runtime 和 overlay prompt 的路线/报告期望。它们不是完整的论文套路经验库，也不是 workspace memory store，没有 writeback proposal、accepted/rejected receipt、workspace pack 或 inventory。

完整的论文套路 domain memory 现在由 [Publication Route Memory Policy](./publication_route_memory_policy.md) 管理，维护者直接编辑 [Publication Route Memory Library](./publication_route_memory_library.md)，repo seed index 位于 [publication_route_memory_seed_fixture.json](./publication_route_memory_seed_fixture.json)，真实 workspace memory pack 位于 `portfolio/research_memory/publication_route_memory/memory_pack.json`。当前 Markdown library 已把这些 archetype 扩展为富文本 natural-language memory cards；每张卡包含 fit/poor-fit、minimum evidence package、analysis/display pattern、claim boundary、reviewer risks、pivot/stop rules 和 stage guidance。这里保留的是第一代 route-bias 正文，方便旧 overlay 和 profile 入口继续读取。

## clinical_classifier

Title: Clinical classifier / risk stratification

### When To Prefer

- the cohort supports a supervised endpoint with clinical decision relevance
- there is room to define clinically interpretable high-risk versus low-risk groups
- the paper can benefit from calibration, threshold tuning, and utility analysis rather than discrimination alone

### Expected Paper Package

- discrimination metrics with internal validation
- calibration assessment and recalibration discussion
- decision-curve / threshold / net-benefit analysis
- subgroup comparison and clinically interpretable risk-group analysis
- explainability surfaces or case-level attribution review
- external validation or public-data-supported extension when feasible

### Public Data Roles

- external validation
- cohort extension
- mechanistic or contextual support for the classifier-defined groups

## clinical_subtype_reconstruction

Title: Clinical subtype reconstruction

### When To Prefer

- the disease shows visible heterogeneity that can be reorganized into clinically legible subgroups
- the paper can compare subtype-specific prognosis, treatment response, or biological differences rather than relying on one fixed factor
- there is room to derive a subtype recognizer or transfer the subtype system to another cohort

### Expected Paper Package

- subtype derivation with explicit feature set and modeling contract
- cluster stability or reproducibility assessment
- clinical characterization across subtype groups
- outcome or treatment-response comparison across subtypes
- subtype recognizer or assignment model when feasible
- external cohort transfer or public-data-supported subtype contextualization

### Public Data Roles

- external subtype transfer
- cohort broadening
- biological or functional contextualization of the reconstructed groups

## external_validation_model_update

Title: External validation / model update

### When To Prefer

- a usable clinical prediction model already exists locally or in the literature
- the key value is to show transportability, recalibration, or model updating rather than inventing a new model family
- public or collaborative cohorts can materially strengthen evidence beyond a single-center story

### Expected Paper Package

- baseline model reproduction or registry
- external validation with discrimination and calibration assessment
- transportability / recalibration / model-updating analysis
- clinical subgroup heterogeneity across sites, periods, or case mix
- decision-utility comparison before and after updating when feasible
- manuscript-safe reproducibility manifest for the transferred model path

### Public Data Roles

- external validation
- temporal or geographic transport testing
- model updating or recalibration support

## gray_zone_triage

Title: Gray-zone triage / reflex-testing support

### When To Prefer

- the clinical task is not simply yes-versus-no but involves rule-in, rule-out, and indeterminate zones
- the paper can change downstream workflow such as who needs extra imaging, testing, follow-up, or expert review
- the gray-zone design can improve safety, resource allocation, or clinician workload even when discrimination gains are moderate

### Expected Paper Package

- triage-zone definition with explicit operating thresholds
- rule-in / rule-out / gray-zone yield analysis
- net-benefit or resource-utilization comparison against current workflow
- subgroup comparison across clinically relevant strata
- error review for unsafe triage patterns
- simplified bedside pathway or reflex-testing recommendation

### Public Data Roles

- threshold robustness checking
- workflow transfer testing in external cohorts
- case-mix expansion for safety analysis

## llm_agent_clinical_task

Title: LLM agent for a clinical task

### When To Prefer

- the clinical problem can be framed as a bounded task such as diagnosis support, report abstraction, triage, or structured decision support
- a strong non-agent baseline exists and can be compared fairly
- there is enough case material to study variation across prompt, reasoning, and agent-architecture choices

### Expected Paper Package

- task-level performance against conventional baselines
- prompt / reasoning / agent-architecture variants
- subgroup comparison across clinically meaningful strata
- error taxonomy or failure-mode review
- case-level interpretability or trajectory review
- external validation, temporal split validation, or public benchmark transfer
- calibration and utility analysis when the task is a clinical classification decision

### Public Data Roles

- public benchmark extension
- external validation
- case-mix broadening beyond the local dataset

## mechanistic_sidecar_extension

Title: Mechanistic sidecar extension

### When To Prefer

- a stronger primary clinical route already exists and needs biological, pathway, regulator, or public-dataset support
- the paper benefits from linking classifier- or subtype-defined groups to plausible biological interpretation
- public omics or knowledge resources can materially deepen the story rather than decorate it

### Expected Paper Package

- primary clinical grouping or model-defined contrast
- functional / pathway / regulator-level interpretation
- cross-dataset consistency check for the mechanistic signal when feasible
- subgroup-aware biological interpretation rather than one pooled enrichment table
- clear separation between primary clinical claim and sidecar mechanistic support

### Public Data Roles

- omics or functional extension
- knowledge-base or regulator inference support
- independent contextual support for clinically defined groups

## survey_trend_analysis

Title: Survey trend / guideline correspondence

### When To Prefer

- the primary asset is one or more clinician or patient surveys rather than a labeled prediction endpoint
- the paper value comes from trend comparison across timepoints, respondent groups, or stakeholder perspectives
- the manuscript needs to map observed uptake or preference patterns onto guideline-aligned treatment axes without drifting into causal effectiveness claims

### Expected Paper Package

- cross-timepoint prevalence / uptake / preference trend tables
- explicit survey harmonization and denominator contract
- trend comparison across timepoints
- pre-draft asset upgrade scan across timepoint, stakeholder, center/geography, and guideline axes
- field-verified multicenter or geography coverage before national or multicenter framing
- subgroup comparison across clinically legible respondent strata
- prespecified subgroup or association analyses when verified variables support them
- guideline-correspondence matrix on mechanism or family axes
- practice or preference drift interpretation with access, reimbursement, and safety context
- guideline-to-reality constraint discussion covering price, reimbursement, access, safety, and clinician recommendation gaps
- transparent separation between current-use, future-preference, and clinician-adoption surfaces

### Public Data Roles

- guideline or policy context for interpretation
- practice or preference drift
- external survey triangulation
- market-access or reimbursement context that explains observed adoption gaps
