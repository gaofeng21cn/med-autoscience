# Program Portfolio Consolidation

Status: `active portfolio governance`
Date: `2026-05-12`
Owner: `MedAutoScience`

## 当前结论

`docs/program/` 现在承载仍需要 program 级阅读顺序、owner gate、closeout evidence 或 landed provenance 的文档。

当前 MAS program 组合按目标、框架优先执行、产品化、基础 guard 四层阅读，不能按文件名、立项时间或 P0/P1/P2/P3 编号理解成并列待办队列：

1. **目标层**：AI-first paper autonomy 是 MAS 的论文自治目标合同。它定义 MAS 要达到的闭环：AI reviewer finding、repair work unit、gate replay、reviewer re-eval、route decision、stage knowledge/memory、真实 paper soak，以及 artifact delta / human gate / stop-loss 的验收口径。
2. **框架优先执行层**：P2 是当前执行优先级。它先完成 OPL 完整智能体框架，再把 MAS 迁移为 OPL-admitted domain agent，并把新旧功能分类迁移、分层、沉淀或退役。
3. **横向 stage 形式层**：Stage surface standardization 负责把 MAS 的 stage card、route contract、prompt/skill、tool surface、knowledge packet、closeout memory、quality pack 与 OPL projection boundary 做成统一维护形态。当前 generated stage cards、缺失 knowledge/closeout obligations、stage quality pack contract 和 OPL descriptor locator 已落地；剩余重点是 append-block 主 stage 的独立 skill surface 与 production provider-hosted soak。
4. **产品化层**：P1 负责把迁移后的 MAS/OPL 状态、对话、产物、terminal/log 和受控 action 接到 OPL App Runtime Workbench。
5. **已落地基础层**：P3 和 P3a 已完成主要实施，当前角色是 owner/provenance/guard。它们保留在 `docs/program/`，是因为仍承载 monolith、MDS provenance、restore proof、runtime lifecycle、quest/root Git retirement 和后续兼容判断的当前 owner 文档，不再代表活跃实现队列。

因此，当前真实执行逻辑是：**P0 提供目标和验收口径，P2 先完成 OPL framework 与 MAS 迁移/分层/退役收口，P1 把迁移后的状态产品化，最后用 P0 做真实 paper autonomy 验收；P3/P3a 提供已完成基础和 guard 证据**。具体执行时先读 [MAS Current Development Lines](./current_development_lines.md)，按内容块选择当前线路，不按整份旧计划推进。

## 当前事实

- MAS 已完成 monolith / no-history absorb。默认运行、诊断、进度、artifact、quality、status、cockpit 和 OPL handoff 均由 MAS-owned surface 承接。
- MDS / DeepScientist 的当前角色是 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。
- Runtime lifecycle / quest Git / workspace root Git retirement 已进入 landed guard 口径；新 workspace 默认使用 MAS-owned layout 和 SQLite/file truth authority。
- AI-first paper autonomy repo callable loop 已落地；真实论文线仍必须通过 live MAS truth surface 证明 artifact delta、gate replay、AI reviewer judgment、route decision、human gate、stop-loss 或 stable blocker。
- OPL 已上升为 stage-led、以 Agent executor 为最小执行单位的完整智能体运行框架。MAS 作为医学研究 domain agent 暴露 stage descriptor、sidecar export/dispatch、receipt schema、projection builder、artifact locator 和 authority refs；OPL 持有 framework-level stage attempt、queue/wakeup、retry/dead-letter、approval transport、projection 和 shared lifecycle/index primitives。

## Program Map

| layer | document | current state | role now | next handling |
| --- | --- | --- | --- | --- |
| Execution map | [MAS Current Development Lines](./current_development_lines.md) | `active_content_level_development_map` | 汇总 framework-first 内容级线路、过时/降级材料、合并吸收规则、优先级和 done signal。 | 执行旧 program 内容前先读；新内容先映射到 OPL framework、MAS migration、feature retirement、P1 productization、P0 final soak、P3/P3a/support。 |
| Goal / acceptance | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `outcome_contract; repo_loop_landed; live_soak_active` | 定义论文自治闭环、质量边界、stage knowledge/memory、repair/review/gate/route 的目标和验收。 | 保留为目标 owner。新增实现细节应先判断属于 MAS paper loop、P1 workbench，还是 P2 OPL framework。 |
| Framework enabler | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `active_enabler; framework_first` | 先完成 OPL framework foundation，再把 MAS scheduler/watchdog/legacy provider/local diagnostics、sidecar、domain-agent skeleton 和 lifecycle primitives 对齐 OPL stage-led framework，并执行旧面退役收口。 | 跟随 OPL master roadmap；真实 MAS paper-line soak 放在 framework/migration/retirement 收口之后，不把目标 provider cutover 写成已完成。 |
| Cross-cutting form | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `partially_landed; skill_surface_migration_pending` | 统一 MAS stage 的人读 surface、machine source、prompt/skill、tool、knowledge、closeout、quality pack 与 OPL projection boundary。 | stage / prompt / skill / knowledge / quality 变更先按该模板归一；append-block 主 stage 继续迁移为独立 skill surface，再进入 P0/P2/P1 对应 owner surface。 |
| Product enabler | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `active_enabler; follows_framework_migration` | 把迁移后的 MAS progress、conversation、Live Console、terminal attach、安全 action、provider attempt refs 和 artifacts 产品化到 OPL App。 | 作为迁移后用户可见闭环的主要产品化 lane 推进。 |
| Landed foundation | [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md) | `landed_owner_doc; provenance_guard` | 记录当前 MAS monolith、MDS retained roles、workspace layout、entry compatibility、functional monolith 和 behavior parity 边界；完整历史记录在 `docs/history/program/`。 | 只维护 guard、provenance 和后续 source intake 分类；新增默认运行能力不回到 MDS absorb 旧路线。 |
| Landed foundation | [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `landed_owner_doc; maintenance_guard` | 记录当前 runtime lifecycle authority、SQLite/file truth boundary、quest/root Git retirement、restore proof 和 migration ledger；完整历史记录在 `docs/history/program/`。 | 维护新 drift、restore diagnostic 和 explicit archive import。 |

## 当前执行顺序

| order | lane | owner doc | current meaning | closeout signal |
| --- | --- | --- | --- | --- |
| `1` | `p2_opl_framework_foundation` | `opl_temporal_mas_runtime_retirement_program.md` plus OPL master roadmap | 先完成 OPL 作为完整智能体框架的 stage attempt、provider runtime、queue/wakeup、retry/dead-letter、approval transport、receipt/projection 和 shared lifecycle/index primitives。 | OPL provider/framework 能承载 MAS stage attempt，并只持有 framework receipt/ref/projection。 |
| `2` | `p2_mas_framework_migration_and_retirement` | `opl_temporal_mas_runtime_retirement_program.md`, `mas_single_project_mds_absorb_program.md`, `runtime_lifecycle_sqlite_migration_program.md` | MAS 迁移到 OPL framework，新旧功能分类迁移/分层/沉淀，过时模块和旧兼容面按替代证据退役清理。 | direct MAS skill path 与 OPL-hosted path 共享 MAS owner receipts；旧默认依赖无 default caller / no fixture requirement / replacement proof。 |
| `3` | `p1_opl_app_runtime_workbench` | `opl_app_mas_runtime_workbench_program.md` | 产品化迁移后的用户可见面，让用户在 OPL App 直接看到论文状态、路线、执行器对话、terminal/log、产物和受控 action receipt。 | `mas_opl_runtime_workbench_projection`、safe action receipt、terminal attach owner gate 和 OPL App drilldown 有稳定 contract / UI evidence。 |
| `4` | `stage_surface_standardization` | `stage_surface_standardization_program.md` | 横向统一 stage card、prompt/skill、tool surface、knowledge packet、closeout memory、quality pack 和 OPL projection boundary，避免 prompt/skill/quality 继续分散增长。 | Generated stage cards、knowledge/closeout obligations、quality pack contract 和 descriptor locator 已落地；最终完成还需要 append-block 主 stage 独立 skill surface 与真实 provider-hosted paper-line soak。 |
| `5` | `p0_live_paper_autonomy_acceptance` | `ai_first_paper_autonomy_closure_program.md` | 在 framework-first 目标形态下，用真实 study / paper line 验证 artifact delta、gate replay、AI reviewer judgment、route decision、human gate、stop-loss 或 typed blocker。 | controlled live apply 或 read-only evidence 明确显示 progress delta / blocker；worker live、queue task 或 repo test 只作为支撑证据。 |
| `6` | `p3_foundation_guard` | `mas_single_project_mds_absorb_program.md`, `runtime_lifecycle_sqlite_migration_program.md` | 对 monolith、MDS provenance、runtime lifecycle、restore proof 和 old workspace drift 做 guard 维护。 | 新 drift 有 explicit inventory / restore proof / provenance classification；不新增默认 MDS dependency 或 Git lifecycle。 |

当前统一表达为：P0 是目标和验收面，但执行顺序不是 P0-first；P2 先完成 OPL framework 和 MAS 迁移/退役收口，P1 产品化迁移后的可见面，P0 最后做真实 paper autonomy 验收，P3/P3a 贯穿提供 foundation guard。[MAS Current Development Lines](./current_development_lines.md) 是这些层级的内容级执行地图。

## 已收口状态

| area | current state | owner surface | lifecycle placement |
| --- | --- | --- | --- |
| workspace layout de-MDS/DS | `landed` | `mas_single_project_mds_absorb_program.md` | P3 landed foundation |
| profile / entry compatibility retirement | `landed` | `mas_single_project_mds_absorb_program.md` | P3 landed foundation |
| no-history physical absorb | `landed` | `mas_single_project_mds_absorb_program.md`, `docs/references/med-deepscientist/` | P3 landed foundation + references |
| functional monolith completion | `landed` | `mas_single_project_mds_absorb_program.md`, `docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` | P3 landed foundation |
| MDS behavior equivalence audit | `landed_matrix` | `docs/references/mds-parity/` | reference / parity |
| Runtime lifecycle / Git retirement | `landed_owner_doc` | `runtime_lifecycle_sqlite_migration_program.md` | P3a landed foundation |
| Runtime control / progress projection | `landed_contract` | `docs/runtime/control/`, `docs/runtime/projections/` | runtime owner docs |
| Portal / Live Console | `landed_read_model` | `docs/runtime/display/` | runtime/product projection |
| paper-progress degradation guard | `landed_repo_guard` | `docs/runtime/control/`, `docs/references/verification/plan_completion_ledger.md` | runtime guard / evidence |
| Stage surface generated cards / knowledge obligations / quality packs | `partially_landed_contract; skill_surface_migration_pending` | `stage_surface_standardization_program.md`, `docs/runtime/contracts/stage_surfaces.md`, `stage_surface_contract.py`, `stage_knowledge_contract.py`, `stage_quality_contract.py` | cross-cutting form + P0/P2/P1 support |
| Stage-led knowledge and publication-route memory | `repo_contract_landed; migration_active` | `ai_first_paper_autonomy_closure_program.md`, `docs/policies/study-workflow/`, `docs/status.md` | P0 objective + policy |
| OPL stage-led / Temporal alignment | `active_alignment` | OPL master roadmap plus `opl_temporal_mas_runtime_retirement_program.md` | P2 active enabler |
| OPL App MAS Runtime Workbench | `active_plan` | `opl_app_mas_runtime_workbench_program.md` | P1 active enabler |

## Content-Level Disposition

| document | current content role | disposition |
| --- | --- | --- |
| `program_portfolio_consolidation.md` | 当前 program 组合总控、执行顺序、生命周期处置 | 保持当前 owner；每次新增 program 先更新本文。 |
| `current_development_lines.md` | 当前内容级开发线路图、过时/降级材料表、合并吸收规则和优先级 | 保留为执行地图。执行旧计划前先用它判断内容块归属；不作为 runtime、paper 或 publication truth。 |
| `ai_first_paper_autonomy_closure_program.md` | P0 目标合同、repo loop current state、真实 paper soak 验收 | 保留在 program。MAS paper loop 由本文持有；历史 full record 已移入 `docs/history/program/`；OPL provider 与 App UI 实现细节分别进入 P2/P1。 |
| `opl_app_mas_runtime_workbench_program.md` | P1 产品化 enabler owner | 保留为精简 active owner doc。完整旧记录已移入 `docs/history/program/`；当前跟随 framework migration 执行 read-only workbench、action receipt、terminal attach、provider join 等内容级 lane。 |
| `opl_temporal_mas_runtime_retirement_program.md` | P2 framework/runtime enabler owner | 保留为精简 active owner doc。完整旧记录已移入 `docs/history/program/`；当前先执行 OPL framework foundation、MAS framework migration、framework-generic lift、legacy retirement，再进入 final paper-line soak。 |
| `stage_surface_standardization_program.md` | 横向 stage 形式统一 owner | 保留为 partially landed cross-cutting program。凡是修改 stage prompt、skill、knowledge packet、closeout memory、quality pack、stage descriptor 或 OPL projection boundary，先按本文归一；不要把已落地的 generated facade / obligations / quality pack 重新写成计划态。 |
| `mas_single_project_mds_absorb_program.md` | P3 landed foundation、MDS provenance、monolith guard current owner | 保留在 program 作为精简 landed owner doc；历史 full record 已移入 `docs/history/program/`；后续只维护 provenance、classification、compat/restore guard。 |
| `runtime_lifecycle_sqlite_migration_program.md` | P3a landed foundation、runtime lifecycle / Git retirement guard current owner | 保留在 program 作为精简 landed owner doc；历史 full record 已移入 `docs/history/program/`；后续只处理 drift、restore diagnostic、explicit archive import。 |
| `docs/history/program/*` | dated closeout、activation package、recurring intake snapshot、superseded plan | 留在 history。活跃触发规则进入 `docs/status.md`、`docs/references/**` 或本文。 |

## Architecture Fitness Budget

模块化治理继续作为横向 fitness budget。当前评估与落地记录见 [MAS Modularity Assessment 2026-05-07](../references/mainline/mas_modularity_assessment_2026_05_07.md)。后续 P1/P2/P0 live-soak 触碰高 fan-in/fan-out 区域时，必须保持：

- hub role 清楚：authority 持有裁决，read-model 投影 canonical truth，adapter 验证/调用/渲染，materializer 执行受控写入。
- 用户状态读取 `study_macro_state -> user_visible_projection`。
- 运行动作读取 `owner_route -> consumer latest -> executor dispatch`。
- OPL App 消费 MAS projection、freshness、source refs、artifact locators、action receipts 和 terminal attach gate；MAS 持有 study truth、publication verdict、quality verdict、runtime owner decision 和 controller next action。
- `scripts/verify.sh structure` 的 Sentrux `quality_signal` 允许在有解释的范围内波动；DSM `above_diagonal` 保持 `0`。

## Support Lanes

这些 lane 属于按触发执行的长期支持能力：入口、policy 或 protocol 留在 `docs/status.md` / `docs/references/`，每次执行后的 dated record 留在 `docs/history/program/`。

| recurring lane | active owner | dated records |
| --- | --- | --- |
| DeepScientist latest-update learning | `docs/status.md`, `docs/references/med-deepscientist/deepscientist_continuous_learning_policy.md`, `docs/references/med-deepscientist/deepscientist_latest_update_learning_protocol.md` | `docs/history/program/deepscientist_learning_intake_YYYY_MM_DD.md` |
| external agent orchestration learning | `docs/status.md` | `docs/history/program/external_agent_orchestration_learning_intake_YYYY_MM_DD.md` |
| PaperOrchestra / adjacent writing-system learning | `docs/status.md` | `docs/history/program/paper_orchestra_learning_intake_YYYY_MM_DD.md` |
| open auto research learning | `docs/status.md` | `docs/history/program/open_auto_research_learning_intake_YYYY_MM_DD.md` |
| research-harness learning | `docs/status.md` | `docs/history/program/research_harness_learning_intake_YYYY_MM_DD.md` |

Snapshot-local saturation protocols are provenance until promoted into `docs/status.md`, `docs/references/**`, or another current owner document. A future repeated intake must first promote the durable trigger, scope, and absorption rule out of the dated record.

## Archive Rule

历史归档后置于链接审计，执行顺序如下：

1. 先判断内容块属于 target/outcome、active enabler、landed foundation、support reference、dated snapshot 还是 tombstone。
2. 当前事实合入核心五件套、runtime owner doc、policy 或本 portfolio。
3. P0 目标不吸收 P1/P2 实现细节；P1/P2 也不重新定义医学质量或 paper authority。
4. P3/P3a 的已完成事实保留在 landed owner docs 或 verification ledger；只有纯日期流水、旧 board、旧 activation package 进入 `docs/history/program/`。
5. 用 `rg` 查 inbound links，更新到新路径或保留 stub。
6. 代码和测试使用稳定 id、schema 或 durable surface 表达 program / policy / runtime 概念。
7. 归档验收采用人工 review、`git diff --check` 和必要的 link spot-check。

## Definition Of Done

当前 portfolio 的完成标准是：

- 读者能一眼看出 P0 是目标/验收，P2 是当前 framework-first 执行优先级，P1 是迁移后的产品化入口，P3/P3a 是已完成基础和 guard。
- 后续 Agent 能先读本文决定新内容落在目标层、active enabler、landed foundation、reference、policy 还是 history。
- 已落地 closeout 留在 landed owner doc、reference 或 history 层。
- OPL framework 相关实现、MAS framework migration、功能分层和旧面退役进入 P2 或 OPL master roadmap；MAS paper autonomy 质量和 artifact authority 仍回到 P0 / MAS owner surfaces。
- 真实 paper closure 仍以 live MAS truth surface 为准，不用文档状态、repo tests 或 queue receipt 伪装成投稿级完成。
