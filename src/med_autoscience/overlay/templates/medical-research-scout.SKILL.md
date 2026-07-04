---
name: scout
description: MAS scout stage projection for framing, source readiness, baseline-neighborhood routing, and owner-boundary handoff.
---

# Scout Stage Operating Prompt

Use this stage prompt when MAS routes the current work unit to `scout`.

## MAS Stage Projection Boundary (not Professional Skill source)

This file is the MAS-owned stage/runtime projection for Codex discovery. It is
not the Professional Skill source for literature review, dataset governance,
statistics, writing, or submission methods. It decides what framing evidence is
needed, what can route forward, what must route back, and which MAS owner
surface must accept the result. Route professional method work through
`contracts/capability_map.json` to MAS Scholar Skills.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_CONTROLLER_FIRST}}

{{MED_AUTOSCIENCE_ROUTE_BIAS}}

{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}

{{MED_AUTOSCIENCE_REFERENCE_PAPERS}}

## Stage Contract

Before routing out of `scout`, confirm:

- active study/work-unit identity and current controller route;
- task frame, cohort or dataset source, split, metric, and comparator scope;
- closest paper, guideline, registry, dataset, benchmark, and repo refs;
- source/provider/citation readiness for refs promoted beyond watchlist;
- baseline-neighborhood direction, including attach/import/reproduce/reject;
- the next legal owner: `baseline`, `idea`, `decision`, or a named route-back.

## Professional Skill Routes

Use MAS Scholar Skills only as refs-only professional support:

- `medical-research-lit` for literature, citation, guideline, and PubMed/source
  candidate refs.
- `medical-data-governance` for cohort/source lineage, access, privacy,
  registry, public-sidecar, and data-readiness candidates.
- `medical-statistical-review` for metric, split, estimand, comparator, and
  baseline-evaluation-contract candidates.
- `medical-manuscript-review` only when the framing question is driven by an
  existing draft or reviewer critique.
- `medical-submission-prep` only when venue constraints affect the framing or
  journal-shortlist route.

If the eight core MAS Scholar Skills do not cover a named specialist gap, use
the external specialist policy in `contracts/capability_map.json`; search,
inspect, and sync a single skill only. External and ScholarSkills outputs remain
candidate refs until MAS owner evidence accepts them.

## Scout Responsibilities

- Lock the smallest honest framing contract: task, source, metric, split,
  comparator, and baseline-neighborhood direction.
- Keep scouting bounded; stop when the next anchor is clear or the blocker is
  explicit.
- Preserve retained/rejected/watchlist status for material sources.
- Distinguish source-readiness, provider provenance, and citation-readiness
  gaps from downstream baseline or idea work.
- Prefer durable quest/state refs over memory-only recollection; use external
  discovery only to close a real framing gap.

## Forbidden Shortcuts

- Do not turn generic browsing, paper summaries, or memory recall into scout
  authority.
- Do not guess dataset, split, metric, citation, or baseline identity when local
  evidence is ambiguous.
- Do not create MAS domain truth, owner receipts, typed blockers, human gates,
  publication verdicts, current-package authority, runtime queues, or provider
  attempts from this prompt.
- Do not let ScholarSkills, OMA, or external specialist outputs close the MAS
  owner loop.

## Route-Back and Blocker Shape

When scouting cannot route forward, return the smallest explicit blocker:

- missing or conflicting task frame;
- missing cohort/source/readiness ref;
- unresolved metric/split/comparator contract;
- missing or weak baseline provenance;
- insufficient citation/source provenance for downstream claims;
- specialist gap requiring a named refs-only route.

Each blocker must name the missing ref class, why it changes downstream routing,
the next legal owner, and the validation method.

## Closeout Shape

Return one of:

- `scout_framing_report_ref`;
- `eval_contract_candidate_ref`;
- `source_readiness_route_back_ref`;
- `baseline_neighborhood_ref`;
- `citation_or_literature_route_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.

## Continuation Handoff

Route to `baseline` when a baseline attach/import/reproduce decision is the next
honest move. Route to `idea` only when the framing and baseline direction are
already durable enough for direction selection. Route to `decision` when the
remaining ambiguity is a stop/branch/reset or preference-sensitive route choice.
