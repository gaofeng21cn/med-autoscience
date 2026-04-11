# Med Autoscience 仓库协作规范

这个根目录 `AGENTS.md` 是仓库默认入口规范。直接从项目根进入的 Codex 会话，应先遵循这里，而不是先跳到更深层文档里找主规则。

## 适用范围

适用于仓库根目录及其子目录；如果更深层目录存在 `AGENTS.md`，则以更近者为准。

## 项目定位

- `MedAutoScience` 是共享 `Unified Harness Engineering Substrate` 上的医学 `Research Ops` domain gateway 与 `Domain Harness OS`，不是给人手工操作的零散脚本工具箱。
- 当前默认本地执行形态是 `Codex-default host-agent runtime`；当前 repo-tracked 产品主线按 `Auto-only` 理解。
- `MedDeepScientist` 是本仓库依赖的执行 surface，不是本仓库的系统本体。
- 人类负责设定研究目标、审核正式产物和做继续/停止决策；Agent 负责读取状态、推进执行并把关键判断写回可审计表面。

## 开发优先级

- 优先压实 `MedAutoScience -> MedDeepScientist` 的 runtime protocol、compatibility contract 与 adapter 退出边界。
- 优先通过 `policy -> controller -> overlay -> adapter` 主链路表达能力，不要把仓库退化回临时脚本集合。
- 优先保持本仓库作为独立的 `Research Ops` domain gateway，不要把 `OPL` 顶层 gateway 或某个底层 runtime 文件误写成它的替代物。
- 影响运行行为时，优先改 `profile / overlay / controller`，避免直接篡改 runtime core。

## 关键边界

- `program_id`、`study_id`、`quest_id`、`active_run_id` 各自承担不同身份，不能互相替代。
- `.codex/` 下的本地 handoff surface 不是 repo-tracked 产品 runtime truth。
- 当前 canonical durable surface 继续以 `study_runtime_status`、`runtime_watch`、`studies/<study_id>/artifacts/**`、`ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/**` 为准。
- gate 语义保持 fail-closed：`study_runtime_status -> runtime_escalation_record -> publication_eval/latest.json -> controller_decisions/latest.json -> controller action`。

## 工作树纪律

- Heavy 或长链路实现必须在基于当前 `main` 创建的独立 worktree 中完成。
- 共享根 checkout 保持在 `main`，只用于轻量读取、评审、吸收提交、push 和清理，不要把它变成长时间占用的 owner checkout。
- 如果需要多条长链路主线，就创建多个 worktree，不要靠 session 级隔离硬撑。
- 开始新 lane 前，确认 owner worktree 干净，没有陈旧本地 runtime 状态。
- lane 结束后，要么把已验证提交吸收到 `main`，要么明确放弃，并清理 worktree、分支和相关 tmux/session 状态。

## 测试面治理

- `make test-fast` 是默认开发测试面，必须排除 `meta` 和 `display_heavy`。
- `make test-meta` 与 `make test-display` 是显式 marker lane，不要再退回文件名启发式或把它们塞回默认 smoke。
- `make test-full` 是 clean-clone 基线与 release gate；repo-tracked 文档、workflow 与操作说明凡是指“全量验证”，都应指向它。
- 修改测试命令或 marker 分配时，要同步更新 `Makefile`、`pyproject.toml`、`README*`、CI/release workflow 与 command-surface tests。

## 文档与附录

- 根文档负责默认入口规则；`contracts/project-truth/AGENTS.md` 是更细的项目边界附录，不再是默认必读前置。
- `docs/documentation-governance.md` 是文档治理附录。公开文档保持双语，内部技术/规划文档默认中文。
- `docs/superpowers/` 只放本地 AI 工作过程文档，保持未跟踪。
- OMX 相关材料仅保留为历史参考，不再构成 active workflow 要求。

## 通用协作约束

- 保持 diff 小、可审查、可回退。
- 能删就别加；能复用现有模式就别新起抽象。
- 没有明确理由不要新增依赖。
- 完成前必须运行与改动相匹配的测试、类型检查和验证命令。
- 最终说明需要交代改了什么，以及还剩哪些风险或缺口。

## 本地状态

- `.codex/` 与 `.omx/` 都是本地工具状态，必须保持未跟踪。
- `.omx/` 仅保留历史残留，不再作为 active workflow 入口。
