# Codex Plugin 接入

Owner: `MedAutoScience`
Purpose: `Support MAS integration and OPL handoff understanding.`
State: `support_reference`
Machine boundary: Human-readable integration reference only; callable and generated-surface truth remains in `agent/`, manifests, contracts, source, tests, OPL handoff contracts, and read-model output.

## 当前结论

`plugins/med-autoscience/` 是 Codex plugin carrier，不是 MAS 自己维护的 CLI、MCP server、installer 或 runtime。

当前仓库只保留：

- `.codex-plugin/plugin.json`：plugin metadata；
- `skills/med-autoscience/SKILL.md`：`agent/primary_skill/SKILL.md` 的受控 full-skill carrier mirror；
- plugin assets。

`plugins/med-autoscience/bin/medautosci-mcp`、repo-local MCP JSON-RPC transport、`medautosci` parser、专用 installer 和 home-local wrapper 已退役。不要把这些旧路径写成 direct/proof lane，也不要要求它们出现在 `PATH`。

## 可调用面从哪里来

OPL 从下面的 MAS pack 输入生成或托管 CLI、MCP、Skill、product-entry、status 和 workbench surface：

- `contracts/domain_descriptor.json`
- `contracts/pack_compiler_input.json`
- `contracts/action_catalog.json`
- `contracts/schemas/v1/mas-action.input.schema.json`
- `contracts/schemas/v1/mas-action.output.schema.json`
- `contracts/generated_surface_handoff.json`
- `agent/`

`contracts/action_catalog.json` 是当前 action identity 列表。普通 action 的 handler target 统一为：

```text
med_autoscience.domain_entry:MedAutoScienceDomainEntry.dispatch#<action_id>
```

其中 `study_progress`、`launch_study`、`submit_study_task`、`paper_mission`、`study_state_matrix`、`domain_handler_export` 和 `domain_handler_dispatch` 等是 action id，不是仓内手写 shell 命令。OPL generated surface 可以把 action id 映射为 CLI/MCP/tool UI，但 MAS 不再维护第二份 parser 或 transport。

catalog 中没有的 `init_workspace`、`workspace bootstrap`、`doctor report/profile/backend-upgrade`、`runtime domain-diagnostic-report` 和 `runtime overlay-status` 只属于 retired/provenance 语境，不是当前可执行入口。workspace lifecycle、profile binding、environment preparation、runtime supervision 和 operator shell 归 OPL owner surface。

## Agent 使用顺序

1. 通过 OPL generated/hosted workspace surface 获得 `profile_ref` 和 `study_id`。
2. 用 `submit_study_task` 写入 durable MAS study task intake。
3. 用 `launch_study` 提交 MAS domain handoff，由 OPL 唯一控制面 hydrate stage attempt。
4. 用 `study_progress`、`study_state_matrix` 或 `paper_mission` 读取 MAS refs、owner route、typed blocker 和 owner receipt。
5. 只有 action catalog 明确声明的 mutating action，且输入 schema、authority boundary 和 human gate 成立时，才允许写 MAS-owned surface。

调用方不得直接修改 registry、runtime ledger、publication truth、artifact authority 或 `current_package`。新 workspace 默认 no root Git / no quest Git；Git history、Git diff/log、workspace root Git 和 quest `.git` 都不是 current runtime truth。

## 安装与分发边界

仓库里存在 plugin carrier，不等于本机 Codex 已加载它。package discovery、plugin materialization、cache refresh 和 generated interface currentness 由 OPL 安装/启动维护面负责；MAS 不提供 standalone GitHub Release、marketplace、installer 或系统级 skill copy 命令。

Python package 只按标准 packaging/`uv sync` 或 OPL workspace override 安装。运行环境由 OPL 根据 `contracts/runtime_environment_requirements.json` 准备；MAS import、plugin load 或 domain handler 不安装/修复 Python、R、Bioconductor 或系统依赖。

另一台机器的标准步骤是：

1. 让 OPL 发现 MAS package 和 canonical id `mas`；
2. 由 OPL 编译/物化 generated interfaces 与 Codex carrier；
3. 由 OPL 刷新对应 plugin cache；
4. 用 action catalog/schema 和 generated-surface readback 核对 interface parity。

不要恢复 `.agents/plugins/marketplace.json`、`plugins/mas`、`medautosci-mcp`、`uv tool install .` 作为 MAS plugin 安装合同，或把 package import success 当作 runtime ready。

## Live Runtime Guard

当 generated `study_progress`、`launch_study` 或 OPL `current_control_state` 返回 `execution_owner_guard.supervisor_only = true` 时，Codex 前台只做状态读取、通知和 pause/resume/stop/takeover 决策，不继续直接写 study-local paper/package/runtime surface。

如果同时 `publication_supervisor_state.bundle_tasks_downstream_only = true`，bundle/build/proofing 仍属后续件，前台不得抢跑。

Plugin/interface parity 只能证明结构与 dispatch binding 成立；它不证明 provider running、paper progress、publication quality、artifact mutation authorization、domain ready 或 production ready。Live evidence 继续由对应 runtime/readback/owner receipt 证明。
