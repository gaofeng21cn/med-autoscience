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

## 6. 当前正式支持的 outer-loop controller actions

当前只冻结四类 action：

- `ensure_study_runtime`
- `ensure_study_runtime_relaunch_stopped`
- `pause_runtime`
- `stop_runtime`

约束：

- 未列入上述清单的 action 一律 fail-closed
- `stop-after-current-step` 的正式状态是 unsupported
- future rerun action 需要新的 canonical spec 才能加入

## 7. bridge 到现有文档

- `./outer_loop_wakeup_and_decision_loop.md`
  - 负责 outer-loop wakeup、artifact loop、decision write-back 主链路
- `./study_runtime_orchestration.md`
  - 负责 `study_runtime_status(...)` / `ensure_study_runtime(...)` 的状态机与执行 contract
- `./study_runtime_control_surface.md`（本文）
  - 负责 stop / rerun / human-confirmation / outer-loop action surface 的单义收口

## 8. runtime truth priority

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
