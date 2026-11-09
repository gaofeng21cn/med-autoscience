# MAS runtime detail contribution

MAS declares one `runtime.detail` contribution for a selected paper work item.
The executable producer is `plugins/med-autoscience/bin/mas-app-contribution`;
`contracts/runtime_detail_contribution_contract.json` declares its machine contract.
It reads `workspace_index.json` and MAS research trajectory bytes without keeping
a second App or Studio state store.

Paused or delivered studies have empty `work.active` and `work.queued` arrays.
Scientific trajectory can retain an active branch; that does not make it runtime
work. A next owner action is projected under `work.pending`.

## Current study and usable output

The shared MCP App consumes the selected resolved identity under
`input.work_item_identity`, including `agent_id`, `domain_id`, `work_item_id`,
`domain_work_item_id`, `work_item_scope_id`, and `identity_state`. Framework
validates selection before invocation. MAS independently rejects unresolved,
mismatched, missing, or non-inventory identity and never selects a default study.
The shared host supplies this identity and the registered workspace; the user does
not enter status, trajectory or manifest paths. Starting or continuing research
uses the existing Framework task actions rather than a second MAS execution loop.

Study progress remains available before the first research trajectory is written.
A missing snapshot is reported as `trajectory_status=not_available`; an invalid
or mismatched snapshot remains an error. The read-only `artifacts` collection is
projected directly from complete owner-authored trajectory nodes of kind `artifact`,
preserving their revisions, labels, status, details and source references; the
`artifact_id` and `title` aliases make those same nodes usable by shared views. It does not scan
workspace directories, select a latest file or promote an output to accepted
research or publication quality.

The `trajectory` field preserves the complete selected snapshot. Hypothesis
summaries also retain `details` and `source_refs`. Supporting, opposing and
inconclusive relationships, failed routes and review sources remain MAS-authored.
The host-neutral Framework workbench renders this contract in Codex and Studio;
Studio provides the standard DSH MCP Apps plugin and no MAS-specific renderer.
Missing evidence stays missing; execution completion does not imply support.

## Review and continue the selected study

`review_context` carries the selected resolved work-item identity, the owner
trajectory revision, the full artifact projection and exact SHA-256 source refs.
Its `revision` binds the selected study row and full trajectory; a change to a
different study does not invalidate this review. Source hashes record the bytes
observed and do not grant scientific acceptance. The producer reads only the
declared workspace index and selected trajectory within the registered workspace.

The shared workbench submits a user's judgment through the current Framework
work-item action (`opl.runtime.v1#action`), with this context in the existing
action payload. Framework owns the current route, confirmation, StageRun signal
and result readback; MAS owns the scientific inputs, subsequent review and
publication authority. Reading, reopening or selecting a hypothesis does not
submit a decision. A paused study still requires its existing explicit lifecycle
admission before a Stage can run.

After a source update, refresh the owner contribution and confirm the current
context before continuing. Read the original task after an unknown signal
outcome. Local source tests cover context reopening, changed study evidence,
pending-decision updates and workspace containment. They do not claim a real
hosted StageRun or installed UI acceptance.

Source tests and browser fixtures cover rendering, identity, source selection,
conditional revisions and human confirmation. Installed Package currentness,
App installation and publication require their own delivery evidence.
