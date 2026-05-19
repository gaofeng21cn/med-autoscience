# 当前状态

**更新时间：2026-05-19**

## 当前角色

`Med Auto Science` 是医学研究 domain agent，也是 OPL-compatible package。单一 MAS app skill 是 direct path 的稳定入口；经 OPL 托管时，OPL 只承载 stage-led runtime、attempt、queue、human gate transport、generated surface、projection 和 App/workbench shell。

MAS 持有医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body/writeback decision、artifact/package authority、runtime-facing owner receipt/projection、typed blocker 和 safe action refs。OPL 不写 MAS study truth、memory body、publication verdict、artifact authority 或 `current_package`。

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能显式接入，并只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不是 MAS 默认 backend。

## 当前运行与文档事实

- Direct MAS app skill path 与 OPL-hosted path 共享同一 MAS-owned stage、controller、durable truth、quality verdict 和 artifact surface。
- `product-entry-manifest`、sidecar export、contracts、runtime/controller surfaces 和 workspace artifact receipts 是当前机器真相；`docs/**` 只做解释、导航、治理和 provenance。
- MAS 标准 OPL Agent 语义包已归位到 repo-root `agent/`：`prompts/`、`stages/`、`skills/`、`quality_gates/`、`knowledge/` 持有 canonical medical research semantic pack；`contracts/pack_compiler_input.json` 通过 `required_domain_pack_paths` 强制列出这些文件，`contracts/stage_control_plane.json` 的 6 个 stage `prompt_refs` 直接指向 `agent/prompts/*.md`。`src/` 当前角色是 domain handler、minimal authority function 与 native helper，不再作为 canonical semantic pack。
- OPL generated / hosted surfaces 消费 `agent/` pack refs、action catalog、stage control plane、handoff、memory/artifact/receipt contracts 和私有 authority boundary；它们可以生成 CLI / MCP / Skill / product-entry / status/workbench descriptor 并 dispatch allowlisted MAS task，但不能写 MAS study truth、publication-route memory body、AI reviewer verdict、publication verdict、artifact authority、source body 或 `current_package`。
- `functional_consumer_boundary` 已完成通用功能面分类、禁回流 guard 和 5 个结构 follow-through gate：`classification_gap_count=0`、`active_private_generic_residue_count=0`、`functional_structure_gap_count=0`。该口径依赖 OPL proof bundle / admission 对 MAS runtime-guard stage 的机器验证；若任一 `runtime_guard_required=true` stage 缺少 `runtime_event_refs`，必须重新打开结构 gap。
- `runtime_transport_handoff_projection` 已进入 `product-entry-manifest` 与 sidecar export：`mas_runtime_core`、turn runner、worker lease、runtime supervisor scan/consume/dispatch/reconcile 和 `runtime_lifecycle_store.py` 只允许作为 domain bridge、receipt signer、typed blocker、refs-only sidecar 或 standalone diagnostic；generic runtime / queue / attempt ledger / retry-dead-letter / worker residency / transition runner / persistence-lifecycle / workbench owner 全部归 OPL。
- 2026-05-19 的 OPL legacy cleanup dry-run 读取当前 MAS manifest 后返回 `plan_status=ready` / `lifecycle_apply.status=dry_run_ready`；MAS tombstone proof 已补齐 replacement parity refs、no-regression evidence refs、history refs 和 tombstone refs。该状态只证明 OPL cleanup gate 可安全消费 MAS cleanup proof，不表示 tracked runtime transport、supervisor 或 SQLite sidecar 已物理删除。
- 2026-05-18 的 MAS `family_stage_control_plane` 修复已为 6 个 runtime-guard stage 同步声明 `trust_boundary.runtime_event_refs` 和 `stage_contract.runtime_event_refs`；OPL proof bundle / admission 读取当前 MAS contract 后返回 MAS 6 个 stage 全部 `admitted`、`blockers_count=0`、`warnings_count=0`。
- 已关闭的结构 gate 是：`generated_surface_active_caller_cutover`、`refs_only_adapter_thinning`、`legacy_cleanup_physical_retirement`、`opl_app_workbench_drilldown` 和 `lifecycle_locator_retention_restore_ledger_reconciliation`。剩余只作为真实 provider、paper-line、memory/artifact receipt、human gate/resume 和 long-soak evidence gate 管理。
- OPL `substrate projection --domain med-autoscience` 当前返回 `projection_status=substrate_refs_resolved`；MAS product-entry manifest 顶层暴露 body-free `source_provenance` refs，OPL lifecycle projection 只索引 source/artifact/memory refs，不读取 source body、memory body、artifact body 或医学 verdict。
- 旧 MDS physical root / monolith binding / legacy provenance 只作为 archive、tombstone 或 refs-only historical fixture 读取；不得回写成 current runtime owner。
- dated closeout、follow-through 和修复流水已经移到 [MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)，不再作为 `docs/status.md` 当前结论展开。

## 当前功能/结构状态

0. `agent_lab_medical_manuscript_self_evolution`
   DM002 的 2026-05-18 高质量医学论文反馈已经通过 OPL Agent Lab blocked suite 和 `opl-meta-agent` developer patch work order 进入 MAS 能力层。`agent-lab-medical-manuscript-quality-suite` 现在把 research wiki / failed-route memory 投影为 typed body-free `research_memory_graph`，把 analysis queue / campaign manifest 投影为 typed body-free `analysis_queue_manifest`，把 runtime events 投影为只含 refs/count/type metadata 的 `runtime_event_ledger`，把 executor/provider/context isolation refs 投影为只读 `provider_switch_hygiene`，并把 claim/evidence/reviewer/display refs 投影为 `claim_assurance_map`。这些输入共同进入 `mas_agent_lab_mechanism_evolution_inputs`，可作为 `opl agent-lab evolve --suite <suite.json> --json` 的外部 suite 输入。当前 self-evolution 口径是：`opl-meta-agent` 可以修改 MAS stage/skill/prompt/rubric/quality-contract/tests/docs；MAS study truth、runtime event body、claim body、AI reviewer verdict、review verdict、publication gate、publication-route memory body 和 current package / artifact authority 仍归 MAS owner chain，OPL 只消费 refs/metadata。新的 work order 必须提供 gap-to-patch traceability、测试 receipt、developer patch receipt、版本记录和 no-forbidden-write 证据。
   本轮已把 HDL/unit harmonization 污染从 prose/source-documentation repair 提升为 hard methodology route：Agent Lab suite 暴露 `mas/analysis-harmonization-owner-routing` 与 `mas/hard-methodology-unit-harmonization-route`，owner callable registry 暴露 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。MAS runtime 现在只接受 unit-harmonized rerun evidence 或 `blocked_reason=unit_harmonized_rerun_required` 的 owner handoff；普通 completed receipt、package refresh 或 AI reviewer prose note 不能关闭该类阻塞。
   随后的 source provenance follow-up 把 Agent Lab work order 扩展到 `source_provenance_owner_recovery` 和 `source_provenance_terminal_blocker_route_back`：`source_provenance_owner` 会在受控 study/runtime root 内搜索模型、RESULT 和 provenance 候选，并只接受完整 `canonical_transport_model_provenance_bundle`。只有指标摘要、旧稿方法描述或重新拟合替代模型时，它会保留 `transport_model_provenance_recovery_required` typed blocker，并把 `provenance_search` 写入 owner result 供下一步决策审计；当前搜索完成但仍未找到 canonical bundle 时，supervisor read model 退到 `blocked_reason=methodology_reframe_required`、`next_owner=decision`，避免继续显示同一 source owner 可执行假循环。
   最新补丁把该终态 blocker 接到 `methodology_reframe_route_decision`：scan 生成 decision action，consumer 生成 decision request/dispatch，dispatch executor 写 `artifacts/supervision/requests/decision/latest.json` 并由 decision owner 物化 `controller_decisions/latest.json`。这只授权 DM002 回到方法学路线选择，不写论文交付面、不改 `publication_eval/latest.json`，也不替 AI reviewer 宣布 ready。
   本轮调度补丁进一步修复了 `consumer/latest.json` 被后续空 scan 覆盖后，显式 `unit_harmonized_external_validation_rerun` 无法执行的问题。executor 现在只在显式 action type、study-level persisted dispatch 为 ready、且 owner request 与 owner route 完全匹配时读取 persisted dispatch；没有 owner request 的旧 dispatch 仍然不能执行，owner route / forbidden surface / prompt contract / repeat-suppression gate 仍 fail closed。

1. `generated_surface_active_caller_cutover`
   已关闭为 OPL generated / hosted surface 与 MAS domain handler target 边界。MAS hand-written shell 只允许继续承担 direct domain entry、domain handler、AI-first validator、owner receipt signer、diagnostic cleanup 或 provenance fixture；旧 wrapper/alias/facade 不再作为长期 caller 语义保留。

2. `refs_only_adapter_thinning`
   runtime lifecycle SQLite、paper outbox、storage maintenance、publication-route memory transport、artifact lifecycle audit、terminal attach、runtime transport 和 runtime supervisor shell 已收薄为 refs-only domain sidecar / locator / receipt / blocker / authority-ref / diagnostic surface；MAS 不声明 generic lifecycle、source、session、workbench、queue、attempt ledger、worker residency、transition runner 或 scheduler owner。后续只做回流防护、物理删除 gate 和 evidence scaleout。

3. `legacy_cleanup_physical_retirement`
   local LaunchAgent install path、workspace-local wrapper、旧 status/remove cleanup diagnostic、旧 alias/facade/test entry 已完成 physical retirement；当前允许角色只剩 tombstone/provenance refs 和 forbidden-caller proof。`manager=local` direct call 必须 fail closed，不再返回可用 adapter payload。

4. `opl_app_workbench_drilldown`
   MAS route/source/quality/artifact/memory/blocker/action refs 作为 OPL App/workbench drilldown 输入；MAS 不复制通用工作台 owner。剩余是真实用户路径、截图/发布包和长时 operator evidence。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   lifecycle locator、retention、restore、cleanup ledger 与 workspace runtime artifact root locator 已按 OPL generic lifecycle shell / MAS artifact authority receipt 边界对账；MAS 不持有 generic restore-retention engine。真实 workspace receipt scaleout 仍待完成。

## 当前测试/证据差距

以下属于剩余证据门，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization：

- 真实 paper-line provider apply。
- publication-route memory receipt scaleout。
- artifact lifecycle receipt scaleout。
- human gate / resume / explicit wakeup owner-chain 运行证明。
- provider SLO long soak。

## 当前完善顺序

1. 用真实 paper-line provider apply 验证 OPL provider -> MAS sidecar -> MAS owner chain 能持续返回 owner receipt、progress delta 或 typed blocker。
2. 扩展 publication-route memory accepted/rejected/blocked writeback receipts。
3. 扩展 artifact lifecycle mutation / cleanup / restore / retention guarded receipts。
4. 验证 human gate、resume、explicit wakeup 与 owner route 不越过 MAS quality gate 或 artifact authority。
5. 做 provider SLO long soak、restart/re-query、retry/dead-letter 和 no-forbidden-write 长窗口验证。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能把结构 gate 关闭、classification closure、descriptor ready、local LaunchAgent no-active-caller proof 或 selected proof 写成真实 paper closure、publication-ready、artifact mutation authorization 或 provider long-soak 已完成。
- 不能把 `classification_gap_count=0`、`active_private_generic_residue_count=0` 或 descriptor ready 单独写成结构闭合；结构闭合必须来自 5 个 closure gate 的 replacement/cutover/thinning/retirement/reconciliation proof。
- 不能把 provider/live paper-line evidence gate 写成已完成的真实 provider / paper-line 证据。
- 不能把 OPL legacy cleanup dry-run ready 写成 MAS repo 物理源码已经清零；物理删除仍受 no-active-caller、OPL parity 和 domain receipt parity gate 约束。
- 不能把 dated specs、dated closeout、修复流水或历史 full record 当成 current truth。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 MAS tracked runtime transport / supervisor / SQLite sidecar 文件的存在写成 MAS 仍拥有 generic runtime；也不能反过来写成这些文件已物理删除。当前事实是 OPL handoff 投影已落地，物理删除仍受 no-active-caller、OPL parity 和 domain receipt parity gate 约束。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 过程归档：[MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)
