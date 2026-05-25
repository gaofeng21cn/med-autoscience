# Runtime Capability Matrix

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime projection and read-model semantics for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable projection support only; projection truth remains in source, tests, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这份 contract 学习 `DeepScientist` 的 runner / settings / admin health surfaces，但在 `MAS` 中只固定 runtime capability 与 doctor 投影，不扩展 provider 主线，也不把 MAS 提升为 generic runtime owner。

## 目标

`MAS` 需要知道当前 runtime backend 能不能承担长时间医学研究，而不是只知道某个 binary 是否存在。

每个 runtime capability item 至少投影以下能力：

- `capability_id`
- `transport_owner`
- `executor_kind`
- `provider_owner`
- `mcp_ready`
- `long_running_tool_timeout_sec`
- `supports_pause_resume`
- `supports_user_message_queue`
- `supports_artifact_inventory`
- `supports_workspace_file_refs`
- `doctor_status`
- `blocking_reasons`

## Provider / executor 分类

- `opl_provider_backed_stage_runtime`：默认 hosted autonomous runtime。`provider_owner=one-person-lab`，production online substrate 为 OPL/Temporal；MAS 只消费 `current_control_state`、provider attempt refs、typed closeout、owner receipt 或 typed blocker。
- `codex_cli`：当前第一公民 Agent executor kind。它可以作为 direct MAS path 或 OPL provider-backed stage 内的 executor，但不能写成 MAS 自持 scheduler / queue / worker residency。
- `med_deepscientist_backend`：历史 fixture、explicit archive/import、backend audit、upstream intake buffer 与 parity oracle reference；不作为 MAS 默认 backend。
- `hermes_agent`：上游外部 executor / diagnostic / provenance reference，可经显式 adapter 进入 proof lane；不作为 MAS 生产 online substrate，也不替代 OPL/Temporal provider。

## Doctor 规则

runtime doctor 不应只返回 pass/fail。它必须说明：

1. OPL `current_control_state` 或 explicit direct path 是否提供当前 attempt / owner refs。
2. pause / resume / stop 是 OPL runtime owner handoff、MAS typed blocker，还是历史 diagnostic/provenance。
3. user message / approval / wakeup 是否有 durable OPL transport 或 MAS owner-route refs。
4. artifact inventory 和 workspace file refs 是否能投影到用户面，且不会被提升为 artifact authority。
5. 当前 blocker 是配置、凭据、provider 不可达、timeout、owner receipt 缺失，还是 contract 不支持。

## Timeout 规则

长时间研究默认由 OPL provider-backed stage runtime 承担，MAS projection 只显示 timeout 能力和 blocker refs。降低 timeout 必须有明确理由，并且不得破坏：

- long-running bash / analysis task
- artifact refresh
- publication package rebuild
- runtime watch / outer-loop wakeup

## 不吸收范围

本 contract 不要求 MAS 追随 upstream 的 Claude、Kimi、OpenCode provider 扩面，也不要求 MAS 私有接管 Temporal / queue / retry-dead-letter / worker residency。它只吸收“runtime capability 应被显式投影和验证”的思路；provider truth 继续归 OPL，domain truth 与 authority refs 继续归 MAS。
