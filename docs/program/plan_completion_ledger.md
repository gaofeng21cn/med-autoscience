# Plan Mode 完成性台账

本台账记录 Plan Mode 产生的实施计划是否真正完成。closeout 时必须逐项更新，不允许把“已规划”写成“已完成”。

## 字段

| 字段 | 含义 |
| --- | --- |
| planned | 计划是否已形成明确范围与验收口径 |
| implemented | 代码、文档或运行面是否已实际改动 |
| verified | 是否已运行与改动匹配的验证 |
| pushed | 是否已推送到目标远端或目标分支 |
| cleaned | 临时 worktree、分支、本地状态是否已清理 |
| live_validated | 是否已在真实 workspace / live surface 做只读验收 |
| superseded | 是否已被后续计划替代 |
| blocked | 是否有明确外部阻塞，且记录了阻塞原因 |

## 当前计划记录

| plan_id | scope | planned | implemented | verified | pushed | cleaned | live_validated | superseded | blocked | closeout_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-01-mas-mds-non-truth-kernel-closeout | MAS/MDS 非 Truth-Kernel 收口：AI Doctor/SLO live 接入、上游 PR 状态、Plan Mode 台账 | yes | yes_on_branch | yes_full_lane | branch_only | no | yes_dm_cvd_002_003_004 | no | no | 本轮只在 `codex/mas-non-truth-closeout` worktree 实施并验证；MAS 根 checkout 仍有 Truth Kernel ahead/active 状态，本轮不吸收到 root main、不清理该隔离 worktree。 |
| 2026-05-01-truth-kernel-current-line | MAS Truth Kernel 当前线 | yes | external_active_conversation | external_active_conversation | external_active_conversation | external_active_conversation | external_active_conversation | no | blocked | 不触碰 `truth-fixtures-governance`、`truth-projections`、`truth-reconcile`；由其他对话继续收口。 |

## 上游 PR 状态

| upstream_pr | title | current_status | completion_policy |
| --- | --- | --- | --- |
| #65 | Runner: sidecar oversized Codex tool results | merged_upstream | 可计入 upstream 已吸收；本轮不再重复清理。 |
| #66 | Runtime: bound bash logs and skip runtime mirrors | merged_upstream | 可计入 upstream 已吸收；本轮不再重复清理。 |
| #67 | Diagnostics: classify provider runner failures | merged_upstream | 可计入 upstream 已吸收；本轮不再重复清理。 |
| #71 | Cache repeated MCP reads and add tool-budget telemetry | opened_pending_upstream_review | 不标记完成；保留 PR worktree/branch，等待 upstream review。 |
| #72 | Extract runtime storage maintenance helpers | opened_pending_upstream_review | 不标记完成；保留 PR worktree/branch，等待 upstream review。 |
| #73 | Return sidecar deltas for paper write artifacts | opened_pending_upstream_review | 不标记完成；保留 PR worktree/branch，等待 upstream review。 |
| #74 | Tighten publishability stop-loss guidance | opened_pending_upstream_review | 不标记完成；保留 PR worktree/branch，等待 upstream review。 |

## Closeout 规则

1. closeout 必须逐项填写 `planned / implemented / verified / pushed / cleaned / live_validated / superseded / blocked`。
2. open upstream PR 只能记录为 `opened_pending_upstream_review`，不能标记为完成。
3. 正在 review 的 PR worktree/branch 不清理；只有确认 PR merged/closed 且本地无未提交改动后才清理。
4. live study artifact 不允许手工 patch 作为最终修复；必须由 repo 层实现或 canonical controller/runtime surface 重新生成。
