# MAS 理想目标态

Owner: `MedAutoScience`
Purpose: `north_star_reference`
State: `active_support`
Machine boundary: 本文是人读目标态参考。机器可读真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-21`

## 文档读法

- 本文只写 MAS 的 north-star 目标态和长期 owner boundary；当前差距、实施顺序和验收缺口回到 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)。
- dated 过程校准、follow-through 和 closeout 证据归档到 [MAS standard agent 文档过程归档 2026-05](../../history/program/mas-standard-agent-doc-process-history-2026-05.md)，不在本文承担 current truth。
- 理想目标态高于当前实现。当前 MAS 内已经存在的 controller、scheduler、SQLite/lifecycle、workspace/source intake、memory/artifact transport、Portal/workbench、CLI/MCP/Skill/product-entry/sidecar/status wrapper 都只能作为迁移输入，不是长期架构约束。
- 理想目标态不包含兼容旧 MAS/MDS 平台面的义务。旧模块、旧接口、旧测试、旧文档入口和旧 CLI / wrapper / facade 在 replacement proof 与 no-active-caller proof 成立后直接清理；需要历史脉络时只保留 history/tombstone/provenance refs，不保留可调用兼容入口。

## 结论

理想状态下，`Med Auto Science` 是医学研究与医学论文交付的完整 domain agent。它能从研究问题进入同一条 study line，持续管理 workspace 语境、证据、分析、写作、审阅、投稿准备、运行状态、human gate、交付包和事后记忆，直到给出可审计的 artifact delta、quality verdict、publication route、submission package 或明确 blocker。

MAS 的核心价值是医学研究知识、研究路线、stage 语义、AI-first quality verdict、publication authority、artifact authority、memory writeback decision 和 owner receipt。MAS 的理想形态是：

`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal medical authority functions`

MAS 不应长期维护一套独立 agent runtime platform。通用 scheduler、queue、attempt ledger、generic transition runner、memory/artifact locator、lifecycle/restore/retention shell、observability/SLO、CLI/MCP/Skill/product-entry/sidecar/status wrapper 和跨 domain App/workbench shell 应由 OPL Framework / One Person Lab App 承载或生成。

Direct MAS app skill path 仍是一等入口。经 direct path 或 OPL-hosted path 调用时，都必须回到同一套 MAS-owned stage、controller、ledger、review、quality gate、domain transition table、publication-route memory 和 artifact surface。

MAS 的理想物理源码形态也必须表达这个边界。`agent/` 是医学研究语义包；`contracts/` 是机器合同和 OPL handoff；`runtime/authority_functions/`、`src/med_autoscience/**` 或测试夹具中长期保留的程序面只能是 medical authority function、domain handler、refs-only adapter、native helper、diagnostic probe 或 fixture。`supervisor`、`supervision_scheduler`、`runtime_supervisor_*`、`runtime_transport`、`worker lease`、`turn runner`、`lifecycle_refs_adapter.py` 这类名称不能长期让源码读者误以为 MAS 拥有 generic runtime / queue / scheduler / worker residency / persistence engine。当前若这些文件仍存在，理想处理是 rename、split、delete、archive 或 tombstone 到医学语义角色：domain route projection、owner action request、authority receipt dispatch、typed blocker reconcile、lifecycle refs adapter 或 diagnostic provenance。

`analysis_harmonization_owner`、`source_provenance_owner`、`provenance_limited_harmonization_owner` 等 hard-methodology callable 是 MAS 可长期保留的 medical authority functions。它们的存在是为了产出医学方法学 evidence、owner receipt 或 typed blocker，不能被包装成 MAS 私有 generic runner、queue、attempt ledger、state-machine engine 或 App route；OPL 只负责 provider、queue、attempt、generic runner、projection 和 workbench shell。

## 长期 Owner 边界

MAS 持有：

- 医学研究 truth：study charter、research question、population/outcome/timepoint、analysis plan、source asset refs、evidence ledger 和 review ledger。
- 医学 stage pack：`scout`、`idea`、`baseline`、`experiment`、`analysis-campaign`、`write`、`review`、`finalize`、`decision`、`journal-resolution` 的目标、知识、prompt/skill、tool refs 和输出义务。
- AI-first quality gate：AI reviewer rubric、auditor record、publication gate policy、reporting guideline、display-to-claim map 和 route-back decision。
- Domain transition table：publication supervisor state、completion receipt consumption、human gate、stop-loss、memory writeback receipt、artifact delta、owner apply receipt 和 fail-closed blocker 如何转换成 next owner/action。
- Publication-route memory：memory body、检索策略、accept/reject/blocker decision、writeback receipt 和后续 stage 小集合读取。
- Artifact authority：canonical manuscript、figures/tables、submission/current package、delivery freshness、artifact mutation permission、restore/rebuild proof。
- Owner receipts：stage closeout、quality verdict、artifact delta、human gate response、stop-loss、memory writeback receipt、typed blocker 和 safe action refs。

OPL 持有：

- provider-backed workflow、worker residency、attempt start/query/signal、queue、retry/dead-letter、human gate transport、attempt ledger 和 framework receipt。
- generic state-machine runner、transition matrix runner、lifecycle/index、memory/artifact locator、restore/retention shell、observability/SLO、repair projection 和 App/workbench shell。
- generated runtime-facing adapter / projection：CLI、MCP、Skill、product-entry、sidecar、status、workbench、projection 和 test-lane harness 的通用 wrapper。

OPL 只执行 MAS 声明的 spec、attempt、receipt、retry/dead-letter 和 human-gate transport，不解释医学质量、不改写 MAS study truth、不读取 memory body、不签发 artifact authority、不声明 publication ready。

## AI-first Quality Gate

理想 MAS 的质量门必须由 AI-first stage quality chain 关闭。executor agent 可以执行分析、写作、修复或交付任务；reviewer/auditor agent 必须独立调用，读取 executor 产出的 artifact/source/evidence refs，并留下独立 context、task record、review/audit receipt。

MAS 程序只承担机械职责：

- 校验输入输出 schema、provenance 和 authority refs。
- 持久化 AI-first 质控结果到 durable surface。
- 签发 owner receipt、typed blocker、safe action refs 和 no-forbidden-write proof。
- 阻止 OPL/App/provider 越权写 MAS truth、memory body、publication verdict 或 artifact authority。

程序不得用规则、regex、固定分支或 legacy_restore_import 直接替代 AI reviewer / Quality OS 的医学判断。同一 agent 的自审不能关闭 AI-first quality gate。

## Stage 是医学专家工作的组织单元

理想 MAS stage 接近真实医学研究团队完成一个阶段工作的最小大步骤。每个 stage 都应有明确目标、输入、知识、工具、质量门槛、输出和 closeout。

每个 stage 至少声明：

- `goal`：本阶段要完成的医学研究目标。
- `inputs`：study charter、source refs、workspace locator、上游 artifact refs、用户约束和 previous closeout。
- `knowledge_refs`：publication-route memory、literature refs、policy refs、quality packs、stage-specific method notes。
- `tool_refs`：MAS CLI/MCP/controller surface、analysis helpers、artifact rebuild tools、Office/PDF/browser/native helper 等可审计入口。
- `executor_requirements`：默认 `Codex CLI`；其他 Agent executor 只能显式接入并保留 non-equivalence notice。
- `quality_gates`：AI reviewer、auditor、reporting guideline、publication gate、evidence/review ledger、stage deliverable review。
- `outputs`：artifact delta、stage closeout、memory writeback proposal、owner receipt、human gate、stop-loss 或 typed blocker。
- `handoff`：下一 stage、next owner、resume token、safe action 或 reviewer route-back。
- `cohort_loop_refs`：source scope、auditable cohort query、OPL queue trigger、monitor 和 dashboard freshness metric refs，用于 OPL 在不拥有医学 truth 的前提下判断 stage 是否具备可触发、可观察的闭环声明。

## 理想工作台边界

理想用户工作台面向医生、PI、研究团队和维护者。OPL App / workbench 承担主产品面，MAS 提供 domain-owned projection、route map、stage/review/artifact refs、memory receipt refs、quality/source refs 和 safe action receipts。

工作台应展示：

- `Study Line`：研究问题、当前阶段、owner、paper progress、next action 和 human gate。
- `研究路线地图`：阶段、路线、决策、阻塞、产物、执行回合、改道/替代和产物关系。
- `路线/决策轨迹`：失败路径、阻塞原因、转向理由、superseded path、active/winning path 和 source refs。
- `Evidence`：source refs、evidence ledger、analysis outputs、claim-to-display map 和 freshness。
- `Review`：AI reviewer verdict、stage review page、review ledger、publication blocker 和 route-back。
- `Artifacts`：canonical manuscript、figures/tables、package freshness、delivery refs、restore proof。
- `Runtime`：provider attempt、retry budget、SLO drift、safe repair command 和 typed blocker。
- `Memory`：publication-route memory consumed refs、writeback receipt refs、stale/deprecated review summary 和 grouping。
- `Actions`：只暴露路由到明确 owner 的 safe action，每次 action 必须返回 MAS owner receipt、provider receipt 或 typed blocker。

工作台不得把 UI 状态、provider completion、read-only projection 或 observability finding 写成 quality ready、submission ready 或 publication ready。

## 理想完成门槛

MAS 达到生产级目标态时，应满足：

- Direct MAS app skill path 与 OPL-hosted path 使用同一 MAS owner surfaces，并有语义等价与 forbidden-write 证据。
- 通用 runtime、queue、memory locator、artifact lifecycle、restore/retention、projection、workbench shell 和 generated entry/status wrapper 已上收到 OPL / shared family layer；MAS 保留领域知识、authority、owner receipt、声明式 pack 和 minimal authority functions。
- OPL generated / hosted surfaces 完成 active caller cutover；MAS 旧手写 shell 只保留 direct domain entry、domain handler、authority function、diagnostic cleanup 或 provenance fixture。
- MAS 非知识代码均能归类为 declarative pack / generated surface handoff、refs-only adapter、minimal authority function 或 legacy cleanup no-active-caller gate，并完成对应 cutover、收薄或退役；已物理退役的旧面必须另有 tombstone/provenance refs、forbidden-caller proof 和 `physical_retired` 机器标记。
- MAS cleanup 证据必须区分 OPL refs-only ledger 与 MAS repo 物理删除：OPL `agents legacy-cleanup apply` 的 dry-run / apply / verify ready 只证明 MAS tombstone / replacement / no-regression refs 可被 OPL 消费，不等于 tracked runtime transport、supervisor 或 SQLite refs index 已物理清零。
- 默认 managed runtime backend 必须是 OPL-owned provider surface，例如当前 `opl_provider_backed_stage_runtime`。`mas_runtime_core`、runtime supervisor、turn runner、worker lease 与 runtime lifecycle SQLite 的长期角色只能是 `runtime_backend_is_generic_owner=false` 的 delegated domain adapter / owner receipt / typed blocker / refs-only sidecar / diagnostic surface。它们不能重新声明 MAS-owned generic runtime、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 或 workbench owner。
- runtime-guard stage descriptor 明确声明 machine-readable `trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs`，OPL proof bundle / admission 能把 route decision、baseline/evidence readiness、analysis evidence closure、draft reviewability、AI reviewer gate receipt、publication handoff 和 replay/audit event refs 读成可组合合同，而不是只靠人读 stage 文案。
- stage descriptor 明确声明 source scope、cohort query、OPL queue trigger、monitor 和 dashboard metric refs，OPL `stages cohort-loop` 能把每个 stage 读成 closed-loop ready；这只证明 launch/readiness 声明闭合，不替代真实 provider attempt、paper-line owner receipt 或 memory/artifact apply evidence。
- OPL App/operator 能把 stage expected receipt / monitor freshness 缺口转成 refs-only `stage_production_evidence_receipt_record|verify` route，并提供 payload workorder / preflight；OPL production closeout 能在缺口出现时把 missing workorder 按 domain/stage 聚合成 `stage_evidence_workorder_packet` 供审计。MAS 只提供真实 owner receipt instance、typed blocker、no-regression、memory/artifact/human gate 或 long-soak refs，不维护私有 stage evidence ledger 或通用 App route，不把声明型占位 ref、OPL ledger receipt ref、workorder packet 或 body payload 当作成功证据。
- 每个 stage 都应能被 Codex CLI default executor 直接启动：stage descriptor 必须投影 `codex_cli_launch_packet`，包含 prompt refs、skill/tool refs、knowledge refs、quality gate refs、expected receipt refs、forbidden authority 与 `executor_requirements=Codex CLI`。该 packet 只给执行器搭台、声明边界和证据义务，不用脚本替代医学判断、AI reviewer/auditor gate、publication verdict、artifact authority 或 source readiness。
- Pack compiler input 只能用 `canonical_semantic_pack_root="agent/"` 和 `canonical_semantic_pack_role` 表达 canonical semantic pack；旧 `canonical_repo_source_semantic_pack_root` / `domain_pack_root` / `canonical_repo_source_semantic_pack` 不再作为机器接口。`required_domain_pack_paths` 只列真实语义文件，不能把 `agent/README.md` 这类人读入口当作 required semantic pack path。
- `lifecycle_refs_adapter`、`runtime_storage_maintenance` 和 `terminal_attach_transport` 若仍在源码中存在，长期角色只能是 refs / receipts / blockers / provenance adapter：它们不得输出 generic runtime verdict、generic cleanup policy、generic terminal owner、paper closure verdict 或 MAS-owned lifecycle/persistence/workbench owner claim。
- OPL standard conformance gate 必须保持通过。2026-05-19 fresh family defaults 已显示 MAS structural conformance `passed`；这只证明标准源码形态、generated owner、private generic-owner guard 和 active path scan 被 OPL 接受，不替代真实 paper-line provider evidence、App consumption、owner receipt scaleout 或 active-source physical deletion/tombstone gate。
- Production acceptance 必须有 MAS-owned evidence surface。当前 surface 是 `contracts/production_acceptance/mas-production-acceptance.json`，它把 conformance 后的 `production_live_soak_not_claimed_by_conformance` / `domain_ready_not_claimed_by_conformance` 收口为 MAS owner receipt 或 typed blocker。该 surface 只能承认 structural / physical conformance 与 production-like receipt chain；OPL/provider completion 不能授权 domain ready、publication ready、medical ready、artifact mutation 或 `current_package` 更新。
- Real paper-line canary 的成功标准必须是 `mas_real_paper_line_provider_canary_closeout` 返回 MAS owner receipt 或 stable typed blocker；provider completion、Agent Lab suite pass 或 meta-agent work order 只可作为证据输入。OPL-ingestable surface 只能使用 `paper_line_guarded_apply_evidence` / body-free evidence packet refs，不包含 study truth、quality verdict、artifact body、memory body 或 `current_package`。
- Publication-route memory、artifact lifecycle、human gate/resume 和 provider SLO evidence 必须以 body-free packet 进入 OPL / Agent Lab：packet 只能包含 `ref`、`role`、`freshness`、`owner`、`receipt_id` 和 `no_forbidden_write_proof`。accepted/rejected/blocked memory writeback、artifact mutation/restore/retention、human gate resume 与 long-soak 都不能携带 body 或授权越权写。
- Generated/default caller retirement 必须有机器 proof：`generated_default_caller_boundary` 与 `physical_retirement_gate_matrix` 应列出 hand-written surfaces 的剩余合法角色、active caller proof、OPL parity、MAS receipt parity、focused tests、tombstone refs 和 no-forbidden-write 证据。没有这些 proof 时，只能写成 retained domain adapter / diagnostic / tombstone，不能写成已删或可长期保留为 generic runtime。
- 当前 `classification_gap_count=0`、`active_private_generic_residue_count=0` 与 `functional_structure_gap_count=0` 必须由机器面确认。结构闭合来自 generated surface active caller cutover、refs-only adapter 收薄、legacy physical retirement、OPL App drilldown、lifecycle locator/retention/restore ledger 对账和 runtime-guard stage admission 的 closure proof refs；live paper-line evidence scaleout 是结构门之后的测试/证据门，不能被 descriptor ready、replacement proof 或 repo tests 替代。
- 每个真实 paper-line stage attempt 都留下 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。
- Publication-route memory 在多个真实 paper line 上产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 小集合检索。
- Artifact lifecycle、retention、cleanup、restore proof 和 SQLite/file authority 边界在真实 workspace 中可运行。
- Human gate/resume、explicit wakeup、retry/dead-letter、provider SLO long soak 和 no-forbidden-write 在真实 provider-hosted run 中持续成立。
- Legacy MDS/Hermes/local/default-compat residue 完成 no-active-caller scan、replacement proof、history/provenance 分类与 physical retirement；不保留兼容别名。
- One Person Lab App 的 managed-environment startup maintenance 由 OPL `system startup-maintenance` 与 App shell 自动调用承担；MAS 不再持有本机 LaunchAgent、daemon 或 module maintenance owner。

## 当前差距入口

当前功能/结构差距、测试/证据差距、完善顺序和禁止误写口径由 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 维护。本文不双写 active plan。
