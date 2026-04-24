---
name: med-autoscience
description: Use when Codex should operate MedAutoScience through its stable runtime, controller, overlay, and workspace contracts instead of ad-hoc scripts.
---

# MedAutoScience App Skill

当 Codex 需要通过稳定运行面操作 `MedAutoScience`，而不是把仓库当成临时脚本集合来直接拼装时，使用这个 app skill。

## 这个 app skill 是什么

- `MedAutoScience` 面向 Codex 的单一 domain app skill
- 叠加在现有 Python package、CLI、controller、overlay 与 workspace profile 之上
- 不替代 `medautosci` CLI、controller contract，也不替代非 Codex 集成
- skill 入口只有一个；`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress`、`product-frontdesk` 等命令是这个 app skill 的内部 command contract
- `OPL` handoff、product-entry manifest 和其他机器可读桥接属于集成层，不是这个 skill 的前台主语

## 核心规则

优先走已有的 `MedAutoScience` 运行时 contract：

- 如果 workspace 还不存在，优先调用 MCP tool `init_workspace`
- `medautosci workspace init`
- `medautosci doctor report --profile <profile>`
- `medautosci doctor profile --profile <profile>`
- `medautosci workspace bootstrap --profile <profile>`
- `medautosci runtime watch --runtime-root <runtime-root>`
- `medautosci runtime overlay-status --profile <profile>`
- `medautosci runtime install-overlay --profile <profile>`
- `medautosci doctor backend-upgrade --profile <profile> --refresh`
- `medautosci-mcp`

如果 `medautosci` 不在 `PATH` 上，用模块入口：

```bash
uv run python -m med_autoscience.cli doctor report --profile <profile>
```

## 操作约束

- 任何写操作之前，先读 workspace 当前状态
- 对 `study_runtime_status` 或 `ensure_study_runtime` 的返回，必须检查 `autonomous_runtime_notice`
- 对 `study_runtime_status.execution_owner_guard` 或同名 payload，必须把它当作当前 study 的执行所有权真相源
- 对 `study_runtime_status.publication_supervisor_state` 或同名 payload，必须把它当作论文当前全局阶段的真相源
- 只要 `autonomous_runtime_notice.required=true`，就表示该 study 已处于 live managed runtime；无论是本次刚启动，还是接管到已在运行的 quest，都必须立刻显式通知用户
- 通知里必须给出可监督入口，至少包括 `browser_url`；如果返回了 `quest_session_api_url` 和 `active_run_id`，也要一并告诉用户
- 只要 `execution_owner_guard.supervisor_only=true`，前台就必须进入 supervisor-only 监管态，不得继续直接推进 study-local 执行
- 在 supervisor-only 状态下，不得直接写入 `execution_owner_guard.runtime_owned_roots` 覆盖的 runtime-owned surface；如需人工接管，先显式暂停 runtime
- 不允许在已检测到 live managed runtime 的情况下继续隐式推进对话而不告知用户自动驾驶已经在运行
- 只要 `publication_supervisor_state.bundle_tasks_downstream_only=true`，就不得把 paper bundle 缺件表述成当前 next step；必须明确说明那只是后续件，待 `publication_gate` 放行后再做
- 只要 `publication_supervisor_state.bundle_tasks_downstream_only=true`，就把 bundle/build/proofing 当作硬阻断，不得在前台抢跑
- 当 `paper_contract_health` 给出 `recommended_next_stage` / `recommended_action` 时，默认只把它们解释为 paper-line local recommendation，除非 `publication_supervisor_state` 已明确进入对应全局阶段
- 数据资产变更要走 controller 命令和结构化 payload，不直接手改 registry
- 保持 `MedAutoScience` 作为运行层，不要把 controller、profile、overlay、workspace 逻辑塌缩进 plugin 私有文件
- 保持 CLI 和 controller 入口稳定，避免破坏其他 Agent 的兼容性
- plugin-local MCP 依赖 `medautosci-mcp` 在 `PATH` 上可用
- 旧 `med-deepscientist-*` overlay 目录名和 `doctor med-deepscientist-upgrade` 只保留为 internal compatibility surface

## 首先应读的文件

- `bootstrap/README.md`
- `controllers/README.md`
- `docs/references/codex_plugin.md`

## 典型任务

- 审核某个 workspace profile 是否接对
- 为新的病种 workspace 建立骨架并接入 Codex 驱动执行
- 检查 overlay 是否漂移，必要时重覆写
- 运行 runtime watch 并归纳阻塞点
- 通过可审计命令驱动数据资产和投稿交付 controller
