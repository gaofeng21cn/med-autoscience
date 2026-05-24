# 活跃文档

Owner: `MedAutoScience`
Purpose: `active_execution_and_gap_index`
State: `active_support`
Machine boundary: 人读索引。机器真相继续归 contracts、schemas、source、runtime ledgers、study workspaces、publication artifacts 与 owner receipts。

本目录是 OPL-family canonical 目录中承接 MAS 当前执行、当前计划、当前差距和 active baton 的位置。当前唯一 single Active Truth owner 是 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)：它维护当前唯一真相、目标态、已落地状态、功能/结构差距、测试/证据差距、近期完善计划和历史索引。dated closeout、过程流水、旧 full record 和 superseded plan 进入 `docs/history/**`。

旧 `docs/program/` active-baton 层已物理退役。当前 MAS 执行地图、论文自治目标、产品化依托、stage 形式计划和 landed foundation guard 文档都进入本目录。已完成或被 current owner surface 吸收的 framework migration / retirement 记录进入 history。`program_id` 与 `human_doc:program_*` 只作为语义 ID 保留，不代表物理 `docs/program/` 目录。

当前入口先看：

- [文档索引](../README.md)
- [当前状态](../status.md)
- [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)
- [MAS Current Development Lines](./current-development-lines.md)
- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)
- [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md)
- [MAS Stage Surfaces](../runtime/contracts/stage_surfaces.md)

过程归档只在需要追溯历史时读取，不作为 active 默认入口：

- [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)
- [Docs lifecycle governance closeout 2026-05-20](../history/program/docs_lifecycle_governance_closeout_2026_05_20.md)

## 当前 active 层次

| 层次 | 文档 | 当前作用 |
| --- | --- | --- |
| 理想差距 / 完善计划 | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | 对照 MAS 理想目标态，维护当前唯一真相、已落地状态、功能/结构差距、测试/证据差距、完善顺序、历史索引和禁止误写口径。 |
| 当前内容线索引 | [MAS Current Development Lines](./current-development-lines.md) | 把仍有效内容线归为 landed foundation、functional follow-through gate 或 production evidence gate；不维护第二 backlog，若与 gap plan 冲突以 gap plan 为准。 |
| 文档组合 / 历史归位 | [Program Portfolio Consolidation](./program_portfolio_consolidation.md) | 只说明 active program 文档唯一职责、历史记录去向和 direct retirement rule；不替代 gap plan，也不作为第二 backlog。 |
| 目标 / 验收 owner | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | 只定义 MAS 论文自治验收合同和 AI-first quality gate；dated evidence 与 full record 回 history。 |
| Stage pack owner | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | 只维护 stage/prompt/skill/knowledge/quality gate 的标准形态；长 proof 流水回 history。 |
| Product projection owner | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | 只维护 MAS 输出给 OPL App/workbench 的 refs-only 投影边界；不复制通用 workbench。 |
| Landed foundation guard | [MAS 单项目 MDS 吸收 program](./mas_single_project_mds_absorb_program.md)、[Domain Authority Refs Index Guard](../runtime/domain_authority_refs_index_guard.md) | 只保留 MDS provenance、monolith closeout、SQLite/file authority、quest/root Git retirement 和 drift guard；不再作为活跃实现队列。 |

实际开发按内容块推进，不按整份旧文档推进。P0/P1/P2/P3/P3a 的完整旧记录已经归档；当前 active owner 文档只保留当前 owner 边界、gate 分类和仍可执行的内容线。旧 full record、旧 board、旧 activation package、dated follow-through 和命令流水只作为 history provenance 读取。

active 文档不得继续追加历史增量长清单。若需要记录 proof、receipt、分支名、测试输出或 closeout 过程，写入 `docs/history/program/` 或对应 history 目录；active 层只保留当前 gate 是否仍 open、谁负责、下一条验证命令类别和不能误写的边界。

## 放置规则

- `docs/active/`：仍需要执行顺序、owner gate、当前差距或当前 owner plan 的文档。
- `docs/runtime/`：runtime contract、control surface、projection、display、active design；它说明已经或正在变成 runtime/API/contract 的技术面。
- `docs/delivery/`：manuscript、package、submission/export 和 medical-display delivery 支撑。
- `docs/references/`：支撑参考、parity、integration、MDS 学习和 mainline assessment；dated verification ledger 归 `docs/history/program/`。
- `docs/policies/`：稳定内部规则和长期 workflow/governance policy。
- `docs/history/program/`：旧 full record、closeout、activation package、dated recurring intake snapshot、process archive 和 superseded plan。

判断方式：如果内容还决定“接下来按什么顺序做、由谁验收、什么算完成”，放 `docs/active/`；如果已经沉淀成 runtime/interface 约束，放 `docs/runtime/`；如果只是背景、比较、学习或证据，放 `docs/references/`；如果只保留历史脉络或 dated process，放 `docs/history/`。
