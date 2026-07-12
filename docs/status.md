# 当前状态

Owner: `MedAutoScience`
Purpose: `current_status_summary`
State: `active_current_truth`
Machine boundary: 本文只总结 repo current state。具体 study/runtime 状态必须 fresh 读取 OPL StageRun/readback、MAS owner surfaces、workspace artifacts 与 receipts。

## 结论

MAS 的 12 项过度设计结构目标已经落地：repo-local platform surfaces 已删除、上收或收成 OPL-consumable declarations；MAS 当前形态是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。

这是一项 repo/source/control-plane 结论，不是 live readiness 结论。L1-L5 已关闭，双仓 full verify、提交、push 与 target-ref readback 均已完成。Live evidence 仍后置且独立为 `partial_deferred`。

## 当前机器形态

| Surface | Current state |
| --- | --- |
| Identity | canonical id `mas` |
| Action catalog | 22 actions，含 `paper_mission`、display、integrity、status 与 domain-handler actions |
| Interface owner | OPL 生成 CLI/MCP/Skill/product-entry/status/workbench |
| MAS runtime role | domain-handler targets + minimal authority functions |
| Environment | MAS 声明 requirements；OPL `env prepare/run` 负责准备与执行 |
| Next action | `StageOutcome -> NextActionEnvelope` |
| Foundry series | OPL canonical policy + MAS refs-only consumer contract；MAS 无本地 Framework 依赖 |
| Framework Python | OPL 托管 `src/opl_framework` carrier；MAS manifest / lock 不锁 OPL implementation |
| Required capability package | `mas-scholar-skills`；MAS manifest 声明 hard dependency、ABI、11 Skill + 8 module exports；生命周期归统一 `opl packages` |
| Stage prompt model | 六个精简目标型 prompt；专业/证据/authority 顺序由 Stage policy、domain Skill 与 quality gate 托底；普通质量债可前进但不能升级 ready claim |
| Test collection | pytest 原生递归收集 |
| Build isolation | `scripts/run-build-clean.sh`；旧 runtime/editable clean runner 已退役 |
| Legacy control plane | retired/tombstone/provenance only |
| Standard Agent conformance | domain-owned `contracts/standard_agent_conformance_profile.json` 声明六阶段 golden path 与 MAS 物理形态；OPL 只执行通用结构检查 |

## MAS 保留面

- medical study/source truth；
- independent AI reviewer/auditor quality records；
- publication gate 与 submission/artifact authority；
- memory accept/reject；
- owner receipt、typed blocker、human gate、route-back decision；
- action handler target 与必要 domain-native helper。

## 已退役的平台面

- import-time editable bootstrap；
- pytest wildcard aggregation；
- MAS-local StateIndex pilot；
- repo-local installer/workspace environment provisioning；
- retirement work-order/rollup/currentness system；
- repo-local workbench/cockpit，以及 `workspace-cockpit -> mainline-status` compatibility alias；
- hand-maintained Tool Arsenal/capability runtime；
- hand-written CLI/MCP transport glue；
- MAS runtime health/lifecycle/storage platform；
- legacy next-action producer family。
- MAS-local StageRun projector 与残留 `stage_artifact_index` 通用 ref/text helper；MAS 仅保留 stage profile、医学 taxonomy、owner receipt / typed blocker validator 与 authority function，通用 StageRun / artifact projection 由 OPL Stagecraft / Workspace 托管。

`runtime_control/**`、`runtime_protocol/**` 与 MAS-local runtime-state authority/storage path 已清零；通用 runtime identity/readback 归 OPL StageRun、current-control 与 StateIndex refs owner。

详细映射见 [MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)。

## Live evidence tail

以下结论仍需 fresh owner/live evidence，当前不得声明 ready：

- OPL command/event/outbox/StageRun same-identity readback；
- provider admission/running 与 retry/dead-letter/long-soak；
- 真实 paper line 的 owner receipt、stable typed blocker 或 human gate；
- independent reviewer/auditor receipt；
- canonical paper/artifact semantic delta；
- publication/submission/current-package authority。

contracts、tests、descriptor ready、projection clean、queue empty、candidate package 与 docs 不替代上述证据。

## 维护入口

- [项目概览](./project.md)
- [架构](./architecture.md)
- [不可变约束](./invariants.md)
- [关键决策](./decisions.md)
- [Active plan](./active/mas-ideal-state-gap-plan.md)
- [Product surfaces](./product/README.md)
- [Runtime boundary](./runtime/contracts/runtime_boundary.md)
