# Publication Route Memory Library

Status: active canonical memory body
Owner: MedAutoScience
Purpose: human-maintained Markdown-first publication route experience memory for MAS stage-led Codex execution.
State: canonical repo source for seed cards; workspace packs and receipts are generated/applied MAS owner surfaces.
Machine boundary: this file is the human and Codex-readable memory body. JSON fixtures, workspace packs, inventories, receipts, and OPL projections are indexes or generated surfaces, not the canonical prose source.

## Maintenance Rules

- Edit this Markdown file when adding or revising reusable publication-route experience.
- Keep each card rich enough for Codex CLI to reason with: fit, poor fit, evidence package, analysis/display pattern, claim boundary, reviewer risks, pivot/stop rules, stage guidance, examples, and failure modes.
- Do not turn cards into a recipe engine, route scorer, fixed workflow, publication gate, or controller decision source.
- Keep JSON surfaces generated, indexed, or receipt-like unless they represent runtime truth or machine contracts.

## publication_route_memory_seed__clinical_classifier

Status: active_seed
Route family: clinical_classifier
Stage applicability: scout, idea, decision, analysis-campaign, review
Title: Clinical classifier / risk stratification route

### Summary

Use this route when the dataset supports a supervised clinical endpoint and the publishable value is a clinically interpretable risk stratification tool rather than a bare association. Codex should treat the card as experience about what usually makes the paper credible, then adapt the analysis to the actual cohort, endpoint, event count, and clinical decision point.

### Best Fit

- A clearly measured clinical outcome, follow-up window, or diagnostic target is available.
- The cohort has enough events or positives to support internal validation and subgroup checks.
- Clinicians can act on high-risk, low-risk, or indeterminate strata.
- Calibration, threshold behavior, and decision utility are central to the claim.

### Poor Fit

- The endpoint is too rare, unstable, or post hoc to support a credible model.
- The only available story is a high AUC without calibration or utility.
- Important predictors are leakage-prone or unavailable at the intended decision time.

### Minimum Evidence Package

- Cohort and endpoint lock with inclusion, exclusion, time origin, and prediction horizon.
- Transparent feature availability contract matching the intended clinical moment.
- Internal validation with discrimination, calibration, and optimism control.
- Threshold or risk-group analysis tied to a clinical action or monitoring decision.
- Subgroup and failure-mode review for clinically important strata.

### Analysis Pattern

- Start with a conventional baseline model before testing more flexible learners.
- Separate model development, validation, and final interpretation outputs.
- Report calibration and net benefit alongside discrimination.
- Keep explainability tied to plausible clinical features rather than decorative attribution.

### Table Figure Pattern

- Table 1 cohort and outcome characteristics by development/validation split or risk group.
- Model performance table with discrimination, calibration, and clinical utility metrics.
- Calibration plot and decision-curve plot.
- Risk-strata outcome curve or confusion/threshold table.
- Feature importance or case-level explanation figure when it changes interpretation.

### Reviewer Risks

- Reviewer asks for calibration, external validation, or decision-curve evidence.
- Reviewer identifies leakage between predictors and endpoint ascertainment.
- Reviewer challenges event-per-variable adequacy or overfitting.
- Reviewer rejects black-box claims without clinical interpretation.

### Pivot Or Stop Rules

- Pivot to gray-zone triage if thresholds and rule-in/rule-out behavior are stronger than global discrimination.
- Pivot to external validation / model update if an existing model is the real contribution.
- Stop or downgrade if event count cannot support a stable endpoint model.

### Example Signals

- Outcome rate is sufficient for stable internal validation.
- Clinical users already classify patients into risk strata or follow-up intensities.
- Predictors are available before the decision moment.

### Failure Modes

- AUC-only paper with no calibration or decision relevance.
- Endpoint leakage through post-outcome predictors.
- Risk groups do not map to any clinical decision.
- Subgroup performance collapses in clinically important strata.

### Claim Boundary

A classifier route can claim risk stratification utility only when validation, calibration, and decision relevance are all visible. It should not claim causal effects, treatment benefit, or deployment readiness without separate evidence.

### Codex Stage Guidance

- scout: Check endpoint availability, event count, feature timing, and candidate clinical action.
- idea: Compare classifier, triage, and external-validation routes against actual data affordances.
- decision: Choose this route only with an evidence plan for calibration and clinical utility.
- analysis-campaign: Prioritize validation, calibration, threshold, and subgroup artifacts before narrative expansion.
- review: Expect calibration, leakage, overfitting, and clinical usefulness critiques.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#clinical_classifier | first_generation_route_seed

## publication_route_memory_seed__clinical_subtype_reconstruction

Status: active_seed
Route family: clinical_subtype_reconstruction
Stage applicability: scout, idea, decision, analysis-campaign, review
Title: Clinical subtype reconstruction route

### Summary

Use this route when the disease or syndrome appears heterogeneous and the paper can create clinically legible subtypes that explain prognosis, treatment response, phenotype distribution, or biological context. The route is exploratory and must prove stability and interpretability before making claims about new disease taxonomy.

### Best Fit

- Multiple clinical, laboratory, imaging, or longitudinal features describe disease heterogeneity.
- Simple one-factor stratification leaves an incomplete or unstable story.
- Subtype differences can be linked to outcomes, treatment response, or care pathways.
- There is a plausible way to assign future cases to derived subtypes.

### Poor Fit

- The cohort is too small for stable subgroup discovery.
- Clusters are driven by missingness, site, batch, or obvious severity alone.
- The paper cannot explain what clinicians should do differently with the subtypes.

### Minimum Evidence Package

- Feature set and preprocessing contract for subtype derivation.
- Subtype stability or reproducibility analysis.
- Clinical characterization table across subtypes.
- Outcome, treatment-response, or pathway contrast across subtypes.
- Subtype assignment model or transfer check when feasible.

### Analysis Pattern

- Start with clinically interpretable features and sensitivity checks.
- Evaluate more than one clustering or latent structure only when justified.
- Separate subtype discovery from subtype outcome comparison.
- Check whether subtypes simply reproduce severity, center, or missingness.

### Table Figure Pattern

- Subtype feature heatmap or profile plot.
- Table 1 by subtype.
- Stability or consensus matrix figure.
- Outcome or treatment-response comparison plot.
- Subtype assignment flow or recognizer performance table.

### Reviewer Risks

- Reviewer asks whether clusters are reproducible or clinically actionable.
- Reviewer challenges arbitrary number of clusters.
- Reviewer identifies center, batch, severity, or missingness as the hidden driver.
- Reviewer asks for an assigner or validation cohort.

### Pivot Or Stop Rules

- Pivot to classifier if a stable endpoint model is stronger than subtype discovery.
- Pivot to mechanistic sidecar only after clinical subtypes are stable.
- Stop or downgrade if subtype stability fails under reasonable sensitivity checks.

### Example Signals

- Different feature domains point to recurring patient profiles.
- Subtypes differ in prognosis or treatment path after adjustment.
- A subtype assigner can be built with available clinical variables.

### Failure Modes

- Decorative clustering with no stable clinical meaning.
- Subtype count chosen for narrative convenience.
- Subtypes duplicate known severity without added value.
- No validation, transfer, or assignment route.

### Claim Boundary

Subtype reconstruction can claim an interpretable data-derived grouping with associated clinical differences. It cannot claim a new disease entity, mechanism, or treatment indication without independent validation and supporting biology.

### Codex Stage Guidance

- scout: Look for heterogeneous features, sufficient sample size, and plausible clinical use.
- idea: Compare subtype discovery against simpler stratification and classifier routes.
- decision: Require an explicit stability and interpretability plan before choosing this route.
- analysis-campaign: Treat stability, characterization, and outcome contrast as first-class outputs.
- review: Prepare to answer reproducibility, cluster-number, and actionability critiques.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#clinical_subtype_reconstruction | first_generation_route_seed

## publication_route_memory_seed__negative_result_stoploss

Status: active_seed
Route family: weak_or_negative_result_handling
Stage applicability: decision, analysis-campaign, review
Title: Negative or unstable main analysis should trigger downgrade, bounded repair, route switch, or stop-loss

### Summary

When a bounded analysis campaign returns unstable, reversed, or non-identifiable evidence, preserve failed paths and let the controller decide whether to downgrade the claim, repair a bounded evidence gap, switch route, return to scouting, ask for a human gate, or stop.

### Best Fit

- The current route has real negative, reversed, unstable, or underpowered evidence.
- The team needs to avoid positive-story inflation.
- There are bounded repair options or a plausible lower-claim route.
- Failed-path evidence can be recorded and reused.

### Poor Fit

- A single noisy result is being treated as definitive failure without bounded checks.
- The proposed memory would store current-study evidence instead of reusable route experience.
- The route can still be repaired with a clearly scoped evidence gap.

### Minimum Evidence Package

- Failed-path or weak-result record with source refs.
- Bounded repair attempts or explicit reason not to repair.
- Controller decision request with downgrade, reroute, human-gate, or stop options.
- Claim-boundary update if the paper continues.
- Writeback proposal only for reusable route lessons, not study-specific findings.

### Analysis Pattern

- Freeze the negative or weak evidence before rerouting.
- Separate bounded repair from open-ended fishing.
- Use controller decision to choose stop, downgrade, reroute, or human gate.
- If continuing, write the negative result transparently or switch to a legitimate lower-claim route.

### Table Figure Pattern

- Failed-path or weak-result summary table.
- Sensitivity or bounded repair result matrix.
- Claim downgrade / reroute decision table.
- Reviewer-risk table for continuing versus stopping.
- Updated evidence-to-claim map when the route continues.

### Reviewer Risks

- Reviewer detects hidden negative paths or selective reporting.
- Reviewer challenges exploratory post hoc repairs.
- Reviewer asks why the claim was not downgraded.
- Reviewer sees route switch as unsupported unless provenance is explicit.

### Pivot Or Stop Rules

- Repair only if the gap is bounded and linked to a prespecified or controller-approved issue.
- Reroute only if a different publication route has independent evidence.
- Stop if all candidate claims depend on unstable or reversed evidence.
- Ask for human gate when continuation depends on strategic rather than evidentiary judgment.

### Example Signals

- Primary endpoint effect reverses under basic sensitivity analysis.
- Calibration or subgroup evidence collapses after validation.
- Reviewer or AI review flags positive-story inflation risk.

### Failure Modes

- The proposed memory repeats a single-study result instead of a reusable route lesson.
- The proposed writeback tries to replace evidence or review ledgers.
- The revised paper narrative hides the failed path.
- Open-ended analysis fishing is mislabeled as bounded repair.

### Claim Boundary

Negative-result stop-loss can support transparent downgrade, reroute, or termination. It cannot be used to erase failed evidence, keep a positive claim without support, or authorize open-ended analysis fishing.

### Codex Stage Guidance

- scout: Use this card only as background if prior failed paths exist.
- idea: Compare lower-claim routes without hiding the failed path.
- decision: Make downgrade, reroute, human-gate, or stop the explicit decision surface.
- analysis-campaign: Bound repair attempts and log negative results.
- review: Prepare transparent failed-path and claim-restraint response.

### Source Refs

- human_doc | docs/policies/study-workflow/stage_led_research_autonomy.md | stage_policy

## publication_route_memory_seed__external_validation_model_update

Status: active_seed
Route family: external_validation_or_model_update
Stage applicability: scout, idea, analysis-campaign, review
Title: External validation / model update route

### Summary

Use this route when an existing model, score, or local predictor can be tested across a new cohort, period, site, or case mix. The publishable value is transportability, recalibration, and clinically interpretable updating rather than novelty of the modeling algorithm.

### Best Fit

- A prior model, clinical score, or local model is available with enough implementation detail.
- The target cohort differs in site, period, geography, population, or case mix.
- Validation can report both discrimination and calibration.
- Recalibration or limited updating has a clinically meaningful rationale.

### Poor Fit

- The source model cannot be reconstructed or applied faithfully.
- The target endpoint or predictor definitions are incompatible.
- Only internal resampling is available despite a claimed external-validation story.

### Minimum Evidence Package

- Model reconstruction or source score implementation record.
- Target cohort and endpoint harmonization contract.
- External validation metrics including calibration.
- Recalibration or updating analysis when performance is weak.
- Clinical utility or subgroup transportability check when feasible.

### Analysis Pattern

- Apply original model first before updating.
- Report performance degradation or calibration drift transparently.
- Use parsimonious updating before claiming a new model.
- Compare original, recalibrated, and updated versions under the same endpoint contract.

### Table Figure Pattern

- Source-to-target cohort comparison table.
- Validation performance table for original, recalibrated, and updated models.
- Calibration plot before and after update.
- Decision-curve or threshold utility comparison.
- Transportability subgroup forest or case-mix sensitivity figure.

### Reviewer Risks

- Reviewer asks whether original model implementation was faithful.
- Reviewer challenges endpoint or predictor harmonization.
- Reviewer wants calibration and clinical utility rather than discrimination only.
- Reviewer treats excessive refitting as a new-model paper.

### Pivot Or Stop Rules

- Pivot to external-validation rescue if the original planned discovery claim is weak but validation/update remains credible.
- Pivot to classifier if no source model can be reconstructed but a local endpoint model is feasible.
- Stop if model inputs or endpoint definitions cannot be harmonized.

### Example Signals

- Local dataset contains predictors required by a known score.
- Case mix or clinical period differs enough to make validation informative.
- Calibration drift is clinically meaningful and fixable.

### Failure Modes

- Rebuilt model silently differs from the published model.
- Endpoint harmonization changes the clinical question.
- Updating overfits the target cohort.
- The paper markets recalibration as algorithmic novelty.

### Claim Boundary

This route can claim external performance, transportability limits, recalibration value, or update feasibility. It should not claim discovery of a new predictor unless the study actually validates that claim independently.

### Codex Stage Guidance

- scout: Find prior models and check whether their predictors and endpoints can be reconstructed.
- idea: Frame the contribution around transportability, recalibration, or model updating.
- decision: Choose the route only with a defensible source-to-target harmonization plan.
- analysis-campaign: Run original model, calibration, update, and utility comparisons in order.
- review: Prepare model reconstruction, endpoint harmonization, and calibration evidence.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#external_validation_model_update | first_generation_route_seed

## publication_route_memory_seed__gray_zone_triage

Status: active_seed
Route family: gray_zone_triage
Stage applicability: scout, idea, decision, analysis-campaign, review
Title: Gray-zone triage / reflex-testing route

### Summary

Use this route when the clinical task is better expressed as rule-in, rule-out, and indeterminate management than as one global classifier. It can be publishable when it improves safety, workflow, resource use, or follow-up allocation even if global discrimination gains are moderate.

### Best Fit

- Clinical practice already has a triage or reflex-testing decision.
- There are plausible thresholds for rule-in, rule-out, and gray-zone handling.
- Safety and resource-use consequences can be measured or estimated.
- The gray-zone group is clinically meaningful rather than a leftover.

### Poor Fit

- There is no actionable downstream pathway for indeterminate cases.
- Thresholds are tuned only to maximize apparent performance.
- The gray-zone proportion is so large that the workflow becomes unusable.

### Minimum Evidence Package

- Explicit decision pathway and candidate thresholds.
- Rule-in, rule-out, and gray-zone yield and error analysis.
- Safety review for missed cases and unnecessary escalation.
- Resource-use or workflow comparison against current practice.
- Subgroup checks for unsafe triage behavior.

### Analysis Pattern

- Define operating points before narrative expansion.
- Report threshold tradeoffs and gray-zone burden.
- Compare triage workflow with current standard or simple baseline.
- Analyze unsafe false-negative and false-positive cases separately.

### Table Figure Pattern

- Triage flow diagram with rule-in, rule-out, and gray-zone counts.
- Threshold performance table.
- Decision curve or resource-use comparison figure.
- Safety error review table.
- Subgroup triage performance plot.

### Reviewer Risks

- Reviewer asks why thresholds are clinically justified.
- Reviewer challenges safety of rule-out cases.
- Reviewer argues gray-zone burden is too high for practice.
- Reviewer asks for resource or workflow impact evidence.

### Pivot Or Stop Rules

- Pivot from classifier to triage when threshold behavior is clinically stronger than global AUC.
- Pivot to classifier if no actionable gray-zone workflow exists.
- Stop or downgrade if unsafe miss patterns appear in key subgroups.

### Example Signals

- Clinicians need to decide who needs imaging, follow-up, or specialist review.
- Intermediate-risk patients have a distinct management path.
- A simple threshold pair creates safe and interpretable groups.

### Failure Modes

- Gray-zone is a statistical artifact with no clinical pathway.
- Thresholds are chosen after outcome inspection without restraint.
- Rule-out group contains clinically unacceptable misses.
- Resource-use claims are unsupported.

### Claim Boundary

A gray-zone triage paper can claim improved triage framing, workflow allocation, or safety-aware decision support. It cannot claim diagnostic replacement or reduced harm without direct validation of downstream outcomes.

### Codex Stage Guidance

- scout: Identify the actual clinical triage decision and downstream action.
- idea: Compare triage thresholds with global classifier and simple rule baselines.
- decision: Require a safety and resource-use analysis plan.
- analysis-campaign: Make threshold, flow, safety, and subgroup artifacts first-class.
- review: Expect critiques around threshold justification and gray-zone burden.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#gray_zone_triage | first_generation_route_seed

## publication_route_memory_seed__llm_agent_clinical_task

Status: active_seed
Route family: llm_agent_clinical_task
Stage applicability: scout, idea, decision, analysis-campaign, review
Title: LLM agent for bounded clinical task route

### Summary

Use this route when a clinical workflow can be framed as a bounded task such as abstraction, triage, diagnosis support, report review, or structured decision support. The route needs fair baselines, task definitions, error analysis, and safety boundaries; it should not rely on novelty of the agent alone.

### Best Fit

- The task has clear inputs, outputs, labels, and a clinical use case.
- A non-agent baseline or clinician baseline can be compared fairly.
- Case-level error review is feasible.
- The study can separate prompt, model, and agent-tooling contributions.

### Poor Fit

- Labels are subjective or unavailable.
- The task is too broad for reproducible evaluation.
- The only contribution is using an LLM without clinical benchmark or safety analysis.

### Minimum Evidence Package

- Task definition with input/output contract and label source.
- Baseline comparison against conventional models, rules, or human readers when available.
- Evaluation by subgroup, difficulty, and clinically meaningful error type.
- Prompt or agent configuration record sufficient for reproducibility.
- Safety, failure-mode, and claim-boundary review.

### Analysis Pattern

- Start with simple and conventional baselines.
- Separate prompt-only, tool-assisted, and agentic variants when tested.
- Report error taxonomy rather than only aggregate accuracy.
- Preserve cases where the agent is unsafe, overconfident, or non-reproducible.

### Table Figure Pattern

- Task and evaluation flow diagram.
- Performance table across baseline, LLM, and agent variants.
- Subgroup and difficulty-stratum table.
- Error taxonomy figure or table.
- Representative case review with de-identified evidence trail.

### Reviewer Risks

- Reviewer asks for stronger baselines or clinician comparison.
- Reviewer challenges label quality and leakage.
- Reviewer asks whether prompts, model versions, and tools are reproducible.
- Reviewer flags unsafe errors or overclaiming clinical deployment.

### Pivot Or Stop Rules

- Pivot to clinical classifier if the LLM route adds little over structured features.
- Pivot to workflow audit if labels are too weak for performance claims.
- Stop or downgrade if error review shows unacceptable safety failures.

### Example Signals

- Structured reports or notes contain enough information for labeled abstraction.
- Current workflow has a measurable bottleneck or error-prone step.
- Agent output can be audited case by case.

### Failure Modes

- Novelty-only LLM paper without clinical task discipline.
- Unclear label source or hidden leakage.
- Aggregate accuracy hides unsafe subgroup errors.
- Prompt/model changes make results non-reproducible.

### Claim Boundary

An LLM-agent route can claim bounded task performance under the tested setting. It cannot claim autonomous clinical deployment, diagnostic replacement, or general safety without prospective, workflow-level validation.

### Codex Stage Guidance

- scout: Check whether the task can be bounded and labeled.
- idea: Compare LLM-agent framing with conventional classifier or rule-based alternatives.
- decision: Require baseline, reproducibility, and safety evaluation plans.
- analysis-campaign: Prioritize task contract, baselines, subgroup analysis, and error taxonomy.
- review: Prepare safety, reproducibility, label, and baseline responses.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#llm_agent_clinical_task | first_generation_route_seed

## publication_route_memory_seed__mechanistic_sidecar_extension

Status: active_seed
Route family: mechanistic_sidecar_extension
Stage applicability: idea, decision, analysis-campaign, review
Title: Mechanistic sidecar extension route

### Summary

Use this route as an extension to a stronger clinical paper line when public omics, pathway, regulator, or knowledge-base evidence can explain a clinically defined contrast. It should strengthen interpretation, not replace weak clinical evidence.

### Best Fit

- A primary clinical classifier, subtype, or contrast is already credible.
- Public omics or biological resources can map to the clinical grouping.
- Mechanistic evidence clarifies interpretation or reviewer concerns.
- The manuscript can keep biological support separate from primary clinical claims.

### Poor Fit

- The primary clinical route is weak or unstable.
- Public data do not match disease, tissue, cell type, or clinical contrast.
- The sidecar becomes decorative enrichment without a testable connection.

### Minimum Evidence Package

- Primary clinical grouping or model-defined contrast.
- Public dataset or knowledge resource provenance and relevance check.
- Pathway, regulator, cell-type, or functional analysis tied to the clinical contrast.
- Sensitivity or cross-dataset consistency check when feasible.
- Clear text boundary between mechanism hypothesis and clinical evidence.

### Analysis Pattern

- Start from the clinical contrast and ask which public evidence can support it.
- Avoid pooled enrichment detached from subtype or risk strata.
- Use cross-dataset consistency when public data are available.
- Treat mechanism as interpretive support unless independently validated.

### Table Figure Pattern

- Clinical contrast to public-data mapping diagram.
- Pathway or regulator enrichment figure.
- Cross-dataset consistency plot.
- Subtype/risk-group mechanistic summary table.
- Evidence-boundary figure or table distinguishing clinical and biological claims.

### Reviewer Risks

- Reviewer says public data are mismatched to the clinical cohort.
- Reviewer treats enrichment as speculative decoration.
- Reviewer asks whether mechanism is independent or circular with model features.
- Reviewer challenges causal language.

### Pivot Or Stop Rules

- Use as a sidecar only after a primary clinical route is viable.
- Pivot back to clinical route repair if mechanism is being used to hide weak evidence.
- Stop or remove if public-data relevance cannot be defended.

### Example Signals

- Subtype groups show biological plausibility needing support.
- Public omics data align with the disease context or tissue.
- Reviewer or journal fit expects mechanism/contextual evidence.

### Failure Modes

- Mechanistic analysis is used to cover weak clinical results.
- Public datasets do not match the clinical question.
- Enrichment outputs are generic and non-specific.
- Causal claims exceed evidence.

### Claim Boundary

Mechanistic sidecar evidence can support plausibility and interpretation. It cannot rescue an invalid clinical route or claim mechanism, causality, or therapeutic target validation without dedicated experimental evidence.

### Codex Stage Guidance

- scout: Do not choose this as a standalone route unless the clinical contrast already exists.
- idea: Identify which clinical route would benefit from mechanism support.
- decision: Require public-data relevance and claim-boundary checks.
- analysis-campaign: Keep mapping, enrichment, and consistency outputs tied to clinical contrast.
- review: Prepare relevance, circularity, and causal-language responses.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#mechanistic_sidecar_extension | first_generation_route_seed

## publication_route_memory_seed__survey_trend_analysis

Status: active_seed
Route family: survey_trend_analysis
Stage applicability: scout, idea, decision, analysis-campaign, review
Title: Survey trend / guideline correspondence route

### Summary

Use this route when the primary evidence is survey, adoption, preference, practice-pattern, or guideline-correspondence data. The publishable value comes from disciplined harmonization, denominator clarity, stakeholder or timepoint comparison, and restrained interpretation in access, reimbursement, safety, or guideline context.

### Best Fit

- Survey instruments, timepoints, stakeholder groups, or regions can be harmonized.
- The denominator and sampling frame are clear enough for descriptive claims.
- Trend, preference, adoption, or guideline correspondence is clinically relevant.
- Access, reimbursement, safety, or policy context explains observed gaps.

### Poor Fit

- Sampling frame is too unclear for any interpretable denominator.
- Question wording changes prevent credible harmonization.
- The manuscript tries to infer clinical effectiveness from preference or adoption data.

### Minimum Evidence Package

- Survey instrument and denominator contract.
- Question harmonization table across timepoints or groups.
- Trend, subgroup, or stakeholder comparison.
- Guideline correspondence matrix when relevant.
- Contextual interpretation covering access, reimbursement, safety, and recommendation gaps.

### Analysis Pattern

- Separate current use, future preference, clinician recommendation, and patient access surfaces.
- Preserve denominator changes rather than smoothing them away.
- Use subgroup or association analyses only when variables support them.
- Avoid causal claims about treatment benefit.

### Table Figure Pattern

- Survey harmonization and denominator table.
- Trend or uptake figure across timepoints.
- Stakeholder or subgroup comparison table.
- Guideline correspondence matrix.
- Constraint interpretation figure covering cost, reimbursement, access, safety, and recommendation gaps.

### Reviewer Risks

- Reviewer challenges denominator, sampling frame, or response bias.
- Reviewer asks whether question wording is harmonized.
- Reviewer rejects causal or effectiveness language.
- Reviewer wants guideline and access context for interpretation.

### Pivot Or Stop Rules

- Pivot to descriptive brief if harmonization is limited but transparent trend evidence remains useful.
- Pivot to data asset upgrade if geography, timepoint, or stakeholder coverage is insufficient.
- Stop or downgrade if denominator cannot support even descriptive claims.

### Example Signals

- Multiple timepoints or stakeholder groups can be compared.
- Guideline recommendations and observed adoption diverge.
- Access or reimbursement context explains practice gaps.

### Failure Modes

- Unclear denominator invalidates trend claims.
- Different question wording is treated as the same measure.
- Preference data are overclaimed as treatment effectiveness.
- National or multicenter framing lacks field verification.

### Claim Boundary

Survey trend analysis can claim observed practice, preference, adoption, or guideline-correspondence patterns under the sampling frame. It cannot claim clinical effectiveness, causal determinants, or national representativeness without matching design evidence.

### Codex Stage Guidance

- scout: Inventory survey instruments, denominator, stakeholder groups, timepoints, and geography.
- idea: Test whether harmonization supports trend, subgroup, or guideline-correspondence routes.
- decision: Require explicit claim boundaries around representativeness and causality.
- analysis-campaign: Build harmonization, denominator, trend, subgroup, and guideline matrices first.
- review: Prepare response around sampling, response bias, harmonization, and overclaiming.

### Source Refs

- human_doc | docs/policies/study-workflow/study_archetypes.md#survey_trend_analysis | first_generation_route_seed

## publication_route_memory_seed__external_validation_rescue

Status: active_seed
Route family: external_validation_or_model_update
Stage applicability: scout, idea, analysis-campaign, review
Title: Weak internal effect can be rescued by validation, transportability, or model-update framing when clinically grounded

### Summary

Consider a rescue route when the planned discovery claim is weak but the endpoint, cohort, and decision context remain clinically important. The rescue should shift the paper toward validation, recalibration, transportability, or clinically interpretable model updating rather than inflating a weak internal effect.

### Best Fit

- The original analysis underperforms but the clinical question remains relevant.
- An external cohort, temporal split, literature model, or local-to-external comparison is available.
- Calibration or decision utility can explain why updating matters.
- The revised claim can be written as validation or transportability instead of discovery.

### Poor Fit

- No independent or temporal validation signal exists.
- Endpoint and predictor definitions cannot be harmonized.
- The rescue would hide rather than disclose a failed primary path.

### Minimum Evidence Package

- Failed or weak internal path recorded as provenance.
- External, temporal, or literature-model validation plan.
- Calibration, updating, and utility evidence if model performance changes.
- Claim rewrite that clearly downgrades discovery language.
- Controller decision or closeout receipt preserving the route switch.

### Analysis Pattern

- Do not delete the weak path; preserve it as failed-path evidence.
- Reframe contribution around transportability, recalibration, or update value.
- Compare original and rescued route evidence transparently.
- Use external validation before adding more model complexity.

### Table Figure Pattern

- Original weak-path summary table.
- External or temporal validation performance table.
- Calibration before/after rescue plot.
- Decision utility or subgroup transportability figure.
- Route-switch rationale table linking evidence to claim downgrade.

### Reviewer Risks

- Reviewer sees the rescue as post hoc if the weak path is hidden.
- Reviewer asks for calibration or clinical utility after recalibration.
- Reviewer challenges external cohort comparability.
- Reviewer says revised claim still reads as discovery.

### Pivot Or Stop Rules

- Pivot to negative-result stop-loss if validation or recalibration cannot support a restrained claim.
- Pivot to standard external-validation route if source model and target cohort are clean.
- Stop if all rescue evidence depends on the same weak internal signal.

### Example Signals

- Internal AUC is modest but external calibration drift is clinically informative.
- A literature score performs differently in a local cohort.
- Temporal validation reveals case-mix change worth reporting.

### Failure Modes

- No independent cohort or temporal split can support transportability.
- Calibration or clinical utility evidence is absent.
- The revised claim still reads as discovery rather than validation.
- Failed original path is omitted from provenance.

### Claim Boundary

A rescue route can claim that a model, score, or clinical signal was externally evaluated, recalibrated, or bounded after weak discovery evidence. It cannot claim the original discovery is positive unless current evidence supports that separately.

### Codex Stage Guidance

- scout: Look for external, temporal, or source-model material before declaring the route dead.
- idea: Compare rescue framing against stop-loss and new-route scouting.
- decision: Require failed-path provenance and claim-downgrade language.
- analysis-campaign: Generate validation, calibration, and route-switch evidence before writing.
- review: Be ready to explain why this is transparent validation, not post hoc spin.

### Source Refs

- human_doc | docs/policies/study-workflow/publication_route_memory_policy.md#writeback | policy_seed
