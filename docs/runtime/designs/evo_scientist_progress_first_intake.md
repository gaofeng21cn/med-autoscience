# EvoScientist Progress-First Intake

Owner: `MedAutoScience`
Purpose: `progress_first_learning_sidecar_intake`
State: `active_repo_callable_sidecar_execution_surface`
Machine boundary: 本文是人读 upstream learning foldback。机器真相继续归 `agent/` pack、`contracts/`、runtime/controller durable surfaces、真实 workspace artifact、owner receipt、typed blocker、AI reviewer/auditor record 和 repo-native verification。
Date: `2026-06-09`

## 结论

EvoScientist / EvoSkills 的可吸收点进入 MAS 时只作为 `ordinary progress spine` 的加速层和审计旁路。它们帮助更快选工具、复用失败路径、沉淀观察记忆和组织研究生命周期技能；它们不持有 MAS study truth、publication quality、artifact authority、memory accept/reject、owner receipt、typed blocker、stage transition 或 reviewer/auditor authority。

本轮采用的 upstream facts 是：EvoScientist v0.1.4 release 提到 auxiliary model for background memory workers / tool selector，以及 fire-and-forget observation memory；EvoSkills v1.0.0 提到 research lifecycle skills with IDE / IVE / ESE memory。这些能力只折回 MAS 的 sidecar 设计，不引入 EvoScientist runtime、executor backend、代码、依赖或默认执行 owner。

本设计不保留“后续学习计划”。EvoScientist / EvoSkills 的可取点已经一次性折成 MAS 目标态 sidecar execution architecture，并已落到 repo 可调用执行面：`med_autoscience.runtime_protocol.evo_scientist_sidecar_refs.write_evo_scientist_sidecar_observation` 可写 `artifacts/runtime/evo_scientist_sidecar/` 下的 refs-only observation，`medautosci evo-scientist-sidecar observe/read-latest` 可手工或由 OPL 调用，`study_progress` 在 materialize read-model 时会在 current owner/action 投影后 best-effort 写入 sidecar ref。后续工作只能是在同一合同下扩面生产接入或增加真实 evidence，不再重新决定是否学习、如何学习，也不能新增会阻断 ordinary progress spine 的阶段门。

MAS 普通推进主干保持不变：

```text
current_owner_delta
  -> current medical stage goal
  -> concrete paper / evidence / reviewer / gate delta
  -> ProgressDeltaReceipt / OwnerReceipt / TypedBlocker
  -> next current_owner_delta
```

任何 async learning、auxiliary helper、tool selector 或 memory observation 都不得插入为这条主干的前置 gate。

## 目标态 Sidecar Execution Architecture

Sidecar 的目标态从设计层面完整固定：

| Execution slot | Trigger | Output | Failure policy |
| --- | --- | --- | --- |
| `tool_selector_helper` | tool surface 噪声超过阈值；repo 侧 writer 当前输出 ref slot。 | `tool_affordance_ref`。 | fail open，owner-required tools 永远保留。 |
| `observation_memory_sidecar` | executor turn、subagent completion 或 `study_progress` current owner/action materialization 后。 | `observation_memory_ref`。 | fire-and-forget，mainline 不等待；event fingerprint 幂等写入。 |
| `failed_path_taxonomy` | receipt、typed blocker 或 failed attempt 记录后；CLI 可提交对应 ref。 | `failed_path_memory_ref`。 | 只给 no-loop hint，不关闭 Stage。 |
| `routing_eval` | release / meta regression gate；repo 侧 writer 当前输出 ref slot。 | `route_regression_ref`。 | meta gate only，不作为 live delta gate。 |
| `attempt_budget_stop_loss` | 重复失败签名出现后；repo 侧 writer 当前输出 ref slot。 | `stop_loss_candidate_ref`。 | candidate ref only，必须等 owner decision。 |

统一调度语义：

- OPL 持有通用 sidecar scheduling / execution substrate；MAS 只声明 domain boundary，并接受 refs-only candidates。
- sidecar 与 ordinary progress parallel run；critical path 不等待 sidecar。
- sidecar 缺失、失败、超时、预算耗尽或与 owner policy 冲突时，停止 sidecar，不停止 owner action。
- sidecar 可以提交 hard-gate candidate ref；真正 gate 仍必须由 MAS owner surface、OPL Stage Transition Authority、independent reviewer/auditor、human gate 或 typed blocker materializer 产出。
- 已落地执行入口：`med_autoscience.runtime_protocol.evo_scientist_sidecar_refs.write_evo_scientist_sidecar_observation`、`read_latest_evo_scientist_sidecar_projection`、`medautosci evo-scientist-sidecar observe/read-latest`、`study_progress` materialize hook、`refs_only_state_index_pilot` 的 `evo_scientist_sidecar_ref` family。
- 后续生产扩面只能证明这些槽位按合同运行；不能把 resident daemon 缺失、sidecar completion、tool selector score、observation memory 或 lifecycle skill match 重新写成学习阶段、admission gate 或当前 owner action 的前置条件。

## 可吸收映射

| Upstream fact | MAS 映射 | 权限边界 |
| --- | --- | --- |
| auxiliary model for background memory workers | `async_learning_sidecar`，在后台整理观察、失败签名、上下文压缩和下一步提示。 | 只产出 refs-only hint / audit note；不能写 memory body、memory accept/reject、study truth 或 owner answer。 |
| auxiliary model for tool selector | `tool_selector_helper`，给当前 owner action 提供工具排序和缺口提示。 | 必须 fail open：helper 缺失、超时、低置信或冲突时继续执行 owner tool policy，不阻断 admission。 |
| fire-and-forget observation memory | `observation_memory_sidecar`，把运行观察、失败路径和可复用经验记为旁路 evidence。 | fire-and-forget 成功不等于 progress；失败不等于 blocker。只有 MAS owner 或 quality gate 可把相关事实转成 typed blocker / route-back / human gate。 |
| EvoSkills research lifecycle skills with IDE / IVE / ESE memory | `research_lifecycle_skill_taxonomy`，用于命名 research lifecycle prompt / skill / memory hint family。 | 只能帮助 skill routing 和 reviewer briefing；不能替代独立 reviewer/auditor invocation，也不能关闭质量门。 |

## MAS 采用规则

1. `async_learning_sidecar` 只跟随当前 owner delta，不产生新的 current owner。它可以补充失败路径、工具效果、上下文摘要、memory hint 和 no-loop signal；普通 executor 不需要等它完成。
2. `tool_selector_helper` 是 advisory selector。它可以给出工具优先级、候选工具和拒用理由；当 helper 不可用或结果与 MAS owner policy 冲突时，按 MAS owner policy / OPL allowed action 继续。
3. `failed_path_taxonomy` 用于减少重复走错路：把失败归入 stale currentness、missing owner answer、quality gap、source gap、tool/auth gap、platform repair、human gate、artifact authority gap 等类别。分类本身不关闭 Stage，不授权写 artifact，不写成 paper progress。
4. `observation_memory_sidecar` 只记录观察 ref、source fingerprint、time、scope、suggested reuse 和 confidence。memory body 与 accept/reject/blocker decision 仍归 MAS publication-route memory authority。
5. 独立 reviewer/auditor gate 不被 sidecar 替代。sidecar 可以生成 reviewer briefing、gap hint 或 prior-failure hint；质量结论必须来自独立 invocation、独立 context/task record 和 quality receipt / route-back / typed blocker。

## Hard Gate 转换

Sidecar 观察到 hard-gate 风险时，只能提交 refs-only candidate：

- owner / stage transition / execution authorization / closeout binding 缺失；
- artifact mutation、publication submission、package promotion 或 physical delete 这类不可逆动作；
- human decision、source readiness、memory accept/reject、quality verdict 或 independent reviewer/auditor record 缺失；
- tool/auth failure 导致当前 owner action 无法产生 safe output。

真正的 gate 仍必须由 MAS owner surface、OPL Stage Transition Authority、independent reviewer/auditor、human gate 或 typed blocker materializer 产出。sidecar candidate 不能单独阻断 ordinary progress spine。

## 不能写成

- 不能把 EvoScientist / EvoSkills sidecar 写成 MAS 默认 runtime owner、executor backend、queue、scheduler、memory writer、tool authority 或 quality owner。
- 不能把 async learning completion、tool selector score、observation memory、failed-path taxonomy 或 lifecycle skill match 写成 paper progress、owner receipt、quality verdict、publication-ready、submission-ready、artifact authority 或 production-ready。
- 不能因为 sidecar 缺失、超时、失败或没有 memory hit 阻断当前可执行 owner action。
- 不能把 sidecar-generated reviewer briefing 改名成 reviewer/auditor output；AI-first quality gate 仍要求独立 reviewer/auditor invocation。

## 折回位置

- `docs/active/mas-ideal-state-gap-plan.md` 记录 single Active Truth 中的当前读法、已落地状态、open evidence tail 和禁止误写口径。
- `docs/active/mas-opl-stage-native-state-machine.md` 记录 Stage Native 下 ordinary progress spine / audit sidecar 的设计映射。
- `docs/status.md` 记录 current-state 摘要。
- `docs/decisions.md` 记录 2026-06-09 决策边界。
- `contracts/evo_scientist_progress_accelerator.json` 与 `med_autoscience.evo_scientist_learning_projection.build_evo_scientist_learning_projection` 记录完整目标态 sidecar execution architecture；`remaining_learning_plan=false` 是稳定机器口径。
