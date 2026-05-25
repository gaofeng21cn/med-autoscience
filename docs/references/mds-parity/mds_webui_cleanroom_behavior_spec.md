# MDS WebUI Clean-Room Behavior Spec

Status: `clean_room_oracle`
Owner: `MedAutoScience Runtime OS`
Purpose: `Preserve MDS parity, backend-audit, and historical fixture reference context for MAS.`
State: `support_reference`
Machine boundary: Human-readable parity reference only; current MAS and MDS-source truth remains in explicit archive imports, source provenance, contracts, tests, diagnostics, and receipts.

Related contract: `live-console-parity`

## Scope

This file records observable behavior that MAS Live Console preserves from the old MDS WebUI class of tools. It is not source code, not a UI asset list, and not a package import plan.

The already landed retained behavior is limited to read-only runtime observation:

- workspace status is visible in one stable place;
- multiple study lines are distinguishable by `study_id`;
- active run identity, worker state, runtime health, supervision freshness, terminal tail, log tail, recent events, and artifact delta have source refs;
- controller actions are shown as intent or command refs only.

User-facing UX behavior that is still a parity target is tracked separately in
[MDS WebUI User Parity Gap Review](./mds_webui_user_parity_gap_review.md).
That review treats old project/quest-scoped navigation, stage/file workspace,
executor conversation, and interactive terminal/control as clean-room behavior
targets. Those targets are not licensed code or identity imports.

## Clean-Room Rules

- Do not copy old MDS React/WebUI source, CSS, assets, WebSocket server code, lockfiles, commits, or contributor metadata.
- Do not use old MDS product identity in MAS runtime UI.
- Oracle fixtures may name the behavior class and source categories, but must not contain code snippets, bundle paths, author names, emails, commit hashes, or license-bearing UI assets.
- MAS implementation must write only MAS-owned read-model/display surfaces.

## Event Topics

The minimum Live Console stream topics are:

- `workspace.status`
- `study.status`
- `runtime.health`
- `runtime.supervision`
- `terminal.tail`
- `log.tail`
- `artifact.delta`

Every event carries:

- `sequence`
- `topic`
- `study_id` when the event is study scoped
- `status`
- `source_ref`
- `observed_at`
- `local_time`

## Authority Boundary

The console never writes `study_truth`, `runtime_lifecycle.sqlite`, `publication_eval/latest.json`, `controller_decisions/latest.json`, `paper/current_package`, `manuscript/current_package`, or submission package surfaces. Runtime changes still go through MAS controller/runtime commands.
