# MedDeepScientist Runtime Protocol And Adapter Retirement Design

Date: `2026-04-02`

## Context

上一轮已经完成两件关键收口：

1. `med-deepscientist` 已经成为受控 fork，并且把当前主线优先级明确为 `MedAutoScience -> MedDeepScientist` 兼容性优先，而不是逐 commit 做 upstream intake。
2. `med-autoscience` 已经把 profile、runtime transport、CLI/MCP、workspace 文档和大部分 runtime contract 迁移到 `med-deepscientist` / `med_deepscientist_*` 命名。

但这条主线还没有真正闭合。

当前仍有两个核心缺口：

- `med-deepscientist` 的“最小稳定 runtime 面”仍然主要存在于测试和代码事实里，没有一份显式、可引用、可审计的 protocol spec。
- `med-autoscience` 里虽然生产代码主链已经基本绕过 `adapters/deepscientist/*`，但 adapter 兼容壳还在，且少量 `ops/med-deepscientist/...` 路径边界仍散落在 controller / protocol 帮助层里，没有收成更明确的协议配置。

这意味着现在的系统虽然已经比依赖 upstream `DeepScientist` 稳定得多，但还没有达到“边界清楚、协议清楚、退出路径清楚”的状态。

## Problem Statement

当前问题不是“功能不能跑”，而是“稳定边界还不够显式”。

具体有三类风险：

### 1. Runtime stability is still implicit

`med-deepscientist` 当前真正被 `med-autoscience` 依赖的稳定面，主要靠：

- daemon API 测试
- prompt builder 测试
- quest/worktree/paper 布局假设
- startup / continuation / stage gating 行为

来共同定义。

这对于实现层是够用的，但对于后续维护不够稳：

- intake 时很难快速判断一个变更是不是越界
- 上层很难明确知道哪些 route / payload / layout 可以依赖
- runtime 仍容易被当成“大产品壳”而不是“窄而稳定的执行 runtime”

### 2. Adapter retirement is not complete

`med-autoscience` 现在已经形成了更清楚的主链：

`controller -> runtime_protocol / runtime_transport -> med-deepscientist`

但 `adapters/deepscientist/*` 仍然存在，并继续暴露 legacy 名称。

这会产生两个负面效果：

- 从架构上看，系统仍像“有两套解释层并存”
- 从阅读体验看，维护者仍容易误以为 adapter 是正式真相源，而不是兼容壳

### 3. Layout knowledge is still too scattered

当前仍有少量 `ops/med-deepscientist/...` 路径假设分散在：

- `runtime_protocol.topology`
- `study_runtime_router`
- workspace / bootstrap / guide 文档

虽然这些路径已经比之前统一得多，但它们还没有被收成一个更明确的“workspace runtime layout contract”。

这会使未来的进一步抽象变难：

- controller 会继续背负路径知识
- runtime protocol 无法成为单一的 filesystem-facing truth
- workspace 迁移和 cutover gate 仍然只能部分依赖文档约束

## User-Level Requirements

本轮必须满足：

1. 不做大范围 engine rewrite，不引入新的 runtime core。
2. 不做“双写兼容”或保留长期旧名的降级处理。
3. 先把当前真实稳定面写实、写窄、写清楚，再继续删兼容层。
4. `med-deepscientist` 的 spec 必须足够明确，能够直接支撑后续 intake 审计和上层依赖判断。
5. `med-autoscience` 的 adapter 退役必须建立在已有测试回归之上，不得靠“先删再看哪里坏了”的试错方式。

## Scope

本次只覆盖两条强耦合主线。

### Workstream A: MedDeepScientist 最小稳定 runtime protocol 显式化

目标：

- 在 `med-deepscientist` 中新增一份显式 protocol spec
- 明确声明哪些 surface 是稳定 runtime contract
- 明确声明哪些 surface 仍属于非稳定产品面或上游兼容面

本次要覆盖的最小稳定面包括：

- daemon health / quest / control 的最小 route 与 payload shape
- quest / worktree / paper / document asset 的最小 layout contract
- startup / continuation / stage gating 的最小行为契约
- prompt/runtime contract 中 `med-autoscience` 实际依赖的字段与语义

本次明确不做：

- 不重命名 `deepscientist` Python package
- 不裁剪现有 router 的大产品面
- 不重写 daemon / turn loop
- 不引入版本协商或新的 transport 协议层

### Workstream B: MedAutoScience 继续退休 adapter 并收口 layout boundary

目标：

- 让生产控制路径彻底只依赖 `runtime_protocol` / `runtime_transport`
- 让 `adapters/deepscientist/*` 退化为可删的 legacy shim，或直接删除
- 把仍散落的 `ops/med-deepscientist/...` 路径知识收成集中协议配置

本次要覆盖的边界包括：

- adapter import 边界
- runtime root / daemon root / workspace runtime ops root 的关系
- startup payload / startup brief / behavior gate / runtime binding 等 project-local 路径

本次明确不做：

- 不把整个 runtime layout 变成完全 engine-neutral
- 不引入第二套 generic engine abstraction
- 不重做 workspace profile 模型

## Considered Approaches

### Option A. 先写 runtime spec，再按 spec 继续退休 adapter

做法：

- 先在 `med-deepscientist` 明确最小稳定 runtime protocol
- 再在 `med-autoscience` 用这份 spec 驱动 adapter retirement 与 layout boundary 抽取

优点：

- 先定义边界，再删兼容层，顺序正确
- 有利于 intake、review、回归和 cutover 共用同一套语言
- 风险最小，最贴合当前系统演化方式

缺点：

- 需要先做一轮文档与测试对齐，看起来推进速度略慢

结论：

- 这是本次选定方案。

### Option B. 直接在 `med-autoscience` 里先删 adapter，再倒推 spec

做法：

- 直接从上层把 `adapters/deepscientist/*` 继续删除
- 事后把剩下的 runtime 依赖总结成 spec

优点：

- 短期代码变更看起来更直接

缺点：

- 很容易把 spec 变成事后总结，而不是设计约束
- 不利于判断哪些 legacy 面可以删、哪些仍应保留

结论：

- 不选。

### Option C. 一步做到 engine-neutral runtime interface

做法：

- 同时抽象 runtime protocol、layout、transport 和 engine family

优点：

- 长期分层最干净

缺点：

- 改动面过大
- 当前没有必要，也没有足够证据说明需要立即支持第二个 engine

结论：

- 不选。

## Chosen Design

采用 Option A：

先把 `med-deepscientist` 的最小稳定 runtime protocol 显式写成 spec，并让回归测试与这份 spec 对齐；然后在 `med-autoscience` 中继续退休 adapter，并把散落的 `ops/med-deepscientist/...` 路径知识收成更明确的协议配置。

## Design

### A. MedDeepScientist: explicit minimal runtime protocol

新增一份稳定 protocol 文档，建议位置：

- `med-deepscientist/docs/runtime_protocol.md`

这份文档应按“稳定面 / 非稳定面”分区，而不是写成完整产品手册。

#### 1. Stable routes

明确列出 `med-autoscience` 当前可稳定依赖的 daemon surface：

- health
- create quest
- quest control
- active worktree document asset resolution
- workflow / layout / node traces / stage view 中被上层实际消费的部分

每个 route 至少写清：

- path
- method
- request payload shape
- response payload shape
- stability note

#### 2. Stable filesystem/layout contract

明确列出：

- quest root
- `.ds/worktrees/<worktree>/paper`
- active document asset lookup
- quest-local interaction / runtime state file

并写清哪些目录/文件是当前稳定 layout，哪些只是实现细节或不应由上层直接读取。

#### 3. Stable startup / turn contract

明确列出上层实际依赖的行为边界：

- startup contract 如何影响 turn intent / stage gate
- `review_audit` / `revision_rebuttal` 的允许入口
- algorithm-first 下 `experiment -> optimize` 的 gate 规则
- bootstrap question 与 structured bootstrap 的区别

这里不需要把所有 prompt 细节都文档化，只需要把上层依赖的 deterministic contract 写清。

#### 4. Non-stable product surfaces

明确标记以下内容当前不属于稳定 runtime protocol：

- UI branding / product shell
- 广泛 router 中未被 `med-autoscience` 使用的端点
- quest-local prompt 覆盖能力
- 其他仅供前台产品使用的扩展接口

这一步的目标不是删除它们，而是防止它们被误当成正式依赖面。

### B. MedAutoScience: adapter retirement and layout contract cleanup

#### 1. Production boundary

新增或强化架构约束：

- production code 不再 import `adapters.deepscientist.*`
- `adapters/deepscientist/*` 若保留，只允许作为 legacy shim
- 新增的 runtime consumer 一律走 `runtime_protocol` / `runtime_transport`

#### 2. Layout contract extraction

当前散落的路径知识要继续集中，建议把 workspace runtime layout 明确收成一层配置帮助函数或 dataclass，而不是继续散落字符串。

建议方向：

- 以 `WorkspaceProfile` 为输入
- 统一生成 `med-deepscientist` workspace ops root
- 再由此派生：
  - runtime root
  - startup brief root
  - startup payload root
  - behavior gate path
  - runtime binding related roots

这样：

- `study_runtime_router`
- `workspace_contracts`
- `workspace_init`
- 相关 guide / bootstrap 输出

都依赖同一套 layout contract，而不是重复写 `ops/med-deepscientist/...`

#### 3. Adapter exit sequencing

adapter retirement 采用三步走：

1. 先把 production imports 清零并用测试锁住
2. 再把 remaining shim 改成纯 re-export 或直接删除
3. 最后补文档，明确 adapter 已退出正式架构

这样可以避免“删掉 adapter 文件，但测试和维护心智还停留在旧结构”的半完成状态。

## Testing Strategy

### MedDeepScientist

至少补或强化：

- protocol spec 对应的 daemon API 回归
- prompt builder / stage gate 回归
- document asset / worktree layout 回归

目标不是给所有产品端点补 spec，而是让“最小稳定面”与测试一一对应。

### MedAutoScience

至少覆盖：

- adapter retirement boundary test
- runtime protocol topology tests
- transport tests
- study runtime router tests
- workspace contract / bootstrap / CLI / MCP 命名对齐测试

如果新增 layout config helper，则必须有独立单测，不允许只靠 controller 间接覆盖。

## Deliverables

本轮完成后，应该得到：

1. `med-deepscientist` 中一份显式的最小稳定 runtime protocol spec。
2. 与 spec 对齐的一组回归测试。
3. `med-autoscience` 中进一步退休的 `adapters/deepscientist/*`。
4. 一层更明确的 workspace runtime layout contract，减少散落的 `ops/med-deepscientist/...` 路径硬编码。
5. 更新后的技术文档，使 Agent 和维护者读取仓库时不再依赖隐式上下文理解这些边界。

## Acceptance Criteria

完成标准如下：

- `med-deepscientist` 的最小稳定 runtime 面可以由一份文档直接说明，而不是必须翻测试和代码才能知道
- `med-autoscience` 的生产路径不再依赖 `adapters/deepscientist/*`
- `ops/med-deepscientist/...` 路径知识不再以散落字符串的方式重复出现在多个关键模块
- 相关回归全部通过
- 文档中不再把 adapter 或旧命名写成正式主链的一部分

