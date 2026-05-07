# Study Progress Projection

这份文档冻结 `MedAutoScience` 侧“前台持续有进度”的正式落地方向。

核心结论：

- `study_progress` 是 `controller-owned progress projection`
- 用户可见状态只从 `study_macro_state` 派生
- 前台判断围绕同一条 study authority 展开，不再各入口自行拼装 runtime / publication / controller 细节

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
- `runtime_watch` 的 controller scan 结果
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

- `study_runtime_status`
- `studies/<study_id>/artifacts/controller/task_intake/latest.json`
- `studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json`
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `studies/<study_id>/artifacts/controller/controller_confirmation_summary.json`
- `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- legacy diagnostic reference: `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `runtime_watch` 最新 report

允许吸收但不赋予 authority 的 enrichment surface：

- legacy enrichment: `quest_root/.ds/projections/details.v1.json`
- legacy enrichment: `quest_root/.ds/bash_exec/summary.json`

这里的关键约束是：

- canonical truth 仍来自 durable surface
- `study_runtime_status` 内的 `interaction_arbitration` 与 `continuation_state` 属于正式 typed status surface，可直接用于前台判断“这是用户阻塞，还是 MAS 已经仲裁为自动继续”
- legacy `details` projection 与 `bash_exec` summary 只用于补充“最近完成了什么”“论文建议推进到哪一步”，不得作为 active quest lifecycle 或 publication authority
- `.ds/codex_history` 原始事件流只保留给审计和调试场景；新 quest 不依赖 `.ds`、MDS Git 或 `.ds/worktrees` 维护前台进度
- 只要 `runtime_supervision/latest.json` 报告 `recovering / degraded / escalated`，前台就必须优先展示 runtime health，论文阶段在展示顺序上后置
- 只要 `study_runtime_status.supervisor_tick_audit` 报告 `missing / stale / invalid`，前台就必须明确表述“MAS 外环监管心跳异常”，并停止使用“持续托管监管”口径
- 即使宿主机尚无 external `Hermes` runtime，前台的人话进度也固定来自这些 `MAS` durable surface；外部 runtime substrate 的状态按实际已验证接入情况描述

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
- `latest_events` 必须带明确时间戳
- `autonomy_soak_status` 用于表达最近一次已被 durable surface 记录的自治续跑 / outer-loop dispatch，至少要能回答“系统自动转去了哪条线、关键问题是什么、下一次确认看什么、证据引用在哪里”
- `autonomy_contract.restore_point` 是恢复点与 human gate 的前台真相；调用方应读取其中的 `human_gate_required` 与 `summary`，不要从泛化 blocker 推断恢复许可
- `quality_closure_truth` / `quality_review_followthrough` 分别表达质量闭环裁决与复评后的跟进状态，用于和 `autonomy_soak_status` 一起解释“系统是否仍在同线自动收口”
- `research_runtime_control_projection` 是给 `workspace-cockpit`、`product-entry-status`、`build-product-entry` 和上层 gateway 消费的控制投影；它必须把 `restore_point_surface`、`artifact_pickup_surface.pickup_refs`、`command_templates` 与 `research_gate_surface` 固定到同一条 `study-progress` 字段路径上
- `needs_physician_decision` 只在触达正式人类 gate 边界时为 true
- `physician_decision_summary` 必须说明触达的是初始方向锁定、重大转向、止损、外部凭据/秘密、投稿客观信息或最终投稿前审计中的哪一类
- `supervision` 至少包含 `browser_url`、`quest_session_api_url`、`active_run_id`、`launch_report_path`
- `supervision` 应同步暴露 `supervisor_tick_status`，用于前台解释当前是否仍有新鲜的 MAS 外环监管

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
- `止损/终止`：当前论文线不再自动推进，需新计划或明确重开。

入口层规则：

- MCP compact / markdown、CLI markdown、`workspace-cockpit`、workspace alerts 和 product-entry-status preview 必须读取 schema v2 `user_visible_projection`。
- 缺少 v2 `user_visible_projection` 时，入口只允许通过 assembly/read-model 层用 `study_macro_state` 生成；缺 `study_macro_state` 或发现 writer 冲突时必须 fail-closed 为 `inspect/conflict`，提示重新生成 canonical projection。
- 入口不得回退到 legacy top-level `current_stage/current_blockers/next_system_action` 作为用户状态来源。
- `user_visible_projection.conditions` 只表达 projection 状态，例如 `macro_state_known`、`package_delivered`、`actual_write_active`、`blocked`、`next_action_known`、`evidence_available`、`user_action_required`、`runtime_supervised`；不得作为 runtime write gate 或 publication quality authority。
- `evidence.refs` 只保存可审计引用路径；任何质量关闭、投稿授权、runtime 写操作仍回到 `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status` 和对应 controller surface。

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

- 保持 `MedDeepScientist` 作为常驻 inner runtime
- 保持 `MedAutoScience` 作为 tick-driven outer controller
- 新增 `study_progress` 作为只读 progress/watch/report projection

前台想要“持续有进度”，可以通过：

- CLI 轮询 `study-progress`
- MCP 调用 `study_progress`
- future automation / heartbeat 周期调用

来持续刷新前台时间线。控制面仍由现有 runtime/control surface 承担，前台只读投影负责解释当前状态和人类 gate 边界。
