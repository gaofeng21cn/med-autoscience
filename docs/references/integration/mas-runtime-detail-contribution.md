# MAS runtime detail contribution

MAS declares one `runtime.detail` contribution for a selected paper work item. The
producer reads the selected study row from `workspace_index.json` and its MAS-authored
research trajectory snapshot. It does not keep an App or Studio copy of current state.

The response separates business activity from scientific trajectory. A paused or
delivered study therefore has empty `work.active` and `work.queued` arrays even when
its research trajectory retains an active scientific branch. The next owner action is
projected under `work.pending` instead of being relabeled as queued runtime work.

## Required App contract delta

The current Host projection admits `slot=runtime.detail` and `scope=work_item`, but
that scope is placement metadata only. The current App renderer invokes package reads
with `input: {}` and only the `channel_access` renderer reads dynamic contribution
data. End-to-end display remains blocked until the App owner makes both changes:

1. Bind each `runtime.detail` contribution read to the selected resolved work item and
   pass `agent_id`, `domain_id`, `work_item_id`, `domain_work_item_id`,
   `work_item_scope_id`, and `identity_state` under `input.work_item_identity`.
2. Add a generic declarative result renderer for an admitted view type such as
   `task_board`, or add an allowlisted runtime-detail result contract. The renderer
   must display the producer response without inferring MAS state.

Framework should validate the selected identity before invoking the package command.
MAS then independently rejects unresolved, mismatched, missing, or non-inventory
identity and never falls back to a default study.

The producer is ready for Host CLI readback, but this document does not claim current
App UI projection, installation, release, deployment, or publication readiness.
