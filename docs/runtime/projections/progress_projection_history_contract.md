# Progress Projection History Contract

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime projection and read-model semantics for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable projection support only; projection truth remains in source, tests, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这份 contract 学习 `DeepScientist` 的 quest history、lazy detail load 和 admin ops observability，但在 `MAS` 中落为 study-progress / runtime-watch 的轻量投影规则。

## 目标

长 study 的用户进度读取必须快、准、可接管。默认进度面不应为了展示完整历史而重读所有 runtime logs、terminal output、delivery package 或旧 artifact，也不得把 OPL provider attempt history 当作 MAS-owned runtime truth。

## Projection layers

### Summary layer

默认 `study-progress` 只读取：

- current study status
- active route
- current blocker
- next action
- latest controller decision
- latest publication eval
- top relevant artifact inventory items

### Detail layer

只有用户请求细节、debug、接管或审计时，才读取受控 detail refs：

- OPL `current_control_state` / provider attempt refs
- bounded runtime event tail refs
- bounded terminal/log tail refs
- historical artifact list
- old failed paths
- full delivery package manifest

这些 detail refs 属于 audit / handoff / diagnostic view。MAS projection 可以显示引用、freshness、截断信息和下一 owner；不能直接读取无界历史日志，也不能据此启动、恢复或裁决 provider worker。

### Admin ops layer

runtime-watch 和 operator view 可以读取更多状态，但必须把 heavy detail 与 user summary 分离；provider retry/dead-letter、worker liveness、terminal/log tail 和 long-running attempt truth 归 OPL `current_control_state`，MAS 只展示 domain blocker、owner receipt、typed blocker 与 refs。

## Freshness 规则

- summary layer 可以引用 cached projection，但必须带 freshness timestamp。
- stale projection 必须显示 stale reason 或 refresh action。
- heavy detail load 不得阻塞 current blocker 和 next action 的显示。
- 如果 history 与 current truth 冲突，current durable truth 优先。

## 与上游关系

上游 lazy-load quest detail 的 lesson 是：inspectability 不等于首屏加载所有细节。

`MAS` 吸收为 progress projection layering：前台先给可行动真相，细节按需展开。
