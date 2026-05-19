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

- `direction_and_route_selection`：`runtime_event:domain_route_owner_route.direction_route_selected`、`runtime_event:controller_decisions.direction_route_selected`。
- `baseline_and_evidence_setup`：`runtime_event:controller_decisions.baseline_evidence_ready`、`runtime_event:evidence_ledger.baseline_evidence_ready`。
- `bounded_analysis_campaign`：`runtime_event:runtime_watch.bounded_analysis_evidence_ready`、`runtime_event:evidence_ledger.bounded_analysis_evidence_ready`。
- `manuscript_authoring`：`runtime_event:controller_decisions.manuscript_draft_reviewable`、`runtime_event:canonical_manuscript.manuscript_draft_reviewable`。
- `review_and_quality_gate`：`runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded`、`runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded`。
- `finalize_and_publication_handoff`：`runtime_event:controller_decisions.publication_handoff_ready_or_route_back_recorded`、`runtime_event:artifact_authority.publication_handoff_ready_or_route_back_recorded`。

OPL proof bundle / admission 只有在所有 runtime-guard stage 返回 `admission_status=admitted`、`blockers_count=0`、`warnings_count=0` 后，才能继续把 MAS 当前结构口径写成 `functional_structure_gap_count=0`。若 admission 未跑或返回 blocked，本节必须降级为“存在 stage admission 结构 gap”，不得只把它归入 evidence gate。

在上述 admission gate 通过的前提下，当前机器面已关闭未分类 generic owner 回流、runtime-guard stage admission 和 5 个 structural follow-through gate：`classification_gap_count=0`、`active_private_generic_residue_count=0`、`functional_structure_gap_count=0`。`functional_structure_gap_count` 由 closure evidence 计算，只有同时具备 closed 状态、非结构 gap 标记和 closure proof refs 的 gate 才计入 closed。真实 provider、paper-line、memory/artifact receipt 与 long-soak 仍是后置 evidence gate，不能被结构 closure、repo tests、descriptor ready 或 OPL admission 替代。

2026-05-19 的 MAS stage cohort-loop refs 已补齐：每个 stage 的 `stage_contract` 都提供 source scope、auditable cohort query、OPL queue trigger、stage/runtime monitor 和 operator dashboard freshness metric refs。OPL isolated verification 读取当前 MAS main 后，`opl stages cohort-loop --domain mas` 返回 `stage_count=6`、`closed_loop_ready_count=6`、`blocker_count=0`。这关闭的是声明式 launch/readiness 闭环结构 gap；真实 paper-line provider launch、consumed refs、owner receipt、memory/artifact apply、human gate/resume 和 long-soak 仍在测试/证据差距中。

2026-05-19 的标准 pack 合同校准把 MAS `pack_compiler_input` 收到 OPL scaffold 的 canonical 形状：`canonical_semantic_pack_root="agent/"`、`canonical_semantic_pack_role="declarative_medical_research_semantics_for_opl_pack_compiler"`，不再暴露旧 `canonical_repo_source_semantic_pack_root`。`required_domain_pack_paths` 必须只指向真实 agent pack 语义文件，不能通过 README 或目录存在性替代 prompts / stages / skills / quality gates / knowledge 文件。

2026-05-19 继续把物理代码层的 runtime transport 收薄边界机器化：`runtime_backend_default_operation_contract`、`product-entry-manifest` 与 sidecar export 现在都暴露 `runtime_backend_is_generic_owner=false` / `runtime_transport_handoff_projection`。它逐项声明 `mas_runtime_core`、turn runner、worker lease、domain route scan/consume/dispatch/reconcile 和 `runtime_lifecycle_store.py` 只能作为 MAS domain owner receipt adapter、refs-only SQLite sidecar、guarded apply / typed blocker 或 standalone diagnostic；generic runtime、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 和 workbench owner 全部归 OPL replacement surface。该投影不是把这些文件写成长期 MAS 平台；它是后续在无 domain direct/diagnostic caller、OPL parity 与 domain receipt parity 成立后执行物理删除或 archive/tombstone 的 gate。

本轮把 `physical_source_morphology_standardization` 明确为独立结构口径并完成 active source 收口。成熟 agent/runtime 框架的共同做法是分开 agent declaration、tools / authority functions、runtime orchestration、state persistence 与 workbench/evidence gate；OPL 吸收这一分层原则，MAS 不能继续用物理源码形态暗示自己持有 generic runtime platform。2026-05-19 live check 的参考依据包括 [OpenAI Agents SDK Agents](https://openai.github.io/openai-agents-python/agents/) 对 Agent 与 Runner / sessions / handoffs / guardrails 的分层，[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 对 checkpoint / thread / store / replay 的分层，[AutoGen AgentChat agents](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/agents.html) 与 [teams](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html) 对 agents / tools / workbench / teams 的分层，以及 [CrewAI agents](https://docs.crewai.com/en/concepts/agents) 对 YAML agent declaration 与 process 承载的分层。它们是工程经验来源，不是 MAS runtime dependency。MAS 理想源码读法应是:

- `agent/` 持有医学 stage、prompt、skill、knowledge、quality gate 和 policy。
- `contracts/` 持有 OPL pack compiler input、stage/action/memory/artifact/receipt contract、runtime handoff、evidence request 和 cleanup gate。
- `runtime/authority_functions/` 或 `src/med_autoscience/**` 中长期保留的代码只承担 medical authority function、domain handler、refs-only adapter、native helper、diagnostic probe 或 fixture。
- generic runtime / lifecycle / worker lease 命名如果仍在 active source 中出现，必须被拆分或证明为 domain bridge / refs-only adapter / diagnostic / tombstone；不能让读者理解为 MAS-owned generic runtime。

因此，当前 active API 已物理归位到 `domain_route_scan.py`、`domain_action_request_materializer.py`、`domain_owner_action_dispatch.py`、`domain_route_reconcile.py` 和 `domain_slo_scheduler_projection.py`。这些 active surfaces 现在表达 domain route projection、owner action request、authority dispatch receipt、typed blocker reconcile 与 OPL runtime-manager SLO projection；developer repair/worktree 元数据不再进入 owner payload。该结构 tail 已关闭，剩余删除 gate 只针对 runtime transport、SQLite lifecycle sidecar、turn runner 和 worker lease 这类仍有 active domain/diagnostic ref caller 的 refs-only adapter。

同一轮收口把 `runtime_lifecycle_sqlite_reference_adapter`、`runtime_storage_maintenance` 和 `terminal_attach_transport` 的 residual 物理形态写入 `functional_consumer_boundary` / `functional_module_inventory`：三者均为 `refs_only_adapter`，只允许输出 owner receipt ref、workspace/artifact/source/status refs、cleanup/terminal gate receipts 或 typed blocker；`generic_owner_claim_allowed=false`，并显式禁止 generic runtime verdict、generic cleanup policy、generic terminal runtime owner 和 paper closure verdict。该项解决的是“正确的东西在正确位置”的结构问题，不是单纯测试补强。

2026-05-19 的后续退役证明把上一轮仍按 `legacy_cleanup_no_active_caller_gate` 命名的四个 residue 从 active classification 中移出，改为 `legacy_cleanup_tombstone_provenance` 与 `retired_legacy_residue_tombstones` 机器面：`mas_generic_workbench_shell`、`legacy_scheduler_default_aliases`、`daemonish_terminal_attach_status_as_runtime_owner`、`scheduler_legacy_residue_without_active_caller` 均为 `active_caller_count=0`、`default_entry_allowed=false`、`current_role=history_tombstone_provenance_only`。这表示它们已经进入 history/tombstone 证明面，不再作为 active cleanup gate 或 MAS 私有 runtime residue 计数。

同一轮也给全部仍保留 active domain / diagnostic caller 的 `refs_only_adapter` 增加 `refs_only_adapter_retirement_gates`：`runtime_lifecycle_sqlite_reference_adapter`、`paper_work_unit_outbox_index`、`runtime_storage_maintenance`、`publication_route_memory_locator_transport_shell`、`artifact_lifecycle_storage_audit_shell`、`terminal_attach_transport` 必须逐项声明 active caller proof、`active_caller_count>0`、`delete_or_tombstone_after`、`generic_owner_claim_allowed=false`、`can_emit_paper_closure_verdict=false` 和 `can_emit_generic_owner_verdict=false`。这些 gate 证明仍保留的代码路径只是 refs-only / diagnostic / domain receipt adapter；只有在 active caller 清零、OPL parity 与对应 focused tests 成立后，才进入物理删除或 tombstone。

2026-05-19 的 OPL legacy cleanup 进一步证明 MAS tombstone proof refs 已被 OPL gate 接受：`opl agents legacy-cleanup apply --domain mas --mode dry-run` 返回 `plan_status=ready` 与 `lifecycle_apply.status=dry_run_ready`，随后 `--mode apply` 写入 OPL refs-only lifecycle ledger 的空计划 closure batch receipt，`--mode verify` 可读回 `verified_receipt_count=1`。MAS manifest 现在向 OPL 暴露 replacement parity refs、no-regression evidence refs、history refs 和 tombstone refs；这只关闭 OPL cleanup ledger blocker，不表示 MAS tracked runtime transport 或 SQLite sidecar 已物理删除，也不表示真实 paper-line provider apply、App 发布路径或 App/workbench 用户路径已完成。

以下 5 项已作为功能/结构 closure gate 关闭：

1. `generated_surface_active_caller_cutover`
   OPL generated / hosted CLI、MCP、Skill、product-entry、sidecar、status、workbench 和 projection descriptor 已 ready，并以 active-caller target proof 路由到 OPL generated surface 或 MAS domain handler target。MAS hand-written shell 只能继续作为 direct domain entry、domain handler、owner receipt signer、AI-first output validator、diagnostic cleanup 或 fixture/provenance。

2. `refs_only_adapter_thinning`
   runtime lifecycle SQLite、paper outbox、runtime storage maintenance、workspace/source intake、publication-route memory transport、artifact lifecycle audit、terminal attach 和相关 projection 已收薄为 body-free locator、receipt、blocker、authority refs 或 diagnostic exporter；这些路径不得承担 MAS generic lifecycle / restore-retention / workbench owner，也不得读取 memory body 或 artifact body。
   `runtime_transport_handoff_projection` 进一步把 runtime transport 与 domain route 代码路径逐项约束为 OPL-owned generic runtime 的 domain bridge / diagnostic，不允许它们重新声明 MAS-owned queue、attempt ledger、worker residency、transition runner 或 persistence engine。

3. `legacy_cleanup_physical_retirement`
   local LaunchAgent/status/remove cleanup、workspace-local watch service wrappers、旧 alias/facade 和 legacy no-active-caller gate 已完成 physical retirement；当前机器清单把 local scheduler install path 与 workspace-local watch wrappers 归为 `legacy_cleanup_physical_retired`，只保留 tombstone/provenance refs 和 forbidden-caller proof。当前 `manager=local` direct call 必须 fail closed，不再返回可用 adapter payload。OPL cleanup dry-run / apply / verify 已能消费 MAS replacement / history / tombstone proof refs；后续任何物理删除、archive 或 tombstone 仍受 domain owner receipt、OPL parity 和 no-active-caller gate 约束。

4. `opl_app_workbench_drilldown`
   OPL App / workbench drilldown 消费 MAS route/source/quality/artifact/memory/blocker/action refs 和 operator grouping。MAS 只输出 domain projection refs，不在本仓复制通用工作台。仍需证明真实用户路径消费 OPL read model，而不是 MAS repo 复制 Portal/workbench shell。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   lifecycle locator、retention、restore、cleanup ledger 和 workspace/runtime artifact root locator 已按 OPL primitive 与 MAS artifact/source/memory authority 对账。MAS 不持有 generic restore-retention engine，只持有 artifact authority、receipt refs 和 guarded permission；真实 workspace 中的 accepted/rejected writeback、artifact mutation、cleanup/restore/retention receipt 仍需 scaleout。

## 当前测试/证据差距

## 当前物理源码形态差距

这部分属于结构治理 tail，不能被 `classification_gap_count=0`、`functional_structure_gap_count=0`、OPL admission、legacy cleanup ledger 或 generated interface ready 吞掉。

- domain route 与 domain SLO projection active source 已完成物理命名收口；剩余历史语境只允许作为 tombstone/provenance、diagnostic ref 或医学 publication/control surface 术语存在。
- `runtime_transport/`、turn runner、worker lease 与 `runtime_lifecycle_store.py` 仍有 active domain / diagnostic caller；目标是 OPL provider parity、paper-line receipt parity 和 no-active-caller 通过后删除、archive 或 tombstone，只保留必要 domain receipt adapter。
- `product_entry_parts/workspace_cockpit/`、product-entry manifest/status、sidecar provider 与 runtime status projection 仍承担 direct MAS path 和 OPL handoff 输入；目标是 OPL generated product/status/workbench shell 成为 production/default caller 后，MAS 只保留 domain handler target、receipt signer、typed blocker 和 authority refs。
- developer repair / worktree / verification 元数据不得长期留在 MAS domain handler；目标是迁入 OPL Agent Lab / developer repair lane 或 explicit contract refs。

这组差距的关闭门槛是：active caller proof、OPL generated/provider parity、MAS domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs 同时成立。未满足前不能物理删除；满足后不保留 compatibility alias。

以下是目标结构边界正确后的证据缺口，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization：

- 真实 paper-line provider apply：OPL provider -> MAS sidecar -> MAS owner chain 在多篇真实论文线上留下 attempt query、typed closeout、MAS owner receipt、artifact delta、gate replay、route decision、stop-loss 或 stable typed blocker。
- publication-route memory receipt scaleout：更多真实 paper line 产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 小集合检索。
- artifact lifecycle receipt scaleout：真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded apply receipt 和 rebuild/freshness proof。
- human gate / resume：approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。
- provider SLO long soak：长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。

## 完善顺序

1. `paper_line_evidence_scaleout`
   在结构收口后推进真实 paper-line provider apply、memory receipt、artifact lifecycle receipt、human gate/resume 和 provider SLO long soak。这里负责验收迁移后的目标边界，不负责替代迁移本身。

2. `refs_only_physical_deletion_gates`
   在不重建 MAS generic runtime 的前提下，按 active caller、OPL parity、domain receipt parity 和 provenance gate 继续处理 runtime transport / turn runner / worker lease / SQLite lifecycle writer / product cockpit / sidecar provider / status projection。domain route 与 domain SLO projection active source 已完成物理命名收口；后续只在 no-active-caller、OPL parity 和 domain receipt parity 成立时继续删除、archive 或 tombstone refs-only adapter，并保持 no-forbidden-write、paper truth / artifact authority 不越权。

## 当前不能写成

- 不能写成 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能写成 `mas_owner_receipt_present` / stable blocker 等于 workspace mutation、artifact authority 放行或 paper closure。
- 不能写成 MAS 已经没有任何私有程序面；准确口径是私有面已收敛为声明式 pack / generated surface handoff、refs-only adapter、minimal authority function 或 no-active-caller cleanup tombstone/provenance gate。
- 不能写成 `runtime_transport/`、domain route 或 `runtime_lifecycle_store.py` 已经物理删除；准确口径是它们已有 OPL handoff 机器投影，默认不能作为 MAS generic runtime 基座，只能在无 domain direct/diagnostic caller 与 parity proof 后进入物理删除、archive 或 tombstone。
- 不能把 `refs_only_adapter_retirement_gates` 写成继续保留 MAS generic runtime；这些 gate 只证明仍有 active domain / diagnostic ref caller 和明确删除门。
- 不能把 `legacy_cleanup_tombstone_provenance` 写成 active cleanup residue；它只保留 no-active-caller proof、history/tombstone refs 和 forbidden output 边界。
- 不能把 `runtime_backend_id=mas_runtime_core` 读成 MAS generic runtime owner；当前 machine contract 已明确 `runtime_owner=one-person-lab`、`runtime_substrate=opl_provider_backed_stage_runtime`、`runtime_backend_role=mas_domain_owner_receipt_adapter`、`runtime_backend_is_generic_owner=false`。
- 不能把 MAS legacy cleanup dry-run / apply / verify ready 写成物理源码已清零；它只证明 OPL cleanup gate 和 refs-only ledger 可消费 MAS replacement / no-regression / history / tombstone refs。
- 不能把 generated surface cutover、refs-only adapter 收薄、legacy physical retirement、OPL App/workbench drilldown 或 lifecycle ledger 对账的结构 closure 写成真实 paper closure、publication-ready、artifact mutation authorization 或 provider long-soak 已完成。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可以由 repo tests 替代的事项。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出，程序只做校验、持久化、签收和防越权。
- 不能把 `judgment_mode=mechanical_guard` 的 helper、owner receipt signer、schema validator、currentness checker 或 refs-only adapter 写成医学 verdict owner；这些面只能签收、校验、投影或阻断，不能生成 quality/source/memory/artifact ready/pass。
- 不能把 executor agent 的自审、同一上下文内的“执行后复核”、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
