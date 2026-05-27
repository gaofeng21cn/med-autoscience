# MAS 当前开发线路

Status: `active content-level development map`
Date: `2026-05-25`
Owner: `MedAutoScience`
Purpose: 在 MAS standard OPL Agent 目标态下，给出当前内容级开发线路图。
State: `active_plan_index`
Machine boundary: 本文是人读规划地图。机器真相继续归 MAS runtime/controller/artifact surfaces、OPL provider/framework contracts、product-entry manifest、domain-handler receipt、测试和真实 workspace evidence。

## 当前结论

`docs/active/` 现在按 single Active Truth plan 阅读。[MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) 持有当前 `/goal` 范围和结构/证据差距；本文只保留内容线索引，避免再形成平行总计划。

当前执行优先级是 framework-first：MAS 收敛为 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions + refs-only domain projections`；OPL 承担 generated / hosted runtime、entry、projection 与 App/workbench surface。MAS 只保留医学 study truth、stage semantics、AI reviewer / auditor quality gate、publication route、artifact authority、publication-route memory decision、owner receipt 和 typed blocker。

默认运行口径已经收敛为 OPL/Temporal hosted autonomous runtime：MAS hosted path 启动后，持久在线调度、唤醒、retry、resume、attempt ledger 和 worker residency 由 OPL/Temporal 承担；Codex App 只作为 direct entry / 人机操作面，不作为外围持续 driver；`Codex CLI` 是 stage 内默认 concrete executor；MAS 不拥有 generic daemon、scheduler 或 attempt loop。

历史 MAS-local scheduler、Hermes/MDS、runtime lifecycle/SQLite、workspace-local wrapper 与旧 alias 仅作为 `docs/history/**` provenance、explicit archive/import reference 或 parity oracle 读取；当前默认面是 OPL/Temporal hosted runtime + MAS domain authority refs、owner receipts、typed blockers 和 minimal authority functions。

## 当前内容线

| MAS line | owner doc | gate class | current status | 当前动作 | 证据/测试门槛 |
| --- | --- | --- | --- | --- | --- |
| `opl_framework_foundation` | OPL master docs + [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | `production_evidence_gate` | `provider_residency_projected_domain_activity_soak_pending` | 保持 MAS domain-handler receipt 与 OPL provider attempt/history/retry/dead-letter 串联；MAS 不复制 provider runtime。 | 真实 Temporal/provider 下的 Codex/domain activity long soak、domain activity closeout、owner receipt scaleout 和 no-forbidden-write proof 持续通过。 |
| `mas_framework_migration` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | `landed_foundation_with_live_apply_gate` | `owner_receipt_envelope_landed_live_apply_chain_pending` | 保持 direct skill path 与 OPL-hosted path 同用 MAS owner receipt；OPL 只持 attempt / refs / typed blocker。 | 更多真实 live apply owner chain、artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 blocker。 |
| `dm002_anti_stall_owner_route` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) + [当前状态](../status.md) | `landed_foundation_with_opl_admission_gate` | `next_owner_resolution_landed_opl_admission_pending` | 维护 `always resolve to next owner`、AI reviewer currentness consumption、owner-route/read-model/liveness 优先级和 bounded manifest/read-model refresh；当前 DM002 不再读成 stale reviewer 或 stale live-run 等待，剩余下一跳是 OPL stage-attempt admission / owner-route scaleout。 | 非终局 study 必须投影到唯一 owner action、owner receipt、typed blocker、human gate 或 stop-loss；manifest/status/workbench refresh 只复用 bounded current snapshot，不写 study truth、publication eval、controller decision、artifact/package authority 或 `current_package`。 |
| `publication_route_memory_management` | [Publication Route Memory Policy](../policies/study-workflow/publication_route_memory_policy.md) + [Study Workflow](../policies/study-workflow/README.md) | `functional_follow_through_gate` | `body_free_descriptor_landed_receipt_scaleout_pending` | 保持 body-free descriptor、router/writeback refs 和 maintainer review discipline；OPL 只消费 locator/projection，不拿 memory body。 | 多 paper-line `stage-memory-closeout-route -> memory_write_router_receipt -> inventory/export` proof，覆盖 accepted、rejected、route-back lessons、grouping 和 review summary。 |
| `domain_transition_table_hardening` | [MAS 理想目标态](../references/positioning/mas_ideal_state.md) + OPL master docs | `functional_follow_through_gate` | `domain_transition_read_model_landed_opl_runner_consumption_landed` | 维护 MAS-owned transition spec/table、receipt consumption context 和 owner guard；OPL 只执行 MAS spec、不产生 publication-ready verdict。 | 更多真实 paper-line owner surfaces、focused reducer tests 和 live receipt coverage。 |
| `stage_surface_standardization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `landed_foundation_with_live_apply_gate` | `stage_surfaces_landed_live_apply_followthrough_pending` | 维护 skill-change guard、standard skeleton slot discipline；新增 stage/prompt/skill 必须继续消费 machine-derived refs。 | 真实 live review/index follow-through 和 live paper apply，不提前宣称 production closure。 |
| `ai_first_quality_gate_alignment` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) + [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | `functional_follow_through_gate` | `contract_and_validator_landed_paper_line_reviewer_record_scaleout_pending` | `review`、`write`、`finalize`、`journal-resolution`、`source-intake/scout` stage 产生 AI-first quality record，MAS code 只做 validator / receipt / guard；executor 与 reviewer/auditor 必须独立 invocation。 | focused tests 防止 self-review、mechanical projection、regex、archive import diagnostic、file presence、queue completion、test pass 或普通脚本替代 quality judgment；真实 paper-line 仍需 reviewer/auditor record scaleout。 |
| `app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `functional_follow_through_gate` | `mas_reference_projection_available_opl_app_drilldown_pending` | OPL App 只读消费 MAS workbench projection、stage review/index、memory refs、provider refs 和 owner-route handoff refs。 | App / Workbench 用真实 refs、freshness、blocker 和 owner 验证 drilldown，action 只返回 domain-handler / OPL owner-route handoff refs。 |
| `paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `production_evidence_gate` | `guarded_apply_surface_landed_live_provider_apply_pending` | 多条真实 paper line 经 provider-hosted guarded apply 进入同一 MAS owner chain。 | artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker；provider completion 只是支撑证据。 |
| `standard_agent_purity_projection` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md), [Domain Authority Refs Index Guard](../runtime/domain_authority_refs_index_guard.md) | `landed_foundation_with_evidence_gate` | `standard_agent_purity_source_shape_landed` | current product-entry / domain-handler / read-model 默认只暴露 `standard_agent_purity`、domain authority refs、owner receipts、typed blockers 和 refs-only blockers；停驻、manual hold、runtime parking 与 OPL handoff 等当前用户可见文案只写 MAS / OPL runtime owner；retired runtime action 与 MDS 名称只保留 tombstone/provenance、旧输入测试、parity oracle 或 purity guard。 | generated/hosted parity、MAS receipt parity、focused boundary tests、no-forbidden-write proof 和 current-surface stale scan 通过；真实 paper-line evidence tail 继续另行推进。 |
| `domain_authority_refs_boundary` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) + OPL lifecycle/index/artifact docs | `landed_foundation_with_evidence_gate` | `domain_authority_refs_active` | `domain_authority_refs_index`、paper outbox、storage maintenance、publication-route memory locator 和 artifact lifecycle audit 只允许 body-free refs / locator / receipt / blocker exporter；通用 lifecycle/index/workbench/artifact/terminal transport 逻辑归 OPL primitive。 | refs payload 不含 body / verdict / artifact blob；OPL primitive 消费 refs 后仍不能写 MAS truth；focused tests 覆盖 no body, no authority, no archive-import diagnostic owner。 |
| `standard_skeleton_physicalization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) + [Standard Domain Agent Skeleton](../runtime/contracts/standard_domain_agent_skeleton.md) | `functional_follow_through_gate` | `repo_source_anchors_landed` | 新增 repo-source surface 默认按 standard slots 落位；破坏性目录迁移只在 parity/provenance/no-forbidden-write proof 后做。 | 新增 surface 按 skeleton slot 落位，现有路径保持明确 repo mapping 或 locator/provenance。 |
| `foundation_guard` | [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md) + [Domain Authority Refs Index Guard](../runtime/domain_authority_refs_index_guard.md) | `landed_foundation` | `maintenance_only_no_default_mds_dependency` | 只处理新 drift、restore diagnostic、explicit archive import、MDS provenance / upstream intake 分类。 | 不新增默认 MDS dependency、不恢复 Git lifecycle、不制造第二套 study/runtime truth。 |

规划完成的含义是：每条 MAS 内容线都有唯一入口、owner doc、gate class、下一实施单元和验收证据。它不表示真实 paper live apply、真实 memory writeback、App UI drilldown 或 provider long-soak 已完成；这些继续按上表的 gate 推进。

## OPL Production Functional Closure 对齐

OPL 层面的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`；当前 production/framework closure owner 是 `/Users/gaofeng/workspace/one-person-lab/docs/active/production-framework-closure-gap-matrix.md`。MAS 这里不维护平行 production/framework closure 大计划；MAS 的下一批可立即工程落地工作应作为 OPL 当前 closure matrix 下的 MAS implementation lane 并行推进。

这意味着：

- OPL plan 持有跨仓总目标、吸收顺序、provider/operator/workbench/cross-repo gate；
- MAS 文档只持有 MAS-owned domain receipt、memory、stage review、skeleton、standard Agent projection 和 domain-handler/product-entry projection；
- stage surface standardization 是 MAS implementation lane 的基础依赖之一，不是 production functional closure 的总目标；
- 真实 paper-line provider-hosted live apply 仍是 production evidence gate，不阻塞功能性闭环先落地。

## 当前完成信号与未闭合门槛

| 线路 | 完成信号 |
| --- | --- |
| `opl_framework_foundation` | 已完成：OPL production proof 可被 MAS manifest / domain-handler ingest，`provider_runtime_residency_read_model` 与 `managed_temporal_state_consistency` 可投影；未闭合：真实 domain activity long soak、restart/re-query 后的 domain receipt 串联、human gate/resume owner chain。 |
| `mas_framework_migration` | 已完成：MAS direct skill path 与 OPL-hosted path 使用同一 MAS owner receipt envelope，`provider_completion_is_paper_closure=false` 且 OPL 不写 forbidden MAS truth surface；未闭合：真实 live apply owner receipt chain。 |
| `publication_route_memory_management` | 已完成：人类用户能从 policy/index 进入 Markdown canonical route-memory library、workspace memory pack 与 receipt/proposal locator，并能用 body-free inventory 查看 card 元数据、locator、receipt summary、operator grouping 和 stale/deprecated review summary；未闭合：更多真实论文线通过 MAS router receipt 生成 accepted/rejected reusable lessons。 |
| `standard_agent_purity_projection` | 已完成：current product-entry / domain-handler / read-model 默认只暴露标准 Agent 口径、domain refs、owner receipts 和 typed blockers；未闭合：真实 provider/paper-line evidence tail 和 OPL App/operator drilldown scaleout。 |
| `stage_surface_standardization` | 已完成：generated stage card、route contract、knowledge/closeout obligations、quality pack contract、OPL projection boundary、独立 stage skill surface、provider projection / typed blocker proof、OPL production proof ingestion、Stage Review / Index workspace locator proof，以及 standard skeleton repo-source anchors；未闭合：provider-hosted live apply 证明 stage closeout / memory / quality / artifact delta 沿 MAS owner surface 闭合。 |
| `app_runtime_workbench` | 已完成：MAS 可把 workbench 所需 refs、freshness、owner-route handoff refs 和 typed blocker 汇入 read-only projection；未闭合：OPL App / Workbench drilldown 的产品化展示和真实 operator loop。 |
| `paper_autonomy_acceptance` | 已完成：Read-only evidence 已要求真实论文线 typed closeout projection，guarded apply proof surface 已要求 MAS owner receipt gate，不允许 provider 直接写 workspace truth；未闭合：更多真实 paper line 反复产出 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 MAS owner surface 下的 typed blocker scaleout。 |

## 验证

Docs-only 维护：

- `git diff --check`；
- 用 `rg` spot-check inbound links 和 stale references；
- 不新增断言 prose wording 的测试。

Contract/runtime/product 变更：

- 跑触及线路的 focused owner-surface tests；
- 修改 machine-readable contract、action metadata、schema 或 runtime semantics 时跑 `make test-meta`；
- 常规代码变更跑 `scripts/verify.sh`；
- guarded apply 前先有真实 workspace read-only evidence。
