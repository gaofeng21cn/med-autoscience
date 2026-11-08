# Study Lifecycle Control

Owner: `MedAutoScience`
Purpose: `durable_study_lifecycle_user_truth`
State: `current`
Machine boundary: 机器真相归 `studies/<study_id>/control/lifecycle.json`。本文只解释状态语义、写入入口、优先级与恢复门禁，不授权手工编辑 ledger、论文正文、publication eval、runtime queue、attempt 或 telemetry。

## 结论

MAS 用独立 lifecycle control 表达用户真正关心的论文状态，不再让旧 stage、runtime residue、heartbeat、provider attempt 或缺失 telemetry 推断“论文现在是什么状态”。

正式状态只有四种：

| 状态 | 用户语义 | 当前 stage | 自动恢复 | 投稿包语义 |
| --- | --- | --- | --- | --- |
| `active` | 研究线正在推进或允许继续推进 | 由当前 MAS/OPL readback 投影 | 允许 | 不自动升级 ready |
| `paused` | 用户暂停，等待显式唤醒 | `null` | 禁止 | `not_ready` |
| `delivered_paused` | 已交付里程碑投稿包，自动暂停 | `null` | 禁止 | `milestone_delivered`，但 `submission_ready=false` |
| `stopped` | 已止损停止，不再自动推进 | `null` | 禁止 | `not_ready` |

`delivered_paused` 只证明 milestone package 已交付，不证明作者信息、机构信息、目标期刊要求、外部提交授权或最终 submission-ready 已满足。

## Canonical Surfaces

单篇论文当前真相：

```text
studies/<study_id>/control/lifecycle.json
```

单篇论文不可变历史：

```text
studies/<study_id>/artifacts/controller/lifecycle_control/history/*.json
```

病种 workspace 聚合账本：

```text
runtime/artifacts/study_lifecycle_control/latest.json
runtime/artifacts/study_lifecycle_control/history/*.json
```

用户总览派生面：

```text
workspace_index.json
reports/studies_index.json
reports/latest_status.json
```

`workspace_index.json` 对 inactive study 必须投影 `current_stage_id=null`、`current_stage_status=null`、正式 `lifecycle_ref` 和 lifecycle-owned package status。结构诊断仍可保存在 `diagnostic_blockers`，但不能把暂停或停止的论文翻译成“需要系统处理”。

## Authority And Precedence

优先级固定为：

1. `control/lifecycle.json` 的显式 MAS lifecycle truth。
2. 当前 MAS paper/progress owner readback。
3. OPL runtime、attempt、heartbeat 与 telemetry projection。
4. legacy runtime、archive 或历史 stage residue。

只要 lifecycle 为 `paused`、`delivered_paused` 或 `stopped`：

- 当前 stage 必须显示为空。
- stale runtime route 不得继续成为下一步。
- App/Framework 可以只读消费，不得覆盖 lifecycle truth。
- Token、耗时和历史 attempt 可继续作为诊断证据，但不改变论文业务状态。

## Formal Write Boundary

Lifecycle 变更必须由当前受权 StageAttempt形成 explicit owner request，并由 MAS
owner-authorized canonical artifact mutation落盘；OPL负责传输、identity、receipt与
readback，不解释或改写 lifecycle语义。不得恢复已退役的 domain-entry dispatch、
workspace wrapper或 direct file-edit command。

Owner request至少绑定：

- `profile_ref`
- `study_id`
- `lifecycle_state`
- `reason_code`
- `reason_summary`
- `source_kind`
- `source_ref`

可选字段：`evidence_refs`、`recorded_at`。

合法 mutation原子更新 per-study current/history与 workspace inventory refs。它不修改论文正文，不写 publication verdict，不提升 current package，也不写 OPL queue/provider state。

## Wakeup Gate

`contracts/study_lifecycle_reactivation_contract.json` 与对应 registry handler
校验显式用户指令、revision intake、inactive lifecycle bytes 和 identity，
返回 exact-bytes CAS request。Framework 完成受权物化并 fresh readback 后才可
进入新的 Stage admission；历史唤醒命令和 force 参数不构成旁路。

## Readback Contract

读取 `control/lifecycle.json`、`workspace_index.json`、Framework Work Item 和
StageRun/Attempt readback。非 active study 必须没有当前 active Stage 和
自动 route admission；业务状态、历史用量和研究 trajectory 分别展示。
MAS App contribution 只消费已解析的 selected work-item identity，不回退到默认论文。
