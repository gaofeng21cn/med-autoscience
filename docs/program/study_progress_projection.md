# Study Progress Projection

这份文档冻结 `MedAutoScience` 侧“前台持续有进度”的正式落地方向。

一句话结论：

- 这里要做的是 `controller-owned progress projection`
- 不是第二个 authority daemon
- 也不是去读 `.ds/codex_history` 原始日志拼接一份“看起来有进度”的黑盒摘要

## 1. 目标

前台需要持续看到：

- 几点几分完成了什么
- 当前研究整体推进到哪一步
- 论文主线推进到哪一步
- 目前卡在什么地方
- 下一步系统准备做什么
- 是否已经到了必须由医生 / PI 判断的节点

这些信息必须以医生 / 医学专家能看懂的人话表达，而不是把 runtime 内部技术术语直接甩给前台。

当前“人话进度”不是拍脑袋总结，而是有固定来源：

- `runtime_supervision/latest.json` 的 `clinician_update`、`summary`、`next_action_summary`
- `runtime_watch` 的 controller scan 结果
- `publication_eval/latest.json` 的 verdict / gap summary
- `controller_decisions/latest.json` 的正式下一步决定
- `bash_exec summary` 与 `details projection` 提供的最近推进描述

## 2. Authority 边界

`study_progress` 的正式定位是：

- `controller-owned progress projection`
- 只读投影面
- 前台解释层

它不负责：

- 启动或停止 runtime
- 改写 study-level truth
- 越权触碰 runtime-owned surface
- 代替 `study_runtime_status` / `ensure_study_runtime`

所以它不是：

- 第二个常驻 daemon
- 第二个 authority controller
- 第二份 runtime truth

## 3. 输入表面

`study_progress` 的 authority 输入只读下列表面：

- `study_runtime_status`
- `studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json`
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `runtime_watch` 最新 report

允许吸收但不赋予 authority 的 enrichment surface：

- `quest_root/.ds/projections/details.v1.json`
- `quest_root/.ds/bash_exec/summary.json`

这里的关键约束是：

- canonical truth 仍来自 durable surface
- `study_runtime_status` 内的 `interaction_arbitration` 与 `continuation_state` 属于正式 typed status surface，可直接用于前台判断“这是用户阻塞，还是 MAS 已经仲裁为自动继续”
- `details` projection 与 `bash_exec` summary 只用于补充“最近完成了什么”“论文建议推进到哪一步”
- 不直接读 `.ds/codex_history` 原始事件流
- 只要 `runtime_supervision/latest.json` 报告 `recovering / degraded / escalated`，前台就必须优先展示 runtime health，而不是被论文阶段覆盖
- 只要 `study_runtime_status.supervisor_tick_audit` 报告 `missing / stale / invalid`，前台就必须明确表述“MAS 外环监管心跳异常”，不能继续把 study 写成被持续托管监管
- 即使宿主机尚无 external `Hermes` runtime，前台的人话进度也仍来自这些 MAS durable surface，而不是假装另有一个独立 Hermes host 已经在后台接管一切

## 4. 输出合同

`study_progress` 至少输出：

- `current_stage`
- `current_stage_summary`
- `paper_stage`
- `paper_stage_summary`
- `runtime_decision`
- `runtime_reason`
- `latest_events`
- `current_blockers`
- `next_system_action`
- `needs_physician_decision`
- `physician_decision_summary`
- `supervision`
- `refs`

其中：

- `current_stage` 表示当前整体研究推进阶段
- `paper_stage` 表示论文主线当前建议推进阶段
- `latest_events` 必须带明确时间戳
- `supervision` 至少包含 `browser_url`、`quest_session_api_url`、`active_run_id`、`launch_report_path`
- `supervision` 应同步暴露 `supervisor_tick_status`，用于前台解释当前是否仍有新鲜的 MAS 外环监管

前台 markdown / 线程回报的固定口径至少保持下面顺序：

1. 当前阶段
2. 论文推进
3. 运行监管
4. 当前阻塞
5. 下一步
6. 医生判断（仅在确实需要时出现）
7. 最近进展
8. 监督入口

## 5. 人话约束

面向医生 / 医学专家的前台文案必须遵守：

- 先说临床/研究含义，再说技术动作
- 避免把 `quest`, `projection`, `fingerprint`, `runtime reentry` 这类内部术语直接当主句
- 不能伪造百分比进度
- 不能把 bundle/build/proofing 误报成当前主线 next step；如果 `bundle_tasks_downstream_only=true`，就必须明确那是后续步骤
- 如果当前需要人工确认，必须直说“需要医生/PI 确认”，不能只写 `requires_human_confirmation=true`
- 如果 `interaction_arbitration.action == resume`，前台不得继续把原始 `pending_user_interaction` 误投影成“等待医生/PI 决策”
- 如果 `continuation_reason == unchanged_finalize_state` 且 MAS 已判定自动继续，前台必须把它表述成“系统接管 runtime 的本地 finalize 停车”，而不是“用户要不要继续”

## 6. 运行形态

`MedAutoScience` 自己没有必要因为这件事变成第二个常驻 authority daemon。

正确形态是：

- 保持 `MedDeepScientist` 作为常驻 inner runtime
- 保持 `MedAutoScience` 作为 tick-driven outer controller
- 新增 `study_progress` 作为只读 progress/watch/report projection

前台想要“持续有进度”，可以通过：

- CLI 轮询 `study-progress`
- MCP 调用 `study_progress`
- future automation / heartbeat 周期调用

来持续刷新前台时间线，而不是把整个控制面改写成第二个 daemon。
