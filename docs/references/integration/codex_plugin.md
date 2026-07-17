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
- `contracts/schemas/v2/mas-stage-action.input.schema.json`
- `contracts/schemas/v2/mas-stage-action.output.schema.json`
- `contracts/schemas/v2/mas-paper-mission-authority.input.schema.json`
- `contracts/schemas/v2/mas-paper-mission-authority.output.schema.json`
- `contracts/generated_surface_handoff.json`
- `agent/`

`contracts/action_catalog.json` 是当前 action identity 列表。六个公开 action 都使用 Stage binding：

```text
direction_and_route_selection
baseline_and_evidence_setup
bounded_analysis_campaign
manuscript_authoring
review_and_quality_gate
finalize_and_publication_handoff
  -> agent/stages/manifest.json
```

OPL generated/hosted surface 可以把这些 Stage action 映射为 CLI/MCP/tool UI，但 MAS 不维护第二份 parser、transport 或 command template。catalog 内两个非 Stage action 是 host-only `candidate_admission_authority_evaluate` 与 `paper_mission_authority_evaluate`；它们通过 `contracts/domain_handler_registry.json` 的 closed bindings 指向纯 authority callables，没有 CLI/MCP/Skill/product user surface。registry 另绑定 `mas.agent-lab-self-evolution-closeout`，因此当前精确边界是六个公开 Stage actions、两个 host-only actions 与三个 closed-registry authority handlers。

catalog 中没有的 `study_progress`、`launch_study`、`submit_study_task`、`paper_mission`、`study_state_matrix`、`domain_handler_export`、`domain_handler_dispatch`、`scientific_capability_registry`、`display_pack_*`、`init_workspace`、`doctor report/profile/backend-upgrade`、`runtime domain-diagnostic-report` 和 `runtime overlay-status` 只属于 internal residue/provenance 语境，不是当前可执行入口。workspace lifecycle、profile binding、environment preparation、runtime supervision 和 operator shell 归 OPL owner surface。

## Agent 使用顺序

1. 通过 OPL generated/hosted workspace surface 获得 `workspace_root`、`study_id` 与当前 refs。
2. Codex 根据当前研究目标选择六个 Stage action 之一；Stage manifest 中的 `requires` 是质量上下文，不是固定启动门，允许 advance/skip/repeat/reverse/route-back。
3. OPL 创建并持有 StageRun/attempt；Stage executor 通过 Tool Affordance Boundary 选择 ScholarSkills、Connect、Runway、Workspace 等能力。
4. MAS pure authority functions 只消费 refs、生成医学 gate input/authority result；OPL transport 或 provider completion不能替代 MAS owner receipt。
5. 只有 Stage action 的写范围、authority boundary 和 human gate 同时成立时，才允许写 MAS-owned surface；用户不直接调用 host-only authority action。

调用方不得直接修改 registry、runtime ledger、publication truth、artifact authority 或 `current_package`。新 workspace 默认 no root Git / no quest Git；Git history、Git diff/log、workspace root Git 和 quest `.git` 都不是 current runtime truth。

## 安装与分发边界

仓库里存在 plugin carrier，不等于本机 Codex 已加载它。package discovery、plugin materialization、cache refresh 和 generated interface currentness 由 OPL 安装/启动维护面负责；MAS 不提供 standalone GitHub Release、marketplace、installer 或系统级 skill copy 命令。

Python package 只按标准 packaging/`uv sync` 或 OPL workspace override 安装。运行环境由 OPL 根据 `contracts/runtime_environment_requirements.json` 准备；MAS import、plugin load 或 domain handler 不安装/修复 Python、R、Bioconductor 或系统依赖。

另一台机器的用户生命周期入口只有：

```bash
opl packages install mas
opl packages update mas
opl packages uninstall mas
```

OPL 在这些 lifecycle transaction 内完成依赖闭包解析、generated interface/Carrier 物化、currentness readback、卸载保护与回滚；MAS 文档不暴露内部 activation/status/repair 命令。

不要恢复 `.agents/plugins/marketplace.json`、`plugins/mas`、`medautosci-mcp`、`uv tool install .` 作为 MAS plugin 安装合同，或把 package import success 当作 runtime ready。

## Live Runtime Guard

当 OPL StageRun/current-control readback 返回 `execution_owner_guard.supervisor_only = true` 时，Codex 前台只做状态读取、通知和 pause/resume/stop/takeover 决策，不继续直接写 study-local paper/package/runtime surface。

如果同时 `publication_supervisor_state.bundle_tasks_downstream_only = true`，bundle/build/proofing 仍属后续件，前台不得抢跑。

Plugin/interface parity 只能证明结构与 dispatch binding 成立；它不证明 provider running、paper progress、publication quality、artifact mutation authorization、domain ready 或 production ready。Live evidence 继续由对应 runtime/readback/owner receipt 证明。
