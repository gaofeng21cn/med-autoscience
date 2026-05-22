# Direction And Route Selection Prompt

Owner: MedAutoScience
Stage id: direction_and_route_selection
Stage kind: planning
Domain routes: scout, idea, decision
Next stage: baseline_and_evidence_setup
Machine boundary: prompt source for the MAS semantic pack. Runtime truth remains in stage packets, controller decisions, evidence ledgers, review ledgers, owner receipts, and durable artifact refs.

## Stage Objective

Freeze a medically worthwhile study direction, evidence target, and immediate route recommendation inside the active study boundary. The stage must decide whether the best next move is to proceed, narrow, pivot, stop, or request a human decision, and it must preserve the reasoning behind rejected routes.

## Codex Execution Posture

Codex acts as a stage work executor, not as a publication gate. Use open-ended medical research judgment over the structured refs: clinical importance, biological plausibility, cohort/data fit, novelty, likely evidence gain, journal route, and failure risk all matter. Structured route contracts and progress projections are traceability floors; they do not replace expert judgment.

Work from current MAS-owned refs. If the available refs do not establish the study boundary, source scope, or route authority, return a typed blocker or human gate recommendation instead of manufacturing a direction.

## Inputs And Refs

- Study charter, task intake, controller decision refs, and current `progress_projection`.
- Source readiness refs, source provenance refs, and workspace source locators.
- Evidence ledger refs, prior failed-path refs, review ledger refs, and publication-route memory refs.
- Literature coverage refs and journal-neighbor context when present.
- Product-entry/action catalog refs only as allowed dispatch and status surfaces.

## Allowed Tools And Native Helpers

- Inspect MAS refs through the MAS direct skill or generated OPL-hosted surfaces that expose `product_entry_status`, `workspace_cockpit`, and `study_progress`.
- Use `medical_research_execution` to reason over study, source, evidence, review, and memory refs.
- Use `owner_receipt_and_route_control` to form the owner route recommendation, route-back, typed blocker, or human gate request.
- Use sidecar/export refs only as locator and dispatch metadata; MAS remains the truth owner.

## Required Reasoning

- State the candidate clinical question, population, exposure or model target, outcome, source boundary, and intended contribution.
- Compare candidate routes by clinical relevance, data fit, novelty, evidence gain, journal fit, reviewer risk, and stop or pivot rule.
- Treat publication-route memory as reusable experience. It may suggest question shapes, table/figure patterns, or failed-path warnings; it cannot authorize a claim, quality verdict, or final route by itself.
- Preserve negative, weak, or rejected routes as failed-path evidence with explicit reasons.
- Select `baseline_and_evidence_setup` only when source readiness and study boundary are specific enough for managed execution.

## Forbidden Shortcuts

- Do not widen the study charter, endpoint, population, model target, or main claim without a decision receipt or human gate.
- Do not infer route readiness from descriptor readiness, test pass, generated interface status, progress projection, or provider completion.
- Do not copy publication-route memory into current truth without an accept/reject record and router receipt.
- Do not write MAS truth, publication eval, memory body, current package, or artifact authority from an OPL-generated surface.

## Review And Audit Separation

This stage produces execution reasoning and an owner route recommendation. It does not close a quality gate. Any quality, source-readiness, or memory accept/reject decision that affects publication authority requires a separate reviewer or auditor invocation with separate context, task record, and receipt.

## AI-First Handoff And Receipt

Return a stage execution receipt containing candidate routes, rejected alternatives, selected route, source refs, literature refs, publication-route memory refs used, blockers, and next-owner recommendation. The receipt must make the owner route explicit:

- `direction_route_selected` with refs and rationale.
- typed blocker when the source, study boundary, or memory currentness is insufficient.
- human gate request when scope expansion, claim shift, or PI decision is required.

## Done Criteria

- The selected route is tied to current study, source, evidence, literature, and memory refs.
- Rejected routes and stop/pivot criteria are recorded.
- No MAS truth body, memory body, publication verdict, or artifact authority was written by the executor.
- Next stage is `baseline_and_evidence_setup`, or the receipt contains a typed blocker/human gate with exact missing refs.
