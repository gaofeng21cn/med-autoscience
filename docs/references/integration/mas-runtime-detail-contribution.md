# MAS runtime detail contribution

MAS declares one `runtime.detail` contribution for a selected paper work item.
The executable producer is `plugins/med-autoscience/bin/mas-app-contribution`;
`contracts/runtime_detail_contribution_contract.json` declares its machine contract.
It reads `workspace_index.json` and MAS research trajectory bytes without keeping
a second App or Studio state store.

Paused or delivered studies have empty `work.active` and `work.queued` arrays.
Scientific trajectory can retain an active branch; that does not make it runtime
work. A next owner action is projected under `work.pending`.

## Required App contract delta

The MAS contract records the consumer requirements and its last integration
blocker. That marker is a MAS integration record, not fresh proof of App behavior.
End-to-end acceptance must verify the current App consumer:

1. Pass the selected resolved work item under `input.work_item_identity` with
   `agent_id`, `domain_id`, `work_item_id`, `domain_work_item_id`,
   `work_item_scope_id`, and `identity_state`.
2. Render the admitted `activity_log` view from the producer response without
   inferring MAS state or creating a private renderer contract.

Framework validates selected identity before invocation. MAS independently
rejects unresolved, mismatched, missing, or non-inventory identity and never
falls back to a default study. Producer tests and Host CLI readback do not prove
current App rendering, installed Package state, release, or deployment.
