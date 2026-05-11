# Program 目录

`docs/program/` 是 MAS 当前开发计划层。这里放仍在推进、仍需维护执行顺序或仍承载 closeout gate 的 program；稳定规则进入 `docs/policies/`，参考与学习材料进入 `docs/references/`，已完成或退役的计划记录进入 `docs/history/program/`。

## 当前入口

- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)：当前 program 组合的总入口。它给出当前状态、活跃 program、已收口历史和执行队列。

## 当前活跃 program

| 层级 | program | 作用 |
| --- | --- | --- |
| `P0` | [AI-first paper autonomy closure program](./ai_first_paper_autonomy_closure_program.md) | 当前最高优先级医学论文主循环：AI reviewer finding、repair work unit、复评、路线决策、stage knowledge/memory 和真实 paper soak。 |
| `P1` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | 把 MAS progress、Live Console、执行器对话、terminal attach、安全 actions 和 artifacts 接入 OPL App Runtime Workbench。 |
| `P2` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | 在 OPL stage-led family runtime 和 Temporal provider 具备真实运行证据后，迁移 MAS scheduler/watchdog/legacy runtime surface。 |
| `P3` | [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md) | 记录 MAS monolith、MDS 能力吸收、workspace layout、entry compatibility 和 no-history absorb 的执行边界；当前作为 landed owner doc 和后续 provenance 入口维护。 |
| `P3a` | [Runtime lifecycle SQLite 迁移 program](./runtime_lifecycle_sqlite_migration_program.md) | MAS absorb program 下的 runtime / Git / SQLite 子计划；当前作为 runtime lifecycle authority、restore proof 和迁移 ledger 的 owner doc 维护。 |

## 支撑与历史

- 稳定操作规则：`docs/policies/`
- MDS 学习、parity、ledger 和技术参考：`docs/references/`
- 已退役 board、closeout、周期性支持线 dated intake snapshot 和已落地 program 记录：`docs/history/program/`

DeepScientist latest-update learning 这类 recurring support lane 由对应 reference policy/protocol 触发，并由 `MAS` 直接面向 upstream DeepScientist 执行。`docs/history/program/` 里的 dated 文件是单轮快照；当前入口、触发条件和吸收规则由 `docs/references/` 与 `docs/status.md` 持有。

新增 program board 前，先在 [Program Portfolio Consolidation](./program_portfolio_consolidation.md) 中确定层级、owner doc、closeout gate 和历史归档规则。
