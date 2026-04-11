# Medical Display Visual Audit Protocol

This document defines the formal AI-first visual audit protocol for the medical display platform in `med-autoscience`.

Use this file when the question is:

- how paper-facing figure review should happen after deterministic generation;
- what should count as a visual-audit finding;
- when a finding stays paper-local versus being promoted into platform truth;
- how the active Codex execution lane should keep improving visual quality without falling back to hidden patches or heuristics.

This protocol sits above the audited deterministic layer described in [medical_display_audit_guide.md](./medical_display_audit_guide.md).

It does not replace renderer contracts, schema contracts, layout QC, or manuscript-facing validation.

## Purpose

Templates and deterministic QC protect the lower bound.

Visual audit exists because some paper-facing quality judgments are hard to encode perfectly in advance, including:

- balance and spacing;
- local crowding;
- annotation placement quality;
- arrow placement quality;
- panel-level visual hierarchy;
- figure-level visual rhythm;
- article-level palette or style coherence.

The protocol exists to make those judgments explicit, reviewable, and promotable back into formal platform truth where appropriate.

## Canonical Truth Surface

Visual audit must inspect real rendered outputs, not only manifests, catalog rows, or textual reports.

The canonical paper-facing inspection surfaces are:

- `paper/figures/generated/`
- `paper/tables/generated/` when table rendering/readability matters;
- `paper/submission_minimal/` when packaging structure affects delivery interpretation;
- `manuscript/` as the human-facing mirror when applicable.

The following supporting surfaces remain important, but they are not sufficient by themselves:

- `paper/publication_style_profile.json`
- `paper/display_overrides.json`
- template catalogs;
- QC results;
- gate status reports.

## Entry Conditions

Visual audit should start when all of the following are true:

1. the figure or table has been generated through the audited path;
2. the relevant deterministic checks have already run;
3. the actual rendered output exists on the canonical paper-facing surface.

Visual audit may also reopen after deterministic hardening if:

- a human flags paper-facing issues;
- a new article-level style truth changes the expected appearance;
- a previously accepted visual compromise is no longer acceptable for the paper.

## Review Targets

Visual audit should explicitly look for at least the following classes of problems:

### 1. Composition and hierarchy

- panel balance;
- empty-space usage;
- panel header hierarchy;
- figure-level rhythm;
- callout and caption alignment with the visual story.

### 2. Readability

- overlapping text or marks;
- labels that are technically present but visually hard to read;
- legend density or poor grouping;
- axis windows that are technically valid but visually wasteful;
- titles or annotations competing for the same space.

### 3. Semantic presentation quality

- misleading grouping emphasis;
- poor ordering communication;
- confusing legend semantics;
- visually ambiguous arrow or callout direction;
- article-level palette drift from paper truth.

### 4. Manuscript-facing contract quality

- mismatch between how the figure is used in the manuscript and what the visual actually emphasizes;
- unnecessary figure-level titles when policy expects only panel titles;
- surface inconsistencies between generated outputs and submission-facing packaging.

## Required Finding Format

Every visual-audit finding should be recorded in a concrete, reviewable format.

Use the following fields:

- `artifact`
  - exact figure/table identifier and path
- `observed_issue`
  - what is visibly wrong
- `paper_facing_impact`
  - why this matters for publication quality
- `suspected_layer`
  - one or more of:
    - `paper_input`
    - `display_override`
    - `publication_style_profile`
    - `renderer_contract`
    - `layout_qc`
    - `readability_qc`
    - `manuscript_surface`
- `proposed_action`
  - what should change next
- `promotion_decision`
  - one of:
    - `paper_local_only`
    - `promote_to_contract`
    - `promote_to_qc`
    - `promote_to_golden_regression`
    - `needs_human_decision`
- `verification_plan`
  - how the finding will be checked after revision

Avoid vague findings such as:

- "looks weird"
- "maybe adjust spacing"
- "could be prettier"

The critique should be specific enough to drive an actual revision step.

## Revision Logic

Once a finding is logged, the expected response order is:

1. determine whether the problem is paper-local or reusable;
2. fix the narrowest correct layer;
3. rerender the figure through the audited path;
4. re-run the relevant deterministic checks;
5. re-run visual audit on the new output.

Preferred correction surfaces are:

- paper-owned input truth;
- structured display overrides;
- article-level style profile;
- renderer logic;
- layout/readability QC;
- golden regressions.

Do not treat hidden post-processing as the normal response.

## Promotion Rules

A visual finding should be promoted into platform truth when at least one of the following is true:

1. the same defect can recur across papers or templates;
2. the defect reflects a renderer or contract weakness rather than one paper's unique story choice;
3. the defect is clear enough to express as a deterministic invariant or regression expectation;
4. the defect reveals a stable style-policy requirement, such as title policy or palette obedience.

A finding may remain paper-local when:

- it is genuinely article-specific;
- it does not indicate reusable renderer or QC weakness;
- it depends on manuscript narrative choices that should stay paper-owned.

## Acceptance Standard

A figure or table should only be treated as paper-ready when both layers are satisfied:

1. the deterministic audited layer is clear;
2. the visual-audit finding set is either:
   - resolved;
   - intentionally accepted by a human with the tradeoff made explicit.

Therefore:

- `gate clear` is necessary;
- `visual audit clear` is the paper-facing completion signal.

## What Not To Do

Visual audit must not degrade into:

- silent patching outside the audited path;
- hand-made cleanup that never feeds back into formal surfaces;
- heuristic post-processing that hides renderer defects;
- figure approval based only on manifests or tests without looking at the image.

## Minimal Loop For Codex Runtime

The expected loop for Codex runtime is:

1. generate the display through the audited path;
2. inspect the actual output image;
3. write concrete critique findings;
4. classify each finding by layer and promotion decision;
5. revise the correct surface;
6. rerender and recheck;
7. stop only when the finding set is closed or explicitly handed upward.
