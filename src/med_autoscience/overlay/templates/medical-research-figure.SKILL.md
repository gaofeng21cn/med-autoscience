---
name: figure
description: MAS figure stage operating prompt for claim-bound medical figure planning, rendering, and handoff.
---

# Figure Stage Operating Prompt

Use this stage prompt when MAS routes the current work unit to `figure`.

## MAS Stage Projection Boundary (not Professional Skill source)

This file is the MAS-owned stage/runtime projection for Codex discovery. It is
not the Professional Skill source for figure-design content. It decides whether
a figure should exist, what claim and evidence it must carry, which artifact
surfaces may change, and which owner gate must accept the result. Route
professional design and visual QA through `contracts/capability_map.json` to
`medical-figure-design` from MAS Scholar Skills.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

## Stage Contract

Before planning or rendering a figure, confirm:

- figure purpose and supported claim;
- source data/statistical refs and allowed artifact target;
- intended figure family, panel role, and manuscript placement;
- caption/legend boundary and forbidden in-figure prose;
- visual audit and owner-gate handoff surface.

## Professional Skill Route

Use `medical-figure-design` when the work needs:

- figure intent and panel planning;
- renderer/template selection;
- first-draft figure design;
- Visual QA and polish;
- figure-to-claim consistency checks;
- reviewer handoff for display issues.

Route adjacent professional checks to sibling MAS Scholar Skills instead of
embedding their methods here:

- `medical-statistical-review` for statistical annotation and uncertainty
  checks;
- `medical-table-design` when a table is the better display surface;
- `medical-research-lit` when a display claim needs citation support;
- `medical-manuscript-review` for adversarial display-to-claim critique.

The specialist skill may prepare design candidates, figure refs, QA notes, and
route-back recommendations. MAS remains the owner for figure artifact mutation,
visual-audit receipts, owner receipts, typed blockers, human gates, current
package, and publication readiness.

## Default Defense

- Do not make decorative figures without a claim/evidence role.
- Do not change data, statistics, methods labels, or claims while polishing.
- Do not use a gallery or template preview as paper truth.
- Do not create owner receipts, typed blockers, human gates, publication evals,
  controller decisions, runtime queues, or current-package authority from this
  prompt.
- If the figure lacks evidence refs, purpose, or owner target, emit a route-back
  candidate instead of rendering.

## Closeout Shape

Return one of:

- `figure_intent_ref`;
- `figure_design_candidate_ref`;
- `figure_render_candidate_ref`;
- `visual_qa_candidate_ref`;
- `figure_route_back_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.
