# Study Runtime Control Surface

这份文档是当前 `study runtime / outer-loop / decision artifact / transport` 之间的 **canonical bridge**。

它与下列文档配套使用：

- `./outer_loop_wakeup_and_decision_loop.md`
- `./study_runtime_orchestration.md`

本文把两份文档之间最容易漂移的控制语义收口成一个明确入口，让 `stop / rerun / human-confirmation` 固定进入 repo-tracked contract 与 durable decision artifact。

## 1. 作用域

当前 control surface 只覆盖四个正式对象：

1. `study_runtime_status(...)`
2. `ensure_study_runtime(...)`
3. `study_outer_loop_tick(...)`
4. `study_decision_record`

其目标是回答：

- outer loop 什么时候可以继续 dispatch
- `pause` 与 `stop` 的边界是什么
- `stop-after-current-step` 是否正式支持
- `rerun` 当前是否正式支持
- 哪些边界触发 `requires_human_confirmation` dispatch gate

## 2. surface 分层

### 2.1 `study_runtime_status(...)`

- 只读状态机入口
- 负责决定：
  - 当前是否属于 managed runtime
  - 当前 quest 是否可创建 / 可恢复 / 需要 pause / 已完成 / 被 gate 阻塞
- 不直接消费 `study_decision_record` 做 side effect

### 2.2 `ensure_study_runtime(...)`

- controller-owned 执行入口
- 负责把 `study_runtime_status(...)` 给出的运行时决策推进到 transport
- 只处理 runtime orchestration 内部决策：
  - `CREATE_AND_START`
  - `CREATE_ONLY`
  - `RESUME`
  - `PAUSE`
  - `SYNC_COMPLETION`
  - `PAUSE_AND_COMPLETE`

### 2.3 `study_outer_loop_tick(...)`

- outer-loop controller tick
- 负责：
  - 读取 `runtime_escalation_ref`
  - 读取 `publication_eval_ref`
  - durable 写出 `study_decision_record`
  - 根据 formal contract 决定是否允许继续 dispatch

### 2.4 `study_decision_record`

- controller-owned durable decision artifact
- 与 `study_charter`、`runtime_escalation_record`、`publication_eval` 分层维护
- 只表达：
  - 这次 outer-loop 的裁决
  - 它依赖的 refs
  - 它允许的下一步 controller action
  - 它是否必须先经过 human confirmation

## 3. formal stop semantics

### 3.1 `pause_runtime`

语义：

- 立即通过 daemon `pause` 收回 compute
- quest 保持当前 identity
- 这是 **recoverable runtime state**

后果：

- `quest_status=paused`
- 在 startup / reentry gates 允许且 controller policy 允许时，`ensure_study_runtime(...)` 可以再次把它推进到 `resume`

### 3.2 `stop_runtime`

语义：

- 立即通过 daemon `stop` 终止当前 quest 的运行
- quest 的 audit identity 仍保留（`study_id` / `quest_id` 不变）
- 这是 **terminal control action**；`pause` 继续表示可恢复运行态

后果：

- `quest_status=stopped`
- `study_runtime_status(...)` 不再把 `stopped` 当作可自动恢复状态
- 当前 P1 contract 下，stopped quest 的下一步固定为显式 relaunch policy

### 3.3 `stop-after-current-step`

当前结论：

- **未正式支持**
- 当前 stable transport contract 没有对应 daemon control action
- controller 对 caller 请求必须 fail-closed；以下形态均归入 unsupported：
  - `pause`
  - `stop`
  - 延迟执行的本地旁路
  - 任何启发式轮询补救

因此：

- 若 caller 请求 `stop-after-current-step`，必须直接 fail-closed

## 4. rerun policy

当前正式结论：

- `stopped quest` 进入显式 relaunch policy
- 但已经正式支持 **显式 stopped-quest relaunch**
- 该 relaunch 只允许通过 controller-owned 显式动作触发，并在 controller 记录中标注为 stopped relaunch

### 4.1 当前允许的 re-entry

当前唯一允许的 re-entry 是：

- 对 **同一个 existing quest identity** 执行正常的 managed runtime orchestration
- 典型形态是：
  - quest 已 `paused`
  - gates clear
  - `ensure_study_runtime(...)` 给出 `RESUME`

这类路径命名为 **resume / re-entry**。

### 4.2 stopped quest 的结论

一旦 quest 进入 `stopped`：

- 当前 control surface 只保留其审计 identity
- 不提供自动恢复
- `study_runtime_status(...)` 继续返回
  - `decision=blocked`
  - `reason=quest_stopped_requires_explicit_rerun`
- `ensure_study_runtime(...)` 只有在 caller 显式传入 stopped relaunch 许可时，才允许把它推进到正式 relaunch 动作

换句话说：

- `stopped` 会把系统带到 “需要显式 relaunch policy” 的阻塞态

### 4.3 stopped quest 的正式 relaunch

当前正式支持的 stopped-quest relaunch 只有一条：

- outer-loop action:
  - `ensure_study_runtime_relaunch_stopped`
- direct controller entry:
  - `ensure_study_runtime(..., allow_stopped_relaunch=True)`

约束：

- `study_runtime_status(...)` 不因为 caller 有 relaunch 意图而改变其只读真相
- 显式 relaunch 仍需通过 startup boundary 与 runtime reentry gate
- transport 层当前仍复用 daemon 的 `resume` control action
- controller / launch report / runtime binding 必须把该动作记为 `relaunch_stopped`

### 4.4 明确拒绝的 rerun 形态

当前必须显式拒绝：

- 任何未显式授权的 `rerun_*` controller action
- 任何试图让 `ensure_study_runtime(...)` 自动恢复 `stopped` quest 的行为
- 任何“保留旧交付 identity，但重新开跑”的隐式重放
- 任何需要 real-study relaunch / end-to-end study harness / cross-repo write 的 rerun

## 5. `requires_human_confirmation` 的正式地位

当前 P1 正式结论：

- `requires_human_confirmation` 是 **boundary-scoped dispatch gate**

方向锁定之后，普通科研推进、论文质量判断、证据充分性判断、reviewer concern 排序和下一步研究动作默认由 `MAS` 自主裁决。`requires_human_confirmation` 只在少数人类 gate 边界触发。

正式 gate 边界固定为：

1. 初始研究方向锁定
2. 重大研究转向
3. 止损、终止或搁置研究
4. 外部凭据、账户、秘密、授权或付费资源
5. 作者、伦理、基金、利益冲突、数据可用性、声明等客观投稿信息
6. 最终投稿前审计

普通质量推进由 controller 写入 decision artifact，并继续 dispatch 下一步动作；触达上述边界时，controller 写入同一类 decision artifact，同时打开人类 gate。

规则：

1. `study_outer_loop_tick(...)` 必须先写出 `study_decision_record`
2. 若 `requires_human_confirmation=true`
   - 允许写 artifact
   - 暂停 dispatch controller action
   - 必须返回结构化 `human_confirmation_request`
   - 必须同步写出 `studies/<study_id>/artifacts/controller/controller_confirmation_summary.json`
3. 只有在 human gate 清除后，后续 controller 才能执行下一步动作

这个 companion surface 的职责固定为：

- 用稳定、typed 的方式表达当前待人工确认的边界 gate
- 提供 `question_for_user`、`allowed_responses`、`next_action_if_approved`
- 供 `study_progress` 与 runtime 决策面读取

## 6. takeover / mailbox semantics

本节把从 `DeepScientist` 上游学习到的 mailbox / takeover 思路翻译成 `MAS` 的正式 runtime control contract。

### 6.1 running study 收到新用户消息

当 quest 已经处于 running / active 状态时，新的用户消息不启动第二个 runner，也不绕过 controller 直接改写 study / paper durable truth。

正式语义：

- 新用户消息必须优先于 retry / backoff 计时；runtime 可以 preempt retry/backoff 进入下一次可审计 interaction point。
- preempt 只改变调度优先级，不改变 study authority，也不允许 provider / UI bypass。
- 消息进入 quest-local `user_message_queue`。
- runtime state 必须暴露 `pending_user_message_count`。
- interaction journal 必须留下 `user_inbound` 事件。
- 下一次 agent / controller interaction point 才能消费该消息。
- 若消息表达的是人类 gate 所需的客观信息，controller 在 gate 清除后继续 dispatch。
- 若消息表达的是重大方向变化、终止、暂停或投稿前最终审计，controller 写出 `study_decision_record` 并进入 human confirmation gate。

这保证用户输入不会丢失，同时避免同一 study 出现两个并行 authority writer。

### 6.2 pause / resume / stop 与消息队列

`pause_runtime`、`resume` 和 `stop_runtime` 对 queued user messages 的处理必须保持单义：

- `pause_runtime` 收回 compute，但保留 queued user messages、quest identity、artifact 和 branch。
- `resume` 在 startup / reentry gate 清除后继续同一 quest identity，并允许后续 interaction point 消费 queued user messages。
- `stop_runtime` 是 terminal control action，必须取消自动 dispatch；queued user messages 不得被静默 replay 成新的研究动作。
- stopped quest 的后续动作只能走显式 stopped-quest relaunch policy，并在 controller 记录中标注为 relaunch。

### 6.3 takeover boundary

人工接管不是本地文件旁路写入。正式接管必须满足：

1. 先通过 `pause_runtime` 或 human gate 收回运行时写权。
2. 人工修改只写入对应的 controller-owned artifact、study docs、paper surface 或明确的 workspace 文件。
3. 接管完成后，通过 `study_decision_record` 或 runtime-facing startup projection 表达新的恢复点。
4. `ensure_study_runtime(...)` 只能从该恢复点继续，不得根据旧队列或旧 launch summary 隐式重放。

### 6.4 durable surface 分工

- `artifact` / reports：记录 stage result、route truth、checkpoint、handoff 和恢复点。
- `memory` / portfolio lesson：只记录会改变未来默认行为的 reusable lesson。
- `bash_exec` / terminal evidence：记录第一手执行证据，不承担研究结论 authority。
- `study_charter`、`evidence_ledger`、`review_ledger`、`publication_eval/latest.json`、`controller_decisions/latest.json`：承担 `MAS` 医学研究 owner truth。

`memory` 不得替代 baseline、analysis、paper state 或 publication gate 的主记录。

## 7. 当前正式支持的 outer-loop controller actions

当前只冻结四类 action：

- `ensure_study_runtime`
- `ensure_study_runtime_relaunch_stopped`
- `pause_runtime`
- `stop_runtime`

约束：

- 未列入上述清单的 action 一律 fail-closed
- `stop-after-current-step` 的正式状态是 unsupported
- future rerun action 需要新的 canonical spec 才能加入

## 8. bridge 到现有文档

- `./outer_loop_wakeup_and_decision_loop.md`
  - 负责 outer-loop wakeup、artifact loop、decision write-back 主链路
- `./study_runtime_orchestration.md`
  - 负责 `study_runtime_status(...)` / `ensure_study_runtime(...)` 的状态机与执行 contract
- `./study_runtime_control_surface.md`（本文）
  - 负责 stop / rerun / human-confirmation / outer-loop action surface 的单义收口

## 9. runtime truth priority

workspace 层 runtime 真相优先级当前固定为：

1. quest runtime state / `study_runtime_status(...)`
2. workspace `last_launch_report.json`

因此：

- `last_launch_report.json` 是 workspace summary；runtime truth source 由 `study_runtime_status(...)` 承担
- 若 `study_runtime_status(...)` 发现 launch report 与当前 quest status 不一致，允许通过正式 persistence helper 刷新该 summary
- 这种刷新不改变 runtime 本体，只修正 workspace 派生摘要

如果三者冲突：

1. 本文优先裁定 `stop / rerun / human-confirmation` 语义
2. orchestration 文档裁定 runtime state machine 与 transport 执行面
3. outer-loop 文档裁定 escalation -> decision -> next action 的闭环
