# Research Route Bias Policy

Status: `active first-generation route memory seed`
Owner: `MedAutoScience`
Purpose: Markdown-first canonical body for research-route bias prose injected into MAS stage overlay context.
State: first-generation route bias / contract input; full publication-route domain memory lives in `publication_route_memory_library.md`.
Machine boundary: Python loads and validates this Markdown for overlay rendering and profile policy validation. This document does not score routes, choose the winning study line, authorize publication quality, or replace controller decisions.

默认 `research_route_bias_policy = "high_plasticity_medical"`。

这套 policy 用来把医学课题的路线选择前移到 `scout / idea / decision`。它保留的是给 Codex 参考的自然语言经验，不是程序化 route scorer。

## high_plasticity_medical

Title: High-plasticity medical publication bias

### Preferred Route Order

- supervised prediction or risk-stratification routes with clinically interpretable downstream analyses
- subtype-reconstruction routes that can be converted into clinically legible subgroup stories or subtype recognizers
- routes that can absorb external public data for validation, extension, or mechanism/context support
- gray-zone triage routes when they can change workflow, testing, or follow-up decisions even without dramatic AUC gains
- LLM / agent tasks only when the task can be bounded, benchmarked fairly, and translated into a medical paper package
- routes that can naturally produce a full paper-facing evidence package rather than a single fragile association
- fixed-factor clinical association routes only when prior evidence or clinical importance is unusually strong

### Candidate Scoring Dimensions

- clinical significance if the result is positive
- controllability of the downstream paper path
- room for iterative model/package refinement
- public-data extensibility
- likely figure/table depth for a Q2+ medical paper
- whether the route can survive a moderate rather than spectacular main effect

### Downrank Patterns

- the main value would hinge on one fixed clinical factor being significant
- a negative result would leave little room for branching or rescue
- the likely paper would have weak clinical utility even if the analysis is technically clean
- the route cannot be expanded beyond a thin association table and discussion
- an LLM / agent route is framed too broadly to benchmark rigorously against clinician-relevant baselines

### Public Data Rules

- Use public data when it can materially add external validation, cohort extension, or biological/context support.
- Do not add public data only as decorative workload.

### Stage Openers

- intake-audit: When auditing an in-flight medical quest, explicitly judge whether the current line still has a controllable path to a publishable paper rather than merely a path to more execution.
- scout: When the quest is a medical-data paper line, do not treat all reasonable frames as equally good scouting outputs. Prefer frames that are more controllable for publication and more extensible for downstream evidence-building.
- baseline: For medical-data quests, baseline work should preserve a strong paper route rather than turning into endless comparator reproduction with little downstream clinical utility.
- idea: For medical-data quests, treat publishability controllability as a first-class selection criterion. Do not prefer a route merely because it is clinically familiar or easy to describe.
- decision: For medical-data quests, route selection should explicitly favor lines with a more controllable path to a publishable paper. In practice, prefer routes that preserve room for meaningful iteration, richer paper packaging, and clinically legible utility.
- experiment: For medical-data quests, main experiments should be judged by the strength of the eventual paper package, not only by a single discrimination number or an engineering-style benchmark win.
- analysis-campaign: For medical-data quests, follow-up campaigns should preferentially build publication-strength evidence packages such as utility, subgroup, explainability, or external-validation support rather than tiny metric-chasing loops.

### Stage Questions

- intake-audit: is the current strongest line still clinically meaningful if the main effect is only moderate?
- intake-audit: does the current line still preserve room for a classifier, subtype, utility, or public-data extension package?
- intake-audit: would continuing this line mostly package weak evidence, or can it still build stronger evidence efficiently?
- baseline: which baseline route best preserves a clinically interpretable and publishable comparison surface?
- baseline: is the baseline path helping the paper route, or just consuming time on low-yield reproduction?
- decision: which route is most likely to support a clinically meaningful classifier / risk-stratification / utility package?
- decision: which route could support a subtype-reconstruction or gray-zone triage story if the main discriminative gain is only moderate?
- decision: which route leaves room for calibration, subgroup, explainability, and external-validation expansion?
- decision: for LLM / agent tasks, is the task narrow enough to benchmark cleanly and clinically?
- decision: which route can still branch productively if the first main result is only moderate rather than striking?
- decision: which route is most likely to accumulate enough figure/table depth for a Q2+ medical manuscript?
- experiment: if this run is positive, does it naturally open calibration, utility, subgroup, explainability, or external-validation follow-up?
- experiment: if this run is only moderate, is there still a credible medical-paper route rather than a dead end?
- experiment: is the experiment package clinically legible, or mostly an engineering comparison with weak bedside meaning?
- analysis-campaign: which follow-up analyses would materially improve publication strength rather than only decorate workload?
- analysis-campaign: are we spending compute on clinically meaningful utility and heterogeneity checks, or on low-yield metric drift?
