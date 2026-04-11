# 架构概览

## 主链路

仓库的能力表达遵循 `policy -> controller -> overlay -> adapter` 主链路，避免旁路把临时状态升级为真相。关键运行语义以 contract 形式固化在 repo-tracked 文档与代码里，再由 controller 负责执行与审计。

当前 runtime 拓扑固定为：

- `MedAutoScience`：唯一研究入口、research gateway、study/workspace/outer-loop authority owner
- `Hermes`：外层 runtime substrate owner，负责 backend-generic runtime contract、runtime handle 与 durable surface
- `MedDeepScientist`：controlled research backend，保留当前仍需由 research runtime 承担的 backend execution 能力

旧 `Codex-default host-agent runtime` 不再是长期产品 runtime 深化方向，只保留为迁移期对照面。

## 入口与控制面

- 默认正式入口：`CLI`
- 支持协议层：`MCP`
- 内部控制面：`controller`

入口只描述 Agent 进入 runtime 的方式，不改变 repo-tracked 主线的 `Auto-only` 定义。

## 权威与 durable surface

可审计真相必须落在 repo-tracked contract 与明确的 durable surface。关键身份与运行面包括：

- `program_id`、`study_id`、`quest_id`、`active_run_id`
- `study_runtime_status`、`runtime_watch`
- `publication_eval/latest.json`
- `runtime_escalation_record.json`
- `controller_decisions/latest.json`

具体 contract 以运行层文档为准，例如：

- `runtime/agent_runtime_interface.md`
- `program/med_deepscientist_deconstruction_map.md`
- `runtime/runtime_handle_and_durable_surface_contract.md`
- `runtime/study_runtime_control_surface.md`
- `runtime/delivery_plane_contract_map.md`

## 能力族与程序材料

- 能力族/专题面收口到 `docs/capabilities/`（例如 medical display 系列）。
- tranche、freeze、hardening、cleanup、intake 等程序材料收口到 `docs/program/`。
- 背景、定位、审计与非活跃参考收口到 `docs/references/`。
