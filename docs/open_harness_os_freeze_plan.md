# Open Harness OS Freeze Plan

这份文档定义 `MedAutoScience` 在走向开放 `Harness OS` 过程中，哪些东西现在可以冻结，哪些东西不能冻结，以及它们分别依赖哪些主线收口。

它的目标不是宣布“系统已经定型”，而是避免把不同层级的冻结混成一件事。

当前正式判断是：

- 现在可以冻结 `L1`：顶层架构与 authority 原则
- 现在不能冻结 `L2`：core 与 medical pack 的细粒度 vocabulary 边界
- 现在更不能冻结 `L3`：machine-auditable schema / package / public contract 边界

## 为什么要分层冻结

当前仓库的唯一顶层主线已经固定为：

- `research-foundry-medical-mainline`
  - 当前 phase：`harness authority convergence`
  - 当前唯一活跃子线：`publication eval minimal schema`

与此同时，以下子线继续作为 inherited truth surface 提供 L2/L3 冻结所需输入：

- `medical-display-template-mainline`
  - 继续提供 medical delivery / publication pack 的收口事实
- `monorepo-transition-program`
  - 已完成 `study charter artifact carrier`
  - 已完成 `runtime escalation record` 的最小 clean-worktree 验证与 integration handoff
  - 当前向本主线提供 publication-eval 之前置 authority truth

因此，“冻结”必须分三层理解：

- 方向可以先冻结
- 术语表不能过早冻结
- schema 不能在 contract 仍活跃演化时冻结

## L1：Architecture Freeze

### 含义

`L1` 冻结的是顶层架构与 authority 原则。

这一层回答的是：

- `MedAutoScience` 在 `OPL` 里是什么
- future `Harness OS` 应如何理解
- `gateway`、`harness OS`、`runtime`、`eval`、`delivery` 之间谁归谁管
- medical system 与 future open system 的关系是什么

### 当前状态

`L1` 已可以视为冻结。

当前冻结结论以这份文档为准：

- [Open Harness OS Architecture](./open_harness_os_architecture.md)

### 当前冻结内容

- `MedAutoScience` 继续是 `Research Ops` 的 `domain gateway`
- `MedAutoScience` 对内继续是 `medical domain harness OS`
- future 开放路线不是“把医学语义原样推广”，而是：
  - `Harness OS core + domain packs`
- `MedAutoScience` 继续承担：
  - medical reference implementation
  - medical domain pack
- `OPL` 继续位于 domain gateway 之上，不替代 domain gateway
- authority 顶层边界继续保持：
  - controller authority
  - runtime authority
  - eval authority
  - delivery authority

### 变更门槛

`L1` 一旦变更，就不应被视为普通实现细节调整。

只有在以下情况下才允许改动：

- 出现新的顶层 federation 约束
- 第二个真实 domain 的验证结果证明当前三层结构不成立
- 需要显式新的 architecture PRD / spec 收口

也就是说：

- `L1` 不是“永远不变”
- 但它已经不应随着 display / runtime 的日常实现细节继续摇摆

## L2：Vocabulary Freeze

### 含义

`L2` 冻结的是：

- 哪些词属于 `Harness OS core`
- 哪些词属于 `medical domain pack`
- 哪些对象只能是 projection
- 哪些对象可以是 authority artifact

这一层回答的是“术语与对象归属”。

例如：

- `study_charter`
  - 是否明确属于 controller authority
- `runtime_escalation_record`
  - 是否明确属于 runtime authority
- `startup_contract`
  - 是否明确只做 projection，而不是 authority root
- `publication eval`
  - 哪些部分属于 core verdict substrate，哪些属于 medical publication pack
- `submission_companion`
  - 它是 medical delivery surface，还是 future core delivery substrate 的一部分

### 当前状态

`L2` 现在不能整体冻结。

原因不是方向不清楚，而是对象级 vocabulary 仍同时受 inherited display truth 与当前 authority-convergence 子线收敛影响。

### 当前仍在活跃变化的区域

#### 来自 display 主线

- `submission_graphical_abstract` 的正式注册
- `submission_companion` 进入 figure renderer semantics contract
- `002` 的 reporting / publication / registry 基础合同
- `Phase C / Phase D` 真课题 materialization 与 publication-facing semantics

这些变化会直接影响：

- 哪些 surface 属于 medical delivery pack
- 哪些显示/交付对象只是 paper-local shell
- 哪些对象将来可能上升成通用 delivery substrate

#### 来自 monorepo inherited truth

- `runtime escalation record` 已完成最小 clean-worktree 验证与 integration handoff
- `publication eval minimal schema` 已形成首轮最小实现准入 contract，但尚未完成 L2 定型
- `charter-parameterized input contract` 尚未定型

这些变化会直接影响：

- `runtime` / `eval_hygiene` 的 vocabulary 边界
- controller projection 与 runtime truth 的术语边界
- core verdict object 是否能从 medical publication gate 中抽象出来

### L2 的冻结触发条件

只有当下面两类条件都满足时，才适合冻结 `L2`。

#### A. display 主线收口条件

至少应满足：

- `001 submission companion / graphical abstract contract` 已正式进入主线 contract
- `002` 已完成 `Phase C / Phase D` 的真实课题落地
- 当前论文展示面的主要 publication-facing semantics 不再处于高频改名/改归属阶段

#### B. monorepo 主线收口条件

至少应满足：

- `runtime escalation record` 已完成 clean integration 并回主线
- `publication eval minimal schema` 已形成首轮稳定 contract
- `charter-parameterized input contract` 已形成首轮稳定 contract

### L2 冻结后的目标产物

当 `L2` 可冻结时，应正式形成一份 machine-adjacent 但仍以人类可审为主的 vocabulary 边界文档，至少明确：

- `core nouns`
- `medical pack nouns`
- `projection-only objects`
- `authority objects`
- `runtime-owned objects`
- `eval-owned objects`
- `delivery-owned objects`

## L3：Schema Freeze

### 含义

`L3` 冻结的是：

- machine-auditable schema
- package layout
- public contract surface
- 更严格的 CLI / MCP / controller / artifact compatibility promises

这一层回答的是“程序表面是否可以长期稳定依赖”。

### 当前状态

`L3` 明确不能冻结。

当前还没有足够条件把这些 schema 宣布为稳定公共内核表面。

### 当前不能冻结的原因

- display 的 publication-facing objects 仍在继续收口
- publication eval 相关 contract 还没完成首轮 formalization
- charter parameterization 还没完成
- future core 与 medical pack 的 vocabulary 还未正式拆清

如果在这个阶段强行冻结 `L3`，结果通常会是：

- schema 名义上稳定，实际上不断破例
- core 与 medical pack 混叠进同一批 public artifacts
- 以后每次真收口都要打破所谓“冻结”

### L3 的冻结触发条件

至少应同时满足：

- `L2` 已完成冻结
- medical pack 的第一轮 publication / display / reporting 主线已稳定
- monorepo 的 core candidate contracts 已形成稳定边界
- 至少出现一个非医学 domain 候选，能够用来验证哪些 schema 真正属于 core

换句话说：

在没有第二个 domain pack 验证前，`L3` 最多只能局部冻结，不能宣布完成“开放 Harness OS schema freeze”。

## 当前正式执行策略

### 现在立刻执行

- 冻结 `L1`
- 继续允许 `L2`、`L3` 演化
- 不把日常 contract 改动误说成“架构不稳定”

### 当前 inherited truth surfaces 的职责

#### `medical-display-template-mainline`

负责把 medical publication / display / table / figure 的 domain pack 表面收紧清楚。

它当前不是在定义通用 core，而是在帮助未来回答：

- 哪些 publication surface 是 medical-only
- 哪些 delivery semantics 值得被 core 吸收

#### `monorepo-transition-program`

负责把 core 候选对象的 authority 与 contract 边界收紧清楚。

它当前不是在做全仓抽象，而是在帮助未来回答：

- 哪些 artifact 是 controller truth
- 哪些 artifact 是 runtime truth
- 哪些 verdict / escalation object 将来可以进入 core substrate

## 当前推荐口径

今后对外或对内讨论“冻结”时，推荐统一使用下面这条口径：

- `L1` 已冻结
- `L2` 待当前 inherited truth surfaces 与 active authority-convergence 子线收口后冻结
- `L3` 需在 `L2` 完成且出现第二个 domain 验证后再考虑冻结

这样做的好处是：

- 方向稳定
- 实现不被过早锁死
- 不会把活跃 contract 收口误判为架构漂移

## 结论

因此，关于“现在能不能冻结 Harness OS core 与 medical domain pack 的 vocabulary / authority 边界”，正式结论是：

- 可以冻结顶层架构与 authority 原则
- 不能冻结对象级 vocabulary 全表
- 更不能冻结 machine-level schema 全表
- 正确做法是按 `L1 -> L2 -> L3` 分层推进，而不是一次性宣布“全部冻结”
