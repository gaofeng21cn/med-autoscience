# 当前状态

**更新时间：2026-05-21**

Owner: `MedAutoScience`
Purpose: `current_truth_summary`
State: `active_current_truth`
Machine boundary: 本文是人读 current-state 摘要。机器真相继续归 `agent/` pack、`contracts/`、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace artifact、owner receipt 和 generated artifact proof。

## 当前角色

`Med Auto Science` 是医学研究 domain agent，也是 OPL-compatible package。单一 MAS app skill 是 direct path 的稳定入口；经 OPL 托管时，OPL 承载 stage-led runtime、attempt、queue、human gate transport、generated surface、projection 和 App/workbench shell。

MAS 持有医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body/writeback decision、artifact/package authority、runtime-facing owner receipt/projection、typed blocker 和 safe action refs。OPL 不写 MAS study truth、memory body、publication verdict、artifact authority 或 `current_package`。

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能显式接入，并只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不是 MAS 默认 backend。

## 当前机器事实

- `agent/` 是 canonical medical research semantic pack：`prompts/`、`stages/`、`skills/`、`quality_gates/`、`knowledge/` 持有医学研究 stage / prompt / skill / quality / knowledge 语义。
- `contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是 OPL handoff、generated surface、functional boundary 与 production acceptance 的主要机器面。
- Direct MAS app skill path 与 OPL-hosted path 共享同一 MAS-owned stage、controller、durable truth、quality verdict 和 artifact surface。
- OPL generated / hosted surfaces 可以生成或托管 CLI / MCP / Skill / product-entry / status / workbench descriptor，并 dispatch allowlisted MAS task；它们不能写 MAS study truth、publication-route memory body、AI reviewer verdict、publication verdict、artifact authority、source body 或 `current_package`。
- Workspace/file lifecycle 已按 repo-source 与 live/runtime 写集分层：开发 checkout 只承载 semantic pack、机器合同、authority-function descriptor/receipt refs、domain handler/native helper 和人读治理；真实 workspace state、runtime artifact、receipt instance、paper/package/export artifact 和临时 build/cache/venv/pycache/pytest cache/install sync 副产物必须进入受控 study workspace/runtime artifact root 或用户级 runtime state。
- `DEFAULT_MANAGED_RUNTIME_BACKEND_ID` 已切到 `opl_provider_backed_stage_runtime`；`runtime_backend_default_operation_contract`、product-entry manifest 与 sidecar export 声明默认 generic runtime owner 为 `one-person-lab`，默认 backend 为 `opl_provider_backed_stage_runtime`，delegated domain adapter 为 `mas_runtime_core`。`mas_runtime_core` 的角色是 `mas_domain_owner_receipt_adapter` / diagnostic adapter，不是 MAS-owned generic runtime platform。
- `functional_consumer_boundary` 已关闭未分类 generic owner 回流，并把 MAS 私有面限定为 declarative pack / generated surface handoff、refs-only adapter、minimal authority function 或 legacy tombstone/provenance gate。
- MAS stage control plane 已为 6 个 runtime-guard stage 声明 `trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs`；stage cohort-loop refs 也已声明 source scope、cohort query、OPL queue trigger、monitor 和 dashboard metric refs。
- `contracts/production_acceptance/mas-production-acceptance.json` 只承认 structural / physical conformance 与 production-like receipt chain；它不授权 domain ready、publication ready、medical ready、artifact mutation 或 `current_package` 更新。
- 2026-05-21 physical cleanup follow-through 已删除 current product-entry / sidecar 上的旧 residue audit 程序面；当前旧 residue 只通过 `legacy_retirement_tombstone_proof`、`functional_consumer_boundary.retired_legacy_residue_tombstones` 和 `contracts/runtime/legacy-active-path-tombstones.json` 保留 tombstone/provenance refs，不再作为 current manifest audit surface 暴露。
- `paper_line_guarded_apply_evidence` 已作为 OPL-ingestable body-free ref packet 固化。它可暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume 和 stable typed blocker refs；真实 closeout 仍需要 MAS owner receipt 或 stable typed blocker。
- 2026-05-21 `paper_line_guarded_apply_evidence.opl_stage_evidence_receipt_handoff.stage_owned_typed_blocker_handoff` 已为 6 个 MAS stage 提供 MAS-owned typed blocker refs，并已被 OPL `stage_production_evidence_receipt_record|verify` refs-only ledger 消费。当前 OPL App/readiness/production closeout 不再把 MAS stage expected receipt / monitor freshness 显示为 open；这不声明任何具体 paper-line、publication quality、artifact mutation、memory writeback、human gate 或 long-soak 已完成。
- 2026-05-21 `study_runtime_status` 已补齐 stopped controller work-unit redrive 状态转换：`stopped + controller_work_unit_pending + last_controller_decision_authorization` 会优先仲裁为 `controller_work_unit_pending_redrive` / `quest_waiting_platform_repair_redrive`，不会被 submission metadata-only package 或 synchronized delivery 误停车。对应 focused tests 覆盖 submission metadata waiting、platform repair redrive 与 AI reviewer submission metadata routeback 组合路径；该修复只消费 MAS owner-chain runtime/status truth，不改变 OPL/MAS 边界。
- 2026-05-21 `family_action_catalog` 新增 read-only `study_state_matrix` action，并同步到 product-entry shell、CLI/Skill descriptor 和 descriptor-only MCP projection。该 action 只物化 MAS-owned `study_state_matrix` / `domain_transition_table` / `family_transition_spec` / `family_transition_matrix_cases`，供 OPL generic `family-transition-runner` 消费；它不写 study truth、不执行 domain action、不授权 publication quality / submission readiness，也不会作为 public MCP runtime tool 暴露。
- 2026-05-21 hard-methodology callable routing 已收口：`unit_harmonized_validation_uncertainty_and_grouped_calibration` 这类 work unit 现在经 managed worker authorization 映射到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`，并由 `domain-owner-action-dispatch` 执行 MAS owner callable。该路径只产出 unit-harmonized rerun evidence 或 MAS-owned typed blocker，不落回 generic `ensure_study_runtime`、quality prose repair、OPL transition runner 或 MAS 私有 control-plane 扩张；它不写 paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 submission readiness。

## 当前功能/结构状态

当前已关闭的结构 gate 是：

| gate | 当前口径 |
| --- | --- |
| `generated_surface_active_caller_cutover` | OPL generated / hosted surface 与 MAS domain handler target 边界已闭合；MAS hand-written shell 只允许继续承担 direct domain entry、domain handler、AI-first validator、owner receipt signer、diagnostic cleanup 或 provenance fixture。 |
| `refs_only_adapter_thinning` | runtime lifecycle SQLite、paper outbox、storage maintenance、publication-route memory transport、artifact lifecycle audit、terminal attach、runtime transport 和 domain route shell 已收薄为 refs-only domain sidecar / locator / receipt / blocker / authority-ref / diagnostic surface。 |
| `legacy_cleanup_physical_retirement` | local LaunchAgent install path、workspace-local wrapper、旧 status/remove cleanup diagnostic、旧 alias/facade/test entry 已进入 physical retirement / tombstone / provenance 口径。`manager=local` direct call 必须 fail closed。 |
| `opl_app_workbench_drilldown` | MAS route/source/quality/artifact/memory/blocker/action refs 已作为 OPL App/workbench drilldown 输入；MAS 不复制通用工作台 owner。 |
| `lifecycle_locator_retention_restore_ledger_reconciliation` | lifecycle locator、retention、restore、cleanup ledger 与 workspace runtime artifact root locator 已按 OPL generic lifecycle shell / MAS artifact authority receipt 边界对账。 |
| `family_transition_materialization_handoff` | MAS 只暴露 read-only `study_state_matrix` materialization；OPL 负责消费 spec/cases 并执行 generic transition matrix runner。MAS 不持有 generic state-machine runner，也不把 matrix pass 写成 publication / submission ready。 |
| `hard_methodology_callable_routing` | HDL/unit harmonization 与 grouped calibration 这类 hard-methodology work unit 已路由到 `analysis_harmonization_owner` authority callable；MAS 只保留医学方法学 owner evidence / typed blocker，generic runner 与 App/workbench shell 仍归 OPL。 |

这些 gate 的关闭不等于真实 paper closure、publication-ready、artifact mutation authorization、provider long-soak 或 MAS runtime transport / SQLite sidecar 物理删除。

## 当前物理源码形态差距

MAS 已完成 owner/contract/read-model 收薄，并完成 domain route / domain SLO projection active source 命名收口。剩余差距是 retained adapter / diagnostic 的物理删除门，不是 MAS generic runtime owner 复活，也不是已经清零：

- 私有实现 / OPL 迁移台账已落到 [MAS 私有实现与 OPL 迁移台账](./runtime/opl_private_implementation_migration_inventory.md)。该台账把 `status_and_decision.py` 明确列为 `needs_split_before_migration` 的 control-plane thinning item：通用状态机、runner、queue、watch shell 和 status/projection 外壳长线迁 OPL；publication quality verdict、study truth、artifact mutation、owner receipt、source readiness 和 typed blocker 留 MAS。该台账是当前迁移治理索引，不表示迁移或物理删除已经完成。
- `runtime_transport/`、turn runner、worker lease 与 `runtime_lifecycle_store.py` 仍有 active domain / diagnostic caller；当前角色只能是 domain receipt adapter、refs-only lifecycle sidecar、guarded apply / typed blocker bridge 或 standalone diagnostic。
- 2026-05-21 手写 MAS CLI 聚合器已做自然边界收薄：`src/med_autoscience/cli.py` 从约 1391 行降到约 982 行，stage-memory、workbench/portal、watch/supervision、workspace/data/bootstrap dispatch 迁入 `cli_parts/*_commands.py`。这只是 direct CLI adapter 体积收薄；OPL generated CLI / Skill / MCP / product-entry default caller 尚未因此完成。
- `product_entry_parts/workspace_cockpit/`、product-entry manifest/status 与 runtime status projection 仍承担 direct MAS path、OPL handoff 输入或 diagnostic read model；generic sidecar provider lifecycle CLI 已退役，sidecar active bridge 只剩 `sidecar_family_adapter` 的 export/dispatch owner-route。剩余 product/status/workbench shell 在 OPL generated product/status/workbench shell 成为 production/default caller 前不能删除。
- 2026-05-21 本 worktree 已对 product-entry / workspace cockpit / workbench projection shell 做一处最小 alias 清理：旧 `needs_physician_decision` / `legacy_*physician*` / `study_physician_decision_gate` 不再作为 product/workbench human-gate 输出或 fallback；`needs_user_decision` 是该层唯一 human-gate 字段。该项只减少 wrapper/facade residue，不声明 status/progress runtime truth 物理删除。
- 当前 active cleanup gate 需显式审计三项 retained residue：`workbench_shell_domain_projection_refs` 是 OPL workbench 的 domain projection refs，`sidecar_dispatch_adapter` 是 domain sidecar dispatch adapter / provider diagnostic，`status_projection_domain_truth_refs` 是 MAS domain truth status projection。三项都仍有 active caller，`physical_delete_permitted=false`，只能在 active caller 清零、OPL replacement parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 tombstone/provenance refs 同时成立后删除或 tombstone。
- developer repair / worktree / verification 元数据不得长期留在 MAS domain handler；目标是迁入 OPL Agent Lab / developer repair lane 或 explicit contract refs。

关闭门槛固定为：active caller proof、OPL generated/provider parity、MAS domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs 同时成立。满足后直接物理删除、archive 或 tombstone，不保留 compatibility alias、wrapper、facade 或兼容聚合测试。

## 当前测试/证据差距

以下是后续真实 paper-line / workspace scaleout 验证范围，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization，也不再作为结构标准化缺口计数：

- 真实 paper-line provider apply：OPL provider -> MAS sidecar -> MAS owner chain 在真实论文线上留下 attempt query、typed closeout、MAS owner receipt，并通过 Lane 4A ref packet 暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、stop-loss 或 stable typed blocker。
- publication-route memory receipt scaleout：更多真实 paper line 产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 按 refs 检索。
- artifact lifecycle receipt scaleout：真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded receipt 和 rebuild/freshness proof。
- human gate / resume：approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。
- provider SLO long soak：长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。
- 状态转移 focused proof：stopped / waiting / paused / live 等 runtime 状态与 controller authorization、domain transition、submission metadata handoff 的组合路径需要继续用 focused tests 锁定。2026-05-21 已补 `stopped controller_work_unit_pending` 不被 metadata parking 覆盖的回归测试；后续真实 paper-line canary 仍需证明对应 redrive 能产出 owner receipt、progress delta、gate replay、human gate、stop-loss 或 stable typed blocker。
- family transition materialization proof：`study_state_matrix` action 与 OPL generic matrix runner 已有 focused proof；后续真实 paper-line canary 仍需证明 matrix route/work-unit 能进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。

## 当前完善顺序

1. 并行推进 Codex pack canonicalization、OPL-generated default caller cutover 和 runtime_transport / SQLite physical retirement gate 盘点；只关闭具备 no-active-caller、replacement parity、domain receipt parity 和 no-forbidden-write proof 的删除项。
2. 同步推进 workbench / sidecar / status retirement：OPL generated product/status/workbench shell 成为 production/default caller 后，MAS 只保留 direct skill target、domain handler、receipt signer、typed blocker 和 authority refs。
3. 跑真实 paper-line canary，验证 OPL provider attempt -> MAS sidecar -> MAS owner chain 能产出 owner receipt、progress delta、gate replay、route decision、human gate、stop-loss 或 stable typed blocker。
4. canary 之后扩展 publication-route memory、artifact lifecycle、human gate/resume 和 provider SLO long-soak evidence；这些属于测试/证据 tail，不回写成结构 closure，也不替 publication gate、AI reviewer 或 artifact authority 宣布 ready。
5. 每个物理删除动作都必须带 no-active-caller、replacement parity、domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs；满足即删除、archive 或 tombstone，不新增兼容 alias。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能声明 MAS production acceptance receipt 等于具体论文线 publication-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 descriptor ready、conformance passed、classification closed、legacy cleanup ledger ready 或 selected proof 写成 production ready、paper closure 或物理源码清零。
- 不能把 `runtime_transport/`、domain route、turn runner、worker lease 或 `runtime_lifecycle_store.py` 的存在写成 MAS 仍拥有 generic runtime；也不能反过来写成它们已经物理删除。
- 不能把 OPL `stage_production_evidence_receipt_record|verify` 写成 MAS production ready；它只是 expected receipt / monitor freshness 的 refs-only record/verify route。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 当前执行地图：[MAS 当前开发线路](./active/current-development-lines.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 过程归档：[MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)
