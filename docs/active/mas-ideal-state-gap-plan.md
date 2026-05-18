# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `ideal_state_gap_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-18`

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

当前机器面已关闭未分类 generic owner 回流：`classification_gap_count=0`、`active_private_generic_residue_count=0`。但结构 follow-through 仍打开，当前 `functional_structure_gap_count=5`，归类为 `functional_followthrough_and_test_evidence_gates`。这 5 项是已经明确的功能/结构工作，不应被 live evidence gate 或分类 closure 替代。

以下 5 项是 active follow-through gate，后续要继续以 OPL replacement、active caller cutover、refs-only thinning、物理清理和 App/lifecycle 消费证据关闭：

1. `generated_surface_active_caller_cutover`
   OPL generated / hosted CLI、MCP、Skill、product-entry、sidecar、status、workbench 和 projection surface 已成为目标接收面；仍需持续证明 active caller 已迁移，MAS hand-written shell 只作为 direct domain entry、domain handler、owner receipt signer、AI-first output validator、diagnostic cleanup 或 fixture/provenance。

2. `refs_only_adapter_thinning`
   runtime lifecycle SQLite、paper outbox、runtime storage maintenance、workspace/source intake、publication-route memory transport、artifact lifecycle audit、terminal attach 和相关 projection 必须继续收薄为 body-free locator、receipt、blocker、authority refs 或 diagnostic exporter。

3. `legacy_cleanup_physical_retirement`
   local LaunchAgent/status/remove cleanup、workspace-local watch service wrappers、旧 alias/facade 和 legacy no-active-caller gate 已进入 no-active-caller cleanup / tombstone 语义；仍需按 replacement proof、no-active-caller scan、fixture/provenance refs-only 条件完成物理删除或 tombstone，不保留兼容别名。

4. `opl_app_workbench_drilldown`
   OPL App / workbench drilldown 需要实际消费 MAS route/source/quality/artifact/memory/blocker/action refs 和 operator grouping。MAS 只输出 domain projection refs，不在本仓复制通用工作台。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   lifecycle locator、retention、restore、cleanup ledger 和 workspace/runtime artifact root locator 需要持续按 OPL primitive 与 MAS artifact/source/memory authority 对账。MAS 不持有 generic restore-retention engine，只持有 artifact authority、receipt refs 和 guarded permission。

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
- 不能写成 MAS 已经没有私有功能实现；准确口径是私有面已收敛为声明式 pack / generated surface handoff、refs-only adapter、minimal authority function 或 no-active-caller cleanup gate。
- 不能把 generated surface cutover、refs-only adapter 收薄、legacy physical retirement、OPL App/workbench drilldown 或 lifecycle ledger 对账写成已关闭；当前它们仍是 `functional_structure_gap_count=5` 的 active follow-through gate。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可以由 repo tests 替代的事项。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出，程序只做校验、持久化、签收和防越权。
- 不能把 `judgment_mode=mechanical_guard` 的 helper、owner receipt signer、schema validator、currentness checker 或 refs-only adapter 写成医学 verdict owner；这些面只能签收、校验、投影或阻断，不能生成 quality/source/memory/artifact ready/pass。
- 不能把 executor agent 的自审、同一上下文内的“执行后复核”、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
