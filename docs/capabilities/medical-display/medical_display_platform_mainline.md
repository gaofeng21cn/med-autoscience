# Medical Display Platform Mainline

This document is the authoritative mainline charter and operating model for the medical display platform in `med-autoscience`.

Use this file when the question is:

- what the display mainline is ultimately trying to accomplish;
- how long-horizon display work should advance without losing context;
- how current paper work, platform hardening, and future family expansion should relate;
- when the active display round should continue, hand off, or stop.

For the current baseline-completion provenance across `A-H`, see [medical_display_family_baseline_program.md](./medical_display_family_baseline_program.md).

For the top-level evidence roadmap, see [medical_display_family_roadmap.md](./medical_display_family_roadmap.md).

For the strict audited engineering truth, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

For the generated template inventory, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).

For the paper-facing visual review discipline above deterministic contracts, see [medical_display_visual_audit_protocol.md](./medical_display_visual_audit_protocol.md).

For the package architecture that separates template-library evolution from host-platform development, see [medical_display_template_pack_architecture.md](./medical_display_template_pack_architecture.md).

For the tracked active execution surface that replaces retired project-local runtime state, see [medical_display_active_board.md](./medical_display_active_board.md).

Historical OMX / Codex materials under [`docs/history/omx/`](../../history/omx/README.md) remain audit provenance only. They must not be treated as the current execution surface.

## North Star

The display mainline exists to make `med-autoscience` a stable paper-facing platform for medical figures and tables.

That means:

1. recurring manuscript display needs should become reusable audited platform capabilities;
2. deterministic contracts should prevent low-quality outputs from passing unnoticed;
3. AI-first visual review should keep pushing the platform toward stronger paper-facing quality;
4. every meaningful improvement should be traceable back to real paper delivery, not abstract template counting.

The goal is not "draw more figures."

The goal is "deliver publishable medical paper displays through a stable, extensible platform."

## Current Operating Reality

The current long-run operating reality is not "full maturity everywhere."

It is:

- the first audited-baseline coverage across `A-H` is already complete;
- the display mainline should now stay in rolling hardening, visual audit, and paper-driven strengthening;
- historical baseline-completion milestones remain provenance, not the current program identity.

The authoritative baseline-completion provenance lives in [medical_display_family_baseline_program.md](./medical_display_family_baseline_program.md).

That means the mainline now has three distinct layers of truth:

1. a permanent platform north star;
2. a current rolling-hardening operating mode;
3. historical baseline-completion provenance across `A-H`.

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

### 6. Continuous autonomous continuation is the default

Within the display-only scope, the active display round should continue automatically across phases.

It should not stop just because:

- one owner round reached merge-back ready;
- one visual-audit round closed;
- one family crossed a milestone.

The default is to continue.

Only hard blockers, truth conflicts, or genuine user-priority decisions should stop the line.

## Lane Model

The display mainline uses four lane types.

### 1. Mainline controller lane

Responsibilities:

- maintain the tracked long-horizon charter and active-board surface;
- route the active display round to the correct current phase;
- keep the taxonomy and baton logic coherent;
- prevent retired project-local runtime state or stale historical docs from reviving closed lines.

Write scope:

- `docs/capabilities/medical-display/medical_display_platform_mainline.md`
- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- other tracked display docs only when the audited truth changes

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

## Operating Modes

The mainline may move through the following recurring operating modes.
They are routing modes for continuous execution, not the long-run identity of the platform.

### Phase 0: Truth Intake And Routing

Use when:

- a new owner worktree starts;
- reports and working tree disagree;
- old prompts may be contaminating the current route;
- multiple candidate truths exist.

Required outputs:

- active owner lane identified;
- current truth surfaces identified;
- current operating mode identified;
- next highest-value continuation path refreshed.

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
- explicit statement of the next active operating mode or blocker state.

## Autonomous Routing Priority

When multiple reasonable next actions exist, the default priority order is:

1. finish the currently active hardening or audit round cleanly;
2. finish required integration and merge-back;
3. perform visual audit if freshly integrated outputs still need formal paper-facing review;
4. if any `A-H` family still lacks a first audited baseline, onboard that missing family next;
5. otherwise, harden the weakest or most paper-relevant family.

This rule is what turns the display mainline from a sequence of isolated tasks into a continuous program.

## What "Excellent" Looks Like

The display mainline should eventually look like this:

1. recurring paper display families are covered by audited templates or shells;
2. lower-bound defects are routinely caught before paper-facing review;
3. AI-first visual audit is a normal quality loop, not an emergency rescue step;
4. each real paper either:
   - uses an existing family cleanly; or
   - leaves behind a stronger audited family after closure;
5. the active display round can continue across phases without repeatedly losing the plot.

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

The current completion-program scoreboard is broader than that nucleus:

- `A/B/H` are the deepest currently hardened families;
- `C/D/E/F/G` already have first audited baselines, but remain thinner;
- the first-baseline completion target across `A-H` is now met, so continuation should shift to rolling hardening / visual-audit / paper-driven family strengthening rather than parking.

## Stop Conditions

The mainline should only stop when at least one of the following is true:

1. a real truth conflict exists:
   - paper-owned inputs, study truth, reports, or rendered outputs disagree in a way that cannot be resolved locally;
2. the next continuation path requires a genuine human priority or scope decision;
3. an external blocker prevents truthful continuation even though the current round has already been integrated.

Stopping because "one round of figures passed" is not enough.

## Change Protocol

When display work advances, the following should be kept coherent:

- this mainline charter;
- [medical_display_active_board.md](./medical_display_active_board.md);
- [medical_display_family_roadmap.md](./medical_display_family_roadmap.md);
- [medical_display_audit_guide.md](./medical_display_audit_guide.md);
- [medical_display_template_catalog.md](./medical_display_template_catalog.md);
- the tracked current-round execution notes;
- the active owner worktree itself.
