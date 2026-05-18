# Program Portfolio Consolidation

Status: `active portfolio governance`
Date: `2026-05-14`
Owner: `MedAutoScience`

## 当前结论

`docs/active/` 现在承载仍需要 program 级阅读顺序、owner gate、当前差距或当前完成门槛的文档。dated closeout evidence、完整过程流水和 landed provenance 进入 `docs/history/**`。

当前 MAS program 组合按目标、框架优先执行、产品化、基础 guard 四层阅读，不能按文件名、立项时间或 P0/P1/P2/P3 编号理解成并列待办队列：

1. **目标层**：AI-first paper autonomy 是 MAS 的论文自治目标合同。它定义 MAS 要达到的闭环：AI reviewer finding、repair work unit、gate replay、reviewer re-eval、route decision、stage knowledge/memory、真实 paper soak，以及 artifact delta / human gate / stop-loss 的验收口径。
2. **框架优先执行层**：P2 是当前执行优先级。它先完成 OPL 完整智能体框架，再把 MAS 迁移为 OPL-admitted domain agent，并把新旧功能分类迁移、分层、沉淀或退役。
3. **横向 stage 形式层**：Stage surface standardization 负责把 MAS 的 stage card、route contract、prompt/skill、tool surface、knowledge packet、closeout memory、quality pack 与 OPL projection boundary 做成统一维护形态。当前 generated stage cards、缺失 knowledge/closeout obligations、stage quality pack contract、OPL descriptor locator、独立 stage skill surface、既有 skill 的 stage surface / quality pack / Research Harness clean-room gate 消费、provider residency read model、guarded apply harness、OPL production proof -> MAS provider availability ingestion、Stage Deliverable Review Page / Index workspace locator proof、publication-route memory body-free receipt inventory、Workbench reference projection、standard skeleton slot audit 和 legacy residue audit 已落地；真实 production provider-hosted live paper apply 仍 pending。
4. **产品化层**：P1 负责把迁移后的 MAS/OPL 状态、对话、产物、terminal/log 和受控 action 接到 OPL App Runtime Workbench。
5. **已落地基础层**：P3 和 P3a 已完成主要实施，当前角色是 owner/provenance/archive/parity guard。它们保留在 `docs/active/`，是因为仍承载 monolith、MDS provenance、restore proof、runtime lifecycle、quest/root Git retirement 和后续 source-intake / archive / parity 判断的当前 owner 文档，不再代表活跃实现队列。

因此，当前真实执行逻辑是：**P0 提供目标和验收口径，P2 先完成 OPL framework 与 MAS 迁移/分层/退役收口，P1 把迁移后的状态产品化，最后用 P0 做真实 paper autonomy 验收；P3/P3a 提供已完成基础和 guard 证据**。具体执行时先读 [MAS Current Development Lines](./current-development-lines.md)，按内容块选择当前线路，不按整份旧计划推进。

## 当前事实

- MAS 已完成 monolith / no-history absorb。默认运行、诊断、进度、artifact、quality、status、cockpit 和 OPL handoff 均由 MAS-owned surface 承接。
- MDS / DeepScientist 的当前角色是 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。
- Runtime lifecycle / quest Git / workspace root Git retirement 已进入 landed guard 口径；新 workspace 默认使用 MAS-owned layout 和 SQLite/file truth authority。
- AI-first paper autonomy repo callable loop 已落地；真实论文线仍必须通过 live MAS truth surface 证明 artifact delta、gate replay、AI reviewer judgment、route decision、human gate、stop-loss 或 stable blocker。
- OPL 已上升为 stage-led、以 Agent executor 为最小执行单位的完整智能体运行框架。MAS 作为医学研究 domain agent 暴露 stage descriptor、sidecar export/dispatch、receipt schema、projection builder、artifact locator 和 authority refs；OPL 持有 framework-level stage attempt、queue/wakeup、retry/dead-letter、approval transport、projection 和 shared lifecycle/index primitives。
- Stage surface 的形式统一已基本进入可维护状态：主 stage generated card、独立 skill surface、knowledge / closeout obligations、stage quality packs、Research Harness clean-room gates、OPL descriptor locator、provider residency read model、guarded apply harness、OPL production proof ingestion、真实 workspace review/index locator proof、body-free route-memory receipt inventory、Workbench reference projection、standard skeleton slot audit 和 legacy residue audit 已落地。距离理想态的核心差距集中在真实 domain activity 长时 soak、provider-hosted live paper apply、更多真实 paper-line Stage Deliverable Review Page / Index instance、更多 publication-route memory receipts、OPL App UI drilldown 和按 audit finding 直接清理旧接口残留。当前 portfolio 的清理口径是 direct cleanup：旧接口只要无 active caller、无 public surface 引用、无 fixture/provenance 必需且有 replacement proof，就删除源码/命令/test 入口，不再保留兼容 wrapper。
- Production/framework closure 的跨仓当前 owner 归 OPL `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md` 与 `/Users/gaofeng/workspace/one-person-lab/docs/active/production-framework-closure-gap-matrix.md` 持有。MAS 不维护平行大计划；MAS 负责在该 OPL closure matrix 下提供 MAS-owned owner receipt、domain memory receipt、stage review/index locator、skeleton follow-through、legacy no-active-caller proof 和 workbench/closeout projection refs。真实 paper-line live apply 继续是 P0 production evidence gate。旧 `production-functional-closure-plan` 只按 OPL history provenance 阅读。
- MAS 当前规划已经收口到 [MAS Current Development Lines](./current-development-lines.md) 的全线规划闭环表。后续每条 MAS 线必须先归入 `landed_foundation`、`functional_follow_through_gate` 或 `production_evidence_gate`，再跳到 P0/P1/P2/stage/memory/P3 owner doc；不要把同一批剩余项复制成新的平行 program。

## Program Map

| layer | document | current state | role now | next handling |
| --- | --- | --- | --- | --- |
| Execution map | [MAS Current Development Lines](./current-development-lines.md) | `active_content_level_development_map` | 汇总 framework-first 内容级线路、过时/降级材料、合并吸收规则、优先级和 done signal。 | 执行旧 program 内容前先读；新内容先映射到 OPL framework、MAS migration、feature retirement、P1 productization、P0 final soak、P3/P3a/support。 |
| Goal / acceptance | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `outcome_contract; repo_loop_landed; live_soak_active` | 定义论文自治闭环、质量边界、stage knowledge/memory、repair/review/gate/route 的目标和验收。 | 保留为目标 owner。新增实现细节应先判断属于 MAS paper loop、P1 workbench，还是 P2 OPL framework。 |
| Framework enabler | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `production_residency_proof_landed; mas_proof_ingestion_landed; live_paper_apply_pending` | 先完成 OPL framework foundation，再把 MAS scheduler/watchdog/legacy provider provenance/local diagnostics、sidecar、domain-agent skeleton 和 lifecycle primitives 对齐 OPL stage-led framework，并执行旧面退役收口。 | OPL production proof 与 MAS provider availability ingestion 已落地；真实 MAS paper-line live apply、真实 domain activity soak 和旧 residue 物理退役继续推进。 |
| Cross-cutting form | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `stage_skill_surfaces_landed; ideal_state_read_models_landed; provider_live_apply_pending` | 统一 MAS stage 的人读 surface、machine source、prompt/skill、tool、knowledge、closeout、quality pack 与 OPL projection boundary。 | stage / prompt / skill / knowledge / quality 变更继续按该模板归一；production provider-hosted live apply 完成前，不把 provider projection、typed blocker、repo test、queue receipt 或 production residency proof 写成论文自动化已闭合。 |
| Product enabler | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `active_enabler; follows_framework_migration` | 把迁移后的 MAS progress、conversation、Live Console、terminal attach、安全 action、provider attempt refs 和 artifacts 产品化到 OPL App。 | 作为迁移后用户可见闭环的主要产品化 lane 推进。 |
| Landed foundation | [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md) | `landed_owner_doc; provenance_guard` | 记录当前 MAS monolith、MDS retained roles、workspace layout、entry retirement、functional monolith 和 behavior parity 边界；完整历史记录在 `docs/history/program/`。 | 只维护 guard、provenance 和后续 source intake 分类；新增默认运行能力不回到 MDS absorb 旧路线。 |
| Landed foundation | [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `landed_owner_doc; maintenance_guard` | 记录当前 runtime lifecycle authority、SQLite/file truth boundary、quest/root Git retirement、restore proof 和 migration ledger；完整历史记录在 `docs/history/program/`。 | 维护新 drift、restore diagnostic 和 explicit archive import。 |

## 当前执行顺序

| order | lane | owner doc | current meaning | closeout signal |
| --- | --- | --- | --- | --- |
| `1` | `p2_opl_framework_foundation` | `opl_temporal_mas_runtime_retirement_program.md` plus OPL master roadmap | 先完成 OPL 作为完整智能体框架的 stage attempt、provider runtime、queue/wakeup、retry/dead-letter、approval transport、receipt/projection 和 shared lifecycle/index primitives。 | OPL provider/framework 能承载 MAS stage attempt，并只持有 framework receipt/ref/projection。 |
| `2` | `p2_mas_framework_migration_and_retirement` | `opl_temporal_mas_runtime_retirement_program.md`, `mas_single_project_mds_absorb_program.md`, `runtime_lifecycle_sqlite_migration_program.md` | MAS 迁移到 OPL framework，新旧功能分类迁移/分层/沉淀，过时模块和旧别名/接口按替代证据退役清理。 | direct MAS skill path 与 OPL-hosted path 共享 MAS owner receipts；MAS product-entry / sidecar 可消费 OPL production proof；旧默认依赖无 default caller / no fixture requirement / replacement proof；无 public caller 的旧接口直接删除。workspace-local service wrapper 当前已进入物理退役：新 scaffold 不生成，旧 workspace init 删除旧生成物。 |
| `3` | `p1_opl_app_runtime_workbench` | `opl_app_mas_runtime_workbench_program.md` | 产品化迁移后的用户可见面，让用户在 OPL App 直接看到论文状态、路线、执行器对话、terminal/log、产物和受控 action receipt。 | `mas_opl_runtime_workbench_projection`、safe action receipt、terminal attach owner gate 和 OPL App drilldown 有稳定 contract / UI evidence。 |
| `4` | `stage_surface_standardization` | `stage_surface_standardization_program.md` | 横向统一 stage card、prompt/skill、tool surface、knowledge packet、closeout memory、quality pack、Stage Deliverable Review Page / Index 和 OPL projection boundary，避免 prompt/skill/quality 继续分散增长。 | Generated stage cards、knowledge/closeout obligations、quality pack contract、descriptor locator、主 stage 独立 skill surface、既有 skill 的 pack/RH gate 消费、provider projection / typed blocker proof、OPL production proof ingestion，以及 repo-level review/index workspace locator proof 已落地；最终完成还需要真实 provider-hosted live apply 持续产生 MAS owner progress 或 typed blocker。 |
| `5` | `p0_live_paper_autonomy_acceptance` | `ai_first_paper_autonomy_closure_program.md` | 在 framework-first 目标形态下，用真实 study / paper line 验证 artifact delta、gate replay、AI reviewer judgment、route decision、human gate、stop-loss 或 typed blocker。 | controlled live apply 或 read-only evidence 明确显示 progress delta / blocker；worker live、queue task 或 repo test 只作为支撑证据。 |
| `6` | `p3_foundation_guard` | `mas_single_project_mds_absorb_program.md`, `runtime_lifecycle_sqlite_migration_program.md` | 对 monolith、MDS provenance、runtime lifecycle、restore proof 和 old workspace drift 做 guard 维护。 | 新 drift 有 explicit inventory / restore proof / provenance classification；不新增默认 MDS dependency 或 Git lifecycle。 |

当前统一表达为：P0 是目标和验收面，但执行顺序不是 P0-first；P2 先完成 OPL framework 和 MAS 迁移/退役收口，P1 产品化迁移后的可见面，P0 最后做真实 paper autonomy 验收，P3/P3a 贯穿提供 foundation guard。[MAS Current Development Lines](./current-development-lines.md) 是这些层级的内容级执行地图。

## 已收口状态

| area | current state | owner surface | lifecycle placement |
| --- | --- | --- | --- |
| workspace layout de-MDS/DS | `landed` | `mas_single_project_mds_absorb_program.md` | P3 landed foundation |
| profile / entry retirement | `landed` | `mas_single_project_mds_absorb_program.md` | P3 landed foundation |
| no-history physical absorb | `landed` | `mas_single_project_mds_absorb_program.md`, `docs/references/med-deepscientist/` | P3 landed foundation + references |
| functional monolith completion | `landed` | `mas_single_project_mds_absorb_program.md`, `docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` | P3 landed foundation |
| MDS behavior equivalence audit | `landed_matrix` | `docs/references/mds-parity/` | reference / parity |
| Runtime lifecycle / Git retirement | `landed_owner_doc` | `runtime_lifecycle_sqlite_migration_program.md` | P3a landed foundation |
| Runtime control / progress projection | `landed_contract` | `docs/runtime/control/`, `docs/runtime/projections/` | runtime owner docs |
| Portal / Live Console | `landed_read_model` | `docs/runtime/display/` | runtime/product projection |
| paper-progress degradation guard | `landed_repo_guard` | `docs/runtime/control/`, `docs/references/verification/plan_completion_ledger.md` | runtime guard / evidence |
| Stage surface generated cards / knowledge obligations / quality packs / skill surfaces | `stage_skill_surfaces_landed; review_index_workspace_proof_landed; provider_harness_landed; opl_production_proof_ingested; provider_live_apply_pending` | `stage_surface_standardization_program.md`, `docs/runtime/contracts/stage_surfaces.md`, `stage_surface_contract.py`, `stage_knowledge_contract.py`, `stage_quality_contract.py`, product-entry read models | cross-cutting form + P0/P2/P1 support |
| Stage-led knowledge and publication-route memory | `repo_contract_landed; migration_active` | `ai_first_paper_autonomy_closure_program.md`, `docs/policies/study-workflow/`, `docs/status.md` | P0 objective + policy |
| OPL stage-led / Temporal alignment | `production_residency_proof_landed; mas_proof_ingestion_landed; live_paper_apply_pending` | OPL master roadmap plus `opl_temporal_mas_runtime_retirement_program.md` | P2 active enabler |
| OPL App MAS Runtime Workbench | `active_plan` | `opl_app_mas_runtime_workbench_program.md` | P1 active enabler |
| Workspace-local service wrapper retirement | `cleanup_in_progress; scaffold_removed; init_cleanup_surface` | `current-development-lines.md`, `opl_temporal_mas_runtime_retirement_program.md`, `agent_runtime_interface.md` | P2 legacy cleanup |

## MAS Line Gate Map

当前 portfolio 的执行和汇报统一使用以下 gate 分类。该表只做 program routing；具体实施细节仍归各 owner doc 和 machine-readable contract。

| gate class | meaning | MAS lines |
| --- | --- | --- |
| `landed_foundation` | 已有 repo/source/contract/read-model/receipt 证据；后续只维护 drift、provenance、archive/parity reference 和 guard。 | P3 monolith / MDS provenance、P3a runtime lifecycle、repo-source skeleton anchors、stage skill surface baseline。 |
| `functional_follow_through_gate` | 基础功能 surface 已有；还需要更多 owner receipts、真实 workspace refs、App drilldown、stale scan 或物理 cleanup。 | publication-route memory receipt scaleout、OPL App MAS workbench drilldown、legacy residue physical cleanup、standard skeleton physicalization、stage review/index live follow-through。已满足 direct cleanup 判据的 residue 不再挂旧兼容面。 |
| `production_evidence_gate` | 需要真实 provider、真实 paper-line、live workspace、owner gate 或长时运行证据；文档、repo tests、queue completion 或 provider liveness 不能替代。 | provider/domain activity long soak、provider-hosted guarded apply、MAS live paper owner chain、human gate/resume owner proof。 |

完成某个 gate 的有效证据只有三类：机器可读 owner receipt / no-regression evidence、真实 workspace/runtime artifact locator proof、或带 owner/source/repair action 的 typed blocker。文档状态只解释这些证据，不制造第二真相源。

## Content-Level Disposition

| document | current content role | disposition |
| --- | --- | --- |
| `program_portfolio_consolidation.md` | 当前 program 组合总控、执行顺序、生命周期处置 | 保持当前 owner；每次新增 program 先更新本文。 |
| `current-development-lines.md` | 当前内容级开发线路图、过时/降级材料表、合并吸收规则和优先级 | 保留为执行地图。执行旧计划前先用它判断内容块归属；不作为 runtime、paper 或 publication truth。 |
| `ai_first_paper_autonomy_closure_program.md` | P0 目标合同、repo loop current state、真实 paper soak 验收 | 保留在 program。MAS paper loop 由本文持有；历史 full record 已移入 `docs/history/program/`；OPL provider 与 App UI 实现细节分别进入 P2/P1。 |
| `opl_app_mas_runtime_workbench_program.md` | P1 产品化 enabler owner | 保留为精简 active owner doc。完整旧记录已移入 `docs/history/program/`；当前跟随 framework migration 执行 read-only workbench、action receipt、terminal attach、provider join 等内容级 lane。 |
| `opl_temporal_mas_runtime_retirement_program.md` | P2 framework/runtime enabler owner | 保留为精简 active owner doc。完整旧记录已移入 `docs/history/program/`；当前先执行 OPL framework foundation、MAS framework migration、framework-generic lift、legacy retirement，再进入 final paper-line soak。 |
| `stage_surface_standardization_program.md` | 横向 stage 形式统一 owner | 保留为 stage skill surfaces landed / provider live apply pending 的 cross-cutting program。凡是修改 stage prompt、skill、knowledge packet、closeout memory、quality pack、stage descriptor 或 OPL projection boundary，先按本文归一；不要把已落地的 generated facade / obligations / quality pack / independent skill surfaces 重新写成计划态，也不要把 provider projection / typed blocker proof 写成 production live apply 已完成。 |
| `mas_single_project_mds_absorb_program.md` | P3 landed foundation、MDS provenance、monolith guard current owner | 保留在 program 作为精简 landed owner doc；历史 full record 已移入 `docs/history/program/`；后续只维护 provenance、classification、archive/restore/parity guard。 |
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
- 旧模块/接口/test 只要完成 no-active-caller、replacement proof 和 provenance/fixture 排除，就以删除为完成形态；测试应验证 canonical surface、删除行为或 fail-closed blocker，不再要求旧入口继续可用。
