# MAS 理想目标态

Owner: `MedAutoScience`
Purpose: `north_star_reference`
State: `active_support`
Machine boundary: 本文是人读目标态参考。机器可读真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-14`

## 结论

理想状态下，`Med Auto Science` 是医学研究与医学论文交付的完整 domain agent。它能从研究问题进入同一条 study line，持续管理 workspace 语境、证据、分析、写作、审阅、投稿准备、运行状态、human gate、交付包和事后记忆，直到给出可审计的 artifact delta、quality verdict、publication route、submission package 或明确 blocker。

MAS 的核心价值不是维护通用 agent runtime、通用 memory service、通用 artifact lifecycle 或通用用户工作台，而是持有医学研究知识、研究路线、stage 语义、quality verdict、publication authority 和 artifact authority。`OPL Framework` 提供 stage-led、provider-backed、可恢复的外层运行框架，以及尽量可复用的 queue、wakeup、attempt ledger、memory locator、artifact lifecycle、projection 和 workbench shell；MAS 作为 admitted medical research domain agent 暴露 stage descriptor、sidecar、receipt、artifact locator、projection 和 authority refs。经 OPL 托管运行或通过 MAS app skill 直接调用，最终都必须回到同一套 MAS-owned stage、controller、ledger、review、quality gate 和 artifact surface。

因此，MAS 的理想形态是医学研究 `Domain Knowledge / Authority Pack + thin adapter`，不是一套独立 agent runtime platform。MAS 可以保留 direct/local diagnostic path 和 MAS-owned controller truth，但 generic scheduler、generic queue、generic attempt ledger、generic memory locator、generic artifact lifecycle、generic state-machine runner、generic workbench shell、observability/SLO 和跨 domain App projection 都应由 OPL Framework / One Person Lab App 承载。MAS 的 sidecar、projection、runtime-facing surface 只负责把医学 owner chain、typed blocker、owner receipt、artifact locator 和 domain transition spec 暴露给 OPL，不承担平行通用运行框架职责。

状态转换也服从同一分层：通用 state-machine runner、transition schema、幂等 tick、retry/dead-letter、human gate transport、dispatch receipt 和 transition matrix runner 应进入 OPL / shared family layer；MAS 持有医学 domain transition table / transition matrix，定义 `publication_supervisor_state`、publication gate、AI reviewer、claim/evidence/display blocker、submission authority 和 artifact/package authority 如何转换成 `decision_type`、`route_target`、`next_work_unit` 与 `controller_action`。OPL 执行 MAS 声明的 transition spec，不能自行解释医学发表状态。

本文描述目标态，不替代当前状态判断。当前落地程度、生产证据缺口和开发顺序以 [当前状态](../../status.md)、[架构](../../architecture.md)、[MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)、[MAS 当前开发线路](../../active/current_development_lines.md) 与 [MAS AI-first Research OS Architecture](../mainline/ai_first_research_os_architecture.md) 为准。

OPL 系列项目的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`。本文只维护 MAS 自己的理想态、authority 边界和通用能力上收清单；MAS 当前差距和完善计划由 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 维护。OPL、MAG、RCA、MDS/DeepScientist 或 OPL-owned App/workbench 的具体完善计划回到各自 owner surface。

2026-05-14 当前差距可归纳为三类。第一，生产证据缺口：真实 provider-hosted paper apply、domain activity long soak、human gate/resume 和更多真实 memory writeback receipts 仍要由 live workspace / owner receipt 证明。第二，产品化缺口：OPL App / Workbench 需要把 MAS refs、stage review/index、route-memory refs、provider refs、safe action receipt 和 typed blocker 做成人用 drilldown。第三，历史残留缺口：旧 MDS/Hermes/local/default-compat surface 只要没有 active caller、public surface 引用或 fixture/provenance 必需，并且已有 replacement proof，就应直接删除源码、命令 wrapper 和对应测试，不再以兼容接口形式保留。

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

MAS 长期职责是把医学研究领域内的判断、证据、路线、质量和交付 authority 收口成可审计的 domain-owned surface。通用运行能力、通用 memory/index、通用 artifact lifecycle、通用 workbench shell 和 provider 运维能力应优先由 OPL 或 shared family primitives 实现；MAS 只保留领域知识、领域 policy、owner receipt、quality gate、artifact authority 和必要的薄适配。

### 职责边界

| 能力族 | 理想通用 owner | MAS 理想职责 |
| --- | --- | --- |
| Long-running runtime | OPL provider / OPL Framework | 声明 stage、owner route、allowed task、domain receipt 和 forbidden writes；接收 OPL dispatch 后回到 MAS owner chain。 |
| Queue / retry / dead-letter / human gate transport | OPL Framework | 给出 human gate 边界、resume 语义、stop-loss 语义和 domain blocker，不重复维护通用 transport。 |
| Memory locator / index / writeback transport | OPL shared primitive + MAS workspace owner surface | MAS 持有 publication-route memory 正文、领域检索策略、接受/拒绝规则和 writeback receipt；OPL 只持 locator、refs、freshness 和展示分组。 |
| Artifact lifecycle / restore / retention | OPL shared primitive + MAS artifact owner surface | MAS 持有 canonical manuscript/package authority、artifact mutation permission 和 rebuild proof；OPL 只处理 locator、restore/retention primitive 和 operator projection。 |
| Product workbench shell | OPL App / shared workbench | MAS 提供 per-study projection、研究路线地图、stage/review/artifact refs 和 action receipt；Workbench 只展示和路由，不裁决。 |
| Observability / diagnostics | OPL/shared observability + MAS read models | MAS 提供 domain blocker、quality/source refs、runtime health facts 和 safe repair hints；观测结果不授权 publication 或 artifact 写入。 |
| State transition / decision table | OPL state-machine runner + MAS domain transition table | OPL 提供通用 transition schema、tick、retry/dead-letter、human gate transport、dispatch receipt 和 matrix runner；MAS 声明医学 domain transition table、guard、owner、fail-closed blocker 和 oracle fixtures。当前 `study-state-matrix` 已把 MAS-owned `domain_transition_table` 和可供 OPL 消费的 `family_transition_spec` 一起投影出来，`product-entry manifest` 与 `sidecar export` 只挂 `family_transition_spec_descriptor`，不再重复背完整医学判断。 |
| Runtime-facing adapter / projection | OPL hosted runtime + MAS thin adapter | MAS sidecar/export/dispatch 只暴露 owner route、typed blocker、receipt refs、artifact locator 和 domain spec；不成为第二套 scheduler、queue、attempt ledger 或 workbench runtime。 |

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
- generic workbench navigation、attention queue、running/recent items、notification 和 cross-domain dashboard；
- generic observability transport、trace/log/event collection、stale scan 和 repair command projection。

这个边界的目的，是让 MAS 成为高质量医学研究 domain brain，而不是又维护一套通用平台。

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

- OPL 持有 stage attempt、provider workflow、queue、wakeup、signal/query、retry/dead-letter、human gate transport、attempt ledger、framework-level receipt 和 operator projection。
- MAS 持有 stage semantics、prompt/skill、knowledge packet、domain transition table、quality gate、study truth、publication verdict、memory writeback decision 和 artifact authority；MAS 的 runtime-facing surface 是薄 adapter / owner receipt / projection builder，不是通用 runtime owner。
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
- 通用 runtime、queue、memory locator、artifact lifecycle、restore/retention、projection 和 workbench shell 已尽量上收到 OPL / shared family layer；MAS 只保留领域知识、authority、owner receipt 和薄适配。
- MAS domain transition table / transition matrix 成为 controller route 的单一语义来源；新增或修改 transition 必须同步更新 spec、oracle fixtures、matrix tests 和 owner receipt/fingerprint 字段。
- Study charter、evidence ledger、review ledger、publication eval、controller decisions、runtime status 和 artifact rebuild proof 构成同一条 current truth。
- Publication-route memory 在多个真实 paper line 上产生 accepted/rejected writeback receipts，并可被后续 stage 小集合检索。
- 单篇论文工作台能稳定展示研究路线地图和路线/决策轨迹，包括分支、失败/阻塞原因、转向理由、superseded path、active/winning path、route map node/edge 和 source refs。
- Stage Deliverable Review Page / Index 在真实 workspace 中持续更新，并被 Portal / Workbench 只读展示。
- Artifact lifecycle、retention、cleanup、restore proof 和 SQLite/file authority 边界在真实 workspace 中可运行。
- AI reviewer workflow 前置进入 pre-draft 和 revision route，不再依赖机械 gate 后置补救论文质量。
- Legacy MDS/Hermes/local/default-compat residue 完成 no-active-caller scan、replacement proof、history/provenance 分类；无 active caller、无 public surface 引用、无 fixture/provenance 必需的 residue 完成物理删除。旧 workspace-local service wrapper 属于应删除 residue，scheduler 管理只保留 canonical runtime CLI。
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
- 新增机器接口写入 `contracts/`、源码、CLI/MCP/API payload、manifest 或 MAS-owned generated surface，不写入本文。
