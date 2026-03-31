---
name: figure-polish
description: Use when a quest needs a polished milestone chart, paper-facing figure, appendix figure, or a mandatory render-inspect-revise pass before treating a figure as final.
---

# Figure Polish

Use this skill when a figure matters beyond transient debugging.

This includes:

- a durable connector milestone figure
- a paper-facing main-text figure
- an appendix or supplementary figure
- an internal review figure that may later be promoted into a manuscript-facing surface

Do not use this skill for disposable debug plots unless the user explicitly asks for them to be polished.

## Core principle

In MedAutoScience, a manuscript-facing figure is an evidence surface, not an infographic surface.

Figure polish exists to tighten visual expression around an already accepted claim.
It must not change the claim, invent a new methods label, or introduce visible narrative that the manuscript body has not defined.

## Visible text contract

For any main-text figure, appendix figure, or other durable paper-facing surface, visible in-figure text may only include:

- panel labels
- axis labels
- legend labels
- necessary statistical annotations
- minimal group, cohort, or sample notes

The following are prohibited inside the figure itself:

- summary cards
- narrative paragraphs
- claim banners
- tool/vendor/service mention
- repository or website disclosures
- engineering route labels
- AI system self-advertising

Do not move prohibited in-figure prose into the caption and keep the same problem alive there.
If the figure surface is overloaded, rewrite the visible figure text and metadata until only manuscript-safe content remains.

## Claim-preservation contract

Figure polish may adjust layout, labels, ordering, sizing, palette, spacing, and export settings.
Figure polish must not:

- change the underlying data
- change a statistical result
- rename a method into a manuscript-facing label that is not already durably defined
- strengthen or soften the scientific claim beyond what the accepted evidence supports

If a figure needs semantic changes rather than presentation cleanup, route back to the underlying analysis or writing task instead of polishing harder.

## Style contract

DeepScientist figures should feel academic, restrained, and clear.

Default visual rules:

- white or near-white background
- muted palette only
- no neon colors
- no rainbow or jet-like colormaps
- no glossy gradients, shadows, or heavy borders
- top and right spines removed unless the chart truly requires them
- light grid only when it improves reading
- minimal legend, with direct labeling when that is clearer
- the main method visually dominant over baselines or comparators

## Chart selection

Choose the chart by the research question:

- line chart for ordered trends
- bar chart for a small number of categorical end-point comparisons with a meaningful zero baseline
- point-range or dot plot when uncertainty matters
- box, violin, or histogram only for true distribution questions
- heatmap only when matrix structure itself is the result

Do not choose a chart because it looks richer or more decorative.

## Mandatory render-inspect-revise workflow

If the figure is intended for milestone reporting, manuscript drafting, appendix use, or durable artifact storage, follow this exact sequence:

1. render a first draft
2. open the rendered file yourself
3. inspect the actual exported result, not only the code
4. revise the figure if readability, composition, or manuscript-safety is weak
5. re-export the final version

Do not treat a figure as final if you have not inspected the rendered result.

## Mandatory self-review checklist

When reviewing the rendered figure, check at least:

- is the main message obvious in a few seconds
- are labels, units, and baselines explicit
- is the main method visually dominant and comparison hierarchy clear
- are text size, line width, marker size, and error bars balanced
- do ticks and labels remain readable after realistic down-scaling
- would the figure still work in grayscale or for color-vision-deficient readers
- does the figure avoid any prohibited visible text or manuscript-unsafe metadata

If any answer is negative, revise before calling the figure complete.

## Export discipline

- connector milestone figure: usually export `png`
- paper-facing figure: export `pdf` or `svg`, plus a `png` preview
- appendix figure: usually export vector plus preview

Prefer deterministic export names and keep the generating script path explicit.
Do not append tooling disclosures, vendor references, service links, or editing recommendations to captions, notes, or visible figure text.

## Durable recording

Whenever a figure is accepted as durable, record:

- source data path
- generating script path
- final export paths
- figure surface class
- the supported comparison or claim
- one short note describing what changed during the self-review pass

For manuscript work, keep this aligned with `paper/figures/figure_catalog.json` and `paper/figure_semantics_manifest.json`.

## Implementation boundary

Explanation figures, workflow schematics, cohort diagrams, and graphical abstracts must be generated through MedAutoScience-controlled programmatic drawing.
Do not assume an external figure-editing runtime, service, or vendor step is part of the accepted manuscript path.
