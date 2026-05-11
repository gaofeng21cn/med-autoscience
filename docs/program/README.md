# Program Directory

`docs/program/` is the MAS program-lifecycle layer. It holds the current paper-autonomy target, the OPL framework-first migration line, the productization enabler, and the landed foundation owner docs that still carry provenance or guard obligations. It is not a flat backlog.

## Current Entry

- [Program Portfolio Consolidation](./program_portfolio_consolidation.md): the current portfolio entry. Read it first for the target, framework-first execution, productization, landed foundation, content-level disposition, and archive rules.
- [MAS Current Development Lines](./current_development_lines.md): the current content-level development map. Use it before executing or evaluating old program content to decide whether a block belongs to OPL framework, MAS migration, feature retirement, P1 productization, P0 final soak, P3/P3a, or support.

## Current Program Layers

| Layer | document | current role |
| --- | --- | --- |
| Target / acceptance | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | Defines the MAS paper-autonomy target and final acceptance contract: reviewer findings, repair units, gate replay, route decisions, stage knowledge/memory, live paper soak, and quality boundaries. |
| Current execution priority | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | Framework-first migration line: finish the OPL agent framework, migrate MAS, partition and preserve new/old capabilities, then retire old default dependencies and compatibility surfaces. |
| Product enabler | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | Productization lane that follows framework migration and makes migrated MAS/OPL state visible and controllable through the OPL App Runtime Workbench. |
| Landed foundation | [MAS single-project MDS absorb program](./mas_single_project_mds_absorb_program.md) | Landed monolith/provenance owner doc. It now preserves the current boundary and guard rules; the full historical record lives in `docs/history/program/`. |
| Landed foundation | [Runtime lifecycle SQLite migration program](./runtime_lifecycle_sqlite_migration_program.md) | Landed runtime-lifecycle guard doc. It now preserves the current SQLite/file authority, quest/root Git retirement, and drift rules; the full historical record lives in `docs/history/program/`. |

The current execution reading is: P0 supplies the target and acceptance criteria; P2 first delivers the OPL framework foundation, MAS framework migration, capability partitioning, and legacy retirement; P1 productizes the migrated state; P0 then runs final paper-line soak / App E2E acceptance; P3/P3a supply landed foundation evidence and maintenance guardrails throughout.

P0 was started first, but its current implementation dependency now lives at the OPL framework layer. MAS keeps medical research, paper quality, and artifact authority; OPL provides the Codex-first, stage-led agent framework that hosts, wakes, recovers, and projects MAS as a domain agent.

Actual development now proceeds by content block, not by completing every section of an old whole-file plan. The full old P1/P2 records are archived; the current files keep owner boundaries, priority, and active content lanes.

## Where MAS Planning Docs Live

Current rule:

- `docs/program/`: current plans and owner docs that still need program-level execution order, owner gates, closeout evidence, or landed provenance.
- `docs/runtime/`: runtime contracts, control surfaces, projections, display contracts, and active designs that are becoming technical runtime/API/contract surfaces.
- `docs/references/`: support references, parity, integration notes, MDS learning, verification ledgers, and mainline assessments. It does not own active backlog.
- `docs/policies/`: stable internal rules and long-lived workflow/governance policy.
- `docs/history/program/`: old full records, closeouts, activation packages, dated recurring intake snapshots, and superseded plans.

Use this decision rule: if the content still decides what happens next, who owns closeout, or what counts as done, keep it in `docs/program/`; if it has become a runtime/interface constraint, move it to `docs/runtime/`; if it is background, comparison, learning, or evidence, use `docs/references/`; if it only preserves historical context, use `docs/history/`.

## Support And History

Recurring support lanes such as DeepScientist latest-update learning are triggered through their reference policies and protocols, then executed by `MAS` against upstream DeepScientist. Dated files in `docs/history/program/` are single-run snapshots; current entry points, trigger rules, and absorption rules live in `docs/references/` and `docs/status.md`.

Before adding a program board or editing an old plan, map each content block through [Program Portfolio Consolidation](./program_portfolio_consolidation.md) and [MAS Current Development Lines](./current_development_lines.md): OPL framework, MAS migration, feature retirement, product enabler, target acceptance, landed foundation, support reference, dated snapshot, or tombstone.
