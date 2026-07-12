# PaperRecovery 事故 replay 与 authority 边界

Owner: `MedAutoScience`
Purpose: `paper_recovery_authority_and_replay_runbook`
State: `superseded_control_design`
Machine boundary: 本文是人读设计与事故 replay runbook。机器真相归 `contracts/paper_recovery_kernel_contract.json`、fresh `study_progress`、Codex CLI route judgment、owner receipt、typed blocker、human gate、route-back evidence 和 canonical changed surface refs；transport readback 不选择或阻断 stage route。

## Supersession notice

2026-06-29 之后，默认论文 next action authority 已由 [Next Action Control Plane](./next_action_control_plane.md) 持有：`StageOutcome -> NextActionEnvelope`。`OPL StageAttemptReceipt` 只作 transport receipt-only evidence 和 MAS owner-consumption input。本文只保留 PaperRecovery 事故 replay、migration diagnostic、provenance 和 no-resurrection guard 读法；不得再用 PaperRecovery / `paper_recovery_state` 生成 `current_executable_owner_action`、provider admission、默认 next action、paper progress、publication-ready 或 submission-ready claim。

Reader rule：本文不是 active runbook、active backlog 或 provider admission 入口。下文保留的 `Kernel`、`Phase`、`Replay`、`Derived surfaces` 和 `Manual foreground adoption` 只解释历史事故如何被判读，以及为什么旧 surface 不应复活；若与当前 [Next Action Control Plane](./next_action_control_plane.md)、`docs/status.md` 或 fresh runtime/owner readback 冲突，以当前 envelope / owner surface 为准。

## Tombstone conclusion

`PaperRecovery` 是历史 recovery obligation kernel，不再是当前控制面。OPL 是 execution substrate，负责 StageRun、attempt ledger、provider liveness、terminal closeout transport、queue / retry / dead-letter 与 workbench shell；OPL 不选择 recovery obligation，不签 MAS owner receipt，不声明 paper progress、publication readiness 或 manual foreground adoption。

历史 `study_progress`、domain diagnostic provider admission、operator card、OPL admission 和 human workbench card 曾从 `paper_recovery_state` 派生。当前默认读面只能从 StageOutcome / NextActionEnvelope / OPL StageAttemptReceipt 派生；本文中的 `paper_recovery_state` 只能展示事故 replay、迁移诊断或历史 recovery obligation，不能从 queue、active run、transport status、operator card、old handoff 或 docs claim 反向生成 current next action。

历史目标接口详见 [PaperRecovery Obligation 目标架构](../designs/paper_recovery_obligation_target_architecture.md)：`RecoveryObligationKernel` 曾用于把 MAS owner evidence、OPL execution observation、terminal closeout refs、manual / human gate refs 和 read-model projection status 归一为 `paper_recovery_state`。当前只能把该 shape 当作诊断/provenance；operator projection 不得从它、queue、active run、transport status 或旧 handoff 重判 currentness。

## Kernel 形状

机器合同入口是 `contracts/paper_recovery_kernel_contract.json`。这些字段只服务 historical diagnostic / replay / no-resurrection guard：

- `surface_kind` / `schema_version` / `study_id`：声明机器 surface 身份。
- `recovery_obligation_id`：当前 recovery 的唯一身份，格式为 `paper-recovery::<study_id>::<action_type>::<work_unit_id>::<work_unit_fingerprint_or_blocker_or_truth_epoch>`。
- `phase`：声明唯一互斥状态。
- `current_authority`：声明当前 owner、authority 和 obligation identity。
- `conditions` / `next_safe_action`：声明为什么处在该 phase，以及下一步安全动作。
- `authority_boundary`：声明 MAS / OPL 的可做与不可做范围。

历史 replay 中只能有一个 diagnostic obligation。零个或多个 obligation 都是 `projection_inconsistency_fail_closed`，不得继续 provider admission、paper progress、owner receipt claim 或 publication-ready claim。

Legacy provider-admission replay 若引用 `paper_recovery_state`，必须携带 `route_identity_key`、`attempt_idempotency_key`、owner-route currentness basis，以及 selected stage packet binding refs，且只能作为 diagnostic / no-resurrection evidence。缺这些字段时只允许进入 diagnostic / typed blocker candidate，不允许 domain-handler export 生成 pending family task；即使字段完整，当前默认 admission 仍必须回到 canonical `NextActionEnvelope` identity。

## Phase 不变量

`phase` 是互斥状态。合同允许 `owner_action_ready`、`admission_pending`、`admission_blocked`、`attempt_running`、`terminal_closeout_ready`、`owner_answer_consumed`、`domain_blocked`、`human_gate`、`projection_inconsistent` 和 `manual_foreground_unadopted`。

关键禁区：

- `admission_pending` 必须有 identity-bound provider admission candidate / count。`domain diagnostic.action_class=observe_only` 不能创建或证明 recovery execution；但已有 identity-bound provider admission candidate / count 时，observe-only 只是诊断，不覆盖 `paper_recovery_state` 的 pending truth。
- `terminal_closeout_ready` 必须走 consume 或 reject。terminal closeout 不能悬挂成隐式 paper progress，也不能触发同 identity redrive。
- `domain_blocked` 中的 stop-loss / anti-loop blocker 必须有 successor obligation 或 human gate。没有 successor / human gate 时保持 fail closed，禁止同 work-unit 重跑。
- `manual_foreground_unadopted` 没有 MAS/OPL adoption refs 时只能是 manual work product，不能写成 governed recovery。

## 事故 replay

Replay 读取顺序固定为：

1. fresh `study_progress`
2. `paper_recovery_state`
3. OPL current-control / attempt / worker live readback
4. MAS `domain_handler_export` refs and same-identity transition/closeout evidence
5. owner receipt / typed blocker / human gate / route-back refs

常见事故与裁决：

| Case | 症状 | 裁决 | 下一安全动作 |
| --- | --- | --- | --- |
| `pending_without_identity_bound_provider_admission` | read-model 或 operator card 仍显示 pending/actionable，但没有 identity-bound provider admission candidate / count，且 domain diagnostic dry-run 是 `observe_only` | `admission_blocked` | run admission apply or report operator gate |
| `terminal_closeout_not_consumed` | OPL/default executor terminal closeout 已存在，但 MAS 未 consume/reject | `terminal_closeout_ready` | consume or reject terminal closeout |
| `same_work_unit_stop_loss` | stop-loss / anti-loop budget 后同一 work unit 继续 redrive | `domain_blocked` | create successor recovery obligation or open human gate |
| `manual_foreground_unadopted` | 前台/人工 paper-local 输出存在，但没有 adoption refs | `manual_foreground_unadopted` | adopt through MAS owner receipt or keep non-authority |

禁止把 `docs_only_claim`、operator card、queue empty、provider completion、active run id、transport status 或无 adoption refs 的 manual foreground output 当作 recovery acceptance evidence。

## Stage-route conformance replay

DM002 / DM003 类卡点的 historical replay 仍可按旧 diagnostic chain 复盘，但该链已被 `StageOutcome -> NextActionEnvelope` 取代为默认 next-action authority：

`legacy stage-route/current-work-unit diagnostic chain`

任何跳过 `MAS closeout consume_or_reject` 的边都只能是诊断；旧链里的 `current_work_unit` / `current_execution_envelope` 也只能作为 diagnostic drilldown，不能覆盖 canonical `NextActionEnvelope`。`queue_empty`、`active_run_id`、transport status、trace/span、read-model projection、stale selected dispatch、old route-back packet 和 provider completion 不能生成 recovery obligation、owner receipt、typed blocker、provider admission 或 paper progress。

`stage_packet_not_current_selected_dispatch` 的 owner 是 OPL。安全出口是 OPL authorization repair owner action、`NextActionEnvelope` / owner-surface 绑定的 derived repair action、successor recovery obligation、human gate 或 route-back evidence；同一 work unit provider admission redrive、stale stage-packet replay 和 foreground gate replay retry 都必须 fail closed。

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

Legacy derived surfaces 若为了事故 replay 读取 `PaperRecovery`，只能投影 `paper_recovery_state` 的 phase、conditions、next safe action 与 authority boundary。`study_progress`、domain diagnostic provider admission、operator status card 和 OPL admission 不得据此自造 current recovery truth、default next action 或 provider admission。

## 派生可见面收口

Historical PaperRecovery replay 中，`paper_recovery_state` 进入 `admission_blocked`、`projection_inconsistent`、`manual_foreground_unadopted`、`terminal_closeout_ready`、`domain_blocked` 或 `human_gate` 时，下列用户/操作员可见面只能把它当作 diagnostic background：

- `operator_status_card`
- `intervention_lane`
- `operator_verdict`
- `auto_runtime_parked`
- `recovery_contract`
- `autonomy_contract`
- `user_visible_projection`

这些 surface 可以展示 `paper_recovery_state.phase`、`recovery_obligation_id`、`current_authority` 和 `next_safe_action` 作为历史事故解释，但不得继续保留旧的 `auto_runtime_parked`、`explicit_resume_pending`、`awaiting_explicit_wakeup` 或“需要用户显式恢复后才能推进”的残留说法，除非 fresh current owner surface 本身就是 `human_gate`。`human_gate` 仍必须来自当前 MAS owner surface / canonical envelope chain，不来自旧 parked runtime。

这条规则解决的是 read-model / operator projection 的剩余漂移：旧停驻面只能是 diagnostic background，不能重新成为 current recovery authority。

## Manual foreground adoption

前台 Codex 或人工可以在用户明确授权时产出 manual foreground work product，但默认不更新 MAS/OPL truth。它要被 governed recovery 采信，必须至少有以下 adoption refs 之一：

- MAS owner receipt ref
- quality gate receipt ref
- 被 MAS/OPL 消费的 canonical changed surface ref
- stable typed blocker ref
- human gate ref
- route-back evidence ref

缺少 adoption refs 时，manual output 不能清 current obligation、不能触发 OPL admission、不能声明 publication-ready，也不能手写 `publication_eval/latest.json`、`controller_decisions/latest.json` 或 runtime/study artifacts。
