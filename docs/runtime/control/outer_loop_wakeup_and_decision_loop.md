# Outer-Loop Wakeup And Decision Loop

Owner: `MedAutoScience`
Purpose: `domain_transition_and_outer_loop_wakeup_contract`
State: `active_runtime_control_support`
Machine boundary: 本文是 MAS 医学研究 domain controller 的人读解释。机器真相继续归 MAS contracts、schema、CLI/MCP/API payload、`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`、sidecar receipt 和真实 workspace artifact；通用 provider workflow、queue、attempt ledger、retry/dead-letter、memory/artifact locator、operator projection 与 App/workbench shell 归 OPL Framework / shared family layer。

当前阅读规则：本文不再描述 `Domain Harness OS` 时代的通用 runtime 计划，也不把 MAS 写成 generic runtime platform。这里的 `outer loop` 只指 MAS 如何把医学研究状态、publication quality、runtime-facing blocker 和 owner receipt 收成 domain transition / controller decision。OPL 可以托管 tick、queue、provider、attempt 与投影，但不能解释或改写 MAS 的医学研究 truth、publication verdict、paper/package authority 或 artifact gate。

这份文档回答一个当前主线里必须明确的问题：

`MedAutoScience` 作为 MAS-owned study/runtime-facing controller，不是常驻 monolithic runtime daemon，也不是 OPL 的 generic runtime kernel。
当 MAS domain execution / runtime-facing owner surface 发现“当前状态不能再只作为本地研究迭代继续处理”时，`MedAutoScience` 以什么形式被唤醒、读取哪些 durable refs，并继续往下推进？

与 `stop / rerun / requires_human_confirmation` 相关的正式控制语义，现统一收口到：

- [`./study_runtime_control_surface.md`](./study_runtime_control_surface.md)

与 `publication_eval`、`study_decision_record` 下游如何连接到 delivery/publication plane 的 artifact 边界，现统一桥接到：

- [`../contracts/delivery_plane_contract_map.md`](../contracts/delivery_plane_contract_map.md)

## 一句话结论

当前机制不是：

- 让 `MedAutoScience` 常驻监听所有 runtime
- 让 MAS 自建通用 scheduler / queue / state-machine platform
- 让 provider、local scheduler 或 runtime-facing helper 直接越权决定 study-level 改向

而是：

**由 MAS runtime-facing surface 写出 durable escalation / blocker / owner refs，由 MAS outer loop 在显式 controller tick 中读取这些 refs、按 domain transition table 产出 study-level decision、再把可执行动作交给当前 owner surface 或 OPL-hosted provider。**

换句话说：

- provider / scheduler / local diagnostic shell 可以触发 tick
- MAS outer loop 的裁决必须显式、可审计、可重放
- OPL 与 MAS 通过 durable artifact + ref + owner receipt + controller tick 对接

## 为什么必须这样设计

如果没有独立的 outer-loop wakeup 设计，系统会退化成两种坏形态之一：

1. provider / runtime-facing helper 自己判断整条研究线是否要改题、停题、换故事
2. `MedAutoScience` 理论上拥有 study-level authority，但实际上没有被正式唤醒的路径

第一种会让 runtime 越权。
第二种会让 “outer loop controller” 只停留在概念层。

因此必须明确：

- runtime-facing surface 在什么情况下发出升级信号
- outer loop 通过什么正式入口读到这个信号
- outer loop 做完判断后，结果以什么 durable artifact 写回

## 角色分工

### MAS runtime-facing execution surface

负责：

- 执行 MAS 已授权的研究 work unit、repair work unit 或 delivery sync
- 暴露 runtime liveness、owner route、typed blocker、artifact locator、receipt ref 和 escalation ref
- 在 MAS 授权范围内做 quest-local diagnose / repair / iterate
- 发现“这已经不是纯本地迭代问题”并发出 escalation 或 typed blocker

不负责：

- study-level reroute authority
- 改核心 claim family
- 改 endpoint / cohort contract
- 放宽 publication evidence standard
- 最终决定整条研究线 stop / continue / relaunch
- generic scheduler、generic queue、attempt ledger、retry/dead-letter、operator projection 或 App/workbench runtime

### `MedAutoScience`

负责：

- `study_charter`
- study-level authority
- publication viability judgment
- outer-loop reroute / relaunch / stop-loss / delivery promotion
- 通过 controller tick 消费 escalation signal 并继续推进

不负责：

- 替代 runtime 成为 resident quest daemon
- 维护 generic runtime platform
- 重写 provider / OPL attempt lifecycle 真相

## 当前正确的 wakeup 形态

当前最正确的设计是：

### 1. runtime-facing surface 发出 durable signal

当 MAS runtime-facing surface 需要升级回 outer loop 时，不直接修改 study-level truth，而是写出：

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
- OPL-hosted provider / MCP / automation 定期调度

也就是说，outer loop 的唤醒是：

- **tick-driven**

而不是：

- callback-driven daemon coupling

## 当前仓库里已经存在的 wakeup 入口

### `study_runtime_status(...)`

用途：

- 只读当前 MAS study runtime-facing 状态
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

- 对 quest root 或 runtime-facing roots 做周期性扫描
- 聚合 MAS controller / owner-route / receipt refs
- 为 OPL-hosted provider、automation 或 direct/local diagnostic shell 提供 poll 点

它适合：

- 被 OPL provider、定时器、automation 或上层 agent 周期调用
- 作为 MAS outer-loop wakeup 的 domain read / receipt shell

## 当前 P0 已落地的对象

当前主线已经具备这条 durable loop 的 4 个正式对象：

- `study_charter`
- `runtime_escalation_record`
- `publication_eval`
- `study_decision_record`

## Domain Transition Table

outer loop 的状态转换应按集中 domain transition table 理解，而不是由多个局部 helper 隐式拼出下一步。当前实现仍分散在 `publication_work_units`、`study_outer_loop`、`owner_priority`、`controller_authorization` 等模块；这是实现形态，不是目标 contract。目标 contract 是：MAS 在一个可审计的 transition matrix 中声明“输入状态组合 -> domain route/work-unit/controller action”，再由 controller tick materialize `study_decision_record`。

MAS domain transition table 的输入至少包括：

- `publication_supervisor_state`
- publication gate report
- `publication_eval/latest.json`
- task intake / reviewer revision intake
- latest `controller_decisions/latest.json` authorization
- runtime liveness / retry / owner guard

MAS domain transition table 的输出至少包括：

- `decision_type`
- `route_target`
- `next_work_unit`
- `controller_action`
- owner / callable surface
- work-unit fingerprint / source fingerprint / idempotency key
- fail-closed blocker 或 human gate reason

必须显式区分三类容易混淆的状态：

- `bundle_stage_ready` / `continue_bundle_stage`：可以进入 finalize-level submission authority / delivery sync。
- `bundle_stage_blocked` / `complete_bundle_stage`：只允许执行 controller-owned bundle-stage closure，例如 submission authority sync 或 delivery sync；不能回到 generic review loop。
- `publishability_gate_blocked` / `bundle_tasks_downstream_only=true`：还不能进入 package/finalize；当前 next action 应留在 claim/evidence/display/story/AI reviewer 等 publication-quality repair owner。

每次修改 transition 规则，都必须同步更新 table-driven transition matrix tests。测试对象不是单个 helper 的返回值，而是完整的 `status_payload + gate_report + publication_eval + task_intake -> decision_type + route_target + next_work_unit + controller_action`。

长期边界是：OPL 可以提供通用 state-machine runner、transition schema、幂等 tick、attempt/retry/dead-letter、human gate transport、dispatch receipt 和 transition matrix runner；MAS 继续持有 domain transition table、医学状态语义、publication quality verdict、paper/package authority 和 oracle fixtures。OPL 只能执行 MAS 声明的 transition spec，不能自行解释 `publication_gate`、`stale_submission_minimal_authority`、AI reviewer judgement 或 claim/evidence/display blocker。

## `study_decision_record`

当前实现的 study-level durable decision artifact 形态为：

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
3. MAS Runtime OS runs within the approved envelope
4. MAS runtime-facing surface writes runtime_escalation_record when local autonomy is no longer enough
5. MedAutoScience status/read-model exposes runtime_escalation_ref
6. outer-loop supervisor tick reads:
   - study_charter
   - runtime_escalation_ref
   - publication_eval
   - current delivery/readiness surfaces when needed
7. MedAutoScience writes study_decision_record
8. controller dispatches the allowed next action through MAS owner surface or OPL-hosted provider
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

- 为什么 runtime/backend loop 不能继续只做本地迭代

### `publication_eval`

回答：

- 这条线现在是否还具备 publication viability

### `study_decision_record`

回答：

- outer loop 最终决定怎么做

## 当前实现与后续收口

## Phase A. 维护当前已有对象

当前对象继续作为 MAS-owned decision loop 的 durable anchors：

- `study_charter`
- `runtime_escalation_record`
- `publication_eval`

没有这三者，outer-loop wakeup 会重新退化成 prompt 讨论或 provider 自行解释 domain state。

## Phase B. 新增 outer-loop supervisor controller

当前实现中的正式 controller tick 为：

- `study_outer_loop_tick(...)`

当前 P0 下它的显式输入包括：

- `profile`
- `study_id` 或 `study_root`
- `charter_ref`
- `publication_eval_ref`
- `decision_type`
- `requires_human_confirmation`
- `controller_actions`
- `reason`
- optional `source`
- optional `recorded_at`

当前实现中它的责任是：

1. 读取 `study_runtime_status`
2. 判断是否存在 `runtime_escalation_ref`
3. 如存在，读取 full escalation artifact
4. 读取当前 `study_charter`
5. 读取当前 `publication_eval`
6. 写出 `study_decision_record`
7. 若 `requires_human_confirmation=false`，才执行 `controller_actions[0]` 指定的下一个 controller action
8. 若 `requires_human_confirmation=true`，只写 artifact，不 dispatch side effect

当前 P0 明确保持：

- `study_outer_loop_tick(...)` 只接受显式 `charter_ref` / `publication_eval_ref`
- runtime escalation 必须从 `study_runtime_status(...).runtime_escalation_ref` 读到，并回读 full artifact 校验
- 缺 ref、stable path 不匹配、或 escalation artifact 与 status ref 不一致时，直接 fail-closed

## Phase C. 把 wakeup 挂到稳定 poll surface

推荐的挂载方式不是引入第二个 daemon，也不是让 MAS 维护 generic queue，而是：

- 让 `runtime_watch` 成为 MAS domain poll / receipt shell
- 由 OPL provider、MCP automation、cron 或 external scheduler 周期调用
- 或由 agent 在关键节点显式调用

最稳妥的方式是：

- poll-based / provider-triggered controller wakeup
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

future automation 或 OPL provider 不应直接替代 MAS outer-loop authority。
它更适合承担：

- 周期触发 `runtime_watch`
- 周期触发 `study_outer_loop_tick`
- 汇总需要人工审核的 study-level decisions
- queue、retry、dead-letter、attempt receipt 和 operator projection

也就是说：

- OPL / automation / scheduler 负责唤醒和承载 attempt
- MAS controller 负责 domain 裁决
- MAS owner surface 负责医学研究 truth、quality verdict、artifact/package authority 和 receipt

## 最关键的边界

这套设计里最关键的边界是：

- MAS runtime-facing surface 可以发现当前研究执行不可继续推进
- 但不能自主宣布“整条研究线改题”
- `MedAutoScience` 不需要常驻 daemon
- 但必须拥有稳定的 wakeup tick 和 decision artifact
- OPL 可以托管 wakeup / queue / provider / attempt / projection
- 但不能替代 MAS 解释 publication gate、AI reviewer judgement、claim/evidence/display blocker 或 paper/package readiness

因此，正确问题不是：

- outer loop 是否常驻

而是：

- outer loop 是否有稳定、可审计、可重复触发的 wakeup-and-decision loop

## 当前推荐口径

今后统一按下面这条口径理解：

`MedAutoScience` 是医学研究 domain controller；MAS runtime-facing owner surfaces 只执行 MAS 授权的 work unit、写出 blocker / escalation / receipt refs；OPL Framework 可以承载 provider-backed tick、queue、attempt、retry/dead-letter、operator projection 和 App/workbench shell；`Hermes gateway cron`、local scheduler 与旧 MDS daemon 只作为显式 optional adapter、direct/local diagnostic 或 historical fixture / explicit archive import reference 读取。
MAS 与 OPL 通过 `study_charter -> startup projection -> runtime_escalation_record -> publication_eval -> study_decision_record -> owner receipt` 这条 durable artifact loop 对接，而不是通过隐式回调耦合成一个常驻大运行体。后续发现旧 module、interface、CLI alias、wrapper 或测试入口已无 active caller 且已有 replacement proof 时，直接退役清理或归档到 history/tombstone，不保留兼容面。
