# Program Portfolio Consolidation

Status: `active portfolio governance`
Date: `2026-05-07`
Owner: `MedAutoScience`

## 结论

`docs/program/program_portfolio_consolidation.md` 是后续 MAS/MDS 收敛工作的唯一总控入口。Agent 接到后续执行任务时，先读本文，再按本文的 next execution queue 选择 lane、worktree、验证、吸收和清理；无需另开规划会。

当前三层关系固定如下：

1. 本文是唯一 portfolio 入口，负责决定 active owner doc、执行顺序和 closeout 口径。
2. `mas_single_project_mds_absorb_program.md` 是 MDS 退场、MAS 单项目吸收、workspace layout 收敛、entry compat retirement 和 no-history physical absorb 的总执行计划。
3. `runtime_lifecycle_sqlite_migration_program.md` 是 MAS single-project absorb 之下的 runtime / Git 子计划，负责 runtime lifecycle SQLite authority、workspace root Git full retirement、quest Git retirement、restore proof 和 lifecycle ledger。
4. `mas_mds_autonomy_operating_system_program.md`、`mas_mds_unified_enhancement_program.md` 与 owner-boundary、parity matrix、completion ledger、preflight / cleanup / gate 文档继续作为方向板、增强 backlog、合同、台账和操作政策保留，不再作为并行总控入口。

因此，Git 退役和 MAS 吸收 MDS 不作为两条互相竞争的改造线推进。技术实现可以分 lane 并行，但必须在同一个 authority contract、同一个 cutover gate 和同一个 closeout ledger 下吸收。SQLite runtime authority 接管的是 MDS Git-era 的 runtime lifecycle、lineage、workspace allocation、checkpoint metadata、diff / Canvas read model、restore index 和 runtime lifecycle ledger；MAS single-project absorb 接管的是产品入口、owner 边界、代码归属、真实 workspace layout 和 compatibility retirement。

## Next Execution Queue

后续 Agent 默认按下面队列自动取下一项；只有遇到真实 blocker、外部 active owner 冲突或用户改口时才暂停说明。

| order | execution lane | owner doc | required closeout |
| --- | --- | --- | --- |
| `1` | `workspace_layout_de_mds_ds` | `mas_single_project_mds_absorb_program.md` | 用户/医生可见 workspace layout、profile/docs 和 quest 管理命名去 MDS/DS 化；旧路径仅保留为 migration ledger、restore proof 或 maintainer diagnostic。 |
| `2` | `profile_entry_compat_retirement` | `mas_single_project_mds_absorb_program.md` | 退役 profile 字段兼容、MDS product entry、默认 legacy reader/fallback；保留入口必须显式标成 legacy diagnostic 并 fail-closed。 |
| `3` | `no_history_physical_absorb` | `mas_single_project_mds_absorb_program.md` | 按 no-history import、author audit、provenance、parity proof 和 rollback surface 吸收可保留 MDS 能力。 |

本文是队列 authority。实现 lane 可以并行拆分，但吸收顺序仍按上表 gate；不能绕过 portfolio 直接新建另一套 program board。

## 推进模型

后续推进采用一条主序列、多个可并行 implementation lane：

| order | portfolio gate | owner doc | 并行性 |
| --- | --- | --- | --- |
| `A0_program_portfolio_freeze` | 固定 active / support / historical 分类，停止新建重复 program board。 | 本文 | 可单独落地。 |
| `A1_authority_contract` | 固定 MAS owner matrix、SQLite runtime authority schema、MDS oracle-only 规则。 | `mas_mds_owner_boundary_refactor_plan.md`、`runtime_lifecycle_sqlite_migration_program.md` | `Q0` 必须先完成，其他 lane 只能读合同。 |
| `A2_repo_capability_absorb` | 把 MDS Git-era branch/worktree/checkpoint/diff/canvas 语义迁入 SQLite lineage/materializer/projection。 | `mas_single_project_mds_absorb_program.md`、`runtime_lifecycle_sqlite_migration_program.md` | `Q1/Q2/Q3` 可按 disjoint write set 并行。 |
| `A3_workspace_cutover` | 当前 NF-PitNET、DM-CVD / DPCC、AS biologics、HeRR 等 workspace 进入 SQLite-backed runtime layout，quest `.git` 和 workspace root Git 退为 restore diagnostic archive；new workspace no root Git / no quest Git。 | `runtime_lifecycle_sqlite_migration_program.md` | current-project active-path quest Git 与 workspace root Git 已 verified；下一步是用户可见 layout 去 MDS/DS 化。 |
| `A4_entry_and_compat_retirement` | MDS product entry、默认 Git writer、Git worktree writer、隐式 Git diff/log reader 退役；root Git 只允许作为 legacy maintenance diagnostic 被显式处理。 | `mas_single_project_mds_absorb_program.md` | quest Git default path 已完成；MDS product entry / physical absorb 仍需 parity 和 no-history import gate。 |
| `A5_archive_cleanup` | 已落地 closeout、intake 和 activation package 移入 history/reference 或保持只读参考。 | 本文 | 只做链接保全后的文档移动，不改变 runtime。 |

关键顺序是 `A1 -> A2 -> A3 -> A4`。当前 quest Git 和 workspace root Git 相关的 `A2-A4` 已对 current projects 完成到 verified / default-retired；下一步固定为 workspace 用户可见 layout 去 MDS/DS 化，然后依次处理 profile/entry compatibility retirement 和 no-history physical absorb。如果把 SQLite 当成 paper truth，会破坏 MAS publication authority。

## Active Portfolio

这些文件继续作为 active portfolio 面维护。

| file | portfolio role | current handling |
| --- | --- | --- |
| `mas_mds_autonomy_operating_system_program.md` | active master board | 最高层 program board，只放方向、lane 和 gate，不承载 implementation detail。 |
| `mas_single_project_mds_absorb_program.md` | active execution program | MAS 吸收 MDS、no-history import、真实 workspace layout cutover 和 MDS entry retirement 的总计划。 |
| `runtime_lifecycle_sqlite_migration_program.md` | active subprogram | runtime lifecycle SQLite authority、文件数量压降、quest Git retirement、current workspace cutover 的执行子计划。 |
| `mas_mds_unified_enhancement_program.md` | active enhancement program | L1-L5 backlog / read-model / projection / maintainability program；repo-level surface 已有 closeout，真实 workspace 数据与 audit apply 继续按 owner gate 推进。 |
| `mas_mds_owner_boundary_refactor_plan.md` | active contract | owner matrix、projection/oracle/observability 越权防护，所有 bridge / adapter / projection 必须引用。 |
| `mas_single_project_quality_and_autonomy_mainline.md` | active mainline narrative | 医学论文质量和长时间自治优化收口到 MAS 单项目主线的解释入口。 |

## Support Docs

这些文件不是独立 program owner，继续作为 active program 的支撑材料。

| file | support role | target owner |
| --- | --- | --- |
| `mds_capability_parity_matrix.md` | MDS capability parity / oracle matrix | 由 `mas_single_project_mds_absorb_program.md` 引用，作为 absorb gate 的 appendix。 |
| `plan_completion_ledger.md` | landed evidence ledger | 记录 planned vs landed vs verified；不得把计划写成完成。 |
| `mainline_integration_and_cleanup.md` | operational policy | worktree absorb、cleanup、push、主线卫生纪律。 |
| `repository_ci_preflight.md` | operational policy | repo 验证与 preflight 纪律；叙述性 docs-only 走 documentation review。 |
| `merge_and_cutover_gates.md` | gate policy | repo merge gate 与 runtime cutover gate 的老入口，后续只作为 gate policy。 |
| `external_runtime_dependency_gate.md` | external blocker policy | external runtime / workspace / human gate 未清除前的 blocker package。 |
| `deepscientist_continuous_learning_policy.md` | learning policy | MDS 被吸收后仍保留的 upstream learning policy。 |
| `deepscientist_latest_update_learning_protocol.md` | learning protocol | fresh upstream audit、decision matrix、worktree absorb 和验证流程。 |
| `med_deepscientist_method_learning_disciplines.md` | learning discipline | 方法论吸收边界。 |
| `med_deepscientist_continuous_learning_plan.md` | learning plan | 继续学习 DeepScientist 的长期 intake 入口。 |
| `med_deepscientist_upstream_source_provenance.md` | provenance record | upstream source / provenance / license / source-map 支撑材料。 |
| `med_deepscientist_deconstruction_map.md` | deconstruction map | MDS 解构参考，归入 absorb program 的 support surface。 |
| `upstream_intake.md` | intake policy | 旧 med-deepscientist fork upstream intake 流程；MDS 退役前保留。 |
| `project_repair_priority_map.md` | repair triage reference | 维护优先级参考，不作为独立 program board。 |
| `manual_runtime_stabilization_checklist.md` | manual ops checklist | 外部/runtime 稳定化清单。 |
| `real_study_relaunch_verification.md` | real workspace verification reference | 真实 study relaunch 验证参考。 |

## Landed Or Historical Reference

这些文件已经完成主要吸收，或被更新的 active board 覆盖。已完成链接审计且没有 active contract 职责的文件移入 `docs/history/program/`。如果业务代码或行为测试还依赖叙述性 docs 路径，优先退役这条机器依赖，改用稳定 id 或 durable surface，再执行归档。

| file | recommended state | reason |
| --- | --- | --- |
| `../references/ai_first_research_os_architecture.md` | reference | AI-first OS 架构已进入 architecture/status/mainline 口径，保留为目标架构参考。 |
| `../history/program/ai_first_operationalization_closeout.md` | landed closeout | AI-first repo-level closeout 记录，后续只读。 |
| `../history/program/ai_first_usable_closeout_projection.md` | landed closeout | usable closeout projection 已落地，后续由 ledger 与 active surfaces 接续。 |
| `../history/program/ai_first_closeout_handoff_governance.md` | landed closeout / support | handoff governance 已落地，可作为 closeout policy 参考。 |
| `../history/program/external_agent_orchestration_learning_intake_2026_04_30.md` | historical intake | 外部 orchestration 学习快照，已归入 autonomy board。 |
| `../history/program/open_auto_research_learning_intake_2026_05_04.md` | historical intake | OAR lesson 已吸收为 repo-level read model，真实 soak 另由 active lanes 管理。 |
| `../history/program/paper_orchestra_learning_intake_2026_05_02.md` | historical intake | PaperOrchestra lesson intake，后续只作为学习参考。 |
| `../history/program/deepscientist_learning_intake_2026_04_25.md` | historical intake | 旧 DeepScientist intake。 |
| `../history/program/deepscientist_learning_intake_2026_04_28.md` | historical intake | 旧 DeepScientist intake。 |
| `../history/program/deepscientist_learning_intake_2026_04_30.md` | historical intake | 旧 DeepScientist intake。 |
| `../history/program/deepscientist_learning_intake_2026_05_05.md` | latest intake record | 当前最新 intake 记录，仍由 learning protocol 引用，但不是独立 program。 |
| `../history/program/research_foundry_medical_mainline.md` | superseded narrative / reference | Research Foundry / Harness OS 叙述已被当前 MAS/MDS autonomy 与 single-project docs 收口；保留为历史架构脉络。 |
| `../history/program/research_foundry_medical_execution_map.md` | superseded execution map / reference | 同上，作为旧 phase ladder 入口保留。 |
| `../history/program/open_harness_os_freeze_plan.md` | historical architecture freeze | Harness OS freeze 计划不再作为当前 MAS/MDS 执行板。 |
| `../history/program/integration_harness_activation_package.md` | landed activation package | activation baseline 历史包。 |
| `../history/program/hermes_backend_activation_package.md` | landed activation package | activation baseline 历史包。 |
| `../history/program/hermes_backend_continuation_board.md` | historical continuation board | 外部 Hermes 目标 wording / seam 历史板，当前不应超过 MAS/MDS absorb 与 Runtime OS owner。 |
| `../history/program/upstream_hermes_agent_fast_cutover_board.md` | historical cutover board | upstream Hermes cutover 历史板；external runtime gate 未清除时只读参考。 |
| `../history/program/journal_package_builtins_upgrade_plan.md` | landed/specific implementation plan | journal package builtins 计划不再作为 portfolio board。 |
| `../runtime/study_progress_projection.md` | landed projection reference | study-progress projection 已是稳定 surface 参考。 |

## Deprecated Or Merge Candidates

这些文件不建议继续新增实质计划内容；需要更新时应合并到 active docs。

| file | merge target |
| --- | --- |
| `../history/program/research_foundry_medical_mainline.md` | `mas_mds_autonomy_operating_system_program.md` / `mas_single_project_quality_and_autonomy_mainline.md` |
| `../history/program/research_foundry_medical_execution_map.md` | `mas_mds_autonomy_operating_system_program.md` |
| `../history/program/open_harness_os_freeze_plan.md` | `docs/architecture.md` 或 `docs/references/` |
| `../history/program/hermes_backend_continuation_board.md` | `external_runtime_dependency_gate.md` / `mas_single_project_mds_absorb_program.md` |
| `../history/program/hermes_backend_activation_package.md` | `plan_completion_ledger.md` / `docs/history/program/` |
| `../history/program/integration_harness_activation_package.md` | `plan_completion_ledger.md` / `docs/history/program/` |
| `../history/program/upstream_hermes_agent_fast_cutover_board.md` | `external_runtime_dependency_gate.md` / `docs/history/program/` |

## Archive Rule

历史归档必须后置于链接审计，不能在当前 active planning 里直接移动文件。归档时遵守：

1. 先在本文把文件标成 `historical_reference`、`landed_closeout` 或 `superseded`.
2. 用 `rg` 查所有 inbound links，更新到新路径或保留 stub。
3. 只移动叙述性历史材料，不移动 active contracts、ledgers、policies 或 runtime docs。
4. 代码和测试不得把 `docs/**` 当成机器 truth、policy truth、runtime truth 或 regression oracle；如需引用 program / policy / runtime 概念，使用稳定 id 或 durable surface。
5. 只允许 docs tooling 识别 `docs/` 路径、生成 docs asset 或输出人读链接；这些工具不得读取 Markdown 措辞作为行为断言。
6. 不写 pytest 固定 Markdown 措辞、标题或链接锚点；归档验收走人工 review、`git diff --check` 和必要的 link spot-check。
7. 任何文档移动都不能作为 repo capability、workspace cutover 或 runtime migration 完成证明。

## Definition Of Done

这个 portfolio 收敛完成时必须满足：

- 后续 Agent 能先读本文决定该更新落在哪个 active owner doc。
- 新的 runtime lifecycle / quest Git / MDS absorb 工作都进入同一个 `A1-A4` 主序列。
- `runtime_lifecycle_sqlite_migration_program.md` 明确作为 `mas_single_project_mds_absorb_program.md` 的 runtime persistence 子计划执行。
- current-project quest Git 和 workspace root Git retirement 不再作为未完成 active backlog 重复规划；next execution queue 固定为 workspace layout 去 MDS/DS 化、profile/entry compatibility retirement、MDS physical no-history absorb。
- 已落地 closeout、learning intake、activation package 不再被当作 active backlog。
- `plan_completion_ledger.md` 继续区分 repo capability landed、真实 workspace cutover completed、compatibility retirement completed。
