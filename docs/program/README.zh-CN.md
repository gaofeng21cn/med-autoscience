# Program 目录

`docs/program/` 只保留当前开发计划层，不再承载所有 policy、reference、checklist、ledger 或历史 closeout。

当前 active 入口固定为三件：

- [Program portfolio consolidation](./program_portfolio_consolidation.md)：唯一规划入口和执行队列。
- [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md)：MDS 退场、MAS 吸收、workspace layout 收敛、entry compatibility retirement 与 no-history physical absorb 的执行总计划。
- [Runtime lifecycle SQLite 迁移 program](./runtime_lifecycle_sqlite_migration_program.md)：MAS absorb program 下的 runtime / Git / SQLite 子计划。

支撑材料放在其他目录：

- 稳定操作规则：`docs/policies/`
- MDS 学习、parity、ledger 和技术参考：`docs/references/`
- 已退役 board、closeout、intake snapshot 和已落地 program 记录：`docs/history/program/`

新增 program board 前，必须先通过 `program_portfolio_consolidation.md` 映射到当前 portfolio。
