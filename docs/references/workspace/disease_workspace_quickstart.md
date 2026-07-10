# Disease Workspace Quickstart

Owner: `MedAutoScience`
Purpose: `workspace_bootstrap_reference`
State: `current_reference`
Machine boundary: 本文是人读 workspace 接入指南；workspace lifecycle、locator、environment、StateIndex、retention/restore 和 hosted workbench 的机器真相归 OPL。MAS 机器真相归 profile/action schemas、domain handlers、owner receipts、typed blockers 和医学 authority surfaces。

## 结论

MAS 已退役 repo-local workspace initializer、bootstrap shell、MCP `init_workspace` 和 CLI `init-workspace`。新 workspace 由 OPL generated/hosted workspace lifecycle surface 创建和绑定，MAS 只接收 `profile_ref`、`study_id` 与受权 refs。

不要运行或恢复：

- `medautosci-mcp` / MCP `init_workspace`；
- `python -m med_autoscience.cli init-workspace`；
- `medautosci workspace init/bootstrap`；
- `ops/medautoscience/bin/bootstrap`、`show-profile`、`enter-study`、`storage-audit`；
- repo-local installer、workspace environment builder 或 runtime wrapper。

这些 identity 只用于旧 workspace 的 provenance/retirement 说明，不是当前执行入口。

## 对象边界

- `workspace`：病种级长期资产层，可含多个 dataset version、study 和 paper line。
- `dataset family/version`：workspace 级数据版本；study 只消费已登记版本。
- `study`：单条具体研究线，通常对应一篇主稿或一组强关联交付物。
- `quest` / StageRun：OPL 受管执行身份；attempt lifecycle 归 OPL，医学结果解释归 MAS。
- `paper bundle/submission package`：study-local 交付物，不属于 workspace 顶层。

## 最小接入信息

OPL workspace surface 至少要给 MAS action 提供：

- `profile_ref`
- `study_id`
- `task_intent`（提交任务时）
- action schema 要求的 workspace/source refs

`profiles/workspace.profile.template.toml` 是 profile 结构参考，不是 workspace initializer。不要让文档、Agent 或 wrapper 从目录猜 profile、repo 或 runtime path。

推荐的 domain 资产布局是：

```text
<workspace>/
├── data/
│   └── datasets/
├── studies/
├── memory/
│   └── portfolio/
│       ├── data_assets/
│       └── research_memory/
├── refs/
└── artifacts/
```

OPL 可以在其 owner contract 下增加 runtime/quest/restore/index 目录；这些目录不是 MAS bootstrap 输出合同，也不能让 MAS 重新成为 generic lifecycle owner。

## 启动顺序

1. 通过 OPL generated/hosted workspace lifecycle surface 创建或登记 workspace。
2. 绑定 `profile_ref`，登记 source/data refs、数据字典、终点定义、纳排标准和参考资料。
3. 用 generated action `submit_study_task` 写 durable study task intake。
4. 用 generated action `launch_study` 提交 MAS domain handoff，由 OPL hydrate StageRun。
5. 用 `study_progress`、`study_state_matrix` 或 `paper_mission` 读取 refs-only progress/owner route。
6. 当 action 返回 typed blocker 或 human gate 时，交对应 owner 处理；不得用 workspace wrapper 绕过。

这些是 action id，不承诺具体 CLI 拼写。实际 CLI/MCP/Skill/product UI 由 OPL 从 `contracts/action_catalog.json` 和 schemas 生成。

## 数据与 authority

- 私有/公开数据版本登记在 workspace 级数据资产层。
- study 只消费已登记的版本；同一版本可被多个 study 复用。
- 不在每个 study 复制一份未经登记的数据真相源。
- MAS 只保留 source readiness、study truth、quality gate、artifact/package authority、memory accept/reject、owner receipt 和 typed blocker。
- generic workspace/file lifecycle、artifact locator、StateIndex、restore/retention、cleanup 和 operator shell 归 OPL。

数据资产状态、startup readiness、asset update、impact 和 release explanation 的医学函数仍可作为 MAS internal authority functions 存在；它们当前不是 22-action catalog 的 public action。除非 catalog/schema 正式增加 action id，否则不能把旧 `medautosci data ...` 文案当作可运行命令。

## Git 与旧 workspace

新 workspace 默认 no root Git / no quest Git。Git history、Git diff/log、workspace root Git、quest `.git` 和 worktree list 都不是 current runtime truth。

旧 workspace 中的 `ops/medautoscience/bin/*`、`ops/med-deepscientist/bin/*`、quest-local `.ds/`、`.ds/worktrees/` 和 quest `.git` 只作为 legacy intake、restore proof、diagnostic provenance 或 cleanup target。涉及 archive/remove 等物理操作时，必须交 OPL lifecycle owner，并要求 inventory、authority classification、hash、restore command、authorization 和 readback；不要恢复已退役的 MAS `storage-audit` wrapper。

## Runtime boundary

- `MedAutoScience` 是医学研究 domain owner，不是 generic runtime platform。
- OPL provider-backed stage runtime 持有 attempt、queue、worker residency、retry/dead-letter、resume 与 operator projection。
- OPL generated/hosted surface 消费 MAS action schemas、body-free refs、owner receipts 和 typed blockers。
- `MedDeepScientist` 只作为 frozen source archive、historical fixture、explicit archive import、backend audit 或 parity oracle reference。
- `Hermes-Agent` 只可指外部 runtime 项目/服务、显式 proof lane 或历史 provenance。

Workspace 已创建、profile 可解析或 generated interface ready 都不证明 runtime live、paper progress、publication-ready、artifact mutation authority 或 domain ready。Live evidence 必须从对应 OPL runtime readback、MAS owner receipt/quality gate/typed blocker/human gate 和真实 artifact 读取。

## 接下来读什么

- [MAS Bootstrap](../../../bootstrap/README.md)
- [Workspace Architecture](workspace_architecture.md)
- [Runtime Boundary](../../runtime/contracts/runtime_boundary.md)
- [Agent Runtime Interface](../../runtime/contracts/agent_runtime_interface.md)
- [workspace.profile.template.toml](../../../profiles/workspace.profile.template.toml)
