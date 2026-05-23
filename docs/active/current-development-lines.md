# MAS 当前开发线路

Status: `active content-level development map`
Date: `2026-05-17`
Owner: `MedAutoScience`
Purpose: 在 MAS monolith closeout 和 OPL stage-led framework 新定位之后，给出当前内容级开发线路图。
State: `active_plan_index`
Machine boundary: 本文是人读规划地图。机器真相继续归 MAS runtime/controller/artifact surfaces、OPL provider/framework contracts、product-entry manifest、sidecar receipt、测试和真实 workspace evidence。

## 当前结论

`docs/active/` 现在按内容线阅读，不按整份旧计划阅读。旧文档里的部分内容仍有效，但当前任务不是“把每个旧计划从头到尾做完”。

当前执行优先级是 framework-first：OPL 承担通用 stage runtime、attempt、queue、retry/dead-letter、human-gate transport、projection 与 App/workbench shell；MAS 保留医学 study truth、stage semantics、AI reviewer / auditor quality gate、publication route、artifact authority、publication-route memory decision、owner receipt 和 typed blocker。

默认运行口径已经收敛为 OPL/Temporal hosted autonomous runtime：MAS hosted path 启动后，持久在线调度、唤醒、retry、resume、attempt ledger 和 worker residency 由 OPL/Temporal 承担；Codex App 只作为 direct entry / 人机操作面，不作为外围持续 driver；`Codex CLI` 是 stage 内默认 concrete executor；MAS 不拥有 generic daemon、scheduler 或 attempt loop。

当前机器面已经形成三类基线：

- `mas_functional_closure_status_projection`、product-entry manifest、sidecar export 和 OPL descriptor 能把 MAS 内容线投影为 read-only owner refs、typed blockers、forbidden-write boundary 和 gate class。
- MAS 标准 Agent 结构面已经把 generated surface、domain authority refs、minimal authority function、legacy tombstone/provenance 和 active-source morphology 收敛到主参考口径；结构 closure 不等于真实 paper closure。
- provider residency、guarded apply、publication-route memory inventory、Stage Deliverable Review Page / Index、workbench refs、legacy tombstone 和 AI-first authority boundary 都有 repo / contract / projection 基线，但真实 paper-line provider apply、domain activity long soak、human gate/resume、更多 memory/artifact receipts 和 App drilldown 仍是 evidence gate。

dated proof、具体 attempt、receipt id、follow-through 流水和历史 closeout 只作为 provenance 读取，入口见 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)、[Plan Completion Ledger](../history/program/plan_completion_ledger.md) 和对应 machine-readable contracts。本文只保留当前内容线、owner 文档、gate class、下一实施单元和禁止误写口径。

## MAS 全线规划闭环

本文是 MAS 当前开发规划的唯一入口。后续不要再为 MAS production closure、stage surface、paper autonomy、App workbench 或 legacy cleanup 新建平行总计划；新增工作先落到本文的内容线路，再跳到对应 owner 文档执行。

当前 MAS 线已经完成规划分层；表格中 `结构/功能动作` 只写要改的 owner boundary、接口、模块、调用链或迁移动作，`证据/测试门槛` 只写证明方式、真实运行证据、receipt、soak、coverage 或 focused tests：

- `landed_foundation`：已经有 repo/source/contract/read-model/receipt 证据，后续只维护 drift、provenance 和明确的 archive/restore reference；
- `functional_follow_through_gate`：不是基础功能缺口，而是需要更多 owner receipt、真实 workspace refs、UI drilldown、stale scan 或物理 cleanup 的工程收口；
- `production_evidence_gate`：需要真实 provider、真实 paper-line、live workspace、owner gate 或长时运行证据；不能用文档、repo tests、queue completion 或 provider liveness 代替。

| MAS line | owner doc | gate class | planning status | 结构/功能动作 | 证据/测试门槛 |
| --- | --- | --- | --- | --- | --- |
| `p2_provider_residency_and_activity_soak` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) + OPL master docs | `production_evidence_gate` | `functional_projection_landed; source_fingerprint_owner_loop_proven; multi_paper_task_projection_landed; domain_activity_soak_pending` | 保持 MAS sidecar receipt 与 OPL provider attempt/history/retry/dead-letter 串联；MAS 不复制 provider runtime。 | `mas_functional_closure_status_projection` 暴露 provider residency / managed Temporal state / domain activity typed blocker；source-keyed owner blocker loop 与 multi-paper guarded-apply task projection 已有基线。最终仍需真实 Temporal/provider 下的 Codex/domain activity long soak、domain activity closeout、owner receipt scaleout 和 no-forbidden-write proof 持续通过；单次 attempt / receipt 细节读 history/ledger。 |
| `p2_mas_framework_migration` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `landed_foundation_with_live_apply_gate` | `functional_projection_landed; sidecar_source_fingerprint_landed; owner_stable_blocker_loop_proven; multi_paper_task_projection_landed; live_apply_owner_chain_pending` | 保持 direct skill path 与 OPL-hosted path 同用 MAS owner receipt；OPL 只持 attempt / refs / typed blocker。 | `mas_functional_closure_status_projection` 暴露 owner receipt envelope 与 live owner receipt typed blocker；MAS sidecar export / dispatch 已按 task source fingerprint、owner controller decision refs 与 OPL attempt loop 对齐，并能为多条真实 paper line 生成 guarded-apply pending task；后续证据是更多真实 live apply owner chain、artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 blocker。 |
| `publication_route_memory_management` | [Publication Route Memory Policy](../policies/study-workflow/publication_route_memory_policy.md) + [Study Workflow](../policies/study-workflow/README.md) | `functional_follow_through_gate` | `functional_projection_landed; body_free_descriptor_landed_receipt_scaleout_pending` | 保持 body-free descriptor、router/writeback refs 和 maintainer review discipline；OPL 只消费 locator/projection，不拿 memory body。 | `mas_functional_closure_status_projection` 默认暴露 body-free memory descriptor / receipt scaleout typed blocker；`publication-route-memory-inventory` 已有 operator grouping 与 stale/deprecated review summary；`study-state-matrix` 已能消费 accepted/rejected/blocked publication-route memory writeback receipt；多 paper-line `stage-memory-closeout-route -> memory_write_router_receipt -> inventory/export` proof 仍由真实 workspace receipt 扩展。 |
| `domain_transition_table_hardening` | [MAS 理想目标态](../references/positioning/mas_ideal_state.md) + OPL master docs | `functional_follow_through_gate` | `domain_transition_read_model_landed; opl_runner_consumption_landed; live_receipt_coverage_pending` | 维护 MAS-owned transition spec/table、receipt consumption context 和 owner guard；OPL 只执行 MAS spec、不产生 publication-ready verdict。 | `study-state-matrix` 已投影 JSON/Markdown `domain_transition_table` 并纳入 completion / execution / AI reviewer publication eval / human-gate resume / delivered-package metadata / stop-loss owner receipt / memory writeback receipt 和 fail-closed receipt isolation；OPL generic runner / matrix runner 已作为消费方存在。后续证据是更多真实 paper-line owner surfaces、focused reducer tests 和 live receipt coverage。 |
| `stage_surface_standardization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `landed_foundation_with_live_apply_gate` | `functional_projection_landed; stage_surfaces_landed_live_apply_followthrough_pending` | 维护 skill-change guard、standard skeleton slot discipline；新增 stage/prompt/skill 必须继续消费 machine-derived refs。 | `mas_functional_closure_status_projection` 暴露 standard skeleton / stage surfaces 与 live provider owner-chain typed blocker；generated stage card、knowledge/closeout obligations、quality pack、review/index locator 和 MAS owner closeout refs 已可投影；后续证据是真实 live review/index follow-through 和 live paper apply，不提前宣称 production closure。 |
| `ai_first_quality_gate_alignment` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) + [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | `functional_follow_through_gate` | `contract_and_validator_landed; paper_line_reviewer_record_scaleout_pending` | `minimal_authority_function` 已校准为 `AI-first stage quality gate boundary`；`review`、`write`、`finalize`、`journal-resolution`、`source-intake/scout` stage 产生 AI-first quality record，MAS code 只做 validator / receipt / guard；executor 与 reviewer/auditor 必须独立 invocation。 | `minimal_authority_function_manifest`、pack compiler input、private policy、test-lane manifest、product-entry 和 sidecar/supervision projection 暴露 `judgment_mode` 与 program output policy；focused tests 防止 self-review、mechanical projection、regex、archive import diagnostic、file presence、queue completion、test pass 或普通脚本替代质量 judgment。真实 paper-line 仍需更多 reviewer/auditor record scaleout。 |
| `p1_app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `functional_follow_through_gate` | `functional_projection_landed; opl_app_drilldown_pending` | OPL App 只读消费 MAS workbench projection、stage review/index、memory refs、provider refs 和安全 action receipt。 | `mas_functional_closure_status_projection` 暴露 workbench reference projection 与 App drilldown typed blocker；App / Workbench 需用真实 refs、freshness、blocker 和 owner 验证 drilldown，action 只返回 MAS typed receipt；terminal/log/provider drilldown 只能从 OPL `current_control_state` 读取。 |
| `p0_live_paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `production_evidence_gate` | `functional_projection_landed; live_provider_apply_pending` | 多条真实 paper line 经 provider-hosted guarded apply 进入同一 MAS owner chain。 | `mas_functional_closure_status_projection` 暴露 guarded apply surface 与 provider-hosted live paper apply typed blocker；最终证据仍是 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker；provider completion 只是支撑证据。 |
| `legacy_residue_retirement` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md), [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md), [Domain Authority Refs Index Guard](./runtime_lifecycle_sqlite_migration_program.md) | `functional_follow_through_gate` | `functional_projection_landed; no_resurrection_cleanup_policy_satisfied; current_audit_surface_retired; workspace_service_wrapper_retirement_in_progress` | 旧 residue 的 current product/sidecar audit surface 已删除；当前机器面只保留 `legacy_retirement_tombstone_proof`、`domain_authority_refs_index` 与 `functional_consumer_boundary.retired_legacy_residue_tombstones`。新 workspace 不再生成旧 service wrappers，旧生成物由 `init-workspace` 删除；scheduler / provider lifecycle 管理归 OPL current control state。 | `mas_functional_closure_status_projection` 聚合 tombstone proof 和 retired tombstone machine surface；当前 read model 可证明 default runtime owner 为 OPL。完成门槛是 stale surface scan、scaffold 不再生成、legacy workspace upgrade 删除旧文件、focused init/bootstrap tests 通过；仅 archive/provenance/parity 必需 reader 保留。 |
| `functional_privatization_boundary` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md), [MAS 理想目标态](../references/positioning/mas_ideal_state.md) | `landed_foundation_with_evidence_gate` | `classification_closed; active_private_generic_residue_count=0; functional_structure_gap_count=0` | 已把 runtime/storage/artifact/workbench/terminal/scheduler/runner surfaces 分类为 declarative pack / OPL generated surface、domain authority refs、minimal authority function 或 physical-retired tombstone/provenance gate；5 个结构 closure gate 均由 proof refs 计算为 closed。 | `functional_consumer_boundary`、`contracts/test-lane-manifest.json` 与 domain authority refs guard 固定当前边界：declarative pack/generated surface、domain authority refs、minimal authority function、physical-retired legacy；focused tests 证明 manifest、product-entry、sidecar/supervision projection 同步。剩余是 real App/user evidence、authority receipt scaleout 与 provider/paper-line evidence gate。 |
| `generated_surface_bridge_retirement` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) + OPL pack compiler docs | `landed_foundation_with_evidence_gate` | `closed; opl_default_owner_target_proof_present` | workspace/source intake shell、Portal/workbench shell、domain route scan/dispatch、generic CLI/MCP/product wrappers、scheduler lifecycle、queue/attempt/retry/dead-letter 和 generic transition runner 的长期 owner 已迁到 OPL generated/hosted surface 或 MAS domain handler target；MAS 只保留 domain handler、AI-first validator、owner receipt signer 和 body-free projection refs。 | generated surface parity、OPL default-owner target proof、stale-surface scan、旧 wrapper/alias/facade tombstone/provenance 与 focused tests 继续作为 drift guard。 |
| `domain_authority_refs_boundary` | [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) + OPL lifecycle/index/artifact docs | `landed_foundation_with_evidence_gate` | `closed; domain_authority_refs_active` | `domain_authority_refs_index`、paper outbox、storage maintenance、publication-route memory locator 和 artifact lifecycle audit 只允许 body-free refs / locator / receipt / blocker exporter；通用 lifecycle/index/workbench/artifact/terminal transport 逻辑归 OPL primitive。 | refs payload 不含 body / verdict / artifact blob；OPL primitive 消费 refs 后仍不能写 MAS truth；focused tests 覆盖 no body, no authority, no archive-import diagnostic owner。 |
| `standard_skeleton_physicalization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) + [Standard Domain Agent Skeleton](../runtime/contracts/standard_domain_agent_skeleton.md) | `functional_follow_through_gate` | `functional_projection_landed; repo_source_anchors_landed` | 新增 repo-source surface 默认按 standard slots 落位；破坏性目录迁移只在 parity/provenance/no-forbidden-write proof 后做。 | `mas_functional_closure_status_projection` 聚合 standard skeleton repo-source anchors；skeleton audit 能解释标准 slot 与现有路径；workspace artifacts、memory body、receipt instances 仍 locator-only。 |
| `p3_foundation_guard` | [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md) + [Domain Authority Refs Index Guard](./runtime_lifecycle_sqlite_migration_program.md) | `landed_foundation` | `landed_foundation; maintenance_only_no_default_mds_dependency` | 只处理新 drift、restore diagnostic、explicit archive import、MDS provenance / upstream intake 分类。 | `mas_functional_closure_status_projection` 将该线固定为 maintenance-only；验证口径是不新增默认 MDS dependency、不恢复 Git lifecycle、不制造第二套 study/runtime truth。 |

当前 `domain_transition_table_hardening` 已经从“完成态消费”扩展到多类 owner receipt 消费：package closure、execution receipt、artifact-delta owner apply、stable blocker、route decision、AI reviewer publication eval、human-gate resume、stop-loss、publication-route memory writeback 和 fail-closed receipt isolation 都应进入同一 MAS-owned transition context。memory writeback receipt 只进入 refs/counts/blocker 的 inspect handoff，不携带 memory body、不授权 quality/submission、不允许 generic runner resume；仍未闭合的是更多真实 paper-line memory receipt scaleout、更多 package closure 变体和真实 provider-hosted paper-line owner-chain receipt。单次 repo-level matrix evidence 归 [Plan Completion Ledger](../history/program/plan_completion_ledger.md) 和 history/provenance。

规划完成的含义是：每条 MAS 内容线都有唯一入口、owner doc、gate class、下一实施单元和验收证据。它不表示真实 paper live apply、真实 memory writeback、App UI drilldown 或 legacy 物理删除已经完成；这些继续按上表的 gate 推进。

## OPL Production Functional Closure 对齐

OPL 层面的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`；当前 production/framework closure owner 是 `/Users/gaofeng/workspace/one-person-lab/docs/active/production-framework-closure-gap-matrix.md`。2026-05-14 一次性 functional closure 计划只作为 OPL history provenance 保留在 `/Users/gaofeng/workspace/one-person-lab/docs/history/process/plans/2026-05-14-production-functional-closure-plan.md`。MAS 这里不再维护一份平行的 production/framework closure 大计划；MAS 的下一批可立即工程落地工作应作为 OPL 当前 closure matrix 下的 MAS implementation lane 并行推进。

这意味着：

- OPL plan 持有跨仓总目标、吸收顺序、provider/operator/workbench/cross-repo gate；
- MAS 文档只持有 MAS-owned domain receipt、memory、stage review、skeleton、legacy cleanup 和 sidecar/product-entry projection；
- stage surface standardization 是 MAS implementation lane 的基础依赖之一，不是 production functional closure 的总目标；
- 真实 paper-line provider-hosted live apply 仍是 production evidence gate，不阻塞下面这些功能性闭环先落地。

| OPL umbrella lane | MAS 对应 implementation lane | MAS owner surface | MAS done signal |
| --- | --- | --- | --- |
| `owner-receipt-contract-generalization` | `mas_owner_receipt_envelope` | sidecar dispatch receipt、guarded apply receipt、stage closeout、human gate、stop-loss、paper progress owner receipt | paper guarded apply、stage closeout、memory writeback、human gate 和 stop-loss 都能投影成同构 MAS owner receipt 或 typed blocker refs；OPL 只保存 refs。 |
| `domain-memory-apply-generalization` | `publication_route_memory_receipt_generalization` | stage knowledge plane、publication-route memory pack、writeback proposal/router receipt、body-free inventory | consumed/proposal/accepted/rejected/writeback refs 扩展到更多 fixture / workspace proof；OPL/Aion 只读展示 locator、freshness、receipt refs，不持有 memory body。 |
| `authority-guarded-apply-generalization` | `mas_artifact_authority_receipt_requirement` | domain authority refs locator、artifact locator、restore/retention receipt boundary | OPL-owned metadata 可被 locator/projection 消费；任何 domain artifact 删除、重写或 package mutation 都必须返回 MAS domain receipt requirement 或 typed blocker。 |
| `physical-skeleton-follow-through` | `mas_standard_skeleton_followthrough` | `standard_domain_agent_skeleton`、agent/stage/skill/knowledge/quality/sidecar/projection locator | repo-source physical anchors 已落到 `agent/`、`contracts/runtime/`、`runtime/artifact_locator/` 和 `docs/runtime/contracts/`；新增 repo-source surface 默认映射到标准 slot，现有路径只作为当前 repo mapping 或 locator/provenance。 |
| `legacy-active-path-final-retirement` | `mas_legacy_residue_no_resurrection_proof` | P2 classification、MDS/Hermes/local scheduler provenance、cleanup tests | stale scan + no-resurrection proof + replacement proof；legacy active-path tombstone contract 与 history tombstone 已落地，可删接口按 stale-surface / 无 fixture 依赖直接删除。旧 workspace-local service wrapper 已归入这一类：它们不是 public retained surface，init 只负责移除旧生成物。 |
| `operator-workbench-drilldown` | `mas_workbench_projection_completion` | `mas_opl_runtime_workbench_projection`、Progress Portal stage review、provider readiness refs、route-memory refs、safe action receipts | provider readiness、stage review/index、memory refs、safe action receipt、typed blocker 在同一 App-consumable read model 中分 lane 展示，且不写 MAS truth。 |
| `cross-repo-production-closeout-gate` | `mas_functional_closure_status_projection` | product-entry manifest、sidecar export、focused verification report | MAS 可以给 OPL closeout gate 提供当前 descriptor alignment、provider proof ingestion、memory receipt coverage、stage review proof、legacy residue state 和 typed blockers。 |

当前执行优先级应是 framework-first：

1. 先把 OPL 做成完整的 stage-led、以 Agent executor 为最小执行单位的智能体框架，具备 durable stage attempt、queue/wakeup、retry/dead-letter、approval/human gate、receipt/projection、shared lifecycle/index primitive 和 provider-backed runtime。
2. 再把 MAS 迁移到这个框架：MAS 暴露 domain-agent skeleton、stage descriptor、sidecar export/dispatch、owner receipt、artifact locator、projection builder 和 authority refs；OPL/Temporal 承载任务启动后的框架运行外围、持久调度、唤醒、retry 与 resume。
3. 同步把新旧功能逐块分类、迁移、分层或沉淀：domain truth 留在 MAS，framework-generic lifecycle/index/restore/retention 能力上收到 OPL，旧 local active path 只保留 tombstone/provenance，证据面按 refs-only 投影。
4. 同步推进 stage surface 形式统一：主 stage card、生成人读 facade、缺失 knowledge / closeout obligations、stage-selectable quality packs、OPL descriptor locator 和 `baseline` / `experiment` / `analysis-campaign` / `review` 独立 stage skill surface 已落地；既有 skill 已消费 stage surface、quality pack 与 Research Harness clean-room gates。剩余重点是用真实 provider-hosted live apply 证明目标形态。横向 owner 见 [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md)。
5. 过时模块、Hermes/MDS/default path、旧 manager wording、重复 UI 入口和旧兼容别名在替代证据存在后直接退役清理；这属于迁移收口条件，不应无限期后置。
6. 最后再做真实 E2E / paper-line soak / App workbench 验收，证明新框架下 MAS paper autonomy 能产生 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 typed blocker。

这里的“最后再测试”指真实运行验收和 paper soak，不表示代码级验证后置。每个迁移步骤仍必须跑对应 focused tests、contract checks 和 repo-native verification。

## 内容线路

| 顺序 | 线路 | owner 文档 | 当前状态 | 当前实际要做 |
| --- | --- | --- | --- | --- |
| `1` | `opl_framework_foundation` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) + OPL master docs | `provider_residency_projected_domain_activity_soak_pending` | OPL 已具备 stage attempt、attempt start/query/signal、typed closeout ledger、Codex runner harness、Temporal production residency proof 和 provider-backed family-runtime read model；MAS manifest / sidecar 已暴露 `provider_runtime_residency_read_model` 与 `managed_temporal_state_consistency`，有 OPL proof 时切到 available/consistent。下一步是真实 domain activity 长时 soak 和 provider-hosted paper apply。 |
| `2` | `mas_framework_migration` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `owner_receipt_envelope_landed_live_apply_chain_pending` | MAS 迁移为 OPL-admitted domain agent：sidecar/receipt contract、stage descriptor、domain skeleton、artifact locator、authority refs、direct path / hosted path receipt equivalence；product-entry manifest 与 sidecar export 已消费 OPL production proof 并把 provider read model 切到 available，同时保持 OPL 不能写 MAS memory body、router acceptance、domain truth 或 publication authority。下一步是真实 live apply owner receipt chain。 |
| `2a` | `publication_route_memory_management` | [Publication Route Memory Policy](../policies/study-workflow/publication_route_memory_policy.md), [Study Workflow](../policies/study-workflow/README.md) | `body_free_descriptor_landed_receipt_scaleout_pending` | 继续把可复用论文路线经验写成富文本自然语言 memory card：维护 workspace `publication_route_memory/memory_pack.json`、migration/writeback receipts、MAS `publication-route-memory-inventory` body-free 默认导出、OPL/Aion ref-only projection、operator grouping 和 stale/deprecated review summary。现在可以继续落地的是更多真实论文线 accepted/rejected receipt、跨 workspace inventory smoke、maintainer-level review discipline 和 App/workbench polish；暂缓 recipe engine、自动 winning-route scorer、OPL-owned memory body 和未审计的普通用户编辑器。 |
| `3` | `feature_partition_and_retirement` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md), [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md), [Domain Authority Refs Index Guard](./runtime_lifecycle_sqlite_migration_program.md) | `no_resurrection_cleanup_policy_satisfied; direct_cleanup_default` | 新旧功能逐块分类为 retain/move/lift/degrade/retire；旧 active-path wording 已有 tombstone contract 和 no-resurrection proof。后续遇到 stale surface / 无 fixture 依赖 / 有 replacement proof 的接口、wrapper、测试或文档入口，直接物理删除或让初始化清理旧生成物，不再新增兼容别名。 |
| `4` | `stage_surface_standardization` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | `stage_surfaces_landed_live_apply_followthrough_pending` | 已落地 generated stage cards、缺失 knowledge/closeout obligations、stage quality pack contract、product-entry / family descriptor locator、独立 stage skill surface、既有 skill 的 stage surface / quality pack / RH clean-room gate 消费、provider residency read model、guarded apply harness、Stage Review / Index workspace locator proof、body-free memory receipt inventory、workbench reference projection、standard skeleton physical anchors、workspace/runtime evidence receipt 和 legacy active-path tombstones。下一步是真实 provider-hosted live paper apply、更多真实 review/index instance 和更多真实 memory receipts。 |
| `4a` | `ai_first_quality_gate_alignment` | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) + [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) | `required; authority_wording_split_pending` | 把 verdict 从脚本函数口径拆成 OPL standard stage quality gate：AI reviewer / quality pack / evidence refs 产出 judgment，MAS validator / receipt / guard 持久化和防越权。 |
| `5` | `app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `mas_reference_projection_available_opl_app_drilldown_pending` | OPL App / Workbench 继续产品化 MAS 状态、route、conversation、terminal/log、artifact、safe action receipt 和 typed blocker drilldown；MAS 只提供 read-only projection，不重新定义 runtime truth。 |
| `6` | `paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `guarded_apply_surface_landed_live_provider_apply_pending` | 在 OPL framework + migrated MAS 形态下做真实 paper-line soak；当前 guarded apply proof 已覆盖多条真实 paper-line typed closeout、memory/writeback/receipt refs、MAS owner receipt gate 和 fail-closed forbidden-write guard。下一步仍是 live provider-hosted guarded apply 下的 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。 |
| `7` | `recurring_learning_support` | `docs/status.md`, `docs/references/**` | `triggered_support` | DeepScientist / external harness / adjacent framework intake 只在触发时执行，dated snapshot 留在 history。 |

## 已过时或已降级内容

| 内容 | 当前处置 |
| --- | --- |
| “P0 等于 MAS-only runtime 完成” | 已过时。P0 是目标和验收，产品/框架依托分别在 P1/P2。 |
| “整份 P1 workbench 计划都要做完” | 已替换为 P1 内容 lane：read-only workbench、action receipt、provider join；terminal/log/provider drilldown 归 OPL current_control_state。 |
| “整份 P2 Temporal retirement 计划都要做完” | 已替换为 framework-first 的 P2 内容 lane：OPL framework foundation、MAS framework migration、framework-generic lift、legacy retirement、再进入 paper-line soak。 |
| Hermes-first 或 MAS local scheduler 作为 Full online target | 已退役。OPL Full online target 是 Temporal-backed production runtime；MAS local scheduler 只保留 tombstone/provenance refs；`hermes_agent` 只保留为显式非默认 executor/proof lane。 |
| 旧 MDS daemon/WebUI/runtime transport 作为默认依赖 | 默认路径已退役；只保留 provenance、explicit archive import、backend audit、upstream learning 或 parity reference。 |
| Runtime lifecycle Git-era cleanup 作为活跃大迁移 | 已落地。新发现问题按 P3a drift/maintenance 处理，除非证明有 live writer regression。 |
| Local Portal / Live Console 作为最终主产品面 | OPL App workbench 成为主用户面后，local Portal / Live Console 降级为 diagnostic/debug/evidence。 |
| 依赖 Markdown wording 的测试或脚本 | 方向无效。机器接口应使用 schema、JSON、CLI/API payload、manifest 或 durable semantic ID。 |
| Workspace-local `install/watch/uninstall-watch-runtime-service` wrapper | 已退役。新 workspace 不生成，旧 workspace 重跑 `init-workspace` 时删除旧生成物；scheduler 生命周期只走 canonical runtime CLI。 |

## 合并与吸收规则

编辑旧 program 内容时按下表归位：

| 内容类型 | 归属 |
| --- | --- |
| 论文质量、reviewer repair、route decision、stage knowledge/memory、live-soak acceptance | P0 |
| App-native 状态、路线视图、conversation timeline、terminal/log panel、安全 action UI | P1 |
| OPL provider、Temporal attempt、queue、retry/dead-letter、approval transport、sidecar receipt、provider projection | P2 或 OPL master docs |
| MDS provenance、explicit archive import、no-history source intake、behavior parity oracle | P3 或 `docs/references/mds-parity/` / `docs/references/med-deepscientist/` |
| domain authority refs、retired-runtime SQLite/file boundary、Git retirement drift、restore proof | P3a |
| 可服务多个 domain 的 lifecycle/index/restore/retention primitive | 先进入 P2 的 `lift_to_opl_framework`，再进入 OPL framework docs |
| stage prompt、skill、knowledge packet、closeout memory、quality pack、stage descriptor、OPL projection boundary | 先进入 `stage_surface_standardization_program.md` 做形式归一，再落到 P0/P2/P1 对应 owner surface |
| dated evidence、旧 phase table、旧 activation package、superseded checklist | `docs/history/program/` |
| recurring external learning trigger 和 absorption rule | `docs/status.md` 或 `docs/references/**`，单次执行快照进入 history |

## 优先级规则

1. Framework-first：OPL 完整智能体框架是 MAS 迁移和真实 paper soak 的前置条件。
2. 迁移优先于测试：真实 E2E / paper soak 应验证迁移后的目标形态，不应验证一个即将退役的 MAS-local 运行外围。
3. 退役清理属于迁移收口：旧默认依赖、legacy aliases、重复 UI、过时 manager surface 不应无限期留作“以后再说”；替代证据、无默认调用、无 fixture/provenance 必需成立后直接删除，测试同步改成验证删除和 fail-closed 行为。
4. 只上收通用 framework primitive：lifecycle、locator、retention、restore proof、attempt receipt、cache cleanup 可以进入 OPL；study truth 和 publication authority 留在 MAS。
5. 产品 workbench 跟随框架迁移：OPL App 展示 OPL framework + MAS owner receipts 的状态，不重新发明第二套 runtime truth。
6. 代码级验证持续执行：每个 contract、runtime、projection 或 cleanup 步骤都要跑 focused tests；最后的真实 paper soak 是目标形态验收。

## 当前完成信号与未闭合门槛

| 线路 | 完成信号 |
| --- | --- |
| `opl_framework_foundation` | 已完成：OPL production proof 可被 MAS manifest / sidecar ingest，`provider_runtime_residency_read_model` 与 `managed_temporal_state_consistency` 可投影；未闭合：真实 domain activity long soak、restart/re-query 后的 domain receipt 串联、human gate/resume owner chain。 |
| `mas_framework_migration` | 已完成：MAS direct skill path 与 OPL-hosted path 使用同一 MAS owner receipt envelope，`provider_completion_is_paper_closure=false` 且 OPL 不写 forbidden MAS truth surface；未闭合：真实 live apply owner receipt chain。 |
| `publication_route_memory_management` | 已完成：人类用户能从 policy/index 进入 Markdown canonical route-memory library、9 张富文本 seed cards、workspace memory pack 与 receipt/proposal locator，并能用 `medautosci publication route-memory-inventory --workspace-root <workspace>` body-free 查看 card 元数据、locator、receipt summary、operator grouping 和 stale/deprecated review summary；OPL/Aion 只显示 consumed refs、writeback receipt refs、rejected reason、freshness 和分组信息；未闭合：更多真实论文线通过 MAS router receipt 生成 accepted/rejected reusable lessons。 |
| `feature_partition_and_retirement` | 已完成：legacy active-path tombstone contract、no-resurrection proof 和 cleanup policy satisfied projection；MAS watchdog 的通用在线执行、queue/wakeup/retry/signal/query 责任已有 OPL native replacement proof，MAS `domain_health_diagnostic` 保留为 domain diagnostic、progress read-model 关联和 owner receipt projection；已进入物理删除的当前项是 workspace-local service wrapper；未闭合：继续按 audit finding 清理其他可删代码。 |
| `stage_surface_standardization` | 已完成：generated stage card、route contract、knowledge/closeout obligations、quality pack contract、OPL projection boundary、`baseline` / `experiment` / `analysis-campaign` / `review` 独立 stage skill surface、既有 skill 的 stage surface / quality pack / RH clean-room gate 消费、provider projection / typed blocker proof、OPL production proof ingestion、Stage Review / Index workspace locator proof，以及 standard skeleton repo-source anchors；未闭合：provider-hosted live apply 证明 stage closeout / memory / quality / artifact delta 沿 MAS owner surface 闭合。 |
| `app_runtime_workbench` | 已完成：MAS 可把 workbench 所需 refs、freshness、safe action receipt 和 typed blocker 汇入 read-only projection；未闭合：OPL App / Workbench drilldown 的产品化展示和真实 operator loop。 |
| `paper_autonomy_acceptance` | 已完成：Read-only evidence 已要求三篇真实论文线各有 typed closeout projection，且至少一篇带 memory consumed/writeback receipt refs；guarded apply proof surface 已要求 MAS owner receipt gate，不允许 provider 直接写 workspace truth；source-keyed MAS dispatch receipt 与 owner stable blocker 已证明 OPL rehydrate / dispatch loop 能消费 MAS owner evidence。未闭合：更多真实 paper line 反复产出 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 MAS owner surface 下的 typed blocker scaleout。 |
| `monolith_and_mds_foundation_guard` | 已完成：后续 MDS/DeepScientist 引用被分类为 provenance、explicit archive import、backend audit、upstream learning 或 parity oracle reference，不能成为默认 runtime、quality 或 artifact authority。 |
| `runtime_lifecycle_foundation_guard` | 已完成：新 runtime/Git/path drift 进入 inventory/archive/restore/verification 维护口径，并保持在默认 MAS authority 之外；未闭合：新发现 live writer regression 时按 P3a 单独处理。 |

## 距离理想态的后续切片

| slice | why now | owner doc | completion proof |
| --- | --- | --- | --- |
| `provider_residency_status_and_activity_soak` | `mas_functional_closure_status_projection` 已把 provider residency 投影为可读状态，并保留 `mas_domain_activity_long_soak_pending` typed blocker；下一风险在真实 domain activity 是否能长时运行、恢复和查询。 | P2 / OPL master docs | `family-runtime status --provider temporal` managed-state 一致性、restart/re-query、retry/dead-letter、Codex/domain activity long soak receipt、MAS sidecar receipt。 |
| `provider_guarded_apply_soak` | guarded apply harness 已覆盖 owner receipt gate、provider unavailable、duplicate/conflict、forbidden-write；task source fingerprint、MAS owner decision refs、owner contract source ref 和 source-keyed dispatch receipt 已避免同一 OPL task 复用旧 provider / owner evidence receipt；owner stable blocker loop 已有基线，`provider_hosted_live_paper_apply_pending` 仍是 production evidence gate。 | P0 + stage surface program | typed closeout、MAS owner receipt、artifact delta / gate replay / human gate / typed blocker、no-forbidden-write proof。 |
| `stage_review_index_live_provider_followthrough` | repo-level workspace locator proof 和 Portal/Workbench 只读展示已落地；还需要 live provider-hosted apply 持续产出同一类 refs。 | stage surface program + P1 | live attempt 触发 MAS owner closeout 后产生 workspace latest review page / index refs、freshness、claim impact、human annotation、next owner 或 typed blocker，Portal/Workbench 只读展示。 |
| `publication_route_memory_receipt_scaleout` | body-free receipt inventory、operator grouping 和 stale/deprecated review summary 已能投影 migration/writeback accepted/rejected refs；仍需更多真实 accepted/rejected lessons 和跨 workspace smoke。 | Study Workflow / publication route memory policy | 多 paper-line router receipts、body-free inventory、OPL/Aion ref-only 分组、review summary 和 freshness refs。 |
| `legacy_residue_retirement` | legacy active-path tombstone contract、no-resurrection proof 和 cleanup policy satisfied projection 已落地；后续只按 finding 删除或保留 reference。当前 wrapper 清理切片用于固定执行口径：新 scaffold 不再生成旧 service wrapper，旧生成物由 init 删除。 | P2 / P3 / P3a | stale scan、no-resurrection proof、replacement proof、focused cleanup tests。 |
| `standard_skeleton_physicalization` | repo-source physical anchors 已落地，真实 workspace artifact body 仍 locator-only。 | stage surface program | 新增 surface 按 skeleton slot 落位，现有路径保持明确 repo mapping 或 locator/provenance。 |

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
