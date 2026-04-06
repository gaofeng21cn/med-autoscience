# Medical Display Platform Mainline

This document is the authoritative mainline charter and operating model for the medical display platform in `med-autoscience`.

Use this file when the question is:

- what the display mainline is ultimately trying to accomplish;
- how long-horizon display work should advance without losing context;
- how current paper work, platform hardening, and future family expansion should relate;
- when an OMX lane should continue, hand off, or stop.

For the top-level evidence roadmap, see [medical_display_family_roadmap.md](./medical_display_family_roadmap.md).

For the strict audited engineering truth, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

For the generated template inventory, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).

For the paper-facing visual review discipline above deterministic contracts, see [medical_display_visual_audit_protocol.md](./medical_display_visual_audit_protocol.md).

## North Star

The display mainline exists to make `med-autoscience` a stable paper-facing platform for medical figures and tables.

That means:

1. recurring manuscript display needs should become reusable audited platform capabilities;
2. deterministic contracts should prevent low-quality outputs from passing unnoticed;
3. AI-first visual review should keep pushing the platform toward stronger paper-facing quality;
4. every meaningful improvement should be traceable back to real paper delivery, not abstract template counting.

The goal is not "draw more figures."

The goal is "deliver publishable medical paper displays through a stable, extensible platform."

## Stable Operating Model

The display mainline always operates across three layers:

1. **Paper Family**
   - the manuscript-facing evidence question;
   - the stable long-horizon target, organized as `A-H`.
2. **Audit Family**
   - the engineering governance layer;
   - the place where renderer structure, schema shape, and QC risks are managed.
3. **Template Instance**
   - the concrete implementation artifact;
   - the place where a template ID, input schema, renderer family, QC profile, and exports are defined.

Those layers must remain aligned, but they must not collapse into one taxonomy.

## Core Principles

### 1. Publication service comes first

Every display decision is subordinate to manuscript delivery quality.

This platform exists for:

- paper-facing evidence presentation;
- submission-safe and manuscript-safe packaging;
- repeatable paper-quality figure and table delivery.

It does not exist to maximize template count, renderer novelty, or catalog breadth for its own sake.

### 2. Real papers drive maturity

The platform should grow by absorbing recurring needs from real papers.

The expected loop is:

1. a paper needs a figure or table family;
2. the figure is made to pass real paper review;
3. the reusable part is promoted into audited platform truth;
4. later papers inherit that capability at a higher baseline.

### 3. Deterministic lower bound, AI-first upper bound

Deterministic contracts are responsible for the lower bound:

- schema validation;
- renderer contracts;
- layout QC;
- catalog and packaging consistency;
- manuscript-facing safety checks.

AI-first visual review is responsible for the upper bound:

- actual image inspection;
- localized readability and balance judgment;
- crowding and composition critique;
- article-level style coherence;
- figure-specific paper-facing refinement.

The AI-first layer is a formal review loop, not a hidden patching step.

### 4. Gate clear is necessary, not sufficient

`medical-reporting-audit`, `publication-gate`, catalog completeness, and submission-manifest consistency are required.

They do not by themselves prove that a figure is paper-ready.

A figure family is only mature when:

- the audited path is stable;
- deterministic QC catches known lower-bound failures;
- real rendered outputs survive visual review.

### 5. No heuristic cleanup backdoors

The platform must not rely on:

- silent post-processing fixes;
- one-off local nudges that are not promoted to a formal contract surface;
- heuristic masking of renderer defects;
- manual memory as the real source of truth.

## Lane Model

The display mainline uses four lane types.

### 1. Mainline controller lane

Responsibilities:

- maintain the long-horizon prompt/report/control surface;
- route OMX to the correct current phase;
- keep the taxonomy and baton logic coherent;
- prevent old prompts or stale statuses from reviving closed lines.

Write scope:

- `.omx/context/*`
- `.omx/reports/medical-display-mainline/*`

### 2. Owner implementation lane

Responsibilities:

- make tracked code and tracked-doc changes for the currently active display phase;
- own the shared write set for core implementation work;
- run focused verification and worktree-local reporting.

Default mode:

- `ralph` outer loop;
- `leader-only / single-lane` for core implementation.

### 3. Visual audit lane

Responsibilities:

- inspect real rendered outputs after deterministic generation;
- produce concrete paper-facing critique;
- separate lower-bound failures from upper-bound refinement findings;
- recommend what should be promoted into renderer/QC/input/override/test truth.

Default mode:

- read-only unless explicitly handed ownership of a disjoint write set.

### 4. Bounded verification lane

Responsibilities:

- focused regression verification;
- inventory checks;
- read-only auditing;
- limited, disjoint support tasks.

Default mode:

- `team` only when write sets are clearly non-overlapping.

## Phase Map

The mainline should progress through the following phases.

### Phase 0: Truth Intake And Routing

Use when:

- a new owner worktree starts;
- reports and working tree disagree;
- old prompts may be contaminating the current route;
- multiple candidate truths exist.

Required outputs:

- active owner lane identified;
- current truth surfaces identified;
- current phase identified;
- `NEXT_BATON` refreshed.

### Phase 1: Paper-Proven Baseline Harvest

Use when:

- one or more real papers have already proven stable figure/table capabilities;
- those capabilities need to be made explicit as platform truth.

Required outputs:

- stable paper-proven baseline statement;
- explicit mapping from paper family to audit family to template instance;
- gap list derived from real paper evidence.

### Phase 2: Cross-Paper Deterministic Hardening

Use when:

- a paper-proven capability exists;
- known failures should become enforceable lower-bound rules.

Typical work:

- renderer tightening;
- schema tightening;
- layout/readability QC;
- golden regression suites;
- catalog or contract sync.

Exit criteria:

- new deterministic truth is landed or clearly merge-back ready;
- repeated lower-bound failures are caught automatically.

### Phase 3: AI-First Visual Audit And Revise

Use when:

- deterministic generation is already in place;
- actual rendered figures still need paper-facing review;
- some quality questions remain too figure-specific or visual to encode up front.

Typical work:

- inspect actual generated images;
- log concrete critique points;
- decide whether each point is:
  - a paper-local refinement;
  - a reusable platform issue to promote downward into contracts/QC/tests.

Exit criteria:

- critique set is either resolved or intentionally accepted by a human;
- reusable failures are promoted into the deterministic layer where justified.

### Phase 4: New Family Onboarding By Real Paper Demand

Use when:

- the next paper requires a family that is not yet mature enough.

Required outputs:

- paper demand anchor;
- new or expanded audit family coverage;
- promoted template instances;
- regression and visual-review evidence.

### Phase 5: Integration, Merge-Back, And Monitor

Use when:

- the current owner lane is clean or merge-back ready;
- the in-flight hardening round is complete enough to integrate;
- the line can shift from active writing to monitored steady state.

Required outputs:

- integration evidence;
- clean handoff notes;
- updated mainline reports;
- explicit statement of the next active phase.

## What "Excellent" Looks Like

The display mainline should eventually look like this:

1. recurring paper display families are covered by audited templates or shells;
2. lower-bound defects are routinely caught before paper-facing review;
3. AI-first visual audit is a normal quality loop, not an emergency rescue step;
4. each real paper either:
   - uses an existing family cleanly; or
   - leaves behind a stronger audited family after closure;
5. OMX can continue across phases without repeatedly losing the plot.

In short:

- the lower bound is stable;
- the upper bound keeps improving;
- the route stays tied to real paper delivery.

## Current Proven Baseline

The current paper-proven baseline begins with `A/B/H`, derived from the already absorbed anchor-paper work.

This baseline currently proves that the platform can already support, at minimum:

- predictive-performance and decision evidence;
- time-to-event discrimination, calibration, grouped separation, and grouped summaries;
- multicenter generalizability and publication shell surfaces.

That baseline is not the end state.

It is the first durable nucleus for the long-horizon platform.

## Stop Conditions

The mainline should only stop when at least one of the following is true:

1. a real truth conflict exists:
   - paper-owned inputs, study truth, reports, or rendered outputs disagree in a way that cannot be resolved locally;
2. the current phase is fully landed and the next phase requires a human scope decision;
3. the current owner lane has reached a clean integration boundary and the next baton has already been written down.

Stopping because "one round of figures passed" is not enough.

## Change Protocol

When display work advances, the following should be kept coherent:

- this mainline charter;
- [medical_display_family_roadmap.md](./medical_display_family_roadmap.md);
- [medical_display_audit_guide.md](./medical_display_audit_guide.md);
- [medical_display_template_catalog.md](./medical_display_template_catalog.md);
- the active `.omx` mainline control surface;
- the active owner worktree reports.
