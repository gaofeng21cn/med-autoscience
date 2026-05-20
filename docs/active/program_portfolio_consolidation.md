# Program Portfolio Consolidation

Status: `active_portfolio_governance`
Date: `2026-05-20`
Owner: `MedAutoScience`
Purpose: `active_program_document_lifecycle`
State: `active_support`
Machine boundary: 本文是人读 program 文档组合治理入口。机器真相继续归 `contracts/`、source、runtime/controller surfaces、product-entry manifest、sidecar receipt、owner receipts 和真实 workspace evidence。

## 当前结论

`docs/active/` 只承载仍需要执行顺序、owner gate、当前差距或当前完成门槛的文档。它不保存 dated proof ledger、attempt id、分支名、长 closeout 流水或旧 phase checklist。

MAS 当前唯一 gap / completion plan 是 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)。当前唯一执行地图是 [MAS 当前开发线路](./current-development-lines.md)。本文只说明各 program 文档的唯一职责、归档关系和禁止重复维护的内容。

## 当前 Program 职责表

| document | unique responsibility | state | 不承载 |
| --- | --- | --- | --- |
| [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | 唯一当前功能/结构差距、测试/证据差距、完善顺序和禁止误写口径。 | `active_plan` | 不保存 dated closeout、receipt 流水、旧 phase checklist。 |
| [MAS 当前开发线路](./current-development-lines.md) | 唯一内容级执行地图，按 `landed_foundation` / `functional_follow_through_gate` / `production_evidence_gate` 分配后续工作。 | `active_plan_index` | 不成为第二 gap matrix，不冻结瞬时 proof 计数。 |
| [AI-first 论文自治闭环](./ai_first_paper_autonomy_closure_program.md) | 论文自治目标和验收合同：真实 paper line 上的 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。 | `active_target_and_acceptance_owner` | 不维护 OPL provider 实现、App UI、旧 MDS/Hermes/local scheduler 退役清单。 |
| [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | MAS 侧 provider / sidecar / owner receipt / legacy-retirement 边界。 | `active_support` | 不维护 OPL framework 总路线，不把旧 phase checklist 当当前计划。 |
| [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | MAS 输出给 OPL App/workbench 的 refs-only 投影、safe action receipt、stage review / memory drilldown 边界。 | `active_support` | 不复制通用 workbench，不定义 study truth 或 publication readiness。 |
| [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | Stage / prompt / skill / knowledge / quality gate / review-index 的标准形态和横向守门。 | `active_support` | 不作为 OPL production closure 总计划，不维护长 proof ledger。 |
| [MAS 单项目 MDS 吸收](./mas_single_project_mds_absorb_program.md) | MDS retained-role、provenance、archive/import、parity oracle 和 monolith closeout guard。 | `landed_foundation_guard` | 不作为活跃 MDS migration queue，不恢复 MDS 默认 backend。 |
| [Runtime Lifecycle SQLite 迁移](./runtime_lifecycle_sqlite_migration_program.md) | SQLite/file authority、quest/root Git retirement、restore proof 和 runtime lifecycle drift guard。 | `landed_foundation_guard` | 不作为 broad runtime refactor board，不授权 study/publication/artifact truth。 |

## 历史归位

| content type | target |
| --- | --- |
| full record、旧 phase table、旧 activation package、旧 board、完整命令流水 | `docs/history/program/` |
| old runtime / outer-loop / wakeup / legacy boundary design | `docs/history/runtime/` |
| old Domain Harness OS / Open Harness OS / Research Foundry positioning | `docs/history/positioning/` |
| external learning dated intake | `docs/history/program/*_learning_intake_YYYY_MM_DD.md` |
| current target / current gap / current execution map | `docs/references/positioning/mas_ideal_state.md`、`docs/active/mas-ideal-state-gap-plan.md`、`docs/active/current-development-lines.md` |
| stable operating rule | `docs/policies/` |
| stable runtime/control/projection/display contract explanation | `docs/runtime/` |
| background support or parity oracle | `docs/references/` |

## Direct Retirement Rule

当旧模块、旧接口、旧 CLI alias、旧 wrapper、旧 facade、旧测试入口或旧文档入口已被当前 owner surface 替代时，默认完成形态是退役，而不是兼容保留：

1. 证明没有 default CLI/MCP/product-entry/app-skill/OPL active caller。
2. 证明没有 public surface、fixture 或 provenance 必须依赖该旧入口。
3. 证明 replacement owner surface、history link 或 tombstone contract 已存在。
4. 删除旧源码、命令 wrapper、alias、facade 和对应兼容测试；测试改断言当前 machine-readable contract、schema、CLI/API、manifest、generated artifact 或 fail-closed 行为。

满足上述条件后，不保留旧名兼容层，不新增聚合兼容测试，也不把旧文档路径当成稳定机器接口。

## 新内容准入

新增 program-like 内容必须先回答四个问题：

1. 是否改变当前功能/结构差距或测试/证据差距？如果是，更新 `mas-ideal-state-gap-plan.md`。
2. 是否改变实际执行顺序或 gate 分类？如果是，更新 `current-development-lines.md`。
3. 是否只是 dated proof、closeout、attempt、receipt、branch 或历史解释？如果是，写入 `docs/history/**` 或 verification ledger。
4. 是否变成稳定 runtime / policy / delivery / source / product / reference 规则？如果是，落入对应 canonical 目录，不扩写 active program。

无法回答这些问题的文档不应新增到 active layer。

## 验收

Program 文档治理的完成标准：

- active 层每份文档有唯一任务，不互相维护第二份 gap matrix 或第二份 execution queue。
- dated evidence、旧 closeout、旧路线和 superseded plan 只在 history/provenance 层保留。
- MAS 文档只维护 MAS-owned truth、authority、direct/hosted boundary 和上收候选；OPL/MAG/RCA backlog 不写进 MAS active docs。
- 旧兼容面满足退役条件后直接删除、archive 或 tombstone；不保留兼容 alias、facade、wrapper 或聚合测试。
- `docs/**` 不作为机器接口；代码和测试依赖 schema、JSON、CLI/API payload、manifest、contract、source path 或 durable semantic ID。
