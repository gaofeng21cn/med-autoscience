# Medical Display Family Baseline Program

This document defines the current long-horizon completion program for the medical display platform in `med-autoscience`.

Use this file when the question is:

- what the current display program is trying to complete across `A-H`;
- what should count as "enough coverage" for a paper family in the current long run;
- how the active Codex execution lane should continue automatically after the current owner round finishes;
- when the platform should keep hardening an existing family versus opening a missing one.

For the top-level family roadmap, see [medical_display_family_roadmap.md](./medical_display_family_roadmap.md).

For the mainline operating model, see [medical_display_platform_mainline.md](./medical_display_platform_mainline.md).

For the strict audited engineering truth, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

## Program Target

The milestone defined by this document is:

**every `A-H` paper family should have at least one end-to-end audited baseline.**

That milestone is already complete.

It is intentionally:

- narrower than "every family is fully mature";
- broader than "the current owner round is done";
- more concrete than a generic desire to "keep improving displays."

## What Counts As A First Audited Baseline

A paper family counts as having reached its first audited baseline only when all of the following are true for at least one family-aligned display surface:

1. the family has at least one template, shell, or table that is implemented end to end under the audit guide definition;
2. that surface is clearly mappable from:
   - `Paper Family`
   - to `Audit Family`
   - to `Template Instance`;
3. the surface can be materialized through the registered audited path;
4. the result survives catalog and manuscript-facing contract checks;
5. the family is no longer pretending to be covered only through loosely related neighboring templates.

This definition is deliberately stronger than "there is something vaguely similar in the registry."

It is also deliberately weaker than "the whole family is already paper-perfect."

## Important Distinction

Three statements can all be true at once:

1. a family already has a first audited baseline;
2. that family is still only `partial` at the roadmap level;
3. that family still needs substantial hardening or visual-review work.

So:

- `first audited baseline` is the current completion metric for this program;
- `partial` roadmap status still matters;
- later hardening work does not mean the first baseline was fake.

## Current Scoreboard

The current best-grounded baseline scoreboard is:

| Paper Family | First Audited Baseline | Current Program State | Current Notes |
| --- | --- | --- | --- |
| `A. Predictive Performance and Decision` | `yes` | `baseline_complete / hardening_active` | binary performance, decision, and composite panel evidence already audited |
| `B. Survival and Time-to-Event` | `yes` | `baseline_complete / hardening_active` | grouped survival, horizon, calibration, and risk-summary surfaces audited |
| `C. Effect Size and Heterogeneity` | `yes` | `baseline_complete / hardening_pending` | effect-estimate baseline exists through forest displays |
| `D. Representation Structure and Data Geometry` | `yes` | `baseline_complete / hardening_pending` | grouped embedding baseline exists |
| `E. Feature Pattern and Matrix` | `yes` | `baseline_complete / hardening_pending` | heatmap-style matrix baseline exists |
| `F. Model Explanation` | `yes` | `baseline_complete / hardening_pending` | explanation baseline exists, but remains thin |
| `G. Omics-Native Evidence` | `yes` | `baseline_complete / hardening_pending` | dedicated omics-native baseline now exists through `gsva_ssgsea_heatmap` |
| `H. Cohort and Study Design Evidence` | `yes` | `baseline_complete / hardening_active` | shells, tables, and generalizability surfaces exist |

In other words:

- current completion score is `8 / 8`;
- every `A-H` family now has a first audited baseline.

## Current Operating Implication

Because the milestone is already complete:

- this document is now baseline-completion provenance;
- the active display program should be understood as rolling hardening, visual audit, and paper-driven strengthening;
- the first-baseline scoreboard remains the lower coverage floor, not the current stopping rule.

## Execution Strategy

The user-approved execution strategy is:

1. keep `A-H` first-baseline coverage as the minimum coverage floor;
2. keep real paper demand as the default source of truth for what to build next;
3. do not reduce the program to a mechanical checklist;
4. but if a family remains completely missing and no higher-priority paper blocker is active, the active Codex execution lane should proactively onboard that missing family instead of parking.

This means:

- the old `A-H` coverage target remains the completed milestone floor;
- real-paper priority is still the execution policy.

## Default Continuation Order

The active Codex execution lane should continue in the following order unless a hard blocker overrides it:

1. finish the currently active owner round;
2. finish required integration / merge-back;
3. perform formal visual audit if the freshly integrated outputs still need paper-facing review;
4. if no urgent visual-audit reopen exists and any family still lacks a first audited baseline, open that missing family next;
5. once all `A-H` families have a first audited baseline, continue hardening the weakest or most paper-relevant family.

## Current Default Next Family

Now that `G` has its first audited baseline, the default next family should be:

- `F. Model Explanation`

unless one of the following is true:

1. the newly integrated `G` outputs require a formal `Phase 3` visual-audit round;
2. a harder cross-family deterministic gap is exposed in another weaker family;
3. a higher-priority real paper demand appears and clearly outranks proactive `F` hardening.

## Acceptable First-Baseline Shapes For `G`

The first audited `G` family baseline does not need to solve the whole omics universe.

It only needs one real, end-to-end, paper-credible omics-native baseline surface.

Acceptable candidates include:

- volcano plot;
- enrichment dot plot or bar plot;
- GSVA/ssGSEA heatmap;
- oncoplot;
- another omics-native display, if a real paper anchor justifies it more strongly.

The correct choice should still be driven by the strongest real anchor available at execution time.

## After `G` Is Over The Line

Once `G` reaches its first audited baseline:

1. the current completion program target across `A-H` is met;
2. the display mainline itself does **not** end;
3. the active Codex execution lane should shift to rolling hardening mode:
   - strengthen the weakest family;
   - keep improving deterministic lower-bound protection;
   - keep running visual audit where paper-facing quality demands it.

The most likely next weak families after `G` are:

- `F`
- `E`
- `D`
- `C`

but the exact order should remain paper-driven where possible.

## Autonomous Continuation Rule

Within the display-only scope, the active Codex execution lane should not stop at phase boundaries just because one baton succeeded.

It should continue automatically unless one of the following is true:

1. a hard blocker exists;
2. a scope decision genuinely requires the user;
3. the display truth surfaces conflict and cannot be reconciled locally.

If none of those are true, the active Codex execution lane should keep moving:

- from implementation to integration;
- from integration to visual audit;
- from visual audit to missing-family onboarding;
- from missing-family onboarding to the next hardening round.

## Stop Conditions

The current rolling-hardening program should only stop when at least one of the following is true:

1. a hard blocker prevents reliable continuation;
2. the next family or paper demand requires a user priority decision that cannot be inferred from current truth;
3. current truth surfaces conflict and cannot be reconciled locally.

## Governance Rule

If the docs appear to disagree:

1. [medical_display_family_roadmap.md](./medical_display_family_roadmap.md) defines the long-horizon family target model;
2. this document defines the current completion program across those families;
3. [medical_display_platform_mainline.md](./medical_display_platform_mainline.md) defines how the mainline executes;
4. [medical_display_audit_guide.md](./medical_display_audit_guide.md) defines the strict audited engineering truth.
