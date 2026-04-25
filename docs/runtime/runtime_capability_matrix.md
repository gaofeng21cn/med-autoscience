# Runtime Capability Matrix

这份 contract 学习 `DeepScientist` 的 runner / settings / admin health surfaces，但在 `MAS` 中只固定 runtime capability 与 doctor 投影，不扩展 provider 主线。

## 目标

`MAS` 需要知道当前 runtime backend 能不能承担长时间医学研究，而不是只知道某个 binary 是否存在。

每个 backend 至少投影以下能力：

- `backend_id`
- `transport_owner`
- `default_runner`
- `mcp_ready`
- `long_running_tool_timeout_sec`
- `supports_pause_resume`
- `supports_user_message_queue`
- `supports_artifact_inventory`
- `supports_workspace_file_refs`
- `doctor_status`
- `blocking_reasons`

## 后端分类

- `codex_default_host_agent_runtime`：默认本机 Codex path，承担 MAS 直接运行语义。
- `med_deepscientist_backend`：迁移期 research backend、behavior oracle、upstream intake buffer。
- `hermes_optional_hosted_runtime`：可选 hosted runtime target / reference layer。

## Doctor 规则

runtime doctor 不应只返回 pass/fail。它必须说明：

1. MCP 是否能启动并维持 long-running tool timeout。
2. pause / resume / stop 是否有 daemon path。
3. user message queue 是否有 durable mailbox surface。
4. artifact inventory 和 workspace file refs 是否能投影到用户面。
5. 当前 blocker 是配置、凭据、backend 不可达、timeout，还是 contract 不支持。

## Timeout 规则

长时间研究默认需要宽松 timeout。降低 timeout 必须有明确理由，并且不得破坏：

- long-running bash / analysis task
- artifact refresh
- publication package rebuild
- runtime watch / outer-loop wakeup

## 不吸收范围

本 contract 不要求 MAS 追随 upstream 的 Claude、Kimi、OpenCode provider 扩面。它只吸收“backend capability 应被显式投影和验证”的思路。
