# Publication Route Memory Policy

Status: `active policy`
Date: `2026-05-11`
Owner: `MedAutoScience`
Purpose: keep reusable publication-route experience available to Codex-led stages without turning it into a mechanical recipe engine.
State: `active operating policy`
Machine boundary: this is a human-readable policy. Machine truth remains in `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, `stage_recall_index`, `study_charter`, evidence/review ledgers, controller decisions, publication eval, and generated artifacts.

## Conclusion

Publication routes such as clinical classifier / risk stratification, subtype reconstruction, external validation / model update, gray-zone triage, survey trend analysis, or mechanistic sidecar extension should be maintained primarily as natural-language route memory.

They are not a programmatic recipe engine. Their role is to remind Codex CLI of reusable medical publication experience at the right stage, then let the stage produce context-specific research judgment, candidate routes, failed paths, and next actions.

The correct shape is:

- lightweight route memory cards
- minimal searchable metadata
- stage-specific retrieval and injection
- typed closeout writeback
- controller/evidence guards around claims and publication authority

The incorrect shape is:

- a large prompt block containing every route
- a rigid schema that tries to precompute which paper must be written
- a scoring engine that generates the winning research route before stage work
- a checklist that turns exploratory medical research into fixed analysis execution

## Why Natural-Language Memory

High-yield publication routes are exploratory knowledge. They encode experience such as:

- which data affordances often support a publishable paper
- which figure/table packages usually make a route credible
- which routes survive moderate or weak main effects
- which routes often fail because evidence, external validation, or clinical value is too thin
- which journal or reviewer expectations tend to matter

This knowledge is valuable because Codex can reason with it. Over-structuring it too early removes that value: the system starts optimizing fields rather than thinking medically.

Therefore route memory should preserve rich prose, caveats, examples, and failure modes. Structure is allowed only where it helps discovery, provenance, stage targeting, freshness, and writeback routing.

## Route Memory Card Shape

Each reusable route memory card should remain readable as prose. A useful card normally contains:

- title and route family
- short description of the publication pattern
- when it is worth considering
- data signals that make it promising
- common evidence package
- common figures/tables or display routes
- common failure modes and stop/pivot signals
- examples or prior study refs when available
- notes on journal/reviewer fit

Metadata should be minimal:

- stable `memory_id`
- route family tags
- stage applicability, such as `scout`, `idea`, `decision`, `analysis-campaign`, or `review`
- source/provenance refs
- status such as `draft`, `active`, `paper_proven`, `deprecated`
- freshness or review date

The metadata supports retrieval. It does not decide the research route.

## Stage Use

Route memory is consumed through stage packets, not through global prompt stuffing.

Recommended behavior by stage:

- `scout`: retrieve a few route memories that may fit the dataset and disease area; use them to widen or sharpen candidate questions.
- `idea`: compare route memories against actual data affordances, literature gaps, endpoint feasibility, and clinical value; produce selected and rejected candidate lines.
- `decision`: use route memories as background for route rationale, stop/pivot rules, and risk of weak evidence; final route must still come from stage output and controller decision.
- `analysis-campaign`: retrieve memory about common evidence gaps, figure/table packages, weak-result handling, and reviewer-facing repairs.
- `review`: retrieve memory about recurring critique patterns, claim restraint, citation gaps, and route-specific reviewer expectations.

The retrieved set should be small and stage-relevant. A practical default is top few cards, not the whole library.

## Writeback

New experience from a stage should be written back only when it is reusable beyond the current paper.

Good writebacks:

- a route worked only after adding external validation
- a classifier route failed because event count was too low for credible calibration
- a survey trend route needed guideline correspondence and access/reimbursement context
- a reviewer repeatedly expected decision-curve or subgroup evidence for a risk model
- a figure/table package made a route easier to argue

Bad writebacks:

- single-study results or conclusions
- claim support that belongs in the evidence ledger
- reviewer findings that belong in the review ledger
- publication readiness assertions
- raw analysis outputs, logs, or package state

`stage_memory_closeout_packet` should propose the writeback. `memory_write_router_receipt` should route it to the correct owner surface or reject it.

## Authority Boundaries

Route memory can inspire and inform. It cannot authorize.

It cannot:

- expand the study charter
- replace evidence refs
- replace AI reviewer judgment
- authorize quality ready, publication ready, finalize ready, or submission ready
- hide negative or failed paths
- force Codex CLI to follow a fixed recipe when stage evidence points elsewhere

Controller and quality surfaces remain responsible for boundaries, evidence, owner route, stop-loss, publication gate, and human gate.

## Relationship To Existing Archetypes

Existing `preferred_study_archetypes` and `research_route_bias_policy` are the first generation of route memory. They should be treated as high-level memory seeds and stage bias, not as exhaustive or binding route definitions.

Future migration may move them into a richer route-memory library, but the migration should preserve natural-language prose and Codex-first autonomy. It should not turn each archetype into a hard-coded workflow unless a specific route has matured into a separate audited capability with its own evidence, tests, and owner boundary.

## OPL Boundary

This policy belongs to MAS because publication-route experience is medical domain knowledge.

OPL may provide family-level discovery, indexing, stage descriptor refs, handoff, receipts, projection, and storage mechanics for domain knowledge packs. OPL must not own the medical content, choose the publication route, or turn MAS route memory into OPL-level truth.

The same mechanism can later support other domains, such as grant strategy memory in MAG or visual deliverable pattern memory in RCA. The content owner remains the domain agent.

## Related Memory Candidates

The current migration audit found several MAS surfaces that look similar to reusable recipes but should not all be handled the same way:

| surface | correct handling |
| --- | --- |
| `preferred_study_archetypes` and route-bias prose | Treat as first-generation natural-language route memory seeds. |
| AI reviewer repair lessons, route-back rationales, weak-result / negative-result handling | Write back only reusable lessons through stage closeout memory proposals; current-paper findings stay in evidence/review/controller ledgers. |
| journal-family expectations, recurring reviewer critique, claim-restraint lessons | Keep as natural-language review / publication-route memory unless they become audited gate requirements. |
| medical display template catalog, renderer contracts, layout QC, input schemas | Keep as strong audited display contracts; do not downgrade to route memory. |
| figure/table selection rationale and visual audit lessons across papers | Good candidate for natural-language memory linked from stage knowledge packets. |
| paper progress reconciler, owner route, publication gate, AI reviewer verdict, canonical package freshness proof | Strong controller / quality / artifact truth; never memory authority. |

The practical migration rule is: when a lesson helps Codex decide what to explore, keep it as prose memory; when it decides whether an artifact, claim, gate, or package is valid, keep it as a structured MAS-owned contract or truth surface.

## Current Implementation Posture

This policy is intentionally ahead of any large memory-store implementation. The useful work now is:

- keep the route memory cards natural-language-first;
- keep `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, and `stage_recall_index` as the small controlled retrieval/writeback surfaces;
- record candidate memories and their owner boundaries in docs before moving them into runtime machinery;
- preserve Codex CLI autonomy inside each stage.

Do not implement a separate publication recipe engine until a route has matured into an audited capability with clear evidence obligations, tests, owner boundary, and failure behavior.
