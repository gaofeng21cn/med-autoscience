# Program 目录

`docs/program/` 是 MAS 的 program 生命周期层。这里保存当前论文自治目标、OPL framework-first 迁移线路、产品化依托，以及仍承载 provenance 或 guard 责任的已落地基础 owner 文档。这里不是并列待办清单。

## 当前入口

- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)：当前 program 组合总入口。先读这份文档，理解目标层、framework-first 执行层、产品化层、已落地基础层、内容级处置表和归档规则。
- [MAS Current Development Lines](./current_development_lines.md)：当前内容级开发线路图。执行或评估旧 program 内容前，先用它判断内容块属于 OPL framework、MAS migration、feature retirement、P1 productization、P0 final soak、P3/P3a/support 的哪一条线。
- [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md)：横向 stage 形式统一计划。修改 stage prompt、skill、tool、knowledge packet、closeout memory、quality pack、最终人读 Stage Deliverable Review Page、Stage Deliverable Index 或 OPL stage descriptor 前先读这份文档。
- [MAS Stage Surfaces](../runtime/contracts/stage_surfaces.md)：主 MAS routes 的生成人读 stage cards。该 Markdown 只是 `src/med_autoscience/stage_surface_contract.py` 与 canonical route contract 的渲染面，不是机器真相。

## 当前 program 层次

| 层次 | 文档 | 当前作用 |
| --- | --- | --- |
| 目标 / 验收 | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | 定义当前 MAS 论文自治目标和最终验收合同：reviewer finding、repair work unit、gate replay、路线决策、stage knowledge/memory、真实 paper soak 和质量边界。 |
| 当前执行优先级 | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | framework-first 迁移线路：先完成 OPL 完整智能体框架，再迁移 MAS、分层沉淀新旧功能、退役旧默认依赖和兼容面。 |
| 横向 stage 形式 | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | 统一每个 MAS stage 的 stage card、route contract、prompt/skill、tool surface、knowledge packet、closeout obligation、一页式 Stage Deliverable Review Page / Index、quality gate 和 OPL projection boundary。 |
| 产品化依托 | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | 跟随 framework migration 的产品化路径，把迁移后的 MAS/OPL 状态变成 OPL App Runtime Workbench 中可见、可审阅、可受控的用户体验。 |
| 已落地基础 | [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md) | 已落地的 monolith / provenance owner 文档，只保存当前边界和 guard；完整历史记录在 `docs/history/program/`。 |
| 已落地基础 | [Runtime lifecycle SQLite 迁移 program](./runtime_lifecycle_sqlite_migration_program.md) | 已落地的 runtime lifecycle guard 文档，只保存当前 SQLite/file authority、quest/root Git retirement 和 drift 维护规则；完整历史记录在 `docs/history/program/`。 |

当前真实执行顺序是：P0 给出目标和验收口径；P2 先完成 OPL framework foundation、MAS framework migration、功能分层沉淀和旧面退役；P1 产品化迁移后的可见面；P0 最后做真实 paper-line soak / App E2E 验收；P3/P3a 贯穿提供已完成基础和后续 guard 证据。

P0 立项最早，但当前实现依托已经上升到 OPL framework 层。MAS 继续持有医学研究、论文质量和 artifact authority；OPL 提供 stage-led、以 Agent executor 为最小执行单位的智能体运行框架，让 MAS 作为 domain agent 被托管、唤醒、恢复和投影。

实际开发按内容块推进，不按整份旧文档推进。P1/P2 的完整旧记录已经归档；当前文件只保留 owner 边界、优先级和可执行内容线。

## MAS 规划文档放在哪里

当前规则是：

- `docs/program/`：仍需要 program 级阅读顺序、owner gate、closeout evidence 或 landed provenance 的当前计划和 owner 文档。
- `docs/runtime/`：runtime contract、control surface、projection、display、active design；它说明已经或正在变成 runtime/API/contract 的技术面。
- `docs/references/`：支撑参考、parity、integration、MDS 学习、verification ledger、mainline assessment；它不持有 active backlog。
- `docs/policies/`：稳定内部规则和长期 workflow/governance policy。
- `docs/history/program/`：旧 full record、closeout、activation package、dated recurring intake snapshot 和 superseded plan。

判断方式：如果内容还决定“接下来按什么顺序做、由谁验收、什么算完成”，放 `docs/program/`；如果已经沉淀成 runtime/interface 约束，放 `docs/runtime/`；如果只是背景、比较、学习或证据，放 `docs/references/`；如果只保留历史脉络，放 `docs/history/`。

## 支撑与历史

DeepScientist latest-update learning 这类 recurring support lane 由对应 reference policy/protocol 触发，并由 `MAS` 直接面向 upstream DeepScientist 执行。`docs/history/program/` 里的 dated 文件是单轮快照；当前入口、触发条件和吸收规则由 `docs/references/` 与 `docs/status.md` 持有。

新增 program board 或修改旧计划前，先在 [Program Portfolio Consolidation](./program_portfolio_consolidation.md) 与 [MAS Current Development Lines](./current_development_lines.md) 中把每个内容块归类为 OPL framework、MAS migration、feature retirement、product enabler、target acceptance、landed foundation、support reference、dated snapshot 或 tombstone。
