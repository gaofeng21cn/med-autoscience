# PaperRecovery 事故 replay 与 authority 边界

Owner: `MedAutoScience`
Purpose: `paper_recovery_authority_and_replay_runbook`
State: `active_control_design`
Machine boundary: 本文是人读设计与事故 replay runbook。机器真相归 `contracts/paper_recovery_kernel_contract.json`、`contracts/stage_route_reconcile_contract.json`、fresh `study_progress`、DHD dry-run / apply、OPL current-control、owner receipt、typed blocker、human gate、route-back evidence 和 canonical changed surface refs。

## 当前结论

`PaperRecovery` 是 MAS authority kernel。OPL 是 recovery obligation 的 execution substrate，负责 StageRun、attempt ledger、provider liveness、terminal closeout transport、queue / retry / dead-letter 与 workbench shell；OPL 不选择 recovery obligation，不签 MAS owner receipt，不声明 paper progress、publication readiness 或 manual foreground adoption。

所有 `study_progress`、DHD provider admission、operator card、OPL admission 和 human workbench card 都必须从 `paper_recovery_state` 派生。它们只能展示、执行或运输 `PaperRecovery` 当前义务，不能从 queue、active run、transport status、operator card、old handoff 或 docs claim 反向生成 paper recovery truth。

目标接口详见 [PaperRecovery Obligation 目标架构](../designs/paper_recovery_obligation_target_architecture.md)：`RecoveryObligationKernel` 接收 MAS owner evidence、OPL execution observation、terminal closeout refs、manual / human gate refs 和 read-model projection status，输出唯一 `paper_recovery_state`。所有 operator projection 都必须消费该输出，不能各自重判 currentness。

## Kernel 形状

机器合同入口是 `contracts/paper_recovery_kernel_contract.json`。目标态固定以下字段：

- `surface_kind` / `schema_version` / `study_id`：声明机器 surface 身份。
- `recovery_obligation_id`：当前 recovery 的唯一身份，格式为 `paper-recovery::<study_id>::<action_type>::<work_unit_id>::<work_unit_fingerprint_or_blocker_or_truth_epoch>`。
- `phase`：声明唯一互斥状态。
- `current_authority`：声明当前 owner、authority 和 obligation identity。
- `conditions` / `next_safe_action`：声明为什么处在该 phase，以及下一步安全动作。
- `authority_boundary`：声明 MAS / OPL 的可做与不可做范围。

任何时刻只能有一个 current obligation。零个或多个 current obligation 都是 `projection_inconsistency_fail_closed`，不得继续 provider admission、paper progress、owner receipt claim 或 publication-ready claim。

Provider admission 若要从 `paper_recovery_state` 派生为 OPL StageRun admission，必须携带 `route_identity_key`、`attempt_idempotency_key`、owner-route currentness basis，以及 selected stage packet binding refs。缺这些字段时只允许进入 diagnostic / typed blocker candidate，不允许 domain-handler export 生成 pending family task。

## Phase 不变量

`phase` 是互斥状态。合同允许 `owner_action_ready`、`admission_pending`、`admission_blocked`、`attempt_running`、`terminal_closeout_ready`、`owner_answer_consumed`、`domain_blocked`、`human_gate`、`projection_inconsistent` 和 `manual_foreground_unadopted`。

关键禁区：

- `admission_pending + DHD.action_class=observe_only` 必须变成 `admission_blocked`。observe-only 表示当前没有可当作 recovery execution 的 provider admission。
- `terminal_closeout_ready` 必须走 consume 或 reject。terminal closeout 不能悬挂成隐式 paper progress，也不能触发同 identity redrive。
- `domain_blocked` 中的 stop-loss / anti-loop blocker 必须有 successor obligation 或 human gate。没有 successor / human gate 时保持 fail closed，禁止同 work-unit 重跑。
- `manual_foreground_unadopted` 没有 MAS/OPL adoption refs 时只能是 manual work product，不能写成 governed recovery。

## 事故 replay

Replay 读取顺序固定为：

1. fresh `study_progress`
2. `paper_recovery_state`
3. `domain-health-diagnostic --dry-run`
4. OPL current-control / attempt ledger
5. owner receipt / typed blocker / human gate / route-back refs

常见事故与裁决：

| Case | 症状 | 裁决 | 下一安全动作 |
| --- | --- | --- | --- |
| `pending_plus_observe_only` | read-model 或 operator card 仍显示 pending/actionable，但 DHD dry-run 是 `observe_only` | `admission_blocked` | run admission apply or report operator gate |
| `terminal_closeout_not_consumed` | OPL/default executor terminal closeout 已存在，但 MAS 未 consume/reject | `terminal_closeout_ready` | consume or reject terminal closeout |
| `same_work_unit_stop_loss` | stop-loss / anti-loop budget 后同一 work unit 继续 redrive | `domain_blocked` | create successor recovery obligation or open human gate |
| `manual_foreground_unadopted` | 前台/人工 paper-local 输出存在，但没有 adoption refs | `manual_foreground_unadopted` | adopt through MAS owner receipt or keep non-authority |

禁止把 `docs_only_claim`、operator card、queue empty、provider completion、active run id、transport status 或无 adoption refs 的 manual foreground output 当作 recovery acceptance evidence。

## Stage-route conformance replay

DM002 / DM003 类卡点按同一条 governed chain 复盘：

`current_owner_delta -> current_work_unit -> current_execution_envelope -> provider_admission_current_control -> OPL StageRun -> terminal_closeout -> MAS closeout consume_or_reject -> next_current_owner_delta`

任何跳过 `MAS closeout consume_or_reject` 的边都只能是诊断。`queue_empty`、`active_run_id`、transport status、trace/span、read-model projection、stale selected dispatch、old route-back packet 和 provider completion 不能生成 recovery obligation、owner receipt、typed blocker、provider admission 或 paper progress。

`stage_packet_not_current_selected_dispatch` 的 owner 是 OPL。安全出口是 OPL authorization repair owner action、带 current work-unit binding 的 derived repair action、successor recovery obligation、human gate 或 route-back evidence；同一 work unit provider admission redrive、stale stage-packet replay 和 foreground gate replay retry 都必须 fail closed。

Terminal closeout 若缺 `paper_stage_log` 的 duration、token usage、cost 或其它 required field，必须写成 `missing_with_reason` 并带 refs。缺字段且没有 reason 时，MAS 只能 consume 为 `domain_closeout_provided_incomplete_user_stage_log` typed blocker；这不产生 paper-progress credit，也不触发自动 redrive。

## Authority 边界

MAS 持有：

- `PaperRecovery` schema 与 `paper_recovery_state`
- `recovery_obligation_id` 选择
- current owner delta
- owner receipt、quality gate receipt、stable typed blocker、human gate、route-back evidence
- canonical changed surface adoption

OPL 持有：

- StageRun execution
- attempt ledger
- queue / retry / dead-letter substrate
- provider liveness
- terminal closeout transport
- workbench / operator shell projection

Derived surfaces 必须从 `PaperRecovery` 读取，不得自造 recovery truth。尤其是 `study_progress`、DHD provider admission、operator status card 和 OPL admission 都只能投影 `paper_recovery_state` 的当前义务、phase、conditions、next safe action 与 authority boundary。

## 派生可见面收口

`paper_recovery_state` 一旦进入 `admission_blocked`、`projection_inconsistent`、`manual_foreground_unadopted`、`terminal_closeout_ready`、`domain_blocked` 或 `human_gate`，所有用户/操作员可见面都必须改为 PaperRecovery phase 派生：

- `operator_status_card`
- `intervention_lane`
- `operator_verdict`
- `auto_runtime_parked`
- `recovery_contract`
- `autonomy_contract`
- `user_visible_projection`

这些 surface 可以展示 `paper_recovery_state.phase`、`recovery_obligation_id`、`current_authority` 和 `next_safe_action`，但不得继续保留旧的 `auto_runtime_parked`、`explicit_resume_pending`、`awaiting_explicit_wakeup` 或“需要用户显式恢复后才能推进”的残留说法，除非当前 phase 本身就是 `human_gate`。`human_gate` 仍保留用户决策信号，但它的来源是 PaperRecovery owner/human gate，不是旧 parked runtime。

这条规则解决的是 read-model / operator projection 的剩余漂移：旧停驻面只能是被 PaperRecovery 覆盖的诊断背景，不能重新成为 current recovery authority。

## Manual foreground adoption

前台 Codex 或人工可以在用户明确授权时产出 manual foreground work product，但默认不更新 MAS/OPL truth。它要被 governed recovery 采信，必须至少有以下 adoption refs 之一：

- MAS owner receipt ref
- quality gate receipt ref
- 被 MAS/OPL 消费的 canonical changed surface ref
- stable typed blocker ref
- human gate ref
- route-back evidence ref

缺少 adoption refs 时，manual output 不能清 current obligation、不能触发 OPL admission、不能声明 publication-ready，也不能手写 `publication_eval/latest.json`、`controller_decisions/latest.json` 或 runtime/study artifacts。
