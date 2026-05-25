# Managed Runtime User Notice Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

## Goal

把下面这条规则提升为 `MedAutoScience` 的正式 contract，而不是依赖单次会话中的人工记忆：

- 当 agent 发现某个 study 已处于 live managed runtime 时，必须显式通知用户
- 通知必须包含监督入口，而不是只说“后台在跑”
- 这条规则适用于“本次 controller 刚把 quest 推进到 live”以及“agent 接管时 quest 已经在 live”两种情形

## Design

新增一个稳定 surface：`autonomous_runtime_notice`

出现条件：

- execution engine 为 `med-deepscientist`
- study 属于 managed runtime 路径
- quest 当前处于 live runtime 状态

payload 最小 shape：

```json
{
  "required": true,
  "notice_key": "quest:<quest_id>:<active_run_id-or-quest_status>",
  "notification_reason": "detected_existing_live_managed_runtime|managed_runtime_started|managed_runtime_resumed",
  "quest_id": "002-dm-china-us-mortality-attribution",
  "quest_status": "running",
  "active_run_id": "run-xxxx",
  "browser_url": "http://127.0.0.1:20999",
  "quest_api_url": "http://127.0.0.1:20999/api/quests/<quest_id>",
  "quest_session_api_url": "http://127.0.0.1:20999/api/quests/<quest_id>/session",
  "monitoring_available": true,
  "monitoring_error": null,
  "launch_report_path": "/abs/path/to/studies/<study_id>/artifacts/runtime/last_launch_report.json"
}
```

## Injection Points

1. `study_runtime_status(...)`

- 当 controller 读到 live managed runtime 时，直接把 `autonomous_runtime_notice` 暴露在返回 payload 中
- 这样 agent 即使接管到一个已经在跑的 quest，也能立即补发通知

2. `ensure_study_runtime(...)`

- 复用同一 notice surface
- 若本次执行把 quest 推到 live，则 `notification_reason` 应体现 `started` 或 `resumed`

3. `studies/<study_id>/artifacts/runtime/last_launch_report.json`

- 把同一 notice surface durable 落盘
- 让人类与上层 agent 都能从同一个可审计表面读取监督入口

4. `automation_ready` policy 与 workspace rules

- 明确：自动推进不仅意味着 controller 可以创建/恢复 quest，也意味着 agent 必须向用户显式报告自动驾驶已启动或已检测到

## Boundary

- 平台只负责暴露 machine-readable notice surface
- 上层 agent 负责真的向用户发出显式通知
- 平台不追踪“用户是否已读”这类 chat truth，不新增 notification receipt artifact

## Verification

- `study_runtime_status(...)` 在 existing live quest 上返回 `autonomous_runtime_notice`
- `ensure_study_runtime(...)` 在 live quest 上返回 `autonomous_runtime_notice`
- `last_launch_report.json` 持久包含 `autonomous_runtime_notice`
- workspace rules 文案包含“显式通知用户并提供监督入口”
