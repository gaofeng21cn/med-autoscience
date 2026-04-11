# Runtime Event And Outer-Loop Input Contract

## 1. 背景

当前 `MedAutoScience -> MedDeepScientist` 托管运行链路已经具备：

- `study_runtime_status`
- `runtime_watch`
- `runtime_escalation_record`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `last_launch_report.json`

这些 durable surfaces 足以表达大多数正式控制动作，但仍然缺一条关键 contract：

- runtime 在进入 `park / pause / stop / waiting_for_user / degraded / stale` 等非 live 状态时，
  没有稳定、显式、quest-owned、可被 MAS 直接消费的事件面。

结果是：

- MAS 需要从 `runtime_state.json`、launch report、watch report、liveness audit、pending interaction 等多个 projection 反推 runtime 真相；
- 很多状态迁移只在 poll tick 中被“推断到”，而不是被“回报到”；
- `pause / stop / parking / invisible` 场景容易从 `runtime_watch` 扫描面消失，或者被折叠成过于宽泛的健康态。

本文件冻结两件事：

1. `runtime event contract`
2. `outer-loop input contract`

它们共同构成 MAS 在当前双仓形态下的最小闭环。

## 2. 设计目标

- 让 MAS 不再只依赖 `poll + inference` 才能知道 quest 已进入非 live 状态。
- 把 quest 级状态迁移收敛成一条稳定、可审计、可复读的事件面。
- 让 outer loop 不再只依赖 `{decision, reason}` 这类压缩摘要做控制决策。
- 保持当前 fail-closed 语义，不引入旁路、启发式纠偏或 silent healing。
- 保持当前 repo-side contract-first 边界，不把 `.omx/`、`manuscript/`、`runtime_watch` 等 projection 升格为 authority root。

## 3. Runtime Event Contract

### 3.1 Owner 与 surface

- owner: `quest-owned runtime artifact`
- stable surface:
  - `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_events/<timestamp>_<event_kind>.json`
  - `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_events/latest.json`

`runtime_event` 是 runtime plane 的正式事件面，不是 launch report 的别名，也不是 runtime watch 的投影。

### 3.2 Event schema

每条 event 至少必须包含：

- `schema_version`
- `event_id`
- `study_id`
- `quest_id`
- `emitted_at`
- `event_source`
- `event_kind`
- `summary_ref`
- `status_snapshot`
- `outer_loop_input`
- `artifact_path`

其中：

- `event_source` 表示是谁物化了这个事件。
  - 当前 repo-side 允许：
    - `study_runtime_status`
    - `study_runtime_execution`
    - `runtime_supervision`
- `event_kind` 表示事件类别。
  - 当前 repo-side 允许：
    - `status_observed`
    - `transition_applied`
    - `supervision_changed`

### 3.3 Status snapshot

`status_snapshot` 至少必须包含：

- `quest_status`
- `decision`
- `reason`
- `active_run_id`
- `runtime_liveness_status`
- `worker_running`
- `continuation_policy`
- `continuation_reason`
- `supervisor_tick_status`
- `controller_owned_finalize_parking`
- `runtime_escalation_ref`

语义要求：

- 这是 MAS 在物化该 event 时看到的 quest 级 runtime snapshot。
- 它不是 launch report summary，也不是 publication eval verdict。
- 它必须保留 pause/stop/park/waiting/degraded 这类一等状态，不得用单一健康态吞并全部语义。

### 3.4 Event emission rules

当前 repo-side 冻结如下：

- `study_runtime_status(...)` 在 managed runtime 上必须写 `status_observed` event。
- `ensure_study_runtime(...)` 在执行 create/resume/pause/relaunch/completion 后必须写 `transition_applied` event。
- `runtime_supervision` 在健康态发生变化时必须写 `supervision_changed` event。

这意味着：

- `stopped`
- `paused`
- `waiting_for_user`
- `controller-owned finalize parking`
- `strict_live` 丢失
- `supervisor tick stale`

都必须能在 quest 级 durable event 面上留下痕迹。

## 4. Outer-Loop Input Contract

### 4.1 Formal input

对 managed runtime，`study_outer_loop_tick(...)` 的 runtime 输入不再只等价于：

- `decision`
- `reason`
- optional `runtime_escalation_ref`

正式输入固定为：

- `runtime_event_ref`
- `runtime_event.outer_loop_input`
- `publication_eval/latest.json`

### 4.2 Outer-loop input schema

`runtime_event.outer_loop_input` 至少必须包含：

- `quest_status`
- `decision`
- `reason`
- `active_run_id`
- `runtime_liveness_status`
- `worker_running`
- `supervisor_tick_status`
- `controller_owned_finalize_parking`
- `interaction_action`
- `interaction_requires_user_input`
- `runtime_escalation_ref`

这些字段是 outer loop 允许直接依赖的 runtime 输入面。

### 4.3 Fail-closed rules

对 managed runtime，outer loop 必须继续 fail-closed：

- 缺 `runtime_event_ref` 时，不得自行假定 runtime 输入完整。
- `runtime_event_ref` 指向的 artifact 不存在、schema 不合法、quest/study 身份不匹配时，必须报错。
- 不得再在 outer loop 内“现造” runtime escalation record 来弥补输入缺口。
- `runtime_escalation_ref` 若存在，必须与 event snapshot 对齐。
- `supervisor_tick_status != fresh` 时，outer loop 不得把运行面描述成“持续稳定托管中”。

## 5. 与现有 surfaces 的关系

- `launch_report`
  - 保持为 runtime orchestration summary
  - 不是 event plane
- `runtime_watch`
  - 保持为 poll/report shell
  - 不替代 runtime event
- `runtime_supervision/latest.json`
  - 保持为 study-level health truth
  - 不替代 quest-level runtime event
- `runtime_escalation_record`
  - 保持为 escalation plane
  - 不能吞并全部 runtime 状态迁移

## 6. Repo-side implementation phases

### P0

- 引入 `runtime_event` durable surface 与 typed schema。
- 在 `study_runtime_status` / `study_runtime_execution` / `runtime_supervision` 上物化 event。
- 让 outer loop 强依赖 `runtime_event_ref`，移除“缺 ref 时自动 synthesize escalation”。

### P1

- 收紧 watch 扫描面，确保 `paused / stopped / idle / created` 不再天然隐身。
- 收紧 runtime summary alignment，不只比对 `quest_status`，还要比对 `active_run_id`、liveness、supervisor freshness。
- 区分 semantic runtime state 与 health state，避免全都坍缩到 `inactive`。

### P2

- 用 transition matrix 补齐测试：
  - `running -> parked`
  - `running -> paused`
  - `running -> stopped`
  - `waiting_for_user -> MAS_resume`
  - `degraded -> live`
  - `fresh -> stale`
  - cross-surface conflict

## 7. 当前限制

这个 contract 目前仍是 repo-side contract 收紧，不等于 external `med-deepscientist` 已完成同等事件语义内建。

在当前双仓形态下，MAS 仍然需要从 repo-side 能读到的 surfaces 物化事件；
真正的 monorepo end-state 则应把该 event plane 下沉为 runtime core 的原生输出。
