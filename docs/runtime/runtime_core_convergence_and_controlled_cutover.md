# Runtime Core Convergence And Controlled Cutover

## 1. 当前事实

当前正式状态已经不是“runtime truth 还没做”，而是：

- `P0 runtime native truth` 已在 `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a` 完成
- `MedAutoScience` 已完成 consumer-side cutover：managed runtime 不再主写 quest-owned `runtime_events/*`
- `P1 workspace canonical literature / knowledge truth` 已完成
- 当前剩余 active tranche 只剩 `P2 controlled cutover -> physical monorepo migration`

因此，runtime tranche 的问题已经从“谁负责写 truth”切换成“如何带着正确 owner 进入受控 cutover”。

## 2. 已关闭的风险

下面这些风险已经关闭：

1. quest runtime truth 主要由 MAS controller 代写
2. session-native `runtime_event_ref` 被 transport 静默丢弃
3. `study_runtime_status` / `study_runtime_execution` / `runtime_supervision` 覆盖 quest-owned `runtime_events/latest.json`
4. workspace literature 仍停留在 quest-local owner 语义

## 3. 当前剩余风险

当前仍需解决的是 `P2` 风险，而不是重新打开 `P0` / `P1`：

### 3.1 Cross-repo parity gate 仍未完全关闭

虽然 owner 已经收口，但 physical cutover 之前仍要持续验证：

- session-native `runtime_event_ref` / `runtime_event`
- MAS transport/status/outer-loop 消费链路
- workspace canonical literature / reference-context / quest materialization-only

这些 contract 在跨 repo 回归下必须继续完全对齐。

### 3.2 Physical monorepo migration 仍未开始

当前还没有进入真正的 physical absorb。  
如果现在贸然迁移，风险不再是“吸收了错误 owner”，而是：

- 在没有明确模块边界和删除条件的前提下吸入过多双仓 glue
- 把尚未完成的 parity gate 与 cutover runbook 一起硬塞进 monorepo

### 3.3 文档与 gate 必须持续诚实

最大的流程风险已经不是代码侧 silent fallback，而是：

- 把已完成的 tranche 再写成待办
- 把未完成的 tranche 再写成已完成
- 用同一个 `P0 / P1 / P2` 编号混写全局顺序和局部实现阶段

### 3.4 Hermes backend onramp 仍需 repo-side 冻结

虽然 `runtime backend interface` contract 已经冻结，但 `Hermes` 当前还不能只靠一句“未来可接入”来表述。

在 external gate 未清除前，repo-side 仍然可以、也仍然应该继续完成：

- `Hermes` backend continuation board
- `Hermes` backend activation package
- backend registry / transport / durable-surface 对 `Hermes` 的 fail-closed 收口

但这条 onramp 仍然不能被写成：

- default backend 已切换
- runtime cutover 已放行
- physical migration 已开始

## 4. Controlled Cutover Gate

当前 cutover gate 应按下面顺序理解：

1. quest-owned native runtime writer 已存在并稳定
2. MAS 已切成 managed runtime truth 的消费者，而不是主 writer
3. workspace canonical knowledge / literature 已稳定
4. cross-repo parity suite 必须持续 green
5. `Hermes` backend onramp 必须在 repo-side 完成 truth / adapter / durable-surface freeze
6. physical monorepo absorb plan 必须写清模块边界、删除条件与回退条件
7. 只有 1-6 全部满足后，才进入 physical migration

前 1-3 项已经满足。当前 active work 在 4-6。

## 5. 非目标

当前 tranche 不做：

- 重新引入 controller-side synthetic runtime event 作为长期方案
- 用双写或旁路修补掩盖 owner 边界
- 在 parity gate 未关之前提前做 physical migration
- 把 workspace knowledge plane 再退回 quest-local cache

## 6. 结论

当前正确任务不是：

- “继续完成 P0”
- “继续完成 P1”

当前正确任务是：

- 守住已经完成的 `P0 runtime native truth`
- 守住已经完成的 `P1 workspace canonical literature / knowledge truth`
- 把全部剩余精力集中到 `P2 controlled cutover -> physical monorepo migration`
