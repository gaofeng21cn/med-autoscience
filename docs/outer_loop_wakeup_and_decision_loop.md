# Outer-Loop Wakeup And Decision Loop

这份文档回答一个当前主线里必须明确的问题：

`MedAutoScience` 作为 `Domain Harness OS` 的 outer loop controller，不是常驻 runtime daemon。
那么当 `MedDeepScientist` 内环跑到“不能再把当前情况当作本地迭代继续处理”时，`MedAutoScience` 以什么形式被唤醒，并继续往下推进？

## 一句话结论

当前推荐机制不是：

- 让 `MedAutoScience` 常驻监听所有 runtime
- 也不是让 `MedDeepScientist` 直接越权决定 study-level 改向

而是：

**由 inner loop 写出 durable escalation artifact，由 outer loop 在显式 controller tick 中读取该 artifact、产出 study-level decision、再决定后续动作。**

换句话说：

- inner loop 常驻
- outer loop 被显式唤醒
- 二者通过 durable artifact + ref + controller tick 对接

## 为什么必须这样设计

如果没有独立的 outer-loop wakeup 设计，系统会退化成两种坏形态之一：

1. `MedDeepScientist` 自己判断整条研究线是否要改题、停题、换故事
2. `MedAutoScience` 理论上拥有 study-level authority，但实际上没有被正式唤醒的路径

第一种会让 runtime 越权。  
第二种会让 “outer loop controller” 只停留在概念层。

因此必须明确：

- runtime 在什么情况下发出升级信号
- outer loop 通过什么正式入口读到这个信号
- outer loop 做完判断后，结果以什么 durable artifact 写回

## 角色分工

### `MedDeepScientist`

负责：

- quest runtime lifecycle
- 长时间执行
- quest-local branch / iterate / diagnose
- within-envelope local autonomy
- 发现“这已经不是纯本地迭代问题”并发出 escalation

不负责：

- study-level reroute authority
- 改核心 claim family
- 改 endpoint / cohort contract
- 放宽 publication evidence standard
- 最终决定整条研究线 stop / continue / relaunch

### `MedAutoScience`

负责：

- `study_charter`
- study-level authority
- publication viability judgment
- outer-loop reroute / relaunch / stop-loss / delivery promotion
- 通过 controller tick 消费 escalation signal 并继续推进

不负责：

- 替代 runtime 成为 quest daemon
- 重写 runtime lifecycle 真相

## 当前正确的 wakeup 形态

当前最正确的设计是：

### 1. runtime 发出 durable signal

当 inner loop 需要升级回 outer loop 时，不直接修改 study-level truth，而是写出：

```text
quest_root/artifacts/reports/escalation/runtime_escalation_record.json
```

这个对象回答的是：

- 为什么当前 quest 不能再只做本地迭代
- 依据了哪些 evidence
- 建议 outer loop 考虑什么动作

它不是：

- `study_charter`
- `startup_contract`
- publication verdict

### 2. status surface 只暴露 ref

outer loop 不应把 full runtime event object 长期塞回 controller status 根层。

当前推荐 read-model 只暴露：

```yaml
runtime_escalation_ref:
  record_id: "..."
  artifact_path: "..."
  summary_ref: "..."
```

这让 outer loop 可以读到“升级已经发生”，但不会把 runtime truth 与 controller truth 混成一个大对象。

### 3. outer loop 在 controller tick 中被唤醒

`MedAutoScience` 当前不是常驻 runtime。  
它应通过显式 tick 被唤醒，例如：

- `study_runtime_status(...)`
- `ensure_study_runtime(...)`
- `runtime_watch`
- future MCP / automation 定期调度

也就是说，outer loop 的唤醒是：

- **tick-driven**

而不是：

- callback-driven daemon coupling

## 当前仓库里已经存在的 wakeup 入口

### `study_runtime_status(...)`

用途：

- 只读当前 managed study runtime 状态
- 在受控条件下读到 `runtime_escalation_ref`

它适合：

- outer loop 做 read-model intake
- Agent / supervisor 判定是否需要继续推进

### `ensure_study_runtime(...)`

用途：

- 读状态
- 跑 preflight
- 按 controller decision 执行 create / resume / pause / completion sync

它适合：

- outer loop 在已有 decision 后，继续把 runtime 推到下一个正确状态

### `runtime_watch`

用途：

- 对 quest root 或 runtime root 做周期性扫描
- 聚合 controller runners
- 为 future outer-loop supervisor 提供天然的 poll 点

它适合：

- 被定时器、automation 或上层 agent 周期调用
- 作为 outer-loop wakeup 的默认执行外壳

## 当前 still missing 的对象

现在已经基本具备：

- `study_charter`
- `runtime_escalation_record`
- `publication_eval`

但 outer loop 真正要“继续往下跑”，还缺一个正式对象：

## `study_decision_record`

推荐新增一个 study-level durable decision artifact，例如：

```text
studies/<study_id>/artifacts/controller_decisions/<timestamp>_<decision_id>.json
```

它回答的是：

- outer loop 这次看完 escalation / eval / charter 后，最终裁决是什么
- 为什么这么裁决
- 接下来允许系统执行什么动作

### 最小 shape 建议

```yaml
schema_version: 1
decision_id: "..."
study_id: "..."
quest_id: "..."
emitted_at: "..."

decision_type: "continue_same_line|relaunch_branch|reroute_study|stop_loss|promote_to_delivery"

charter_ref:
  charter_id: "..."
  artifact_path: "..."

runtime_escalation_ref:
  record_id: "..."
  artifact_path: "..."

publication_eval_ref:
  eval_id: "..."
  artifact_path: "..."

requires_human_confirmation: true|false
controller_actions:
  - action_type: "..."
    payload_ref: "..."

reason: "..."
```

## 推荐的完整 outer-loop decision loop

理想链路如下：

```text
1. study_charter defines outer-loop authority and autonomy envelope
2. startup_contract projects the approved subset to runtime
3. MedDeepScientist runs within the approved envelope
4. runtime writes runtime_escalation_record when local autonomy is no longer enough
5. MedAutoScience status/read-model exposes runtime_escalation_ref
6. outer-loop supervisor tick reads:
   - study_charter
   - runtime_escalation_ref
   - publication_eval
   - current delivery/readiness surfaces when needed
7. MedAutoScience writes study_decision_record
8. controller executes the allowed next action
9. system returns to runtime loop or moves to delivery / stop-loss / reroute
```

## 这条 loop 中每个对象回答什么问题

### `study_charter`

回答：

- 研究目标是什么
- 哪些局部自治是允许的
- 哪些情况必须升级

### `runtime_escalation_record`

回答：

- 为什么 inner loop 不能继续只做本地迭代

### `publication_eval`

回答：

- 这条线现在是否还具备 publication viability

### `study_decision_record`

回答：

- outer loop 最终决定怎么做

## 技术实现建议

## Phase A. 完成当前已有对象

先继续完成并吸收当前主线已在推进的对象：

- `study_charter`
- `runtime_escalation_record`
- `publication_eval`

没有这三者，outer-loop wakeup 设计只会重新退化成 prompt 讨论。

## Phase B. 新增 outer-loop supervisor controller

推荐新增一个正式 controller，例如：

- `study_outer_loop_tick(...)`

它的输入至少包括：

- `profile`
- `study_id` 或 `study_root`
- optional `force`
- optional `source`

它的责任是：

1. 读取 `study_runtime_status`
2. 判断是否存在 `runtime_escalation_ref`
3. 如存在，读取 full escalation artifact
4. 读取当前 `study_charter`
5. 读取当前 `publication_eval`
6. 写出 `study_decision_record`
7. 如 decision 允许，调用下一步 controller action

## Phase C. 把 wakeup 挂到稳定 poll surface

推荐的挂载方式不是引入第二个 daemon，而是：

- 让 `runtime_watch` 成为默认 poll shell
- 由 MCP automation / cron / external scheduler 周期调用
- 或由 agent 在关键节点显式调用

最稳妥的方式是：

- poll-based controller wakeup
- durable artifact handoff
- non-callback orchestration

## 为什么不推荐直接 callback 到 outer loop

不推荐把设计做成：

- runtime 内部直接回调 `MedAutoScience` controller
- outer loop 永久监听 runtime event bus

原因有三：

1. 会把 outer loop 与 runtime 耦死
2. 会削弱 durable artifact 的审计价值
3. 会让 controller authority 与 runtime truth 更容易混叠

当前系统更适合：

- runtime emit
- controller poll
- decision write-back

## 与 automation 的关系

future automation 不应直接替代 outer-loop authority。  
它更适合承担：

- 周期触发 `runtime_watch`
- 周期触发 `study_outer_loop_tick`
- 汇总需要人工审核的 study-level decisions

也就是说：

- automation 负责唤醒
- controller 负责裁决
- runtime 负责执行

## 最关键的边界

这套设计里最关键的边界是：

- `MedDeepScientist` 可以自主发现“本地已做不下去”
- 但不能自主宣布“整条研究线改题”
- `MedAutoScience` 不需要常驻 daemon
- 但必须拥有稳定的 wakeup tick 和 decision artifact

因此，正确问题不是：

- outer loop 是否常驻

而是：

- outer loop 是否有稳定、可审计、可重复触发的 wakeup-and-decision loop

## 当前推荐口径

今后统一按下面这条口径理解：

`MedDeepScientist` 是常驻 inner runtime；`MedAutoScience` 是 tick-driven outer controller。  
两者通过 `study_charter -> startup projection -> runtime_escalation_record -> publication_eval -> study_decision_record` 这条 durable artifact loop 对接，而不是通过隐式回调耦合成一个大运行体。
