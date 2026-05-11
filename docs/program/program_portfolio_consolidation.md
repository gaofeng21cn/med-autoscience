# Program Portfolio Consolidation

Status: `active portfolio governance`
Date: `2026-05-11`
Owner: `MedAutoScience`

## 当前结论

`docs/program/program_portfolio_consolidation.md` 是 MAS program 组合的当前入口。它负责说明当前事实、排列活跃 program、归口已落地记录，并给维护者判断新文档应该进入 `docs/program/`、`docs/policies/`、`docs/references/` 还是 `docs/history/program/`。

当前事实固定如下：

- MAS 已完成 monolith / no-history absorb。默认运行、诊断、进度、artifact、quality、status、cockpit 和 OPL handoff 均由 MAS-owned surface 承接。
- MDS / DeepScientist 的当前角色是 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。
- Runtime Control、Progress Projection、runtime continuity、Live Console、Portal、watchdog、paper-progress degradation guard 和 owner-route reconcile 已进入 landed / guard 口径。
- 当前最高优先级是 AI-first paper autonomy closure：AI reviewer finding、repair work unit、gate replay、reviewer re-eval、route decision、stage knowledge/memory 和真实 paper soak。
- OPL 对齐进入 Codex-first、stage-led family framework 阶段。MAS 向 OPL 暴露 stage、skill、knowledge、quality gate、sidecar、receipt schema、projection builder 和 artifact locator；MAS 持有医学研究 truth、quality verdict 和 artifact authority。

## 活跃 Program 栈

| level | program | state | current owner role |
| --- | --- | --- | --- |
| `P0` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `active` | 当前医学论文主闭环。 |
| `P1` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `active` | MAS 人类运行工作台与 OPL App 集成。 |
| `P2` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `active / gated_by_opl_master` | MAS sidecar/export/dispatch、provider receipt 和真实 paper-line guarded soak。 |
| `P3` | [MAS Single Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md) | `landed_owner_doc` | MDS 能力吸收、历史来源和后续 provenance 归口。 |
| `P3a` | [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `landed_owner_doc` | runtime lifecycle authority、restore proof 和 migration ledger 归口。 |

新增 program 先归入这张栈：属于 P0/P1/P2 的继续在 `docs/program/` 维护；属于稳定规则的进入 `docs/policies/`；属于参考、学习或 parity 的进入 `docs/references/`；属于已完成、退役或单轮快照的进入 `docs/history/program/`。

## 当前执行顺序

| order | lane | owner doc | closeout signal |
| --- | --- | --- | --- |
| `1` | `ai_first_paper_autonomy_closure` | `ai_first_paper_autonomy_closure_program.md` | AI reviewer finding 进入可执行 repair work unit；analysis weak/negative/unexpected result 进入 claim downgrade、bounded repair、switch line、return_to_scout、stop_loss 或 human_gate；canonical manuscript / table / figure / package source 产生 artifact delta 后 replay gate 并触发 AI reviewer re-eval；DM002、DM003、Obesity 真实 paper soak 证明 queue -> dispatch -> repair/review/gate -> receipt -> notification -> progress delta 或 blocker。 |
| `2` | `opl_app_mas_runtime_workbench` | `opl_app_mas_runtime_workbench_program.md` | MAS 暴露 `mas_opl_runtime_workbench_projection`、action receipt 和 terminal attach owner gate；OPL App 渲染 App-native study workbench、terminal/log 面板、conversation、artifacts 和安全 actions；workspace-local Portal / Live Console 保留为 fallback/evidence。 |
| `3` | `opl_temporal_mas_runtime_retirement` | `opl_temporal_mas_runtime_retirement_program.md` plus OPL master roadmap | MAS 完成 provider-ready contract、sidecar export/dispatch receipt、forbidden-write guard、paper-line guarded soak 和 retirement evidence；真实 soak 通过前，本地 scheduler / Portal / Live Console 作为 diagnostics/fallback 继续服务。 |
| `4` | `standard_domain_agent_skeleton_mapping` | OPL master roadmap plus MAS agent-entry / manifest surfaces | MAS 把现有 stage、prompt/skill、knowledge、quality gate、contract、sidecar、receipt schema / refs、projection builder / refs 和 artifact locator / authority refs 映射到 OPL standard skeleton，并输出 `framework_generic` / `mas_domain_specific` lifecycle 清单。 |

默认先推进 `P0`；P0 的当前 gate 被真实外部 blocker 挡住时，并行推进 P1/P2 的集成、provider-ready contract 或 skeleton mapping。P3/P3a 维护证据、provenance、restore proof 和后续兼容判断。

## 已收口状态

| area | current state | owner surface |
| --- | --- | --- |
| workspace layout de-MDS/DS | `landed` | `mas_single_project_mds_absorb_program.md` |
| profile / entry compatibility retirement | `landed` | `mas_single_project_mds_absorb_program.md` |
| no-history physical absorb | `landed` | `mas_single_project_mds_absorb_program.md`、`docs/references/med-deepscientist/` |
| functional monolith completion | `landed` | `mas_single_project_mds_absorb_program.md`、`docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` |
| MDS behavior equivalence audit | `landed_matrix` | `docs/references/mds-parity/` |
| Runtime lifecycle / Git retirement | `landed_owner_doc` | `runtime_lifecycle_sqlite_migration_program.md` |
| Runtime control / progress projection | `landed_contract` | `docs/runtime/control/`、`docs/runtime/projections/` |
| runtime continuity | `landed` | `docs/runtime/control/runtime_supervision_loop.md`、`docs/runtime/projections/runtime_health_kernel.md` |
| Portal / Live Console | `landed_read_model` | `docs/runtime/display/` |
| runtime watchdog / cost guard | `landed` | `docs/runtime/control/runtime_supervision_loop.md`、`docs/runtime/control/supervision_scheduler_contract.md` |
| paper-progress degradation guard | `landed_repo_guard` | `docs/runtime/control/runtime_supervision_loop.md`、`docs/references/verification/plan_completion_ledger.md` |
| OPL stage-led / Temporal alignment | `active_alignment` | OPL master roadmap plus `opl_temporal_mas_runtime_retirement_program.md` |
| Standard domain-agent skeleton | `active_alignment` | OPL master roadmap plus MAS agent-entry / manifest surfaces |

这张表是当前 program 排序 authority。旧日期流水和双轨执行模型的 closeout 文本可作为 evidence 进入 owner doc、ledger 或 history；当前执行顺序以上一节为准。

## Architecture Fitness Budget

模块化治理是横向 fitness budget。当前评估与落地记录见 [MAS Modularity Assessment 2026-05-07](../references/mainline/mas_modularity_assessment_2026_05_07.md)：MAS 依赖方向干净，Sentrux `above_diagonal=0`，boundary fitness 已达到 `0 blocking / 0 advisory`；`product_entry`、`study_progress`、`runtime/control`、MCP/display 这些高扇入 projection/entry/read-model 仍作为维护热点观察。

后续队列执行统一遵守：

- 文件拆分采用自然 owner 子域命名和 importable module，避免机械编号 `part_*` / `chunk_*` / `split_*`。
- 中心 hub 声明角色：authority 持有裁决，read-model 投影 canonical truth，adapter 验证/调用/渲染，materializer 执行受控写入。
- 用户状态读取 `study_macro_state -> user_visible_projection`，运行动作读取 `owner_route -> consumer latest -> executor dispatch`。
- OPL App 消费 MAS progress/conversation/live-console/terminal projection、freshness、source refs、artifact locators、action receipts 和 terminal attach gate；MAS 持有 study truth、publication verdict、quality verdict、runtime owner decision 和 controller next action。
- 触碰 near-limit part、高 churn hub 或 nested `_parts` 时，按自然 owner 子域补 focused public-surface / subdomain tests。
- `scripts/verify.sh structure` 的 Sentrux `quality_signal` 允许在有解释的范围内波动；DSM `above_diagonal` 保持 `0`。

## Support Lanes

这些 lane 属于按触发执行的长期支持能力：入口、policy 或 protocol 留在 `docs/status.md` / `docs/references/`，每次执行后的 dated record 留在 `docs/history/program/`。

| recurring lane | active owner | dated records |
| --- | --- | --- |
| DeepScientist latest-update learning | `docs/status.md`、`docs/references/med-deepscientist/deepscientist_continuous_learning_policy.md`、`docs/references/med-deepscientist/deepscientist_latest_update_learning_protocol.md` | `docs/history/program/deepscientist_learning_intake_YYYY_MM_DD.md` |
| external agent orchestration learning | `docs/status.md`、`docs/history/program/external_agent_orchestration_learning_intake_2026_04_30.md` 的 saturation protocol | 后续同族 intake snapshot |
| PaperOrchestra / adjacent writing-system learning | `docs/status.md`、`docs/history/program/paper_orchestra_learning_intake_2026_05_02.md` 的 saturation protocol | 后续同族 intake snapshot |
| open auto research learning | `docs/status.md`、`docs/history/program/open_auto_research_learning_intake_2026_05_04.md` 的 saturation protocol | 后续同族 intake snapshot |
| research-harness learning | `docs/status.md`、`docs/history/program/research_harness_learning_intake_2026_05_11.md` 的 saturation protocol | 后续同族 intake snapshot |

`docs/history/program` 里的 `*_learning_intake_YYYY_MM_DD.md` 是 recurring lane 的 dated snapshot。它们记录单轮吸收证据；当前触发规则和吸收边界由对应 reference / status surface 持有。

## 归档规则

历史归档后置于链接审计，执行顺序如下：

1. 先在本文或对应 owner doc 把文件标成 `historical_reference`、`landed_closeout`、`superseded` 或 `dated_recurring_lane_snapshot`。
2. 用 `rg` 查 inbound links，更新到新路径或保留 stub。
3. 只移动叙述性历史材料；active contracts、ledgers、policies 和 runtime docs 保留在 owner surface。
4. 代码和测试使用稳定 id、schema 或 durable surface 表达 program / policy / runtime 概念。
5. docs tooling 可以识别 `docs/` 路径、生成 docs asset 或输出人读链接。
6. 归档验收采用人工 review、`git diff --check` 和必要的 link spot-check。
7. 文档移动本身只说明信息架构变化；repo capability、workspace cutover 或 runtime migration 的完成证明继续来自对应 owner surface 和验证记录。

## Definition Of Done

这个 portfolio 收敛完成时必须满足：

- 后续 Agent 能先读本文决定该更新落在哪个 active owner doc。
- P0/P1/P2 的当前执行顺序清楚，P3/P3a 的 landed owner-doc 身份清楚。
- runtime lifecycle / quest Git / MDS absorb 工作都回到 P3/P3a owner docs 和 verification ledger。
- current-project quest Git、workspace root Git retirement、workspace layout 去 MDS/DS 化、profile/entry compatibility retirement 和 no-history physical absorb repo-level closeout 以 landed owner doc 维护。
- functional monolith completion 保持 landed 口径；future upstream source intake review、explicit archive import reference 和 optional hosted frontend packaging 进入 reference/history 或对应 owner doc。
- paper autonomy stability 使用真实 workspace profile inventory、supervisor reconcile、migration dry-run 和 read-only soak 证据单独关闭。
- paper progress degradation closeout 表示 repo-level 自动推进 guard 已落地；真实论文 blocker 继续由 study/runtime/publication surfaces 暴露下一 owner。
- AI-first paper autonomy closure 完成时，必须证明初稿 / AI reviewer / repair / gate replay / reviewer re-eval / route decision 循环在真实 paper soak 中闭合。
