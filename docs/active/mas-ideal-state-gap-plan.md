# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `ideal_state_gap_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-19`

## 文档读法

- 本文只维护 MAS 当前定位、当前边界、当前差距分类和完善顺序；dated 过程证据、阶段 follow-through 和 closeout 记录归档到 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)。
- MAS 的 north-star 目标态回到 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)。本文不重复目标态长叙述，也不维护 OPL、MAG、RCA、MDS/DeepScientist 或 OPL App 的执行计划。
- 差距按目标态判断，不按当前 MAS 代码是否仍可运行判断。通用 runtime、runner、queue、session、SQLite lifecycle、workspace/source intake、memory/artifact transport、workbench、observability、CLI/MCP/Skill/product-entry/sidecar/status wrapper 必须进入 OPL 上收、generated surface 替换、refs-only 收薄或退役分类。
- `minimal authority` 只表示 MAS 持有医学 stage 质控、publication quality、artifact mutation authorization、publication-route memory accept/reject、source readiness、owner receipt 和 typed blocker 等领域裁决边界；它不表示 MAS 应继续维护通用运行平台。

## 当前定位

MAS 是医学研究 domain agent，也是 OPL-compatible package。它保留 direct MAS app skill path，并可被 OPL stage-led runtime 发现、托管和投影。两条入口必须回到同一套 MAS-owned study truth、stage semantics、AI reviewer / quality gate、publication route、artifact authority、memory writeback decision、owner receipt 和 typed blocker。

OPL Framework / shared family layer 持有通用 scheduler、queue、attempt ledger、state-machine runner、provider workflow、human gate transport、memory/artifact locator、lifecycle/index、observability、repair projection、generated entry/status/workbench shell 和 App drilldown。MAS 不把这些通用能力继续写成长期私有平台。

MDS / DeepScientist 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不回到 MAS 默认 backend。

## 当前边界

MAS 必须持有：

- study charter、research question、claim boundary、analysis plan、source asset refs 和 study-level owner route。
- 医学 stage pack、prompt/skill、knowledge packet、quality rubric、AI reviewer / auditor record 要求和 stage closeout 义务。
- domain transition table / transition matrix、publication gate、stop-loss、human gate resume 语义和 controller route。
- publication-route memory body、accept/reject/blocker decision 和 body-free writeback receipt。
- canonical manuscript、figures/tables、submission/current package authority、artifact mutation permission 和 rebuild proof。
- owner receipt、typed blocker、safe action refs、no-forbidden-write guard 和 MAS domain projection refs。

OPL 必须持有：

- provider-backed workflow、worker residency、attempt start/query/signal、retry/dead-letter、queue 和 human gate transport。
- generic transition runner、attempt ledger、lifecycle/index、memory/artifact locator、restore/retention shell、operator projection 和 App/workbench shell。
- CLI/MCP/Skill/product-entry/sidecar/status/workbench/projection wrapper 的 generated/hosted surface，除非某个入口仍作为 MAS direct domain handler 或迁移桥明确保留。

AI-first 质量门要求 executor agent 与 reviewer/auditor agent 独立 invocation、独立 context/task record 和独立 receipt。同一 agent 的自审、同一上下文内的执行后复核、或把 executor summary 改名为 reviewer output，不能关闭 MAS quality gate。

## 当前功能/结构状态

2026-05-18 fresh OPL stage proof 发现过一个结构 blocker：OPL proof bundle 已把 `runtime_guard_required=true` 的 stage 当作 runtime-event obligation；真实 MAS manifest 当时只有 AI/effect-boundary stage 有 machine-readable `runtime_event_refs`。该项属于 MAS `family_stage_control_plane` 结构/功能 gap，不是测试证据尾巴。

当前修复后，MAS 在 `trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs` 中声明了：

- `direction_and_route_selection`：`runtime_event:runtime_supervisor_owner_route.direction_route_selected`、`runtime_event:controller_decisions.direction_route_selected`。
- `baseline_and_evidence_setup`：`runtime_event:controller_decisions.baseline_evidence_ready`、`runtime_event:evidence_ledger.baseline_evidence_ready`。
- `bounded_analysis_campaign`：`runtime_event:runtime_watch.bounded_analysis_evidence_ready`、`runtime_event:evidence_ledger.bounded_analysis_evidence_ready`。
- `manuscript_authoring`：`runtime_event:controller_decisions.manuscript_draft_reviewable`、`runtime_event:canonical_manuscript.manuscript_draft_reviewable`。
- `review_and_quality_gate`：`runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded`、`runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded`。
- `finalize_and_publication_handoff`：`runtime_event:controller_decisions.publication_handoff_ready_or_route_back_recorded`、`runtime_event:artifact_authority.publication_handoff_ready_or_route_back_recorded`。

OPL proof bundle / admission 只有在所有 runtime-guard stage 返回 `admission_status=admitted`、`blockers_count=0`、`warnings_count=0` 后，才能继续把 MAS 当前结构口径写成 `functional_structure_gap_count=0`。若 admission 未跑或返回 blocked，本节必须降级为“存在 stage admission 结构 gap”，不得只把它归入 evidence gate。

在上述 admission gate 通过的前提下，当前机器面已关闭未分类 generic owner 回流、runtime-guard stage admission 和 5 个 structural follow-through gate：`classification_gap_count=0`、`active_private_generic_residue_count=0`、`functional_structure_gap_count=0`。`functional_structure_gap_count` 由 closure evidence 计算，只有同时具备 closed 状态、非结构 gap 标记和 closure proof refs 的 gate 才计入 closed。真实 provider、paper-line、memory/artifact receipt 与 long-soak 仍是后置 evidence gate，不能被结构 closure、repo tests、descriptor ready 或 OPL admission 替代。

2026-05-19 继续把物理代码层的 runtime transport 收薄边界机器化：`product-entry-manifest` 与 sidecar export 现在暴露 `runtime_transport_handoff_projection`。它逐项声明 `mas_runtime_core`、turn runner、worker lease、runtime supervisor scan/consume/dispatch/reconcile 和 `runtime_lifecycle_store.py` 只能作为 MAS domain owner receipt adapter、refs-only SQLite sidecar、guarded apply / typed blocker 或 standalone diagnostic；generic runtime、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 和 workbench owner 全部归 OPL replacement surface。该投影不是把这些文件写成长期 MAS 平台；它是后续在无 domain direct/diagnostic caller、OPL parity 与 domain receipt parity 成立后执行物理删除或 archive/tombstone 的 gate。

以下 5 项已作为功能/结构 closure gate 关闭：

1. `generated_surface_active_caller_cutover`
   OPL generated / hosted CLI、MCP、Skill、product-entry、sidecar、status、workbench 和 projection descriptor 已 ready，并以 active-caller target proof 路由到 OPL generated surface 或 MAS domain handler target。MAS hand-written shell 只能继续作为 direct domain entry、domain handler、owner receipt signer、AI-first output validator、diagnostic cleanup 或 fixture/provenance。

2. `refs_only_adapter_thinning`
   runtime lifecycle SQLite、paper outbox、runtime storage maintenance、workspace/source intake、publication-route memory transport、artifact lifecycle audit、terminal attach 和相关 projection 已收薄为 body-free locator、receipt、blocker、authority refs 或 diagnostic exporter；这些路径不得承担 MAS generic lifecycle / restore-retention / workbench owner，也不得读取 memory body 或 artifact body。
   `runtime_transport_handoff_projection` 进一步把 runtime transport 与 supervisor 代码路径逐项约束为 OPL-owned generic runtime 的 domain bridge / diagnostic，不允许它们重新声明 MAS-owned queue、attempt ledger、worker residency、transition runner 或 persistence engine。

3. `legacy_cleanup_physical_retirement`
   local LaunchAgent/status/remove cleanup、workspace-local watch service wrappers、旧 alias/facade 和 legacy no-active-caller gate 已完成 physical retirement；当前机器清单把 local scheduler install path 与 workspace-local watch wrappers 归为 `legacy_cleanup_physical_retired`，只保留 tombstone/provenance refs 和 forbidden-caller proof。当前 `manager=local` direct call 必须 fail closed，不再返回可用 adapter payload。

4. `opl_app_workbench_drilldown`
   OPL App / workbench drilldown 消费 MAS route/source/quality/artifact/memory/blocker/action refs 和 operator grouping。MAS 只输出 domain projection refs，不在本仓复制通用工作台。仍需证明真实用户路径消费 OPL read model，而不是 MAS repo 复制 Portal/workbench shell。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   lifecycle locator、retention、restore、cleanup ledger 和 workspace/runtime artifact root locator 已按 OPL primitive 与 MAS artifact/source/memory authority 对账。MAS 不持有 generic restore-retention engine，只持有 artifact authority、receipt refs 和 guarded permission；真实 workspace 中的 accepted/rejected writeback、artifact mutation、cleanup/restore/retention receipt 仍需 scaleout。

## 当前测试/证据差距

以下是目标结构边界正确后的证据缺口，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization：

- 真实 paper-line provider apply：OPL provider -> MAS sidecar -> MAS owner chain 在多篇真实论文线上留下 attempt query、typed closeout、MAS owner receipt、artifact delta、gate replay、route decision、stop-loss 或 stable typed blocker。
- publication-route memory receipt scaleout：更多真实 paper line 产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 小集合检索。
- artifact lifecycle receipt scaleout：真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded apply receipt 和 rebuild/freshness proof。
- human gate / resume：approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。
- provider SLO long soak：长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。

## 完善顺序

1. `paper_line_evidence_scaleout`
   在结构收口后推进真实 paper-line provider apply、memory receipt、artifact lifecycle receipt、human gate/resume 和 provider SLO long soak。这里负责验收迁移后的目标边界，不负责替代迁移本身。

## 当前不能写成

- 不能写成 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能写成 `mas_owner_receipt_present` / stable blocker 等于 workspace mutation、artifact authority 放行或 paper closure。
- 不能写成 MAS 已经没有任何私有程序面；准确口径是私有面已收敛为声明式 pack / generated surface handoff、refs-only adapter、minimal authority function 或 no-active-caller cleanup tombstone/provenance gate。
- 不能写成 `runtime_transport/`、runtime supervisor 或 `runtime_lifecycle_store.py` 已经物理删除；准确口径是它们已有 OPL handoff 机器投影，默认不能作为 MAS generic runtime 基座，只能在无 domain direct/diagnostic caller 与 parity proof 后进入物理删除、archive 或 tombstone。
- 不能把 generated surface cutover、refs-only adapter 收薄、legacy physical retirement、OPL App/workbench drilldown 或 lifecycle ledger 对账的结构 closure 写成真实 paper closure、publication-ready、artifact mutation authorization 或 provider long-soak 已完成。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可以由 repo tests 替代的事项。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出，程序只做校验、持久化、签收和防越权。
- 不能把 `judgment_mode=mechanical_guard` 的 helper、owner receipt signer、schema validator、currentness checker 或 refs-only adapter 写成医学 verdict owner；这些面只能签收、校验、投影或阻断，不能生成 quality/source/memory/artifact ready/pass。
- 不能把 executor agent 的自审、同一上下文内的“执行后复核”、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
