# AI-first Paper Autonomy Closure Program

Status: `active program`
Date: `2026-05-10`
Owner: `MedAutoScience`
Purpose: close the MAS loop for fully automated, high-quality medical manuscript progress after a study line is eligible for autonomous work.
Machine boundary: this is a human-readable program plan. Machine truth remains in `study_charter`, `paper/evidence_ledger.json`, `paper/review_ledger.json`, `artifacts/publication_eval/latest.json`, `artifacts/controller_decisions/latest.json`, `study_runtime_status`, `runtime_watch`, runtime supervision receipts, owner-route dispatch receipts, manuscript/package rebuild proof, and live study artifact refs.

## 结论

全自动推进高质量医学论文的卡点逻辑已经清晰：难点不是单纯“有没有 daemon / gateway / cron”，而是论文主循环是否能把研究方向、分析结果、AI reviewer 结论、稿件修复、gate replay、worker 恢复和转向止损都压成同一条可执行、可重放、可审计的 owner route。

当前 MAS 已经保留并转译了 MDS / DeepScientist 的 skill-led stage discipline：`agent_entry_modes.yaml` 中的 scout、idea、baseline、experiment、analysis-campaign、write、review、decision/finalize 等 route contract，已经把进入条件、hard success gate、durable outputs、human gate boundary、next route 和 route-back triggers 写成 MAS 可消费的合同；`study_charter.paper_quality_contract.stage_expectations`、bounded-analysis policy、route decision surface 和 owner-route dispatch 继续承接这些纪律。也就是说，问题不是 skill-led 逻辑“没有了”。

当前 MAS 同时已经有可运行的外环监管、owner route、AI reviewer provenance、publication gate、quality repair、gate clearing、paper progress SLO、sidecar queue bridge 和 bounded-analysis / route-decision read model。它已经能解释很多停滞原因，也能派发部分可执行修复。但还不能把“初稿 -> AI reviewer/gate -> 自动分析或改稿 -> 复评 -> 继续循环直到通过或明确转向/止损”诚实写成完整闭环。缺口集中在三处：

1. AI reviewer 评审结果到 manuscript / analysis repair work unit 的自动执行闭环还不够完整。
2. 分析结果不符合预期时，候选方向、claim 降级、bounded repair、switch line、stop-loss 的决策面已有结构，但还没有成为默认可执行研究控制循环。
3. 真实 paper soak 的验收还没有把 DM002、DM003、Obesity 这类案例固定为端到端回归：必须看到 artifact delta、gate replay、reviewer re-eval 或明确的 terminal blocker，而不是只看到 worker live 或 queue 有任务。

本 program 的最高目标是把 MAS 从“能监管和解释论文停滞”推进到“能默认持续推进方向锁定后的医学论文，直到进入 human gate、科学/数据止损、或达到 AI reviewer-backed submission-facing quality closure”。

## 保证边界

MAS 可以并且应该保证工程闭环：

- 每个非 human、非 terminal、非权限类 blocker 都进入 typed owner route。
- 每个 owner route 都有 callable surface、required inputs、required outputs、artifact delta predicate、gate replay target、idempotency key 和 source fingerprint。
- 每次执行后必须产出 owner receipt，并进入 artifact delta、gate replay、AI reviewer re-eval、bounded repair、switch line、stop-loss 或 human gate 之一。
- 任何 live worker、queue task、controller packet 或 gate audit 都不能单独算论文进展；只有 manuscript/table/figure/result/package freshness、AI reviewer judgment、publication gate replay 后 owner 前进，才能算 meaningful paper progress。

MAS 不能承诺所有论文最终都一定发表级通过。医学研究存在真实数据限制、伦理/权限限制、外部验证缺失、样本量不足、统计不可辨识、目标期刊不匹配和作者客观信息缺失。MAS 的正确保证是：不能支持的结论自动降级、转向、停止或进入 human gate；系统不得为了“完成论文”伪造证据、隐藏负结果、扩大 claim 或用机械 gate 替代医学质量判断。

## 当前 MAS 已有循环

### Runtime / queue / recovery loop

已落地的运行闭环包括：

- `Runtime Turn Lifecycle Kernel` 承接 runner completion、pending message、auto-continue、human/terminal gate 和 crash-recovery drain。
- `MAS supervision scheduler contract` 以默认 local LaunchAgent 外环定期触发 `watch-runtime -> supervisor-scan -> supervisor-consume -> supervisor-execute-dispatch`。
- per-run worker wrapper / watchdog 负责 worker lease、heartbeat、stdout cursor、child exit 和 low-latency normalization。
- `RuntimeHealthKernel`、`runtime_session`、`recovery_intent`、`runtime_reconcile_trigger`、`paper_progress_stall` 与 `autonomy_progress_slo_status` 把 no-live、stalled、retry exhausted、same fingerprint loop 和 safe reconcile 解释出来。
- OPL/Hermes family bridge 现在通过 MAS `sidecar export/dispatch` 消费 MAS 显式导出的 pending task；OPL/Hermes 负责 queue、dedupe、retry、dead-letter、approval 和 notification，MAS 仍持有 domain truth。

这部分已经接近工程闭环，但它解决的是“系统持续在线、任务可恢复、不会静默停住”。它本身不等于“科学方向和稿件质量已经自动过线”。

### Paper progress / owner-route loop

已落地的论文推进 guard 包括：

- `Paper Progress SLO` 要求 `actual_write_active`、`package_delivered`、`meaningful_artifact_delta`、`next_owner` 和 `why_not_progressing` 同时可见。
- `owner_callable_registry` 注册 `MAS/controller`、`ai_reviewer`、`publication_gate`、`quality_repair_batch`、`gate_clearing_batch` 和 `delivery_sync` 等 owner。
- `runtime-supervisor-scan -> consume -> execute-dispatch -> rescan` 能把 `return_to_ai_reviewer_workflow`、publication gate specificity、quality repair、gate clearing 和 delivery sync 这类 action 转成 owner packet / default executor dispatch。
- `runtime-supervisor-reconcile --dry-run` 保持零 dispatch；`--apply` 只有在 fresh owner_route、未 parked/completed、无 hard human gate、无 publication gate missing、retry budget 可用、fingerprint 新鲜时才派发。

这部分已经把“忙但没有论文产物增量”的问题显性化。仍需补齐的是：每个 owner task 执行后必须推动稿件、分析或 AI reviewer judgment，而不是只生成 request packet 或刷新 read model。

### AI reviewer / quality loop

已落地的质量边界包括：

- `AI-first Quality Boundary Policy` 明确 mechanical projection 不能授权 quality ready、finalize ready 或 submission-facing readiness。
- `ai_reviewer_publication_eval_workflow` 能把 AI reviewer-backed record materialize 到 `artifacts/publication_eval/latest.json`，并附带 reviewer OS trace。
- `ai_reviewer_runtime_workflow_state` 能 fail-closed 检查 publication eval、medical prose review、review ledger 和 evidence ledger 是否关闭。
- `reviewer_refinement_loop` 能从 AI reviewer-backed publication eval 读出质量维度、publication gaps、same-line route-back、comment-to-action matrix、analysis/text repair requirement 和 recheck requirement。
- `ai_reviewer_calibration` 已把 claim overreach、mechanical gate as quality、missing reviewer trace、weak external validation、statistical discipline waiver misuse 这类返工原因沉淀成 calibration corpus / learning read model。

这部分已经把“质量谁说了算”守住了。当前主要缺口是：reviewer refinement 仍偏 read-model / repair-planning，必须进一步成为默认 repair execution loop，并且修复后的 manuscript / analysis / evidence ledger / review ledger 必须自动触发 AI reviewer re-eval。

### Analysis direction / negative-result loop

已落地的方向与负结果 surface 包括：

- `study_line_decision_engine` 对候选方向按 novelty、clinical relevance、data fit、external validation、analysis feasibility、journal fit、risk/cost、stop threshold 打分，并给出 `proceed_to_baseline`、`return_to_scout`、`switch_line`、`human_gate`。
- `route_decision_orchestrator` 把 route action 映射到 controller decision，并要求 candidate path graph 至少具备 question、evidence_basis、expected_artifact、stop_rule 和 decision。
- `route_decision_rehearsal` 覆盖 `weak-result`、`blocked-statistics`、`missing-external-validation`，并演练 `continue`、`route_back`、`bounded_repair`、`stop_loss`、`switch_line`、`human_gate`。
- `bounded_analysis_frontier_policy` 明确 explore / exploit / fusion / debug / stop，要求 accepted / rejected candidates、winning path、failed paths、evidence refs、reviewer concern closure status 和 next route。

这部分已经有很好的结构基础。当前未闭合点是：这些 route/decision/read-model 尚未成为每个异常分析结果后的默认自动控制器。也就是说，MAS 已经知道“弱结果应该怎么表达”，但还需要把“弱结果出现后自动降级 claim、补一个 bounded repair、切换候选方向、或止损”的执行链路固定下来。

## DeepScientist 自动化逻辑现状

上游 DeepScientist 的核心价值不在于它有一个巨大 daemon stage engine。当前 DeepScientist 更像 prompt-led、skill-led、file-led quest runtime：

- daemon 负责常驻、API、connector、session store、turn queue、runner lifecycle、crash auto-resume、terminal attach 和 delivery。
- prompt builder 每 turn 注入 runtime context、quest files、recent durable state、startup contract、paper/evidence snapshot 和 active skill。
- skill 文件定义 stage discipline：analysis campaign、decision、optimize、review 等真正决定研究推进方式。
- durable state 存在 quest files、artifacts、memory、Git / lineage、run logs；UI Canvas 从 durable artifacts 和 runtime events 重建。
- daemon 本身并不是严格 stage-transition engine；非线性研究路线由 skill discipline + durable decision artifacts 支撑。

这些纪律在 MAS 里不是空白。当前已经转译到以下 surface：

- `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`：保存 route contract、stage success gate、durable output、human gate 和 route-back trigger。
- `study_charter.paper_quality_contract.stage_expectations`：把 stage discipline 挂进医学研究合同。
- `docs/policies/study-workflow/bounded_analysis_frontier_policy.md`：把 analysis-campaign / optimize 的 candidate board、negative result visibility、stop / route-back 纪律医学化。
- `study_line_decision_engine` 与 `route_decision_orchestrator`：把候选方向评分、route decision、candidate path graph 和 stop-rule 结构化。
- `owner_callable_registry` 与 owner route：把部分 route action 绑定到 MAS callable surface。

因此，下一步不是重新引入 skill-led 逻辑，而是把这些已经存在的纪律闭合成默认执行链。仍需补齐的自动化纪律包括：

- 每个 analysis campaign 先有 plan/checklist，再有 slice、aggregate report、negative result visibility 和 route decision。
- 每次非平凡继续都写 durable decision，包含 verdict、action、reason、evidence paths 和 next route。
- 优化/方向探索维护 candidate board，不把所有想法都推进，只 promotion 最有价值的少数路线。
- review 像严格审稿人一样把 claim、evidence、novelty、rigor、clarity 和 likely rejection reason 转成 revision plan 或 experiment TODO。
- 负结果不能埋掉；它们必须进入 claim downgrade、bounded repair、switch line、stop-loss 或 human gate。

MAS 应把这些纪律落到医学 domain truth：`study_charter`、`evidence_ledger`、`review_ledger`、`publication_eval/latest.json`、`controller_decisions/latest.json`、owner-route dispatch receipt 和 manuscript/package rebuild proof，而不是恢复旧 MDS 的 GitOps / workspace-local service / WebUI daemon 作为第二 authority。

## 是否存在降级

按当前 MDS behavior equivalence matrix，MAS 没有在“阶段纪律 / skill-led research protocol”这一层降级；这部分已经被 MAS-owned route contract、quality OS、owner route 和 tests 承接，并且医学领域约束比原始 DeepScientist 更强。

存在差异或降级风险的是 runtime/product behavior 层：

- 旧 MDS resident daemon 的 WebSocket terminal attach、connector background delivery、in-memory session continuity、GitOps runtime lifecycle 和 workspace-local host service 没有作为 MAS 默认能力 1:1 保留。
- MAS 的正常 turn completion continuation 已由 Runtime Turn Lifecycle Kernel 接住，不再等 300 秒 cron；但 crash/stale recovery 和 outer supervision 仍是 scheduler-bound，默认 300 秒 fail-safe tick。
- Progress Portal / Live Console 已提供 MAS-owned read-only/pause-resume-stop surface，但多论文 workspace UX、interactive terminal attach 和 connector delivery 仍不是完整等价旧 MDS WebUI / daemon。
- 对论文自动产出而言，P0 降级风险不在“skill-led 没了”，而在 owner handoff、repeat suppression、work-unit redrive、reviewer finding -> repair execution、negative result -> route decision 是否闭合。

因此，本 program 要修的是 execution closure，不是从零恢复 DeepScientist skill-led 体系。

## 外部成熟工程经验

成熟 agent / workflow 系统的共同点不是“一个无限 while loop”，而是 durable execution + typed state + recovery + human-in-loop + observability：

- LangGraph 强调 durable execution、checkpoint / persistence、human-in-the-loop 和 long-term memory。对应到 MAS：每个 paper loop step 都要有 checkpoint、state snapshot、interrupt / approval gate 与恢复点。
- Temporal 把 workflow state、activity retry、timeout、heartbeat 和 failure detection 做成 first-class contract。对应到 MAS：长时间分析、写作和 gate replay 必须有 worker heartbeat、retry budget、idempotency、dead-letter 和 activity-level receipt。
- OpenAI background mode 把长任务变成可查询状态和可异步完成的 run。对应到 MAS：Codex runner 只是执行器，MAS 必须持有 run status、receipt、artifact delta 与 next owner。
- Pydantic AI durable execution、AutoGen state save/load、CrewAI flow persistence、Cloudflare long-running agents 都强调保存 agent state、恢复上下文、按事件继续，而不是依赖单次 chat 记忆。对应到 MAS：不能靠一次 prompt 记住论文进度，必须靠 durable ledgers 和 typed queue。
- 医学论文质量方面，ICMJE、EQUATOR、STROBE、TRIPOD 这类规范要求研究类型、设计、变量、偏倚、统计、验证、局限性和透明报告前置进入 manuscript contract。对应到 MAS：reporting guideline、claim-evidence map、display-to-claim map 和 limitation boundary 必须进入 pre-draft / charter，而不是投稿包阶段机械补救。

工程结论：OPL/Hermes gateway 能提升 24h 在线、跨仓派发、通知、队列和恢复；但医学论文能否高质量自动推进，取决于 MAS 内部是否把 science/writing/review route 做成 durable workflow。gateway 只能唤醒和派发，不能替 MAS 做医学质量判断。

参考来源：

- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 与 [human-in-the-loop interrupts](https://docs.langchain.com/oss/python/langgraph/human-in-the-loop)
- [Temporal documentation](https://docs.temporal.io/) 与 [Temporal Python failure detection](https://docs.temporal.io/develop/python/failure-detection)
- [OpenAI background mode](https://platform.openai.com/docs/guides/background)
- [Pydantic AI durable execution overview](https://pydantic.dev/docs/ai/integrations/durable_execution/overview/)
- [AutoGen managing state](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html)
- [CrewAI production architecture](https://docs.crewai.com/en/concepts/production-architecture)
- [Cloudflare long-running agents](https://developers.cloudflare.com/agents/concepts/long-running-agents/) 与 [durable execution](https://developers.cloudflare.com/agents/api-reference/durable-execution/)
- [ICMJE manuscript preparation](https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html)、[EQUATOR reporting guidelines](https://www.equator-network.org/reporting-guidelines/)、[STROBE](https://www.strobe-statement.org/) 与 [TRIPOD](https://www.tripod-statement.org/scope/)

## Target Architecture

目标主循环如下：

1. **Study line intake / charter freeze**
   - 冻结 clinical question、population、design、endpoint、data boundary、reporting guideline、journal fit、claim boundary、human gate boundary。
   - 输出 `study_charter.paper_quality_contract` 与初始 candidate board。
2. **Analysis direction controller**
   - 为每条候选方向维护 candidate board、expected evidence gain、stop rule、route decision 和 accepted/rejected path。
   - baseline / bounded analysis 结果出现后立即决定 continue、bounded_repair、claim_downgrade、switch_line、return_to_scout、stop_loss 或 human_gate。
3. **First draft / evidence ledger closure**
   - 只在 pre-draft readiness closed 后生成 manuscript-native medical prose。
   - 写作同时维护 claim-evidence map、display-to-claim map、evidence ledger 和 review ledger。
4. **AI reviewer gate**
   - AI reviewer 读取 manuscript、study charter、evidence ledger、review ledger、publication gate projection 和 reporting contract。
   - 输出 AI reviewer-backed `publication_eval/latest.json`、medical prose review、quality dimension status、gaps、route-back decision 和 reviewer OS trace。
5. **Reviewer finding to repair execution**
   - 把每条 reviewer finding 映射成 `analysis_repair`、`text_repair`、`evidence_ledger_repair`、`review_ledger_repair`、`display_rebuild`、`package_refresh`、`claim_downgrade`、`route_decision` 或 `human_gate`。
   - 每个 repair work unit 都有 owner、callable surface、required inputs/outputs、artifact delta predicate、gate replay target、retry budget 和 idempotency key。
6. **Replay and re-eval**
   - repair 完成后自动重放 publication gate、quality closure truth、paper progress SLO，并重新触发 AI reviewer re-eval。
   - 通过则进入 finalize / submission-facing package；未通过则继续有界循环。
7. **Stop / pivot discipline**
   - retry budget 或 evidence gain ceiling 用尽后，不继续包装同一问题。
   - 自动生成 stop-loss、claim downgrade、switch line 或 human gate request，保留负结果与失败路径。

## Parallel Landing Lanes

本 program 可以并行落地，但必须共享同一 paper loop contract 和真实 paper soak 验收。

### Lane 1: Default AI reviewer executor loop

目标：让 `return_to_ai_reviewer_workflow` 成为默认可执行 AI reviewer route，而不是停在 request packet。

落地要求：

- 若 publication eval 缺 AI reviewer provenance，supervisor dispatch 必须能调用 AI reviewer workflow 生成或刷新 AI reviewer-backed eval。
- 输入必须包括 manuscript、study charter、evidence ledger、review ledger、publication gate projection、reporting guideline 和 calibration refs。
- 输出必须是 `artifacts/publication_eval/latest.json`、reviewer OS trace、medical prose review 或明确 blocker。
- 非 human、非权限类缺口不能投影成 `waiting_for_user`。

### Lane 2: Reviewer findings to repair work units

目标：把 AI reviewer finding 自动转成可执行修复单元。

落地要求：

- `reviewer_refinement_loop.comment_to_action_matrix` 不只做 read model，还要进入 owner-route work-unit queue。
- `analysis_repair` 必须能启动 bounded analysis campaign，并写回 evidence ledger / result refs。
- `text_repair` 必须能修改 canonical manuscript source，并写 revision log / review ledger closure。
- 每个 repair 后必须触发 gate replay 和 AI reviewer recheck。

### Lane 3: Analysis direction autonomy

目标：把异常分析结果、负结果和不符合预期的结果变成默认 route-decision 循环。

落地要求：

- 每个 analysis campaign slice 必须写 hypothesis、endpoint、method、expected result、failure criteria、result、interpretation 和 route impact。
- 弱结果或反常结果必须自动进入 claim downgrade、bounded repair、switch line、return to scout、stop-loss 或 human gate。
- `study_line_decision_engine`、`route_decision_orchestrator` 和 `bounded_analysis_frontier_policy` 升级为 executable workflow，不停留在 materializer / read-model。
- 负结果必须进入 evidence ledger 和 failed path history，不能被后续写作隐藏。

### Lane 4: Manuscript rewrite and canonical artifact loop

目标：让稿件修复真正修改 canonical manuscript / tables / figures / legends / package source，而不是只刷新状态。

落地要求：

- AI author / repair worker 从 review finding 和 evidence refs 生成 scoped patch。
- patch 必须更新 canonical source、evidence ledger、review ledger、revision log 和 rebuild proof。
- manuscript-native prose gate 前置运行，防止 controller prose、package anchors、author TODO 或 reviewer-facing labels 进入正文。
- 每次 rewrite 后必须进入 publication gate replay 和 AI reviewer re-eval。

### Lane 5: Durable queue, notification, recovery and soak

目标：把 gateway 在线能力用于持续推进，而不是只做状态轮询。

落地要求：

- OPL/Hermes queue 只消费 MAS 导出的 typed pending tasks，不从只读 projection 推断医学动作。
- queue 支持 lease freshness、retry budget、dead-letter、approval pause、local inbox notification 和 dispatch receipt。
- MAS sidecar dispatch 回到 MAS owner surface 执行；Hermes/OPL 不写 study truth、quality truth、publication truth 或 package truth。
- DM002、DM003、Obesity 必须跑 end-to-end soak：queued -> dispatch -> repair/review/gate -> receipt -> notification -> progress delta 或 blocker。

### Lane 6: Medical quality and reporting guard

目标：把医学质量要求前置到研究与写作合同，而不是后置补救。

落地要求：

- STROBE / TRIPOD / CONSORT / PRISMA / RECORD 等 reporting family 在 study charter 阶段选择。
- pre-draft readiness 必须覆盖 clinical question、population/design/outcome、data boundary、display-to-claim map、claim-evidence map、reader-flow plan 和 journal voice。
- AI reviewer rubric 必须检查 novelty、clinical relevance、methods rigor、statistics, claim restraint、limitations、reporting hygiene、figures/tables 和 submission readiness。
- deterministic gate 只阻断可验证缺口；主观质量只能由 AI reviewer-backed artifact 授权。

## Acceptance Criteria

### Repo-level loop test

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

### Negative-result route test

给定一个分析结果弱于预期或和原 claim 相反的 fixture，MAS 必须自动产生：

- failed path evidence refs；
- claim downgrade / bounded repair / switch line / stop-loss 之一；
- controller decision；
- downstream manuscript / evidence ledger 修复要求；
- 不允许继续把原 claim 写成 supported。

### Real-paper soak

DM002、DM003、Obesity 的 read-only/live verification 必须展示：

- 当前 state 是 running、parked、breach、blocked、human gate 或 terminal；
- `why_not_progressing` 指向 owner route、quality repair、worker recovery、safe reconcile、publication gate、human gate 或 scientific/data stop；
- 最近一个自动动作产生 artifact delta、gate replay、AI reviewer judgment、repair receipt，或稳定 blocker；
- 无 `owner_callable_surface_missing` 的非 human AI reviewer route；
- `meaningful_artifact_delta=true` 只在真实 manuscript/table/figure/result/package freshness/gate owner progress 后出现。

### Product guarantee wording

对外只能承诺：

- MAS 会持续推进所有符合自治条件的医学论文 work unit；
- MAS 会自动修复、复评、转向或止损；
- MAS 会在需要 human gate、权限、作者信息、伦理/投稿授权或科学不可支持时显式停下。

不得承诺：

- 所有数据集都能产出发表级结论；
- AI reviewer 或 publication gate 可以被 mechanical projection 替代；
- worker live 等于论文已取得有效进展。

## Verification Plan

最小验证分层：

- focused tests：AI reviewer workflow dispatch、reviewer refinement repair queue、route decision negative-result handling、manuscript rewrite/gate replay、paper progress SLO、owner callable registry。
- runtime tests：runtime supervisor scan / consume / execute-dispatch / reconcile、worker lease、retry budget、idempotency、dead-letter、sidecar export/dispatch。
- docs/contract tests：`make test-meta` 只检查 machine-readable contracts，不固定叙述性 wording。
- real workspace verification：DM002、DM003、Obesity 只读读取 `runtime_supervision/latest.json`、`slo_status/latest.json`、`controller_decisions/latest.json`、`publication_eval/latest.json`、paper progress projection 和 sidecar export。
- soak：临时 `OPL_STATE_DIR` + Hermes test profile，enqueue 三类 MAS tasks，验证 wakeup、dispatch、receipt、notification、retry/dead-letter、approve/pause 和 gateway restart recovery。

## Risks

- 如果只加强 gateway / daemon 而不关闭 science-writing-review loop，系统会更稳定地空转。
- 如果只加强 AI reviewer 而没有 repair executor，系统会更准确地指出问题，但论文仍不能自动前进。
- 如果只加强 manuscript rewrite 而没有 negative-result route，系统会把弱证据包装成更漂亮的过度 claim。
- 如果只加强 deterministic gate，系统会回到 mechanical quality drift。
- 如果真实 paper soak 不作为验收，repo-level tests 会掩盖 DM002、DM003、Obesity 暴露的长跑缺口。

本 program 的落地顺序可以并行，但验收必须端到端。最终完成信号不是文档一致，而是真实论文线能持续产生可验证论文增量，或清楚进入转向、止损、human gate。
