# MAS / OPL Agent OS 目标运行架构参考

Owner: `MedAutoScience`
Purpose: `target_operating_architecture_support_reference`
State: `active_support_reference`
Machine boundary: 本文是人读目标运行架构参考。机器真相继续归 `agent/` pack、`contracts/`、源码、CLI/MCP/API 行为、OPL generated/hosted surfaces、runtime/controller durable surfaces、owner receipt、typed blocker、真实 workspace artifact 与 repo-native verification；当前差距、执行顺序、完成判断和下一轮 prompt 只回到 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)。
Date: `2026-06-11`

## 读法

本文把外部成熟工程经验和当前 MAS / OPL 边界压成目标运行架构参考。它不是新的 runtime truth、live study 状态、active backlog 或执行队列；当前差距、证据缺口和下一轮执行顺序仍由 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 维护。

目标态高于当前实现。现有 MAS 内的 scheduler、controller、read-model、SQLite、lifecycle、workspace wrapper、sidecar、Portal、CLI、MCP、product-entry 或 test fixture 都只能作为迁移输入；它们不能反向定义长期架构。

本文的判断口径：

- `OPL` 是 Agent OS / runtime substrate。
- `MAS` 是 Medical Research Pack + Medical Authority Kernel。
- `contracts/foundry-agent-os-domain-kernel-manifest.json` 是 W4 `domain-kernel-manifest` 的机器合同入口，固定 retained authority kernel、OPL upcollect surfaces、`current_owner_delta` 默认读根和 false-authority flags。
- 外部 Co-Scientist / Light / EvoScientist / PaperSpine / ARIS / ARK 等只进入 Scientific Capability Registry 或 refs-only advisory worker；它们不是 MAS runtime owner，也不是 publication / artifact / memory authority。
- OPL family 计划已经把 Scientific Capability Registry 抽象为 `Atlas + Pack + Stagecraft` 的 family-level ABI / use-policy；Agent Tool Arsenal / Capability Invocation OS 的品牌 owner 归 OPL Pack，Atlas / Stagecraft / Runway / Console / Connect 协同消费。MAS 不新增独立 external-learning selector、第二 active backlog、always-on advisory pipeline 或第 11 个 OPL 品牌模块；MAS 后续只声明 domain refs consumption、forbidden authority、owner receipt / typed blocker / reviewer receipt 晋级门。
- `Agent Tool Arsenal` 是 OPL generated surfaces 与 MAS authority kernel 之间的 agent-facing invocation ABI；工具给 autonomous agent 用，不给人类用户学习和手动拼装。
- 默认 operator / executor 读面固定为 `current_owner_delta`；audit、lineage、sidecar、observability、raw worklist 只做 drilldown。

## 目标结论

理想形态不是一个更复杂的 MAS 私有平台，而是：

`OPL Agent OS + MAS Declarative Medical Research Pack + MAS Minimal Authority Kernel + Scientific Capability Registry`

这表示：

- OPL 持有 durable execution、stage attempt、queue、retry/dead-letter、resume、human gate transport、state index、locator、generic memory/artifact lifecycle、observability、generated CLI/MCP/Skill/product-entry/workbench。
- MAS 持有医学研究 truth、stage semantics、source readiness、data/study binding、AI reviewer / auditor quality verdict、publication gate、artifact mutation authorization、publication-route memory accept/reject/blocker、owner receipt、typed blocker。
- Agent Tool Arsenal 把 action catalog、owner callable、MCP tool、stage skill、external capability 和 OPL hosted action 统一成 model-discoverable tool cards、invocation plans、risk annotations、structured result envelopes 和 receipt/blocker closeout。
- Scientific capability 只帮助当前 owner delta 更快产生 evidence、repair hint、reviewer briefing、candidate refs 或 no-loop signal；它不能新增默认前置流程，不能关闭 quality / publication / artifact / memory authority。

## 外部成熟经验的转译

| 外部经验 | 可取之处 | MAS / OPL 目标转译 | 禁止误用 |
| --- | --- | --- | --- |
| MCP tool protocol | tool 由模型调用，descriptor 带 name、description、input schema、metadata / annotations / output schema | OPL Pack Compiler 生成 agent-facing tool cards；MAS action catalog 只提供 domain intent、authority boundary 和 handler target | 不把 MCP tool list 当用户手册；不把 annotation 当安全保证；不缺 output schema / authority envelope |
| OpenAI Agents / tool orchestration | tools、handoffs、guardrails、sessions、deferred tool loading 和 approval interrupt | Tool Arsenal 支持按 current delta 延迟加载候选工具、嵌套 agent/tool handoff、approval-required action 和 resumable invocation state | 不把所有工具一次性塞进上下文；不让 handoff agent 越过 MAS owner receipt / typed blocker |
| Claude tool-use guidance | tool description 和 input examples 直接影响模型选择工具的能力 | 每张 MAS tool card 必须写清何时用、何时不用、输入 ref、输出 ref、常见失败和最小 examples | 不用短命令名或人类经验假设替代 agent-facing tool affordance |
| Co-Scientist scientific loop | generate、debate / tournament、evolve、meta-review、research overview | 放入 Scientific Capability Registry，作为 stage 内 hypothesis / review / arbitration affordance，输出 refs-only candidate、briefing、repair hint | 不复制 Co-Scientist runtime；不默认每轮 tournament；不把 ranking / Elo / proximity 写成 quality verdict |
| Temporal durable execution | workflow history、activity retry、signal/query、deterministic resume | OPL provider 承担 stage attempt lifecycle、retry/dead-letter、resume、long-running execution；MAS 只声明 stage pack、owner ticket、idempotency、receipt/blocker | MAS 不再拥有 generic attempt loop、queue、worker residency 或 private scheduler |
| Kubernetes reconciliation | desired/current 分离，controller 只把 current 推近 desired | OPL Reconciler 消费 MAS desired route / current owner delta，投影 next safe action；MAS reducer 给出唯一 owner truth | read-model、worklist 或 sidecar 不能成为第二 current truth |
| W3C PROV / OpenLineage | entity / activity / agent、dataset / job / run / facet lineage | StageRun、artifact、data release、analysis job、figure/table、claim/evidence 建立 refs-only lineage envelope | lineage 只证明来源关系，不授权 publication-ready、artifact mutation 或 source readiness |
| OpenTelemetry | trace / metrics / logs 分层 observability | OPL Observability Plane 暴露 stage trace、runtime SLO、failure class、drilldown；MAS 输出 domain refs 与 diagnostic explanation | traces、metrics、logs 不能关闭 owner receipt、quality gate 或 typed blocker |
| LangGraph workflow / agent split | workflow 编排与 agent open-ended work 分层，持久化与 human interrupt | OPL 承接 workflow / handoff / persistence / human gate；MAS stage executor 保持 open-ended scientific work | 不把 workflow graph 拆成过细小状态，不让 supervisor 取代 stage owner |

参考来源：

- Co-Scientist Nature paper: <https://www.nature.com/articles/s41586-026-10644-y>
- Google Research AI co-scientist overview: <https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/>
- Light skill-pack repository: <https://github.com/Light0305/Light>
- MCP tools specification: <https://modelcontextprotocol.io/specification/2025-11-25/server/tools>
- OpenAI Agents SDK tools: <https://openai.github.io/openai-agents-python/tools/>
- Anthropic tool-use documentation: <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use>
- Temporal durable execution docs: <https://docs.temporal.io/evaluate/understanding-temporal>
- Kubernetes controller pattern: <https://kubernetes.io/docs/concepts/architecture/controller/>
- W3C PROV overview: <https://www.w3.org/TR/prov-overview/>
- OpenLineage facets and object model: <https://openlineage.io/docs/spec/facets/>
- OpenTelemetry observability docs: <https://opentelemetry.io/docs/what-is-opentelemetry/>
- LangGraph overview: <https://docs.langchain.com/oss/python/langgraph/overview>

## 目标分层

### 1. OPL Agent OS

OPL 是跨 domain 的通用运行基座。它的目标能力包括：

- `Pack Compiler`：读取 `agent/` 与 `contracts/`，生成 CLI / MCP / Skill / product-entry / workbench / action catalog descriptors。
- `StageRun Kernel`：管理 stage attempt、attempt identity、current pointer、retry/dead-letter、resume、human gate transport、lease、provider query。
- `State Index Kernel`：从文件 truth、receipt、blocker、locator 和 artifact refs 重建 read model；SQLite / index 只存 refs、fingerprint、cursor、checksum、bounded preview hash。
- `Route Reconciler`：把 MAS desired route、current owner delta 和 OPL provider currentness 对齐；只生成 next safe transport action，不生成医学 truth。
- `Lifecycle Plane`：generic artifact / memory locator、restore、retention、cold-store、cleanup plan 和 workbench drilldown。
- `Observability Plane`：trace / metrics / logs / failure class / SLO drift / repair diagnostics。
- `Workbench Shell`：默认只显示 `current_owner_delta` 和用户可执行动作；audit detail 进入 drilldown。

OPL 不能持有：

- study truth
- source readiness verdict
- AI reviewer / auditor verdict
- publication-ready / submission-ready
- artifact mutation authorization
- publication-route memory body accept/reject
- MAS owner receipt / typed blocker 的语义裁决

### 2. MAS Medical Research Pack

MAS 的 declarative pack 应成为长期主要源码形态：

- `agent/stages/`：stage goal、inputs、outputs、quality gates、handoff、expected refs。
- `agent/skills/`：医学研究 stage 内可用技能，面向 Codex CLI / agent executor。
- `agent/knowledge/`：publication-route memory、method notes、evidence pack、source policy、quality pack refs。
- `agent/quality_gates/`：AI reviewer / auditor / publication gate 的 policy refs。
- `contracts/`：receipt、typed blocker、progress delta、artifact ref、source/data binding、generated surface handoff、forbidden authority boundary。

Pack 的目标是让 OPL 能编译和托管，但不能让 OPL 接管医学语义。

### 3. MAS Medical Authority Kernel

MAS 只长期保留无法声明化的最小 authority functions：

- source readiness verdict
- data / study binding authorization
- publication quality verdict materialization
- AI reviewer / auditor record validation
- artifact mutation authorization
- publication-route memory accept / reject / blocker
- owner receipt signer
- typed blocker materializer
- no-forbidden-write proof
- domain-specific helper implementation

这些函数的输出必须是 owner receipt、typed blocker、quality gate receipt、domain authority ref、safe action ref 或 diagnostic ref。它们不能扩展成 generic runner、queue、session store、workbench、state-machine engine 或 private lifecycle platform。

### 4. Scientific Capability Registry

外部系统和新 skill 进入统一 registry，而不是新增默认流程：

| Capability family | 服务对象 | 输出形状 | 默认行为 |
| --- | --- | --- | --- |
| hypothesis generation / debate / evolution | scout、idea、analysis-campaign | candidate refs、comparison refs、reviewer briefing | current delta 需要时调用 |
| literature / source search | scout、source readiness、write repair | source refs、query refs、limitation refs | route-required 或 payload-present |
| citation / claim locator | write、review、publication gate | claim-support refs、locator audit refs、repair hints | 当前 claim / gate 需要时调用 |
| figure / display QA | display、publication package | manifest refs、integrity warning refs、caption binding refs | 当前 artifact / gate 需要时调用 |
| style / overclaim / argument review | write、review | warning refs、claim-boundary hints、reviewer briefing | reviewer / owner route 需要时调用 |
| tool selector / observation memory / failed-path taxonomy | runtime smoothness、repair loop | refs-only hints、no-loop signal、memory reuse candidate | fail-open sidecar |

所有 capability 都必须声明：

- input refs
- target stage / owner action
- allowed writes
- forbidden authority
- output ref family
- fail-open / hard-gate candidate 条件
- current work-unit identity binding
- owner-consumption / live-soak evidence shape
- no-new-default-next-action 约束

### 5. Agent Tool Arsenal / Capability Invocation OS

MAS 的所有 CLI、MCP、skill、domain-handler、owner callable、sidecar、native helper 和 OPL hosted action，长期都应被 agent 当作一组按当前任务动态发现的工具，而不是被人类用户阅读、记忆和手动组合。

当前实现状态：

- `src/med_autoscience/action_catalog.py` 当前生成 MAS action catalog，已经表达 action id、effect、command、surface kind、MCP tool name、workspace locator fields 和 authority boundary；具体 action 集合以 `contracts/action_catalog.json` 为机器真相。
- `src/med_autoscience/mcp_server_parts/tool_registry.py` 当前暴露 10 个 MCP task tools；`study_progress`、`display_pack_agent`、`scientific_capability_registry`、`authority_operations` 和只读 `agent_tool_arsenal` 已携带 `outputSchema` 与 tool annotations，`display_pack_agent` 以 `discover / orchestrate / plan / preflight / render` mode 聚合绘图资产包调用，`scientific_capability_registry` 以 `index / resolve / invoke` mode 聚合外部科学能力与 refs-only advisory worker 调用，`agent_tool_arsenal` 支持读取 index、card、soft `resolve`、hard invocation plan、result envelope schema 和 completeness diagnostic。成功 MCP call result 的 `structuredContent` 已统一为 `mas_tool_result_envelope`，原 payload 保存在 `structured_payload`；envelope 现在带 `recovery` 与顶层快捷字段，明确 retryability、missing refs、staleness、next safe actions、owner_needed、receipt/blocker/diagnostic refs 和 no-forbidden-authority proof；`doctor_audit`、`workspace_readiness`、`research_assets`、`publication_status`、`open_auto_research_soak` 和 `agent_tool_arsenal` 等非 action-card tools 由 diagnostic 显式标为 support / diagnostic MCP tools。
- `src/med_autoscience/runtime_control/owner_callable_registry.py` 当前表达 owner action 到 callable surface 的 required inputs / outputs / idempotency / fingerprint scope；`contracts/agent_tool_arsenal.json` 已把这些 owner callable 编成 `owner_callable_cards`，供 `current_owner_delta.action_type` 解析 invocation plan。
- `plugins/mas/skills/mas/SKILL.md` 仍是 direct path skill 约束和人读护栏；agent-facing 调用材料由 `contracts/agent_tool_arsenal.json` 和 MCP `agent_tool_arsenal` 读取，不要求 executor 读长 runbook 后自行拼装工具。
- `contracts/pack_compiler_input.json` 已请求 CLI / MCP / Skill / product-entry / domain-handler / status / workbench / harness generated surfaces，并把 `agent_tool_arsenal` source ref 指向 `src/med_autoscience/agent_tool_arsenal.py::build_agent_tool_arsenal_index`；`scientific_capability_registry` 已作为 callable/action catalog/MCP/CLI/product-entry ABI 落地。`contracts/agent_tool_arsenal.json` 的 counts 是 invocation ABI / card counts，不是 OPL brand module counts；新增合同字段只作为生成/校验材料，Agent ordinary path 只消费 `AgentExecutionIndex`、`discovery_hint`、`fit_signal`、`invocation_gate`、`adaptation_policy`、`OperationalToolCard`、`CapabilityResolverReceipt`、`CapabilityInvocationPlan.primary_operational_card` 和 `ToolResultEnvelope.recovery`。OPL 十大品牌模块 taxonomy 以 OPL repo 为 owner truth，MAS 只消费 projection / handler boundary；Capability Invocation OS 折回 Pack / Atlas / Stagecraft / Console / Connect / Runway，不新增第 11 模块。剩余尾项是 hosted OPL ordinary-path live soak、direct/hosted parity、live current-owner-delta soak 和 hosted OPL ordinary-path 对这些 ordinary execution views 的消费验证。
- `lightweight_executor_receipt` 已从 descriptor-only contract 扩展为 L0/L1 可用 evidence 面：`src/med_autoscience/lightweight_executor_receipts.py` 能从 `ToolResultEnvelope` 或 default executor evidence dict 生成 refs-only receipt，记录 tool/action status、stdout/stderr refs、output refs、failure class、env fingerprint 与 isolation diagnostic；`ToolResultEnvelope` / `CapabilityInvocationPlan` / `ToolUseCard` 已暴露可选 `executor_receipt_ref` 和 `lightweight_executor_receipt_contract_ref`。默认只承认 `L0_host_clean_runner` / `L1_process_workspace` 的 Codex / `uv` clean runner / process-workspace evidence；Docker / OpenHands 仍只允许显式 `L3_containerized_sandbox` proof lane，inside-container 默认不启用 Docker / DinD / Docker socket。该 receipt 不执行命令、不新增 external runtime 或 admission gate，也不能写 owner receipt、typed blocker、publication eval、controller decisions、current package、submission package、stage closeout、quality verdict 或 artifact authority，缺 receipt 不阻断 current owner action。

目标接口：

| Surface | Owner | 目标职责 |
| --- | --- | --- |
| `ToolArsenalIndex` | OPL generated, MAS declares domain intent | 只给 agent 一个 compact index：capability family、stage/action applicability、risk class、effect、required refs、load detail pointer。 |
| `AgentExecutionIndex` | OPL generated, MAS declares domain intent | Agent 热路径的短索引，只暴露 tool id、适用语义、required refs、risk 和 next step hint；不要求 Agent 读取原始合同。 |
| `ToolUseCard` / `OperationalToolCard` | OPL generated, MAS authority bounded | 单个工具的完整 card 与可执行操作子集：when to use、when not to use、default invocation、required/optional refs、preflight checks、success signals、failure classes、next safe actions、allowed writes、forbidden authority 和 output schema。 |
| `CapabilityResolverReceipt` | OPL resolves, MAS bounds | soft discovery 保候选、scored fit 给解释、hard invocation gate 给 missing refs / blocker candidate；resolver 不执行工具、不签 authority。 |
| `CapabilityInvocationPlan` | OPL resolves, MAS bounds | 从 `current_owner_delta` 生成一个 primary operational card、少量 fallback、调用顺序、hard gate 条件、human approval requirement 和 no-new-default-next-action 约束。 |
| `ToolResultEnvelope` | Tool returns, OPL stores refs, MAS consumes authority refs | 所有工具结果统一返回 status、output refs、diagnostic refs、receipt refs、typed blocker candidate、error class、`recovery`、retryability、idempotency key 和 no-forbidden-authority proof。 |
| `ToolAuditTrail` | OPL observability / lineage | 记录 agent 为什么选择该工具、输入 refs、输出 refs、model/tool/handoff id、duration、failure class 和 follow-up owner delta；不能签 MAS authority。 |

设计原则：

1. `current_owner_delta` 是唯一 ordinary planning root。Agent 先读当前 owner / action / desired delta / hard gate，再解析工具；不能从全局工具清单或历史 worklist 反推下一步。
2. 工具发现和调用分三层。找工具阶段 soft match / high recall，不因缺 `required_refs` 丢候选；选工具阶段 scored / explainable，返回 fit reasons、missing refs 和 next safe actions；真正调用阶段 hard contract / fail closed，required refs、allowed writes、forbidden authority、human gate 和 owner receipt / typed blocker requirement 必须满足。
3. 工具描述必须面向模型。每个 card 写清任务语义、适用条件、反例、输入 ref contract、输出 ref family、常见失败、最小 examples 和验证方式；短命令名、CLI 习惯或人类 runbook 不算 agent affordance。
4. 风险注解必须机器可读。至少包括 `read_only`、`mutating`、`destructive_candidate`、`idempotent`、`open_world`、`requires_human_gate`、`requires_opl_stage_attempt_or_lease`、`can_write_domain_truth=false/true`、`can_sign_owner_receipt=false/true`。
5. 结构化输出是硬门。tool 没有 `outputSchema` / `ToolResultEnvelope` 时只能作为 diagnostic 或 legacy target；进入 ordinary path 的工具必须能返回 owner receipt、typed blocker、quality gate receipt、human gate、route-back evidence、refs-only advisory 或 explicit no-op。
6. 人类用户只管理目标、授权和异常。用户不需要知道哪个 CLI / MCP / helper 应该怎么拼；human gate 只出现在不可逆 mutation、外部提交、敏感凭据、publication/submission/export、artifact mutation 或 route-required authority 缺口上。
7. 工具失败默认变成可接力结果。失败必须在 `ToolResultEnvelope.recovery` 里产出 typed blocker candidate refs、route-back evidence、retryability、missing ref family、diagnostic refs、owner-needed signal 或 platform repair delta；不能只给 stderr 或长文本。
8. OPL 负责调用丝滑度，MAS 负责医学边界。OPL 处理 discovery、deferred loading、task execution、session state、approval interrupt、observability、retry/dead-letter；MAS 只声明工具能否写 domain truth、签 receipt、产生 blocker、消费 refs 或触发 reviewer / human gate。

理想调用链：

1. Agent 读取 `current_owner_delta`。
2. OPL `AgentExecutionIndex` 根据 stage、owner action、required refs、failure class 和 available context 返回短候选；需要细节时延迟加载对应 `OperationalToolCard`。
3. Agent 或 OPL resolver 选择最小工具集，形成带 `primary_operational_card` 的 `CapabilityInvocationPlan`。
4. Tool 执行并返回 `ToolResultEnvelope`。
5. MAS owner surface 只消费符合 authority boundary 的 refs、receipt、blocker、quality gate 或 human gate；sidecar/advisory refs 只进入 reviewer briefing 或 next owner input。
6. OPL State Index / Workbench 投影 next `current_owner_delta`，audit trail 进入 drilldown。

## 核心合同形状

目标态应把以下合同固定为 OPL / MAS 的共同语言。

| Contract | Owner | 用途 |
| --- | --- | --- |
| `DomainAgentPack` | MAS declares, OPL compiles | 声明 stage、skill、knowledge、quality gate、action、receipt refs、forbidden authority |
| `StageRun` | OPL lifecycle, MAS semantic refs | 表达 stage attempt、manifest、input/output refs、current pointer、owner closeout |
| `CurrentOwnerDelta` | MAS owner truth, OPL projection | 默认读面；说明当前 owner、action、target surface、required delta、hard gate |
| `ProgressDeltaReceipt` | MAS / executor output | 记录非终局 concrete delta，接力下一 owner；不替代 full owner receipt |
| `OwnerReceipt` | MAS authority | 关闭 owner action 或 stage transition 的 domain receipt |
| `TypedBlocker` | MAS / gate owner | 命名 blocker、route-back owner、repair condition、avoided forbidden shortcut |
| `HumanGate` | MAS declares, OPL transports | 明确人类决策项、可选动作、resume token、超时处理 |
| `ToolArsenalIndex` | OPL generated, MAS domain intent | 按 current delta 暴露 compact tool candidates，避免全量工具上下文噪声 |
| `AgentExecutionIndex` | OPL generated, MAS domain intent | Agent 热路径短索引；从合同生成，不要求直接读合同 |
| `ToolUseCard` / `OperationalToolCard` | OPL generated, MAS bounded | 描述单个工具何时用、何时不用、输入输出、风险注解、default invocation、recovery hint、examples 和验收 |
| `CapabilityInvocationPlan` | OPL schedules, MAS bounds | 当前 delta 触发 capability 的 inputs、question、budget、output refs |
| `ToolResultEnvelope` | Tool / OPL / MAS owner surface | 统一 status、output refs、receipt/blocker refs、error class、recovery、retryability 和 no-forbidden-authority proof |
| `ProvenanceEnvelope` | MAS / OPL refs-only | entity / activity / agent / dataset / run / artifact lineage refs |
| `ObservabilityEvent` | OPL | trace / metric / log / failure class；永不直接授权 domain verdict |
| `AuthorityKernelInventory` | MAS authority kernel | 用机器可读 inventory 固定 retained authority function 的 category、owner、active caller、allowed writes、forbidden authority、output refs、不能上收原因和 retirement / upcollect target；它不声明 authority 已退役或 production-ready。 |

## 重构 Lane

### Lane 0：文档与合同入口收敛

目标：把目标态、owner split、迁移顺序和完成门固定在 canonical docs。

写面：

- `docs/runtime/designs/mas_opl_agent_os_target_operating_architecture.md`
- `docs/active/mas-ideal-state-gap-plan.md`
- `docs/status.md`
- `docs/architecture.md`
- `docs/project.md`
- `docs/invariants.md`
- `docs/decisions.md`

完成门：

- 所有入口都指向同一目标态：`OPL Agent OS + MAS Declarative Medical Research Pack + MAS Minimal Authority Kernel + Scientific Capability Registry`。
- 文档明确区分功能/结构改造与测试/证据尾项。
- `git diff --check` 与 conflict-marker scan 通过。

### Lane 1：Pack Compiler 与 generated surface 收敛

目标：让 `agent/` 成为 MAS semantic pack 单一来源，OPL 从 pack 生成 CLI / MCP / Skill / product-entry / workbench / action descriptors，并生成 Agent Tool Arsenal 的 compact index 与 tool cards。

实施步骤：

1. 定义 `DomainAgentPack` machine contract，列出 required stage / skill / knowledge / quality gate / action / receipt refs。
2. 把现有 action catalog、stage route、quality contracts、generated surface handoff 对齐到该 contract。
3. 给 direct MAS skill path 和 OPL-hosted path 加 parity fixture：同一 action 必须落到同一 MAS owner surface。
4. 把 repo-local wrapper 标记为 generated target / authority function / diagnostic ref / tombstone 四类。
5. `contracts/agent_tool_arsenal.json` 已从 action catalog、owner callable registry、stage route、MCP registry 和 plugin skill 汇总 `ToolArsenalIndex` / `ToolUseCard` / `CapabilityInvocationPlan` / `ToolResultEnvelope` / `ToolAuditTrail` 的 machine-readable ABI；MCP `agent_tool_arsenal` 已提供 `completeness_diagnostic`，实际 tool call result 也已返回 `mas_tool_result_envelope`。`scientific_capability_registry` 已新增 repo-side owner-consumption / live-soak evidence packet shape，用于记录 current owner delta identity、capability output refs、owner response refs、no-forbidden-write proof 和 fail-open flags。后续只按 OPL resolver/runtime 消费、parity 和真实 owner evidence 扩展。

验收：

- OPL conformance 能从 pack 发现 MAS stage/action/quality/handoff。
- hand-written generic wrapper 不再作为长期 owner。
- 新 stage 只改 pack / contract，不改 runtime scheduler。
- Agent 能通过 MCP `agent_tool_arsenal` 从 `current_owner_delta` 读取 index、card、plan、result schema 或 completeness diagnostic，并通过 MCP/CLI `scientific_capability_registry` 读取或调用 current-delta-bound refs-only capability；repo-side module API 能生成 refs-only owner-consumption / live-soak evidence packet；hosted OPL resolver/runtime 后续负责把该 ABI 接入 ordinary invocation path。

### Lane 2：OPL StageRun / durable execution 上收

目标：通用 stage attempt、queue、retry、resume、human gate transport、provider query 全部由 OPL 承担。

实施步骤：

1. 把 MAS 内仍像 attempt loop / queue / scheduler / worker residency 的模块分类。
2. 对 active caller 给出 replacement：OPL StageRun primitive、provider transport、human gate transport 或 generated caller。
3. MAS retained code 只保留 owner receipt / typed blocker / diagnostic refs / authority function。
4. 删除或 tombstone 无 active caller 的 legacy scheduler / local runtime wrapper。

验收：

- MAS 不再新增 generic daemon、scheduler、queue、retry/dead-letter、resume owner。
- OPL provider completion 只能作为 transport evidence，不能关闭 MAS domain verdict。
- 缺 OPL execution authorization 时 MAS apply fail closed 到 typed blocker。

### Lane 3：CurrentOwnerDelta 唯一默认读面

目标：operator / executor 默认只看当前 owner、当前 action、target surface、required delta、hard gate。

实施步骤：

1. 把 study progress、domain-handler export、product-entry、workbench 默认字段统一到 `current_owner_delta`。
2. worklist、receipt replay、raw provider trace、sidecar output、private residue 进入 audit plane。
3. currentness reducer 只承认 matching work-unit id、fingerprint、allowed action 和 idempotency key。
4. stale read-model / duplicate receipt / old route-back 只能作为 lineage 或 ignored diagnostic。

验收：

- `current_owner_delta` 不因 zero worklist 消失。
- running proof、typed blocker、executable owner action 三者优先级明确。
- stale projection 不能导出 ordinary pending task。

### Lane 4：MAS Authority Kernel 收薄

目标：把 MAS 程序面压到最小医学 authority function 和 refs-only helper。

当前机器落点：`contracts/authority_kernel_inventory.json` 与 `src/med_autoscience/authority_kernel_inventory.py::build_authority_kernel_inventory` 已把 retained authority kernel inventory 落为 repo-native read model。inventory 覆盖 owner receipt signer、typed blocker materializer、source readiness、publication quality gate、artifact mutation authorization、publication-route memory accept/reject、no-forbidden-write proof、refs-only helper 和 diagnostic probe 的 representative surfaces，并固定 owner、active caller refs、allowed writes、forbidden authority、output refs、cannot-lift-to-OPL reason 与 retirement / upcollect target。该 landing 只关闭分类和读面合同缺口；后续仍要按 inventory 做物理收薄、删除旧 wrapper / residue、OPL upcollect 消费和真实 paper-line evidence 验证。

实施步骤：

1. 以 `contracts/authority_kernel_inventory.json` 为分类入口，持续维护每个 retained function 的 owner、active caller、cannot-lift-to-OPL reason、allowed writes、forbidden authority、output refs。
2. 把开放式医学判断移到 AI reviewer / auditor / stage executor；函数只做校验、签收、物化、索引、阻断。
3. 对 source/data/artifact/memory/publication authority 分别建 boundary fixture。
4. 删除只为旧 wrapper /旧 alias /旧 compatibility test 服务的代码。

验收：

- 每个 retained MAS function 都可归类为 authority function、domain handler target、refs-only projection、native helper、diagnostic probe 或 fixture。
- 程序不能直接生成 publication quality verdict，必须消费 independent reviewer/auditor record。
- inventory 通过 focused contract tests 后，只能声明 `inventory_landed_physical_thinning_pending`；不能声明 authority fully retired、production-ready、paper-line progress、publication-ready 或 artifact mutation authorized。

### Lane 5：Evidence / lineage plane

目标：把 scientific evidence、artifact lineage、data lineage 和 runtime provenance 作为 refs-only 一等对象。

实施步骤：

1. 定义 `ProvenanceEnvelope`：entity、activity、agent、source refs、artifact refs、input/output refs、digest。
2. 对 data release / analysis job / figure / table / manuscript claim / review decision 引入 lineage refs。
3. 把 artifact body 与 locator/index/read-model 分离；SQLite 只做 refs index。
4. 对 failed path、negative result、superseded path、route decision 建 body-free packet。

验收：

- package、figure、claim、analysis result 能追到 source/data/evidence/review refs。
- lifecycle cleanup / restore plan 不能反推 study truth。
- lineage 存在不等于 quality / publication ready。

### Lane 6：AI-first Quality OS

目标：executor 和 reviewer/auditor 独立 invocation，质量门可审计。

实施步骤：

1. 固定 reviewer / auditor task record schema：input refs、artifact refs、rubric refs、context id、output receipt。
2. publication eval 必须带 independent reviewer / auditor provenance 和 current manuscript digest。
3. executor 自审只作为 repair hint，不关闭 gate。
4. reviewer route-back 必须产生 next owner delta、quality gate receipt 或 typed blocker。

验收：

- 缺 independent reviewer/auditor record 时，quality closure fail closed。
- reviewer record stale 时，不能关闭 publication-ready。
- reviewer route-back 不变成无限 review loop；必须接到 owner delta 或 blocker。

### Lane 7：Scientific Capability Registry

目标：吸收外部系统能力，并让 agent 按当前 delta 丝滑调用工具，但不增加 ordinary path 摩擦。

实施步骤：

1. 把 selector / resolver 归入 OPL `W3-capability-registry-fail-open`：由 `Atlas + Pack + Stagecraft` 表达 capability catalog、pack ABI、current-delta-bound use policy 和 fail-open / fail-blocker 规则；MAS 仓内已提供 OPL-owned consumption ABI 的 repo-native surface `scientific_capability_registry`。
2. MAS 只在 pack / authority kernel 中声明每个 external-learning ref family 的 target stage、owner action、input refs、output ref family、allowed writes、forbidden authority 和 owner-consumption boundary。
3. 将 Co-Scientist、Light、EvoScientist、PaperSpine、ARIS、ARK、AutoSci 等统一纳入 capability / advisory worker family；不能在 MAS 内再建私有 selector、always-on sidecar、第二 route table 或第二 active backlog。
4. capability invocation 必须绑定 current work-unit identity、target surface、requested ref family / question 和 `no_new_default_next_action`。
5. capability resolver 必须返回 `CapabilityInvocationPlan` 和 `ToolUseCard`，包含预算、risk annotations、human gate 条件、output schema、receipt/blocker shape 和 failure class。
6. missing capability 默认 fail open；只有 route-required ref 命中 hard gate 才升级 typed blocker candidate，正式 typed blocker 仍由 MAS owner / reviewer / human gate 物化。
7. capability owner-consumption evidence packet 必须保持 refs-only：记录 current owner delta identity、capability output refs、owner receipt / typed blocker / reviewer receipt / route-back refs、no-forbidden-write proof 和 fail-open flags；缺 owner refs 不阻塞，带 owner refs 也不直接授权 progress。

验收：

- 新 capability 不新增默认 preflight。
- sidecar / advisory worker 不生成 current owner，不写 owner receipt，不写 paper progress。
- owner-consumption / live-soak evidence shape 已在 repo-side `scientific_capability_registry` API 与 focused tests 落地；owner-consumed refs 仍必须由真实 owner receipt、typed blocker、reviewer receipt 或 route-back evidence 才能计入当前 delta。
- Agent 工具调用不要求用户理解具体 CLI/MCP/helper；用户只看到目标、授权、人类决策和异常。
- Capability registry 的 MAS repo structure 已由 `scientific_capability_registry` 的 action catalog、MCP runtime、CLI、Agent Tool Arsenal、owner-consumption evidence API 和 focused tests 证明；hosted OPL ordinary-path consumption evidence 已由 `contracts/hosted_ordinary_path_consumption.json` 与 MCP `agent_tool_arsenal(mode=hosted_consumption)` 落地。ARS claim-support、AutoSci source discovery、ARK micro-canary 等真实进度晋级仍由 live owner receipt / typed blocker / reviewer receipt 证明。

### Lane 8：OPL Workbench / Operator UX

目标：用户看到研究推进，不被 audit tail 淹没。

实施步骤：

1. 默认屏只显示 study line、current owner delta、paper/evidence/artifact progress、human gate、next safe action。
2. Audit drilldown 分层显示 lineage、provider trace、sidecar refs、raw worklist、receipt replay、lifecycle details。
3. 所有 action button 必须路由到 owner action 或 human gate，不能直接改 artifact authority。
4. Progress-first 分类拆开：paper progress、evidence progress、artifact progress、platform repair、human wait、hard blocker。

验收：

- zero worklist 不能写成 domain ready。
- platform repair 不写成 paper progress。
- UI / workbench projection 不能直接授权 publication-ready 或 artifact mutation。

### Lane 9：Production evidence 与 soak

目标：从 contract landed 推进到真实 paper-line / provider / reviewer / artifact evidence。

实施步骤：

1. 选择 2-3 条真实 paper line，跑 owner-chain canary。
2. 记录 provider restart / resume / retry / dead-letter / human gate transport。
3. 产出 owner receipt、typed blocker、reviewer/auditor record、artifact lineage、memory writeback receipt 或 route-back evidence。
4. 把 production evidence 拆成 structural conformance、runtime SLO、domain progress、publication readiness 四类，不混写。

验收：

- OPL provider long soak 不等于 MAS paper closure。
- paper-line closeout 必须来自 MAS owner receipt / quality gate receipt / typed blocker / human gate / route-back evidence。
- 每条 canary 都能重建 evidence refs 与 no-forbidden-write proof。

## 推荐迁移顺序

1. **文档和目标合同先固定**：完成 Lane 0，避免后续实现各自解释目标态。
2. **Pack / generated surface 先收敛**：完成 Lane 1，让新增能力都进入同一个 semantic source。
3. **默认读面先变薄**：推进 Lane 3，减少 operator / executor 摩擦。
4. **OPL substrate 与 MAS authority 同步拆分**：Lane 2 和 Lane 4 并行，但写集要分离。
5. **Evidence / Quality / Tool Arsenal / Capability 四条线接入**：Lane 5、6、7 按 stage owner 需要逐步补齐。
6. **Workbench 与 production soak 最后验收**：Lane 8、9 证明用户体验和真实长跑证据。

这不是阶段式停顿，而是并行 lane 的优先级。每条 lane 都必须有 disjoint write set、source of truth、验证命令、stop condition 和 forbidden scope。

## OPL 基座需要优化的接口

| OPL primitive | 目标接口 | MAS 消费方式 |
| --- | --- | --- |
| Pack Compiler | `compile_domain_agent_pack(pack_root)` | 从 MAS `agent/` 和 `contracts/` 生成 hosted surfaces |
| StageRun Kernel | `start/query/signal/closeout_stage_run` | MAS 只消费 attempt refs、lease refs、closeout binding |
| State Index Kernel | `rebuild/read/checkpoint refs index` | MAS 提供 file truth / receipt refs；OPL 生成 read model |
| Route Reconciler | `reconcile_current_owner_delta` | 只对齐 desired/current，不生成医学 verdict |
| Tool Arsenal | `list_tool_cards_for_current_delta` / `load_tool_card` / `invoke_tool_with_envelope` | 给 autonomous agent 低摩擦工具发现、延迟加载、结构化调用和结果 envelope |
| Capability Registry | `resolve_capability_for_current_delta` / `invoke_capability_for_current_delta` | OPL 选择 current-delta-bound capability；MAS 只消费 refs-only advisory / candidate / briefing |
| Human Gate Transport | `open/answer/resume human_gate` | MAS 声明 gate，OPL 承运，MAS 消费 answer refs |
| Lifecycle Plane | `locate/retain/restore/gc refs` | MAS 授权 artifact mutation，OPL 执行 generic lifecycle |
| Observability Plane | `trace/metric/log/failure_class` | MAS 只读诊断，不把 observability 当 authority |
| Workbench Shell | `render_current_owner_delta + audit drilldown` | 默认显示 next action，drilldown 显示 audit refs |

## MAS 需要优化的接口

| MAS surface | 目标接口 | OPL 消费方式 |
| --- | --- | --- |
| Stage pack | `agent/stages/*.yaml|md` | OPL compile / discovery |
| Agent tool affordance | action catalog + owner callable + stage refs + MCP registry | OPL 生成 ToolArsenalIndex / ToolUseCard；MAS 声明 authority boundary 和 result shape |
| Authority functions | `runtime/authority_functions/*` / `src/...` | OPL dispatch 回 MAS owner surface |
| Owner route | `current_owner_delta` | OPL 默认读面和 stage admission |
| Receipt / blocker | `OwnerReceipt` / `TypedBlocker` | OPL closeout / workbench / retry decision |
| Source/data binding | source readiness / data asset contract refs | OPL 只索引 locator，不裁决医学可用性 |
| Quality OS | reviewer/auditor record refs | OPL 展示和 route-back，不签 verdict |
| Artifact OS | artifact mutation authorization / rebuild proof | OPL lifecycle 执行前必须取 MAS authority |
| Memory OS | publication-route memory receipt refs | OPL 运输 refs，不读取或裁决 memory body |

## 验收门

### Functional / structural gate

- 新 runtime-like 功能必须归 OPL primitive；MAS 只留 authority function 或 refs-only projection。
- 新 agent-facing 工具必须有 ToolUseCard、risk annotations、output schema、ToolResultEnvelope 和 current-delta applicability。
- 新 external-learning 功能必须进入 OPL Capability Registry；MAS 不能新增私有 selector、第二 active backlog、always-on sidecar 或默认 preflight。
- 新 workbench / status surface 默认显示 `current_owner_delta`；audit detail 不能抢默认入口。
- 新 lifecycle / artifact / memory 功能必须证明 body / refs / index / authority 分离。

### Evidence gate

- 每个真实 paper-line canary 至少产出一种：owner receipt、quality gate receipt、typed blocker、human gate、route-back evidence、artifact lineage、memory writeback receipt。
- 每个 provider-hosted long run 必须能证明 restart / resume / retry / dead-letter / no-forbidden-write。
- 每个 reviewer / auditor gate 必须有独立 invocation 和 current artifact digest。

### Anti-regression gate

- `current_owner_delta` 不得被 worklist 空、sidecar 缺失、old dispatch 或 stale read-model 覆盖。
- external advisory 缺失默认 fail open。
- observability、lineage、provider completion、queue completion、descriptor ready 都不能声明 paper closure。
- MAS function 不得重新持有 generic scheduler、queue、worker residency、session store、workbench 或 private lifecycle owner。

## 禁止事项

- 不新增 MAS 私有 runtime platform。
- 不把 Co-Scientist / Light / EvoScientist runtime 引入为 dependency。
- 不把 sidecar / advisory / score / ranking / checklist 写成 authority。
- 不把 external-learning 后续优化写成 MAS standalone selector / backlog；selector / resolver 归 OPL Capability Registry，MAS 只声明 domain consumption 与 authority 晋级。
- 不把 full readiness inventory 变成每个 delta 的默认前置门。
- 不把工具说明写成人类操作手册后要求 agent 自己推理；agent-facing 工具必须由 pack/compiler 生成可机器消费的 card、schema 和 result envelope。
- 不让 OPL State Index / SQLite / read-model 保存 artifact body、memory body、study truth 或 publication verdict。
- 不让同一个 executor agent 自审后关闭 AI-first quality gate。
- 不用 provider completion、queue completion、zero worklist、workbench 可见性或 docs 描述声明真实 paper-line 完成。

## 下一步执行地图

当前推荐从以下最小闭环开始：

1. **Lane 0 docs landing**：本文和核心入口落地，作为目标态 source of truth。
2. **Lane 1 contract inventory**：列出 `DomainAgentPack` 所需 machine contract 和现有来源差距。
3. **Lane 1 tool arsenal consumption tail**：`contracts/agent_tool_arsenal.json` 已把 action catalog、MCP tool、owner callable registry、plugin skill、stage route 和 `scientific_capability_registry` 映射成 ToolArsenalIndex / ToolUseCard / CapabilityInvocationPlan；`display_pack_agent` 已从 CLI/domain-handler descriptor 升级为聚合 MCP runtime，`scientific_capability_registry` 已把 external-learning sidecar、Light advisory、Evo sidecar、Co-Scientist affordance 和 Display Pack 折成 public MCP/CLI/product-entry capability runtime，并提供 repo-side refs-only owner-consumption / live-soak evidence packet；`hosted_ordinary_path_consumption` 已把 OPL hosted ordinary path 所需 consumption evidence 接到 MCP `agent_tool_arsenal(mode=hosted_consumption)`。下一步是 direct/hosted parity 和真实 paper-line owner-consumed refs。
4. **Lane 3 default read-surface audit**：检查所有默认 status/export/workbench 是否只以 `current_owner_delta` 为首屏。
5. **Lane 4 authority function inventory**：`contracts/authority_kernel_inventory.json` 已给 retained MAS functions 补 owner / allowed write / forbidden authority / output ref 分类；下一步按该 inventory 做物理收薄、旧 residue 删除门、OPL upcollect consumption 和真实 evidence 验证。
6. **Lane 7 capability registry runtime ABI**：existing external-learning sidecar、Light advisory、Evo sidecar、Co-Scientist affordance 和 Display Pack capability 已折回 `scientific_capability_registry`，MAS 提供 current-delta-bound `index / resolve / invoke` ABI、allowed writes、forbidden authority、owner receipt / typed blocker 晋级边界、owner-consumption / live-soak evidence shape 和 hosted OPL consumption evidence；剩余是真实 owner evidence 和 direct/hosted parity。
7. **Lane 9 real canary selection**：选择真实 paper-line evidence target，不用 repo tests 代替 production evidence。

每个 lane 的完成声明必须写清：功能/结构是否关闭，测试/证据是否关闭，是否仍需真实 paper-line / provider / reviewer / human gate 证据。
