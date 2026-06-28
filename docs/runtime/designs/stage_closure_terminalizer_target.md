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

## 实施顺序

1. Contract first：新增 stage closure terminalizer contract 和 fixture。
2. Delivery split first：拆 `current_package` mirror sync 与 submission-ready build authority。先修 DM002 stale / DM003 missing 的直接断点。
3. Reducer first：实现纯 reducer，不接 authority writes。
4. Budget first：把 repair budget、attempt count、budget exhausted outcome 加到 gate / quality closeout。
5. Projection first：让 `study progress` / `paper-mission inspect` 显示 terminalizer decision、repair budget、package kind、known blockers。
6. Drive integration：`paper-mission drive` 在每轮 closeout 后调用 terminalizer，禁止同义 continue loop。
7. OPL readback parity：OPL StageRun closeout 补齐 terminalizer 所需 identity / duration / token-observed-or-missing 字段。
8. Live canary：DM002 / DM003 各跑一次 readback，要求 exactly one closure outcome。

## 不做的事

- 不把 terminalizer 做成新 scheduler。
- 不让 OPL 生成 MAS owner receipt、typed blocker 或 human gate。
- 不用 inspection package / candidate package 代替 stage closure。
- 不要求每个 quality blocker 立刻人类决策；能自动降 claim、收 scope、替代证据或 carry-forward risk 的仍自动推进。
- 不用 docs、tests 或 read-model freshness 代替 live DM002 / DM003 closure evidence。
