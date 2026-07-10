# Progress-First Stage Outcome

Owner: `MedAutoScience`
Purpose: `stage_outcome_runbook`
State: `active_current_truth`
Machine boundary: 本文是 owner/runbook 说明。机器真相归 stage contracts、NextActionEnvelope、OPL StageRun readback 与 MAS owner receipts。

## 核心规则

每个 stage attempt 必须形成一个可接力 outcome，而不是停在状态刷新：

- 可验证 artifact/evidence delta；
- owner receipt；
- stable typed blocker；
- human gate；
- route-back；
- independent reviewer/auditor receipt。

默认下一步只从 `StageOutcome -> NextActionEnvelope` 产生。OPL 负责 transport/readback，MAS owner 负责医学解释与 authority。

## 最小 outcome shape

Outcome 至少绑定：

- `program_id`、`study_id`、`quest_id`、`active_run_id`；
- stage/attempt identity；
- outcome kind；
- owner 与 required output；
- evidence/artifact refs；
- receipt、blocker 或 human-gate ref；
- forbidden-write/authority boundary。

缺 identity、owner result 或 evidence ref 时 fail closed。不得从旧 provider/current-work-unit projection 推断或拼接下一步。

## Progress 与 platform repair

| Result | 是否算 domain progress |
| --- | --- |
| canonical paper/evidence/artifact semantic delta | 是，需 owner receipt |
| stable typed blocker with owner route | 是，可接力 blocker |
| human gate with resume contract | 是，合法停点 |
| independent reviewer/auditor receipt | 是，按 verdict/route-back 解释 |
| projection/currentness/StateIndex/workbench repair | 否，除非同时产生 domain outcome |
| queue empty / attempt completed / provider ready | 否 |
| docs/tests/schema/descriptor pass | 否 |

## OPL responsibilities

- 创建和恢复 StageRun；
- 维护 command/event/outbox、attempt ledger、retry/dead-letter；
- 运输 owner request/answer 与 human gate；
- 更新 StateIndex 与 hosted workbench projection；
- 保持 same-identity readback。

OPL 不决定医学 quality、publication、artifact 或 memory authority。

## MAS responsibilities

- 定义 stage goal、context、knowledge、quality gate 与 action metadata；
- 评估医学 policy/authority；
- 签 owner receipt或 typed blocker；
- 物化 publication/artifact/memory decision；
- 输出 NextActionEnvelope。

MAS 不维护 runtime transport、queue、StateIndex、health/storage 或 workbench shell。

## Quality stage

需要质量 gate 时，executor 与 reviewer/auditor 必须是独立 invocation、context/task record 与 receipt。同一 executor 的自审、schema pass、scorecard 或 script不能关闭 AI-first quality gate。

## Stop conditions

Stage 可以在以下状态合法停止：

- owner receipt 已确认 terminal outcome；
- stable typed blocker 已绑定 owner route；
- human gate 已有明确 resume input；
- independent reviewer/auditor route-back 已记录；
- stop-loss 由 MAS owner authority 明确授权。

`queue empty`、`no live session`、`provider completed`、`projection clean` 或 `current package exists` 都不是单独 stop proof。

## Live evidence

Synthetic fixtures 与 focused tests只证明 shape。真实 progress 必须 fresh 读取 OPL StageRun/readback、MAS owner receipt与 canonical artifact delta。Live evidence后置时，状态保持 `partial`，不得写成 ready。

## 相关入口

- [Runtime boundary](../contracts/runtime_boundary.md)
- [Controllers](./controllers.md)
- [Invariants](../../invariants.md)
- [Active plan](../../active/mas-ideal-state-gap-plan.md)
