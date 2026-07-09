# Codex Plugin 接入

Owner: `MedAutoScience`
Purpose: `Support MAS integration and OPL handoff understanding.`
State: `support_reference`
Machine boundary: Human-readable integration reference only; callable and generated-surface truth remains in manifests, contracts, source, tests, OPL handoff contracts, and read-model output.

`MedAutoScience` 现在可以通过仓库内置的 Codex plugin 暴露给 Agent，路径在 `plugins/med-autoscience/`。

本文件同时承接原 `codex_plugin_release.md` 的发布说明口径。当前叙事以 repo-tracked plugin source / skill / MCP 入口为准，不再把 MAS standalone release artifact、系统级 skill 安装或 repo-local marketplace 写成默认用户路径。

## 这个 plugin 增加了什么

- 通过 `.codex-plugin/plugin.json` 提供 Codex 可发现、可安装的入口
- 提供一层 plugin skill，让 Codex 通过稳定接口操作 `MedAutoScience`
- 保留 `plugins/med-autoscience/bin/medautosci-mcp` 作为显式 direct / proof lane；默认 Codex App 可见 MCP 能力由 OPL family registry / generated descriptor 统一投影，不由 MAS plugin manifest 单独暴露

## 这个 plugin 不替代什么

- 不替代 Python package
- 不替代 `medautosci`
- 不替代 controller contract
- 不取消 profile 驱动的 workspace 绑定
- 不改变 medical research overlay 的安装模型
- 不会把外部 `MedDeepScientist` 安装成默认运行依赖；只有显式 backend audit、legacy restore/import diagnostic、upstream intake 或 parity oracle 才需要指向外部 checkout

## 兼容性边界

这个 plugin 是增量层，不是分叉运行时。其他框架仍然应通过原有接口接入：

- Python package: `med_autoscience`
- CLI: `medautosci`
- Controllers: `src/med_autoscience/controllers/`
- Overlay installer: `src/med_autoscience/overlay/installer.py`

只要这些接口保持稳定，Codex plugin 的存在就不会降低其他 Agent 或 wrapper 的兼容性。

Compatibility note:
- It does not replace `medautosci`
- It does not reduce compatibility with non-Codex agents or wrappers

## Agent-first 推荐用法

1. 如果还没有病种级 workspace，优先走 OPL generated surface 或 MAS CLI 初始化；只有显式接入 `medautosci-mcp` direct lane 时才调用 MCP tool `init_workspace`
2. 用 `profiles/*.local.toml` 绑定具体 workspace
3. 先跑 `doctor report` 或 `doctor profile`，确认路径、profile 和 overlay 策略
4. 再跑 `workspace bootstrap`，初始化 overlay 和数据资产状态
5. 后续涉及状态更新时，优先走 controller / MCP / CLI，不直接手改 registry

新 workspace 默认 no root Git / no quest Git。Codex 通过 MAS skill 查状态、恢复 runtime 或执行 lifecycle 操作时，优先读取 file authority、`artifacts/runtime/runtime_lifecycle.sqlite`、`artifacts/runtime/lifecycle_migration` ledger、`runtime/quests` manifest 和 `runtime/restore_index`；不要用 Git history、Git diff/log、workspace root Git 或 quest `.git` 作为默认状态来源。legacy Git 只通过显式 restore/import diagnostic 读取。

当前最重要的几条入口面：

- MCP tool: `init_workspace`
- CLI: `medautosci workspace init`
- CLI: `medautosci doctor report --profile <profile>`
- CLI: `medautosci doctor profile --profile <profile>`
- CLI: `medautosci workspace bootstrap --profile <profile>`
- CLI: `medautosci runtime domain-diagnostic-report --runtime-root <runtime-root>`
- CLI: `medautosci runtime domain-diagnostic-report --profile <profile> --studies <study_id>... --request-opl-stage-attempts --request-opl-paper-mission-owner-surface --apply`
- CLI: `medautosci runtime overlay-status --profile <profile>`
- CLI: `medautosci doctor backend-upgrade --profile <profile> --refresh`

`runtime domain-diagnostic-report` 没有 `--format` 参数，输出固定为 JSON。它是 developer-supervisor exact lane 消费 OPL terminal attempt closeout、刷新 current-control 并推导 next work unit 的 controller 入口；`study progress --format json` 是读面，不消费 closeout。普通监督先用 `--request-opl-stage-attempts --dry-run` 做只读探针；只有当前 study scope、fingerprint 和写边界已明确时，才加 `--request-opl-paper-mission-owner-surface --apply`。

## Live Runtime Guard

当 `progress-projection`、`launch-study` 或 OPL `current_control_state` 返回 `execution_owner_guard.supervisor_only = true` 时，Codex 前台必须切换成 supervisor-only 模式：

- 只负责读取状态、通知用户、提供监督入口和接收 pause/resume/stop/takeover 决策
- 不继续直接推进 study-local 写作、bundle、proofing、review 或编译链
- 不直接写入 runtime-owned surface

如果同时 `publication_supervisor_state.bundle_tasks_downstream_only = true`，则 bundle/build/proofing 在语义上仍属后续件，前台不得抢跑。

## 当前安装状态与发布口径

仓库里存在 plugin 文件，不等于 Codex 已经全局启用它。MAS skill 默认随本仓库工作目录发现，不应安装到系统级 skill 目录。

- 仓库内状态：plugin source 由 `plugins/med-autoscience/.codex-plugin/plugin.json` 和 `plugins/med-autoscience/skills/med-autoscience/SKILL.md` 维护；`plugins/med-autoscience/bin/medautosci-mcp` 只保留为 direct / proof lane launcher，不写入 Codex plugin manifest 的 `mcpServers`。
- 退役状态：repo-local `.agents/plugins/marketplace.json` 是 retired local-state surface；MAS 仓库不再跟踪、生成或写回它。
- CLI 安装：仓库不再维护专用 installer 或 home-local wrapper；`medautosci` 与 `medautosci-mcp` 由 `pyproject.toml` 的标准 console scripts 声明，独立 CLI 安装使用 `uv tool install --force .`。`mas` 是 plugin / series agent id，不是本机 PATH readiness 证据；macOS 上 `mas` 常是 Mac App Store CLI。
- Codex marketplace source：由 OPL-owned wrapper / startup maintenance 维护，不由 MAS domain repo 维护。修改 `plugins/med-autoscience/**` 后，通过 OPL-owned plugin sync surface 重新物化 med-autoscience marketplace；Codex plugin cache 仍旧时需要刷新/重启 Codex App。
- 发布状态：Codex plugin 是薄入口，不是新的运行核心，也不是 MAS standalone GitHub Release / installer 通道。

因此，仓库内置 plugin 和整机可用 plugin 不是一回事。

## 在另一台电脑上使用

标准路径是：

1. clone 本仓库
2. 安装 Python CLI：

   ```bash
   uv tool install --force .
   ```

3. 通过 OPL 物化 Codex carrier，并刷新 plugin cache：

   ```bash
   opl connect sync-skills --domain mas
   opl system startup-maintenance
   ```

4. 重启 Codex App，让更新后的 plugin cache 重新加载

然后确保 `medautosci-mcp` 仍然在 `PATH` 上。不要把 MAS/MDS 这类任务 skill 复制到 home-local 或系统级 skill 目录，也不要在 MAS 仓库恢复 `.agents/plugins/marketplace.json` 或 `plugins/mas`；需要 Codex marketplace 注册时，通过 OPL-owned wrapper 处理。需要研究运行时，应通过仓库内 `plugins/med-autoscience/` 与当前 workspace 初始化面发现。

这些入口只安装 `MedAutoScience` 的 CLI 与 plugin / skill / MCP carrier，不会顺带安装 `MedDeepScientist` runtime。研究 workspace 的 Python 依赖由 workspace `pyproject.toml` 中的 `med-autoscience[analysis]` 与 `uv sync` 管理；R/Python runtime profile 的长期 provisioning owner 是 OPL `env prepare`，MAS 只保留依赖声明与 readback。

## 作用边界

这个 plugin 只是薄入口层，真正的医学研究运行层仍然是 `MedAutoScience` 本体。
