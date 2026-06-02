# Progress-first Stage 推进吞吐审计

Status: `read_model_landed_same_tick_pump_and_delta_tail_pending`
Date: `2026-06-01`
Owner: `MedAutoScience`
Purpose: `progress_first_stage_throughput_audit`
State: `active_support`
Machine boundary: 本文是人读系统排查记录。机器真相继续归 `contracts/stage_control_plane.json`、`agent/stages/stage_route_contract.yaml`、`contracts/action_catalog.json`、product-entry manifest、domain-handler receipt、`study_progress` / `study_state_matrix` read-model、OPL current-control-state、真实 workspace owner receipt / typed blocker / artifact / memory / reviewer refs。

## 结论

MAS 当前真正的 runtime-guard Stage 是 6 个，定义源是 `contracts/stage_control_plane.json`；domain route 是 10 个，定义源是 `agent/stages/stage_route_contract.yaml`。Progress-first 设计已经进入 stage contract、owner-route handoff、`study_progress.next_forced_delta`、`progress_first_monitoring_summary`、`study_state_matrix.progress_first_tick_accounting`、Portal / MCP / focused tests。

这轮已把最影响速度、最大产出和 Stage 推进的 P0/P1 读模型与 supervisor cadence 尾项落到可用 surface：target surface 精确性、workspace throughput 排序、terminal closeout 语义完整性、route knowledge/memory obligation descriptor、developer supervisor same-tick pump。仍未关闭的是 production 证据尾项：真实 paper-line owner receipt、stable blocker、no-forbidden-write proof、artifact/memory lifecycle receipt 和 human gate receipt 的持续 scaleout。

1. `ready owner action -> OPL stage attempt -> MAS owner receipt/blocker` 的 pickup latency 现在进入 `study_state_matrix.progress_first_tick_accounting` 排序与 `throughput_bottleneck_counts`。
2. `next_forced_delta.target_surface` 现在带 `target_surface_specificity`、`missing_explicit_target_surface`、`target_surface_fallback_reason` 和 `target_surface_diagnostic`；缺显式 owner-route target 时仍 fail closed 到 generic route obligation，但 operator 能看到这是 fallback。
3. terminal closeout 现在在 `progress_first_monitoring_summary.latest_terminal_stage` 同时投影 `semantic_completeness`、`telemetry_completeness` 与 `terminal_closeout_semantic_completeness`，缺 user stage log / duration / token / cost 时给出 typed blocker diagnostic 和 next forced delta。
4. 10 个 route 的 `knowledge_input_obligations` 与 `memory_closeout_obligations` 现在由 `route_obligations_descriptor` 从 canonical route contract 投影，并嵌入 product-entry `family_stage_control_plane_descriptor`。
5. late-stage 已规定先产出 paper/package delta 再 gate replay；真实 paper-line success receipt / stable blocker scaleout 仍是主要 evidence tail。
6. `domain-health-diagnostic` developer supervisor safe-apply 不再把一次 heartbeat 停在 receipt/read-model follow-through；同 tick 最多追 3 轮，直到 provider handoff、typed blocker、no owner action、repeat-suppressed owner-delta-required 或 max-pass owner-delta-required。focused paper-line 推进必须附带 `--studies <study_id>...`，让 reconcile/materialize/dispatch 共享同一 study scope，避免全 workspace redrive。

## Stage 清单与推进要求

所有 Stage 共享同一 Progress-first 最小推进合同：

- `minimum_forward_delta`：非终局结果必须是 `deliverable_progress_delta`、`typed_blocker_with_next_forced_delta`、`human_gate_with_last_attempted_delta` 或 `stop_loss_candidate`。
- 禁止把 `no_op_with_currentness_proof`、`record_only_reviewer_loop`、`provider_completed_without_typed_closeout`、`platform_repair_counted_as_deliverable_progress` 当成 Stage 推进完成。
- `progress_delta_policy` 必须输出 `progress_delta_classification`、`deliverable_progress_delta`、`platform_repair_delta`、`next_forced_delta`。平台修复不计为论文/交付物推进。
- no-op currentness budget：最多 1 次连续 no-op；第 2 次必须升级为带 `next_forced_delta` 的 typed blocker；第 3 次进入 human gate 或 stop-loss candidate。
- same work-unit receipt / reconcile budget：同一 `study_id`、owner、action、`work_unit_fingerprint` 的 non-consumable closeout 最多触发 1 次 automatic redrive；之后必须收敛为 `progress_first_owner_redrive_budget_exhausted` typed blocker、机制修复、human gate 或 stop-loss candidate，不能继续 mint 新 default-executor task / dedupe key。
- `user_stage_log_contract` 必须给出 `stage_name`、`problem_summary`、`stage_goal`、`stage_work_done`、`changed_stage_surfaces`、`outcome`、`remaining_blockers`、`evidence_refs`，并显式记录或显式缺失 `duration`、`token_usage`、`cost`。
- human gate 必须带 `last_attempted_deliverable_delta`、`why_ai_cannot_progress_one_more_delta`、`next_forced_delta`、`human_decision_owner`。缺这些字段时应回到 AI executor 产出最小 delta 或 typed blocker。
- typed blocker 必须带 `blocker_family`、`study_id_or_domain_identity`、`work_unit_id`、`eval_id_or_review_ref`、`source_fingerprint`、`repeat_count`、`first_seen`、`last_seen`、`last_deliverable_delta`、`next_forced_delta`、`escalation_owner`、`terminal`。
- route obligation lens 必须先投影当前 blocking route obligation，再显示 generic stage status。

| Stage | 类型 | 进入条件 | 推进后保证 | 覆盖 route | 允许 action | runtime event refs |
| --- | --- | --- | --- | --- | --- | --- |
| `direction_and_route_selection` | `planning` | `study_direction_request_received` | `direction_route_selected` | `scout`, `idea`, `decision` | `study_progress`, `study_state_matrix`, `authority_operations` | `domain_route_owner_route.direction_route_selected`, `controller_decisions.direction_route_selected` |
| `baseline_and_evidence_setup` | `source_preparation` | `direction_route_selected` | `baseline_evidence_ready` | `baseline`, `experiment` | `submit_study_task`, `launch_study`, `study_progress` | `controller_decisions.baseline_evidence_ready`, `evidence_ledger.baseline_evidence_ready` |
| `bounded_analysis_campaign` | `creation` | `baseline_evidence_ready` | `bounded_analysis_evidence_ready` | `analysis-campaign` | `launch_study`, `study_progress`, `study_state_matrix` | `domain_health_diagnostic.bounded_analysis_evidence_ready`, `evidence_ledger.bounded_analysis_evidence_ready` |
| `manuscript_authoring` | `creation` | `bounded_analysis_evidence_ready` | `manuscript_draft_reviewable` | `write` | `launch_study`, `submit_study_task`, `study_progress` | `controller_decisions.manuscript_draft_reviewable`, `canonical_manuscript.manuscript_draft_reviewable` |
| `review_and_quality_gate` | `review` | `manuscript_draft_reviewable` | `ai_reviewer_gate_receipt_recorded` | `review`, `decision` | `study_progress`, `authority_operations`, `export_inspection_package` | `ai_reviewer_publication_eval.gate_receipt_recorded`, `publication_eval.ai_reviewer_gate_receipt_recorded` |
| `finalize_and_publication_handoff` | `packaging` | `ai_reviewer_gate_receipt_recorded` | `publication_handoff_ready_or_route_back_recorded` | `finalize`, `journal-resolution`, `decision` | `study_progress`, `authority_operations`, `publication_aftercare_plan` | `controller_decisions.publication_handoff_ready_or_route_back_recorded`, `artifact_authority.publication_handoff_ready_or_route_back_recorded` |

## Route 推进要求

Route 是 MAS domain transition obligation，不拥有 OPL runtime attempt lifecycle。每条 route 都必须留下 durable output 或 durable ref，且 terminal handoff 必须给出 minimum forward delta、changed surface、next owner、next work unit 和 next forced target surface。

| Route | 所属 Stage | 推进成功口径 | 最小 durable output | 主要 route-back / human gate |
| --- | --- | --- | --- | --- |
| `scout` | `direction_and_route_selection` | 锁定研究 target、population、evidence boundary，并给出下一 formal route | scout note、Literature Scout OS、open questions、route recommendation | evidence target 仍模糊、study question 变化、direction rationale 缺失；问题/人群/证据边界重置触发 human gate |
| `idea` | `direction_and_route_selection` | 选择最强 study line，并说明 tradeoff、scorecard、执行建议 | line-selection note、Study Line Selection Scorecard、next-route recommendation、claim sketch | baseline readiness 缺失、后续证据冲突、controller route bias 改变；选线改变 locked direction 触发 human gate |
| `baseline` | `baseline_and_evidence_setup` | baseline / comparator 可复现，且能判断是否继续 | baseline artifact set、baseline summary、continue/reroute recommendation | baseline 不能支撑 claim、cohort/comparator 变化、reviewer-first 缺 baseline proof；claim boundary 改变触发 human gate |
| `experiment` | `baseline_and_evidence_setup` | primary result 带 run context，回答当前 study question | primary result artifacts、experiment summary、next-route recommendation | 结果否定 study line、reproducibility gap、controller boundary 变化；新外部 claim 触发 human gate |
| `analysis-campaign` | `bounded_analysis_campaign` | 每个 bounded evidence gap 有结果或 stop decision，且不扩 primary claim | analysis summary、Bounded Analysis Candidate Board、result refs、remaining gaps、reviewer/Codex revision handoff | 新 gap 超出范围、claim support 变弱、reviewer 要求回 baseline/study line；新增 primary claim 触发 human gate |
| `write` | `manuscript_authoring` | manuscript claim 与 evidence 一致，open gaps 和 next actions 可见 | draft/section update、claim-evidence map、reviewer-first note、first-draft quality note、revision handoff | claim 缺证据、novelty/rigor gap、可用数据维度未用、narrative 改变边界、只改 `current_package` 未回 canonical paper；外部流通/投稿前触发 human gate |
| `review` | `review_and_quality_gate` | reviewer action matrix 把每个 concern 映射到 evidence/citation/text/analysis/decision/human gate | reviewer action matrix、evidence/citation repair request、reusable critique lesson、next route/human gate recommendation | claim 缺直接证据、novelty/rigor/citation gap 无法写作修复、AI reviewer 要求回 baseline/analysis/decision；外部 release 或 submission authorization 触发 human gate |
| `finalize` | `finalize_and_publication_handoff` | final package 内部一致，review artifacts 足够，submit-ready 或 route-back 明确 | final package checklist、limitations/caveats/readiness statement、final review summary | final audit 缺 proof、bundle 暴露 reviewer concern、package assembly 改变 claim；submission-ready / external delivery authorization 触发 human gate |
| `decision` | `direction_and_route_selection` / `review_and_quality_gate` / `finalize_and_publication_handoff` | 记录 go / stop / reroute / human-gate judgment，downstream owner 明确 | controller-facing decision、Stop-loss Memo、evidence refs、next owner/escalation | 新证据推翻 decision、human gate 改变边界、下游报告 unmet assumptions；official go/stop/reroute 或 direction reset 触发 human gate |
| `journal-resolution` | `finalize_and_publication_handoff` | 选择 outlet / package rule，并反映到 draft plan | journal choice note、packaging checklist、next route | journal requirements 暴露 evidence/structure gap、outlet 改变 claim framing、packaging constraint 改变 delivery plan；投稿承诺或外部 release 触发 human gate |

所有 route 还共同要求 `stage_knowledge_packet_ref` 和 `stage_memory_closeout_packet`。高吞吐运行里，这两个 packet 的作用是减少下个 Stage 重读、重搜、重评审；缺 packet 应当被当作 Stage handoff 质量问题，而不是普通文档缺口。

## 已落地机制

| 机制 | 当前状态 | 速度/产出含义 |
| --- | --- | --- |
| 6 个 Stage 的 `minimum_forward_delta` | 已写入 `contracts/stage_control_plane.json` 并由 product-entry stage descriptor tests 覆盖 | 每次 attempt 必须产出交付物 delta、typed blocker、human gate 或 stop-loss，阻断“只跑完 provider 但没有产出” |
| `progress_delta_policy` / 双 delta 分账 | 已在 `src/med_autoscience/opl_domain_pack/progress_first_policies.py`、`study_progress`、Portal、MCP 中投影 | 论文/交付物推进和平台修复分开，避免把 currentness 修复冒充 Stage 产出 |
| `study_progress.next_forced_delta` | 已由 `progress_first_projection` 生成，并被 Portal / MCP / tests 消费 | operator 能直接看到下一次必须产出的 delta、target surface、acceptance refs、owner action |
| target surface diagnostic | 已在 `study_progress.next_forced_delta`、MCP compact projection、Progress Portal 和 focused tests 中透传 | 精确 target 与 generic fallback 可直接区分，避免 operator 只看到“需要推进”却不知道可核查 surface |
| `progress_first_monitoring_summary` | 已聚合 active run、stage attempt、worker liveness、next owner、next work unit、stage log、dispatch consumption、terminal closeout semantic/telemetry completeness | 避免在多个 surface 之间人工判断“是否真的在跑、卡在哪个 owner、closeout 能不能算完成” |
| `study_state_matrix.progress_first_tick_accounting` | 已按 workspace tick 汇总 ready/running/blocker/human gate/unconsumed/overdue，并输出 `priority_rank`、`throughput_bottleneck`、`throughput_bottleneck_counts`、closeout semantic 与 telemetry 缺口 | 可以把多 study 从状态解释推进到可排序的 pickup / running / blocker / closeout 清障入口 |
| route obligations descriptor | 已由 `stage_route_contract.route_obligations_descriptor` 投影 10 个 route 的 knowledge/memory obligations，并嵌入 product-entry descriptor | OPL/operator 可在 Stage handoff 前读取缺哪些 knowledge input 或 memory closeout，减少后续 Stage 重搜、重读、重评审 |
| closeout-first admission | `progress_first_closeout` 会在存在 immutable dispatch 和 running attempt 且未消费 closeout 时阻止新 default-executor task | 防止同一 work unit 被重复派发，要求先消费 owner receipt、stage closeout 或 stable typed blocker |
| same work-unit redrive budget | `default_executor_execution_receipt_consumption` 会把第二次同义 non-consumable default-executor closeout 消费为 `progress_first_owner_redrive_budget_exhausted` typed blocker；`dispatch_repeat_suppression` 不再对 Progress-first owner action 特殊放行 | 防止流程把时间耗在重复 receipt / read-model reconcile / new dedupe key 上，失败后直接暴露机制修复、human gate 或 stop-loss 入口 |
| developer supervisor same-tick pump | `domain-health-diagnostic --apply --request-opl-owner-route-reconcile` 会同 tick 连续执行 owner-route reconcile、action materialize 与 owner-action dispatch，直到 provider handoff、typed blocker、no owner action 或 owner-delta-required diagnostic；focused paper-line tick 必须附带 `--studies <study_id>...`，未指定时才按全 workspace redrive 处理；same-tick initial scan 与 provider-admission probe 使用短 OPL provider/live-attempt 预算，并在 `provider_probe_budget` 中暴露 | 防止每 30 分钟只推进一个 receipt/reconcile 步骤，并避免 002/003 这类 focused 推进误触发 001/004；handoff 后不能长时间卡在 OPL queue/attempt inspect 或 full read-model reconcile，超预算应返回 `provider_handoff_written_admission_pending` / typed diagnostic；若只剩重复 receipt/read-model reconcile，直接暴露 `repeat_suppressed_owner_delta_required` 或 `max_passes_exhausted_owner_delta_required` |
| typed blocker repeat budget | `progress_first_blocker_budget` 会补 `repeat_count`、delta classification、next escalation | 同一 blocker 反复出现时能进入机制修复、human gate 或 stop-loss，不应无限重试 |
| late-stage sprint contract | `stage_route_contract.yaml` 固定先产出 reviewable paper/package delta，再 replay quality gate | 防止 review/currentness loop 抢在实际稿件/包 delta 前无限循环 |

## 系统排查

### P0：owner pickup 和 target specificity

`progress_first_tick_accounting` 已经能显示 `ready_for_owner_action`、`running_provider_attempt`、`unconsumed_owner_action`、`overdue_owner_pickup`、`priority_rank`、`throughput_bottleneck` 和 `throughput_bottleneck_counts`。workspace tick 可以直接按 owner pickup overdue、unconsumed owner action、missing closeout semantics、ready dispatch、running、typed blocker、human gate 和 receipt consumed 做清障排序。

同时，`next_forced_delta.target_surface` 必须尽量来自 current owner route 的精确 paper/source/artifact surface。当前 projection 已对 `owner_route.target_surface` 与 `owner_route.next_forced_target_surface` 标记 `explicit_owner_route_target`，缺显式 target 时标记 `generic_route_obligation_fallback`，并保留 fallback reason。这个 fallback 对 fail-closed 是正确的，但不应被解读为最快推进路径；operator 应优先修补 owner route 的精确 target。

### P0：terminal closeout 语义完整性

Stage 推进最快的路径是 terminal closeout 直接携带 user-readable stage semantics、delta classification、changed surfaces、next owner 和 evidence refs。当前 read-model 已在 latest terminal stage 上投影 `semantic_completeness`、`telemetry_completeness`、`missing_user_stage_log_fields`、`missing_observability_fields`、`closeout_refs` 和 `terminal_closeout_semantic_completeness`。缺字段时不能显示为完成，应直接形成 `typed_closeout_packet_required` 或同等 stable typed blocker，并带 `next_forced_delta`。

### P0：late-stage 必须先产生 paper/package delta

`review_and_quality_gate` 与 `finalize_and_publication_handoff` 最容易被 reviewer/currentness/gate replay 拉进循环。当前 late-stage sprint contract 已规定顺序：先有 reviewable manuscript / candidate package / display freshness proof，再进入 AI reviewer 或 publication gate replay。下一步优化重点是把真实 paper-line success refs 和 stable blocker 扩面，而不是继续增加投影解释。

### P1：no-op 与 platform repair 的预算化

合同已经规定连续 no-op budget，typed blocker 也能携带 repeat lineage。仍需持续审计所有 no-op currentness proof 是否都消费了 duplicate / failed-path / stale-currentness / forbidden-surface refs，并把第二次、第三次升级路径写入 read-model。否则平台修复会占用 Stage attempt，却不产生 deliverable delta。

developer supervisor same-tick pump 已把 `repeat_suppressed_count>0` 和 pass budget exhausted 从普通 diagnostic 升级为 owner-delta-required terminal diagnostic。后续 operator 不应继续安排“再跑一次 reconcile”作为下一步；正确下一步是 domain owner receipt、typed blocker、deliverable delta、human gate、stop-loss 或机制修复。

### P1：route knowledge / memory closeout 防返工

10 条 route 都要求 `knowledge_input_obligations` 与 `memory_closeout_obligations`。这些不是装饰字段，它们决定下一 Stage 是否能少搜、少读、少重评审。当前 `route_obligations_descriptor` 已把每条 route 的 obligations 投影成 `present` / `missing` / `blocker` 与 `handoff_readiness`；下一层真实生产证据是每个 Stage closeout 报告 obligation present / missing / typed blocker 并给出最小补齐 owner action。

### P1：吞吐 telemetry 完整性

`user_stage_log_contract` 要求 `duration`、`token_usage`、`cost`。真实 closeout 缺这些字段时，read-model 可以显示 missing，但无法可靠回答“哪个 Stage 慢、哪个 Stage token 产出比最低、哪个 Stage 重复最多”。应把 duration/token/cost completeness 纳入 stage throughput audit surface，用于后续优先优化。

### P2：OPL App / Portal actionability

Progress Portal 和 MCP compact projection 已能显示 `progress_first_monitoring_summary` 与 `next_forced_delta`，但 Portal 不执行 action。长期主控仍应由 OPL App / Runtime Workbench 承接；MAS 侧只需要保证 read-only payload 足够具体：next owner、work unit、target surface、acceptance refs、dispatch consumption、latest terminal stage 和 evidence refs 都在同一 study scope 内可见。

## 下一步工程动作

1. 继续扩大真实 paper-line delta tranche：至少一条线跑出 manuscript/package/display freshness delta、AI reviewer/gate replay request、owner receipt 或 stable blocker、no-forbidden-write proof，并折回 read-model。
2. 审计所有 terminal closeout producer：provider closeout、domain owner dispatch、writer handoff、AI reviewer handoff、artifact lifecycle handoff 都必须产出 user stage log、delta classification、changed surface、next owner 或 stable typed blocker。
3. 将 route obligation descriptor 的 `present/missing/blocker` 与真实 Stage closeout receipt 关联，避免 descriptor 只停留在 contract 层。
4. 继续把 duration/token/cost completeness 用作 stage throughput evidence，后续才能稳定回答哪个 Stage 慢、哪个 Stage token 产出比最低、哪个 Stage 重复最多。

## 验证入口

设计和合同事实来自：

- `contracts/stage_control_plane.json`
- `agent/stages/stage_route_contract.yaml`
- `src/med_autoscience/opl_domain_pack/progress_first_policies.py`
- `src/med_autoscience/opl_domain_pack/stage_throughput_contracts.py`
- `src/med_autoscience/controllers/study_progress_parts/progress_first_projection.py`
- `src/med_autoscience/controllers/study_progress_parts/progress_first_monitoring.py`
- `src/med_autoscience/controllers/study_state_matrix.py`
- `src/med_autoscience/controllers/domain_owner_action_dispatch.py`
- `src/med_autoscience/controllers/progress_first_closeout.py`
- `src/med_autoscience/controllers/progress_first_blocker_budget.py`
- `docs/runtime/stage_route_handoff_standard.md`
- `docs/runtime/projections/study_progress_projection.md`
- `docs/runtime/display/progress_portal.md`

Docs-only 更新的最小验证是：

```bash
rtk git diff --check
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs
```

若当前 checkout 提供 docs governance doctor，再追加当前有效路径的 doctor 命令；路径缺失时必须在 closeout 中标明未覆盖，不得把未运行的 doc doctor 写成通过。
