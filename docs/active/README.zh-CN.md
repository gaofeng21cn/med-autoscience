# 活跃文档

Owner: `MedAutoScience`
Purpose: `active_execution_and_gap_index`
State: `active_support`
Machine boundary: 人读索引。机器真相继续归 contracts、schemas、source、runtime ledgers、study workspaces、publication artifacts 与 owner receipts。

本目录是 OPL-family canonical 目录中承接 MAS 当前执行、当前计划、当前差距、active baton 和 closeout evidence 的位置。

旧 `docs/program/` active-baton 层已物理退役。当前 MAS 执行地图、论文自治目标、framework migration owner、产品化依托、stage 形式计划和 landed foundation guard 文档都进入本目录。`program_id` 与 `human_doc:program_*` 只作为语义 ID 保留，不代表物理 `docs/program/` 目录。

当前入口先看：

- [文档索引](../README.zh-CN.md)
- [当前状态](../status.md)
- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)
- [MAS Current Development Lines](./current_development_lines.md)
- [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md)
- [MAS Stage Surfaces](../runtime/contracts/stage_surfaces.md)

## 当前 active 层次

| 层次 | 文档 | 当前作用 |
| --- | --- | --- |
| 目标 / 验收 | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | 定义当前 MAS 论文自治目标和最终验收合同：reviewer finding、repair work unit、gate replay、路线决策、stage knowledge/memory、真实 paper soak 和质量边界。 |
| 当前执行优先级 | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | framework-first 迁移线路：先完成 OPL 完整智能体框架，再迁移 MAS、分层沉淀新旧功能、退役旧默认依赖和兼容面。 |
| 横向 stage 形式 | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | 统一每个 MAS stage 的 stage card、route contract、prompt/skill、tool surface、knowledge packet、closeout obligation、一页式 Stage Deliverable Review Page / Index、quality gate 和 OPL projection boundary。 |
| 产品化依托 | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | 跟随 framework migration 的产品化路径，把迁移后的 MAS/OPL 状态变成 OPL App Runtime Workbench 中可见、可审阅、可受控的用户体验。 |
| 已落地基础 | [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md) | 已落地的 monolith / provenance owner 文档，只保存当前边界和 guard；完整历史记录在 `docs/history/program/`。 |
| 已落地基础 | [Runtime lifecycle SQLite 迁移 program](./runtime_lifecycle_sqlite_migration_program.md) | 已落地的 runtime lifecycle guard 文档，只保存当前 SQLite/file authority、quest/root Git retirement 和 drift 维护规则；完整历史记录在 `docs/history/program/`。 |

实际开发按内容块推进，不按整份旧文档推进。P1/P2 的完整旧记录已经归档；当前文件只保留 owner 边界、优先级和可执行内容线。

## 放置规则

- `docs/active/`：仍需要执行顺序、owner gate、closeout evidence 或 landed provenance 的当前计划和 owner 文档。
- `docs/runtime/`：runtime contract、control surface、projection、display、active design；它说明已经或正在变成 runtime/API/contract 的技术面。
- `docs/delivery/`：manuscript、package、submission/export 和 medical-display delivery 支撑。
- `docs/references/`：支撑参考、parity、integration、MDS 学习、verification ledger、mainline assessment。
- `docs/policies/`：稳定内部规则和长期 workflow/governance policy。
- `docs/history/program/`：旧 full record、closeout、activation package、dated recurring intake snapshot 和 superseded plan。

判断方式：如果内容还决定“接下来按什么顺序做、由谁验收、什么算完成”，放 `docs/active/`；如果已经沉淀成 runtime/interface 约束，放 `docs/runtime/`；如果只是背景、比较、学习或证据，放 `docs/references/`；如果只保留历史脉络，放 `docs/history/`。
