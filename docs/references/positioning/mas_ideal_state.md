# MAS 理想目标态

Owner: `MedAutoScience`
Purpose: `north_star_reference`
State: `active_support`
Machine boundary: 本文是人读目标态参考。机器可读真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-18`

## 文档读法

- 本文只写 MAS 的 north-star 目标态和长期 owner boundary；当前差距、实施顺序和验收缺口回到 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)。
- dated 过程校准、follow-through 和 closeout 证据归档到 [MAS standard agent 文档过程归档 2026-05](../../history/program/mas-standard-agent-doc-process-history-2026-05.md)，不在本文承担 current truth。
- 理想目标态高于当前实现。当前 MAS 内已经存在的 controller、scheduler、SQLite/lifecycle、workspace/source intake、memory/artifact transport、Portal/workbench、CLI/MCP/Skill/product-entry/sidecar/status wrapper 都只能作为迁移输入，不是长期架构约束。

## 结论

理想状态下，`Med Auto Science` 是医学研究与医学论文交付的完整 domain agent。它能从研究问题进入同一条 study line，持续管理 workspace 语境、证据、分析、写作、审阅、投稿准备、运行状态、human gate、交付包和事后记忆，直到给出可审计的 artifact delta、quality verdict、publication route、submission package 或明确 blocker。

MAS 的核心价值是医学研究知识、研究路线、stage 语义、AI-first quality verdict、publication authority、artifact authority、memory writeback decision 和 owner receipt。MAS 的理想形态是：

`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal medical authority functions`

MAS 不应长期维护一套独立 agent runtime platform。通用 scheduler、queue、attempt ledger、generic transition runner、memory/artifact locator、lifecycle/restore/retention shell、observability/SLO、CLI/MCP/Skill/product-entry/sidecar/status wrapper 和跨 domain App/workbench shell 应由 OPL Framework / One Person Lab App 承载或生成。

Direct MAS app skill path 仍是一等入口。经 direct path 或 OPL-hosted path 调用时，都必须回到同一套 MAS-owned stage、controller、ledger、review、quality gate、domain transition table、publication-route memory 和 artifact surface。

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

程序不得用规则、regex、固定分支或 fallback 直接替代 AI reviewer / Quality OS 的医学判断。同一 agent 的自审不能关闭 AI-first quality gate。

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
- MAS 非知识代码均能归类为 declarative pack / generated surface handoff、refs-only adapter、minimal authority function 或 no-active-caller cleanup gate，并完成对应 cutover、收薄或退役。
- 当前 `classification_gap_count=0` 与 `active_private_generic_residue_count=0` 只说明私有功能面分类和默认 generic owner 回流已被 guard 住；`functional_structure_gap_count=5` 仍要求继续完成 generated surface active caller cutover、refs-only adapter 收薄、legacy physical retirement、OPL App drilldown、lifecycle locator/retention/restore ledger 对账。live paper-line evidence scaleout 是另一组测试/证据门，不能替代这 5 个功能/结构 gate。
- 每个真实 paper-line stage attempt 都留下 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。
- Publication-route memory 在多个真实 paper line 上产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 小集合检索。
- Artifact lifecycle、retention、cleanup、restore proof 和 SQLite/file authority 边界在真实 workspace 中可运行。
- Human gate/resume、explicit wakeup、retry/dead-letter、provider SLO long soak 和 no-forbidden-write 在真实 provider-hosted run 中持续成立。
- Legacy MDS/Hermes/local/default-compat residue 完成 no-active-caller scan、replacement proof、history/provenance 分类与 physical retirement；不保留兼容别名。

## 当前差距入口

当前功能/结构差距、测试/证据差距、完善顺序和禁止误写口径由 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 维护。本文不双写 active plan。
