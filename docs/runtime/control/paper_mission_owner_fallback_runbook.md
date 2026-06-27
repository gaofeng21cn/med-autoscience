# PaperMission owner fallback runbook

Owner: `MedAutoScience`
Purpose: define the automatic fallback path when MAS/OPL reaches a paper-mission domain gate without a new paper semantic delta.
State: `active_runbook`
Machine boundary: this document is a human-readable control runbook. Runtime truth remains in `PaperMissionRun`, `PaperMissionTransaction`, MAS owner-answer refs, OPL Temporal/read-model surfaces, and fresh CLI readback.

## Problem

For DM002/DM003-style paper missions, OPL can execute and transport stage attempts, but MAS owns paper authority. When a terminal OPL attempt returns to MAS and MAS records `route_back` / `paper_mission_stage_route_domain_gate_pending`, a second identical OPL redrive does not create paper progress by itself.

The missing control loop is:

1. detect that the same paper mission gate has returned without semantic progress;
2. stop synonymous OPL redrive for that mission identity;
3. let `mission_executor` produce a MAS-owned paper-facing answer;
4. expose that answer in `paper-mission inspect` / `study progress`;
5. only then hand a changed route command back to OPL.

## Progress Semantics

Paper progress is one of:

- `paper_facing_delta_ref`
- `owner_decision_ref`
- `carry_forward_risk_receipt_ref`
- `scope_reduction_decision_ref`
- `evidence_substitution_decision_ref`
- `research_pivot_decision_ref`
- narrow `stop_loss_decision_ref`
- `accepted_owner_receipt_ref`
- `quality_gate_receipt_ref`
- `human_gate_ref`
- a narrow `typed_blocker_ref`

Transport evidence is not paper progress:

- queue item existence;
- stage attempt id;
- provider liveness;
- retry count;
- hydrate/tick result;
- focused test pass;
- read-model generated timestamp.

## Default Automatic Fallback Order

When the same mission/stage/route-back reason returns without a new paper semantic delta, MAS should not default to blocker or human gate. The automatic fallback order is:

1. `paper_facing_delta`: revise or materialize the current candidate into a concrete paper-facing delta.
2. `owner_decision`: record a MAS owner decision that changes the next executable work unit.
3. `carry_forward_risk_receipt`: continue with explicit non-fatal residual risk when quality is imperfect but still usable.
4. `scope_or_evidence_or_research_pivot_decision`: narrow the question, substitute acceptable evidence, or pivot to the nearest publishable question.
5. `narrow_stop_loss_or_human_gate`: stop or ask a human only when MAS cannot safely choose among the remaining options.

OPL redrive is not the default after this budget is exhausted. It is only valid when a new candidate semantic fingerprint or a concrete transport/control-plane repair changes the route command.

## Narrow Blocker Rule

Missing ideal evidence is not a blocker. It should be converted to paper-facing delta, owner decision, carry-forward risk, scope reduction, evidence substitution, or pivot first.

Use `typed_blocker_ref` only when at least one is true:

- required data/source files are unavailable or inaccessible;
- privacy, ethics, permission, or credential boundaries cannot be decided by MAS;
- the user must choose publication strategy, risk appetite, or target venue;
- the core positive or publishable result is absent and continuing would be misleading;
- no supported claim, scope, proxy evidence, or pivot remains.

## Synonymous Route-Back Signature

A route-back is synonymous when these fields match after normalization:

- `study_id`
- canonical `mission_id`
- `stage_id` or target stage id
- `stage_terminal_decision.reason`
- `stage_terminal_decision.repair_scope`
- `route_back_evidence_kind`
- candidate semantic fingerprint when available
- accepted answer shape set

Do not include these fields in the semantic signature:

- OPL task id;
- stage attempt id;
- workflow id;
- queue id;
- generated timestamp;
- provider heartbeat age;
- focused test result;
- docs or contract commit id.

## Runtime Rule

First route-back can re-enter OPL if a new candidate or route command exists.

Second synonymous route-back may run a targeted repair if it changes the candidate semantic fingerprint.

Third synonymous route-back must switch to MAS owner fallback. The result must be one of the progress refs listed above, or a narrow stop-loss/human-gate decision.

This is a synonymous redrive budget, not a task budget. Budget exhaustion changes execution mode from OPL redrive to MAS owner fallback; it does not mean the paper mission is unusable.

## Currentness Rule

OPL read-model `status=running` is not running proof by itself. A running claim requires Temporal or equivalent provider visibility for the same workflow plus a live heartbeat or pending activity.

If OPL attempt ledger says `running` but provider status and heartbeat are empty, classify it as `stale_projection_until_provider_confirmed`.

## DM002/DM003 Canary

The canary is successful only when fresh readback shows at least one of:

- `paper-mission inspect` exposes a non-empty MAS owner fallback paper semantic ref;
- `artifact_delta_refs` or semantic delta refs include a changed paper-facing candidate;
- repeated route-back no longer triggers synonymous OPL redrive;
- OPL stale running rows no longer count as running proof.

The canary is not successful if it only shows:

- tests passed;
- queue is empty;
- OPL hydrate ran;
- docs were updated;
- another route-back packet was written with no changed owner-answer shape.
