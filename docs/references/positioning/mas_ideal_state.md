# MAS 理想目标态

Owner: `MedAutoScience`
Purpose: `north_star_reference`
State: `active_support`
Machine boundary: 本文是人读目标态参考。机器可读真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-16`

## 文档读法

- `定位`：本文只写 MAS 的 north-star 目标态和长期 owner boundary；当前差距、实施顺序和 P0 项回到 `mas-ideal-state-gap-plan.md`。
- `当前实态校准`：带日期的校准段只记录当前代码或 live evidence，不把目标态写成已完成事实。
- `Owner 边界`：MAS 持有医学研究 truth、publication quality、artifact authority、memory body/writeback decision、domain transition table 和 owner receipt；OPL 持有 scheduler、queue、attempt ledger、memory/artifact locator、generic runner、provider SLO 和 App/workbench shell。
- `目标态优先`：MAS 当前已经存在的 controller、scheduler、SQLite/lifecycle、workspace/source intake、memory/artifact transport、Portal/workbench、CLI/MCP/product-entry/sidecar/status wrapper 只能作为迁移输入，不是理想态约束。理想 MAS 是标准 OPL Agent：声明式 medical research pack + OPL generated/hosted surfaces + 最小医学 authority functions。
- `最短路径`：默认 scheduler owner 已迁到 OPL replacement；Portal/workbench 中的 generic runtime owner wording 已改成 OPL-owned consumer projection；显式 local scheduler / LaunchAgent legacy diagnostic path 已有 `default_caller_count=0` proof，只作为旧生成物 status/remove、provenance/fixture 和 drift guard 保留。
- `禁写口径`：MAS direct/local diagnostic path 可以存在，但不能写成 MAS 长期 generic runtime platform；OPL provider completion 也不能写成 MAS paper closure 或 publication-ready。
- `功能消费方边界`：MAS 目标态以 `Declarative Medical Research Pack + minimal authority functions` 消费 OPL generic scaffold、pack compiler、generic transition runner、memory/artifact locator、workbench shell 和 observability。MAS 默认提交医学 stage / policy / knowledge / schema / receipt contract；CLI/MCP/product-entry/sidecar/status/workbench 等通用外壳由 OPL 生成或托管，不复制通用 scheduler、daemon、queue、attempt ledger、runner 或工作台。

## 结论

理想状态下，`Med Auto Science` 是医学研究与医学论文交付的完整 domain agent。它能从研究问题进入同一条 study line，持续管理 workspace 语境、证据、分析、写作、审阅、投稿准备、运行状态、human gate、交付包和事后记忆，直到给出可审计的 artifact delta、quality verdict、publication route、submission package 或明确 blocker。

MAS 的核心价值不是维护通用 agent runtime、通用 memory service、通用 artifact lifecycle 或通用用户工作台，而是持有医学研究知识、研究路线、stage 语义、quality verdict、publication authority 和 artifact authority。`OPL Framework` 提供 stage-led、provider-backed、可恢复的外层运行框架，以及尽量可复用的 queue、wakeup、attempt ledger、memory locator、artifact lifecycle、projection 和 workbench shell；MAS 作为 admitted medical research domain agent 暴露 stage descriptor、sidecar、receipt、artifact locator、projection 和 authority refs。经 OPL 托管运行或通过 MAS app skill 直接调用，最终都必须回到同一套 MAS-owned stage、controller、ledger、review、quality gate 和 artifact surface。

因此，MAS 的理想形态是医学研究 `Declarative Medical Research Pack + minimal authority functions`，不是一套独立 agent runtime platform，也不应长期手写一层可由 OPL 派生的薄程序面。MAS 可以保留 direct/local diagnostic path 和 MAS-owned controller truth，但 generic scheduler、generic queue、generic attempt ledger、generic memory locator、generic artifact lifecycle、generic state-machine runner、generic workbench shell、observability/SLO、CLI/MCP/product-entry/sidecar/status wrapper 和跨 domain App projection 都应由 OPL Framework / One Person Lab App 承载或生成。MAS 的 descriptor、contract/schema、domain transition spec/table、quality gate、artifact locator、receipt schema、tests 和 domain entry 只负责把医学 owner chain、typed blocker、owner receipt、artifact locator 和 domain transition spec 暴露给 OPL；手写 adapter/projection 只在无法声明化或仍处迁移桥时保留，并必须写明 `cannot_absorb_reason`。

这条目标态高于当前实现。当前 MAS 内已经能跑的通用 control loop、supervisor、local index、Portal、sidecar 或 product shell，不因为有 active caller 就被视为长期合理。后续可以为了标准 OPL Agent 形态革命式重构 MAS：将通用 transport、ledger、index、runner、workbench、lifecycle 和 wrapper 上收到 OPL primitive / pack compiler；将医学判断、质量裁决、artifact mutation、memory accept/reject、source readiness 和 owner receipt 收薄为最小 authority function；剩余旧面在 caller 迁移后直接退役。

如果某个医学流程当前必须保留程序面，应先证明它无法被 stage policy、transition table、schema、fixture、receipt contract 或 OPL generated surface 表达；保留接口必须只返回 MAS owner receipt、typed blocker、artifact/source/memory refs 或明确的 authority verdict，不得扩展成 MAS 私有运行平台。

状态转换也服从同一分层：通用 state-machine runner、transition schema、幂等 tick、retry/dead-letter、human gate transport、dispatch receipt 和 transition matrix runner 应进入 OPL / shared family layer；MAS 持有医学 domain transition table / transition matrix，定义 `publication_supervisor_state`、publication gate、AI reviewer、claim/evidence/display blocker、submission authority 和 artifact/package authority 如何转换成 `decision_type`、`route_target`、`next_work_unit` 与 `controller_action`。OPL 执行 MAS 声明的 transition spec，不能自行解释医学发表状态。

理想状态下，MAS 的 transition table 不只描述 stage 名称，还必须消费完成态。审稿回复 coverage 完成后应进入 bundle/finalize owner；mechanical projection 缺 AI reviewer provenance 时应回 AI reviewer；AI reviewer 已给出 blocked verdict 时应回 publication gate / bounded repair；owner handoff 已 terminal consumed 时不能被旧 runtime prompt 重新派发。每个状态转换都应有 oracle fixture 和 receipt/fingerprint 约束，避免同一论文线在同一 work unit 上重复运行数十小时。

2026-05-15 三篇真实论文线暴露的设计教训已经进入目标态约束：状态转换必须按 authority 和时间消费 durable completion / execution receipt。`publication_work_unit_lifecycle`、runtime turn closeout、package closure、AI reviewer-backed publication eval、default executor execution receipt 和 controller decision 都不能各自孤立成第二状态机；read model 必须把更高权威、更新的 receipt 消费成当前 next action。具体规则是：DM002 这类 bundle/finalize package closure 已完成时，旧 rebuttal coverage / finalize work unit 不能继续 redrive；DM003 这类更晚的 default executor execution 已回到 AI reviewer owner surface 时，旧 blocked turn closeout 不能继续投成 waiting_for_user；Obesity 这类 AI reviewer-backed publication gate blocked verdict 仍必须保持 bounded repair / gate-blocked 轨道，不能因泛化 finalize 逻辑越过 publishability gate。

2026-05-15 package-ready handoff 约束也进入目标态：submission authority、delivery signatures、current_package freshness 或更新的 delivery manifest 与 clear gate 同时成立时，MAS 应把 current_package / package zip 投成人工审阅或显式 resume 节点，并让较旧 reviewer_revision task intake 让位于该交付包 closeout。这个状态只表示“当前包已交给用户审阅”，不授权 publication closure、submission authority 或外部投稿。

human gate / resume 的目标态同样遵循 owner 分层：OPL 可以提供 approval signal、attempt query、transport、retry 和 human gate UI；MAS 必须把已批准、拒绝或 consumed 的 human gate response 归一成 controller-owned receipt，再由 transition table 消费成 next owner/action。仅有 OPL signal 不能恢复研究线；只有 MAS `controller_confirmation_summary` / controller decision 指向同一 gate 且允许的 resume action 成立时，才可从 human gate 转回 MAS runtime owner。

stop-loss / terminal stop 也必须是 MAS-owned receipt，而不是 provider completion 或泛化 retry 结果。无需 human confirmation 的 `controller_decisions/latest.json` stop-loss 应被 transition matrix 消费成 `mas_owner_stop_loss_receipt`，后续 action 是 honor terminal stop；带 human gate 的 stop-loss 继续停在 human gate，不能被自动消费。这个目标态避免旧 closeout、旧 prompt 或 OPL runner 把 MAS terminal stop 误恢复为自动继续。

publication-route memory writeback receipt 也属于 MAS-owned domain receipt，但它只证明 workspace memory owner 对 writeback 的接受、拒绝或阻塞状态，不证明论文质量、投稿授权或 artifact/package authority。transition table 只能消费 `memory_family=publication_route_memory`、带 writeback ref-chain 且有 accepted/rejected/typed blocker 的 router receipt，并把它投成 body-free refs/counts/blocker handoff；OPL/App 可以展示 locator、freshness、grouping 和 receipt refs，不能读取 memory body、接受/拒绝 writeback 或据此恢复 generic runner。

本文描述目标态，不替代当前状态判断。当前落地程度、生产证据缺口和开发顺序以 [当前状态](../../status.md)、[架构](../../architecture.md)、[MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)、[MAS 当前开发线路](../../active/current_development_lines.md) 与 [MAS AI-first Research OS Architecture](../mainline/ai_first_research_os_architecture.md) 为准。

OPL 系列项目的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`。本文只维护 MAS 自己的理想态、authority 边界和通用能力上收清单；MAS 当前差距和完善计划由 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 维护。OPL、MAG、RCA、MDS/DeepScientist 或 OPL-owned App/workbench 的具体完善计划回到各自 owner surface。

2026-05-14 当前差距可归纳为三类。第一，生产证据缺口：真实 provider-hosted paper apply、domain activity long soak、human gate/resume 和更多真实 memory writeback receipts 仍要由 live workspace / owner receipt 证明。第二，产品化缺口：OPL App / Workbench 需要把 MAS refs、stage review/index、route-memory refs、provider refs、safe action receipt 和 typed blocker 做成人用 drilldown。第三，历史残留缺口：旧 MDS/Hermes/local/default-compat surface 只要没有 active caller、public surface 引用或 fixture/provenance 必需，并且已有 replacement proof，就应直接删除源码、命令 wrapper 和对应测试，不再以兼容接口形式保留。

2026-05-16 校准：默认外层监管 owner 已迁到 OPL replacement。`src/med_autoscience/controllers/supervision_scheduler.py` 现在固定 `SCHEDULER_OWNER=opl_provider_runtime_manager`、`DEFAULT_MANAGER=opl`、`OPL_ADAPTER_ID=opl_family_runtime_provider`；CLI parser 默认 `--manager opl`；`workspace bootstrap` 委托 OPL replacement，不再默认安装 LaunchAgent；`contracts/test-lane-manifest.json` 的 `outer-supervision-slo` 明确 `default_scheduler_owner=opl_provider_runtime_manager`、`default_adapter_id=opl_family_runtime_provider` 和 `legacy_diagnostic_adapter_id=local_launchd_on_macos`。fresh CLI evidence 显示 `runtime-supervision-status --profile <tmp-profile>` 返回 `status=replacement_owner_active`、`scheduler_owner=opl_provider_runtime_manager`、`adapter_id=opl_family_runtime_provider`、`manager=opl`，且 legacy local adapter 当前 `status=not_installed`；默认 `runtime-ensure-supervision --dry-run` 返回 `action=delegated_to_opl_provider_scheduler` / `status=delegated`；显式 `runtime-ensure-supervision --manager local --dry-run` 返回 `action=retired_cleanup_only`、`status=blocked`、`reason=mas_local_scheduler_install_retired_use_opl_replacement`、`write_install_proof=false`，不生成 install proof、不写 tick script、不写 LaunchAgent plist、不触发本机 tick。显式 `--manager local` 只保留 status/remove cleanup，用来检查或删除旧本机 LaunchAgent / tick script；检测到旧生成物时 status 为 `retired_legacy_cleanup_required`，不会再投影 `loaded` 或 `scheduled`。理想终态要求周期唤醒、scheduler lifecycle、provider SLO、job registry 和通用 supervision cadence 继续由 OPL Framework / provider 层提供，MAS 只保留医学 owner route、paper progress SLO 语义、owner receipt、typed blocker、safe action 和质量/交付 authority。

2026-05-16 功能消费方校准：MAS 已把 `functional_consumer_boundary` 投影到 product-entry manifest、sidecar export 和 supervision consumer migration。该边界把 generic scheduler、daemon、queue、attempt ledger、generic runner、generic transition runner、generic workbench、memory locator、artifact lifecycle 和 observability 明确列为 OPL-owned / OPL-consumed surface；MAS 只保留 study truth、publication quality verdict、artifact authority、publication-route memory body、memory writeback decision、domain transition table、owner receipt、typed blocker 和 safe action refs。当前 `opl_functional_harness_consumer_coverage` 还把四条 harness 消费链固定成机器面：refs-only memory writeback chain、queue / stage attempt / typed closeout、generic transition runner、restart / dead-letter / repair / human gate state chain；同一 surface 明确 OPL harness pass 不是 paper closure、不是 publication ready，MAS 也不持有 generic runtime。`no_active_caller_proof.default_caller_count=0` 证明默认 CLI、workspace bootstrap、product-entry、sidecar 和 MCP 不再调用 local LaunchAgent install path；显式 local 只做 status/remove cleanup，并被禁止 install、trigger、loaded-state 或 install-proof 输出。这个 guard 是功能面 no-active-caller / test-lane / docs 证明，不替代真实 paper-line provider soak。

2026-05-17 functional privatization 校准：MAS 非知识层私有功能不再按“当前在 MAS repo 内实现”判断 owner，也不再长期标成 `opl_owned_replacement` 或 `retire_tombstone`。机器面现在由 `functional_consumer_boundary.functional_module_inventory` 持有代码路径级清单，共 18 项，覆盖 runtime lifecycle SQLite reference adapter、paper work-unit outbox index、runtime storage maintenance、workspace/source intake shell、publication-route memory locator/writeback transport、artifact lifecycle/storage audit shell、workbench/portal generic shell、terminal attach transport、runtime supervisor scan/consume/dispatch/reconcile shell、generic CLI/MCP/product wrappers、generic daemon/scheduler lifecycle、queue/attempt/retry/dead-letter、generic transition runner、MAS domain truth/quality/artifact authority，以及 legacy scheduler / workspace wrapper cleanup surfaces。当前分类计数为 `declarative_pack_generated_surface=7`、`refs_only_adapter=6`、`minimal_authority_function=3`、`legacy_cleanup_no_active_caller_gate=2`，长期 `opl_owned_replacement` 与 `retire_tombstone` 分类计数均为 `0`。legacy cleanup / tombstone 只是 no-active-caller gate 后的处置，不能作为长期功能 owner。`runtime_lifecycle.sqlite` 的理想角色因此是 MAS domain sidecar index / refs-only adapter，服务 OPL replacement audit 和 MAS receipt lookup，只消费 OPL lifecycle index refs，不写 MAS domain truth，不是 MAS generic persistence / lifecycle / restore-retention engine；`generic_persistence_engine`、`generic_lifecycle_engine`、`generic_restore_retention_owner` 已明确列为 MAS forbidden roles。

2026-05-17 MAS lane 语义等价校准：6 个功能面已经从“待上收/待 handoff”文案改成 owner 边界完成态。`runtime_storage_maintenance` 与 `artifact_lifecycle_storage_audit_shell` 只作为 refs-only adapter 输出 locator、audit、restore/retention receipt 和 artifact authority refs；`workbench_portal_generic_shell` 只向 OPL generated-hosted workbench 提供 MAS domain projection refs；`runtime_supervisor_scan_consume_dispatch_shell` 消费 OPL runtime manager loop，MAS 保留 owner-route guard、publication gate blocker、safe action refs 和 no-forbidden-write receipt；`generic_cli_mcp_product_wrappers` 由 declarative pack / OPL generated surfaces 派生 wrapper metadata，MAS 只保留 domain handler 与 owner receipt signer；`generic_queue_attempt_retry_dead_letter` 消费 OPL queue/attempt/retry/dead-letter/worker lifecycle transport，MAS 只保留 stage closeout semantics、recovery owner decision 和 owner receipt。它们不得再被写成 `active_private`、`pending`、`should_move`、`handoff_required` 或 `lifecycle_candidate`。

这意味着当前 MAS 并非“已经没有任何私有功能实现”。准确判断是：MAS 仍保有多处活跃 functional shell，但长期处置已被机器面限定为 declarative pack / OPL generated surface、refs-only adapter、minimal authority function 或 no-active-caller cleanup gate。SQLite/lifecycle store、paper outbox、storage maintenance、workspace/source intake、memory transport、artifact lifecycle、Portal/workbench、terminal/log projection、runtime supervisor scan-dispatch 和 CLI/MCP/product shell，只有在承载 MAS owner receipt、domain blocker、artifact authority、locator refs 或 cleanup diagnostic 时才允许留在 MAS；凡是 scheduler、queue、attempt ledger、state-machine runner、locator/index、lifecycle、workbench、observability 或 product shell 的通用部分，都应上收到 OPL pack compiler、App/runtime generated surface 或 refs-only adapter。

2026-05-17 consumer thinning closeout 校准：上述功能残留已经在 MAS 单仓机器面完成分类与清零。`functional_consumer_boundary.functional_gap_zero_summary` 固定 `functional_structure_gap_count=0`、`active_private_generic_residue_count=0`、`remaining_gap_classification=test_evidence_gates_only`。剩余 generated surface active caller cutover、真实 paper-line provider apply、publication-route memory receipt scaleout、artifact lifecycle receipt scaleout、OPL App drilldown 和 provider SLO long soak，均是测试/证据差距或 OPL/Operator evidence gate，不能重新写成 MAS 长期 generic owner 缺口。`local_launchd_scheduler_install_path` 与 `workspace_local_watch_service_wrappers` 不是 active private-function cleanup gap；它们只作为无默认入口、无标准模板引用的 cleanup diagnostic / provenance / drift guard。

完善顺序必须服从这一边界：功能分类与 handoff 机器面先清零，再用真实 paper-line、provider SLO、human gate/resume 和 App drilldown 做验收。live soak 证明迁移后的目标形态成立，不应成为 MAS scheduler 上收、Portal/workbench 边界清理或 OPL primitive handoff 的前置条件。

## 产品分层

MAS 的理想产品认知保持四层：

1. `MAS Domain Agent`
   面向用户和通用 agent 的医学研究入口。它承接研究问题、workspace、进度、human gate、论文文件和交付状态。
2. `MAS Domain Knowledge / Authority Pack`
   MAS 提供医学研究 stage pack、研究路线知识、publication-route memory policy、quality rubric、AI reviewer policy、artifact authority contract、owner receipt schema、domain transition spec 和 domain projection builder。它优先调用 OPL 提供的通用 runtime / state-machine / memory locator / lifecycle / workbench primitive，而不是在 MAS 内重复实现一套通用 OS。
3. `OPL Framework Integration`
   OPL 承担 stage attempt、queue、wakeup、retry/dead-letter、human gate transport、provider receipt、memory locator/index、artifact lifecycle、projection 和 shared lifecycle/index primitive。MAS 只暴露可托管边界，不把医学研究 truth、route choice、quality verdict 或 artifact authority 上收到 OPL。
4. `User Workbench`
   Codex App、OPL App、Progress Portal、Live Console 或其他 UI 只读消费 MAS projection、receipt refs、artifact refs、研究路线地图和 safe action receipts。用户界面不成为第二 runtime owner 或 publication authority。

目标链路如下：

```text
User / Codex App / MAS app skill / CLI / OPL App
  -> MAS entry surface
  -> MAS stage route and study owner surface
  -> Codex CLI or explicit Agent executor inside a stage
  -> evidence / analysis / manuscript / review / artifact work
  -> MAS quality gate / controller / artifact authority
  -> owner receipt, artifact delta, publication verdict, human gate, or typed blocker
```

经 OPL 托管时，外层链路增加 provider-backed attempt：

```text
OPL Framework
  -> stage attempt / queue / provider transport
  -> MAS sidecar dispatch
  -> MAS owner chain
  -> MAS owner receipt or typed blocker
```

## MAS Domain Agent 的理想职责

MAS 长期职责是把医学研究领域内的判断、证据、路线、质量和交付 authority 收口成可审计的 domain-owned surface。通用运行能力、通用 memory/index、通用 artifact lifecycle、通用 workbench shell 和 provider 运维能力应优先由 OPL 或 shared family primitives 实现；MAS 保留领域知识、领域 policy、owner receipt、quality gate、artifact authority、声明式 pack 和 minimal authority functions。当前仍存在的手写薄程序面只作为 MAS package 外壳和迁移桥，用于 OPL 发现、托管、审计和投影，不是通用平台，也不是长期默认实现形态。

2026-05-17 顶层设计收紧后，MAS package 外壳也不再被默认视为长期手写代码。当前机器面已在 `functional_consumer_boundary` 内新增 `declarative_pack_compiler_input`、`generated_surface_handoff` 和 `minimal_authority_function_manifest`：`study-state-matrix`、stage pack、publication-route memory policy、artifact authority policy、source readiness rule、receipt schema、family action/stage descriptor 与 no-forbidden-write contract 被声明为 OPL pack compiler 输入；CLI/MCP/product-entry/sidecar/status/workbench/projection shell/test-lane harness 被声明为 OPL generated/hosted surface 或 MAS handwritten migration bridge；MAS 长期只保留无法可靠声明化的医学 authority function：publication quality verdict、AI reviewer-backed quality decision、artifact mutation authorization、publication-route memory accept/reject、source readiness verdict、owner receipt signer 和必要的医学 helper implementation。当前状态是 handoff 机器面已落下，active caller cutover 与旧 shell 删除仍是后续迁移门槛。

### 职责边界

| 能力族 | 理想通用 owner | MAS 理想职责 |
| --- | --- | --- |
| Long-running runtime | OPL provider / OPL Framework | 声明 stage、owner route、allowed task、domain receipt 和 forbidden writes；接收 OPL dispatch 后回到 MAS owner chain。 |
| Queue / retry / dead-letter / human gate transport | OPL Framework | 给出 human gate 边界、resume 语义、stop-loss 语义和 domain blocker，不重复维护通用 transport。 |
| Memory locator / index / writeback transport | OPL shared primitive + MAS workspace owner surface | MAS 持有 publication-route memory 正文、领域检索策略、接受/拒绝规则和 writeback receipt；OPL 只持 locator、refs、freshness 和展示分组。 |
| Artifact lifecycle / restore / retention | OPL shared primitive + MAS artifact owner surface | MAS 持有 canonical manuscript/package authority、artifact mutation permission 和 rebuild proof；OPL 只处理 locator、restore/retention primitive 和 operator projection。 |
| Product workbench shell | OPL App / shared workbench | MAS 提供 per-study projection、研究路线地图、stage/review/artifact refs 和 action receipt；Workbench 只展示和路由，不裁决。 |
| Observability / diagnostics | OPL/shared observability + MAS read models | MAS 提供 domain blocker、quality/source refs、runtime health facts 和 safe repair hints；观测结果不授权 publication 或 artifact 写入。 |
| State transition / decision table | OPL state-machine runner + MAS domain transition table | OPL 提供通用 transition schema、tick、retry/dead-letter、human gate transport、dispatch receipt 和 matrix runner；MAS 声明医学 domain transition table、guard、owner、fail-closed blocker 和 oracle fixtures。当前 `study-state-matrix` 是 MAS-owned `domain_transition_table`、`family_transition_spec` 和 `family_transition_matrix_cases` 的完整物化 surface；`product-entry manifest` 与 `sidecar export` 只挂 `family_transition_spec_descriptor` 和 descriptor locator，不再重复背完整医学判断。 |
| Generated runtime-facing adapter / projection | OPL hosted runtime + MAS pack compiler | MAS 优先提供 descriptor、stage graph、transition table、receipt schema、artifact/memory/source policies 和 authority function manifest，由 OPL 生成 sidecar/export/dispatch/status/workbench；手写 adapter 只作为迁移桥，不成为第二套 scheduler、queue、attempt ledger 或 workbench runtime。 |

### 功能面完成口径

MAS 作为 OPL 消费方时，剩余功能面按以下口径完成：

- OPL scaffold：MAS 暴露 domain descriptor、stage/quality pack、owner receipt schema、authority function manifest 和 domain entry；不再新增 MAS-owned generic scaffold、手写 generic sidecar/status/workbench 或通用 agent OS。
- OPL generic transition：MAS 维护 `study-state-matrix` 和 domain transition oracle；OPL runner 只执行 spec、attempt、retry/dead-letter 和 human-gate transport，不解释医学质量。
- OPL memory primitive：MAS 持有 publication-route memory body、检索策略和 writeback accept/reject/blocker receipt；OPL 只消费 locator、refs、freshness、counts 和 grouping。
- OPL artifact primitive：MAS 持有 current package、submission package、artifact mutation permission 和 rebuild proof；OPL 只消费 artifact locator、lifecycle/restore/retention shell 和 operator projection。
- OPL workbench primitive：MAS 输出声明式 route map、stage review、quality/source/artifact refs 和 safe action receipt；OPL/App 负责通用导航、attention queue、drilldown、status wrapper 和 action transport。
- OPL observability primitive：MAS 输出 typed blocker、runtime health facts、paper-progress SLO 语义和 safe repair hint；OPL 持有 provider SLO、attempt ledger、trace/log/event transport 和 repair projection shell。

每个新增 MAS 入口都必须能被 test lane 证明：默认 caller 不回到 MAS generic scheduler/daemon/queue/attempt ledger/runner/workbench；如需保留 direct/local path，只能是显式 diagnostic、cleanup 或 provenance。

### MAS 必须持有的领域内容

- `study charter`、research question、claim boundary、population/outcome/timepoint、analysis plan、source asset refs 和 study-level owner route。
- 医学 stage pack：`scout`、`idea`、`baseline`、`experiment`、`analysis-campaign`、`write`、`review`、`finalize`、`decision`、`journal-resolution` 的目标、知识、prompt/skill 和输出义务。
- 研究路线知识：route archetype、publication-route memory、route decision rationale、pivot/stop rules、minimum evidence package 和 rejected alternative 背景。
- 质量知识：reporting guideline、display-to-claim map、medical manuscript prose contract、AI reviewer rubric、review ledger 和 publication gate policy。
- Artifact authority：canonical manuscript、figures/tables、submission package、delivery freshness、rebuild proof 和 current package 写入授权。
- Domain receipts：stage closeout、owner receipt、quality verdict、artifact delta、human gate、stop-loss、memory writeback receipt 和 typed blocker。

### MAS 应尽量调用而非重复实现的功能

以下能力在理想目标态中优先向 OPL / shared family layer 上收。MAS 可以保留 direct/local diagnostic path，但不应把它们写成 MAS 长期产品内核：

- provider-backed workflow、worker residency、attempt start/query/signal、retry/dead-letter 和 restart recovery；
- generic queue、approval transport、human gate signal、resume token、operator action ledger；
- generic memory locator、memory index、body-free inventory projection、freshness、writeback transport 和 App grouping；
- generic artifact locator、retention、cleanup、restore proof、migration ledger 和 file lifecycle index；
- generic state-machine runner、transition matrix runner、attempt ledger 和 workflow transport；
- generic workbench navigation、attention queue、running/recent items、transition bridge evidence drilldown、notification、cross-domain dashboard、CLI/MCP/product-entry/sidecar/status generated wrapper；
- generic observability transport、trace/log/event collection、stale scan 和 repair command projection。

这个边界的目的，是让 MAS 成为高质量医学研究 domain brain，而不是又维护一套通用平台。

现有代码若落在这些功能族中，默认就是功能/结构差距，而不是“MAS 已经实现所以保留”。完善计划应写清上收、generated surface 替换、收薄为 refs-only adapter、或 direct retirement 的路径。

## Stage 是医学专家工作的组织单元

理想 MAS stage 接近真实医学研究团队完成一个阶段工作的最小大步骤。每个 stage 都应有明确目标、输入、知识、工具、质量门槛、输出和 closeout。

每个 stage 至少声明：

- `goal`：本阶段要完成的医学研究目标。
- `inputs`：study charter、source refs、workspace locator、上游 artifact refs、用户约束和 previous closeout。
- `knowledge_refs`：publication-route memory、literature refs、policy refs、quality packs、stage-specific method notes。
- `tool_refs`：MAS CLI/MCP/controller surface、analysis helpers、artifact rebuild tools、Office/PDF/browser/native helper 等可审计入口。
- `executor_requirements`：默认 `Codex CLI`；其他 Agent executor 只能显式接入并保留 non-equivalence notice。
- `quality_gates`：AI reviewer、reporting guideline、publication gate、evidence/review ledger、stage deliverable review。
- `outputs`：artifact delta、stage closeout、memory writeback proposal、owner receipt、human gate、stop-loss 或 typed blocker。
- `handoff`：下一 stage、next owner、resume token、safe action 或 reviewer route-back。

理想 stage family 包括：

| Stage | 理想职责 | 主要 authority |
| --- | --- | --- |
| `scout` | 识别研究机会、数据资产、可发表问题和不可行方向。 | MAS study route / source evidence |
| `idea` | 固化研究问题、claim boundary、目标期刊方向和最低证据包。 | study charter |
| `baseline` | 建立数据、变量、cohort、reporting guideline 和初始 display map。 | evidence ledger / data manifest |
| `experiment` | 执行可审计分析、敏感性分析、亚组或补充验证。 | analysis outputs / evidence ledger |
| `analysis-campaign` | 在不扩大 claim 边界的前提下推进有限补充分析和路线验证。 | controller decision / route receipt |
| `write` | 生成 manuscript-native medical prose 和 canonical manuscript delta。 | canonical manuscript / quality contract |
| `review` | 由 AI reviewer 和 stage review page 检查科学质量、写作质量和论证节奏。 | AI reviewer-backed publication eval |
| `finalize` | 重建 figures/tables/package，确认 freshness、delivery 和 submission blocker。 | artifact rebuild proof / package gate |
| `decision` | 做 submit/pivot/stop/revise/route-back 决策。 | controller decision / publication route |
| `journal-resolution` | 处理 journal fit、reviewer response、revision route 和外部释放边界。 | MAS publication authority |

## OPL 托管理想边界

MAS 理想状态不是把 runtime 外围全部留在 MAS，也不是让 OPL 接管医学大脑。目标边界是：

- OPL 持有 stage attempt、provider workflow、queue、wakeup、signal/query、retry/dead-letter、human gate transport、attempt ledger、framework-level receipt、transition bridge evidence refs-only drilldown 和 operator projection。
- MAS 持有 stage semantics、prompt/skill、knowledge packet、domain transition table、quality gate、study truth、publication verdict、memory writeback decision 和 artifact authority；MAS 的 runtime-facing surface 是 descriptor / contract / thin adapter / owner receipt / projection builder / focused tests，不是通用 runtime owner。
- MAS 当前默认 supervision scheduler 已由 OPL replacement 承载；显式 local supervision scheduler、LaunchAgent/cron job、legacy tick 和 job registry/latest run projection 只作为 legacy status/remove cleanup path 保留。`outer_supervision_slo` 仍由 MAS 解释 paper-progress freshness、owner receipt、typed blocker 和 safe action refs，但 cadence / scheduler / SLO 承载应继续留在 OPL provider，而不是回流成 MAS 私有 scheduler。
- `medautosci sidecar export|dispatch` 是 OPL 到 MAS 的受控桥。Export 只投影 locator、task、status、provider readiness 和 typed blocker；dispatch 只接受 allowlisted task 并回到 MAS owner chain。
- OPL provider completion 只能说明框架 attempt 完成；domain ready verdict 必须来自 MAS owner surface。
- Temporal-backed provider 是 OPL production online path 的目标 substrate；Hermes、local carrier、MDS/DeepScientist 只能在显式 adapter、proof、diagnostic、archive、provenance 或 parity 语境中出现。

## 当前差距与完善计划

MAS 当前差距、总体差距矩阵、后续执行顺序和禁止误写口径已经拆到 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)。本文只保留 north-star 目标态和长期 owner 边界，避免目标态与 active plan 在同一文件里继续双写。

## Workspace 与文件边界

理想 MAS 运行必须保持 repo source、workspace artifact 和 provider metadata 分离。

MAS repo 保存：

- source、contracts、schemas、prompts、skills、stage definitions、quality gates、projection builders、fixtures、tests 和 docs。
- 标准 domain-agent skeleton anchors、artifact locator contract 和 body-free evidence receipt refs。

MAS workspace 保存：

- 用户输入、source assets、study charter、evidence ledger、review ledger、runtime state、controller decisions、publication eval、stage review page/index、memory pack、writeback receipts、analysis outputs、canonical manuscript、figures、tables 和 submission package。

OPL / provider 保存：

- attempt metadata、workflow id、provider receipt、queue item、signal/query history、retry/dead-letter state、framework closeout refs、locator refs、freshness 和 operator projection。

这个边界保证开发目录干净、真实论文资产有生命周期、provider 可以恢复运行，同时医学 truth 和 publication authority 不被 framework metadata 稀释。

## 用户工作台理想职责

理想用户工作台面向医生、PI、研究团队和维护者，而不是展示内部模块列表。它可以由 OPL App 承担主产品面，MAS 提供 domain-owned projection、route map、stage/review/artifact refs 和 safe action receipts。旧 MDS / 上游 DeepScientist 的 per-project / per-quest workspace、canvas、stage history 和 terminal 可作为 clean-room UX oracle；MAS 不导入旧代码、旧产品身份或旧 daemon owner。

它应展示：

- `Study Line`：研究问题、当前阶段、owner、paper progress、next action 和 human gate。
- `研究路线地图`：用节点和边展示研究路线演进，包括阶段、路线、决策、阻塞、产物、执行回合、推进、阻塞、改道/替代和产物关系。
- `路线/决策轨迹`：展示先尝试哪条分析/写作路径，哪一步因为证据、质量、数据或运行 blocker 走不通，为什么切换到另一条路线，哪些 path 已 superseded，当前 active/winning path 是什么。
- `Evidence`：source refs、evidence ledger、analysis outputs、claim-to-display map 和 freshness。
- `Review`：AI reviewer verdict、stage review page、review ledger、publication blocker 和 route-back。
- `Artifacts`：canonical manuscript、figures/tables、package freshness、delivery refs、restore proof。
- `Runtime`：worker liveness、provider attempt、retry budget、SLO drift、safe repair command 和 typed blocker。
- `Memory`：publication-route memory consumed refs、writeback receipt refs、stale/deprecated review summary 和 grouping。
- `Actions`：只暴露路由到明确 owner 的 safe action；每次 action 必须返回 MAS owner receipt、provider receipt 或 typed blocker。

工作台不得把 UI 状态、provider completion、read-only projection 或 observability finding 写成 quality ready、submission ready 或 publication ready。

研究路线视图必须是理想工作台的一等对象。只列当前 stage 或 artifact refs 不够；它要像旧 MDS/DeepScientist 的路线感一样，让用户直观看到路线分叉、失败路径、阻塞原因、转向理由和当前仍成立的主线。该视图只消费 `mas_progress_portal_route_decision_trail`、`mas_progress_portal_route_map`、controller decisions、intervention lane、evidence/review ledgers、runtime lifecycle lineage 和 source refs；缺少输入时必须显示 missing，不能从文件名、stage 文案或 artifact path 猜测研究路线。

## 理想完成门槛

MAS 达到理想生产级状态时，应满足以下门槛：

- Direct MAS app skill path 与 OPL-hosted path 使用同一 MAS owner surfaces，并有语义等价与 forbidden-write 证据。
- 每个真实 paper-line stage attempt 都留下 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。
- OPL provider 能长期托管 MAS stage attempt，并证明 restart/re-query、signal、retry/dead-letter、human gate/resume 和 no-forbidden-write。
- 通用 runtime、queue、memory locator、artifact lifecycle、restore/retention、projection、workbench shell 和 generated entry/status wrapper 已尽量上收到 OPL / shared family layer；MAS 保留领域知识、authority、owner receipt、声明式 pack 和 minimal authority functions。
- MAS 仍保留的非知识代码均能归类为 declarative pack / generated surface handoff、refs-only adapter、minimal authority function 或 no-active-caller cleanup gate；每项都有 active caller、receipt/schema/ref 边界、cannot-absorb reason 或 cleanup gate。能由 OPL pack compiler 生成的 CLI/MCP/product-entry/sidecar/status/projection/harness 不再作为 MAS 长期私有实现扩展。
- `functional_consumer_boundary.declarative_pack_compiler_input`、`generated_surface_handoff` 与 `minimal_authority_function_manifest` 在 product-entry manifest、sidecar export 与 supervision consumer migration 中同步投影；测试断言 MAS 的长期 code owner 只限 publication quality、AI reviewer quality decision、artifact mutation authorization、memory accept/reject、source readiness、owner receipt signer 和 medical helper，其余程序面只能是 OPL generated/hosted surface 或迁移桥。
- MAS domain transition table / transition matrix 成为 controller route 的单一语义来源；新增或修改 transition 必须同步更新 spec、oracle fixtures、matrix tests 和 owner receipt/fingerprint 字段，并证明旧 completion / execution / stop-loss / memory-writeback receipt 不会被 stale prompt 或低权威 closeout 覆盖或误用。
- Study charter、evidence ledger、review ledger、publication eval、controller decisions、runtime status 和 artifact rebuild proof 构成同一条 current truth。
- Publication-route memory 在多个真实 paper line 上产生 accepted/rejected writeback receipts，并可被后续 stage 小集合检索。
- 单篇论文工作台能稳定展示研究路线地图和路线/决策轨迹，包括分支、失败/阻塞原因、转向理由、superseded path、active/winning path、route map node/edge 和 source refs。
- Stage Deliverable Review Page / Index 在真实 workspace 中持续更新，并被 Portal / Workbench 只读展示。
- Artifact lifecycle、retention、cleanup、restore proof 和 SQLite/file authority 边界在真实 workspace 中可运行。
- AI reviewer workflow 前置进入 pre-draft 和 revision route，不再依赖机械 gate 后置补救论文质量。
- Legacy MDS/Hermes/local/default-compat residue 完成 no-active-caller scan、replacement proof、history/provenance 分类；`local_launchd_scheduler_install_path` 与旧 workspace-local service wrapper 不再是标准 OPL Agent 的 active gap，只能作为 cleanup diagnostic、provenance 或 drift guard 被显式读取，scheduler 管理只保留 canonical runtime CLI。
- 文档只解释、导航和治理；机器接口与当前 truth 继续归 durable surface、schema、CLI/API payload、manifest、receipt 和真实 workspace artifact。

## 当前使用方式

本文适合作为以下工作中的目标态参考：

- 评估 MAS 是否偏离医学研究 owner 边界。
- 规划 OPL-hosted MAS production closure。
- 设计 MAS / OPL App runtime workbench。
- 判断 shared modules 应上收到 OPL 还是留在 MAS。
- 处理 MDS/DeepScientist/Hermes/local scheduler legacy residue。
- 新增 stage、quality pack、memory card、artifact locator 或 sidecar receipt。

实际执行时按当前状态递进：

- 当前 truth 读核心五件套。
- 当前开发线路读 `docs/active/current_development_lines.md`。
- AI-first 质量 owner 读 `docs/references/mainline/ai_first_research_os_architecture.md`。
- Stage form 读 `docs/active/stage_surface_standardization_program.md` 与 generated stage surfaces。
- OPL 托管、provider、sidecar 和 skeleton 边界读 runtime contracts 与 product-entry manifest。
- 新增机器接口写入 `contracts/`、源码、CLI/MCP/API payload、manifest 或 OPL-generated surface 的输入 contract，不写入本文。
