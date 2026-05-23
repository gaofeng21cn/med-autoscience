# 当前状态

**更新时间：2026-05-22**

Owner: `MedAutoScience`
Purpose: `current_truth_summary`
State: `active_current_truth`
Machine boundary: 本文是人读 current-state 摘要。机器真相继续归 `agent/` pack、`contracts/`、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace artifact、owner receipt 和 generated artifact proof。

## 当前角色

`Med Auto Science` 是医学研究 domain agent，也是 OPL-compatible package。单一 MAS app skill 是 direct path 的稳定入口；经 OPL 托管时，OPL/Temporal 是默认启用的 hosted autonomous runtime，承载持久在线 stage-led runtime、attempt、queue、wakeup、retry/dead-letter、resume、human gate transport、generated surface、projection 和 App/workbench shell。Codex App 不是任务启动后的外围持续 driver。

MAS 持有医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body/writeback decision、artifact/package authority、runtime-facing owner receipt/projection、typed blocker 和 safe action refs。OPL 不写 MAS study truth、memory body、publication verdict、artifact authority 或 `current_package`。

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能显式接入，并只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不是 MAS 默认 backend。

## 当前机器事实

- `agent/` 是 canonical medical research semantic pack：`prompts/`、`stages/`、`skills/`、`quality_gates/`、`knowledge/` 持有医学研究 stage / prompt / skill / quality / knowledge 语义。
- `contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是 OPL handoff、generated surface、functional boundary 与 production acceptance 的主要机器面。
- Direct MAS app skill path 与 OPL-hosted path 共享同一 MAS-owned stage、controller、durable truth、quality verdict 和 artifact surface。
- OPL generated / hosted surfaces 可以生成或托管 CLI / MCP / Skill / product-entry / status / workbench descriptor，并 dispatch allowlisted MAS task；它们不能写 MAS study truth、publication-route memory body、AI reviewer verdict、publication verdict、artifact authority、source body 或 `current_package`。
- Workspace/file lifecycle 已按 repo-source 与 live/runtime 写集分层：开发 checkout 只承载 semantic pack、机器合同、authority-function descriptor/receipt refs、domain handler/native helper 和人读治理；真实 workspace state、runtime artifact、receipt instance、paper/package/export artifact 和临时 build/cache/venv/pycache/pytest cache/install sync 副产物必须进入受控 study workspace/runtime artifact root 或用户级 runtime state。
- `DEFAULT_MANAGED_RUNTIME_BACKEND_ID` 已切到 `opl_provider_backed_stage_runtime`；`runtime_backend_default_operation_contract`、product-entry manifest 与 sidecar export 声明默认 generic runtime owner 为 `one-person-lab`，默认 backend 为 `opl_provider_backed_stage_runtime`。历史 payload 里的 `mas_runtime_core` 只能按 retired provenance / migration input 读取；当前 MAS 侧只暴露 domain authority refs、owner receipt、typed blocker、artifact/source/quality refs 和 no-forbidden-write proof。`runtime_backend_default_operation_contract.default_autonomous_runtime`、`provider_topology.default_autonomous_runtime`、`managed_temporal_state_consistency.default_autonomous_runtime` 与 `runtime_transport_handoff_projection.default_caller_policy` 共同声明：hosted autonomous runtime 默认启用，provider 为 `temporal`，wakeup/retry/resume owner 为 OPL，`codex_app_outer_driver_required=false`，`mas_daemon_scheduler_attempt_loop_allowed=false`。
- `functional_consumer_boundary` 已关闭未分类 generic owner 回流，并把 MAS 私有面限定为 declarative pack / generated surface handoff、domain authority refs、minimal authority function 或 legacy tombstone/provenance gate。
- MAS stage control plane 已为 6 个 runtime-guard stage 声明 `trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs`；stage cohort-loop refs 也已声明 source scope、cohort query、OPL queue trigger、monitor 和 dashboard metric refs。
- `contracts/production_acceptance/mas-production-acceptance.json` 只承认 structural / physical conformance 与 production-like receipt chain；它不授权 domain ready、publication ready、medical ready、artifact mutation 或 `current_package` 更新。
- 旧 residue audit 程序面已从 current product-entry / sidecar 暴露面移除；旧 residue 只通过 `legacy_retirement_tombstone_proof`、`functional_consumer_boundary.retired_legacy_residue_tombstones` 和 `contracts/runtime/legacy-active-path-tombstones.json` 保留 tombstone/provenance refs。
- `paper_line_guarded_apply_evidence` 已作为 OPL-ingestable body-free ref packet 固化，可暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume 和 stable typed blocker refs；真实 closeout 仍需要 MAS owner receipt 或 stable typed blocker。
- MAS stage expected receipt / monitor freshness 的 current handoff 已由 MAS-owned typed blocker refs 接入 OPL refs-only ledger；当前 OPL App/readiness/production closeout 不再把 MAS stage evidence handoff 当作 open current blocker。该结论不声明任何具体 paper-line、publication quality、artifact mutation、memory writeback、human gate 或 long-soak 已完成。
- owner-route / runtime handoff 当前固定为 body-free refs-only 交接：MAS 发布 controller authorization、domain route、owner receipt、typed blocker、current work-unit refs 和 authority boundary；OPL runtime manager 负责 liveness、queue hydration、attempt retry、dead-letter、provider resume/relaunch 和 operator status projection。MAS 不写 generic runtime queue，不把 OPL attempt 状态当 MAS study truth。
- `sidecar export` 的 `domain_route/reconcile-apply`、`paper_autonomy/guarded-apply`、`publication_aftercare/*` 与 `domain_owner/default-executor-dispatch` pending task 已提供 `domain_dispatch_evidence_record_payload`。该 payload 只携带 MAS-owned typed blocker refs、evidence refs、no-regression refs、identity fields 和 OPL 可记录的 receipt hint；profile path、artifact/memory/current-package body、paper body 和 domain truth body 不能作为 preflight 成功条件。
- owner-route 控制层已收敛为 `mas-owner-route-attempt-protocol.v1`：owner route 统一携带 reason registry、priority lattice、currentness contract 与 `owner_route_currentness_basis`；`domain_owner/default-executor-dispatch` pending task 导出完整 Owner-Route Attempt envelope 和 typed closeout completion boundary。未注册 reason 或缺 work-unit/truth/runtime/source fingerprint 的 dispatch fail closed，不进入 OPL pending task。该协议只授权 OPL queue/attempt/provider/read-model transport；OPL provider completion 不等于 MAS owner receipt、AI reviewer pass、package freshness 或 submission authorization。
- `mas_real_paper_line_provider_canary_closeout` 已把 owner receipt、stable typed blocker、progress delta、AI reviewer/gate、artifact movement、human gate/resume 和 no-forbidden-write refs 物化为标准 `body_free_evidence_packets`。该 packet 只复用既有 MAS owner-chain refs，禁止 artifact/memory/current-package body，供 OPL App / Agent Lab / evidence ledger 摄取；它不新增 owner receipt、不执行 artifact mutation、不声明具体 paper-line closure、publication-ready、domain-ready 或 production-ready。
- 多批 guarded-apply、owner-route、aftercare 与 default-executor dispatch payload 已证明可被 OPL refs-only external evidence ledger 记录/验证，identity mismatch 会 fail-closed。当前状态页不保存具体 attempt、worklist 数字或命令流水；过程证据归 OPL ledger、提交历史和 [MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)。状态结论只保留：MAS owner-chain refs / typed blocker refs 可被 OPL safe-action shell 消费，verified payload 仍不声明 domain ready。
- Portal pause/resume/stop、submission milestone parking、controller refresh/current authorization 与 `study_progress` 当前都按 OPL runtime-owner handoff / read-only progress projection 读取。它们只能暴露 runtime owner route request、proposed runtime-state delta、current domain transition、owner refs 或 typed blocker；不直接调用 MAS generic runtime control，也不生成 provider attempt。
- `family_action_catalog` 的 read-only `study_state_matrix` action 只物化 MAS-owned transition matrix / spec / cases，供 OPL generic `family-transition-runner` 消费；它不写 study truth、不执行 domain action、不授权 publication quality / submission readiness，也不会作为 public MCP runtime tool 暴露。
- hard-methodology callable routing 已收口到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。该路径只产出 unit-harmonized rerun evidence 或 MAS-owned typed blocker，不落回 generic runtime/control-plane，也不写 paper、publication eval、controller decision、submission package 或 submission readiness。
- [MAS Stage / Route / Handoff 标准](./runtime/stage_route_handoff_standard.md) 是当前 route/stage 读法：stage 为 OPL provider-backed attempt admission 单位，route 为 MAS domain transition / owner-chain recommendation，handoff 为 body-free refs-only 交接包。指定杂志后的格式整理应进入 `finalize_and_publication_handoff` stage 下的 `journal-resolution` / `finalize` route transition，由 OPL stage graph 调度 journal requirement、format delta、artifact authority、independent review 和 submission handoff 子节点。
- route/stage 残留边界的机器面已收敛到当前 owner-route/read-model/receipt 名：`owner_route_reconcile`、`progress_projection`、`domain_health_diagnostic`、`domain_decision_authority`、`domain_authority_refs_index` 与 `owner_route_dispatch_receipt`。旧 MAS 私有 runtime/route surface 名只保留为 tombstone/provenance；仍有 domain-ref consumer 的当前实体继续受 no-resurrection、OPL replacement parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 tombstone refs 删除门约束。

## 当前功能/结构状态

当前已关闭的结构 gate 是：

| gate | 当前口径 |
| --- | --- |
| `generated_surface_default_owner_cutover` | OPL generated / hosted surface 与 MAS domain handler target 边界已闭合；MAS hand-written shell 只允许继续承担 direct domain entry、domain handler、AI-first validator、owner receipt signer、diagnostic cleanup 或 provenance fixture。 |
| `domain_authority_refs_thinning` | runtime lifecycle SQLite、paper outbox、storage maintenance、publication-route memory transport、artifact lifecycle audit、runtime transport 和 domain route shell 已收薄为 domain authority refs、locator、receipt、blocker、authority-ref 或 diagnostic provenance surface；terminal attach/read-model 已从 MAS 当前态退役。 |
| `legacy_cleanup_physical_retirement` | local LaunchAgent install path、workspace-local wrapper、旧 status/remove cleanup diagnostic、旧 alias/facade/test entry 已进入 physical retirement / tombstone / provenance 口径。`manager=local` direct call 必须 fail closed。 |
| `opl_app_workbench_drilldown` | MAS route/source/quality/artifact/memory/blocker/action refs 已作为 OPL App/workbench drilldown 输入；MAS 不复制通用工作台 owner。 |
| `lifecycle_locator_retention_restore_ledger_reconciliation` | lifecycle locator、retention、restore、cleanup ledger 与 workspace runtime artifact root locator 已按 OPL generic lifecycle shell / MAS artifact authority receipt 边界对账。 |
| `family_transition_materialization_handoff` | MAS 只暴露 read-only `study_state_matrix` materialization；OPL 负责消费 spec/cases 并执行 generic transition matrix runner。MAS 不持有 generic state-machine runner，也不把 matrix pass 写成 publication / submission ready。 |
| `hard_methodology_callable_routing` | HDL/unit harmonization 与 grouped calibration 这类 hard-methodology work unit 已路由到 `analysis_harmonization_owner` authority callable；MAS 只保留医学方法学 owner evidence / typed blocker，generic runner 与 App/workbench shell 仍归 OPL。 |

这些 gate 的关闭不等于真实 paper closure、publication-ready、artifact mutation authorization、provider long-soak 或 MAS runtime transport / SQLite refs index 物理删除。

## 当前物理源码形态差距

MAS 已完成 owner/contract/read-model 收薄，并完成 domain route / domain SLO projection active source 命名收口。剩余差距统一读作 domain authority refs / diagnostic provenance 的物理删除门，不是 MAS generic runtime owner 复活，也不是已经清零：

| residual surface | 当前定位 | 删除门 |
| --- | --- | --- |
| `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease | 已按旧 runtime 控制面物理退役；仅允许以 tombstone/provenance 或 OPL provider-backed handoff refs 被读取。 | no-resurrection、OPL provider parity、真实 paper-line receipt parity、focused tests、no-forbidden-write proof、history/tombstone refs。 |
| `lifecycle_refs_adapter.py` 与 lifecycle refs parts | 已由 `domain_authority_refs_index` 取代；不得写成 MAS generic persistence engine、diagnostic fallback 或 active adapter。 | OPL lifecycle/current-control-state parity、MAS domain receipt parity、no-resurrection、focused tests、tombstone refs。 |
| product-entry / status / workbench projection shell | direct MAS path、OPL handoff 输入或 diagnostic read model；不复制 OPL App/workbench owner。 | OPL generated product/status/workbench 成为 production/default caller 后，只保留 MAS truth refs、receipt signer、typed blocker 和 authority refs。 |
| `owner_route_handoff*` | owner-route dispatch/export domain authority refs surface；当前只输出 MAS owner-route refs、typed blocker、safe-action receipt 和 no-forbidden-write proof。 | OPL generated sidecar default caller parity、真实 owner receipt 或 stable typed blocker parity、focused sidecar tests、no-forbidden-write proof、history/tombstone refs。 |
| stage/progress/task-intake/storage/knowledge/batch read-model shells | 已按 parts/helpers 收薄为 projection、locator、refs-only payload assembly 或 diagnostic input。 | 不能承担 publication verdict、artifact mutation、memory body、generic queue、generic lifecycle 或 App owner；对应 OPL primitive 与 MAS receipt parity 成立后直接删除或 tombstone。 |
| human-gate alias residue | product/workbench human-gate 输出统一到 `needs_user_decision`。 | 旧 physician/legacy alias 只允许作为 tombstone/provenance 或 fail-closed 测试对象。 |

私有实现 / OPL 迁移台账见 [MAS 私有实现与 OPL 迁移台账](./runtime/opl_private_implementation_migration_inventory.md)。该台账是当前迁移治理索引；具体拆分提交、行数变化、focused proof 和历史 closeout 不再放入本状态页。

关闭门槛固定为：active caller proof、OPL generated/provider parity、MAS domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs 同时成立。满足后直接物理删除、archive 或 tombstone，不保留 compatibility alias、wrapper、facade 或兼容聚合测试。

## 当前测试/证据差距

以下是后续真实 paper-line / workspace scaleout 验证范围，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization，也不再作为结构标准化缺口计数：

- 真实 paper-line provider apply：OPL provider -> MAS sidecar -> MAS owner chain 在真实论文线上留下 attempt query、typed closeout、MAS owner receipt，并通过 Lane 4A ref packet 暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、stop-loss 或 stable typed blocker。
- owner-chain body-free packet scaleout：当前 canary closeout 与 provider-hosted guarded-apply dispatch receipt 已能输出标准 `body_free_evidence_packets`，但这只是 refs 物化和摄取能力；仍需真实 paper-line canary 持续产出 owner receipt、stable blocker、artifact/memory/human-gate receipt 与 no-forbidden-write proof。
- domain dispatch owner-route / aftercare ledger scaleout：当前多批真实 workspace sidecar payload 已证明 OPL identity guard 能消费匹配 refs-only payload，并能 fail-closed 阻断错误回填；这仍只是 payload 消费 / route-back hygiene，不替代 reviewer refresh 执行、runtime redrive 执行、writer direct-fix、owner receipt success、artifact/memory/human-gate receipt 或 long-soak。
- publication-route memory receipt scaleout：更多真实 paper line 产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 按 refs 检索。
- artifact lifecycle receipt scaleout：真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded receipt 和 rebuild/freshness proof。
- human gate / resume：approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。
- provider SLO long soak：长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。
- 状态转移 focused proof：stopped / waiting / paused / live 等 runtime 状态与 controller authorization、domain transition、submission metadata handoff 的组合路径需要继续用 focused tests 锁定。2026-05-21 已补 `stopped controller_work_unit_pending` 不被 metadata parking 覆盖的回归测试；后续真实 paper-line canary 仍需证明对应 redrive 能产出 owner receipt、progress delta、gate replay、human gate、stop-loss 或 stable typed blocker。
- family transition materialization proof：`study_state_matrix` action 与 OPL generic matrix runner 已有 focused proof；后续真实 paper-line canary 仍需证明 matrix route/work-unit 能进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。
- stage graph / route-as-transition proof：OPL 已有承载 route-as-transition 的 stage graph / transition runner / provider attempt 基础面；MAS 仍需用真实 paper-line 与指定 journal 格式整理 canary 回填 owner receipt、artifact authority receipt、independent reviewer/auditor record、human gate 或 stable typed blocker。该 proof 是 production evidence tail，不回写成 MAS 私有 runtime 或 publication-ready 结论。

## 当前完善顺序

1. 并行推进 Codex pack canonicalization、OPL-generated default-owner cutover 和 runtime_transport / SQLite physical retirement gate 盘点；只关闭具备 no-resurrection、replacement parity、domain receipt parity 和 no-forbidden-write proof 的删除项。
2. 同步推进 workbench / sidecar / status retirement：OPL generated product/status/workbench shell 成为 production/default caller 后，MAS 只保留 direct skill target、domain handler、receipt signer、typed blocker 和 authority refs。
3. 跑真实 paper-line canary，验证 OPL provider attempt -> MAS sidecar -> MAS owner chain 能产出 owner receipt、progress delta、gate replay、route decision、human gate、stop-loss 或 stable typed blocker。
4. canary 之后扩展 publication-route memory、artifact lifecycle、human gate/resume 和 provider SLO long-soak evidence；这些属于测试/证据 tail，不回写成结构 closure，也不替 publication gate、AI reviewer 或 artifact authority 宣布 ready。
5. 每个物理删除动作都必须带 no-resurrection、replacement parity、domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs；满足即删除、archive 或 tombstone，不新增兼容 alias。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能声明 MAS production acceptance receipt 等于具体论文线 publication-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 descriptor ready、conformance passed、classification closed、legacy cleanup ledger ready 或 selected proof 写成 production ready、paper closure 或物理源码清零。
- 不能把 `runtime_transport/`、domain route、turn runner、worker lease 或 `lifecycle_refs_adapter.py` 的存在写成 MAS 仍拥有 generic runtime。current active boundary 只允许使用当前 owner-route/read-model/receipt/ref-index surface；旧 MAS 私有 runtime/route surface id 只能作为 retired legacy id 留在 provenance 或 delete-gate 映射中。仍有 caller 的当前实体继续受删除门约束。
- 不能把 OPL `stage_production_evidence_receipt_record|verify` 写成 MAS production ready；它只是 expected receipt / monitor freshness 的 refs-only record/verify route。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 Codex App 外围会话、MAS daemon/scheduler、MAS attempt loop 或 `mas_runtime_core` 写成任务启动后的默认持久在线调度 owner；默认托管自治运行 owner 是 OPL/Temporal。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 当前执行地图：[MAS 当前开发线路](./active/current-development-lines.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 过程归档：[MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)
