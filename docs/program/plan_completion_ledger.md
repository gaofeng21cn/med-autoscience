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
| 2026-05-01-mas-mds-history-plan-closeout | completion ledger; parked telemetry closeout; study_progress SLO projection; parked/liveness consistency; manual_finishing visible-state normalization; live-regression fixtures | MAS `f660567 fix: close plan completion runtime surfaces`, `d7734fa docs: record plan closeout live verification`; MDS `3c1a7ba fix: backfill parked closeout telemetry` | MAS targeted progress/runtime/operator tests; MAS `make test-meta`; MAS `scripts/verify.sh`; MDS parked closeout targeted tests; MDS `scripts/verify.sh` | yes: MAS main and MDS main pushed | yes: removed `codex/mas-closeout-live-surfaces` and `codex/mds-parked-telemetry-closeout`; external worktrees left untouched | DM-CVD 002/003 reread 2026-05-01: `autonomy_slo_status_path` materialized for both; SLO observer generated `same_fingerprint_loop` AI Doctor requests; 003 projects `auto_runtime_parked / explicit_resume_pending` with no supervision active run after completed parked run; 002 has no active run and SLO breach visible | none | live daemon process predates the MDS telemetry-backfill commit, and completed parked runs still lack `telemetry.json` until a safe daemon restart or next patched audit; do not stop active study infrastructure just to backfill history |
| 2026-05-02-ai-first-operationalization-closeout | 将近期 AI-first Research OS 规划收口成可审阅实施台账；区分已经存在的 repo-level contract/read model；收口 pre-draft runtime、AI reviewer workflow、artifact proof、operations state 四条落地 lane；明确真实论文 soak 是剩余证据缺口；固定本 ledger 是人工/AI 审阅材料，不是机械 gate | absorbed on `main` and pushed to `origin/main`: `8ddb1b2 Merge pre-draft quality runtime`, `b162f72 Merge AI reviewer workflow state`, `010ac56 Merge artifact runtime proof`, `d50a41b Merge AI-first operations runtime state`, `250cc29 Merge AI-first closeout ledger`, plus post-merge default-entry closeout on `main`: `ebc2074 Merge AI-first default entry flow`, `aa333ed Merge AI-first operations default projection`, `e739217 Merge AI-first postmerge closeout ledger` | lane closeout verification recorded as repo-native tests plus doc hygiene; post-merge default-entry closeout verified by focused study-progress/product-entry tests, `make test-meta`, `scripts/verify.sh`, and `git diff --check` | yes: implementation closeout and post-merge default-entry closeout are pushed to `origin/main` | yes for the implementation and post-merge default-entry lanes: `codex/predraft-quality-runtime`, `codex/ai-reviewer-workflow`, `codex/artifact-runtime-proof`, `codex/operations-runtime-state`, `codex/ai-first-default-entry-flow`, `codex/ai-first-operations-default-projection`, and `codex/ai-first-postmerge-closeout-ledger` worktrees/branches are no longer present; unrelated active worktrees remain owned by their lanes | 2026-05-02 tracked docs and default entry surfaces now expose the repo-level state for `StudyTruthKernel`, `RuntimeHealthKernel`, AI-first quality boundary, first-draft quality policy, pre-draft readiness, AI reviewer workflow, canonical artifact proof, AI-first observability/operations dashboard, `study_progress`, `workspace_cockpit`, and `product_frontdesk`;详见 `docs/program/ai_first_operationalization_closeout.md` | none | 真实论文 soak 仍是诚实剩余缺口：至少一条 live manuscript 需要同时证明 pre-draft readiness、AI reviewer-backed publication eval、canonical artifact rebuild proof、operations-state projection，以及 study-progress/product-frontdesk truth 一致；本 ledger 不认证该 soak 已完成，也不宣称真实论文质量改善已被证明 |
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
5. AI-first Research OS closeout ledger 是人工/AI 审阅材料，用于说明计划项、owner、证据缺口与并行 lane 状态；它不是机械质量 gate、测试 gate、submission gate 或 runtime authority。
