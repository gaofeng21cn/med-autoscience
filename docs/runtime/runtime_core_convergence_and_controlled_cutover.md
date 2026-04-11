# Runtime Core Convergence And Controlled Cutover

## 1. 当前事实

当前正式状态已经不是“runtime truth 还没做”，也不是“继续长期打磨旧 `Codex-default host-agent runtime`”。

截至当前 repo-side continuation，正确事实应按下面这条顺序理解：

- `P0 runtime native truth` 已在 controlled research backend 一侧完成并 absorbed
- `P1 workspace canonical literature / knowledge truth` 已完成并 absorbed
- `P2 controlled cutover -> physical monorepo migration` 仍未完成
- `P2` 当前 repo 内可继续推进的主线，已经切成：
  - `MedAutoScience gateway -> upstream Hermes-Agent target outer runtime substrate -> MedDeepScientist controlled research backend`
- 当前 repo-tracked 默认 owner 语义，是指向上游目标的 repo-side outer-runtime seam，而不是“仓内已落地独立 Hermes-Agent host”
- `MedDeepScientist` 不再是默认不可替代 runtime truth，而是 controlled research backend

这意味着：

- repo 内当前正确任务不是回头重做 `P0 / P1`
- 也不是把 external runtime gate 伪造成 repo 内已清除
- 而是把“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”的 contract、durable surface、deconstruction map 与 blocker wording 收紧到诚实闭环

## 2. 已关闭的风险

下面这些风险已经关闭：

1. quest runtime truth 主要由 MAS controller 代写
2. session-native `runtime_event_ref` 被 transport 静默丢弃
3. `study_runtime_status` / `study_runtime_execution` / `runtime_supervision` 覆盖 quest-owned `runtime_events/latest.json`
4. workspace literature 仍停留在 quest-local owner 语义
5. `med-deepscientist` 品牌名继续充当默认 outer substrate owner

## 3. 当前剩余风险

当前仍需解决的是 `P2` 风险，而且这些风险都必须按新拓扑理解。

### 3.1 Repo-side `Hermes` 闭环不等于 external `Hermes` truth

当前仓内已完成的是：

- repo-side `Hermes` adapter 作为 controller-facing outer-runtime seam 的 registry / transport / binding wiring
- `runtime_binding.yaml` 同时写出 substrate / research-backend metadata
- controller / outer-loop / transport 只认 backend-generic contract

当前仓内仍未完成的是：

- external `Hermes` runtime repo / workspace / daemon truth
- external `Hermes` runtime root / deployment contract

### 3.2 `MedDeepScientist` 仍未完全退场

虽然 authority truth 已经不再由 `MedDeepScientist` 隐式占有，但下面这些能力仍在 research backend 内：

- quest inner-loop / daemon turn worker / bash session execution
- quest-local logs / memory / config / paper worktree execution
- controlled fork / `behavior_equivalence_gate` 相关 external gate

因此当前不能伪造“已经完全切完”。

### 3.3 Physical monorepo migration 仍未开始

当前还没有进入真正的 physical absorb。
如果现在贸然迁移，风险不再是“吸收了错误 owner”，而是：

- 在没有明确模块边界和删除条件的前提下吸入过多双仓 glue
- 把尚未清除的 external runtime / workspace gate 与 physical migration 混写

### 3.4 文档、gate 与审计面必须持续诚实

最大的流程风险已经不是代码侧 silent fallback，而是：

- 把 `Hermes` 仍写成“只是非默认 backend onramp”
- 把 external blocker 写成已经解除
- 把 display / paper-facing asset packaging 独立线混入 runtime 主线
- 把 repo 内已完成的 tranche 再写成待办，或把未完成的 external truth 写成已完成

## 4. Controlled Cutover Gate

当前 cutover gate 应按下面顺序理解：

1. quest-owned native runtime writer 已存在并稳定
2. MAS 已切成 managed runtime truth 的消费者，而不是主 writer
3. workspace canonical knowledge / literature 已稳定
4. `Hermes` default outer substrate wiring 已在 repo 内完成最小闭环
5. `MedDeepScientist` deconstruction map 已冻结为 repo-tracked truth
6. cross-repo parity suite 与 external runtime / workspace gate 必须持续 green
7. physical monorepo absorb plan 必须写清模块边界、删除条件与回退条件
8. 只有 1-7 全部满足后，才进入 physical migration

前 1-5 项是当前 repo-side continuation 的职责。
第 6-8 项仍依赖 external runtime / workspace / human gate。

## 5. 非目标

当前 tranche 不做：

- 重新引入 controller-side synthetic runtime event 作为长期方案
- 用 hidden fallback、silent downgrade 或 synthetic truth rewrite 掩盖 owner 边界
- 在 external gate 未清除前提前宣称 runtime cutover 已放行
- 在 external gate 未清除前提前做 physical migration
- 把 display / paper-facing asset packaging 独立线混入 runtime 主线

## 6. 结论

当前正确任务不是：

- “继续完成 P0”
- “继续完成 P1”
- “继续把 `Hermes` 写成非默认 backend onramp”

当前正确任务是：

- 守住已经完成的 `P0 runtime native truth`
- 守住已经完成的 `P1 workspace canonical literature / knowledge truth`
- 完成“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”的最小闭环、durable-surface freeze 与 deconstruction map
- 把真正剩余 blocker 诚实收口到 external runtime / workspace / human gate
