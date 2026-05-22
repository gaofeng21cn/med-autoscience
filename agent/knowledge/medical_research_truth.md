# Medical Research Truth Knowledge

Owner: MedAutoScience
Knowledge role: executable truth model for MAS stage packs
Machine boundary: this file describes how Codex should reason over truth refs. It is not itself a truth surface.

## Truth Owners

MAS owns study truth, route decisions, medical evidence interpretation, source readiness verdicts, AI reviewer/auditor quality records, publication verdicts, publication-route memory body acceptance, artifact authority, package authority, typed blockers, and owner receipts.

OPL generated or hosted surfaces may index refs, project status, dispatch allowlisted tasks, and display workbench cards. They do not write MAS truth bodies, memory bodies, publication verdicts, source bodies, artifact authority, `current_package`, or submission readiness.

## Durable Truth Refs

Treat these as the normal truth-bearing surfaces to inspect before making a stage decision:

- study charter, task intake, owner route, and controller decisions.
- `progress_projection` and `domain_health_diagnostic` for runtime state and current next action.
- evidence ledger, run context, runtime event ledger, failed-path records, and claim-evidence map.
- source readiness records, source provenance refs, source locator refs, and data/cohort/endpoint definitions.
- review ledger, AI reviewer operating-system trace, independent reviewer/auditor records, and `publication_eval/latest.json`.
- canonical manuscript/source refs, display/table/figure refs, artifact rebuild proof, delivery manifest, and package refs.
- publication-route memory refs, memory writeback proposals, accept/reject records, and router receipts.

## Currentness Rules

- A ref is useful only if it is current relative to the active task intake, controller decision, source/manuscript refs, and latest materialization it claims to support.
- A stale ready state is a blocker, not a weak ready state.
- Runtime progress, queue completion, generated interface readiness, local test pass, and package presence are not medical truth.
- If two refs disagree, route by MAS owner authority: controller/study/source/evidence/review/artifact authority beats prose docs and generated projections.

## Claim-Boundary Rules

- A claim must name population/cohort, exposure or model target, outcome, comparator or baseline, measurement window, and source boundary.
- Changing any of those fields requires route decision authority or a human gate.
- Weak, negative, or failed analyses remain truth. They should drive claim narrowing, stop-loss, route-back, or explicit limitation text.
- Literature and publication-route memory can shape interpretation, but evidence claims require current study evidence refs.

## Codex Use

Codex should cite the refs it read, state what each ref authorizes, and return a receipt or blocker when a required truth ref is missing. Codex should never fill missing truth by inference from nearby prose, filenames, package freshness, or historical memory.
