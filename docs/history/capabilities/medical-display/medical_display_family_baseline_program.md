# Medical Display Family Baseline Program

Owner: `MedAutoScience`
Purpose: `medical_display_history_record`
State: `history_provenance`
Machine boundary: 人读医学展示能力历史/provenance 记录。当前 medical-display 能力真相继续归 `docs/delivery/medical-display/`、template/renderer source、contracts、generated artifacts、tests 和 audit receipts。

This document preserves the completed first-baseline completion program for the medical display platform in `med-autoscience`.

Historical read rule: read this file as baseline-completion provenance. It records the `A-H` first audited baseline target and its continuation logic at the time it was active; it is not the current active board, current owner round, or current backlog.

Use this file when the question is:

- what first-baseline milestone was completed across `A-H`;
- what counted as "enough coverage" for that historical first-baseline program;
- how the historical Codex execution lane was expected to continue after an owner round;
- why current rolling hardening still treats the completed `A-H` baseline as a lower coverage floor.

For the top-level family roadmap, see [medical_display_family_roadmap.md](../../../delivery/medical-display/portfolio/medical_display_family_roadmap.md).

For the mainline operating model, see [medical_display_platform_mainline.md](../../../delivery/medical-display/contracts/medical_display_platform_mainline.md).

For the strict audited engineering truth, see [medical_display_audit_guide.md](../../../delivery/medical-display/contracts/medical_display_audit_guide.md).

## Program Target

The milestone defined by this document is:

**every `A-H` paper family should have at least one end-to-end audited baseline.**

That milestone is already complete.

It is intentionally:

- narrower than "every family is fully mature";
- broader than "the then-active owner round is done";
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

- `first audited baseline` was the completion metric for this historical program;
- `partial` roadmap status still matters;
- later hardening work does not mean the first baseline was fake.

## Completed Baseline Scoreboard

The completed first-baseline scoreboard is:

| Paper Family | First Audited Baseline | Historical Program State | Notes At Completion |
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

- completed first-baseline score is `8 / 8`;
- every `A-H` family now has a first audited baseline.

## Current Operating Implication

Because the milestone is already complete:

- this document is now baseline-completion provenance;
- the active display program should be understood as rolling hardening, visual audit, and paper-driven strengthening;
- the first-baseline scoreboard remains the lower coverage floor, not the current stopping rule.

## Historical Execution Strategy

The user-approved execution strategy for this completed first-baseline program was:

1. keep `A-H` first-baseline coverage as the minimum coverage floor;
2. keep real paper demand as the default source of truth for what to build next;
3. do not reduce the program to a mechanical checklist;
4. but if a family remained completely missing and no higher-priority paper blocker was active, the Codex execution lane should proactively onboard that missing family instead of parking.

For historical interpretation, this means:

- the old `A-H` coverage target remains the completed milestone floor;
- real-paper priority is still the execution policy.

## Historical Default Continuation Order

When this program was active, the Codex execution lane was expected to continue in the following order unless a hard blocker overrode it:

1. finish the then-active owner round;
2. finish required integration / merge-back;
3. perform formal visual audit if the freshly integrated outputs still need paper-facing review;
4. if no urgent visual-audit reopen exists and any family still lacks a first audited baseline, open that missing family next;
5. once all `A-H` families have a first audited baseline, continue hardening the weakest or most paper-relevant family.

## Historical Default Next Family

At the point this program completed `G` first-baseline coverage, the historical default next family was:

- `F. Model Explanation`

unless one of the following was true:

1. the newly integrated `G` outputs required a formal `Phase 3` visual-audit round;
2. a harder cross-family deterministic gap was exposed in another weaker family;
3. a higher-priority real paper demand appeared and clearly outranked proactive `F` hardening.

## Acceptable First-Baseline Shapes For `G`

The first audited `G` family baseline does not need to solve the whole omics universe.

It only needs one real, end-to-end, paper-credible omics-native baseline surface.

Acceptable candidates include:

- volcano plot;
- enrichment dot plot or bar plot;
- GSVA/ssGSEA heatmap;
- oncoplot;
- another omics-native display, if a real paper anchor justifies it more strongly.

The historical choice was expected to be driven by the strongest real anchor available at execution time.

## After `G` Is Over The Line

Once `G` reached its first audited baseline:

1. the first-baseline completion program target across `A-H` was met;
2. the display mainline itself does **not** end;
3. the Codex execution lane was expected to shift to rolling hardening mode:
   - strengthen the weakest family;
   - keep improving deterministic lower-bound protection;
   - keep running visual audit where paper-facing quality demands it.

The most likely next weak families after `G` are:

- `F`
- `E`
- `D`
- `C`

but the exact order was expected to remain paper-driven where possible.

## Historical Autonomous Continuation Rule

Within the historical display-only completion program, the Codex execution lane was not expected to stop at phase boundaries just because one baton succeeded.

It was expected to continue automatically unless one of the following was true:

1. a hard blocker exists;
2. a scope decision genuinely requires the user;
3. the display truth surfaces conflict and cannot be reconciled locally.

If none of those were true, the historical execution lane was expected to keep moving:

- from implementation to integration;
- from integration to visual audit;
- from visual audit to missing-family onboarding;
- from missing-family onboarding to the next hardening round.

## Historical Stop Conditions

The historical rolling-hardening continuation rule stopped only when at least one of the following was true:

1. a hard blocker prevents reliable continuation;
2. the next family or paper demand requires a user priority decision that cannot be inferred from current truth;
3. current truth surfaces conflict and cannot be reconciled locally.

## Governance Rule

If the docs appear to disagree:

1. [medical_display_family_roadmap.md](../../../delivery/medical-display/portfolio/medical_display_family_roadmap.md) defines the long-horizon family target model;
2. [medical_display_active_board.md](../../../delivery/medical-display/board/medical_display_active_board.md) defines the current owner round and reroute surface;
3. [medical_display_platform_mainline.md](../../../delivery/medical-display/contracts/medical_display_platform_mainline.md) defines how the mainline executes;
4. [medical_display_audit_guide.md](../../../delivery/medical-display/contracts/medical_display_audit_guide.md) defines the strict audited engineering truth;
5. this document preserves the completed first-baseline program and must not reopen a missing-family queue by itself.
