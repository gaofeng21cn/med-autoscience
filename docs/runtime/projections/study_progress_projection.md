# Study Progress Projection

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime projection and read-model semantics for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable projection support only; projection truth remains in source, tests, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这份文档冻结 `MedAutoScience` 侧“前台持续有进度”的正式落地方向。

核心结论：

- `study_progress` 是 `controller-owned progress projection`
- 用户可见状态只从 `study_macro_state` 派生
- 前台判断围绕同一条 study authority 展开，不再各入口自行拼装 runtime / publication / controller 细节
- `MAS Progress Portal` 是这套投影的 workspace-local read-model / display materializer：默认生成静态快照和 OPL handoff refs；它只消费 `study_progress` / `workspace-cockpit` / durable truth，不提供 repo-local HTTP service、action endpoint 或 MAS-owned generic workbench。主用户运行工作台和 App-native drilldown 归 OPL App / OPL Runtime Manager。

## 1. 目标

前台需要持续看到：

- 几点几分完成了什么
- 当前研究整体推进到哪一步
- 论文主线推进到哪一步
- 目前卡在什么地方
- 下一步系统准备做什么
- 是否触达医生 / PI 人类 gate 边界

这些信息必须以医生 / 医学专家能看懂的人话表达；runtime 内部技术术语只作为辅助细节。

当前“人话进度”来自固定来源：

- `artifacts/controller/task_intake/latest.json` 的当前任务意图与输出要求
- `runtime_supervision/latest.json` 的 `clinician_update`、`summary`、`next_action_summary`
- `domain_health_diagnostic` 的 controller scan 结果
- `publication_eval/latest.json` 的 verdict / gap summary
- `controller_decisions/latest.json` 的正式下一步决定
- `artifacts/controller/controller_confirmation_summary.json` 的待人工确认摘要
- `bash_exec summary` 与 `details projection` 提供的最近推进描述

## 2. Authority 边界

`study_progress` 的正式定位是：

- `controller-owned progress projection`
- 只读投影面
- 前台解释层

启动、停止、恢复、study-level truth 写入和 runtime-owned surface 维护继续由正式 runtime/control surface 承担。`study_progress` 只读取权威表面，并把当前阶段、证据、阻塞、下一步和 gate 边界投影给前台。

## 3. 输入表面

`study_progress` 的 authority 输入只读下列表面：

- `progress_projection`
- `studies/<study_id>/artifacts/controller/task_intake/latest.json`
- `studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json`
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `studies/<study_id>/artifacts/controller/controller_confirmation_summary.json`
- `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- explicit archive import reference: `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `domain_health_diagnostic` 最新 report

允许吸收但不赋予 authority 的 enrichment surface：

- legacy enrichment: `quest_root/.ds/projections/details.v1.json`
- legacy enrichment: `quest_root/.ds/bash_exec/summary.json`

这里的关键约束是：

- canonical truth 仍来自 durable surface
- `progress_projection` 内的 `interaction_arbitration` 与 `continuation_state` 属于正式 typed status surface，可直接用于前台判断“这是用户阻塞，还是 MAS 已经仲裁为自动继续”
- legacy `details` projection 与 `bash_exec` summary 只用于补充“最近完成了什么”“论文建议推进到哪一步”，不得作为 active quest lifecycle 或 publication authority
- `.ds/codex_history` 原始事件流只保留给审计和调试场景；新 quest 不依赖 `.ds`、MDS Git 或 `.ds/worktrees` 维护前台进度
- 只要 `runtime_supervision/latest.json` 报告 `recovering / degraded / escalated`，前台就必须优先展示 runtime health，论文阶段在展示顺序上后置
- 只要 `progress_projection.supervisor_tick_audit` 报告 `missing / stale / invalid`，前台就必须明确表述“MAS 外环监管心跳异常”，并停止使用“持续托管监管”口径
- 前台的人话进度固定来自这些 `MAS` durable surface、MAS owner refs 与 OPL `current_control_state` refs；外部 executor adapter、diagnostic 或历史 substrate 的状态只按实际已验证接入情况描述

## 4. 输出合同

`study_progress` 至少输出：

- `study_macro_state`
- `user_visible_projection`
- `current_stage`
- `current_stage_summary`
- `paper_stage`
- `paper_stage_summary`
- `runtime_decision`
- `runtime_reason`
- `task_intake`
- `progress_freshness`
- `deliverable_progress_delta`
- `paper_progress_delta`
- `platform_repair_delta`
- `progress_delta_classification`
- `progress_first_monitoring_summary`
- `opl_current_control_state_refs`
- `domain_authority_refs`
- `runtime_reconcile_trigger`
- `runtime_continuity`
- `latest_events`
- `autonomy_soak_status`
- `autonomy_contract.restore_point`
- `quality_closure_truth`
- `quality_review_followthrough`
- `research_runtime_control_projection`
- `current_blockers`
- `next_system_action`
- `needs_physician_decision`
- `physician_decision_summary`
- `supervision`
- `refs`

其中：

- `study_macro_state` 是用户宏观状态唯一源，短枚举固定为 `writer_state/user_next/reason`
- `user_visible_projection` 是从 `study_macro_state` 派生的人类可见状态读模型；CLI markdown、MCP compact projection、workspace cockpit、attention queue 和 product-entry-status 都只能消费它
- `current_stage` / `current_stage_summary` / `current_blockers` / `next_system_action` 保留为从 `user_visible_projection` 派生的展示字段，不再作为入口自行解释状态的来源
- `task_intake` 表示当前 latest durable study task intake 摘要
- `paper_stage` 表示论文主线当前建议推进阶段
- `progress_freshness` 表示“最近有没有明确研究推进信号”，用于尽早暴露卡住、没进度或空转
- `deliverable_progress_delta` / `platform_repair_delta` 是 OPL generic 进展增量分账投影：前者只计论文/交付物推进、candidate package/display freshness proof、AI reviewer eval follow-through、gate replay 和 write repair，后者只计 controller/read-model/currentness/OPL provider 修复，避免把平台修复混报为交付物推进
- `paper_progress_delta` 是 MAS paper-facing alias，必须与 `deliverable_progress_delta` 同值；新 generic consumer 应优先读取 `deliverable_progress_delta`
- `progress_delta_classification` 使用 OPL shared 分类：`deliverable_progress`、`platform_repair`、`mixed`、`typed_blocker`、`human_gate` 或 `stop_loss`
- `progress_first_monitoring_summary` 是 refs-only 监督摘要：它把 `supervision.active_run_id`、OPL `current_control_state` handoff、`stage_progress_log`、latest terminal stage log、`current_execution_envelope`、`domain_transition` 和 `next_forced_delta` 聚合到一个读模型里，直接回答当前 active run / stage attempt / worker liveness / next owner / next work unit / blocker / stage delta。它只能解释是否有论文推进、平台修复、typed blocker 或 human gate，不能写 runtime-owned surface、paper、package、`publication_eval/latest.json` 或 `controller_decisions/latest.json`，也不能授权质量、投稿或 publication ready。
- `progress_first_monitoring_summary.next_forced_delta` 是 Portal / OPL workbench 的 operator 可见下一 delta 字段。它应表达下一次必须由当前 owner 产出的 study-scoped delta 类型与最小可核查 evidence refs，例如 deliverable / paper delta、platform repair、typed blocker、human gate 或 stop-loss；它不是 action endpoint，也不是 completion claim。`target_surface_specificity`、`missing_explicit_target_surface`、`target_surface_fallback_reason` 与 `target_surface_diagnostic` 用于区分 `owner_route.target_surface` / `owner_route.next_forced_target_surface` 的精确 target 和 generic route obligation fallback。消费方必须把 deliverable / paper delta 与 platform repair 分区展示：refs-only ledger closure、stage replay receipt accounting、typed-blocker payload record / verify、owner-route currentness 和 projection hygiene 只能进入 `platform_repair_delta` 或 operator diagnostic，不能写入 `deliverable_progress_delta` / `paper_progress_delta`，也不能显示为论文主线正在推进。
- `progress_first_monitoring_summary.dispatch_consumption` 是 per-study dispatch/receipt 对账摘要，优先读取 OPL handoff、当前 execution envelope 和 domain transition receipt consumption。它只暴露 `consumption_status`、`action_fingerprint`、`receipt_ref`、`execution_status` 与 `unconsumed_duration_hours` 等 refs-only 字段，用于判断 ready owner action 是否已经被 receipt 消费或仍在等待 owner pickup。
- `progress_first_monitoring_summary.latest_terminal_stage` 必须投影 terminal closeout 语义和 telemetry 完整性：`semantic_completeness`、`telemetry_completeness`、`missing_user_stage_log_fields`、`missing_observability_fields`、`closeout_refs` 与 `terminal_closeout_semantic_completeness`。缺 user-readable stage log、changed surfaces、progress delta classification、duration/token/cost 时，读模型只能显示 typed blocker diagnostic 和 next forced delta，不能把 provider terminal status 读成 Stage 完成。
- `study-state-matrix.progress_first_tick_accounting` 是 workspace/tick 级 Progress-first 对账面，汇总 `expected_owner_action_count`、`ready_for_owner_action_count`、`running_provider_attempt_count`、`typed_blocker_count`、`human_gate_count`、`unconsumed_owner_action_count`、`overdue_owner_pickup_count`、`missing_closeout_semantics_count`、`generic_target_surface_count` 与 `throughput_bottleneck_counts`，并逐 study 投影 `priority_rank`、`monitoring_status`、`throughput_bottleneck`、target specificity、closeout semantic 缺口和 telemetry 缺口；`throughput_bottlenecks` 是同一排序 study list 的 operator alias。它必须优先消费 `progress_projection.progress_first_monitoring_summary` 或顶层 `progress_first_monitoring_summary`，保证 workspace 矩阵与单 study `progress-projection` 使用同一 active attempt、worker liveness、latest terminal stage 和 dispatch consumption 事实。`running` 只能来自 OPL/provider 明确的 `running_provider_attempt=true`；单独存在的 `active_run_id` 只作为 provenance，不能把已 closeout 或 stale attempt 计为运行中。它只能暴露“每个非终局 study 是否落到 running / ready dispatch / receipt consumed / typed blocker / human gate / stalled unconsumed action”之一，不授权 runtime 写入、paper/package 写入、quality verdict 或 publication ready。
- `study-state-matrix.studies[].supervisor_monitoring_bundle` 是 supervisor read-only bundle：它把当前 stage、active run / stage attempt、provider status、worker liveness、24h stage timeline refs、latest closeout、`publication_eval/latest.json` 摘要、currentness、typed blocker 和 next work unit 放到同一个 per-study JSON 字段，供 DM002/DM003 这类监督场景直接读取。该 bundle 是 refs-only 监控入口，不能当 quality verdict、publication ready verdict、submission ready verdict 或写入许可。
- 当 `launch-study --explicit-user-wakeup` 已写入 `explicit_resume` truth event，product-entry launch policy 必须同时暴露 `owner_handoff_hydration_required=true`、hydration action 与 owner refs。`progress_first_monitoring_summary` 应优先把这解释成 OPL owner-route hydration/recovery work unit，而不是继续把旧 `entry_mode_not_managed`、`explicit_resume_pending` 或 `parked_owner=user` 表述为当前用户阻塞。
- `opl_current_control_state_refs` 表示 OPL 当前 attempt / provider / queue / retry-dead-letter / worker liveness projection refs；MAS 不重新解释为 runtime authority
- `domain_authority_refs` 表示 MAS owner receipt、typed blocker、owner-route locator、artifact/source/status locator 和 no-forbidden-write refs
- `runtime_reconcile_trigger` 表示读入口是否可以展示 OPL next action 或 MAS typed blocker；它只返回推荐命令、去重 fingerprint 和 blocked reasons，不直接执行 relaunch/redrive
- `runtime_continuity` 是给 Portal、workspace cockpit、product-entry、MCP 与 OPL handoff 的 compact projection，用来显示 OPL current-control-state ref、MAS owner receipt / typed blocker、next owner 与 why not running；它不重新解释 study truth
- `latest_events` 必须带明确时间戳
- `autonomy_soak_status` 用于表达最近一次已被 durable surface 记录的自治续跑 / outer-loop dispatch，至少要能回答“系统自动转去了哪条线、关键问题是什么、下一次确认看什么、证据引用在哪里”
- `autonomy_contract.restore_point` 是恢复点与 human gate 的前台真相；调用方应读取其中的 `human_gate_required` 与 `summary`，不要从泛化 blocker 推断恢复许可
- `quality_closure_truth` / `quality_review_followthrough` 分别表达质量闭环裁决与复评后的跟进状态，用于和 `autonomy_soak_status` 一起解释“系统是否仍在同线自动收口”
- `research_runtime_control_projection` 是给 `workspace-cockpit`、`product-entry-status`、`build-product-entry` 和上层 gateway 消费的控制投影；它必须把 `restore_point_surface`、`artifact_pickup_surface.pickup_refs`、`command_templates` 与 `research_gate_surface` 固定到同一条 `study-progress` 字段路径上
- `needs_physician_decision` 只在触达正式人类 gate 边界时为 true
- `physician_decision_summary` 必须说明触达的是初始方向锁定、重大转向、止损、外部凭据/秘密、投稿客观信息或最终投稿前审计中的哪一类
- `supervision` 至少包含 `browser_url`、`quest_session_api_url`、`active_run_id`、`launch_report_path` 或 OPL current-control-state refs；`active_run_id` / launch report 只是 provenance，不能单独证明 worker live
- `supervision` 应同步暴露 `supervisor_tick_status`，用于前台解释当前是否仍有新鲜的 MAS 外环监管
- `runtime_continuity` 和 `runtime_reconcile_trigger` 的 authority flags 必须保持 `quality_ready_authorized=false`、`publication_ready_authorized=false`、`submission_ready_authorized=false`
- 双 delta 分账属于 read-model 解释层：不得据此写 `publication_eval/latest.json`、`controller_decisions/latest.json`、paper/package 或任何 domain/runtime authority surface

Late-stage read-model 必须按 progress-first 解释：当同一轮同时出现 sprint delta、candidate package/display freshness proof、gate replay request 和 single next owner blocker / human gate 时，前台先报告 deliverable/paper-facing delta，再报告 gate replay 与下一 owner；不能先把 quality gate blocker 当成“没有交付物进展”。平台修复、projection hygiene、owner-route currentness 或 OPL refs-only ledger closure 只能进入 `platform_repair_delta`，不能冒充 DM002/DM003 deliverable/paper progress。

Progress-first 也适用于无实际 writer 的停滞解释：当 `active_run_id=null`、`actual_write_active=false`，且 OPL provider / worker 未 ready、runtime handoff stale、runtime retry/dead-letter 或 owner-route admission 仍未完成时，`why_not_progressing` 必须优先暴露 runtime / liveness / owner-route 阻断，例如 `runtime_recovery_retry_budget_exhausted` 或当前 owner handoff blocker。`publication_supervisor_state.bundle_tasks_downstream_only` 只能保留为次级 paper gate / downstream delivery 信息，不能抢占主因。typed blocker closeout 中的 structured `remaining_blockers` 也必须折回可执行 current owner projection，例如 `manuscript_story_surface_delta_missing` 进入 write route-back，而不是表现成空等。

`progress_first_monitoring_summary` 是这套解释顺序的单字段监督入口。`study-state-matrix`、MCP compact projection 和 Portal/workbench 消费该字段时，应优先展示它的 `active_run_id`、`running_provider_attempt`、`worker_liveness`、`next_owner`、`controller_action`、`next_work_unit`、`progress_delta_classification`、`stage_progress_log` 和 `latest_terminal_stage`。该字段的 `authority_boundary` 必须保持 `can_write_runtime_owned_surfaces=false`、`can_write_paper_or_package=false`、`can_authorize_quality_verdict=false`、`can_authorize_publication_ready=false`；`foreground_write_policy.supervisor_only=true` 时，前台只能监督或走 MAS/OPL owner route，不得直接写 runtime-owned surfaces。

Progress-first owner action 不能被同 fingerprint 读模型误判为重复调度。当当前 owner route 已授权 `write/run_quality_repair_batch` 或 `ai_reviewer/return_to_ai_reviewer_workflow`，且没有已消费 owner receipt 或明确 terminal gate 时，safe reconcile / same-fingerprint scan 仍必须保留当前 owner action，直到 owner pickup、typed blocker、human gate 或新的 paper-facing artifact delta 关闭该 work unit。repeat suppression 的职责是阻止重复 executor dispatch 和已消费失败路径重放，不能清空当前 owner-authorized action queue。

前台 markdown / 线程回报的固定口径至少保持下面顺序：

1. 当前阶段
2. 当前任务
3. 论文推进
4. 运行监管
5. 当前阻塞
6. 下一步
7. 医生/PI gate（仅在触达正式边界时出现）
8. 最近进展
9. 监督入口

## 4.1 用户可见读模型

`user_visible_projection` 固定为 `study_progress_user_visible_projection`，当前 schema version 为 `2`。它的定位是 truth projection，不是高位 orchestrator。它由 `study_progress` assembly/read-model 层从 `study_macro_state` 生成，入口层只消费，不再自己从低层 surface 拼接当前阶段、阻塞、下一步或证据。

该读模型至少包含：

- `writer_state`
- `user_next`
- `reason`
- `package_delivered`
- `actual_write_active`
- `user_action_required`
- `state_label`
- `state_summary`
- `current_stage` / `current_stage_summary`
- `paper_stage` / `paper_stage_summary`
- `current_blockers`
- `next_system_action`
- `needs_user_decision` / `needs_physician_decision`，均从 `user_action_required` 派生
- `supervision`
- `evidence.latest_events`
- `evidence.refs`
- `evidence_refs`
- `study_macro_state`
- `conditions`

用户可见状态固定为一组短标签：

- `自动运行中`：`writer_state=live`，存在实际 writer / active run。
- `系统排队处理中`：`writer_state=queued`，当前无实际写入，但 MAS 已有明确 owner/action。
- `投稿包已交付，自动停驻`：`package_delivered=true`，系统已释放运行资源。
- `投稿包已交付，等待外部投稿信息`：`package_delivered=true`、`writer_state=parked`、`user_next=submit_info`、`reason=external_info`。
- `用户暂停/手动停驻`：当前无实际写入，需要显式恢复或新方案。
- `质量修复/复审中`：质量、artifact 或 runtime 有明确修复 owner。
- `等待 OPL runtime handoff`：generic runtime lifecycle 需要 OPL 接管；MAS 只输出 domain blocker / handoff refs。
- `止损/终止`：当前论文线不再自动推进，需新计划或明确重开。

入口层规则：

- MCP compact / markdown、CLI markdown、`workspace-cockpit`、workspace alerts 和 product-entry-status preview 必须读取 schema v2 `user_visible_projection`。
- `progress-projection --format json` 的顶层 `current_stage`、`current_stage_summary`、`current_blockers`、`next_system_action`、`paper_stage` 和用户态 writer 字段也必须来自 `progress_projection.user_visible_projection`；runtime 控制字段 `decision` / `reason` 保持原始 controller 语义，用于诊断而不是用户态阶段判断。`study-progress --format json` 的同名顶层字段必须来自自身的 `user_visible_projection`，其中 `reason` 是用户态 Progress-First reason。
- Workspace 监控薄入口固定为 `ops/medautoscience/bin/progress-projection <study_id> --format json` 和 `ops/medautoscience/bin/study-state-matrix --format json`。前者读取单 study 结构化 Progress-first 状态，后者读取 workspace 级 study matrix；`progress-projection <study_id> --json` 只作为旧 JSON alias 兼容。
- 缺少 v2 `user_visible_projection` 时，入口只允许通过 assembly/read-model 层用 `study_macro_state` 生成；缺 `study_macro_state` 或发现 writer 冲突时必须 fail-closed 为 `inspect/conflict`，提示重新生成 canonical projection。
- 入口不得回退到 legacy top-level `current_stage/current_blockers/next_system_action` 作为用户状态来源。
- `user_visible_projection.conditions` 只表达 projection 状态，例如 `macro_state_known`、`package_delivered`、`actual_write_active`、`blocked`、`next_action_known`、`evidence_available`、`user_action_required`、`runtime_supervised`；不得作为 runtime write gate 或 publication quality authority。
- `evidence.refs` 只保存可审计引用路径；任何质量关闭、投稿授权、runtime 写操作仍回到 `publication_eval/latest.json`、`controller_decisions/latest.json`、`progress_projection` 和对应 controller surface。

这个形态借鉴两个成熟工程模式：

- Kubernetes 的 object `spec/status` 分层：controller 观察真实世界并把当前状态写入 status，用户入口读取 status，而不是每个入口重新推断实际状态。
- CQRS / materialized view：写模型持有 authority，读模型面向查询和展示优化，读模型可以由权威事件/状态重建。

## 5. 人话约束

面向医生 / 医学专家的前台文案必须遵守：

- 先说临床/研究含义，再说技术动作
- 避免把 `quest`, `projection`, `fingerprint`, `runtime reentry` 这类内部术语直接当主句
- 百分比进度只在有正式计算口径时展示
- 对正在自动推进的 study，前台应尽量暴露 progress freshness；如果超过阈值仍无明确推进记录，就应把“可能卡住 / 空转”诚实写出来
- bundle/build/proofing 只有在其属于当前主线 next step 时展示为下一步；如果 `bundle_tasks_downstream_only=true`，就必须明确那是后续步骤
- 如果当前需要人工确认，必须直说“需要医生/PI 确认”，并说明对应的人类 gate 边界
- 如果 `interaction_arbitration.action == resume`，前台应采用仲裁后的 resume 结论
- 如果 `continuation_reason == unchanged_finalize_state` 且 MAS 已判定自动继续，前台必须把它表述成“系统接管 runtime 的本地 finalize 停车”，并说明这是 `MAS` 自主恢复动作

方向锁定之后，普通科研和论文质量判断应投影为 `MAS` 自主推进中的下一步，例如补充分析、证据账本更新、review ledger 更新、稿件结构修订或投稿包准备。只有触达正式人类 gate 边界时，前台才展示医生/PI 判断区块。

## 6. 运行形态

`MedAutoScience` 继续保持下面的运行形态：

- OPL current control state 持有 runtime state、attempt event、recovery、worker liveness 和 quest/stage lifecycle projection；MAS 持有 domain authority refs、owner receipt、typed blocker 和 publication/artifact/source authority
- 默认 outer supervision scheduler owner 是 OPL `opl_provider_runtime_manager` / `opl_family_runtime_provider`；MAS local scheduler surface 已物理退役为 tombstone/provenance refs，不再每 `300` 秒调用 MAS one-shot supervision tick，也不再暴露公开 status/remove/ensure command；Hermes gateway cron 只在显式 status/remove 时作为 legacy diagnostic cleanup adapter
- `MedAutoScience` 作为 tick-driven controller / read-model owner
- 新增 `study_progress` 作为只读 progress/watch/report projection

前台想要“持续有进度”，可以通过：

- CLI 轮询 `study-progress`
- MCP 调用 `study_progress`
- OPL provider/runtime manager 默认周期调用；显式 legacy local 只保留 tombstone/provenance，外部 executor adapter 只用于显式 proof lane、diagnostic 或旧 provenance path

来持续刷新前台时间线。控制面仍由现有 runtime/control surface 承担，前台只读投影负责解释当前状态和人类 gate 边界。

这不是旧 MDS resident daemon 的 1:1 行为复刻。默认在线监管 owner 是 OPL provider/runtime manager；MAS 只提供 domain supervision read model、owner receipt、typed blocker 和 direct/local 诊断投影。该组合能满足日常进度与恢复投影，但不会恢复 MDS WebSocket terminal streaming、connector background threads 或 in-memory session store。行为差异见 [MDS Behavior Equivalence Gap Matrix](../../references/mds-parity/mds_behavior_equivalence_gap_matrix.md)。

## 7. MAS Progress Portal 入口

Progress Portal 的开发合同见 [MAS Progress Portal](../display/progress_portal.md)。这里固定它和 `study_progress` 的关系：

- `study_progress.user_visible_projection` 是 Portal 和 OPL App-native MAS study workbench 的主要用户状态输入。
- `workspace-cockpit`、`product-entry-status`、MCP compact/markdown、Portal 和 OPL App workbench 应消费同一套 projection，而不是各自解释状态。
- 默认 Portal 产物是 `ops/mas/progress/index.html` 静态快照；它必须显示生成时间、freshness、stale/missing/conflict 状态和 source refs。
- 本仓不再提供 Progress Portal 本地实时服务；需要长期托管、刷新、跨域唤醒或统一状态面时，由 OPL App / OPL Runtime Manager 消费同一 read-model、HTML refs 和 OPL handoff refs。
- 旧 MDS WebUI 的可视化价值可以被吸收，但默认品牌、路径和用户可见语义必须是 `Med Auto Science`。
