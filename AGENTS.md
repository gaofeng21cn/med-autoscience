# AGENTS 只管工作方式

## 适用范围

本文件适用于仓库根目录及其所有子目录；若更深层目录存在 `AGENTS.md`，以更近者为准。

## 工作方式

- 保持变更可审查、可回退，避免不必要的大范围改动。
- 能删就别加；能复用现有模式就别新起抽象；没有明确必要不要新增依赖。
- 不采用降级处理、兜底方案、临时补丁、启发式方法、局部稳定化手段，避免以非严谨通用算法的后处理补救作为主策略。
- repo-tracked 源码与测试默认都应保持文件边界清晰，优先控制在 `1000` 行以内；超过 `1500` 行应视为明确的拆分信号，而不是继续堆叠实现。
- 新增能力或继续重构时，优先采用稳定薄入口加 `parts/`、`cases/`、`modules/` 等子模块拆分；不要把新逻辑继续堆回单个超长文件。
- 若文档提到 `Hermes-Agent`，只能指上游外部 runtime 项目 / 服务；仓内的 seam、shim、adapter 或过渡 scaffold，不得写成“已接入 Hermes-Agent”。
- 一旦目标 runtime topology 已明确，新增投入默认服务目标形态；旧 substrate 只允许作为迁移桥、兼容层或回归基线存在。
- `family shared modules / shared boundary refactor` 是当前允许推进的 lane；它服务四仓复用、shared helper 收口与 future monorepo readiness。
- external runtime gate、workspace / human gate 与对象边界仍然约束 `physical migration / monorepo absorb / runtime core ingest / controlled cutover`；`monorepo / runtime core ingest / controlled cutover` 继续作为后置长线推进。

## 运行语义一致性

为保持 repo-tracked contract 与文档一致性，以下术语必须在变更中保持一致：

- 运行形态：`Codex-default host-agent runtime`、`CLI`、`MCP`、`controller`、`Auto-only`
- 关键身份：`program_id`、`study_id`、`quest_id`、`active_run_id`
- durable surface：`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`

## 文档骨架（核心五件套）

以下五份是 docs 的稳定核心，保持在 `docs/` 根目录：

- `docs/project.md`
- `docs/architecture.md`
- `docs/invariants.md`
- `docs/decisions.md`
- `docs/status.md`

## 文档分类

- `README*` 与 `docs/README*` 是默认对外与默认入口文档。
- 对外文档保持中英双语；内部技术、规划、备忘文档默认中文，除非明确提升到双语公开面。
- `docs/capabilities/`：能力族/专题面（如 medical display）。
- `docs/program/`：tranche、freeze、hardening、cleanup、intake 等程序阶段材料。
- `docs/runtime/`：接口、控制面、合同/控制语义。
- `docs/references/`：背景、定位、审计与非活跃参考。
- `docs/history/`：历史归档，仅作历史参考入口。
- `docs/policies/`：稳定内部规则，默认中文维护。
- `docs/superpowers/`：存量 repo-tracked 历史设计材料可保留为内部档案；新增本地 AI/Superpowers 过程草稿默认保持未跟踪。

## 本地工具状态

- 项目级 `.codex/` 与 `.omx/` 已退役，不再作为仓库本地状态入口。
- 如需保留历史 session、prompt、log 或 hook 状态，应迁入用户级 `~/.codex/` 归档。

## Worktree 规则

- 大改动、长链路工作、并行多 AI 开发，默认先从当前 `main` 开独立 worktree，在 worktree 内实现和验证。
- 共享根 checkout 只用于轻量阅读、评审、吸收验证后提交、push 和清理。
- 需要多条 lane 时创建多个 worktree，不要把多条长线塞进同一工作目录。
- worktree 内实现和验证完成后，应尽快吸收回 `main`，并清理对应 worktree、分支与临时状态。

## 验证规则

- 统一验证入口：`scripts/verify.sh`。
- 默认最小验证：`scripts/verify.sh`（内部运行 `make test-fast`）。
- full lane：`scripts/verify.sh full`（内部运行 `make test-full`）。
- 修改 docs/contract surface 或运行语义时，至少补跑 `make test-meta`。
