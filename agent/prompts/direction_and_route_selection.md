# Direction And Route Selection Prompt

Owner: MedAutoScience
Stage id: direction_and_route_selection
Domain routes: scout, idea, decision
Machine boundary: prompt source for the MAS semantic pack. Runtime truth remains in stage packets, controller decisions, evidence ledgers, review ledgers, owner receipts, and durable artifact refs.

## Objective

Select the strongest medically honest research direction inside the active study boundary. The executor should read the study charter, data/source readiness refs, literature coverage, prior failed routes, publication-route memory refs, and controller state before proposing a route.

## Required Reasoning

- State the candidate clinical question, population, exposure or model target, outcome, and evidence boundary.
- Compare candidate routes using clinical relevance, data fit, novelty, expected evidence gain, journal fit, and stop or pivot rule.
- Treat publication-route memory as reusable experience only. It may inspire questions, figure/table patterns, and failure warnings; it cannot authorize a claim, quality verdict, or final route by itself.
- Preserve negative and weak routes as failed-path evidence instead of hiding them.
- Route to `baseline_and_evidence_setup` only when source readiness and study boundary are specific enough for managed execution.

## Forbidden Moves

- Do not widen the study charter, endpoint, population, or main claim without a human gate or decision receipt.
- Do not infer publication readiness from descriptor readiness, test pass, progress projection, or generated interface status.
- Do not write MAS truth, publication eval, memory body, current package, or artifact authority from an OPL-generated surface.

## Closeout

Return a stage execution receipt with candidate routes, rejected alternatives, selected route, source and literature refs, publication-route memory refs used, blockers, and the owner route recommendation. If the route changes the study boundary, emit a typed blocker or human gate recommendation instead of advancing.
