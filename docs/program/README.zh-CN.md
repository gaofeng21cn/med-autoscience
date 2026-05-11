# Program 目录

`docs/program/` 是 MAS 的 program 生命周期层。这里保存当前论文自治目标、正在支撑该目标的产品化与框架化实现路径，以及仍承载 provenance 或 guard 责任的已落地基础 owner 文档。这里不是并列待办清单。

## 当前入口

- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)：当前 program 组合总入口。先读这份文档，理解目标层、实现依托层、已落地基础层、内容级处置表和归档规则。

## 当前 program 层次

| 层次 | 文档 | 当前作用 |
| --- | --- | --- |
| 目标 / 验收 | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | 定义当前 MAS 论文自治目标和验收合同：reviewer finding、repair work unit、gate replay、路线决策、stage knowledge/memory、真实 paper soak 和质量边界。 |
| 产品化依托 | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | 当前产品化实现路径，把 P0 目标变成 OPL App Runtime Workbench 中可见、可审阅、可受控的用户体验。 |
| 框架化依托 | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | 当前框架化实现路径，把共享运行外围逐步交给 OPL Codex-first、stage-led framework，同时保留 MAS domain truth。 |
| 已落地基础 | [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md) | 已落地的 monolith / provenance owner 文档，只保存当前边界和 guard；完整历史记录在 `docs/history/program/`。 |
| 已落地基础 | [Runtime lifecycle SQLite 迁移 program](./runtime_lifecycle_sqlite_migration_program.md) | 已落地的 runtime lifecycle guard 文档，只保存当前 SQLite/file authority、quest/root Git retirement 和 drift 维护规则；完整历史记录在 `docs/history/program/`。 |

当前真实读法是：P0 给出目标和验收口径，P1/P2 给出产品化与框架化实现路径，P3/P3a 给出已完成基础和后续 guard 证据。

P0 立项最早，但它的当前实现依托已经上升到 OPL framework 层。MAS 继续持有医学研究、论文质量和 artifact authority；OPL 提供 Codex-first、stage-led 的智能体运行框架，让 MAS 作为 domain agent 被托管、唤醒、恢复和投影。

## 支撑与历史

- 稳定操作规则：`docs/policies/`
- MDS 学习、parity、ledger 和技术参考：`docs/references/`
- 已退役 board、closeout、周期性支持线 dated intake snapshot 和已落地 program 记录：`docs/history/program/`

DeepScientist latest-update learning 这类 recurring support lane 由对应 reference policy/protocol 触发，并由 `MAS` 直接面向 upstream DeepScientist 执行。`docs/history/program/` 里的 dated 文件是单轮快照；当前入口、触发条件和吸收规则由 `docs/references/` 与 `docs/status.md` 持有。

新增 program board 或修改旧计划前，先在 [Program Portfolio Consolidation](./program_portfolio_consolidation.md) 中把每个内容块归类为目标/结果、active enabler、landed foundation、support reference、dated snapshot 或 tombstone。
