# MAS 理想目标态

Owner: `MedAutoScience`
Purpose: `north_star_reference`
State: `active_support`
Machine boundary: 本文是人读目标态参考。机器可读真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-14`

## 结论

理想状态下，`Med Auto Science` 是医学研究与医学论文交付的完整 domain agent。它能从研究问题进入同一条 study line，持续管理 workspace 语境、证据、分析、写作、审阅、投稿准备、运行状态、human gate、交付包和事后记忆，直到给出可审计的 artifact delta、quality verdict、publication route、submission package 或明确 blocker。

MAS 的核心价值不是维护通用 agent runtime，而是持有医学研究的 truth、quality verdict、publication authority 和 artifact authority。`OPL Framework` 提供 stage-led、provider-backed、可恢复的外层运行框架；MAS 作为 admitted medical research domain agent 暴露 stage descriptor、sidecar、receipt、artifact locator、projection 和 authority refs。经 OPL 托管运行或通过 MAS app skill 直接调用，最终都必须回到同一套 MAS-owned stage、controller、ledger、review、quality gate 和 artifact surface。

本文描述目标态，不替代当前状态判断。当前落地程度、生产证据缺口和开发顺序以 [当前状态](../../status.md)、[架构](../../architecture.md)、[MAS 当前开发线路](../../program/current_development_lines.md) 与 [MAS AI-first Research OS Architecture](../mainline/ai_first_research_os_architecture.md) 为准。

## 产品分层

MAS 的理想产品认知保持四层：

1. `MAS Domain Agent`
   面向用户和通用 agent 的医学研究入口。它承接研究问题、workspace、进度、human gate、论文文件和交付状态。
2. `MAS Research OS`
   MAS 内部的医学研究 operating system。它由 Study OS、Quality OS、Runtime OS、Artifact OS、Memory OS、Evaluation OS 和 Observability OS 组成，并统一回到 MAS owner surfaces。
3. `OPL Framework Integration`
   OPL 承担 stage attempt、queue、wakeup、retry/dead-letter、human gate transport、provider receipt、projection 和 shared lifecycle/index primitive。MAS 只暴露可托管边界，不把医学研究 truth 上收到 OPL。
4. `User Workbench`
   Codex App、OPL App、Progress Portal、Live Console 或其他 UI 只读消费 MAS projection、receipt refs、artifact refs 和 safe action receipts。用户界面不成为第二 runtime owner 或 publication authority。

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

## MAS 的理想职责

MAS 长期职责是把医学研究领域内的判断、证据、质量、运行与交付收口成可审计的 domain-owned system。

### Study OS

- 持有 study charter、research question、claim boundary、population/outcome/timepoint、analysis plan、source asset refs 和 study-level owner route。
- 把用户输入、导师反馈、审稿意见、revision request 和 stop/pivot decision 纳入同一条 durable study line。
- 通过 `StudyTruthKernel`、`study_macro_state`、`owner_route` 和 controller decisions 统一用户可见 next action。
- 明确哪些状态允许自动推进，哪些状态需要 human gate，哪些状态只能停驻或止损。

### Quality OS

- 在写作前暴露研究问题、数据资产支撑、reporting guideline、display-to-claim map 和 manuscript-native prose contract。
- 由 AI reviewer workflow 持有科学质量、医学写作质量、publishability 和 submission-facing readiness。
- 使用 evidence ledger、review ledger、publication eval、quality packs 和 stage review index 组织质量证据。
- 机械 gate 只持有完整性、结构、provenance、blocker 和 replay proof；它不能替代 AI reviewer 或医学作者判断。

### Runtime OS

- 把长时间医学研究推进拆成可恢复、可重放、可审计的 stage work units。
- 使用 MAS-owned runtime surfaces 记录 worker liveness、retry budget、controller-owned resume action、human gate、runtime escalation 和 paper progress SLO。
- 在 standalone/local diagnostics 中保持 MAS local scheduler 可用；在 OPL Full online path 中由 OPL provider 唤醒和派发，再回到 MAS sidecar dispatch 与 MAS owner receipt。
- 以 paper progress 为最高运行目标：长期运行必须能产生 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或解释充分的 typed blocker。

### Artifact OS

- 坚持 canonical-source-first：manuscript、figures、tables、submission package 和 delivery mirror 都必须能从 canonical source 重建。
- 交付判断依赖 artifact rebuild proof、freshness proof、package manifest、checksum、restore proof 和 MAS owner receipt。
- `current_package`、submission package、paper/manuscript 文件和真实 workspace artifacts 归 MAS workspace / artifact owner surface。
- Portal、Workbench、OPL 或 provider 只能展示 locator、freshness、receipt 和 blocker，不能直接写 artifact authority。

### Memory OS

- Publication-route memory 以自然语言 memory card、small-set stage refs、typed closeout proposal 和 router receipt 运行。
- MAS workspace 持有 memory body、accepted/rejected writeback receipt、migration receipt 和 review discipline。
- OPL/Aion/Workbench 只读展示 body-free locator、consumed refs、writeback receipt refs、freshness、rejected reason 和 grouping。
- 记忆用于增强 stage reasoning 和 route context，不能成为 recipe engine、winning-route scorer 或 publication authority。

### Evaluation OS

- 把历史返工、审稿失败、路线误判、artifact stale 和 paper progress stall 转成 calibration corpus、quality regression、AI-first drift audit 和 route-back lessons。
- 区分 objective evidence、AI reviewer quality evidence、runtime evidence 和 artifact proof。
- 投稿结果、审稿反馈和真实论文 soak 进入可回放的评价闭环，而不是散落在聊天记录或临时报告里。

### Observability OS

- 面向维护者展示 drift、trace、runtime health、freshness、route-back、cache state、artifact stale、legacy residue 和 safe repair command。
- Observability 只做证据、投影、诊断和 replay proof；它不授权 finalize、submission、publication readiness、artifact mutation 或 runtime recovery。

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
- MAS 持有 stage semantics、prompt/skill、knowledge packet、quality gate、study truth、runtime owner surface、publication verdict、memory writeback decision 和 artifact authority。
- `medautosci sidecar export|dispatch` 是 OPL 到 MAS 的受控桥。Export 只投影 locator、task、status、provider readiness 和 typed blocker；dispatch 只接受 allowlisted task 并回到 MAS owner chain。
- OPL provider completion 只能说明框架 attempt 完成；domain ready verdict 必须来自 MAS owner surface。
- Temporal-backed provider 是 OPL production online path 的目标 substrate；Hermes、local carrier、MDS/DeepScientist 只能在显式 adapter、proof、diagnostic、archive、provenance 或 parity 语境中出现。

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

理想用户工作台面向医生、PI、研究团队和维护者，而不是展示内部模块列表。

它应展示：

- `Study Line`：研究问题、当前阶段、owner、paper progress、next action 和 human gate。
- `Evidence`：source refs、evidence ledger、analysis outputs、claim-to-display map 和 freshness。
- `Review`：AI reviewer verdict、stage review page、review ledger、publication blocker 和 route-back。
- `Artifacts`：canonical manuscript、figures/tables、package freshness、delivery refs、restore proof。
- `Runtime`：worker liveness、provider attempt、retry budget、SLO drift、safe repair command 和 typed blocker。
- `Memory`：publication-route memory consumed refs、writeback receipt refs、stale/deprecated review summary 和 grouping。
- `Actions`：只暴露路由到明确 owner 的 safe action；每次 action 必须返回 MAS owner receipt、provider receipt 或 typed blocker。

工作台不得把 UI 状态、provider completion、read-only projection 或 observability finding 写成 quality ready、submission ready 或 publication ready。

## 理想完成门槛

MAS 达到理想生产级状态时，应满足以下门槛：

- Direct MAS app skill path 与 OPL-hosted path 使用同一 MAS owner surfaces，并有语义等价与 forbidden-write 证据。
- 每个真实 paper-line stage attempt 都留下 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。
- OPL provider 能长期托管 MAS stage attempt，并证明 restart/re-query、signal、retry/dead-letter、human gate/resume 和 no-forbidden-write。
- Study charter、evidence ledger、review ledger、publication eval、controller decisions、runtime status 和 artifact rebuild proof 构成同一条 current truth。
- Publication-route memory 在多个真实 paper line 上产生 accepted/rejected writeback receipts，并可被后续 stage 小集合检索。
- Stage Deliverable Review Page / Index 在真实 workspace 中持续更新，并被 Portal / Workbench 只读展示。
- Artifact lifecycle、retention、cleanup、restore proof 和 SQLite/file authority 边界在真实 workspace 中可运行。
- AI reviewer workflow 前置进入 pre-draft 和 revision route，不再依赖机械 gate 后置补救论文质量。
- Legacy MDS/Hermes/local/default-compat residue 完成 no-active-caller scan、replacement proof、history/provenance 归档或物理删除。
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
- 当前开发线路读 `docs/program/current_development_lines.md`。
- AI-first 质量 owner 读 `docs/references/mainline/ai_first_research_os_architecture.md`。
- Stage form 读 `docs/program/stage_surface_standardization_program.md` 与 generated stage surfaces。
- OPL 托管、provider、sidecar 和 skeleton 边界读 runtime contracts 与 product-entry manifest。
- 新增机器接口写入 `contracts/`、源码、CLI/MCP/API payload、manifest 或 MAS-owned generated surface，不写入本文。
