---
name: figure-polish
description: Use when a quest needs a polished milestone chart, paper-facing figure, appendix figure, or a mandatory render-inspect-revise pass before treating a figure as final.
---

# Figure Polish

Use this skill when a figure matters beyond transient debugging.

## MAS Stage Projection Boundary (not Professional Skill source)

This file is the MAS-owned figure-stage polish/runtime projection for Codex
discovery. It is not the Professional Skill source for figure-design content.
It remains the polish/review phase of the MAS `figure` stage prompt and is not an independent authority source.
For new or materially reworked paper-facing figures, start with the `figure`
stage prompt and route professional design and visual QA through
`contracts/capability_map.json` to `medical-figure-design`.

## Stage Contract

Before polishing, confirm:

- active study/work-unit identity and figure owner route;
- figure purpose, supported claim, and evidence refs;
- source data/statistical refs and allowed artifact target;
- current draft render, caption/legend boundary, and export target;
- visual QA or owner-gate handoff surface.

## Professional Skill Routes

Route figure design and visual QA to `medical-figure-design`.
Route adjacent checks to:

- `medical-statistical-review` for statistical annotations and uncertainty;
- `medical-table-design` when the evidence should be table-first;
- `medical-manuscript-review` for adversarial display-to-claim critique.

Specialist outputs may be candidate refs, QA notes, and route-back
recommendations only. MAS remains owner for figure artifact mutation, visual
audit receipt, owner receipt, typed blocker, human gate, current package, and
publication readiness.

## MAS Stage Responsibilities

- Preserve the accepted claim, data, statistics, and method labels.
- Keep visible in-figure text limited to panel labels, axis labels, legend
  labels, necessary statistical annotations, and minimal group/cohort notes.
- Require render-inspect-revise evidence before calling a durable figure final.
- Record final export refs, source data ref, generating script ref, supported
  claim/comparison, and owner-gate handoff.

## Forbidden Shortcuts

- Do not add narrative cards, claim banners, tool/vendor disclosures, route
  labels, or manuscript-unsafe prose inside the figure.
- Do not change underlying data, statistics, methods, or claim strength while
  polishing.
- Do not treat a gallery/template preview, local render, or specialist output as
  paper truth without MAS owner gate.

## Closeout Shape

Return one of:

- `visual_qa_candidate_ref`;
- `figure_polish_candidate_ref`;
- `render_inspect_revise_ref`;
- `figure_route_back_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.
