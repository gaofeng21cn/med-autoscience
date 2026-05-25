# 当前状态

**更新时间：2026-05-25**

Owner: `MedAutoScience`
Purpose: `current_truth_summary`
State: `active_current_truth`
Machine boundary: 本文是人读 current-state 摘要。机器真相继续归 `agent/` pack、`contracts/`、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace artifact、owner receipt 和 generated artifact proof。

## 当前角色

`Med Auto Science` 是医学研究 domain agent，也是 OPL-compatible package。单一 MAS app skill 是 direct path 的稳定入口；经 OPL 托管时，OPL/Temporal 是默认 hosted autonomous runtime，承载 stage attempt、queue、wakeup、retry/dead-letter、resume、human gate transport、generated surface、projection 和 App/workbench shell。Codex App 只承担 direct entry / 人机操作面，不作为任务启动后的外围持续 driver。

MAS 持有医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body/writeback decision、artifact/package authority、source readiness、owner receipt、typed blocker 和 safe action refs。OPL 不写 MAS study truth、memory body、publication verdict、artifact authority 或 `current_package`。

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能通过 OPL 显式接入，并只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不是 MAS 默认 backend。

历史 MAS-local scheduler/backend、runtime lifecycle/SQLite、workspace wrapper 和 alias 材料只在 `docs/history/**`、explicit archive/import reference 或 parity oracle 语境读取；当前默认面是 OPL/Temporal hosted runtime 加 MAS domain authority refs、owner receipts、typed blockers 和 minimal authority functions。

## 当前机器事实

- `agent/` 是 canonical medical research semantic pack：`prompts/`、`stages/`、`skills/`、`quality_gates/`、`knowledge/` 持有医学研究 stage / prompt / skill / quality / knowledge 语义。
- `contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是 OPL handoff、generated surface、functional boundary 与 production acceptance 的主要机器面。
- Direct MAS app skill path 与 OPL-hosted path 共享同一 MAS-owned stage、controller、durable truth、quality verdict 和 artifact surface。
- OPL generated / hosted surfaces 可以生成或托管 CLI / MCP / Skill / product-entry / status / workbench descriptor，并 dispatch allowlisted MAS task；它们不能写 MAS study truth、publication-route memory body、AI reviewer verdict、publication verdict、artifact authority、source body 或 `current_package`。
- Workspace/file lifecycle 已按 repo-source 与 live/runtime 写集分层：开发 checkout 只承载 semantic pack、机器合同、authority-function descriptor/receipt refs、domain handler/native helper 和人读治理；真实 workspace state、runtime artifact、receipt instance、paper/package/export artifact 和临时 build/cache/venv/pycache/pytest cache/install sync 副产物必须进入受控 study workspace/runtime artifact root 或用户级 runtime state。
- `DEFAULT_MANAGED_RUNTIME_BACKEND_ID` 已切到 `opl_provider_backed_stage_runtime`；`runtime_backend_default_operation_contract`、product-entry manifest 与 sidecar export 声明默认 generic runtime owner 为 `one-person-lab`，默认 backend 为 `opl_provider_backed_stage_runtime`。`runtime_backend_default_operation_contract.default_autonomous_runtime`、`provider_topology.default_autonomous_runtime`、`managed_temporal_state_consistency.default_autonomous_runtime` 与 `opl_unique_control_plane_handoff.default_caller_policy` 共同声明：hosted autonomous runtime 默认启用，provider 为 `temporal`，wakeup/retry/resume owner 为 OPL，`codex_app_outer_driver_required=false`，`mas_daemon_scheduler_attempt_loop_allowed=false`。
- `standard_agent_purity` 是 current product-entry / sidecar / read-model 默认口径：MAS 以 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions + refs-only domain projections` 暴露。
- `study_progress` parked operator projection、manual-hold intake、auto runtime parking 与 autonomy state surface 的当前用户可见 owner 文案已收薄到 MAS / OPL runtime owner；MDS / DeepScientist 名称只保留在 source provenance、historical fixture、explicit archive import、backend audit、upstream learning、parity oracle 或旧状态输入测试语境，不作为当前执行主体。
- MAS stage control plane 已为 6 个 runtime-guard stage 声明 `trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs`；stage cohort-loop refs 也已声明 source scope、cohort query、OPL queue trigger、monitor 和 dashboard metric refs。
- `contracts/production_acceptance/mas-production-acceptance.json` 只承认 structural / physical conformance 与 production-like receipt chain；它不授权 domain ready、publication ready、medical ready、artifact mutation 或 `current_package` 更新。
- owner-route / runtime handoff 当前固定为 body-free refs-only 交接：MAS 发布 controller authorization、domain route、owner receipt、typed blocker、current work-unit refs 和 authority boundary；OPL runtime manager 负责 liveness、queue hydration、attempt retry、dead-letter、provider resume/relaunch 和 operator status projection。MAS 不写 generic runtime queue，不把 OPL attempt 状态当 MAS study truth。
- `domain-action-request-materialize` 现在可从当前 `quality_repair_batch_writer_handoff` owner request 恢复 default-executor dispatch：当 generic runtime-owner route 与 writer handoff request 共享同一 truth/runtime/source/work-unit currentness，且 request 明确 bridge 自当前 owner route，materializer 会重建 write-owner story-surface dispatch，保留 canonical manuscript allowed-write contract。该能力用于 DM002 `dm002_same_line_display_table_package_repair` 类 story-surface route-back，仍禁止 package、publication eval、controller decision 或手工 study truth mutation。
- `sidecar export` 的 `domain_route/reconcile-apply`、`paper_autonomy/guarded-apply`、`publication_aftercare/*`、`domain_owner/default-executor-dispatch` pending task 和 stage-level owner handoff 已提供 `domain_dispatch_evidence_record_payload`。该 payload 只携带 MAS-owned typed blocker refs、owner-chain refs、no-regression evidence refs、identity fields、OPL 可记录的 receipt hint、success / typed-blocker payload path 与可直接提交给 `opl runtime action execute` 的 refs-only payload；typed blocker ref 与 ledger hint 保留 stage/source identity token，避免同类 stage attempt 在 refs-only ledger 中碰撞；`domain_owner_receipt_refs` 为空时只表示 owner receipt 尚未产生，不可读成 paper closure。
- owner-route 控制层已收敛为 `mas-owner-route-attempt-protocol.v1`：owner route 统一携带 reason registry、priority lattice、currentness contract 与 `owner_route_currentness_basis`；未注册 reason 或缺 work-unit/truth/runtime/source fingerprint 的 dispatch fail closed，不进入 OPL pending task。该协议只授权 OPL queue/attempt/provider/read-model transport；OPL provider completion 不等于 MAS owner receipt、AI reviewer pass、package freshness 或 submission authorization。
- `paper_line_guarded_apply_evidence` 和 `body_free_evidence_packets` 已作为 OPL-ingestable body-free ref packet 固化，可暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、stable typed blocker 和 no-forbidden-write refs；真实 closeout 仍需要 MAS owner receipt 或 stable typed blocker。
- runtime storage maintenance 的 workspace audit、study-bound maintenance 与 orphan quest maintenance 报告已携带 `mas_runtime_storage_refs_only_adapter_boundary` payload；该 payload 只声明 workspace/storage refs、cleanup receipt refs、restore proof refs、storage size refs 和 typed blocker，不能声明 generic cleanup policy、restore ready、publication ready、paper closure、artifact mutation authorization，也不能写 `publication_eval/latest.json`、`controller_decisions/latest.json` 或 `current_package`。
- Portal pause/resume/stop、submission milestone parking、controller refresh/current authorization 与 `study_progress` 当前都按 OPL runtime-owner handoff / read-only progress projection 读取。它们只能暴露 runtime owner route request、proposed runtime-state delta、current domain transition、owner refs 或 typed blocker；不直接调用 MAS generic runtime control，也不生成 provider attempt。
- `family_action_catalog` 的 read-only `study_state_matrix` action 只物化 MAS-owned transition matrix / spec / cases，供 OPL generic `family-transition-runner` 消费；它不写 study truth、不执行 domain action、不授权 publication quality / submission readiness，也不会作为 public MCP runtime tool 暴露。
- hard-methodology callable routing 已收口到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。该路径只产出 unit-harmonized rerun evidence 或 MAS-owned typed blocker，不落回 generic runtime/control-plane，也不写 paper、publication eval、controller decision、submission package 或 submission readiness。
- [MAS Stage / Route / Handoff 标准](./runtime/stage_route_handoff_standard.md) 是当前 route/stage 读法：stage 为 OPL provider-backed attempt admission 单位，route 为 MAS domain transition / owner-chain recommendation，handoff 为 body-free refs-only 交接包。指定杂志后的格式整理应进入 `finalize_and_publication_handoff` stage 下的 `journal-resolution` / `finalize` route transition，由 OPL stage graph 调度 journal requirement、format delta、artifact authority、independent review 和 submission handoff 子节点。
- submission-target 输入当前只接受 canonical `exporter_profile`；`publication_profile` 继续只作为已解析 package/export profile 输出字段和 submission manifest 领域字段存在。

## 当前功能/结构状态

当前 MAS 源码形态已按标准 OPL Agent 收口为三类长期 surface：

| 类别 | 当前口径 |
| --- | --- |
| `declarative_medical_pack` | `agent/` 和 contracts 声明医学 stage、prompt、skill、knowledge、quality gate、action catalog、receipt refs 和 forbidden authority boundary。 |
| `opl_generated_hosted_surfaces` | OPL 承担 generated / hosted CLI、MCP、Skill、product-entry、sidecar、status、workbench、projection shell、attempt、queue、retry/dead-letter、watch shell、generic state-machine runner、locator/index/lifecycle 和 operator workbench。 |
| `minimal_authority_functions` | MAS 保留医学 study truth、publication/source/memory/artifact verdict、AI-first record validator、owner receipt signer、typed blocker materializer、safe action refs 和 body-free domain authority refs。 |

当前已关闭的结构 gate 是：

| gate | 当前口径 |
| --- | --- |
| `generated_surface_default_owner_cutover` | OPL generated / hosted surface 与 MAS domain handler target 边界已闭合；MAS hand-written shell 只承担 direct domain entry、domain handler、AI-first validator、owner receipt signer、diagnostic refs 或 provenance fixture。 |
| `domain_authority_refs_thinning` | storage、artifact、memory、source、owner-route 和 status helper 只输出 refs、receipts、blockers 或 locators。 |
| `runtime_storage_refs_only_adapter_boundary` | runtime storage maintenance live reports 已输出 refs-only adapter boundary；MAS 只暴露 storage refs、size refs、cleanup/restore receipt refs 与 typed blocker，不持有 generic cleanup policy、restore readiness、paper closure 或 artifact mutation authority。 |
| `standard_agent_purity` | current product-entry、sidecar、status/read-model 默认只暴露标准 OPL Agent 口径、domain refs、owner receipts 和 typed blockers。 |
| `opl_app_workbench_drilldown` | MAS route/source/quality/artifact/memory/blocker/action refs 已作为 OPL App/workbench drilldown 输入；MAS 不复制通用工作台 owner。 |
| `family_transition_materialization_handoff` | MAS 只暴露 read-only `study_state_matrix` materialization；OPL 负责消费 spec/cases 并执行 generic transition matrix runner。MAS 不持有 generic state-machine runner，也不把 matrix pass 写成 publication / submission ready。 |
| `hard_methodology_callable_routing` | HDL/unit harmonization 与 grouped calibration 这类 hard-methodology work unit 已路由到 `analysis_harmonization_owner` authority callable；MAS 只保留医学方法学 owner evidence / typed blocker，generic runner 与 App/workbench shell仍归 OPL。 |

这些 gate 的关闭不等于真实 paper closure、publication-ready、artifact mutation authorization、provider long-soak 或 workbench / sidecar / status domain-ref shell default caller cutover。

## 当前测试/证据差距

以下是后续真实 paper-line / workspace scaleout 验证范围，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization，也不作为结构标准化缺口计数：

- 真实 paper-line provider apply：OPL provider -> MAS sidecar -> MAS owner chain 在真实论文线上留下 attempt query、typed closeout、MAS owner receipt，并暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、stop-loss 或 stable typed blocker。
- owner-chain dispatch ledger scaleout：`domain_dispatch_evidence_record_payload` 已显式输出 OPL owner-payload group 可消费的 `domain_owner_receipt_refs`、`owner_chain_refs`、`no_regression_evidence_refs`、`typed_blocker_refs`、return shapes 和 payload paths；仍需更多真实 owner-route / guarded-apply / aftercare / default-executor / stage-level handoff 被 OPL identity preflight 与 refs-only ledger 持续消费，并在 mismatch 时 fail closed。
- owner-chain body-free packet scaleout：当前 canary closeout 与 provider-hosted guarded-apply dispatch receipt 已能输出标准 `body_free_evidence_packets`，仍需真实 paper-line canary 持续产出 owner receipt、stable blocker、artifact/memory/human-gate receipt 与 no-forbidden-write proof。
- publication-route memory receipt scaleout：更多真实 paper line 产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 按 refs 检索。
- artifact lifecycle receipt scaleout：真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded receipt、rebuild/freshness proof 或 typed blocker。
- human gate / resume：approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。
- provider SLO long soak：长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。
- family transition live receipt：`study_state_matrix` / OPL generic matrix runner 的 route/work-unit 能进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。
- stage graph / route-as-transition proof：OPL 已有承载 route-as-transition 的 stage graph / transition runner / provider attempt 基础面；MAS 仍需用真实 paper-line 与指定 journal 格式整理 canary 回填 owner receipt、artifact authority receipt、independent reviewer/auditor record、human gate 或 stable typed blocker。

## 当前源码形态收口

MAS repo 本身已收敛为标准 OPL Agent 的源码形态。当前 docs、contracts、source 和 tests 只保护当前标准 Agent 边界：declarative pack、OPL generated/hosted surfaces、minimal authority functions、domain authority refs、owner receipt、typed blocker 和 refs-only evidence。

本轮不触碰真实 study workspace artifact、paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body。

真实 paper-line provider apply、publication-route memory receipt、artifact lifecycle receipt、human gate/resume、provider SLO long-soak 和 App/operator drilldown 仍是测试/证据差距。它们不改变当前源码形态已收口的结论，也不能被 repo tests 或 descriptor conformance 写成 publication-ready、paper closure、artifact mutation authorization 或 `current_package` 更新。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能声明 MAS production acceptance receipt 等于具体论文线 publication-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 descriptor ready、conformance passed、classification closed、provenance proof 或 selected proof 写成 production ready、paper closure 或物理源码清零。
- 不能把 OPL `stage_production_evidence_receipt_record|verify` 写成 MAS production ready；它只是 expected receipt / monitor freshness 的 refs-only record/verify route。
- 不能把 MDS/DeepScientist、non-default executor proof lane 或 workspace archive 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 当前执行地图：[MAS 当前开发线路](./active/current-development-lines.md)
- Runtime 边界：[Runtime boundary](./runtime/contracts/runtime_boundary.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 过程归档：[MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)
