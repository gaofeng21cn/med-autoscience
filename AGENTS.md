# AGENTS 只管工作方式

## 适用范围

本文件适用于仓库根目录及其所有子目录；若更深层目录存在 `AGENTS.md`，以更近者为准。

## 工作方式

- 保持变更可审查、可回退，避免不必要的大范围改动。
- 能删就别加；能复用现有模式就别新起抽象；没有明确必要不要新增依赖。
- 不采用降级处理、兜底方案、临时补丁、启发式方法、局部稳定化手段，避免以非严谨通用算法的后处理补救作为主策略。
- external runtime gate 未清除前，不做 physical migration 或 cross-repo refactor。
- `monorepo / runtime core ingest / controlled cutover` 是后置长线，不作为当前默认实施入口。

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
- `docs/history/omx/`：OMX 历史归档，仅作历史参考入口。
- `docs/policies/`：稳定内部规则，默认中文维护。
- `docs/superpowers/`：本地 AI/Superpowers 过程文档，保持未跟踪。

## Worktree 规则

- 大改动、长链路工作、并行多 AI 开发，默认先从当前 `main` 开独立 worktree，在 worktree 内实现和验证。
- 共享根 checkout 只用于轻量阅读、评审、吸收验证后提交、push 和清理。
- 需要多条 lane 时创建多个 worktree，不要把多条长线塞进同一工作目录。

## 验证规则

- 统一验证入口：`scripts/verify.sh`。
- 默认最小验证：`scripts/verify.sh`（内部运行 `make test-fast`）。
- full lane：`scripts/verify.sh full`（内部运行 `make test-full`）。
- 修改 docs/contract surface 或运行语义时，至少补跑 `make test-meta`。

## `.omx` 历史残留规则

- `.omx/` 仅允许作为历史残留存在，必须保持未跟踪，不得再作为当前 workflow 入口。
- OMX 相关材料只能落在 `docs/history/omx/` 作为历史参考，不得被当作当前流程主入口。
