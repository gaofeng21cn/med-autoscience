# MedAutoScience 仓库协作规范

## 适用范围

本文件适用于仓库根目录及其所有子目录；若更深层目录存在 `AGENTS.md`，以更近者为准。

## 项目定位

- `MedAutoScience` 是共享 `Unified Harness Engineering Substrate` 上的医学 `Research Ops` domain gateway 与 `Domain Harness OS`。
- 当前默认本地执行形态是 `Codex-default host-agent runtime`；当前 repo-tracked 主线按 `Auto-only` 理解。
- 当前 formal-entry matrix 固定为：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`。
- `MedDeepScientist` 是执行 surface，不是本仓库本体；本仓库负责 gateway、controller、overlay、adapter 与可审计 durable surface。

## 非目标

- 不把仓库退化回零散脚本和一次性操作手册集合。
- 不把 `.codex/` 或其他本地 handoff surface 冒充成 repo-tracked 产品真相。
- 不在 external runtime gate 未清除时提前做 physical migration 或跨仓大重构。

## 开发优先级

- 第一优先级：压实 `MedAutoScience -> MedDeepScientist` runtime protocol、compatibility contract 与 adapter 退出边界。
- 第二优先级：通过 `policy -> controller -> overlay -> adapter` 主链路表达能力，减少旁路。
- 第三优先级：把 runtime native truth convergence、workspace knowledge/literature convergence 与 controlled cutover 的顺序写清楚并守住。

## 主要入口与真相面

- 默认人类/AI 入口：`README.md`、`README.zh-CN.md`、`docs/README.md`、`docs/README.zh-CN.md`
- 稳定/长期规则：`docs/policies/README.md`、`docs/agent_runtime_interface.md`、`docs/runtime_handle_and_durable_surface_contract.md`
- 关键身份与 durable surface：`program_id`、`study_id`、`quest_id`、`active_run_id`；`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`
- `monorepo / runtime core ingest / controlled cutover` 仍是后置长线，不是当前默认实现入口。

## 文档规则

- `README*` 与 `docs/README*` 是默认对外与默认入口文档。
- 公开文档保持中英双语；内部技术、规划、备忘文档默认中文。
- `docs/policies/` 放稳定规则，`docs/history/omx/` 放 OMX 历史资料索引，`docs/superpowers/` 放本地 AI 过程文档并保持未跟踪。
- 任何新文档都要先判断它属于公开入口、稳定规则、参考资料还是历史归档，不要混放。

## 变更与验证

- 保持 diff 小、可审查、可回退。
- 能删就别加；能复用现有模式就别新起抽象。
- 没有明确必要不要新增依赖。
- 修改 formal-entry、command surface、marker/test lane、runtime handle 或 durable surface 语义时，必须同步改 README、docs、测试与相应实现。
- 默认测试入口：`make test-fast`；`make test-meta`、`make test-display` 是显式 lane；`make test-full` 是 clean-clone 基线。

## 并行开发与工作树

- 大改动、长链路工作、并行多 AI 开发，默认先从当前 `main` 开独立 worktree，再在 worktree 内实现和验证。
- 共享根 checkout 只用于轻量阅读、评审、吸收验证后提交、push 和清理，不应长期承担重型实现。
- 需要多条 lane 时创建多个 worktree，不要把多条长线塞进同一工作目录。

## 本地状态

- `.codex/` 与 `.omx/` 都是本地工具状态，必须保持未跟踪。
- `.omx/` 仅允许作为历史残留存在，不得再作为当前 workflow 入口。
