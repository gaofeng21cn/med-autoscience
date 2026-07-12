# Stage Closure Terminalizer Target

Owner: `MedAutoScience`
Purpose: `stage_closure_terminalizer_target_design`
State: `active_design`
Machine boundary: 本文是人读顶层设计与落地计划。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、OPL runtime readback、MAS owner receipt、typed blocker、human gate、publication eval、controller decisions 与真实 workspace artifacts。本文不授权写 Yang authority、paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker authority file、human gate、submission package 或 `current_package`。
Date: `2026-06-28`

## 背景

DM002 / DM003 暴露的根因不是 OPL provider 慢，也不是某个 repair action 单次执行慢，而是当前 stage 缺少强制收尾协议。`quality_repair_batch`、`gate_clearing_batch`、AI reviewer record、OPL terminal closeout 和 delivery authority readback 都能产生中间 evidence，但 blocked gate replay 仍会回到 `continue_same_stage`，没有被收束为 MAS 可消费的终态。

这导致同一 stage 可以反复产生 candidate / inspection package / repair delta / closeout，却不能稳定进入下一 stage，也不能形成正式 typed blocker 或 human gate。

2026-06-28 调研进一步把缺口拆成两个可修问题：

1. 修复预算耗尽后的降级放行协议没有接到 delivery authority。质量 gate 仍 blocked 时，系统继续停在同一 stage，而不是生成带 known blockers 的 degraded / pre-package handoff。
2. `delivery-sync` 写权限边界过窄，把 `manuscript/current_package` 这种 human-facing current mirror 错误绑定到 `bundle_build_allowed` / submission-ready authority gate。结果是内部 source package 已变，但 DM002 的 current package stale、DM003 的 current package missing。

## 外部工程经验转译

成熟系统的共同模式不是让普通工作循环自然结束，而是把长流程分成 desired state、execution、terminalization 和 human interrupt：

- Kubernetes controller：controller 持续把 actual state 推向 desired state，并把 current status 回写；status 不是 desired truth，也不是业务完成裁决。
- Temporal：durable execution 允许 workflow 跨故障运行很久，但失败处理仍要通过 retry / error handling / compensation，把 activity 结果收束进 workflow decision。
- AWS Step Functions：Task 可以配置 Retry / Catch；当 retry 耗尽或错误发生时，必须进入显式 fallback state，而不是原地无限重试。
- LangGraph / human-in-the-loop：interrupt 明确暂停、保存状态并等待 resume；human input 是显式 resume event，不是普通状态文本。

MAS / OPL 的目标转译：

- OPL 负责 durable execution、attempt、retry/dead-letter、outbox、StageRun、human gate transport 和 observability。
- MAS 负责 stage semantics、publication / artifact / reviewer authority、owner receipt、typed blocker、human gate declaration 和 next stage decision。
- 普通 repair loop 不能自己决定 stage 已结束；必须经过 MAS Stage Closure Terminalizer。

## 目标模型

每个 MAS paper stage 的收尾必须经过一个唯一 terminalizer：

```text
StageWorkResult
  + owner action receipt
  + gate replay result
  + delivery authority readback
  + OPL closeout readback
  + currentness / identity proof
    -> StageClosureTerminalizer
      -> exactly one StageClosureOutcome
```

`StageClosureOutcome` 只能是以下四类之一：

| outcome | 含义 | 可触发后续 |
| --- | --- | --- |
| `owner_receipt` | MAS owner 接受当前 stage work，并明确 next owner / next stage / delivery permission。 | next stage 或 delivery materialization |
| `typed_blocker` | 当前 stage 已不能自动推进，阻断被归一到最小 owner surface 和恢复条件。 | stop / repair lane / later resume |
| `human_gate` | 只剩真实人类偏好、伦理、凭据、投稿授权或不可逆外部提交决策。 | OPL human gate transport + resume |
| `next_stage_transition` | 当前 stage 已满足终止条件，可进入下一 paper stage。 | OPL route command / next MAS stage |

## Package Authority Split

必须把包分成三层，不能继续混用：

| package kind | 写入面 | authority gate | can_submit | 用途 |
| --- | --- | --- | --- | --- |
| `current_package` | `manuscript/current_package` / `current_package.zip` | 只要求 source package 存在、source signature 可追踪、写入目标是 human-facing mirror。不得要求 `bundle_build_allowed=true`。 | false unless gate passed | 随时给人审阅当前论文状态；允许带 blocker。 |
| `degraded_handoff_package` / `pre_submission_package` | human-facing handoff package | repair budget exhausted 或 terminalizer 选择 degraded handoff；必须携带 known blockers。 | false | 质量未完全通过但可交接，不允许 stage 卡死。 |
| `submission_ready_package` | journal / final submission package | publication gate passed 或 MAS authority 明确授权；需要 `bundle_build_allowed=true`。 | true | 真正投稿包。 |

`bundle_build_allowed` 只控制 `submission_ready_package`、journal package、`can_submit=true` 的最终包，以及任何对外声称 publication/submission ready 的产物。它不能阻止 `current_package` mirror 自动刷新。

`current_package` manifest 在 gate blocked 时必须显式写出：

```json
{
  "package_kind": "current_package",
  "can_submit": false,
  "quality_gate_status": "blocked",
  "known_blockers": [],
  "generated_from_current_source": true,
  "source_signature": "..."
}
```

禁止 terminalizer 输出：

- `continue_same_stage` without semantic delta
- `candidate_ready` as terminal
- `inspection_package_generated` as terminal
- `OPL completed` as domain-ready
- `OPL completed` / provider closeout as paper progress
- `gate blocked` without typed blocker or human gate
- `bundle_build_allowed=false` as final stop
- `focused tests passed` / `queue empty` / `read-model fresh` as progress

## Stage Closure Contract

新增或收敛一个机器合同：

```json
{
  "surface_kind": "mas_stage_closure_decision",
  "schema_version": 1,
  "study_id": "...",
  "stage_id": "...",
  "work_unit_id": "...",
  "work_unit_fingerprint": "...",
  "identity": {
    "paper_mission_run_id": "...",
    "transaction_id": "...",
    "route_identity_key": "...",
    "attempt_idempotency_key": "..."
  },
  "inputs": {
    "owner_action_result_ref": "...",
    "gate_replay_ref": "...",
    "delivery_authority_readback_ref": "...",
    "opl_terminal_closeout_ref": "..."
  },
  "semantic_delta": {
    "paper_delta_refs": [],
    "reviewer_delta_refs": [],
    "gate_delta_refs": [],
    "delivery_delta_refs": [],
    "owner_decision_refs": []
  },
  "outcome": {
    "kind": "owner_receipt|typed_blocker|human_gate|next_stage_transition",
    "authority_materialized": false,
    "next_owner": "...",
    "next_action": "...",
    "resume_condition": "..."
  },
  "forbidden_interpretations": [
    "provider_completion_is_domain_ready",
    "candidate_is_submission_ready",
    "blocked_gate_is_final_without_typed_blocker"
  ]
}
```

## Decision Rules

1. If gate replay passes and delivery authority readback allows package sync, terminalizer emits `owner_receipt` or `next_stage_transition`.
2. If gate replay remains blocked by repairable paper / evidence / reviewer issues, terminalizer emits the next owner action only once per semantic signature. Repeating the same signature must emit `typed_blocker`, `human_gate`, `carry_forward_decision`, `scope_decision`, `evidence_decision`, or `pivot_decision`.
3. If the blocker is submission/package authorization, terminalizer must choose one:
   - authorized owner receipt enabling `bundle_build_allowed`;
   - human gate for irreversible submission/package authorization;
   - typed blocker naming the exact missing authority surface.
4. If OPL closeout is terminal but domain gate remains pending, terminalizer consumes it as input only. It cannot let OPL terminal status become MAS stage completion.
5. If no semantic delta is present after a configured budget, terminalizer must fail closed to a typed blocker or human gate. It may not output another runnable `continue_same_stage`.
6. If gate replay remains blocked by quality-repairable blockers after budget exhaustion, terminalizer emits `degraded_handoff_package` plus `next_stage_transition` to human review / pre-package handoff, not another repair loop.
7. If delivery inspection reports `current_package` stale or missing, terminalizer must request or perform mirror sync independently of `bundle_build_allowed`. A stale/missing mirror is not a submission authority blocker.
8. Delivery projection is terminalizer input, not next-action authority. Even
   when the latest delivery projection is current / fresh / synced and carries
   `submission_ready_package`, `can_submit=true`, `quality_gate_status` clear /
   passed / cleared, `generated_from_current_source=true`, existing package root
   and zip, and `known_blockers=[]`, it can only support MAS owner consumption
   of the same identity. `mission.complete` appears only after that owner
   consumption materializes a `StageOutcome -> NextActionEnvelope`. Missing,
   stale, mirror-only or blocked package evidence must stay fail-closed as
   observation. Delivery mirror readback alone must not project owner receipt,
   choose next action, write owner receipt authority, typed blocker, human gate,
   package authority, runtime queue, provider attempt,
   `publication_eval/latest.json`, or `controller_decisions/latest.json`.

## Blocker Taxonomy

Gate blockers must be classified before they can stop a stage:

| class | examples | terminalizer behavior |
| --- | --- | --- |
| `quality_repairable` | `reviewer_first_concerns_unresolved`, `claim_evidence_consistency_failed`, `submission_hardening_incomplete`, `forbidden_manuscript_terminology`, `submission_surface_qc_failure_present`, `medical_publication_surface_blocked` | Repair while budget remains. On budget exhaustion, generate degraded handoff with known blockers and `can_submit=false`. |
| `mirror_sync` | `stale_study_delivery_mirror`, stale or missing `current_package` | Auto-refresh `current_package` mirror. Does not require `bundle_build_allowed=true`. |
| `submission_authority` | `stale_submission_minimal_authority`, missing submission-ready authority snapshot, final journal package authorization | Blocks `submission_ready_package`, but not `current_package` mirror. May become human gate or typed blocker if no owner can authorize. |
| `hard_authority` | missing source/data, privacy/ethics/credential boundary, forbidden write target, irreversible external submission authorization | Stop as typed blocker or human gate with smallest owner surface and resume command. |

Repair budget fields must be machine-readable:

```json
{
  "repair_budget_max": 3,
  "repair_attempt_count": 3,
  "repair_budget_status": "exhausted",
  "on_exhausted": "degraded_handoff"
}
```

预算来源必须是真实 `quality_repair_batch` / `gate_clearing_batch`
followthrough 或等价 owner-surface readback。若这些 batch 把预算嵌套在各自 key
下，terminalizer / progress projection 只做字段归一化，不猜测预算、不从 queue
状态、focused tests、OPL completed 或 `accepted_submission_milestone_candidate`
推导尝试次数。归一化输出固定为 `repair_budget_max`、
`repair_attempt_count`、`repair_budget_status` 与
`on_exhausted=degraded_handoff`；多个来源同时存在时，`exhausted` 的 batch 优先，
因为它决定是否进入 degraded / pre-submission handoff。

## OPL 基座优化

OPL 不需要知道医学 publication 是否 ready，但必须给 terminalizer 可靠输入：

| OPL primitive | Required optimization |
| --- | --- |
| `StageRun` | 每个 attempt closeout 必须携带 stable identity、attempt idempotency、input refs、output refs、duration、token/cost observed-or-missing 和 terminal reason。 |
| `Transactional Outbox` | route command、provider start、human gate transport、MAS owner callable invocation 都必须由同一 transition event 派生，避免 read-model 反向入队。 |
| `Retry / Dead-letter` | retry exhausted 不能只显示 queue blocked；必须提供 terminal closeout ref 和 retry exhaustion reason，供 MAS terminalizer 归类。 |
| `HumanGateTransport` | 只运输 MAS 声明的 gate question、options、resume token、timeout 和 answer refs；不创建 MAS human gate authority。 |
| `StateIndex` | 只投影 refs、freshness、currentness 和 trace；不得从 provider completion 推导 MAS owner answer。 |
| `Observability` | token/cost/duration 缺失要显式记录为 observability gap；不得填 0 或猜测。 |

最低 OPL readback parity contract 不要求 MAS 新建平台；如果现有 StageRun / closeout / attempt ledger 已有 surface，MAS 只消费并文档化这些字段。缺字段时，修复 owner 是 OPL readback surface，而不是 MAS terminalizer 私自猜测：

| parity field | 最低要求 | 缺失读法 |
| --- | --- | --- |
| `identity` | 同一 `study_id`、`stage_id` / `work_unit_id`、`work_unit_fingerprint`、`route_identity_key` 与 `attempt_idempotency_key` 可比对。 | fail closed 为 cross-identity / stale-readback gap。 |
| `attempt_idempotency` | 同一 route command 重试必须读回同一 idempotency key，避免 closeout 被重复消费或跨 attempt 消费。 | 只能作为 diagnostic closeout，不改变 MAS stage outcome。 |
| `duration` | attempt duration 以 observed value 或 explicit missing marker 表达。 | 记录 observability gap；不填 0，不阻断 terminalizer 四态裁决。 |
| `token/cost` | token 与 cost 各自 observed-or-missing，缺失必须显式标记。 | 记录 observability gap；不得用估算值支持 readiness / cost claim。 |
| `terminal_reason` | terminal closeout 必须说明完成、失败、retry exhausted、human gate transport、provider terminal 或 runtime blocker 的最小原因。 | 不能把 `completed` / `queue blocked` / `checkpoint` 当 MAS domain closeout。 |

## MAS 落地面

最小可维护落地不新建大平台，只补一个强制收尾层：

1. `contracts/mas-stage-closure-terminalizer.json`
   - 定义 `StageClosureDecision`、输入 refs、四类 outcome、forbidden interpretations、identity gate。
2. `src/med_autoscience/controllers/stage_closure_terminalizer.py`
   - 纯 reducer：读取已存在 batch / gate / delivery / OPL readback payload，输出 decision payload。
   - 不写 authority surface。
3. `study progress` projection
   - 当前 work unit 若已有 gate replay blocked，不再只显示 `continue_same_stage`。
   - 必须显示 terminalizer outcome 或 `stage_closure_decision_missing`。
4. `paper-mission drive`
   - 在 `consume-candidate` / OPL closeout / owner callable 后调用 terminalizer。
   - 若 terminalizer 没有四态 outcome，命令 fail closed，不继续造同义 candidate。
5. `quality_repair_batch` / `gate_clearing_batch`
   - 保持现有 repair 行为，但 closeout 必须进入 terminalizer。
   - blocked gate replay 必须产生 structured blocker candidates，供 terminalizer 归并。
6. `study_delivery_sync`
   - 拆分 mirror sync 与 submission-ready build。
   - `current_package` mirror sync 不再要求 `bundle_build_allowed=true`。
   - submission-ready / journal package / `can_submit=true` build 继续要求 authority snapshot。

## 2026-06-29 默认读面收口

`study progress` 的默认 PaperMission readback 只允许从 MAS stage terminal outcome 派生当前状态：

- `paper_mission_run`
- `paper_mission_transaction`
- `stage_terminal_decision`
- `ai_route_context`
- `stage_closure_decision`
- MAS owner receipt / typed blocker / human gate / route-back refs

以下旧面不得再参与默认 stage 完成判断，也不得作为默认 JSON 字段继续暴露：

- `platform_diagnostics`
- `legacy_path_role`
- legacy projection folded fields
- `current_objective_source=diagnostic_fallback`
- `next_owner_source=diagnostic_fallback`
- `opl_stage_attempt_readback`
- `opl_stage_attempt_readback_status`
- `terminal_owner_gate*` derived from OPL closeout

OPL runtime receipt 的角色是 transport receipt，只能说明同一 route command 是否被 OPL 接管、运行或失败；它不能改写 `stage_terminal_decision`、不能选择 `next_owner`，也不能把 provider terminal status 转成 MAS domain completion。需要 OPL runtime 调试时，应走专门 runtime receipt/readback surface，而不是把 queue、attempt、provider closeout 或 legacy projection 回灌进默认 `study progress`。

2026-06-28 当前落地状态：

- `contract / reducer / delivery split` 已落地到 repo 功能面：Stage Closure Terminalizer contract、纯 reducer、CLI / read-model projection 和 `current_package` mirror vs submission-ready authority split 已有实现与 tests evidence。
- `submission_ready` 仍需要 gate 清理：只有 publication gate / MAS authority snapshot 明确允许 `bundle_build_allowed=true` 或等价 final package authorization，才可生成或声明 `submission_ready_package` / `can_submit=true`。
- 下一合法论文动作仍是 owner route，而不是继续造包：`study progress` 当前 action 指向 `return_to_ai_reviewer_workflow`；`paper-mission inspect` 的 terminalizer action 指向 `consume_route_back_checkpoint_or_materialize_terminalizer_outcome`。后续必须通过 AI reviewer / gate clearing / quality repair / legal delivery sync 或等价 MAS owner surface 消费，不能手写 owner receipt、typed blocker、human gate、controller decision、runtime queue 或 package authority。
- 本文档更新只补 readback parity 与验收口径；不写 Yang workspace、`current_package`、submission package、owner receipt、typed blocker、human gate、runtime queue/provider attempt 或 source/paper body。

2026-06-29 Phase A structural closeout 追加：

- `current_package` mirror manifest 必须携带 `package_kind=current_package`、`can_submit=false`、`quality_gate_status`、`known_blockers`、`generated_from_current_source=true` 与 `source_signature`；这些字段是 mirror-only overlay，不改变 controller-authorized source manifest，也不参与 stale 判定。
- `study progress` 顶层必须投影 `current_package`、`repair_budget` 和 `stage_closure`，并保留 nested `paper_mission_run.stage_closure_readback`；调用者不需要把 `accepted_submission_milestone_candidate`、`current_package` 或 `stage_closure_decision` 自行解释成完成态。
- `paper-mission inspect` 必须输出 `durable_mission_stop_guard`，显式声明 `accepted_submission_milestone_candidate_is_durable_stop=false`，并要求 terminalizer outcome、可交付 package / pre-package artifact、owner receipt / typed blocker / human gate / terminal next-stage transition 才能关闭 durable mission。`current_package_mirror_sync`、`route_back_candidate_checkpoint` 和 `bounded_quality_repair_iteration` 是继续推进动作，不是 durable stop。
- `quality_repair_batch` / `gate_clearing_batch` followthrough 若已有预算字段，必须投影为 `repair_budget_max`、`repair_attempt_count`、`repair_budget_status`、`on_exhausted=degraded_handoff`；缺字段只显示缺失，不猜测预算。
- 本段只定义 repo 功能面与 fixture/local readback 验收；DM002 / DM003 live `delivery-inspect`、`study progress`、`paper-mission inspect` acceptance 属于 Phase B，不能由 focused tests、docs 或 contracts 代替。

旧完成态残留治理：

- `accepted_submission_milestone_candidate` 只能是 candidate / owner-consumption input；
  不能成为 durable stop、final package、paper progress 或 submission-ready。
- `bundle_build_allowed=false` 只能阻断 `submission_ready_package` / `can_submit=true`；
  不能阻断 `current_package` mirror，也不能作为 current stage 的最终 stop。
- `current_package` 是 human-facing mirror；`current_package` 存在或 fresh 不等于
  `submission_ready_package`。
- `continue_same_stage` 只有在有新 semantic delta 或预算仍可合法 repair 时才允许；
  预算耗尽或同签名无 delta 时必须转成 degraded handoff、typed blocker、human gate、
  owner decision 或下一 stage transition。

## DM002 / DM003 目标验收

每篇 paper 的当前 stage 不允许再以 `accepted_submission_milestone_candidate`、inspection package、preflight packet、OPL completed 或 `bundle_build_allowed=false` durable stop。

最小验收：

- `paper-mission inspect` 暴露 `stage_closure_decision_ref`。
- `study progress` 显示 exactly one terminalizer outcome。
- `delivery-inspect` 的 stale / missing package 状态被 terminalizer 归入 owner receipt、typed blocker、human gate 或 next stage transition。
- `delivery-inspect` 的 `current_package` stale / missing 能通过 mirror sync 自动变为 current，并在 manifest 中保留 `can_submit=false` 与 known blockers。
- repair budget exhausted 时生成 degraded / pre-package handoff，不再继续同义 repair loop。
- 同一 semantic signature 第二次出现时，不能再产生 runnable `continue_same_stage`。
- token/cost 缺失被记录为 observability gap，不阻断 stage closure。

三层 handoff / readiness runbook：

| layer | 可关闭的验收 | 不能声明 |
| --- | --- | --- |
| `current_package_handoff` | current source package 存在，source signature 可追踪，`manuscript/current_package` 与 zip manifest 显示 `package_kind=current_package`、`can_submit=false unless gate passed`、known blockers / quality gate state 明确，并有 fresh delivery readback。 | submission-ready、publication-ready、owner receipt、typed blocker authority、human gate、paper body mutation。 |
| `degraded_or_pre_submission_handoff` | repair budget exhausted 或 terminalizer 选择 degraded handoff；package / handoff ref 携带 known blockers、next owner、resume condition 和 `can_submit=false`；stage 不再继续同义 repair loop。 | durable final、journal submission package、quality gate passed、human approval complete。 |
| `submission_ready` | publication gate passed 或 MAS authority 明确授权 final build；`bundle_build_allowed=true` / 等价 authority snapshot fresh；final package manifest 可追踪到 owner / gate evidence。 | 任何缺 authority snapshot、只靠 checkpoint、current mirror、candidate package、queue state 或 focused tests 的 ready claim。 |

`submission_ready` 的 readback terminalization 还必须让 canonical
NextActionEnvelope 停止同义 gate replay / route-back redrive：精确成功态
`owner_receipt + submission_ready_package + can_submit=true + gate clear + current/fresh/synced delivery projection + existing package root/zip + no blockers`
映射为 `mission.complete`；裸 `owner_receipt`、missing/stale `current_package`
mirror、blocked gate 或带 known blockers 的包不得映射为 `mission.complete`。

`checkpoint`、candidate package、inspection package、read-model freshness、queue empty 和 focused tests 只能证明中间证据或代码路径；它们不能作为 durable final，也不能替代三层账中对应的 fresh artifact / owner / gate evidence。

## 实施顺序

1. Contract first：新增 stage closure terminalizer contract 和 fixture。
2. Delivery split first：拆 `current_package` mirror sync 与 submission-ready build authority。先修 DM002 stale / DM003 missing 的直接断点。
3. Reducer first：实现纯 reducer，不接 authority writes。
4. Budget first：把 repair budget、attempt count、budget exhausted outcome 加到 gate / quality closeout。
5. Projection first：让 `study progress` / `paper-mission inspect` 显示 terminalizer decision、repair budget、package kind、known blockers。
6. Drive integration：`paper-mission drive` 在每轮 closeout 后调用 terminalizer，禁止同义 continue loop。
7. OPL readback parity：OPL StageRun closeout 补齐 terminalizer 所需 identity / duration / token-observed-or-missing 字段。
8. Live canary：DM002 / DM003 各跑一次 readback，要求 exactly one closure outcome。

当前完成度读法：

- 1-6 已按 repo/source/control-plane 功能面落地。
- 7 是 parity 文档/contract 最低口径；如果 OPL 当前 readback 已提供字段，只需消费并保持一致，不新建 MAS 平台。
- 8 仍是 live evidence lane，未被本文档或 focused tests 关闭。

## 不做的事

- 不把 terminalizer 做成新 scheduler。
- 不让 OPL 生成 MAS owner receipt、typed blocker 或 human gate。
- 不用 inspection package / candidate package 代替 stage closure。
- 不要求每个 quality blocker 立刻人类决策；能自动降 claim、收 scope、替代证据或 carry-forward risk 的仍自动推进。
- 不用 docs、tests 或 read-model freshness 代替 live DM002 / DM003 closure evidence。
