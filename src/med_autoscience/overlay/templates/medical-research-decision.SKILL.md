---
name: decision
description: MAS decision stage projection for go/stop/branch/write/finalize routing, blockers, and owner-boundary handoff.
---

# Decision Stage Operating Prompt

Use this stage prompt when MAS routes the current work unit to `decision`.

## MAS Stage Projection Boundary (not Professional Skill source)

This file is the MAS-owned stage/runtime projection for Codex discovery. It is
not the Professional Skill source for review, writing, submission, statistics,
literature, display, table, or data-governance methods. It decides the smallest
honest next route from durable evidence, what must route back, and which owner
surface must accept the decision. Route professional method work through
`contracts/capability_map.json` to MAS Scholar Skills.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_AUTOMATION_READY}}

## Stage Contract

Before recording a consequential route decision, confirm:

- active study/work-unit identity and controller route;
- exact decision question: continue, stop, branch, reuse/attach baseline,
  launch experiment, launch analysis, write, finalize, reset, or human gate;
- decision-relevant evidence refs and strongest contradictory evidence;
- current blocker, owner receipt, reviewer receipt, route-back, publication
  gate, or human gate state when present;
- rejected alternatives and why they lost;
- next legal owner and validation method.

## Professional Skill Routes

Use MAS Scholar Skills only as refs-only professional support:

- `medical-manuscript-review` for independent critique, reviewer-objection, and
  stop/continue recommendation candidates.
- `medical-statistical-review` for evidence adequacy, uncertainty,
  comparator, analysis-campaign, and result-readiness candidates.
- `medical-research-lit` for citation/source support and closest-prior-work
  candidates.
- `medical-manuscript-writing` for route wording or write-transition contract
  candidates after evidence selection.
- `medical-submission-prep` for submission-package or finalize-transition
  readiness candidates.
- `medical-data-governance` for source, access, privacy, and data-readiness
  decision inputs.

Specialist outputs may inform the decision record, route-back candidate, or
handoff ref. They do not become MAS domain truth, owner acceptance, typed
blockers, human gates, publication verdicts, current-package authority, or
submission readiness.

## Decision Responsibilities

- Choose the smallest action that resolves the current state.
- Separate evidence-building from narrative packaging; do not move to `write`
  or `finalize` just because a draft can be produced.
- Prefer stop, branch, reset, or route-back when durable evidence shows the line
  lacks a credible path.
- For `write` or `finalize`, record the writing/submission contract fields that
  downstream stages need; do not generate the professional content here.
- Use human gates only for real human-held constraints, external secrets,
  credentials, or explicit authority decisions MAS cannot infer.

## Forbidden Shortcuts

- Do not convert momentum, queue status, package presence, test pass,
  specialist output, or chat judgment into route authority.
- Do not create MAS domain truth, owner receipts, typed blockers, human gates,
  publication verdicts, controller decisions, current-package authority,
  runtime queues, or provider attempts from this prompt.
- Do not let ScholarSkills, OMA, or external specialist outputs close the MAS
  owner loop.

## Route-Back and Blocker Shape

When the decision cannot route forward, return the smallest explicit blocker:

- evidence is missing or contradictory for the decision question;
- baseline/scout/idea/analysis/write/finalize contract is incomplete;
- publication adequacy requires review, writing, submission, source, or stats
  candidate refs first;
- only a controller or true human-held constraint can resolve the route.

Each blocker must name missing evidence, affected action, next legal owner,
validation method, and stop condition.

## Closeout Shape

Return one of:

- `decision_record_ref`;
- `continue_route_ref`;
- `branch_or_reset_route_ref`;
- `write_transition_candidate_ref`;
- `finalize_transition_candidate_ref`;
- `stage_route_back_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.

## Continuation Handoff

Route to the selected stage only after the decision record names verdict,
action, reason, evidence refs, rejected alternatives, next owner, and validation
method. If that cannot be stated from durable evidence, route back to the stage
that owns the missing evidence instead of blocking on generic uncertainty.
