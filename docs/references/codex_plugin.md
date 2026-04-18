# Codex Plugin 接入

`MedAutoScience` 现在可以通过仓库内置的 Codex plugin 暴露给 Agent，路径在 `plugins/med-autoscience/`。

如果想看更高层的发布说明，可参考 [codex_plugin_release.md](codex_plugin_release.md)。

## 这个 plugin 增加了什么

- 通过 `.codex-plugin/plugin.json` 提供 Codex 可发现、可安装的入口
- 通过 `.agents/plugins/marketplace.json` 提供本仓库内的 plugin 市场元数据
- 提供一层 plugin skill，让 Codex 通过稳定接口操作 `MedAutoScience`
- 提供 `plugins/med-autoscience/.mcp.json`，让 Codex 直接接入 `medautosci-mcp`

## 这个 plugin 不替代什么

- 不替代 Python package
- 不替代 `medautosci`
- 不替代 controller contract
- 不取消 profile 驱动的 workspace 绑定
- 不改变 `MedDeepScientist` overlay 的安装模型
- 不会替你安装 `MedDeepScientist`；研究运行前仍需本机准备 `med-deepscientist` 并在 profile 中配置

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

1. 如果还没有病种级 workspace，优先调用 MCP tool `init_workspace`
2. 用 `profiles/*.local.toml` 绑定具体 workspace
3. 先跑 `doctor report` 或 `doctor profile`，确认路径、profile 和 overlay 策略
4. 再跑 `workspace bootstrap`，初始化 overlay 和数据资产状态
5. 后续涉及状态更新时，优先走 controller / MCP / CLI，不直接手改 registry

当前最重要的几条入口面：

- MCP tool: `init_workspace`
- CLI: `medautosci workspace init`
- CLI: `medautosci doctor report --profile <profile>`
- CLI: `medautosci doctor profile --profile <profile>`
- CLI: `medautosci workspace bootstrap --profile <profile>`
- CLI: `medautosci runtime watch --runtime-root <runtime-root>`
- CLI: `medautosci runtime overlay-status --profile <profile>`
- CLI: `medautosci doctor med-deepscientist-upgrade --profile <profile> --refresh`

## Live Runtime Guard

当 `study runtime-status` 或 `study ensure-runtime` 返回 `execution_owner_guard.supervisor_only = true` 时，Codex 前台必须切换成 supervisor-only 模式：

- 只负责读取状态、通知用户、提供监督入口和接收 pause/resume/stop/takeover 决策
- 不继续直接推进 study-local 写作、bundle、proofing、review 或编译链
- 不直接写入 runtime-owned surface

如果同时 `publication_supervisor_state.bundle_tasks_downstream_only = true`，则 bundle/build/proofing 在语义上仍属后续件，前台不得抢跑。

## 当前安装状态

仓库里存在 plugin 文件，不等于 Codex 已经全局启用它。

- 仓库内状态：plugin 已经存在于当前仓库，可被仓库自己的 marketplace 元数据发现
- 全局状态：只有当 `~/.codex/config.toml` 中启用了对应 plugin，Codex 才会在整机范围把它当作已安装入口

因此，仓库内置 plugin 和整机可用 plugin 不是一回事。

## 在另一台电脑上使用

最稳妥的路径是：

1. clone 本仓库
2. 运行：

   ```bash
   bash scripts/install-codex-plugin.sh
   ```

3. 重启 Codex，让 skill 和 plugin 元数据重新加载

如果你想把 plugin 放在 home-local，而不是 repo-local，也可以复制或同步：

- `plugins/med-autoscience/` to `~/plugins/med-autoscience/`
- `.agents/plugins/marketplace.json` into `~/.agents/plugins/marketplace.json`

然后确保 `medautosci-mcp` 仍然在 `PATH` 上。

这里仍然只安装 `MedAutoScience` 的 plugin / skill / MCP 入口，不会顺带安装 `MedDeepScientist` runtime。

## 作用边界

这个 plugin 只是薄入口层，真正的医学研究运行层仍然是 `MedAutoScience` 本体。
