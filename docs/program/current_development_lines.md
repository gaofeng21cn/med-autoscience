# MAS 当前开发线路

Status: `active content-level development map`
Date: `2026-05-12`
Owner: `MedAutoScience`
Purpose: 在 MAS monolith closeout 和 OPL stage-led framework 新定位之后，给出当前内容级开发线路图。
Machine boundary: 本文是人读规划地图。机器真相继续归 MAS runtime/controller/artifact surfaces、OPL provider/framework contracts、product-entry manifest、sidecar receipt、测试和真实 workspace evidence。

## 当前结论

`docs/program/` 现在按内容线阅读，不按整份旧计划阅读。旧文档里的部分内容仍有效，但当前任务不是“把每个旧计划从头到尾做完”。

当前执行优先级应是 framework-first，但 2026-05-12 已经有一条重要的真实论文证据进入基线：DM002、DM003、Obesity 三篇 paper line 都能输出 OPL-ingestable read-only typed closeout projection。DM002 当前 verdict 是 `ai_reviewer_re_eval`，DM003 与 Obesity 当前 verdict 是 `artifact_delta`；DM002 同时证明 publication-route memory consumed ref 和 MAS-owned writeback receipt refs 可被 OPL/Aion 以 ref-only 方式展示。`real-paper-autonomy-provider-hosted-paper-proof` 把三篇 typed closeout、OPL attempt-owner context、memory refs/writeback receipt refs 和 fail-closed forbidden-write guard 汇成 provider-hosted path 可消费的只读 proof。`real-paper-autonomy-guarded-apply-proof` 进一步给出 MAS-owned guarded apply proof：只有 MAS owner receipt 存在时才承认真实 workspace mutation；否则输出 typed blocker / receipt。不能把 provider attempt、queue completion 或只读 projection 写成投稿级 closure 已完成。

Domain memory 这条线现在可以回到主线任务推进：`publication_route_memory` 已经具备 policy/index、repo seed fixture、workspace memory pack、只读 CLI inventory、stage entry refs、typed closeout proposal 和 MAS router receipt。2026-05-12 fresh OPL 状态显示 MAS/MAG/RCA 三个 domain agent、18 个 family stages、3 个 domain-memory descriptor 均已 resolved；OPL family-runtime 当前本机 provider 是 `local_sqlite`，`provider_ready=true`、`full_online_ready=false`。OPL roadmap 同时显示 Temporal provider core、attempt start/query/signal、residency proof 和 Codex runner harness 已落地，但外部 production Temporal service、managed worker residency 与真实长时 domain soak 仍未闭合。当前最合适继续落地的是更多真实 paper-line writeback receipt、MAS owner inventory 在更多 workspace 的使用、OPL/Aion ref-only 展示和 App/workbench 分组；不应推进 recipe engine、winning-route scorer 或 OPL-owned memory body store。

距离理想情况的当前判断是：stage form / skill authoring 已接近目标形态，knowledge / quality / memory contract 已可用，OPL-hosted execution 与用户产品闭环已有 callable/read-model 证据面但仍未完成 production closure。provider residency typed blocker、guarded apply harness、Stage Deliverable Review Page / Index locator proof、publication-route memory body-free receipt inventory、Workbench reference projection、standard skeleton slot audit 和 legacy residue audit 已落地；剩余关键是把这些 proof surface 接到真实 production Temporal provider 和更多真实 paper-line instance，而不是再补一批手写 Markdown。

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
| `1` | `opl_framework_foundation` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) + OPL master docs | `temporal_provider_core_landed; local_sqlite_ready; mas_residency_read_model_landed; production_residency_pending` | OPL 已具备 stage attempt、attempt start/query/signal、typed closeout ledger、Codex runner harness、Temporal residency proof 和 provider-backed family-runtime read model；MAS manifest 已暴露 `provider_runtime_residency_read_model`，缺真实 production receipt 时返回 typed blocker。当前本机 runtime 仍是 `local_sqlite`，Full online / durable online 未 ready。下一步是外部 production Temporal service、managed worker residency、真实 domain activity soak 和 production cutover。 |
| `2` | `mas_framework_migration` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `domain_adapter_landed; migration_active; memory_soak_readonly_proof_landed` | MAS 迁移为 OPL-admitted domain agent：sidecar/receipt contract、stage descriptor、domain skeleton、artifact locator、authority refs、direct path / hosted path receipt equivalence；publication-route memory 的 DM002 paper-line proof 已能把 stage route-memory refs、typed closeout proposal、MAS router receipt refs 和 OPL/Aion receipt refs 串成 MAS-owned ref-only surface，OPL 不能写 MAS memory body 或 router acceptance。 |
| `2a` | `publication_route_memory_management` | [Publication Route Memory Policy](../policies/study-workflow/publication_route_memory_policy.md), [Study Workflow](../policies/study-workflow/README.md) | `workspace_apply_closure_ready; read_only_inventory_landed; operator_grouping_ready_next` | 继续把可复用论文路线经验写成自然语言 memory card：维护 workspace `publication_route_memory/memory_pack.json`、migration/writeback receipts、MAS `publication-route-memory-inventory` body-free 默认导出和 OPL/Aion ref-only projection。现在可以立刻落地的是更多真实论文线 accepted/rejected receipt、跨 workspace inventory smoke、按 workspace/stage/route family/status 的 ref-only 分组展示、stale/deprecated card 标记和 maintainer-level body review；暂缓 recipe engine、自动 winning-route scorer、OPL-owned memory body 和未审计的普通用户编辑器。 |
| `3` | `feature_partition_and_retirement` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md), [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md), [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `classification_and_cleanup_active` | 新旧功能逐块分类为 retain/move/lift/degrade/retire；退役旧默认依赖、legacy compat、重复 UI 和过时 manager surface。 |
| `4` | `stage_surface_standardization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `stage_skill_surfaces_landed; review_index_locator_proof_landed; provider_harness_landed; provider_live_apply_pending` | 已落地 generated stage cards、缺失 knowledge/closeout obligations、stage quality pack contract、product-entry / family descriptor locator、独立 stage skill surface、既有 skill 的 stage surface / quality pack / RH clean-room gate 消费、provider residency typed blocker、guarded apply harness、真实 workspace review/index locator proof、body-free memory receipt inventory、workbench reference projection、standard skeleton slot audit 和 legacy residue audit。下一步是 production provider residency、provider-hosted live paper apply、更多真实 review/index instance 和更多真实 memory receipts。 |
| `5` | `app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `read_only_projection_landed; app_productization_active` | 在 OPL App 中产品化迁移后的 MAS 状态、route、conversation、terminal/log、artifact、action receipt；不重新定义 runtime truth。 |
| `6` | `paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `repo_loop_landed; provider_hosted_readonly_paper_proof_landed; mas_guarded_apply_proof_surface_landed; live_provider_apply_pending` | 在 OPL framework + migrated MAS 形态下做真实 paper-line soak；当前 guarded apply proof 已覆盖 DM002/DM003/Obesity typed closeout、DM002 memory/writeback/receipt refs、MAS owner receipt gate 和 fail-closed forbidden-write guard。下一步仍是 live provider-hosted guarded apply 下的 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。 |
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

## 当前完成信号

| 线路 | 完成信号 |
| --- | --- |
| `opl_framework_foundation` | OPL provider/framework 能稳定承载 stage attempt、queue/wakeup、retry/dead-letter、approval/human gate、receipt/projection 和 shared lifecycle/index primitive。 |
| `mas_framework_migration` | MAS direct skill path 与 OPL-hosted path 使用同一 MAS owner receipts，且 OPL 不写 forbidden MAS truth surface。 |
| `publication_route_memory_management` | 人类用户能从 policy/index 进入 workspace memory pack 与 receipt/proposal locator，并能用 `medautosci publication route-memory-inventory --workspace-root <workspace>` body-free 查看 card 元数据、locator 和 receipt summary；OPL/Aion 只显示 consumed refs、writeback receipt refs、rejected reason、freshness 和分组信息；更多真实论文线通过 MAS router receipt 生成 accepted/rejected reusable lessons。 |
| `feature_partition_and_retirement` | 旧默认依赖、legacy compat、重复 UI、过时 manager surface 完成分类、替代和退役清理；保留项都有明确 owner 和用途。 |
| `stage_surface_standardization` | 当前完成信号已覆盖 generated stage card、route contract、knowledge/closeout obligations、quality pack contract、OPL projection boundary、`baseline` / `experiment` / `analysis-campaign` / `review` 独立 stage skill surface、既有 skill 的 stage surface / quality pack / RH clean-room gate 消费，以及 provider projection / typed blocker proof；最终完成还要求 provider-hosted live apply 证明 stage closeout / memory / quality / artifact delta 沿 MAS owner surface 闭合。 |
| `app_runtime_workbench` | 用户在 OPL App 看到 MAS study progress、route、conversation、terminal/log、artifacts、source refs 和 safe action receipts，不必依赖 CLI 或 local HTML。 |
| `paper_autonomy_acceptance` | Read-only evidence 已要求三篇真实论文线各有 typed closeout projection，且至少一篇带 memory consumed/writeback receipt refs；guarded apply proof surface 已要求 MAS owner receipt gate，不允许 provider 直接写 workspace truth。Production evidence 还要求 provider-hosted live apply 能反复产出 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 MAS owner surface 下的 typed blocker。 |
| `monolith_and_mds_foundation_guard` | 后续 MDS/DeepScientist 引用被分类，不能成为默认 runtime、quality 或 artifact authority。 |
| `runtime_lifecycle_foundation_guard` | 新 runtime/Git/path drift 被 inventory、必要时 archive/restore、完成验证，并保持在默认 MAS authority 之外。 |

## 距离理想态的后续切片

| slice | why now | owner doc | completion proof |
| --- | --- | --- | --- |
| `provider_residency` | MAS read model 和 typed blocker 已落地，下一风险在生产 provider 是否真实长驻、可恢复、可查询。 | P2 / OPL master docs | Temporal-backed worker residency、restart/re-query、retry/dead-letter、long soak receipt。 |
| `provider_guarded_apply_soak` | guarded apply harness 已覆盖 owner receipt gate、provider unavailable、duplicate/conflict、forbidden-write；还需要真实 provider-hosted live apply。 | P0 + stage surface program | attempt id、typed closeout、MAS owner receipt、artifact delta / gate replay / human gate / typed blocker、no-forbidden-write proof。 |
| `stage_review_index_workspace_proof` | review/index locator proof 和 Portal/Workbench read-only 展示已落地，仍需更多真实 paper-line instance。 | stage surface program + P1 | workspace latest review page / index refs、freshness、claim impact、human annotation、next owner，Portal/Workbench 只读展示。 |
| `publication_route_memory_receipt_scaleout` | OPL/Aion body-free receipt inventory 已落地，仍需更多真实 accepted/rejected lessons。 | Study Workflow / publication route memory policy | 多 paper-line router receipts、body-free inventory、OPL/Aion ref-only 分组。 |
| `legacy_residue_retirement` | legacy residue audit 已落地，后续按 finding 清理或保留 reference。 | P2 / P3 / P3a | stale scan、no default caller proof、replacement proof、focused compatibility tests。 |
| `standard_skeleton_physicalization` | skeleton slot audit 和新 surface 默认 slot 已落地；物理目录迁移仍后置。 | stage surface program | 新增 surface 按 skeleton slot 落位，旧 facade/locator 保持兼容。 |

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
