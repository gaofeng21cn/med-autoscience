# MAS 当前开发线路

Status: `active content-level development map`
Date: `2026-05-14`
Owner: `MedAutoScience`
Purpose: 在 MAS monolith closeout 和 OPL stage-led framework 新定位之后，给出当前内容级开发线路图。
Machine boundary: 本文是人读规划地图。机器真相继续归 MAS runtime/controller/artifact surfaces、OPL provider/framework contracts、product-entry manifest、sidecar receipt、测试和真实 workspace evidence。

## 当前结论

`docs/program/` 现在按内容线阅读，不按整份旧计划阅读。旧文档里的部分内容仍有效，但当前任务不是“把每个旧计划从头到尾做完”。

当前执行优先级应是 framework-first，但 2026-05-12/13 已经有两类重要证据进入基线。第一，DM002、DM003、Obesity 三篇 paper line 都能输出 OPL-ingestable read-only typed closeout projection。DM002 当前 verdict 是 `ai_reviewer_re_eval`，DM003 与 Obesity 当前 verdict 是 `artifact_delta`；DM002 同时证明 publication-route memory consumed ref 和 MAS-owned writeback receipt refs 可被 OPL/Aion 以 ref-only 方式展示。`real-paper-autonomy-provider-hosted-paper-proof` 把三篇 typed closeout、OPL attempt-owner context、memory refs/writeback receipt refs 和 fail-closed forbidden-write guard 汇成 provider-hosted path 可消费的只读 proof。`real-paper-autonomy-guarded-apply-proof` 进一步给出 MAS-owned guarded apply proof：只有 MAS owner receipt 存在时才承认真实 workspace mutation；否则输出 typed blocker / receipt。第二，OPL production proof 已显示 `production_residency_proven`，MAS product-entry manifest 与 sidecar export 已能通过 `--opl-production-proof` 把 provider availability 切到 available，同时保持 `can_write_domain_truth=false`。不能把 provider attempt、queue completion、只读 projection 或 production residency proof 写成投稿级 closure 已完成。

Domain memory 这条线现在已经进入 functional follow-through：`publication_route_memory` 已经具备 policy/index、Markdown canonical library、9 张富文本 repo seed cards、workspace memory pack、只读 CLI inventory、stage entry refs、typed closeout proposal、MAS router receipt、OPL/Aion body-free receipt inventory、按 workspace/stage/route family/status 的 ref-only grouping，以及 stale/deprecated review summary。旧 `study_archetypes` 仍是第一代 route bias / contract input，不是完整经验库；完整入口是 Study Workflow -> Publication Route Memory Policy -> Publication Route Memory Library -> seed index / workspace pack / inventory / writeback receipts。2026-05-12/14 fresh OPL 状态显示 MAS/MAG/RCA 三个 domain agent、18 个 family stages、3 个 domain-memory descriptor 均已 resolved；OPL roadmap 同时显示 Temporal provider core、attempt start/query/signal、residency proof、Codex runner harness 和 task-bound provider attempt bridge 已落地；fresh proof 已证明 managed Temporal service + worker 的 production residency，MAS product-entry manifest 与 sidecar export 也已能通过 `--opl-production-proof` 将 provider availability 从 typed blocker 切到 available。剩余不是 MAS watchdog 功能性执行能力本身，而是真实 MAS paper-line provider-hosted live apply、human gate/resume owner chain、长时 domain activity soak、更多真实 paper-line memory writeback receipts、App/workbench polish 和 legacy residue cleanup；不应推进 recipe engine、winning-route scorer 或 OPL-owned memory body store。

2026-05-14 functional follow-through 状态：MAS runtime owner surface 已补齐 closed controller work-unit authorization 清理、runtime turn closeout paper-facing artifact delta freshness、supervisor-only live quality repair owner routing、AI reviewer currentness guard、runtime-read manual finish guard 和 publication-route memory operator grouping/review summary。它们都属于 repo-level owner/projection surface，可由 focused tests 验证；它们仍不替代真实 provider-hosted paper apply、human gate/resume 或 publication closure evidence。

2026-05-14 全线闭环执行面：`mas_functional_closure_status_projection` 已进入 product-entry manifest 与 sidecar export。它把本文的 9 条 MAS line 映射成同一份 read-only owner projection：provider residency、MAS owner receipt envelope、publication-route memory descriptor/receipt refs、stage surface/skeleton、workbench refs、paper autonomy guarded apply、legacy residue 和 P3 foundation guard 都有 `line_id`、`gate_class`、owner surface refs、evidence refs、typed blockers 与 authority boundary。该 surface 的全局语义固定为 `functional_surfaces_projected_production_evidence_gated`，并显式声明 `provider_completion_is_paper_closure=false`、`publication_closure_claimed=false`。因此，MAS repo 内的规划聚合与功能性 read-model 闭环已完成；真实 domain activity long soak、provider-hosted live paper apply、human gate/resume 和更多真实 memory writeback receipts 继续作为 production / live evidence gate 暴露 typed blocker，不被 repo tests 或 projection 代替。

距离理想情况的当前判断是：stage form / skill authoring 已接近目标形态，knowledge / quality / memory contract 已可用，OPL-hosted execution 与用户产品闭环已有 callable/read-model 证据面但仍未完成 production closure。provider residency typed blocker、guarded apply harness、Stage Deliverable Review Page / Index locator proof、publication-route memory body-free receipt inventory、Workbench reference projection、standard skeleton repo-source physical anchors、workspace/runtime evidence receipt、standard skeleton slot audit 和 legacy active-path tombstones 已落地；剩余关键是把这些 proof surface 接到真实 production Temporal provider 和更多真实 paper-line instance，而不是再补一批手写 Markdown。

## MAS 全线规划闭环

本文是 MAS 当前开发规划的唯一入口。后续不要再为 MAS production closure、stage surface、paper autonomy、App workbench 或 legacy cleanup 新建平行总计划；新增工作先落到本文的内容线路，再跳到对应 owner 文档执行。

当前 MAS 线已经完成规划分层：

- `landed_foundation`：已经有 repo/source/contract/read-model/receipt 证据，后续只维护 drift、兼容和 provenance；
- `functional_follow_through_gate`：不是基础功能缺口，而是需要更多 owner receipt、真实 workspace refs、UI drilldown、stale scan 或物理 cleanup 的工程收口；
- `production_evidence_gate`：需要真实 provider、真实 paper-line、live workspace、owner gate 或长时运行证据；不能用文档、repo tests、queue completion 或 provider liveness 代替。

| MAS line | owner doc | gate class | planning status | next implementation unit | done evidence |
| --- | --- | --- | --- | --- | --- |
| `p2_provider_residency_and_activity_soak` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) + OPL master docs | `production_evidence_gate` | `functional_projection_landed; domain_activity_soak_pending` | 真实 Temporal/provider 下的 Codex/domain activity long soak、restart/re-query、retry/dead-letter、attempt history 与 MAS sidecar receipt 串联。 | `mas_functional_closure_status_projection` 暴露 provider residency / managed Temporal state / domain activity typed blocker；最终仍需 OPL attempt refs + MAS sidecar dispatch receipt + domain activity closeout + no-forbidden-write proof。 |
| `p2_mas_framework_migration` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `landed_foundation_with_live_apply_gate` | `functional_projection_landed; live_apply_owner_chain_pending` | 保持 direct skill path 与 OPL-hosted path 同用 MAS owner receipt；后续只补真实 live apply owner chain。 | `mas_functional_closure_status_projection` 暴露 owner receipt envelope 与 live owner receipt typed blocker；OPL 只持 attempt / refs / typed blocker；MAS owner surface 给出 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 blocker。 |
| `publication_route_memory_management` | [Publication Route Memory Policy](../policies/study-workflow/publication_route_memory_policy.md) + [Study Workflow](../policies/study-workflow/README.md) | `functional_follow_through_gate` | `functional_projection_landed; body_free_descriptor_landed_receipt_scaleout_pending` | 扩展更多真实 accepted / rejected / route-back receipts，补跨 workspace inventory smoke 和 maintainer review discipline。 | `mas_functional_closure_status_projection` 默认暴露 body-free memory descriptor / receipt scaleout typed blocker；`publication-route-memory-inventory` 已有 operator grouping 与 stale/deprecated review summary；多 paper-line `stage-memory-closeout-route -> memory_write_router_receipt -> inventory/export` proof 仍由真实 workspace receipt 扩展。 |
| `stage_surface_standardization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `landed_foundation_with_live_apply_gate` | `functional_projection_landed; stage_surfaces_landed_live_apply_followthrough_pending` | 维护 skill-change guard、live review/index follow-through、standard skeleton slot discipline；新增 stage/prompt/skill 必须继续消费 machine-derived refs。 | `mas_functional_closure_status_projection` 暴露 standard skeleton / stage surfaces 与 live provider owner-chain typed blocker；generated stage card、knowledge/closeout obligations、quality pack、review/index locator 和 MAS owner closeout refs 已可投影；live paper apply 前不宣称 production closure。 |
| `p1_app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `functional_follow_through_gate` | `functional_projection_landed; opl_app_drilldown_pending` | OPL App 读 MAS workbench projection、stage review/index、memory refs、provider refs、安全 action receipt 和 terminal attach gate。 | `mas_functional_closure_status_projection` 暴露 workbench reference projection 与 App drilldown typed blocker；App / Workbench 只读展示真实 refs、freshness、blocker 和 owner；action 只返回 MAS typed receipt。 |
| `p0_live_paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `production_evidence_gate` | `functional_projection_landed; live_provider_apply_pending` | DM002、DM003、Obesity 等真实 paper line 经 provider-hosted guarded apply 进入 MAS owner chain。 | `mas_functional_closure_status_projection` 暴露 guarded apply surface 与 provider-hosted live paper apply typed blocker；最终证据仍是 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker；provider completion 只是支撑证据。 |
| `legacy_residue_retirement` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md), [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md), [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `functional_follow_through_gate` | `functional_projection_landed; no_active_default_caller_proven_cleanup_policy_satisfied` | 按 `legacy_residue_audit` finding 做 no-active-caller scan、replacement proof、可删代码删除或 history/tombstone 归档。 | `mas_functional_closure_status_projection` 聚合 tombstone proof 与 residue audit；当前 read model 可证明无 active default caller，物理删除仍需 stale scan、replacement proof、无 fixture/provenance dependency、focused compatibility tests。 |
| `standard_skeleton_physicalization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) + [Standard Domain Agent Skeleton](../runtime/contracts/standard_domain_agent_skeleton.md) | `functional_follow_through_gate` | `functional_projection_landed; repo_source_anchors_landed` | 新增 repo-source surface 默认按 standard slots 落位；破坏性目录迁移只在 parity/provenance/no-forbidden-write proof 后做。 | `mas_functional_closure_status_projection` 聚合 standard skeleton repo-source anchors；skeleton audit 能解释标准 slot 与现有路径；workspace artifacts、memory body、receipt instances 仍 locator-only。 |
| `p3_foundation_guard` | [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md) + [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `landed_foundation` | `landed_foundation; maintenance_only_no_default_mds_dependency` | 只处理新 drift、restore diagnostic、explicit archive import、MDS provenance / upstream intake 分类。 | `mas_functional_closure_status_projection` 将该线固定为 maintenance-only；不新增默认 MDS dependency、不恢复 Git lifecycle、不制造第二套 study/runtime truth。 |

规划完成的含义是：每条 MAS 内容线都有唯一入口、owner doc、gate class、下一实施单元和验收证据。它不表示真实 paper live apply、真实 memory writeback、App UI drilldown 或 legacy 物理删除已经完成；这些继续按上表的 gate 推进。

## OPL Production Functional Closure 对齐

OPL 层面的 umbrella plan 是 `one-person-lab/docs/active/production-functional-closure-plan.zh-CN.md`。MAS 这里不再维护一份平行的 production-functional closure 大计划；MAS 的下一批可立即工程落地工作应作为该 umbrella plan 的 MAS implementation lane 并行推进。

这意味着：

- OPL plan 持有跨仓总目标、吸收顺序、provider/operator/workbench/cross-repo gate；
- MAS 文档只持有 MAS-owned domain receipt、memory、stage review、skeleton、legacy cleanup 和 sidecar/product-entry projection；
- stage surface standardization 是 MAS implementation lane 的基础依赖之一，不是 production functional closure 的总目标；
- 真实 paper-line provider-hosted live apply 仍是 production evidence gate，不阻塞下面这些功能性闭环先落地。

| OPL umbrella lane | MAS 对应 implementation lane | MAS owner surface | MAS done signal |
| --- | --- | --- | --- |
| `owner-receipt-contract-generalization` | `mas_owner_receipt_envelope` | sidecar dispatch receipt、guarded apply receipt、stage closeout、human gate、stop-loss、paper progress owner receipt | paper guarded apply、stage closeout、memory writeback、human gate 和 stop-loss 都能投影成同构 MAS owner receipt 或 typed blocker refs；OPL 只保存 refs。 |
| `domain-memory-apply-generalization` | `publication_route_memory_receipt_generalization` | stage knowledge plane、publication-route memory pack、writeback proposal/router receipt、body-free inventory | consumed/proposal/accepted/rejected/writeback refs 覆盖 DM002 proof 之外的 fixture / workspace proof；OPL/Aion 只读展示 locator、freshness、receipt refs，不持有 memory body。 |
| `lifecycle-guarded-apply-generalization` | `mas_lifecycle_artifact_receipt_requirement` | runtime lifecycle locator、artifact locator、restore/retention receipt boundary | OPL-owned metadata 可被 locator/projection 消费；任何 domain artifact 删除、重写或 package mutation 都必须返回 MAS domain receipt requirement 或 typed blocker。 |
| `physical-skeleton-follow-through` | `mas_standard_skeleton_followthrough` | `standard_domain_agent_skeleton`、agent/stage/skill/knowledge/quality/sidecar/projection locator | repo-source physical anchors 已落到 `agent/`、`contracts/runtime/`、`runtime/artifact_locator/` 和 `docs/runtime/contracts/`；新增 repo-source surface 默认映射到标准 slot，旧路径保留 facade/locator/provenance，不做破坏性大搬迁。 |
| `legacy-active-path-final-retirement` | `mas_legacy_residue_no_active_caller_proof` | P2 classification、MDS/Hermes/local scheduler provenance、compat tests | stale scan + no default caller proof + replacement proof；legacy active-path tombstone contract 与 history tombstone 已落地，可删代码仍按无 active reference / 无 fixture 依赖单独执行。 |
| `operator-workbench-drilldown` | `mas_workbench_projection_completion` | `mas_opl_runtime_workbench_projection`、Progress Portal stage review、provider readiness refs、route-memory refs、safe action receipts | provider readiness、stage review/index、memory refs、safe action receipt、typed blocker 在同一 App-consumable read model 中分 lane 展示，且不写 MAS truth。 |
| `cross-repo-production-closeout-gate` | `mas_functional_closure_status_projection` | product-entry manifest、sidecar export、focused verification report | MAS 可以给 OPL closeout gate 提供当前 descriptor alignment、provider proof ingestion、memory receipt coverage、stage review proof、legacy residue state 和 typed blockers。 |

当前执行优先级应是 framework-first：

1. 先把 OPL 做成完整的 stage-led、以 Agent executor 为最小执行单位的智能体框架，具备 durable stage attempt、queue/wakeup、retry/dead-letter、approval/human gate、receipt/projection、shared lifecycle/index primitive 和 provider-backed runtime。
2. 再把 MAS 迁移到这个框架：MAS 暴露 domain-agent skeleton、stage descriptor、sidecar export/dispatch、owner receipt、artifact locator、projection builder 和 authority refs；OPL 承载框架运行外围。
3. 同步把新旧功能逐块分类、迁移、分层或沉淀：domain truth 留在 MAS，framework-generic lifecycle/index/restore/retention 能力上收到 OPL，local diagnostics 和 evidence surface 显式降级。
4. 同步推进 stage surface 形式统一：主 stage card、生成人读 facade、缺失 knowledge / closeout obligations、stage-selectable quality packs、OPL descriptor locator 和 `baseline` / `experiment` / `analysis-campaign` / `review` 独立 stage skill surface 已落地；既有 skill 已消费 stage surface、quality pack 与 Research Harness clean-room gates。剩余重点是用真实 provider-hosted live apply 证明目标形态。横向 owner 见 [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md)。
5. 过时模块、Hermes/MDS/default-compat path、旧 manager wording 和重复 UI 入口在替代证据存在后进入退役清理；这属于迁移收口条件，不应无限期后置。
6. 最后再做真实 E2E / paper-line soak / App workbench 验收，证明新框架下 MAS paper autonomy 能产生 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 typed blocker。

这里的“最后再测试”指真实运行验收和 paper soak，不表示代码级验证后置。每个迁移步骤仍必须跑对应 focused tests、contract checks 和 repo-native verification。

## 内容线路

| 顺序 | 线路 | owner 文档 | 当前状态 | 当前实际要做 |
| --- | --- | --- | --- | --- |
| `1` | `opl_framework_foundation` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) + OPL master docs | `provider_residency_projected_domain_activity_soak_pending` | OPL 已具备 stage attempt、attempt start/query/signal、typed closeout ledger、Codex runner harness、Temporal production residency proof 和 provider-backed family-runtime read model；MAS manifest / sidecar 已暴露 `provider_runtime_residency_read_model` 与 `managed_temporal_state_consistency`，有 OPL proof 时切到 available/consistent。下一步是真实 domain activity 长时 soak 和 provider-hosted paper apply。 |
| `2` | `mas_framework_migration` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `owner_receipt_envelope_landed_live_apply_chain_pending` | MAS 迁移为 OPL-admitted domain agent：sidecar/receipt contract、stage descriptor、domain skeleton、artifact locator、authority refs、direct path / hosted path receipt equivalence；product-entry manifest 与 sidecar export 已消费 OPL production proof 并把 provider read model 切到 available，同时保持 OPL 不能写 MAS memory body、router acceptance、domain truth 或 publication authority。下一步是真实 live apply owner receipt chain。 |
| `2a` | `publication_route_memory_management` | [Publication Route Memory Policy](../policies/study-workflow/publication_route_memory_policy.md), [Study Workflow](../policies/study-workflow/README.md) | `body_free_descriptor_landed_receipt_scaleout_pending` | 继续把可复用论文路线经验写成富文本自然语言 memory card：维护 workspace `publication_route_memory/memory_pack.json`、migration/writeback receipts、MAS `publication-route-memory-inventory` body-free 默认导出、OPL/Aion ref-only projection、operator grouping 和 stale/deprecated review summary。现在可以继续落地的是更多真实论文线 accepted/rejected receipt、跨 workspace inventory smoke、maintainer-level review discipline 和 App/workbench polish；暂缓 recipe engine、自动 winning-route scorer、OPL-owned memory body 和未审计的普通用户编辑器。 |
| `3` | `feature_partition_and_retirement` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md), [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md), [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `no_active_default_caller_proven_cleanup_policy_satisfied` | 新旧功能逐块分类为 retain/move/lift/degrade/retire；旧 active-path wording 已有 tombstone contract 和 no-active-default-caller proof，后续只按无 active reference / 无 fixture 依赖 / replacement proof 做物理删除。 |
| `4` | `stage_surface_standardization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `stage_surfaces_landed_live_apply_followthrough_pending` | 已落地 generated stage cards、缺失 knowledge/closeout obligations、stage quality pack contract、product-entry / family descriptor locator、独立 stage skill surface、既有 skill 的 stage surface / quality pack / RH clean-room gate 消费、provider residency read model、guarded apply harness、Stage Review / Index workspace locator proof、body-free memory receipt inventory、workbench reference projection、standard skeleton physical anchors、workspace/runtime evidence receipt 和 legacy active-path tombstones。下一步是真实 provider-hosted live paper apply、更多真实 review/index instance 和更多真实 memory receipts。 |
| `5` | `app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `mas_reference_projection_available_opl_app_drilldown_pending` | OPL App / Workbench 继续产品化 MAS 状态、route、conversation、terminal/log、artifact、safe action receipt 和 typed blocker drilldown；MAS 只提供 read-only projection，不重新定义 runtime truth。 |
| `6` | `paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `guarded_apply_surface_landed_live_provider_apply_pending` | 在 OPL framework + migrated MAS 形态下做真实 paper-line soak；当前 guarded apply proof 已覆盖 DM002/DM003/Obesity typed closeout、DM002 memory/writeback/receipt refs、MAS owner receipt gate 和 fail-closed forbidden-write guard。下一步仍是 live provider-hosted guarded apply 下的 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。 |
| `7` | `recurring_learning_support` | `docs/status.md`, `docs/references/**` | `triggered_support` | DeepScientist / external harness / adjacent framework intake 只在触发时执行，dated snapshot 留在 history。 |

## 已过时或已降级内容

| 内容 | 当前处置 |
| --- | --- |
| “P0 等于 MAS-only runtime 完成” | 已过时。P0 是目标和验收，产品/框架依托分别在 P1/P2。 |
| “整份 P1 workbench 计划都要做完” | 已替换为 P1 内容 lane：read-only workbench、action receipt、terminal attach、provider join。 |
| “整份 P2 Temporal retirement 计划都要做完” | 已替换为 framework-first 的 P2 内容 lane：OPL framework foundation、MAS framework migration、framework-generic lift、legacy retirement、再进入 paper-line soak。 |
| Hermes-first 或 MAS local scheduler 作为 Full online target | 已降级。OPL Full online target 是 Temporal-backed production runtime；MAS local scheduler 是 diagnostics/fallback；Hermes 只保留为 explicit optional executor adapter / proof lane，除非未来证据改变。 |
| 旧 MDS daemon/WebUI/runtime transport 作为默认依赖 | 默认路径已退役；只保留 provenance、explicit archive import、backend audit、upstream learning 或 parity reference。 |
| Runtime lifecycle Git-era cleanup 作为活跃大迁移 | 已落地。新发现问题按 P3a drift/maintenance 处理，除非证明有 live writer regression。 |
| Local Portal / Live Console 作为最终主产品面 | OPL App workbench 成为主用户面后，local Portal / Live Console 降级为 fallback/debug/evidence。 |
| 依赖 Markdown wording 的测试或脚本 | 方向无效。机器接口应使用 schema、JSON、CLI/API payload、manifest 或 durable semantic ID。 |

## 合并与吸收规则

编辑旧 program 内容时按下表归位：

| 内容类型 | 归属 |
| --- | --- |
| 论文质量、reviewer repair、route decision、stage knowledge/memory、live-soak acceptance | P0 |
| App-native 状态、路线视图、conversation timeline、terminal/log panel、安全 action UI | P1 |
| OPL provider、Temporal attempt、queue、retry/dead-letter、approval transport、sidecar receipt、provider projection | P2 或 OPL master docs |
| MDS provenance、compatibility guard、explicit archive import、no-history source intake、behavior parity | P3 或 `docs/references/mds-parity/` / `docs/references/med-deepscientist/` |
| runtime lifecycle authority、SQLite/file boundary、Git retirement drift、restore proof | P3a |
| 可服务多个 domain 的 lifecycle/index/restore/retention primitive | 先进入 P2 的 `lift_to_opl_framework`，再进入 OPL framework docs |
| stage prompt、skill、knowledge packet、closeout memory、quality pack、stage descriptor、OPL projection boundary | 先进入 `stage_surface_standardization_program.md` 做形式归一，再落到 P0/P2/P1 对应 owner surface |
| dated evidence、旧 phase table、旧 activation package、superseded checklist | `docs/history/program/` |
| recurring external learning trigger 和 absorption rule | `docs/status.md` 或 `docs/references/**`，单次执行快照进入 history |

## 优先级规则

1. Framework-first：OPL 完整智能体框架是 MAS 迁移和真实 paper soak 的前置条件。
2. 迁移优先于测试：真实 E2E / paper soak 应验证迁移后的目标形态，不应验证一个即将退役的 MAS-local 运行外围。
3. 退役清理属于迁移收口：旧默认依赖、legacy compat、重复 UI、过时 manager surface 不应无限期留作“以后再说”；删除前必须有替代证据、无默认调用、无 fixture/provenance 必需。
4. 只上收通用 framework primitive：lifecycle、locator、retention、restore proof、attempt receipt、cache cleanup 可以进入 OPL；study truth 和 publication authority 留在 MAS。
5. 产品 workbench 跟随框架迁移：OPL App 展示 OPL framework + MAS owner receipts 的状态，不重新发明第二套 runtime truth。
6. 代码级验证持续执行：每个 contract、runtime、projection 或 cleanup 步骤都要跑 focused tests；最后的真实 paper soak 是目标形态验收。

## 当前完成信号与未闭合门槛

| 线路 | 完成信号 |
| --- | --- |
| `opl_framework_foundation` | 已完成：OPL production proof 可被 MAS manifest / sidecar ingest，`provider_runtime_residency_read_model` 与 `managed_temporal_state_consistency` 可投影；未闭合：真实 domain activity long soak、restart/re-query 后的 domain receipt 串联、human gate/resume owner chain。 |
| `mas_framework_migration` | 已完成：MAS direct skill path 与 OPL-hosted path 使用同一 MAS owner receipt envelope，`provider_completion_is_paper_closure=false` 且 OPL 不写 forbidden MAS truth surface；未闭合：真实 live apply owner receipt chain。 |
| `publication_route_memory_management` | 已完成：人类用户能从 policy/index 进入 Markdown canonical route-memory library、9 张富文本 seed cards、workspace memory pack 与 receipt/proposal locator，并能用 `medautosci publication route-memory-inventory --workspace-root <workspace>` body-free 查看 card 元数据、locator、receipt summary、operator grouping 和 stale/deprecated review summary；OPL/Aion 只显示 consumed refs、writeback receipt refs、rejected reason、freshness 和分组信息；未闭合：更多真实论文线通过 MAS router receipt 生成 accepted/rejected reusable lessons。 |
| `feature_partition_and_retirement` | 已完成：legacy active-path tombstone contract、no-active-default-caller proof 和 cleanup policy satisfied projection；MAS watchdog 的通用在线执行、queue/wakeup/retry/signal/query 责任已有 OPL native replacement proof，MAS `runtime_watch` 保留为 domain truth、progress/read-model 和 local diagnostics；未闭合：按 audit finding 做可删代码的物理删除。 |
| `stage_surface_standardization` | 已完成：generated stage card、route contract、knowledge/closeout obligations、quality pack contract、OPL projection boundary、`baseline` / `experiment` / `analysis-campaign` / `review` 独立 stage skill surface、既有 skill 的 stage surface / quality pack / RH clean-room gate 消费、provider projection / typed blocker proof、OPL production proof ingestion、Stage Review / Index workspace locator proof，以及 standard skeleton repo-source anchors；未闭合：provider-hosted live apply 证明 stage closeout / memory / quality / artifact delta 沿 MAS owner surface 闭合。 |
| `app_runtime_workbench` | 已完成：MAS 可把 workbench 所需 refs、freshness、safe action receipt 和 typed blocker 汇入 read-only projection；未闭合：OPL App / Workbench drilldown 的产品化展示和真实 operator loop。 |
| `paper_autonomy_acceptance` | 已完成：Read-only evidence 已要求三篇真实论文线各有 typed closeout projection，且至少一篇带 memory consumed/writeback receipt refs；guarded apply proof surface 已要求 MAS owner receipt gate，不允许 provider 直接写 workspace truth；未闭合：provider-hosted live apply 反复产出 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 MAS owner surface 下的 typed blocker。 |
| `monolith_and_mds_foundation_guard` | 已完成：后续 MDS/DeepScientist 引用被分类为 provenance、explicit archive import、backend audit、upstream learning 或 parity oracle reference，不能成为默认 runtime、quality 或 artifact authority。 |
| `runtime_lifecycle_foundation_guard` | 已完成：新 runtime/Git/path drift 进入 inventory/archive/restore/verification 维护口径，并保持在默认 MAS authority 之外；未闭合：新发现 live writer regression 时按 P3a 单独处理。 |

## 距离理想态的后续切片

| slice | why now | owner doc | completion proof |
| --- | --- | --- | --- |
| `provider_residency_status_and_activity_soak` | `mas_functional_closure_status_projection` 已把 provider residency 投影为可读状态，并保留 `mas_domain_activity_long_soak_pending` typed blocker；下一风险在真实 domain activity 是否能长时运行、恢复和查询。 | P2 / OPL master docs | `family-runtime status --provider temporal` managed-state 一致性、restart/re-query、retry/dead-letter、Codex/domain activity long soak receipt、MAS sidecar receipt。 |
| `provider_guarded_apply_soak` | guarded apply harness 已覆盖 owner receipt gate、provider unavailable、duplicate/conflict、forbidden-write；`provider_hosted_live_paper_apply_pending` 仍是 production evidence gate。 | P0 + stage surface program | attempt id、typed closeout、MAS owner receipt、artifact delta / gate replay / human gate / typed blocker、no-forbidden-write proof。 |
| `stage_review_index_live_provider_followthrough` | repo-level workspace locator proof 和 Portal/Workbench 只读展示已落地；还需要 live provider-hosted apply 持续产出同一类 refs。 | stage surface program + P1 | live attempt 触发 MAS owner closeout 后产生 workspace latest review page / index refs、freshness、claim impact、human annotation、next owner 或 typed blocker，Portal/Workbench 只读展示。 |
| `publication_route_memory_receipt_scaleout` | body-free receipt inventory、operator grouping 和 stale/deprecated review summary 已能投影 migration/writeback accepted/rejected refs；仍需更多真实 accepted/rejected lessons 和跨 workspace smoke。 | Study Workflow / publication route memory policy | 多 paper-line router receipts、body-free inventory、OPL/Aion ref-only 分组、review summary 和 freshness refs。 |
| `legacy_residue_retirement` | legacy active-path tombstone contract、no-active-default-caller proof 和 cleanup policy satisfied projection 已落地；后续只按 finding 删除或保留 reference。 | P2 / P3 / P3a | stale scan、no default caller proof、replacement proof、focused compatibility tests。 |
| `standard_skeleton_physicalization` | repo-source physical anchors 已落地，真实 workspace artifact body 仍 locator-only。 | stage surface program | 新增 surface 按 skeleton slot 落位，旧 facade/locator 保持兼容。 |

## 验证

Docs-only 维护：

- `git diff --check`；
- 用 `rg` spot-check inbound links 和 stale references；
- 不新增断言 prose wording 的测试。

Contract/runtime/product 变更：

- 跑触及线路的 focused owner-surface tests；
- 修改 machine-readable contract、action metadata、schema 或 runtime semantics 时跑 `make test-meta`；
- 常规代码变更跑 `scripts/verify.sh`；
- guarded apply 前先有真实 workspace read-only evidence；
- OPL/App/provider integration 必须显式验证 forbidden-write 边界。
