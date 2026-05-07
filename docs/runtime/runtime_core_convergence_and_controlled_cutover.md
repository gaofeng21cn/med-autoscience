# Runtime Core Convergence And Controlled Cutover

## 1. 当前事实

当前正式状态已经不是“runtime truth 还没做”，也不是“继续长期打磨旧 `Codex-default host-agent runtime`”。

截至当前 repo-side continuation，正确事实应按下面这条顺序理解：

- `P0 runtime native truth` 已在 controlled research backend 一侧完成并 absorbed
- `P1 workspace canonical literature / knowledge truth` 已完成并 absorbed
- `P2 controlled cutover -> runtime core ingest / broader platform migration` 仍未完成
- `P2` 当前 repo 内可继续推进的主线，已经切成：
  - `MedAutoScience gateway -> upstream Hermes-Agent target outer runtime substrate -> MAS-owned runtime/artifact/quality surfaces + optional MDS oracle/intake/audit reference`
- 当前 repo-tracked 默认 owner 语义，是指向上游目标的 repo-side outer-runtime seam，而不是“仓内已落地独立 Hermes-Agent host”
- `MedDeepScientist` 不再是默认不可替代 runtime truth，也不再是 MAS 默认 operation 的必需 checkout；它只保留显式 backend audit、legacy diagnostic、parity oracle 与 upstream intake reference 语义。

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

### 3.2 `MedDeepScientist` 仍作为外部参考存在

虽然 authority truth 已经不再由 `MedDeepScientist` 隐式占有，默认 MAS study/status/progress/cockpit operation 也不需要外部 `med-deepscientist` checkout，但下面这些能力仍作为显式参考面保留：

- legacy restore/import diagnostic
- backend audit / upstream intake reference
- retained capability parity oracle fixture

因此当前不能伪造“外部参考仓必须删除”或“runtime core ingest 已完成”。

### 3.3 No-history absorb 已落地，runtime core ingest 仍需独立 gate

当前已经完成的是 MDS retained capability 的 no-history snapshot closeout：source provenance、author audit guard、capability parity harness、MAS-owned retained capability absorb 与 external runtime dependency retirement 已经落到 repo-level guard。

当前仍未完成的是更大的 runtime core ingest / controlled cutover。如果现在贸然继续平台级迁移，风险不再是“吸收了错误 owner”，而是：

- 在没有明确模块边界和删除条件的前提下吸入过多双仓 glue
- 把尚未清除的 external runtime / workspace gate 与 runtime core ingest 混写

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
7. MDS no-history absorb 的 source provenance、author guard、parity proof 与 default dependency retirement 已落地为 repo-level guard
8. 只有 1-7 全部满足后，才进入 runtime core ingest / broader controlled cutover

前 1-7 项是当前 repo-side continuation 已关闭或正在守住的职责。
第 8 项仍依赖 external runtime / workspace / human gate 与独立 owner/proof gate。

## 5. 非目标

当前 tranche 不做：

- 重新引入 controller-side synthetic runtime event 作为长期方案
- 用 hidden fallback、silent downgrade 或 synthetic truth rewrite 掩盖 owner 边界
- 在 external gate 未清除前提前宣称 runtime cutover 已放行
- 在 external gate 未清除前提前做 runtime core ingest / broader controlled cutover
- 把 display / paper-facing asset packaging 独立线混入 runtime 主线

## 6. 结论

当前正确任务不是：

- “继续完成 P0”
- “继续完成 P1”
- “继续把 `Hermes` 写成非默认 backend onramp”

当前正确任务是：

- 守住已经完成的 `P0 runtime native truth`
- 守住已经完成的 `P1 workspace canonical literature / knowledge truth`
- 守住已经完成的 MDS no-history absorb guard/parity/default-dependency-retirement
- 完成“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”的最小闭环、durable-surface freeze 与 deconstruction map
- 把真正剩余 blocker 诚实收口到 external runtime / workspace / human gate
