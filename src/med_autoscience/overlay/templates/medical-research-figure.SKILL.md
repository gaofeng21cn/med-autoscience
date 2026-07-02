---
name: figure
description: Use when a MedAutoScience paper line needs a new or materially repaired manuscript figure from figure intent through evidence refs, panel plan, render, visual QA, polish, and reviewer handoff.
---

# Figure

Use this skill when a paper-facing figure needs to be created or materially repaired from zero to one.

This is the MAS-owned main figure skill. `medical-research-figure-polish` is only the polish/review phase entry for an already scoped figure; it is not an independent authority source.

## Skill-First Operating Model

Use `medical-research-figure` as the owner skill for zero-to-one figure work. External design systems, including Nature Figure-style figure planning and K-Dense-style manifest and QA ideas, are reference material only.

The operating path is skill-first + Tool/Fabric execution + Domain Owner Gate:

- the MAS owner skill decides figure intent, claim scope, evidence fit, panel structure, renderer choice, and route outcome
- tools, scripts, OPL Connect, Fabric, or ScholarSkills display material execute bounded searches, renders, manifest checks, or QA tasks
- MAS owner surfaces decide whether the candidate is accepted, routed back, blocked, or sent to a human gate

Do not introduce a parallel `opl-scholar-display` main entry. Use ScholarSkills display refs only as enhancement or reference material inside the MAS owner path.

## Core Principle

Medical figures are evidence surfaces. This is an AI-first workflow: the AI executor owns the scientific figure reasoning first, including what claim the figure should support, which evidence refs are allowed, what each panel means, and whether the rendered result can survive reviewer scrutiny.

Scripts are render and check tools. They may materialize plots, run deterministic checks, export files, or collect layout metadata. They must not decide the claim, invent evidence, silently switch backend, or turn a local render into MAS owner authority.

## MAS Authority Boundary

Use MAS owner surfaces before declaring a figure accepted:

- `paper/claim_evidence_map.json`
- `paper/evidence/evidence_ledger.json`
- `paper/display_registry.json`
- `paper/figure_semantics_manifest.json`
- `paper/figure_polish_lifecycle.json`
- visual-audit receipt, review ledger, publication eval, controller decision, owner receipt, typed blocker, or human gate surfaces when present

Do not write or imply authority through chat text, local preview files, renderer logs, template catalog matches, ScholarSkills refs, or provider completion. Do not directly write `publication_eval/latest.json`, `controller_decisions/latest.json`, owner receipts, typed blockers, human gates, `current_package`, runtime queues, provider attempts, or Yang authority.

## AI-First Workflow

### Figure Intent And Claim

Start by writing the figure intent in plain scientific terms:

- figure id or proposed figure id
- manuscript location or role
- target claim, reviewer concern, or descriptive question
- clinical or scientific comparison the reader must understand
- what the figure must not claim

If the claim is missing, too broad, or not accepted by MAS evidence surfaces, route to `write`, `review`, `analysis-campaign`, `decision`, or human gate before drawing.

### Evidence Refs

Bind the figure to concrete refs before choosing a visual form:

- data or cohort ref
- analysis, statistic, or model-output ref
- claim-evidence ref
- display registry or figure semantics ref when present
- prior reviewer concern or route reason when the figure is a repair

Missing refs are blockers, not styling issues. Do not fill missing evidence with template defaults, synthetic labels, or caption prose.

If the figure needs background, guideline, reporting-methods, primary-source, PMID, DOI, or citation support for its caption, methods note, or reviewer handoff, get candidate refs through one of these paths:

- `opl connect pubmed search --query <query> --limit <n> --json`
- an external `medical-research-lit` specialist

Use the returned normalized refs only as inputs to MAS evidence, citation, and review workflows. This skill still owns screening, figure relevance, claim-evidence mapping, and the final MAS route decision. If the connector is unavailable, record a route-back or `connector_gap`; do not invent citations, PMIDs, DOIs, guidelines, or source metadata.

### Panel Plan

Plan panels as scientific units, not decorations. For every panel, name:

- panel id
- supported claim or sub-question
- required variables and units
- comparison hierarchy
- statistical annotation or uncertainty requirement
- expected visible text and what must stay in the caption or manifest

Keep in-figure text limited to panel labels, axis labels, legend labels, necessary statistical annotations, and minimal cohort or group notes.

Use progressive disclosure in the reviewer packet: keep the visible figure minimal, put panel intent and statistical decisions in the manifest, and leave longer caveats to the caption, review ledger, or route-back note.

### Template And Backend Selection

Choose the figure grammar after intent and refs are clear.

- Prefer MAS Display Pack and paper-local figure grammar for paper-facing evidence figures.
- Use ScholarSkills display refs as enhancement pack or reference material, not as MAS owner authority.
- Prefer `r_ggplot2` for manuscript evidence figures when the current display contract supports it.
- Use `python` or `html_svg` only when the figure class and contract allow it.
- If the selected backend cannot run, stop and fix the environment or route a blocker. Do not silently fallback to a different renderer family.

Template selection should explain why the template fits the claim, panel semantics, evidence shape, and journal-facing readability.

Record the selected grammar in a figure manifest before polishing. The manifest should name the figure intent, panel ids, evidence refs, statistics and annotations, renderer family, exports, QA checks, and owner-gate status.

### Draft Render

Render the first draft through a deterministic script or MAS display command when available.

Record:

- source data ref
- render script or command
- renderer family
- output paths
- sidecar or lock refs
- known limitations of the draft

The first render is a draft, not acceptance.

### Visual QA

Open the rendered output and inspect the actual figure, not only logs or code.

Check:

- whether the main comparison is obvious in a few seconds
- labels, units, sample sizes, uncertainty, and baselines
- panel order and visual hierarchy
- color accessibility and grayscale robustness
- text size after likely manuscript scaling
- overlap, truncation, clipped legends, duplicate titles, and prose cards
- whether every visible claim is supported by the evidence refs

If the figure fails evidence integrity, route back. If it fails presentation, continue to polish.

The QA pass should be manifest-backed: every failed check must either be fixed, downgraded to a named caveat, routed back to the correct owner, or carried as a human gate.

### Polish

Use polish for presentation-only repair: layout, labels, ordering, sizing, palette, spacing, legends, export settings, and manuscript-safe visible text.

Polish must not change data, statistics, cohort labels, model results, claim strength, or manuscript methods labels. When a requested polish would change meaning, route to `analysis-campaign`, `write`, `review`, `decision`, or human gate.

### Reviewer Handoff

Before handoff, produce a compact reviewer packet:

- figure intent and supported claim
- evidence refs and data/statistics refs
- panel plan
- selected template/backend and why it fits
- draft/final export refs
- visual QA findings and fixes
- remaining caveats, blockers, or human decisions
- next MAS route

The reviewer handoff is candidate evidence. MAS owner surfaces still decide whether the figure is accepted, routed back, blocked, or ready for downstream package work.
