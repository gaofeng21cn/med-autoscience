# Plan Mode 完成性台账

本台账用于记录 Plan Mode 产生的实施计划是否真正完成。closeout 时必须逐项填写，不允许把“已规划”写成“已完成”。

## 必填字段

| 字段 | 含义 |
| --- | --- |
| `planned_items` | 计划拆出的验收项，必须能逐项判定。 |
| `landed_commits` | 已落地的 commit 或分支；未落地写 `none`。 |
| `tests_run` | 实际运行的验证命令；未运行写 `none` 并说明原因。 |
| `pushed` | 是否已推送到目标远端或目标分支。 |
| `worktrees_cleaned` | 临时 worktree/branch 是否已清理；活跃外部线必须写 owner。 |
| `live_surface_verified` | 是否在真实 workspace 或 stable runtime surface 做只读验收。 |
| `skipped_with_user_acceptance` | 哪些项经用户明确接受后跳过。 |
| `remaining_gaps` | 尚未闭环的问题；没有写 `none`。 |

## 当前计划记录

| plan_id | planned_items | landed_commits | tests_run | pushed | worktrees_cleaned | live_surface_verified | skipped_with_user_acceptance | remaining_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-01-mas-mds-history-plan-closeout | completion ledger; parked telemetry closeout; study_progress SLO projection; parked/liveness consistency; manual_finishing visible-state normalization; live-regression fixtures | MAS `f660567 fix: close plan completion runtime surfaces`; MDS `3c1a7ba fix: backfill parked closeout telemetry` | MAS targeted progress/runtime/operator tests; MAS `make test-meta`; MAS `scripts/verify.sh`; MDS parked closeout targeted tests; MDS `scripts/verify.sh` | pending push | pending cleanup of this plan worktrees only | DM-CVD 002/003 reread 2026-05-01: `autonomy_slo_status_path` materialized for both; 002/003 now have live Codex child workers, so current active-run telemetry is expected to remain pending until run closeout | none | live daemon process predates the MDS telemetry-backfill commit, and historical completed parked runs still lack telemetry until a safe daemon restart or next patched audit; do not stop active 002/003 workers just to backfill history |
| 2026-05-01-truth-kernel-current-line | truth kernel reconcile/projection/fixture governance | external_active_conversation | external_active_conversation | external_active_conversation | external_active_conversation owned outside this task | external_active_conversation | not in scope per user instruction | excluded from this closeout |

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

1. `done` 必须同时有落地证据、验证证据和 cleanup/push 状态。
2. open upstream PR 只能记录为 `opened_pending_upstream_review`，不能标记为完成。
3. 正在其他对话处理的 worktree/branch 必须标 owner，不得吸收或清理。
4. live study artifact 不允许手工 patch 作为最终修复；必须由 repo 层实现或 canonical controller/runtime surface 重新生成。
