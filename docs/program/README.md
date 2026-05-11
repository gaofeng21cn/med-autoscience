# Program Directory

`docs/program/` is the current MAS development-plan layer. It holds programs that still need execution order, owner docs, or closeout gates. Stable rules live in `docs/policies/`; references and learning material live in `docs/references/`; completed or retired records live in `docs/history/program/`.

## Current Entry

- [Program Portfolio Consolidation](./program_portfolio_consolidation.md): the portfolio entry for current state, active programs, landed history, and execution order.

## Active Programs

| Level | program | role |
| --- | --- | --- |
| `P0` | [AI-first paper autonomy closure program](./ai_first_paper_autonomy_closure_program.md) | Highest-priority manuscript autonomy loop: AI reviewer findings, repair work units, re-evaluation, route decisions, stage knowledge/memory, and real paper soak. |
| `P1` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | App-native projection of MAS progress, Live Console, conversation, terminal attach, safe actions, and artifacts into the OPL App Runtime Workbench. |
| `P2` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | Migration of MAS scheduler/watchdog/legacy runtime surfaces after OPL stage-led family runtime and the Temporal provider have real operating evidence. |
| `P3` | [MAS single-project MDS absorb program](./mas_single_project_mds_absorb_program.md) | Owner doc for MAS monolith, retained MDS capabilities, workspace layout, entry compatibility, and no-history absorb boundaries. |
| `P3a` | [Runtime lifecycle SQLite migration program](./runtime_lifecycle_sqlite_migration_program.md) | Runtime / Git / SQLite subprogram for lifecycle authority, restore proof, and migration ledger maintenance. |

## Support And History

- Stable operating policies: `docs/policies/`
- MDS learning, parity, ledgers, and technical references: `docs/references/`
- Retired boards, closeouts, dated recurring intake snapshots, and landed records: `docs/history/program/`

Recurring support lanes such as DeepScientist latest-update learning are triggered through their reference policies and protocols, then executed by `MAS` against upstream DeepScientist. Dated files in `docs/history/program/` are single-run snapshots; current entry points, trigger rules, and absorption rules live in `docs/references/` and `docs/status.md`.

Before adding a program board, map its level, owner doc, closeout gate, and archive rule through [Program Portfolio Consolidation](./program_portfolio_consolidation.md).
