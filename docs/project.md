# 项目概览

Owner: `MedAutoScience`
Purpose: `project_current_truth`
State: `active_current_truth`
Machine boundary: 本文是人读概览。机器真相归 `agent/`、`contracts/`、唯一 registry-bound authority function、OPL runtime durable surfaces、真实 workspace artifact 与 owner receipts。

`Med Auto Science`（canonical agent id：`mas`；machine domain id：`medautoscience`）是 OPL family 中的医学研究 domain agent。当前目标形态固定为：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + one registry-bound authority function`

MAS 描述医学研究阶段、知识、质量门、六个公开 Stage action、内部 authority handler binding 与环境需求，并保留无法声明化的医学 authority。OPL 根据这些声明生成或托管 CLI、MCP、Skill、product-entry、status、workbench、runtime lifecycle、StateIndex 和环境准备等通用平台面。

## 当前可交付形态

- `agent/` 是 MAS declarative pack：primary skill、stages、knowledge、prompts 与 quality gates。
- `contracts/action_catalog.json` 是 closed V2 catalog：六个公开 action 与六个 canonical Stage 一一对应；`paper_mission_authority_evaluate` 仅作为无用户 surface 的内部 authority action。
- `contracts/domain_handler_registry.json` 只绑定纯 `evaluate_paper_mission_authority` callable；旧 domain entry、status/read-model、queue 和 transport caller 已从 active source 物理退役。
- 唯一非声明式实现只校验 host 注入的 exact refs，并返回医学 owner receipt、route-back、quality debt、typed blocker 或 human gate；它不持有文件、网络、进程、session、lifecycle 或 transition authority。
- `contracts/runtime_environment_requirements.json` 只声明 MAS 的运行环境需求；环境解析、安装和运行归 OPL `env prepare/run`。
- OPL 持有通用 runtime、queue、attempt ledger、retry/dead-letter、StateIndex、lifecycle/storage、observability 和 hosted workbench。

## Owner 边界

| Surface | Owner | MAS 输出 |
| --- | --- | --- |
| CLI / MCP / Skill / product-entry | OPL generated surfaces | Stage action metadata、schema、stage binding |
| Status / workbench / drilldown | OPL hosted surfaces | body-free refs、receipts、blockers、authority refs |
| Runtime lifecycle / StateIndex / storage / health | OPL Framework | domain policy result、owner answer、forbidden-write boundary |
| Medical study truth / quality / publication | MAS | owner verdict、receipt、typed blocker、human gate |
| Canonical paper / evidence / artifact mutation | MAS | authority decision 与可追踪 artifact refs |

## 论文推进

默认控制链是：

`decisive Codex Attempt -> semantic route decision -> OPL StageRun controller materialization -> MAS owner consumption`

旧 `provider_attempt`、`current_work_unit`、`paper_recovery_state` 和 domain-action request producers 不再是默认 next-action authority。需要追溯时只读 tombstone/provenance；不得从旧 projection、queue、attempt、provider 或 UI 状态推断 paper progress。

## 当前验收边界

V2 public/default command cutover、私有控制面物理退役和 source closure 已完成；repo/source/control-plane 结构已收敛为标准 OPL Agent。见 [MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)。这不等于 live runtime、真实 paper line、publication 或 production ready。

Live evidence 单独后置。只有 fresh OPL StageRun/readback、MAS owner receipt、stable typed blocker、human gate、independent reviewer/auditor receipt 或真实 paper/artifact semantic delta，才能支持对应 live claim。

## 下一跳

- [架构](./architecture.md)
- [不可变约束](./invariants.md)
- [当前状态](./status.md)
- [关键决策](./decisions.md)
- [Runtime boundary](./runtime/contracts/runtime_boundary.md)
- [文档组合治理](./docs_portfolio_consolidation.md)
