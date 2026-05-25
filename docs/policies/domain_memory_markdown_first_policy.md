# Domain Memory Markdown-First Policy

Status: `active policy`
Date: `2026-05-13`
Owner: `MedAutoScience`
Purpose: define how MAS keeps natural-language domain memory maintainable for Codex-first, stage-led execution.
State: `active governance rule`
Machine boundary: this is a human-readable policy. Runtime truth, receipts, indexes, gates, ledgers, controller decisions, and generated artifacts remain on their existing structured surfaces.

## Rule

Human-maintained natural-language experience memory must be Markdown-first.

Use Markdown as the canonical body when the content is meant to help Codex reason, explore, compare routes, remember recurring reviewer expectations, or reuse experience across papers. JSON may index, project, cache, receipt, or materialize that memory, but it must not be the maintainer-facing knowledge body.

## Applies To

Markdown-first is required for:

- publication route experience, such as classifier, subtype, external validation, negative-result stop-loss, survey trend, or mechanistic domain-handler routes;
- reusable stage closeout lessons after they are accepted as cross-paper memory;
- journal-family expectations, claim-restraint lessons, reviewer critique patterns, and route-back rationales;
- figure/table selection rationale, visual audit lessons, readability failures, and article-level display tradeoffs;
- upstream method-learning notes where the lesson is prose guidance rather than a runnable contract.

Structured surfaces remain appropriate for:

- controller decisions, publication eval, quality verdicts, gates, package freshness, evidence ledgers, review ledgers, study charter, and artifact manifests;
- workspace memory packs generated from Markdown or accepted writeback;
- migration receipts, router receipts, domain-handler dispatch receipts, OPL/Aion body-free projections, inventories, freshness summaries, and locator refs;
- schemas, test fixtures, parity oracles, and source-provenance manifests where the value is machine validation rather than human prose.

## Unified Memory Layers

MAS memory is managed as one family of owner-controlled memory surfaces, not as unrelated one-off stores at each level.

| layer | scope | canonical body | structured surfaces | executor entry |
| --- | --- | --- | --- | --- |
| Domain memory | reusable MAS medical knowledge across workspaces, such as publication-route experience, route-bias prose, reviewer-pattern lessons, and figure/table rationale | repo Markdown under `docs/policies/**` when the knowledge is natural language | seed indexes, locator refs, workspace packs, inventories, receipts | direct Markdown reading when rich context is needed; stage packets carry small refs/summaries |
| Workspace memory | disease workspace knowledge across multiple studies, such as topic landscape, dataset-question map, venue intelligence, literature coverage, and cross-study recall | `portfolio/research_memory/*.md` for human/Codex prose | `registry.yaml`, literature JSONL/BibTeX/coverage JSON, workspace memory packs | `stage_knowledge_packet.input_refs` and `high_signal_memory` |
| Study memory | one paper line's reusable context, such as failed paths, selected/rejected lines, reviewer lessons, claim-boundary decisions, and route-back rationale | study artifacts may include Markdown notes, but study truth remains in controller/evidence/review surfaces | `study_charter`, evidence ledger, review ledger, controller decisions, publication eval, claim/display maps | `stage_knowledge_packet.input_refs` plus stage-specific obligations |
| Stage memory | stage-local input and closeout handoff | stage notes can be Markdown, but closeout routing is structured | `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, `stage_recall_index` | executor payload gets `input_contract.required_refs.stage_knowledge_packet` |
| Projection memory | OPL/Aion/family display and provider handoff | no body ownership | body-free refs, freshness, receipt counts, accepted/rejected refs | read-only projection; no writeback acceptance or memory body mutation |

The shared logic is: prose lives in Markdown when it is meant for agent reasoning; machine surfaces carry ids, refs, freshness, receipts, gates, and owner boundaries; stage packets retrieve only small relevant refs; writeback flows through typed closeout and MAS router receipts.

## Maintenance Pattern

The canonical pattern is:

1. `*.md` holds the full memory body and maintainer-editable prose.
2. A small JSON index may list stable ids, route families, stages, source refs, status, and a canonical Markdown locator.
3. MAS owner code may parse or apply selected Markdown into a workspace pack.
4. Workspace packs and receipts are generated/applied MAS owner artifacts, not the canonical editing surface.
5. OPL/Aion receives refs, status, freshness, grouped inventory, and receipts only; it does not own or mutate MAS memory prose.

This keeps Codex CLI free to reason over rich prose without turning exploratory medical research into a rigid recipe engine.

## Current MAS Audit

The current repo-tracked structured files relevant to memory are:

| file | classification | action |
| --- | --- | --- |
| `docs/policies/study-workflow/publication_route_memory_seed_fixture.json` | seed index / locator | kept as JSON index; canonical body moved to `publication_route_memory_library.md`. |
| `docs/references/med-deepscientist/source_provenance.json` | source provenance manifest | keep JSON; it records external source provenance and capability refs, not the natural-language memory body. |
| retired console clean-room oracle fixture | test oracle fixture | keep JSON only in history/provenance context; it supports deterministic tests and is not an active memory body. |

Memory-like runtime surfaces in `portfolio/research_memory/**`, `artifacts/stage_knowledge/**`, receipts, and OPL projections remain structured because they are generated owner surfaces, body-free projections, or runtime proof. They should not become the primary maintainer editing interface for natural-language experience.

The previous non-Markdown-first agent-context residues have been migrated:

| previous surface | current canonical body | current role of code |
| --- | --- | --- |
| `src/med_autoscience/policies/study_archetypes.py` | `docs/policies/study-workflow/study_archetypes.md` | parser, validator, typed API, overlay renderer |
| `src/med_autoscience/policies/research_route_bias.py` | `docs/policies/study-workflow/research_route_bias_policy.md` | parser, validator, typed API, overlay renderer |

`agent/stages/stage_route_contract.yaml` is still structured because it is the MAS route/stage contract source, not a natural-language memory body. It defines route ids, entry modes, gates, durable outputs, route-back triggers, stage knowledge obligations, and derived OPL/family descriptors. It may later gain a richer Markdown projection for human reading, but replacing the contract with Markdown would move route authority into prose and break current stage-surface tests.

## Publication Route Memory Entry

The publication-route memory canonical body is now:

- `docs/policies/study-workflow/publication_route_memory_library.md`

The companion JSON index is:

- `docs/policies/study-workflow/publication_route_memory_seed_fixture.json`

Maintainers edit the Markdown library. MAS may apply it into a workspace memory pack and produce receipts. Codex CLI can read the Markdown directly when it needs rich route experience.
