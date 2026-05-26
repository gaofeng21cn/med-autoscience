# MDS WebUI Clean-Room Behavior Spec

Status: `clean_room_oracle`
Owner: `MedAutoScience Product Projection + OPL Runtime Manager integration boundary`
Purpose: `Preserve MDS parity, backend-audit, and historical fixture reference context for MAS.`
State: `support_reference`
Machine boundary: Human-readable parity reference only; current MAS and MDS-source truth remains in explicit archive imports, source provenance, contracts, tests, diagnostics, and receipts.

Related contract: `live-console-parity`

## Scope

This file records observable behavior that MAS Progress Portal and the OPL runtime drilldown join may preserve from the old MDS WebUI class of tools. It is not source code, not a UI asset list, and not a package import plan.

The already landed MAS-retained behavior is limited to read-only paper/domain progress projection:

- workspace status is visible in one stable place;
- multiple study lines are distinguishable by `study_id`;
- per-study pages, route / decision trail, route map, source refs, artifact refs, owner receipts, typed blockers, and OPL handoff refs have source refs;
- controller/runtime actions are shown as domain-handler / OPL owner-route handoff refs only.

Runtime drilldown behavior is not a MAS private Live Console surface. Runtime state, terminal/log/provider refs, attach/control, worker liveness, and provider attempt details must come from OPL `current_control_state` or provider attempt projection.

User-facing UX behavior that is still a parity target is tracked separately in
[MDS WebUI User Parity Gap Review](./mds_webui_user_parity_gap_review.md).
That review treats old project/quest-scoped navigation, stage/file workspace,
executor conversation, and interactive terminal/control as clean-room behavior
targets. Those targets are not licensed code or identity imports, and runtime
drilldown targets belong to OPL runtime owner surfaces.

## Clean-Room Rules

- Do not copy old MDS React/WebUI source, CSS, assets, WebSocket server code, lockfiles, commits, or contributor metadata.
- Do not use old MDS product identity in MAS runtime UI.
- Oracle fixtures may name the behavior class and source categories, but must not contain code snippets, bundle paths, author names, emails, commit hashes, or license-bearing UI assets.
- MAS implementation must write only MAS-owned progress/domain read-model/display surfaces.
- Runtime drilldown implementation must stay in OPL runtime owner surfaces; MAS may only expose refs, owner receipts, typed blockers, or handoff links.

## Projection Topics

The minimum MAS-owned Progress Portal projection topics are:

- `workspace.status`
- `study.status`
- `study.route`
- `study.route_map`
- `source.refs`
- `artifact.delta`
- `owner.receipt`
- `typed.blocker`
- `opl.runtime_handoff`

Runtime owner topics such as provider attempt state, terminal tail, log tail,
worker liveness, attach/control state, and provider SLO belong to OPL
`current_control_state` / provider attempt projection. MAS may link to those
refs but must not materialize them as MAS-owned runtime truth.

Every MAS projection event carries:

- `sequence`
- `topic`
- `study_id` when the event is study scoped
- `status`
- `source_ref`
- `observed_at`
- `local_time`

## Authority Boundary

The projection never writes `study_truth`, `runtime_lifecycle.sqlite`, `publication_eval/latest.json`, `controller_decisions/latest.json`, `paper/current_package`, `manuscript/current_package`, terminal command files, provider attempts, or submission package surfaces. Runtime changes go through OPL runtime owner transport and MAS domain-handler / owner-route handoff refs; MAS Progress Portal remains read-only.
