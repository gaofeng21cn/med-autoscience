# Program 目录

`docs/program/` 只保留当前开发计划层，不再承载所有 policy、reference、checklist、ledger 或历史 closeout。

当前 active 入口固定为五件：

- [Program portfolio consolidation](./program_portfolio_consolidation.md)：唯一规划入口和执行队列。
- [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md)：把 MAS progress、Live Console、执行器对话、terminal attach、安全 actions 和 artifacts 接入 OPL App Runtime Workbench，同时保留 MAS domain authority 的 App-native 集成计划。
- [AI-first paper autonomy closure program](./ai_first_paper_autonomy_closure_program.md)：最高优先级 program，负责关闭医学论文从 AI reviewer finding 到自动修复、复评、路线决策和真实 paper soak 的闭环。
- [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md)：MDS 退场、MAS 吸收、workspace layout 收敛、entry compatibility retirement 与 no-history physical absorb 的执行总计划。
- [Runtime lifecycle SQLite 迁移 program](./runtime_lifecycle_sqlite_migration_program.md)：MAS absorb program 下的 runtime / Git / SQLite 子计划。

支撑材料放在其他目录：

- 稳定操作规则：`docs/policies/`
- MDS 学习、parity、ledger 和技术参考：`docs/references/`
- 已退役 board、closeout、周期性支持线 dated intake snapshot 和已落地 program 记录：`docs/history/program/`

DeepScientist latest-update learning 这类 learning/intake 工作仍由对应 reference policy/protocol 触发，并由 `MAS` 直接面向 upstream DeepScientist 执行。`docs/history/program/` 里的 dated 文件是单轮快照，不表示 recurring lane 已退役。

新增 program board 前，必须先通过 `program_portfolio_consolidation.md` 映射到当前 portfolio。
