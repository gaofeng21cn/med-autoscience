# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、domain-handler receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-06-03`

## 文档读法

- 本文是 MAS 当前唯一 single Active Truth plan：维护当前唯一真相、目标态、已落地状态、功能/结构差距、测试/证据差距、近期完善计划、完成门和历史索引。
- MAS 的 north-star 目标态读 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)。本文只保留面向执行的差距和顺序。
- [MAS 当前开发线路](./current-development-lines.md) 只作为内容线索引；若它与本文冲突，以本文为准，并把仍有效内容折回本文、核心 canonical docs、runtime/contracts/policies 或 history/tombstone。
- [当前状态](../status.md) 只维护 current-state 摘要；dated closeout、receipt id、OPL worklist 数字、命令流水、旧 phase checklist、same-day follow-through 和 proof 过程进入 `docs/history/**`、runtime ledger、真实 workspace receipt 或提交历史。
- 差距按目标态判断。当前实现可运行只能作为迁移输入、风险和证据来源，不能反向定义 MAS 长期架构。

## 当前唯一真相

| 主题 | 当前结论 |
| --- | --- |
| MAS 身份 | MAS 是医学研究 domain agent，也是 OPL-compatible package。direct MAS app skill path 与 OPL-hosted path 必须回到同一套 MAS-owned stage、controller、durable truth、quality verdict、artifact authority、memory decision、owner receipt 和 typed blocker。 |
| 默认运行 | Hosted autonomous runtime 默认由 OPL/Temporal 承担；OPL 持有 stage attempt、queue、wakeup、retry/dead-letter、resume、human-gate transport、provider query、worker residency 和 operator projection。`Codex CLI` 是 stage 内第一公民 executor；Codex App 只承担 direct entry / 人机操作面，不作为任务启动后的外围持续 driver。 |
| MAS authority | MAS 持有 study truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body 与 accept/reject/blocker decision、artifact/package authority、source readiness、owner receipt、safe action refs 和 typed blocker。 |
| OPL authority | OPL 持有通用 scheduler、queue、attempt ledger、generic transition runner、lifecycle/index、memory/artifact locator、restore/retention shell、observability、repair projection、generated CLI/MCP/Skill/product-entry/domain-handler/status/workbench wrapper 和 App/workbench shell。 |
| MDS / DeepScientist | 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。它不回到 MAS 默认 backend、quality owner、artifact authority 或 runtime owner。 |
| 当前机器面 | `agent/` 是 canonical medical research semantic pack；`contracts/foundry_agent_series.json`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是主要 machine-readable truth。 |
| 控制面收薄 | 稳定 execution contract 收敛为 `macro_state + owner_route + receipt_or_blocker + evidence_refs`。长 runtime/status reason、supersession reason、publication supervisor phase 和 operator/workbench 文案只做 diagnostic/read-model detail，不再成为跨入口执行授权。 |
| SQLite / State Index Kernel | MAS 是小文件 compaction 的首要 domain candidate，但长期 owner 是 OPL State Index Kernel。`contracts/stage_artifact_kernel_adoption.json#/state_index_kernel_adoption` 固定：SQLite sidecar 只存 refs、locator、cursor、checksum、source fingerprint、idempotency key、receipt/blocker/restore refs 和 bounded preview hash；study truth、publication eval、controller decisions、manuscript、package、evidence/review ledger、memory、artifact body、quality verdict 和 owner receipt authority 继续归 MAS 文件/receipt truth。 |

## 目标态

MAS 的目标态是：

`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal medical authority functions`

这表示 MAS 只长期保留医学研究语义、stage pack、quality gate、publication/artifact/memory/source authority、domain transition、owner receipt 和必要医学 helper。通用 runtime platform、queue、attempt ledger、state-machine runner、memory/artifact locator、lifecycle/restore/retention、observability、workbench 和 generated entry/status wrapper 上收到 OPL Framework / shared family layer。

AI-first quality gate 必须由独立 reviewer/auditor agent invocation 关闭。程序函数只做 schema/provenance/authority refs 校验、持久化、owner receipt 签发、typed blocker、safe action refs 和 no-forbidden-write guard；脚本、regex、scorecard、file presence、queue completion 或 executor 自审不能替代医学质量判断。

控制面目标同步收薄为 `macro_state + owner_route + receipt_or_blocker + evidence_refs`。程序只决定当前 owner、allowed action、forbidden writes、idempotency 和 receipt/blocker；开放式医学语义、写作修订、质量判断和路线判断交由 prompt、skill、executor、独立 reviewer/auditor 与 evidence refs 承接。

## 当前完成进度

| Area | 当前进度 | 当前读法 |
| --- | --- | --- |
| Standard OPL Agent source shape | `standard_agent_source_shape_landed` | `agent/` pack、stage/action/memory/artifact contracts、generated surface handoff 与 production acceptance 已成为 MAS 当前机器面；`contracts/functional_privatization_audit.json` 与 focused tests 将 `functional_structure_gap_count` 固定为 `0`。 |
| Runtime owner split | `opl_owned_default` | 默认 hosted autonomous runtime 归 OPL/Temporal；MAS 保留 study truth、quality gate、artifact authority、owner receipt 和 typed blocker。 |
| Legacy runtime no-resurrection | `guarded` | `runtime_transport`、`mas_runtime_core*`、turn runner、worker lease 和旧 lifecycle writer 只能按 tombstone/provenance 或 OPL handoff refs 读取。 |
| DM002 / DM003 anti-stall control loop | `next_owner_resolution_landed_currentness_tail_active` | `always resolve to next owner`、AI reviewer currentness consumption、owner-route/read-model/liveness 优先级、closeout ingestion、gate-clearing receipt consumption 和 stale provider-attempt invalidation 已进入当前口径；当前仍必须 fresh 读取 live owner route，不用 dated follow-through 段落判断论文是否在跑。 |
| Domain owner evidence shape | `shape_landed_live_scaleout_pending` | guarded apply、owner-route、body-free evidence packet、typed blocker shape、paper-line owner-chain result、domain-dispatch payload 和 OPL refs-only return shapes 已可消费；这些仍只是 refs/receipt/projection shape，不声明 paper closure、publication-ready、artifact mutation authorization、memory accept/reject 结论或 `current_package` 更新。 |
| Research evidence pack read-model / schema / canary | `read_model_schema_canary_evidence_landed_not_publication_ready` | read-model、schema validation、Progress Portal / runtime workbench stage review projection 和 canary expectation 已同口径 fail closed；它们只关闭最低科研审计链的可读 / 可校验 / fail-closed 证据。 |
| Docs lifecycle | `single_active_truth_owner_reconfirmed_2026_06_03` | 本文持有 current gap / completion plan；`docs/status.md` 持有 current-state summary；`docs/docs_portfolio_consolidation.md` 持有 docs lifecycle rules；dated closeout 与命令流水归 history/provenance。 |

## 已落地

| Area | 当前状态 | 当前证据入口 | 当前读法 |
| --- | --- | --- | --- |
| MAS semantic pack / generated handoff | `landed_with_evidence_tail` | `agent/`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、product-entry stage descriptor | `agent/` 是 canonical semantic pack；真实 stage attempt 与独立 reviewer/auditor receipt 仍属 evidence tail。 |
| Functional privatization boundary | `closed_functional_structure_gates_evidence_tail_remaining` | `contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`tests/test_opl_standard_pack.py`、`tests/test_opl_family_contract_adoption.py` | `classification_gap_count=0`、`functional_structure_gap_count=0`、`active_private_generic_residue_count=0`、`repo_local_wrapper_tail_count=0`；former wrapper 物理删除仍需 owner receipt / stable typed blocker、no-active-caller 与 tombstone/provenance gate。 |
| Purpose-first adapter thinning | `machine_guard_landed_evidence_tail_remaining` | `contracts/foundry_agent_series.json#/purpose_first_adapter_thinning_policy`、`tests/test_opl_standard_pack.py` | retained product/workbench/status/read-model surface 只能作为 refs-only adapter、domain handler target、minimal authority function、migration input 或 tombstone/provenance 读取；物理删除统一要求 replacement parity、no-active-caller、owner receipt / typed blocker、no-forbidden-write 与 tombstone/provenance。 |
| Default runtime owner | `opl_owned_default` | runtime default/backend contract、product-entry manifest、domain-handler export/read-model | 默认 runtime ref / substrate 是 `opl_hosted_stage_runtime`，默认 backend 是 `opl_provider_backed_stage_runtime`；历史 `mas_runtime_core` 只能按 retired provenance / migration input 读取。 |
| Runtime / lifecycle no-alias retirement | `retired_no_alias_guarded` | `contracts/runtime/legacy-active-path-tombstones.json`、`contracts/runtime/mas-runtime-surface-retirement-inventory.json`、functional boundary audit | `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、旧 lifecycle refs SQLite writer 只能作为 tombstone/provenance、OPL handoff refs 或 standard Agent purity guard 读取。 |
| Owner-route / dispatch currentness | `active_current_truth` | `docs/decisions.md`、owner-route protocol contracts、domain-handler export/dispatch behavior | `mas-owner-route-attempt-protocol.v1` 要求 reason registry、priority lattice、currentness basis、source/work-unit/truth/runtime fingerprint 和 typed closeout boundary；它只授权 OPL transport，不授权 paper closure 或 package freshness。 |
| Progress-first admission and accounting | `landed_with_live_evidence_tail` | [Progress-first Stage Outcome Runbook](../runtime/control/progress_first_stage_outcome.md)、`study_progress`、`study-state-matrix`、Progress Portal、MCP compact | 非终局 study 必须投影到唯一 owner action、owner receipt、typed blocker、human gate 或 stop-loss；platform repair 不计 paper/deliverable progress。 |
| Research evidence pack projection | `landed_not_publication_ready` | schema validation、read-model projection、Progress Portal / runtime workbench stage review、canary expectation | 只证明最低科研审计链可读、可校验、可 fail closed；真实 publication-ready 仍需 MAS owner receipt、独立 reviewer/auditor record、publication gate / human gate 和 artifact/memory/lifecycle authority receipt。 |

## 当前功能/结构差距

当前没有 open functional / structural gap。`contracts/functional_privatization_audit.json` 的 `functional_followthrough_gap_summary` 和 focused tests 固定：

| Metric | 当前值 |
| --- | --- |
| `classification_gap_count` | `0` |
| `functional_structure_gap_count` | `0` |
| `remaining_functional_followthrough_gate_ids` | `[]` |
| `active_private_generic_residue_count` | `0` |
| `repo_local_wrapper_tail_count` | `0` |

下表只保留仍约束后续工作的 closed gate / guard；它们不能被重写成 active backlog，也不能被 OPL transport evidence 升级为 MAS paper closure。

新增或保留 MAS-local adapter 时，默认下一步必须是 `paper_progress_delta_or_mas_owned_typed_blocker`。platform repair、read-model currentness、provider completion、schema/descriptor conformance 和 generated surface readiness 只能作为证据尾项或 refs-only 投影；缺真实 paper / research / reviewer / human-gate delta 时返回 MAS-owned typed blocker，不写成结构 gap 已关闭或 paper progress。

| Gate / guard | 当前实际 | 后续约束 |
| --- | --- | --- |
| `generated_surface_default_owner_cutover` | OPL owns generated/default CLI/MCP/Skill/product-entry/status/workbench/domain-handler shells；MAS provides pack inputs、domain handler targets、authority refs、owner receipts、typed blockers 和 no-forbidden-write guard。 | 不把 MAS direct path、domain handler target 或 read-model projection 写回 MAS-owned generic wrapper。 |
| `standard_agent_purity_guard` | MAS repo source shape 已按 standard Agent purity 收口；former wrapper tail module ids 只作为 guarded provenance / delete-gate context 存在。 | 只有在 OPL generated/default parity、MAS owner receipt 或 stable typed blocker、no-active-caller proof 与 tombstone/provenance proof 同时成立时，才做物理删除；不新增 compatibility shim、alias、facade 或 wrapper。 |
| `domain_authority_refs_thinning` | storage、artifact、memory、source、owner-route、progress/status helper 只输出 refs、receipts、blockers、locators 或 diagnostic projection input。 | generic locator/index/projection shell 属于 OPL primitive；MAS retained path 只能是 domain authority refs、typed blocker、owner receipt 或必要医学 helper。 |
| `state_index_kernel_adoption` | OPL 持有 SQLite sidecar / state index / read-model kernel；MAS 只作为 primary small-file compaction candidate 和 refs-only index source。 | legacy `.ds`/runtime mirror、runtime lifecycle refs、paper work-unit receipts、owner-route/dispatch receipts、artifact locator、retention/restore 和 operator read-model 可进入 OPL sidecar index；`domain_authority_refs.sqlite` 只能是 domain authority refs adapter，不能写成 MAS generic persistence/lifecycle/queue/read-model owner。 |
| `state_contract_thinning_guard` | 稳定控制面只承认 `macro_state`、`owner_route`、`receipt_or_blocker` 和 `evidence_refs`；长 reason 和 supersession reason 只能作为 diagnostic detail。 | 新增执行判断必须进入 owner route 或 typed blocker，不得通过扩展 `StudyRuntimeReason`、publication supervisor phase 或 operator 文案绕开 owner ticket。 |
| `physical_source_morphology_guard` | legacy 名称只允许出现在 tombstone、history/provenance、旧状态输入测试、explicit archive/import fixture 或 standard Agent purity guard。 | current docs/tests/callers 不得把旧名读成 active runtime adapter、diagnostic fallback 或 compatibility alias；发现 generic queue、attempt ledger、scheduler、worker residency、runtime lifecycle owner 语义时按复活旧控制面处理。 |
| `ai_first_quality_record_boundary` | quality gate contract 和 validator 边界已落地；真实 paper-line reviewer/auditor record scaleout 属于证据 tail。 | 程序只做 validator、materializer、receipt signer 和 guard；质量结论必须追到独立 reviewer/auditor invocation、context/task record、quality receipt、route-back 或 typed blocker。 |

## 当前测试/证据差距

以下差距是 production evidence tail。它们不改变上面的结构口径，也不能声明 publication-ready、domain-ready、artifact mutation authorization 或 `current_package` 更新。

| 证据差距 | 当前状态 | 需要看到的下一层证据 |
| --- | --- | --- |
| 真实 paper-line provider apply | multi-profile guarded-apply、DM002 canary、research evidence pack read-model/schema/canary 已证明 refs-only owner-chain shape、stable blocker 和 fail-closed 审计链可见。 | 更多真实 paper line 产出 owner receipt、paper/artifact delta、independent reviewer/auditor record、human gate/resume、route decision、stop-loss、artifact/memory lifecycle receipt 或 stable typed blocker。 |
| owner-chain dispatch ledger scaleout | `domain_dispatch_evidence_record_payload` 与 OPL refs-only identity preflight / record / verify 已覆盖 success refs path 和 typed-blocker path。 | Fresh OPL worklist 重新暴露且能绑定 MAS current owner delta 的 workorder，先取得 MAS owner receipt、stage receipt、monitor freshness receipt、current AI reviewer supersession、human-gate receipt 或 stable blocker，再经新的或 superseding OPL identity preflight record/verify。 |
| publication-route memory receipts | Router/writeback refs 已进入 body-free evidence packets、paper-line result、domain-dispatch payload 和 stage expected refs。 | 多条真实 paper line 持续产生 accepted/rejected/blocked writeback receipts，并由 owner route 明确 memory accept/reject/blocker 结论。 |
| artifact lifecycle receipts | Artifact lifecycle report / retention plan 已输出 bounded refs、physical-thinning handoff 和 stable typed blocker refs-only shape。 | OPL apply receipt、真实 cleanup/restore/freshness apply receipt 或 MAS artifact mutation permission；不能由 report/plan 直接授权 cleanup 或 artifact mutation。 |
| human gate / resume | Stage replay human-gate refs 已有 MAS-owned body-free typed blocker path，`finalize_and_publication_handoff` 有 refs-only success path。 | Human approval、resume chain receipt、新 owner success receipt 或 paper closure。 |
| provider SLO long soak | Provider/runtime read-model 能投影 live attempt、blocked closeout 和 admission/running distinction。 | 长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。 |
| family transition live receipt | `study_state_matrix` 可把 MAS-owned domain transition table materialize 给 OPL generic matrix runner。 | Route/work-unit 进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。 |
| independent reviewer/auditor record scaleout | AI-first quality gate boundary 和 record validator 已落地。 | 真实 paper-line reviewer/auditor invocation、独立 context/task record、quality receipt、route-back 或 typed blocker，不得由 executor 自审替代。 |

## 近期完善计划

1. 优先扩面真实 paper-line owner delta：至少一条线产出 paper/manuscript delta、artifact/package delta、independent reviewer/auditor record、publication-route memory receipt、artifact lifecycle receipt、human gate/resume receipt、provider long-soak owner evidence、family transition live receipt 或 stable typed blocker。
2. 对 read-model/currentness/dispatcher/lifecycle apply 类问题，先判断是否只是 platform repair；没有同步产生 domain delta 或 stable typed blocker时，只能记录为 platform repair，并把下一 owner 指回 MAS paper/artifact/reviewer/human gate 或 OPL generic lifecycle apply。
3. 对 owner-chain dispatch ledger，只处理 fresh OPL worklist 中可绑定 MAS current owner delta 的 workorder；已 verified 的 OPL typed-blocker receipt 不能事后升级为 success receipt，已 verified success refs receipt 也不能写成 domain-ready 或 production-ready。
4. 对 publication-route memory receipt，优先取得真实 accepted/rejected/blocked writeback receipt 或 stable typed blocker，并证明 receipt refs 经 owner result、domain-dispatch payload、stage expected refs 与 body-free packet role 可复验，且不读取 memory body、不越过 publication verdict。
5. 对 artifact lifecycle receipt，优先从 stable typed blocker refs scaleout 前进到 owner-authorized physical thinning、真实 workspace cleanup/restore/retention/rebuild/freshness apply receipt 或 artifact mutation permission，并证明 refs 进入 reproducibility / stage expected / domain-dispatch payload，且不越过 artifact authority。
6. 对文档治理，active/core 文档只保留 current conclusion、open gate、owner、machine boundary 和下一步；过程 proof、receipt id、命令流水和 dated worklist 数字继续归 history/provenance。

## Stage-Native Kernel 完成后的下一层 TODO

本节只在 OPL Stage-Native Artifact Kernel 已完成后作为下一轮 active backlog 读取。完成条件包括：OPL 持有统一 stage folder contract，`stage.json`、`attempt.json`、`manifest.json`、`receipt.json`、`current.json` schema 已落地；`stage_artifact_index` 已降级为 derived projection；MAS/MAG/OMA/RCA 只提供 declarative domain pack 和最小 authority functions；controller/read-model/currentness 只做 repair、projection 和 diagnostic，不再决定 current stage。

2026-06-03 follow-through：MAS 当前已消费 OPL physical Stage Folder Kernel，并把 `stage_kernel_projection` 作为 Progress Portal / Workbench primary progress 的派生输入。当前完成口径提升为：physical stage folder 只有在 `current.json` 指向 latest attempt、manifest / owner receipt / domain decision receipt 成立、consumability gate 通过、lineage events / graph 可定位、retention / restore refs 覆盖时，才可被投影为 current artifact progress。`stage_artifact_index` 继续是 rebuildable diagnostic projection；缺 semantic receipt、stale current pointer、缺 retention / restore 或缺 lineage 时必须 fail closed，并产生下一 owner / blocker，而不是退回 controller/read-model currentness。

完成上述重构后，剩余风险不再是 controller/read-model 阻塞 MAS 推进，而是 Stage Kernel 自身是否能长期承担 artifact operating layer。下一轮 TODO 按以下顺序处理：

1. `manifest_receipt_semantic_validation`：证明 manifest / receipt 不只格式正确，还能绑定 domain-specific semantic validation。MAS 侧至少覆盖医学 reviewer verdict、source readiness、publication gate receipt、artifact mutation authority 和 typed blocker receipt；格式合法但语义缺失时必须 fail closed 或 route back。
2. `current_pointer_promotion_model`：把 current pointer 写成显式 promotion protocol：`attempt output -> manifest valid -> receipt accepted -> current pointer promoted -> projection rebuilt`。并覆盖并发 attempt、partial commit、rollback、stale pointer、orphan output 和 historical pointer tombstone。
3. `legacy_stage_taxonomy_migration`：为旧 MAS `scout/idea/baseline/experiment/analysis-campaign/write/review/finalize` 到 paper/study artifact stages 的映射生成 migration manifest、legacy mapping、tombstone receipt 和 backfilled current pointer。迁移期间 Workbench 不得同时显示两套 current truth。
4. `lineage_graph_unification`：把 stage folder、owner receipt、controller repair projection、provider attempt、artifact manifest、quality receipt 和 human gate receipt 统一成 lineage event；不得让 UI、controller 或 read-model 各自发明 provenance。
5. `artifact_consumability_gate`：物理文件和 content hash 只证明 artifact 存在且未变；能否进入下一 owner 还必须检查 input role、source/current truth、receipt authority、lineage、retention/restore policy 和 domain validation。
6. `workbench_information_hierarchy`：OPL App 第一屏只呈现 current stage、artifact roles、missing outputs、accepted receipts、blocker、next owner 和 provider liveness；repair/currentness/telemetry/evidence-tail 只能作为 secondary diagnostics，不能被 UI 写成 progress 或 readiness。
7. `retention_restore_gc_protocol`：Stage Kernel 成为第一事实层后，GC、归档、restore、artifact store、去重和离线 retention 必须受 manifest / receipt / current pointer 约束。禁止出现 manifest 指向已清理文件、receipt 指向不可恢复 artifact 或 current pointer 指向 orphan output。
8. `cross_domain_soak`：用 MAS、MAG、OMA、RCA 至少各一条真实 domain lane 证明同一 Stage Kernel 能承载不同 authority function、artifact role、human gate、export/readiness 语义。通过条件是每条 lane 都能从 stage folder 重建 DB、App/workbench、artifact gallery、stage_progress_log 和 next owner，而不引入 domain-specific controller 复活。

下一层完成口径：OPL 成为 artifact operating layer；Stage Kernel 负责事实重建，Domain Authority 负责裁决，Policy Engine 负责权限，Workbench 只读展示派生视图。任何 index、controller、read-model 或 App surface 重新获得第一真相权，都按架构回归处理。

## 验证与完成门

Docs-only 维护：

- `rtk git diff --check`
- `rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs README.md README.zh-CN.md`
- 必要的 docs/path inventory 检查。

触及 source/contracts/runtime 时才追加：

- `rtk scripts/verify.sh`
- 按触及面追加 focused `scripts/run-pytest-clean.sh ...`、`make test-meta` 或对应 owner-route / domain-handler / product-entry smoke。
- 消费 OPL refs 时追加 OPL 侧 read-model check：`rtk opl agents interfaces --repo-dir /Users/gaofeng/workspace/med-autoscience --json`、`rtk opl framework readiness --family-defaults --json`、`rtk opl runtime app-operator-drilldown --json`。

Completion gate:

- 本轮输出能归类为 domain delta / stable typed blocker / platform repair；platform repair 没有被写成 paper-line progress 或 production evidence tail closure。
- 仍 open 的真实 paper-line、memory/artifact/lifecycle、human gate/resume、provider SLO long-soak 和独立 reviewer/auditor record 留在“当前测试/证据差距”。
- 新增或修改的 owner receipt / typed blocker / evidence packet 有 live refs、focused verification 和 no-forbidden-write proof；OPL transport/read-model 证据没有被升级为 MAS domain verdict。
- worktree lane 已吸收回 `main` 或明确标记为近期写入/有未提交改动而保留；最终在 `main` checkout 完成最小充分验证。

## 历史索引

| 需要追溯的内容 | 当前入口 |
| --- | --- |
| 当前状态摘要 | [当前状态](../status.md) |
| 架构与 owner 边界 | [架构概览](../architecture.md) |
| 不可变约束 | [不可变约束](../invariants.md) |
| 日期决策日志 | [关键决策记录](../decisions.md) |
| north-star 目标态 | [MAS 理想目标态](../references/positioning/mas_ideal_state.md) |
| 当前内容线索引 | [MAS 当前开发线路](./current-development-lines.md) |
| 文档生命周期治理 | [MAS 文档组合治理](../docs_portfolio_consolidation.md) |
| 本轮 docs lifecycle closeout | [Docs lifecycle governance closeout 2026-06-03](../history/program/docs_lifecycle_governance_closeout_2026_06_03.md) |
| 2026-05 标准 Agent 文档过程归档 | [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md) |
| 历史完成台账 | [Plan Completion Ledger](../history/program/plan_completion_ledger.md) |

## Active / History Foldback

| 内容 | Foldback target | 规则 |
| --- | --- | --- |
| dated closeout、attempt / receipt id、命令流水、旧 phase checklist、OPL worklist 数字 | `docs/history/program/` 或对应 `docs/history/<area>/` | 只保留 provenance；不得作为 current truth 或 active backlog。 |
| 已被 current owner surface 替代的旧 runtime/workbench/scheduler/alias 文案 | `docs/history/**` tombstone / provenance，或 machine-readable tombstone refs | active docs 只写当前 owner、删除门和 standard Agent purity guard。 |
| 已关闭功能/结构 gap | 本文 `已落地`，必要时加 compact tombstone pointer | 不保留旧 checklist chronology。 |
| 仍缺 live evidence 的能力 | 本文 `当前测试/证据差距` | 不回写成结构未完成，也不写成 production/domain ready。 |

## 当前不能写成

- 不能把 OPL provider proof、suite pass、queue completion、refs-only ledger receipt 或 provider completion 写成 MAS paper closure、publication-ready、domain-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 MAS production acceptance receipt 写成具体论文线 publication-ready；它只承认 structural / physical conformance 与 production-like receipt chain 的边界。
- 不能把 `mas_owner_receipt_present`、stable blocker、body-free evidence packet 或 OPL workorder preflight 写成 workspace mutation、artifact authority 放行、memory writeback success 或 paper closure。
- 不能把 MAS 已经没有任何私有程序面写成绝对清零；准确口径是私有面已收敛为 declarative pack / generated surface handoff、domain authority refs、minimal authority function 或 explicit tombstone/provenance refs。
- 不能把旧 `runtime_transport/`、turn runner、worker lease、runtime lifecycle SQLite、`lifecycle_refs_adapter.py`、MDS/DeepScientist、Hermes、local scheduler、workspace wrapper、`mas_runtime_core`、compat alias、fallback 或只保护旧路径的聚合测试写成 MAS 默认 active runtime owner、active adapter、diagnostic fallback、compat alias 或 retained caller。
- 不能把 product-entry / workbench / owner-route / progress projection shell 写成长期 MAS generic workbench、queue、attempt ledger、retry/dead-letter、worker residency、terminal transport 或 lifecycle owner；它们当前只能输出 domain projection refs、owner receipt、typed blocker、authority refs 或 diagnostic refs。
- 不能把 `study_state_matrix` 或 OPL `family-transition-runner` matrix pass 写成 paper closure、publication quality、artifact authority、submission readiness 或 domain ready。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可由 repo tests、descriptor ready 或 conformance 替代。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出。
- 不能把 executor agent 自审、同一上下文内的执行后复核、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 dated specs、dated closeout、follow-through 记录、receipt id、OPL worklist 数字或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
