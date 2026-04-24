# Runtime Boundary

这份文档定义 `MedAutoScience`、`Hermes` 与 `MedDeepScientist` 在当前架构下的边界。

## 一句话版本

`MedAutoScience` 是唯一研究入口与 research gateway，外层由单一 MAS app skill 承接稳定 callable surface；`Hermes` 是默认 outer runtime substrate owner，`MedDeepScientist`（仓库名 `med-deepscientist`）是 controlled research backend；`DeepScientist` 只在指代其上游来源或兼容语义时单独出现。

display / paper-facing asset packaging 独立线明确排除在这条 runtime 主线之外。

## 角色划分

- `MedAutoScience`
  - 负责 workspace / study 治理
  - 负责 startup boundary、数据准备度、overlay、研究路线和投稿约束
  - 负责决定 quest 何时可以创建、启动、恢复、暂停
  - 通过单一 MAS app skill 对外承接 CLI、workspace commands / scripts、durable surfaces 与 repo-tracked contracts
- `Hermes`
  - 负责 controller-facing outer runtime substrate
  - 负责 backend registry、backend selection、runtime binding 与 substrate-level durable metadata
  - 负责把 controller / outer-loop / transport 收口到 backend-generic contract
- `MedDeepScientist`
  - 负责 quest inner-loop、执行调度、daemon turn worker、bash session execution
  - 负责当前 research backend 仍需承担的 quest-local logs / memory / config / paper worktree execution
  - 不承担医学研究治理真相，也不再是默认不可替代 runtime truth

## 允许的入口

正式研究流程只允许从这些入口进入：

- `med_autoscience.cli`
- `medautosci-mcp`
- workspace 下的 `ops/medautoscience/bin/*`
- 由这些入口进一步调用的 controller

`OPL` handoff、product-entry manifest 和其他机器可读桥接属于集成或参考层，不是正式研究入口。

## 不允许的入口

下列路径不应作为研究入口使用：

- 直接调用 external `Hermes` daemon / repo / workspace surface
- 直接调用 `MedDeepScientist` daemon HTTP API
- 直接在 `MedDeepScientist` UI 中创建或启动 quest
- 直接用 `MedDeepScientist` CLI 发起研究流程
- 绕过 `MedAutoScience` controller 的自定义脚本

这些路径即使技术上可达，在架构上也视为旁路。

关于 “runtime 发出升级信号后，outer loop 如何被唤醒并继续推进” 的正式设计，见：

- [Outer-Loop Wakeup And Decision Loop](./outer_loop_wakeup_and_decision_loop.md)

## `ops/med-deepscientist/` 的定位

workspace 下的 `ops/med-deepscientist/` 当前只保留：

- controlled research backend 的 runtime state
- launcher config
- 运维脚本
- startup brief / startup payload 等 project-local runtime 附件

它不是面向研究用户或 Agent 的正式研究入口。

`ops/med-deepscientist/bin/start-web`、`status`、`doctor`、`stop` 只用于 runtime 运维，不用于研究启动决策。
`ops/med-deepscientist/` 相关路径的程序化派生应统一走 `med_autoscience.runtime_protocol.layout`，而不是在 controller、workspace scaffold 或 wrapper 中重复硬编码。

当前 repo 内还没有 external `Hermes` runtime workspace truth，因此不得在本仓文档里伪造新的 `ops/hermes/...` 正式布局。

## 为什么不需要把研究门禁下沉到 backend 内核

在当前架构里，只要 `MedAutoScience` 是唯一交互层，研究门禁就应该放在入口层，而不是 backend 内核：

- startup boundary 是研究治理规则，不是 runtime 调度规则
- 期刊约束、证据包约束、study framing 约束都属于 `MedAutoScience`
- `Hermes` 负责 substrate-level contract，不负责 study governance
- `MedDeepScientist` 只需要执行被批准的动作

因此，不把研究治理规则继续堆到 `MedDeepScientist` runtime 内核里，并不代表门禁变弱；前提是所有正式调用都经过 `MedAutoScience`。
如果讨论的是受控 fork 与其上游差异，再单独使用 `DeepScientist upstream` 这一说法。

## 工程约束

为保持这条边界成立，后续新增功能时应遵守：

- 不新增直接面向用户的 `MedDeepScientist` 或 external `Hermes` 研究入口说明
- 不新增绕过 `MedAutoScience` 的 quest 创建脚本
- Agent 入口模板、workspace 脚手架和公开文档都必须把 `MedAutoScience` 写成唯一研究入口
- 不重新引入 `adapters/deepscientist/*` 这类 legacy shim 作为 production 依赖
- 不在 controller 中重复拼接 `ops/med-deepscientist/...`；统一走 `runtime_protocol.layout`
- external runtime gate 未清除前，不得把 external `Hermes` repo / daemon / workspace truth 写成本仓既成事实
