# AI-first Paper Autonomy Closure Program

Status: `active program`
Date: `2026-05-10`
Owner: `MedAutoScience`
Purpose: close the MAS loop for fully automated, high-quality medical manuscript progress after a study line is eligible for autonomous work.
Machine boundary: this is a human-readable program plan. Machine truth remains in `study_charter`, `paper/evidence_ledger.json`, `paper/review_ledger.json`, `artifacts/publication_eval/latest.json`, `artifacts/controller_decisions/latest.json`, `study_runtime_status`, `runtime_watch`, runtime supervision receipts, owner-route dispatch receipts, manuscript/package rebuild proof, and live study artifact refs.

## 结论

全自动推进高质量医学论文的卡点已经清晰：难点不是单纯“有没有 daemon / gateway / cron”，而是论文主循环是否能把研究方向、分析结果、AI reviewer 结论、稿件修复、gate replay、worker 恢复和转向止损压成同一条可执行、可重放、可审计的 owner route。

当前 MAS 没有丢掉旧 MDS / DeepScientist 的 skill-led stage discipline。旧 stage skill 仍按 workspace / quest-local `.codex/skills` 给 Codex CLI 使用；MAS 也把 scout、idea、baseline、experiment、analysis-campaign、write、review、decision/finalize 等阶段语义转译进 `agent_entry_modes.yaml`、study charter、bounded-analysis policy、route decision surface 和 owner-route dispatch。当前要补的是 execution closure：AI reviewer finding、负结果、稿件修复、gate replay 和 reviewer re-eval 必须形成默认执行链。

MAS 可以保证工程闭环：

- 每个非 human、非 terminal、非权限类 blocker 都进入 typed owner route。
- 每个 owner route 都有 callable surface、required inputs、required outputs、artifact delta predicate、gate replay target、idempotency key 和 source fingerprint。
- 每次执行后必须产出 owner receipt，并进入 artifact delta、gate replay、AI reviewer re-eval、bounded repair、switch line、stop-loss 或 human gate 之一。
- worker live、queue task、controller packet 或 gate audit 不能单独算论文进展；只有 manuscript/table/figure/result/package freshness、AI reviewer judgment、publication gate replay 后 owner 前进，才能算 meaningful paper progress。

MAS 不能承诺所有论文最终都发表级通过。医学研究存在真实数据限制、伦理/权限限制、外部验证缺失、样本量不足、统计不可辨识、目标期刊不匹配和作者客观信息缺失。MAS 的正确保证是：不能支持的结论自动降级、转向、停止或进入 human gate；系统不得为了“完成论文”伪造证据、隐藏负结果、扩大 claim 或用 mechanical gate 替代医学质量判断。

## 当前已有循环

### Runtime / Queue / Recovery

已落地能力：

- `Runtime Turn Lifecycle Kernel` 承接 runner completion、pending message、auto-continue、human/terminal gate 和 crash-recovery drain。
- `MAS supervision scheduler contract` 以默认 local LaunchAgent 外环定期触发 `watch-runtime -> supervisor-scan -> supervisor-consume -> supervisor-execute-dispatch`。
- per-run worker wrapper / watchdog 负责 worker lease、heartbeat、stdout cursor、child exit 和 low-latency normalization。
- `RuntimeHealthKernel`、`runtime_session`、`recovery_intent`、`runtime_reconcile_trigger`、`paper_progress_stall` 与 `autonomy_progress_slo_status` 把 no-live、stalled、retry exhausted、same fingerprint loop 和 safe reconcile 解释出来。
- OPL/Hermes family bridge 通过 MAS `sidecar export/dispatch` 消费 MAS 显式导出的 pending task；OPL/Hermes 负责 queue、dedupe、retry、dead-letter、approval 和 notification，MAS 仍持有 domain truth。

这部分解决“系统持续在线、任务可恢复、不会静默停住”。它本身不等于“科学方向和稿件质量已经自动过线”。

### Paper Progress / Owner Route

已落地能力：

- `Paper Progress SLO` 要求 `actual_write_active`、`package_delivered`、`meaningful_artifact_delta`、`next_owner` 和 `why_not_progressing` 同时可见。
- `owner_callable_registry` 注册 `MAS/controller`、`ai_reviewer`、`publication_gate`、`quality_repair_batch`、`gate_clearing_batch` 和 `delivery_sync` 等 owner。
- `runtime-supervisor-scan -> consume -> execute-dispatch -> rescan` 能把 AI reviewer、publication gate specificity、quality repair、gate clearing 和 delivery sync 转成 owner packet / default executor dispatch。
- `runtime-supervisor-reconcile --dry-run` 保持零 dispatch；`--apply` 只有在 fresh owner_route、未 parked/completed、无 hard human gate、无 publication gate missing、retry budget 可用、fingerprint 新鲜时才派发。

仍需闭合：每个 owner task 执行后必须推动稿件、分析或 AI reviewer judgment，而不是只生成 request packet 或刷新 read model。

### AI Reviewer / Quality

已落地能力：

- `AI-first Quality Boundary Policy` 明确 mechanical projection 不能授权 quality ready、finalize ready 或 submission-facing readiness。
- `ai_reviewer_publication_eval_workflow` 能 materialize AI reviewer-backed `artifacts/publication_eval/latest.json`，并附带 reviewer OS trace。
- `reviewer_refinement_loop` 能从 AI reviewer-backed publication eval 读出质量维度、publication gaps、same-line route-back、comment-to-action matrix、analysis/text repair requirement 和 recheck requirement。
- `ai_reviewer_calibration` 已把 claim overreach、mechanical gate as quality、missing reviewer trace、weak external validation、statistical discipline waiver misuse 这类返工原因沉淀成 calibration corpus / learning read model。

需要闭合：reviewer refinement 必须从 repair planning 变成默认 repair execution loop，并且修复后的 manuscript / analysis / evidence ledger / review ledger 必须自动触发 gate replay 和 AI reviewer re-eval。

### Analysis Direction / Negative Result

已落地能力：

- `study_line_decision_engine` 对候选方向按 novelty、clinical relevance、data fit、external validation、analysis feasibility、journal fit、risk/cost、stop threshold 打分。
- `route_decision_orchestrator` 把 route action 映射到 controller decision，并要求 candidate path graph 至少具备 question、evidence_basis、expected_artifact、stop_rule 和 decision。
- `route_decision_rehearsal` 覆盖 weak-result、blocked-statistics、missing-external-validation，并演练 continue、route_back、bounded_repair、stop_loss、switch_line、human_gate。
- `bounded_analysis_frontier_policy` 要求 accepted / rejected candidates、winning path、failed paths、evidence refs、reviewer concern closure status 和 next route。

需要闭合：弱结果或反常结果出现后，MAS 必须默认进入 claim downgrade、bounded repair、switch line、return_to_scout、stop-loss 或 human gate，不能继续把原 claim 写成 supported。

## Target Architecture

目标主循环：

1. **Study line intake / charter freeze**：冻结 clinical question、population、design、endpoint、data boundary、reporting guideline、journal fit、claim boundary、human gate boundary。
2. **Analysis direction controller**：维护 candidate board、expected evidence gain、stop rule、route decision 和 accepted/rejected path。
3. **First draft / evidence ledger closure**：只在 pre-draft readiness closed 后生成 manuscript-native medical prose，并维护 claim-evidence map、display-to-claim map、evidence ledger 和 review ledger。
4. **AI reviewer gate**：AI reviewer 读取 manuscript、study charter、evidence ledger、review ledger、publication gate projection 和 reporting contract，输出 reviewer-backed `publication_eval/latest.json`。
5. **Reviewer finding to repair execution**：每条 finding 映射成 `analysis_repair`、`text_repair`、`evidence_ledger_repair`、`review_ledger_repair`、`display_rebuild`、`package_refresh`、`claim_downgrade`、`route_decision` 或 `human_gate`。
6. **Replay and re-eval**：repair 完成后自动重放 publication gate、quality closure truth、paper progress SLO，并重新触发 AI reviewer re-eval。
7. **Stop / pivot discipline**：retry budget 或 evidence gain ceiling 用尽后，生成 stop-loss、claim downgrade、switch line 或 human gate request，保留负结果与失败路径。

## Landing Lanes

### Lane 1: Default AI Reviewer Executor Loop

- `return_to_ai_reviewer_workflow` 必须能默认调用 AI reviewer workflow 生成或刷新 AI reviewer-backed eval。
- 输入包括 manuscript、study charter、evidence ledger、review ledger、publication gate projection、reporting guideline 和 calibration refs。
- 输出是 `artifacts/publication_eval/latest.json`、reviewer OS trace、medical prose review 或明确 blocker。

### Lane 2: Reviewer Findings To Repair Work Units

- `reviewer_refinement_loop.comment_to_action_matrix` 必须进入 owner-route work-unit queue。
- `analysis_repair` 启动 bounded analysis campaign，并写回 evidence ledger / result refs。
- `text_repair` 修改 canonical manuscript source，并写 revision log / review ledger closure。
- 每个 repair 后必须触发 gate replay 和 AI reviewer recheck。

### Lane 3: Analysis Direction Autonomy

- 每个 analysis campaign slice 必须写 hypothesis、endpoint、method、expected result、failure criteria、result、interpretation 和 route impact。
- 弱结果或反常结果必须进入 claim downgrade、bounded repair、switch line、return_to_scout、stop-loss 或 human gate。
- 负结果进入 evidence ledger 和 failed path history，不能被后续写作隐藏。

### Lane 4: Manuscript Rewrite And Canonical Artifact Loop

- AI author / repair worker 从 review finding 和 evidence refs 生成 scoped patch。
- patch 必须更新 canonical source、evidence ledger、review ledger、revision log 和 rebuild proof。
- 每次 rewrite 后进入 publication gate replay 和 AI reviewer re-eval。

### Lane 5: Durable Queue, Notification, Recovery And Soak

- OPL/Hermes queue 只消费 MAS 导出的 typed pending tasks，不从只读 projection 推断医学动作。
- queue 支持 lease freshness、retry budget、dead-letter、approval pause、local inbox notification 和 dispatch receipt。
- MAS sidecar dispatch 回到 MAS owner surface 执行；Hermes/OPL 不写 study truth、quality truth、publication truth 或 package truth。
- DM002、DM003、Obesity 必须跑 end-to-end soak：queued -> dispatch -> repair/review/gate -> receipt -> notification -> progress delta 或 blocker。

### Lane 6: Medical Quality And Reporting Guard

- STROBE / TRIPOD / CONSORT / PRISMA / RECORD 等 reporting family 在 study charter 阶段选择。
- pre-draft readiness 覆盖 clinical question、population/design/outcome、data boundary、display-to-claim map、claim-evidence map、reader-flow plan 和 journal voice。
- deterministic gate 只阻断可验证缺口；主观质量只能由 AI reviewer-backed artifact 授权。

## Acceptance Criteria

### Repo-Level Loop Test

给定一个 fixture study，其中 manuscript 有 AI reviewer blocking finding，MAS 必须能完成：

1. publication eval 标记 AI reviewer blocker；
2. supervisor scan 产生 owner_route；
3. consume 生成 dispatch request；
4. execute-dispatch 调用正确 owner surface；
5. 生成 analysis/text repair work unit；
6. repair 写入 canonical artifact delta；
7. publication gate replay；
8. AI reviewer re-eval；
9. progress 显示 pass、bounded blocker、switch line、stop-loss 或 human gate。

### Negative-Result Route Test

给定一个分析结果弱于预期或和原 claim 相反的 fixture，MAS 必须自动产生：

- failed path evidence refs；
- claim downgrade / bounded repair / switch line / stop-loss 之一；
- controller decision；
- downstream manuscript / evidence ledger 修复要求；
- 不允许继续把原 claim 写成 supported。

### Real-Paper Soak

DM002、DM003、Obesity 的 read-only/live verification 必须展示：

- 当前 state 是 running、parked、breach、blocked、human gate 或 terminal；
- `why_not_progressing` 指向 owner route、quality repair、worker recovery、safe reconcile、publication gate、human gate 或 scientific/data stop；
- 最近一个自动动作产生 artifact delta、gate replay、AI reviewer judgment、repair receipt，或稳定 blocker；
- 无 `owner_callable_surface_missing` 的非 human AI reviewer route；
- `meaningful_artifact_delta=true` 只在真实 manuscript/table/figure/result/package freshness/gate owner progress 后出现。

## Product Wording

对外只能承诺：

- MAS 会持续推进所有符合自治条件的医学论文 work unit；
- MAS 会自动修复、复评、转向或止损；
- MAS 会在需要 human gate、权限、作者信息、伦理/投稿授权或科学不可支持时显式停下。

不得承诺：

- 所有数据集都能产出发表级结论；
- AI reviewer 或 publication gate 可以被 mechanical projection 替代；
- worker live 等于论文已取得有效进展。

## Verification Plan

- focused tests：AI reviewer workflow dispatch、reviewer refinement repair queue、route decision negative-result handling、manuscript rewrite/gate replay、paper progress SLO、owner callable registry。
- runtime tests：runtime supervisor scan / consume / execute-dispatch / reconcile、worker lease、retry budget、idempotency、dead-letter、sidecar export/dispatch。
- docs/contract tests：`make test-meta` 只检查 machine-readable contracts，不固定叙述性 wording。
- real workspace verification：DM002、DM003、Obesity 只读读取 `runtime_supervision/latest.json`、`slo_status/latest.json`、`controller_decisions/latest.json`、`publication_eval/latest.json`、paper progress projection 和 sidecar export。

最终完成信号不是文档一致，而是真实论文线能持续产生可验证论文增量，或清楚进入转向、止损、human gate。
