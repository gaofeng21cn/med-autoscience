# Medical Research Execution Skill Policy

Owner: MedAutoScience
Skill role: domain execution policy for Codex stage work executors
Machine boundary: this policy guides executor behavior. It does not own study truth, quality verdicts, source readiness verdicts, memory body acceptance, artifact authority, or submission readiness.

## Execution Scope

Use this skill when Codex is executing MAS stage work in `direction_and_route_selection`, `baseline_and_evidence_setup`, `bounded_analysis_campaign`, `manuscript_authoring`, or `finalize_and_publication_handoff`. The executor may inspect MAS-owned refs, reason over them, run allowlisted MAS tasks, and emit execution receipts, evidence refs, artifact/source refs, route-back reasons, human gate requests, or typed blockers.

The executor must treat all medical research work as claim-boundary work. A cohort change, endpoint change, source substitution, model target change, external validation change, or journal-route change is a route decision, not a local implementation detail.

## Required Inputs

- Study charter, task intake, controller decisions, and active route refs.
- Source readiness refs, source provenance refs, data/cohort/endpoint refs, and source locator metadata.
- Evidence ledger refs, run context refs, runtime event refs, failed-path refs, and reviewer concern refs.
- Publication-route memory refs and memory writeback receipt refs when available.
- Canonical manuscript, claim-evidence, citation, display, artifact rebuild, and package refs when the stage touches delivery.

## Allowed Work

- Interpret medical and statistical meaning across current refs.
- Produce current result refs, evidence refs, canonical manuscript refs, artifact rebuild refs, and owner execution receipts.
- Classify outcomes as completed evidence, no-op with currentness proof, route-back, typed blocker, or human gate request.
- Use OPL generated surfaces only as locator, status, and allowlisted dispatch surfaces.
- Use MAS native helpers only when their outputs remain refs, receipts, progress deltas, or typed blockers.

## Medical Judgment Requirements

- Keep claims tied to evidence, source, and citation refs.
- Preserve weak, negative, failed, or uncertain findings as route evidence.
- Name the clinical interpretation and reviewer risk of each material result.
- Prefer claim narrowing, stop-loss, or route-back over unsupported positive-result harvesting.
- Record when source provenance, artifact rebuild proof, or reviewer currentness is missing.

## Forbidden Work

- Do not write MAS study truth, publication eval verdicts, source body, memory body, artifact authority, current package, or submission readiness from this skill.
- Do not use script success, file presence, queue completion, generated interface readiness, provider completion, or test pass as medical readiness.
- Do not use publication-route memory as evidence or as a quality verdict.
- Do not self-review the executor's own output to close an AI-first quality gate.

## Required Output Shape

Every execution must return one of these semantic outcomes:

- owner receipt with input refs, output refs, changed refs, currentness proof, and next owner.
- typed blocker with blocker type, missing refs, route-back owner, and required repair.
- route-back request with owner, work unit, reason, and refs.
- human gate request with decision needed, scope impact, and refs.
- no-op with currentness proof explaining why no mutation was needed.

Ambiguous completion is invalid because it lets runtime progress replace medical authority.
