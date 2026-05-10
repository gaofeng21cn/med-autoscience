# AI-first Paper Autonomy Closure Program

Status: `repo implementation landed; real-paper soak projection active`
Date: `2026-05-10`
Owner: `MedAutoScience`
Purpose: close the MAS loop for fully automated, high-quality medical manuscript progress after a study line is eligible for autonomous work.
Machine boundary: this is a human-readable program plan. Machine truth remains in `study_charter`, `paper/evidence_ledger.json`, `paper/review_ledger.json`, `artifacts/publication_eval/latest.json`, `artifacts/controller_decisions/latest.json`, `study_runtime_status`, `runtime_watch`, runtime supervision receipts, owner-route dispatch receipts, manuscript/package rebuild proof, and live study artifact refs.

## 结论

全自动推进高质量医学论文的卡点逻辑已经清晰：难点不是单纯“有没有 daemon / gateway / cron”，而是论文主循环是否能把研究方向、分析结果、AI reviewer 结论、稿件修复、gate replay、worker 恢复和转向止损都压成同一条可执行、可重放、可审计的 owner route。

当前 MAS 已经保留并转译了 MDS / DeepScientist 的 skill-led stage discipline：`agent_entry_modes.yaml` 中的 scout、idea、baseline、experiment、analysis-campaign、write、review、decision/finalize 等 route contract，已经把进入条件、hard success gate、durable outputs、human gate boundary、next route 和 route-back triggers 写成 MAS 可消费的合同；`study_charter.paper_quality_contract.stage_expectations`、bounded-analysis policy、route decision surface 和 owner-route dispatch 继续承接这些纪律。也就是说，问题不是 skill-led 逻辑“没有了”。

2026-05-10 探索自治校准：`docs/policies/study-workflow/stage_led_research_autonomy.md` 固定 `stage-led autonomy, controller-governed evidence` 为长期策略。该策略要求 `controller` 只守医学边界、证据账本、质量门禁、owner route 和止损；研究思考、候选路线、方法比较和结果解释必须主要发生在 stage 内，让 Codex CLI 在 stage packet 约束下自由探索。后续实现不得把 `study_line_decision_engine`、bounded-analysis board 或 route decision surface 误用成机械研究思路生成器；这些 surface 是审计、比较和路由合同。

当前 MAS 同时已经有可运行的外环监管、owner route、AI reviewer provenance、publication gate、quality repair、gate clearing、paper progress SLO、sidecar queue bridge 和 bounded-analysis / route-decision surface。本轮进一步把 repo 级闭环落成可调用实现：AI reviewer finding 能进入 `paper_repair_executor`，负结果/弱结果能产出 executable owner task，修复会写 canonical manuscript / evidence ledger / review ledger / revision log / gate replay request / AI reviewer recheck request / package freshness proof，sidecar dispatch 能消费 `paper_autonomy/*` task，真实 DM002、DM003、Obesity 的 soak 投影能只读报告 artifact delta、gate replay、AI reviewer re-eval、route decision、stop-loss、human gate、continuing repair 或 stable blocker。

仍需保持诚实的边界是：repo implementation landed 不等于每个真实 study 已经完成投稿级闭环。真实论文线必须继续通过受控 live apply / read-only projection 证明最近动作确实带来 manuscript/table/figure/result/package freshness、gate owner 前进、AI reviewer judgment 更新、route switch、stop-loss 或 human gate；worker live、queue task 或状态刷新本身仍不算论文进展。

本 program 的最高目标是把 MAS 从“能监管和解释论文停滞”推进到“能默认持续推进方向锁定后的医学论文，直到进入 human gate、科学/数据止损、或达到 AI reviewer-backed submission-facing quality closure”。

## 当前落地状态

本轮已经落地的是 MAS repo 级 AI-first paper autonomy callable loop，不是全部历史计划的产品级终态。

| 范围 | 状态 | 当前证据 / 边界 |
| --- | --- | --- |
| MAS repair executor closure | `landed` | `paper_repair_executor` 可执行 `analysis_repair`、`text_repair`、`evidence_ledger_repair`、`review_ledger_repair`、`claim_downgrade`、`route_decision`，并写 owner receipt、canonical delta、ledger update、gate replay request、AI reviewer recheck request。 |
| Negative-result executable route | `landed` | `route_decision_orchestrator` 对 weak / negative / contradictory / blocked analysis slice 输出 analysis slice contract、failed path refs、claim policy 和 executable owner tasks。 |
| Default AI reviewer replay loop | `repo surface landed` | supervisor dispatch 与 sidecar `paper_autonomy/ai-reviewer-recheck` 可触发 MAS-owned AI reviewer workflow；最终质量仍以 AI reviewer-backed `publication_eval/latest.json` 为准。 |
| Canonical manuscript/package loop | `landed` | repair 只写 canonical manuscript / evidence ledger / review ledger / revision log 与 rebuild/freshness/delivery proof；`current_package_write_authorized=false`。 |
| OPL/Hermes family runtime E2E queue | `partial` | MAS sidecar task schema 与 OPL family queue projection landed；真实 Hermes gateway cron/webhook restart soak、MAG/RCA parity 和 Full App packaging 不属于本 MAS commit 的完成范围。 |
| Real paper soak | `read-only projection landed` | DM002、DM003、Obesity 可只读报告 artifact delta、AI reviewer re-eval、route decision、stop-loss、human gate、continuing repair 或 stable blocker；尚未把三篇都跑到 controlled live apply 的 submission-facing closure。 |
| Medical quality/reporting guard | `existing guard plus loop integration` | 医学质量仍由 study charter、evidence/review ledger、AI reviewer-backed publication eval 和 publication gate 授权；repo loop 不能机械授权 quality ready。 |
| Stage-led knowledge loop | `repo contract/read-model landed` | `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt`、`stage_recall_index`、stage entry injection、Progress/Portal visibility 和 route materialization guard 已落地；真实 paper line 仍需 read-only / guarded apply soak 持续证明 consumed refs、accepted/rejected writes、route impact、progress delta 或 human gate。 |

因此，当前可以说“MAS AI-first paper autonomy 的 repo callable loop 已落地并有文档/测试/只读真实 paper projection”，不能说“所有计划都已经完整产品化”。Full OPL App 携带 Hermes、MAG/RCA domain adapters、Hermes gateway 真实 24h restart soak、三篇论文 controlled live apply 到最终投稿级交付，仍是后续验收项。

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

这部分已经把“忙但没有论文产物增量”的问题显性化。本轮新增的 `paper_repair_executor` 和 sidecar `paper_autonomy/repair-recheck` dispatch 会在 MAS owner surface 内执行 repair work unit，产出 owner receipt、repair execution evidence、gate replay request、AI reviewer recheck request 和 canonical package loop proof。缺少结构化 canonical patch 的 text repair 会 fail-closed 为 typed blocker，不把内部说明写进正文。

### AI reviewer / quality loop

已落地的质量边界包括：

- `AI-first Quality Boundary Policy` 明确 mechanical projection 不能授权 quality ready、finalize ready 或 submission-facing readiness。
- `ai_reviewer_publication_eval_workflow` 能把 AI reviewer-backed record materialize 到 `artifacts/publication_eval/latest.json`，并附带 reviewer OS trace。
- `ai_reviewer_runtime_workflow_state` 能 fail-closed 检查 publication eval、medical prose review、review ledger 和 evidence ledger 是否关闭。
- `reviewer_refinement_loop` 能从 AI reviewer-backed publication eval 读出质量维度、publication gaps、same-line route-back、comment-to-action matrix、analysis/text repair requirement 和 recheck requirement。
- `ai_reviewer_calibration` 已把 claim overreach、mechanical gate as quality、missing reviewer trace、weak external validation、statistical discipline waiver misuse 这类返工原因沉淀成 calibration corpus / learning read model。

这部分已经把“质量谁说了算”守住了。本轮把 reviewer refinement 的 repair work unit 接到默认 repair execution loop：`analysis_repair`、`text_repair`、`evidence_ledger_repair`、`review_ledger_repair`、`claim_downgrade`、`route_decision` 都有 MAS-owned callable dispatch；不可自动执行的 `display_rebuild`、`package_refresh` 和缺少结构化输入的稿件补丁返回 typed blocker。repair 后自动生成 gate replay target 和 AI reviewer recheck request，但最终质量授权仍必须来自 AI reviewer-backed `publication_eval/latest.json`。

### Analysis direction / negative-result loop

已落地的方向与负结果 surface 包括：

- `study_line_decision_engine` 对候选方向按 novelty、clinical relevance、data fit、external validation、analysis feasibility、journal fit、risk/cost、stop threshold 打分，并给出 `proceed_to_baseline`、`return_to_scout`、`switch_line`、`human_gate`。
- `route_decision_orchestrator` 把 route action 映射到 controller decision，并要求 candidate path graph 至少具备 question、evidence_basis、expected_artifact、stop_rule 和 decision。
- `route_decision_rehearsal` 覆盖 `weak-result`、`blocked-statistics`、`missing-external-validation`，并演练 `continue`、`route_back`、`bounded_repair`、`stop_loss`、`switch_line`、`human_gate`。
- `bounded_analysis_frontier_policy` 明确 explore / exploit / fusion / debug / stop，要求 accepted / rejected candidates、winning path、failed paths、evidence refs、reviewer concern closure status 和 next route。

这部分已经从 read model 推进为 executable owner task plan。`route_decision_orchestrator` 对弱结果、负结果、反向结果或 blocked analysis slice 固定输出 hypothesis、endpoint、method、expected result、failure criteria、actual result、interpretation、route impact、claim policy、failed path evidence refs，以及 `claim_downgrade`、`bounded_repair`、`switch_line`、`return_to_scout`、`stop_loss` 或 `human_gate` 的 owner task。后续 writer / evidence ledger 禁止把 `claim_policy.supported=false` 的原 claim 继续写成 supported。

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
- `docs/policies/study-workflow/stage_led_research_autonomy.md`：固定 stage-led research autonomy，避免 controller 把 Codex 的研究思考机械化为过细任务列表。
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

落地状态：repo surface landed。`runtime_supervisor_dispatch_executor` 的 AI reviewer workflow 输入已携带 manuscript、study charter、evidence ledger、review ledger、publication gate projection，并支持 reporting guideline / calibration refs 作为附加输入；sidecar `paper_autonomy/ai-reviewer-recheck` 会回到 MAS supervisor executor 执行 `return_to_ai_reviewer_workflow`。

落地要求：

- 若 publication eval 缺 AI reviewer provenance，supervisor dispatch 必须能调用 AI reviewer workflow 生成或刷新 AI reviewer-backed eval。
- 输入必须包括 manuscript、study charter、evidence ledger、review ledger、publication gate projection、reporting guideline 和 calibration refs。
- 输出必须是 `artifacts/publication_eval/latest.json`、reviewer OS trace、medical prose review 或明确 blocker。
- 非 human、非权限类缺口不能投影成 `waiting_for_user`。

### Lane 2: Reviewer findings to repair work units

目标：把 AI reviewer finding 自动转成可执行修复单元。

落地状态：repo surface landed。`reviewer_refinement_loop -> repair_work_units -> paper_repair_executor.dispatch_repair_work_unit` 已形成执行链，输出 owner receipt、canonical artifact delta、ledger update、gate replay request 和 AI reviewer recheck request。缺少结构化稿件 patch 的 text repair 返回 typed blocker，不直接污染正文。

落地要求：

- `reviewer_refinement_loop.comment_to_action_matrix` 不只做 read model，还要进入 owner-route work-unit queue。
- `analysis_repair` 必须能启动 bounded analysis campaign，并写回 evidence ledger / result refs。
- `text_repair` 必须能修改 canonical manuscript source，并写 revision log / review ledger closure。
- 每个 repair 后必须触发 gate replay 和 AI reviewer recheck。

### Lane 3: Analysis direction autonomy

目标：把异常分析结果、负结果和不符合预期的结果变成默认 route-decision 循环。

落地状态：repo surface landed。`route_decision_orchestrator` 已把 adverse analysis slice 物化为 executable owner task plan，并把 failed path、claim downgrade policy、required outputs、gate replay target、idempotency key 和 source fingerprint 写入 controller decision projection。

落地要求：

- 每个 analysis campaign slice 必须写 hypothesis、endpoint、method、expected result、failure criteria、result、interpretation 和 route impact。
- 弱结果或反常结果必须自动进入 claim downgrade、bounded repair、switch line、return to scout、stop-loss 或 human gate。
- `study_line_decision_engine`、`route_decision_orchestrator` 和 `bounded_analysis_frontier_policy` 升级为 executable workflow，不停留在 materializer / read-model。
- 负结果必须进入 evidence ledger 和 failed path history，不能被后续写作隐藏。

### Lane 4: Manuscript rewrite and canonical artifact loop

目标：让稿件修复真正修改 canonical manuscript / tables / figures / legends / package source，而不是只刷新状态。

落地状态：repo surface landed。`canonical_manuscript_package_loop` 会在 repair 后写 rebuild proof、current package freshness proof 和 delivery manifest，且 `current_package_write_authorized=false`。`current_package` 仍只能由 controller-authorized rebuild 生成；repair executor 不直接写 package。

落地要求：

- AI author / repair worker 从 review finding 和 evidence refs 生成 scoped patch。
- patch 必须更新 canonical source、evidence ledger、review ledger、revision log 和 rebuild proof。
- manuscript-native prose gate 前置运行，防止 controller prose、package anchors、author TODO 或 reviewer-facing labels 进入正文。
- 每次 rewrite 后必须进入 publication gate replay 和 AI reviewer re-eval。

### Lane 5: Durable queue, notification, recovery and soak

目标：把 gateway 在线能力用于持续推进，而不是只做状态轮询。

落地状态：MAS side landed，OPL bridge landed in family runtime。MAS sidecar export/dispatch 已支持 `paper_autonomy/repair-recheck`、`paper_autonomy/ai-reviewer-recheck`、`paper_autonomy/gate-replay` 和 `paper_autonomy/route-decision`；OPL family queue 只保存 task、projection、dispatch receipt 和 inbox/event，不写 MAS truth。

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

### Lane 7: Stage knowledge and literature memory loop

目标：让 `scout`、`idea`、`analysis-campaign`、`review` 等会改变论文走向的 stage 自动消费 MAS 的 knowledge / literature / memory plane，并在 closeout 时把可复用 lesson、失败路径、引用缺口和研究方向判断写回正确层级。

落地状态：repo surface 已落地；真实 paper soak 仍保持 evidence-gated。当前已固定 `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt` 和 `stage_recall_index`，并把 stage entry injection、typed closeout routing、Progress/Portal visibility、route materialization guard 接进 MAS-owned controller/read-model surface。

这条 lane 解决的是旧 DeepScientist/MDS 里 `memory.search/list_recent` 和 quest literature shelf 的探索体验，在 MAS 中被 authority 分层后没有完全闭合的问题。正确方向不是恢复一个 generic memory truth source，而是把 memory 变成 stage packet 的输入和 closeout 的受控输出。

落地要求：

- 每个探索性 stage 进入前必须生成 `stage_knowledge_packet`，至少包含 workspace research memory summary、workspace canonical literature coverage、study reference context、literature provider/runtime readiness、recent failed-path lessons、citation gap status、active claim/evidence boundary 和 source fingerprint。
- `scout` 必须读取 topic landscape、dataset question map、venue intelligence、canonical literature coverage 和 provider literature readiness；输出 clinical question framing、literature gap、anchor paper role 和 route recommendation。
- `idea` 必须读取 prior candidate/failed lines、study recall index、reference context 和 journal neighbor refs；输出 selected line、rejected alternatives、selection rationale、stop rule、memory reuse note。
- `analysis-campaign` 必须读取 failed-path history、evidence ledger、citation gaps、provider literature refs、bounded frontier 和 reviewer concerns；输出 slice ledger、negative/weak-result interpretation、route impact、failed-path lesson。
- `review` 必须读取 manuscript、claim-evidence map、display-to-claim map、reference context、citation ledger refs、AI reviewer calibration memory 和 prior reviewer findings；输出 reviewer action matrix、evidence/citation repair request、reusable critique lesson。
- 每个 stage closeout 必须生成 `stage_memory_closeout_packet`，把内容分流到正确 owner：workspace reusable lesson、study-specific reference role、quest materialization refresh、evidence ledger update、review ledger update、controller decision 或 human gate request。
- memory/literature 回写必须 fail-closed：不能把 quest-local literature cache 升格为 workspace authority，不能用 memory card 授权 publication quality，不能用 provider projection 替代 AI reviewer 或 controller decision。

## Stage Knowledge Plane Target Design

### 核心对象

新增的目标不是一个新 daemon，而是一组 MAS-owned controller/read-model/materializer surface：

1. `stage_knowledge_packet`
   - 进入 stage 前生成。
   - 只读聚合 workspace memory、workspace literature、study reference context、quest materialization、evidence/review ledgers、publication eval、controller decisions 和 route history。
   - 作用是给 Codex stage 执行器足够上下文，避免每轮从零发现。
2. `stage_memory_closeout_packet`
   - stage 完成时生成。
   - 把 stage 新发现的 reusable lesson、failed path、citation gap、reference role change、claim-boundary decision 和 next route 归类。
   - 只描述 proposed writes；真正写入仍由 owner-specific materializer 执行。
3. `memory_write_router`
   - 根据 closeout packet 把内容路由到 workspace research memory、study reference context、evidence ledger、review ledger、controller decision、quest materialization refresh 或 human gate。
   - 对每个目的地使用显式 schema、source refs、idempotency key 和 authority boundary。
4. `stage_recall_index`
   - 面向 runtime/progress 的 read model。
   - 显示当前 stage 消费了哪些 memory/literature，产生了哪些可复用 lesson，哪些被拒绝写回，哪些需要 human gate。

### 输入顺序

stage packet 的输入优先级固定如下：

1. `study_charter`、active claim boundary、human gate boundary。
2. `artifacts/controller_decisions/latest.json`、route decision history。
3. `paper/evidence_ledger.json`、`paper/review_ledger.json`、claim-evidence / display-to-claim map。
4. `studies/<study_id>/artifacts/reference_context/latest.json`。
5. `portfolio/research_memory/literature/registry.jsonl`、`references.bib`、`coverage/latest.json`。
6. `portfolio/research_memory/topic_landscape.md`、`dataset_question_map.md`、`venue_intelligence.md`、`study_recall_index.md`。
7. `literature_provider_runtime`、`literature_intelligence_os`、provider response ledger refs 和 citation freshness。
8. quest-local `literature/*`、`paper/references.bib`、`reference_coverage_report.json`，只作为 materialized working copy。

这个顺序保证 Codex 能自由探索，但不能绕过 study boundary、controller decision 或 evidence authority。

### 输出归属

stage closeout 的输出按下面规则分流：

| closeout 内容 | owner surface | 说明 |
| --- | --- | --- |
| 跨 study 可复用的临床方向、数据约束、venue 经验 | `portfolio/research_memory/*` | 只写可复用 lesson，不写单篇 paper 结论。 |
| 新增或修正的文献 record | workspace canonical literature | 必须有 DOI/PMID/PMCID/arXiv/url/local asset source，冲突 fail-closed。 |
| 当前 study 的 anchor / competitor / neighbor 角色 | study reference context | 只改变本 study 选择和角色，不改变 workspace truth。 |
| 引用缺口、reference gap、metadata gap | literature provider/runtime repair request | 进入 provider operation 或 medical literature audit。 |
| 支撑 claim 的结果、表图、统计输出 | evidence ledger / display-to-claim map | memory 不能替代 evidence。 |
| reviewer finding、批评和修复闭环 | review ledger / AI reviewer route | memory 只能保存 reusable critique lesson。 |
| 弱结果、失败路径、stop rule、路线影响 | failed-path history / controller decision | 必须影响 route，不允许被写作隐藏。 |
| 需要人类判断的边界变化 | human gate request | 不能自动扩大 charter。 |

### 与外部成熟工程经验的映射

本设计借鉴但不直接依赖外部框架：

- LangGraph 的 checkpoint / persistence / long-term memory / interrupt 思路映射为 `stage_knowledge_packet`、`stage_memory_closeout_packet`、restore point 和 human gate。
- Temporal 的 Workflow Event History、Activity retry、timeout、heartbeat 映射为 MAS runtime event log、work-unit idempotency、retry budget、worker lease 和 dispatch receipt。
- OpenAI Agents/Responses 的 sessions / background run / tracing 思路映射为 MAS 持有 run status、trace refs、artifact delta 和 next owner；Codex CLI 仍只是执行器。
- Pydantic AI durable execution 的 graph persistence 思路映射为 typed stage state、durable packet schema 和可恢复 stage closeout。
- 医学 reporting guideline 的前置约束映射为 stage packet 输入，而不是投稿包后置补救。

## Stage Knowledge Plane Landed Scope And Remaining Soak

这条计划已经作为本 program 的 `Lane 7` 落地到 repo surface。当前完成口径是 contract、read model、entry injection、typed closeout routing、visibility 和 route materialization guard 已可用；真实 paper line 的效果仍必须继续通过 read-only / guarded apply soak 证明。

### T0: Contract freeze

Status: `landed`

- `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt`、`stage_recall_index` 已作为 machine-readable contract 固定。
- `agent_entry_modes` 已为 `scout`、`idea`、`analysis-campaign`、`review` 增加 knowledge input obligations 和 memory closeout obligations。
- packet 必须带 `schema_version`、`study_id`、`stage`、`input_refs`、`source_fingerprint`、`authority_boundary`、`idempotency_key`，并禁止把聊天总结当作 authority。

### T1: Read model aggregator

Status: `landed`

- `stage_knowledge_packet` builder 已只读聚合 workspace memory、workspace literature、study reference context、quest materialization、evidence/review ledgers、controller decisions 和 route history。
- `scout`、`idea`、`analysis-campaign`、`review` 可生成 stage-specific packet；缺 registry、reference context 或 ledgers 时 fail-closed 到明确 `missing_reasons`。
- packet 只做 read model，不写 study truth、publication truth 或 quality truth。

### T2: Prompt / stage entry injection

Status: `landed`

- agent entry / owner dispatch / runtime packet 可注入 stage knowledge packet ref。
- `review` stage 的 AI reviewer request packet 已带 `stage_knowledge_packet_ref`、status、missing reasons 和 required ref validity。
- `write` / `finalize` 不开放扩大探索；它们继续读取 evidence/review/claim map。

### T3: Closeout packet and memory write router

Status: `landed`

- stage closeout 已通过 typed normalizer 进入 `stage_memory_closeout_packet`。
- `memory_write_router` 只接受 typed closeout，不解析自由文本。
- reusable lesson、citation gap、failed path、reference role、claim boundary、controller request 会分别进入 workspace memory proposal、literature provider repair、failed-path history、reference context owner、controller decision request 或 human gate owner。
- duplicate closeout idempotent；single-study claim 不得误写为 workspace memory。

### T4: Route coupling for weak and negative results

Status: `landed`

- `study_line_decision_engine` 已标记为 `audit_comparator_only`，只比较 stage output，不拥有路线生成 authority。
- `route_decision_orchestrator` 已固定为 `route_router_and_materializer`，缺 `stage_output_refs` 时会阻断 controller decision write。
- winning path 必须回指 stage output、evidence refs、failed paths 和 controller decision；默认路径不能绕过 stage closeout 直接生成 winning path。

### T5: Real paper soak

Status: `remaining evidence gate`

- DM002、DM003、Obesity 或当前 active paper line 仍需继续展示 `stage entry packet -> Codex execution -> closeout packet -> router receipt -> progress delta / human gate / stop-loss`。
- 若没有可继续推进的 paper line，必须展示 terminal blocker、human gate、publication gate 或 data/science stop。
- OPL/Hermes 只负责 queue、wakeup、notification、receipt，不写 MAS truth。

### T6: Operator visibility and parity guard

Status: `landed with continued workspace polish`

- Product Entry / Progress Portal 可投影 stage knowledge freshness、consumed refs、closeout receipt、accepted/rejected writes、route impact 和 next owner。
- MDS behavior matrix 已把 memory/literature 标记为 `purpose_equivalent_with_authority_split`：MAS 保留 DeepScientist/MDS 的 stage memory/literature 目的，但通过 workspace/study/quest/controller/evidence authority 分层实现。
- 继续真实 workspace polish，防止 stage entry memory 退化成静态 docs 链接或聊天记忆。

### T7: Mechanical route cleanup and retirement

Status: `landed guard; cleanup discipline remains active`

- `study_line_decision_engine` 保留为 audit comparator。
- `route_decision_orchestrator` 保留为 route router / stop-loss / executable task materializer。
- 固定分流器不能单独生成研究路线；所有 route decision 必须回指 stage output、evidence refs、failed path history 和 controller decision。
- 后续删除旧入口时必须先保留 parity fixture，再清理不再被 tests、runtime、docs、MCP、product-entry 消费的旧 vocabulary，避免形成第二套研究路线污染源。

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

### Stop-loss decision test

给定一个无法发表或继续收益很低的 fixture，MAS 必须完成：

- 任意 stage 能提出 `stop_loss_candidate`；
- `decision` stage 汇总 attempted paths、failed paths、evidence gain ceiling、repair attempts、alternative routes 和 human gate question；
- controller decision 正式写出 `stop_loss`、`claim_downgrade`、`switch_line`、`return_to_scout` 或 `human_gate`；
- workspace memory / study recall 记录 reusable lesson 和 re-entry condition；
- write/finalize 不允许继续推进原 claim。

### Real-paper soak

DM002、DM003、Obesity 的 read-only/live verification 必须展示：

- 当前 state 是 running、parked、breach、blocked、human gate 或 terminal；
- `why_not_progressing` 指向 owner route、quality repair、worker recovery、safe reconcile、publication gate、human gate 或 scientific/data stop；
- 最近一个自动动作产生 artifact delta、gate replay、AI reviewer judgment、repair receipt，或稳定 blocker；
- 无 `owner_callable_surface_missing` 的非 human AI reviewer route；
- `meaningful_artifact_delta=true` 只在真实 manuscript/table/figure/result/package freshness/gate owner progress 后出现。

### Stage knowledge loop test

repo contract 应继续证明：

1. 为 `scout`、`idea`、`analysis-campaign`、`review` 生成 stage-specific `stage_knowledge_packet`；
2. packet 引用 workspace memory、workspace literature、study reference context、provider literature runtime、evidence/review ledgers 和 controller decisions；
3. Codex owner packet 包含 stage knowledge refs 和 closeout obligation；
4. stage closeout 生成 typed `stage_memory_closeout_packet`；
5. router 把 reusable lesson、citation gap、failed path、reference role update、evidence repair 和 human gate 分流到正确 owner；
6. 产生 idempotent router receipt；
7. progress surface 显示 memory consumed、writes accepted/rejected、route impact 和 next owner。
8. Progress/Portal 或 recall index 显示 packet freshness、consumed refs、accepted/rejected writes 和 next owner。

不通过条件：

- 用 chat summary 代替 packet；
- 用 memory card 代替 evidence ledger；
- 用 quest-local literature cache 更新 workspace canonical literature；
- 用 provider projection 授权 publication quality；
- stage 负结果没有进入 failed-path 或 route decision。

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

- stage knowledge tests：packet builder、stage-specific obligations、closeout normalizer、memory write router、idempotency、authority boundary、negative-result route coupling。
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
