# Runtime Boundary

这份文档定义 `MedAutoScience` 与 `DeepScientist` 在当前架构下的边界。

## 一句话版本

`MedAutoScience` 是唯一研究入口，`DeepScientist` 是被它调用的 runtime。

## 角色划分

- `MedAutoScience`
  - 负责 workspace / study 治理
  - 负责 startup boundary、数据准备度、overlay、研究路线和投稿约束
  - 负责决定 quest 何时可以创建、启动、恢复、暂停
- `DeepScientist`
  - 负责 quest runtime、执行调度、日志、记忆和底层 turn 循环
  - 不承担医学研究治理真相

## 允许的入口

正式研究流程只允许从这些入口进入：

- `med_autoscience.cli`
- `medautosci-mcp`
- workspace 下的 `ops/medautoscience/bin/*`
- 由这些入口进一步调用的 controller

## 不允许的入口

下列路径不应作为研究入口使用：

- 直接调用 `DeepScientist` daemon HTTP API
- 直接在 `DeepScientist` UI 中创建或启动 quest
- 直接用 `DeepScientist` CLI 发起研究流程
- 绕过 `MedAutoScience` controller 的自定义脚本

这些路径即使技术上可达，在架构上也视为旁路。

## `ops/deepscientist/` 的定位

workspace 下的 `ops/deepscientist/` 只保留：

- runtime state
- launcher config
- 运维脚本
- startup brief / startup payload 等 project-local runtime 附件

它不是面向研究用户或 Agent 的正式研究入口。

`ops/deepscientist/bin/start-web`、`status`、`doctor`、`stop` 只用于 runtime 运维，不用于研究启动决策。

## 为什么不需要修改 DeepScientist 源码

在当前架构里，只要 `MedAutoScience` 是唯一交互层，研究门禁就应该放在入口层，而不是 runtime 内核：

- startup boundary 是研究治理规则，不是 runtime 调度规则
- 期刊约束、证据包约束、study framing 约束都属于 `MedAutoScience`
- runtime 只需要执行被批准的动作

因此，不修改 `DeepScientist` 源码并不代表门禁变弱；前提是所有正式调用都经过 `MedAutoScience`。

## 工程约束

为保持这条边界成立，后续新增功能时应遵守：

- 不新增直接面向用户的 `DeepScientist` 研究入口说明
- 不新增绕过 `MedAutoScience` 的 quest 创建脚本
- Agent 入口模板、workspace 脚手架和公开文档都必须把 `MedAutoScience` 写成唯一研究入口
- 如果未来出现第二个上层系统直连 `DeepScientist`，再考虑把门禁下沉到 runtime 本体
