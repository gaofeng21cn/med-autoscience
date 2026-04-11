# Runtime Core Convergence And Controlled Cutover

## 1. 背景

当前 repo-side 已经完成：

- `runtime_event` durable surface
- `runtime_event_ref`
- `outer_loop_input`
- `runtime_watch` 扫描面收紧
- `runtime_summary_alignment` 扩展比对

这条链已经足以让 `MedAutoScience` 不再只靠 `poll + inference` 监管 managed runtime。

但它仍然不是 end-state。

当前最大的结构性事实是：

- `runtime_event` 仍然主要由 `MedAutoScience` controller 在 repo-side 物化；
- runtime event plane 还不是 `med-deepscientist` runtime core 的原生输出面。

所以当前正确结论不是“runtime 问题已经彻底解决”，而是：

- repo-side contract 已收紧；
- runtime core convergence 仍然是下一条必须完成的 tranche；
- monorepo 只能在这条 tranche 完成后做 controlled cutover。
- 当前诚实停车结论仍然是 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`。

## 2. 目标

这条主线要完成三件事：

1. 把 `runtime_event` 从 repo-side projection 收敛成 runtime-native truth。
2. 让 MAS 对 managed runtime 的正式输入固定为 event contract，而不是继续代写 runtime 事件。
3. 为 future monorepo 提供可以直接吸收的 runtime core 模块边界，而不是继续吸收 glue code。

## 3. 非目标

本 tranche 不做：

- 提前 physical merge 两个 repo；
- 把 `MedAutoScience` 改成常驻 runtime daemon；
- 用新的 watch shell 或补丁 controller 替代 runtime-native event；
- 把 `launch_report`、`runtime_watch` 或 `study_progress` 升格成 runtime truth；
- 用降级、兜底、静默双写长期维持不清晰 owner。

## 4. 当前 authority 边界

当前至少必须继续保持下面这组边界：

- `study_id`
  - study-owned aggregate root
- `quest_id`
  - managed runtime handle
- `active_run_id`
  - live daemon run handle
- `runtime_event`
  - quest-owned runtime event plane
- `runtime_supervision/latest.json`
  - study-owned health truth
- `controller_decisions/latest.json`
  - study-owned outer-loop decision truth

这里最关键的约束是：

- quest-owned runtime state 不能继续主要靠 study-side controller 代写才可见；
- study-owned decision / health surfaces 也不能反向吞并 runtime state plane。

## 5. 当前剩余漏洞

### 5.1 事件 owner 仍不够原生

现在的 `status_observed / transition_applied / supervision_changed` 虽然已经稳定，但主 writer 仍在 MAS repo。

后果是：

- 某些 runtime 状态迁移仍需要 MAS 看到之后才能正式落到 event plane；
- 一旦 outer supervisor tick 停摆，runtime 真实状态仍可能延迟暴露给 controller；
- event plane 的 owner 语义仍不够干净。

### 5.2 Outer loop 仍是 tick-driven consumer

这本身没有问题，但它要求：

- runtime event plane 必须已经是原生 durable truth；
- MAS 不能一边 tick，一边继续负责替 runtime 生成主要状态事件。

否则系统仍然停留在“controller observation loop”而不是“runtime self-report + controller consume”。

### 5.3 Monorepo 现在直接做会吸收错误层

如果现在就 physical migration，实际被吸进去的会是：

- repo-side runtime observation glue
- controller-side event synthesis logic

而不是：

- runtime-native event ownership
- runtime core 的正式模块边界

这会把当前过渡态固化进 monorepo。

而且当前仓内的 monorepo 仍主要体现为：

- `controller_charter / runtime / eval_hygiene`

这组三模块的 scaffold boundary，
还不是 runtime core ingest 已经完成后的真实承载态。

## 6. 目标 end-state

### 6.1 Native runtime event plane

`med-deepscientist` runtime core 必须原生写出：

- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_events/<timestamp>_<event_kind>.json`
- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_events/latest.json`

并保持 MAS-facing schema 与当前 contract 兼容：

- `event_id`
- `study_id`
- `quest_id`
- `event_kind`
- `status_snapshot`
- `outer_loop_input`
- `summary_ref`
- `artifact_path`

对 MAS 来说，正式 contract 不变；变化的是 writer 从 repo-side controller 迁到 runtime core。

换句话说，这一层必须成为：

- `runtime core 原生输出`

### 6.2 MAS 改为纯消费者

cutover 完成后，MAS 在 managed runtime 上的职责应收敛为：

- 读取 runtime event plane
- 读取 study-owned health / decision / eval surfaces
- 做 outer-loop judgment
- 执行受控 action

而不是继续承担：

- runtime state event 的主要生产者

### 6.3 Progress / launch / watch 保持 projection 身份

以下表面继续保留，但不升格：

- `launch_report`
- `runtime_watch`
- `study_progress`

它们可以读 event plane，但不能替代 event plane。

## 7. Controlled Cutover Gate

只有在下面条件全部满足后，才进入 physical monorepo cutover：

1. runtime core 已原生写出 `runtime_event`。
2. MAS 可以在不代写 runtime event 的前提下继续完成 managed supervision。
3. `paused / stopped / idle / created / waiting_for_user / parking / stale / degraded / live` 全部能经 transition matrix 覆盖。
4. `study_outer_loop_tick(...)` 继续只消费 `runtime_event_ref + outer_loop_input + publication_eval/latest.json`。
5. `launch_report` / `runtime_watch` / `study_progress` 仍保持 projection 身份，没有重新膨胀成 authority root。
6. external runtime gate 已经通过，不再处于“repo-side absorb 完成但 external dependency blocked”的状态。

## 8. 推荐阶段

### P0: Cutover 前置合同冻结

- 冻结 runtime-native event owner contract。
- 冻结 MAS cutover 后的 consumer-only contract。
- 冻结 transition matrix 与 parity gate。

### P1: Runtime Core 吸收

- 在 runtime repo 原生实现 event writer。
- 让 MAS 改为读 native event，而不是继续主写 event。
- 保持现有 MAS-facing schema 不变，避免同时改 writer 与 consumer contract。

### P2: Physical Monorepo Cutover

- 在 `controller_charter / runtime / eval_hygiene` 三模块边界明确后做物理吸收。
- 删除过渡期 glue，避免把 repo-side observation shell 固化到 monorepo 内部。

## 9. 结论

当前 runtime tranche 的正确任务不是“继续补 controller”，而是：

- 把 repo-side event contract 变成 runtime-native truth；
- 把 MAS 变成诚实的 outer-loop consumer；
- 在此基础上再做 controlled monorepo cutover。

换句话说：

- `runtime event contract` 已经写对了；
- 下一步要修的是 owner，不是再修一层 summary。
