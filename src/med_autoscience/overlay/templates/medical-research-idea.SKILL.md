---
name: idea
description: MAS idea stage projection for candidate-direction selection, professional-skill routing, and owner-boundary handoff.
---

# Idea Stage Operating Prompt

Use this stage prompt when MAS routes the current work unit to `idea`.

## MAS Stage Projection Boundary (not Professional Skill source)

This file is the MAS-owned stage/runtime projection for Codex discovery. It is
not the Professional Skill source for literature review, statistics, manuscript
writing, review, figure/table design, submission, or data-governance methods.
It decides whether direction selection is allowed, which evidence must shape
candidate ideas, what must route back, and which owner surface may accept the
candidate route. Route professional method work through
`contracts/capability_map.json` to MAS Scholar Skills.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_REFERENCE_PAPERS}}

## Stage Contract

Before selecting, branching, rejecting, or routing an idea, confirm:

- active study/work-unit identity and controller route;
- accepted scout/evaluation contract, baseline state, and comparator scope;
- current evidence refs, failure patterns, limitations, and prior decisions;
- closest-prior-work refs that materially affect novelty or research value;
- candidate board with selected, rejected, parked, or blocked status;
- next legal owner: `experiment`, `analysis-campaign`, `decision`, `scout`,
  `baseline`, or a named route-back.

## Professional Skill Routes

Use MAS Scholar Skills only as refs-only professional support:

- `medical-research-lit` for closest-prior-work, citation, guideline, and
  related-work candidate refs.
- `medical-statistical-review` for metric fit, estimand, comparator,
  analysis-design, and falsification-plan candidates.
- `medical-data-governance` for source, cohort, data-lineage, privacy, and
  feasibility candidates.
- `medical-manuscript-review` for claim-defensibility, reviewer-objection, and
  stop/continue critique candidates.
- `medical-manuscript-writing` only for a concise selected-idea draft or
  handoff wording after the route is evidence-shaped.

Route display, table, submission, or external-specialist needs through
`contracts/capability_map.json` rather than embedding those playbooks here. All
specialist outputs remain candidate refs until MAS owner evidence accepts them.

## Idea Responsibilities

- Start from durable scout/baseline evidence; do not invent a new dataset,
  metric, or evaluation regime from this prompt.
- Rank the decision-relevant gaps before ranking candidate ideas.
- Keep a small serious frontier; preserve rejected and parked candidates only
  when they matter for downstream recombination or audit.
- Select only an idea that has an explicit limitation, closest-prior-work
  relation, feasibility path, falsification path, and claim boundary.
- If no candidate survives feasibility, literature, or defensibility gates,
  record a blocked/rejected outcome and route back instead of extending
  brainstorming.

## Forbidden Shortcuts

- Do not claim novelty, publication strength, or idea acceptance from recall,
  style, implementation convenience, or specialist output alone.
- Do not treat a literature candidate set as MAS citation or publication
  authority.
- Do not create MAS domain truth, owner receipts, typed blockers, human gates,
  publication verdicts, current-package authority, runtime queues, or provider
  attempts from this prompt.
- Do not let ScholarSkills, OMA, or external specialist outputs close the MAS
  owner loop.

## Route-Back and Blocker Shape

When ideation cannot route forward, return the smallest explicit blocker:

- baseline or evaluation contract is not durable enough;
- closest-prior-work coverage is too thin to judge novelty/value;
- all candidates are infeasible, confounded, or not differentiated;
- source/data/statistical assumptions require specialist candidate refs first;
- route choice is a real controller/human preference, not an internal ranking
  problem.

Each blocker must name the missing evidence, affected candidate or route, next
legal owner, and validation method.

## Closeout Shape

Return one of:

- `idea_candidate_board_ref`;
- `selected_idea_candidate_ref`;
- `rejected_idea_set_ref`;
- `literature_or_novelty_route_back_ref`;
- `baseline_or_eval_contract_route_back_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.

## Continuation Handoff

Route to `experiment` only when the selected idea is executable and falsifiable
under the active evaluation contract. Route to `analysis-campaign` only when the
candidate needs bounded evidence before implementation or writing. Route to
`decision` when the honest next move is stop, branch, reset, continue, or
preference-sensitive route selection. Route back to `scout` or `baseline` when
framing or comparator evidence is still missing.
