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

## AI-first handoff 扩展字段

AI-first closeout/handoff lane 使用以下扩展字段记录人工/AI 接力状态。这些字段服务审阅和续接，不新增 wording gate、publication gate、submission gate 或 runtime authority。

| 字段 | 含义 |
| --- | --- |
| `handoff_receiver` | 下一接手者、外部 active owner 或 `none`。 |
| `handoff_entrypoint` | 下一次继续时读取的文档、surface、branch、PR 或命令。 |
| `out_of_scope_boundaries` | 本轮明确不触碰的 live artifact、worktree、risk 或 soak 边界。 |

`external_active_owner` 表示某项由本轮以外的活跃对话、worktree、branch 或上游 PR 持有。它不得被写成 `done`，当前 lane 也不得吸收、重写或清理该 owner 持有的 worktree/branch。

worktree cleanup 只允许覆盖本轮新建并完成吸收的 worktree/branch。外部活跃 worktree、`risk-*` 独立线、等待上游 review 的 PR worktree、用户明确排除的 worktree，以及状态无法确认的 worktree 都必须保留并标 owner。

## AI-first closeout/handoff 记录模板

| plan_id | planned_items | landed_commits | tests_run | pushed | worktrees_cleaned | live_surface_verified | skipped_with_user_acceptance | remaining_gaps | handoff_receiver | handoff_entrypoint | out_of_scope_boundaries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| template | item A; item B | none | none: not run yet | no | not_performed_by_request | none | none | none | external_active_owner or none | docs/program/... | DM002 live artifact; risk-*; real-paper soak; external worktrees |

## 当前计划记录

| plan_id | planned_items | landed_commits | tests_run | pushed | worktrees_cleaned | live_surface_verified | skipped_with_user_acceptance | remaining_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-03-ai-first-nonconflict-governance | action dispatch ledger; external lane registry; cross-study completion projection; quality learning queue; closeout/handoff governance; protect DM002/risk/external worktrees from this lane | absorbed on `main` and pushed to `origin/main`: `c4b80bc Merge AI-first action dispatch ledger`, `a705a16 Merge AI-first external lane registry`, `4c547bd Merge AI-first cross-study completion projection`, `0f98356 Merge AI-first quality learning queue`, `77e593f Merge AI-first closeout handoff governance` | focused AI-first tests: `31 passed`; `make test-meta`: `209 passed, 2455 deselected`; `scripts/verify.sh`: `1971 passed, 693 deselected`; `git diff --check` | yes: pushed to `origin/main` | yes for this lane: removed `codex/ai-first-action-dispatch-ledger`, `codex/ai-first-external-lane-registry`, `codex/ai-first-cross-study-completion`, `codex/ai-first-quality-learning-queue`, and `codex/ai-first-closeout-handoff-governance`; external active worktrees intentionally preserved | repo-level synthetic/focused surfaces verified for action dispatch lifecycle, external lane cleanup protection, cross-study completion, quality learning queue, and closeout handoff governance; no DM002 live artifact was read or modified for this lane | none | DM002 live study, `risk-*`, real-paper soak, and existing external worktrees remain out of scope; this row records operations/governance readiness, not final manuscript quality improvement |
| 2026-05-01-mas-mds-history-plan-closeout | completion ledger; parked telemetry closeout; study_progress SLO projection; parked/liveness consistency; manual_finishing visible-state normalization; live-regression fixtures | MAS `f660567 fix: close plan completion runtime surfaces`, `d7734fa docs: record plan closeout live verification`; MDS `3c1a7ba fix: backfill parked closeout telemetry` | MAS targeted progress/runtime/operator tests; MAS `make test-meta`; MAS `scripts/verify.sh`; MDS parked closeout targeted tests; MDS `scripts/verify.sh` | yes: MAS main and MDS main pushed | yes: removed `codex/mas-closeout-live-surfaces` and `codex/mds-parked-telemetry-closeout`; external worktrees left untouched | DM-CVD 002/003 reread 2026-05-01: `autonomy_slo_status_path` materialized for both; SLO observer generated `same_fingerprint_loop` AI Doctor requests; 003 projects `auto_runtime_parked / explicit_resume_pending` with no supervision active run after completed parked run; 002 has no active run and SLO breach visible | none | live daemon process predates the MDS telemetry-backfill commit, and completed parked runs still lack `telemetry.json` until a safe daemon restart or next patched audit; do not stop active study infrastructure just to backfill history |
| 2026-05-02-ai-first-operationalization-closeout | 将近期 AI-first Research OS 规划收口成可审阅实施台账；区分已经存在的 repo-level contract/read model；收口 pre-draft runtime、AI reviewer workflow、artifact proof、operations state 四条落地 lane；明确真实论文 soak 是剩余证据缺口；固定本 ledger 是人工/AI 审阅材料，不是机械 gate | absorbed on `main` and pushed to `origin/main`: `8ddb1b2 Merge pre-draft quality runtime`, `b162f72 Merge AI reviewer workflow state`, `010ac56 Merge artifact runtime proof`, `d50a41b Merge AI-first operations runtime state`, `250cc29 Merge AI-first closeout ledger`, plus post-merge default-entry closeout on `main`: `ebc2074 Merge AI-first default entry flow`, `aa333ed Merge AI-first operations default projection`, `e739217 Merge AI-first postmerge closeout ledger` | lane closeout verification recorded as repo-native tests plus doc hygiene; post-merge default-entry closeout verified by focused study-progress/product-entry tests, `make test-meta`, `scripts/verify.sh`, and `git diff --check` | yes: implementation closeout and post-merge default-entry closeout are pushed to `origin/main` | yes for the implementation and post-merge default-entry lanes: `codex/predraft-quality-runtime`, `codex/ai-reviewer-workflow`, `codex/artifact-runtime-proof`, `codex/operations-runtime-state`, `codex/ai-first-default-entry-flow`, `codex/ai-first-operations-default-projection`, and `codex/ai-first-postmerge-closeout-ledger` worktrees/branches are no longer present; unrelated active worktrees remain owned by their lanes | 2026-05-02 tracked docs and default entry surfaces now expose the repo-level state for `StudyTruthKernel`, `RuntimeHealthKernel`, AI-first quality boundary, first-draft quality policy, pre-draft readiness, AI reviewer workflow, canonical artifact proof, AI-first observability/operations dashboard, `study_progress`, `workspace_cockpit`, and `product_frontdesk`;详见 `docs/program/ai_first_operationalization_closeout.md` | none | 真实论文 soak 仍是诚实剩余缺口：至少一条 live manuscript 需要同时证明 pre-draft readiness、AI reviewer-backed publication eval、canonical artifact rebuild proof、operations-state projection，以及 study-progress/product-frontdesk truth 一致；本 ledger 不认证该 soak 已完成，也不宣称真实论文质量改善已被证明 |
| 2026-05-02-ai-first-runtime-feedback-loop | AI-first 运行数据反馈闭环；feedback kernel；feedback ledger open/close/repeat；study_progress feedback state；workspace_cockpit/product_frontdesk 共享 feedback projection；operations metrics；明确 feedback 只做 observability，不做 quality/submission authority；排除真实论文 soak 与 `risk-*` 独立线 | absorbed on `main`: `f4f39c1 Merge AI-first runtime feedback loop`, implementation commit `6e1b5c7 Add AI-first runtime feedback loop` | targeted feedback/study-progress/product-entry tests; `make test-meta`; `scripts/verify.sh`; `git diff --check` | yes: pushed to `origin/main` | yes: removed `codex/ai-first-feedback-kernel`; `risk-*` worktrees/branches intentionally untouched and owned by other conversations | repo-level runtime feedback surfaces verified: `ai_first_feedback_state`, `ai_first_feedback_ledger`, `study_progress`, `workspace_cockpit`, `product_frontdesk`, and product-entry manifest payload all project observability-only feedback status | none | 真实论文 soak 仍未作为本轮完成项；feedback ledger 只能证明 repo-level feedback loop 可运行，不能证明真实论文质量改善 |
| 2026-05-02-dm002-feedback-action-loop | DM-CVD 002 作为 active study/live observation anchor；DM002 最小脱敏 observation fixture；feedback category -> action recommendation kernel；repeat-toil analytics by category/reason/source/open-closed；study_progress/workspace_cockpit/product_frontdesk 投影 primary action；保持 feedback/action/analytics `observability_only`，不得授权 quality/finalize/submission；排除真实论文 soak、`risk-*` 独立线和 display/gate-clearing 侧线 | absorbed on `main`: `70208b3 Merge AI-first feedback action kernel`, `6261a37 Add DM002 AI-first feedback observation fixture`, `48661f1 Merge AI-first repeat toil analytics`, `93cc17e Project AI-first feedback actions into entry surfaces`; non-scope display/gate-clearing local merges were reverted by `907022c` and `a6e4d97` and preserved on `codex/preserve-*` branches | targeted feedback/study-progress/product-entry tests; `make test-meta`; `scripts/verify.sh`; `git diff --check`; live DM002 projection check via stable MAS surface | yes: pushed to `origin/main` after verification | yes: removed `codex/dm002-feedback-observation-baseline`, `codex/feedback-to-action-kernel`, `codex/repeat-toil-analytics`, and `codex/dm002-feedback-entry-integration`; `codex/risk-preflight-hardening` and `codex/preserve-*` branches intentionally left untouched as external/non-scope lines | DM-CVD 002 read-only/controller-owned projection verified: feedback state can answer primary feedback, next action, human review need, artifact pending and repeat-toil signal without becoming quality authority | none | 真实论文 soak 仍未作为本轮完成项；DM002 observation fixture proves safe live-observation wiring, not final paper quality improvement |
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
