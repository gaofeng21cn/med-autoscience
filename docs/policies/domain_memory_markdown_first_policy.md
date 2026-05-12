# Domain Memory Markdown-First Policy

Status: `active policy`
Date: `2026-05-12`
Owner: `MedAutoScience`
Purpose: define how MAS keeps natural-language domain memory maintainable for Codex-first, stage-led execution.
State: `active governance rule`
Machine boundary: this is a human-readable policy. Runtime truth, receipts, indexes, gates, ledgers, controller decisions, and generated artifacts remain on their existing structured surfaces.

## Rule

Human-maintained natural-language experience memory must be Markdown-first.

Use Markdown as the canonical body when the content is meant to help Codex reason, explore, compare routes, remember recurring reviewer expectations, or reuse experience across papers. JSON may index, project, cache, receipt, or materialize that memory, but it must not be the maintainer-facing knowledge body.

## Applies To

Markdown-first is required for:

- publication route experience, such as classifier, subtype, external validation, negative-result stop-loss, survey trend, or mechanistic sidecar routes;
- reusable stage closeout lessons after they are accepted as cross-paper memory;
- journal-family expectations, claim-restraint lessons, reviewer critique patterns, and route-back rationales;
- figure/table selection rationale, visual audit lessons, readability failures, and article-level display tradeoffs;
- upstream method-learning notes where the lesson is prose guidance rather than a runnable contract.

Structured surfaces remain appropriate for:

- controller decisions, publication eval, quality verdicts, gates, package freshness, evidence ledgers, review ledgers, study charter, and artifact manifests;
- workspace memory packs generated from Markdown or accepted writeback;
- migration receipts, router receipts, sidecar dispatch receipts, OPL/Aion body-free projections, inventories, freshness summaries, and locator refs;
- schemas, test fixtures, parity oracles, and source-provenance manifests where the value is machine validation rather than human prose.

## Maintenance Pattern

The canonical pattern is:

1. `*.md` holds the full memory body and maintainer-editable prose.
2. A small JSON index may list stable ids, route families, stages, source refs, status, and a canonical Markdown locator.
3. MAS owner code may parse or apply selected Markdown into a workspace pack.
4. Workspace packs and receipts are generated/applied MAS owner artifacts, not the canonical editing surface.
5. OPL/Aion receives refs, status, freshness, grouped inventory, and receipts only; it does not own or mutate MAS memory prose.

This keeps Codex CLI free to reason over rich prose without turning exploratory medical research into a rigid recipe engine.

## Current MAS Audit

The current repo-tracked JSON files are:

| file | classification | action |
| --- | --- | --- |
| `docs/policies/study-workflow/publication_route_memory_seed_fixture.json` | seed index / locator | kept as JSON index; canonical body moved to `publication_route_memory_library.md`. |
| `docs/references/med-deepscientist/source_provenance.json` | source provenance manifest | keep JSON; it records external source provenance and capability refs, not the natural-language memory body. |
| `tests/fixtures/live_console/mds_webui_cleanroom_oracle.json` | test oracle fixture | keep JSON; it supports deterministic tests. |

Memory-like runtime surfaces in `portfolio/research_memory/**`, `artifacts/stage_knowledge/**`, receipts, and OPL projections remain structured because they are generated owner surfaces, body-free projections, or runtime proof. They should not become the primary maintainer editing interface for natural-language experience.

## Publication Route Memory Entry

The publication-route memory canonical body is now:

- `docs/policies/study-workflow/publication_route_memory_library.md`

The companion JSON index is:

- `docs/policies/study-workflow/publication_route_memory_seed_fixture.json`

Maintainers edit the Markdown library. MAS may apply it into a workspace memory pack and produce receipts. Codex CLI can read the Markdown directly when it needs rich route experience.
