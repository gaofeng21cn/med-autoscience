# 当前状态

Owner: `MedAutoScience`
Purpose: `current_status_summary`
State: `active_current_truth`
Machine boundary: 本文只总结 repo current state。具体 study/runtime 状态必须 fresh 读取 OPL StageRun/readback、MAS owner surfaces、workspace artifacts 与 receipts。

## 结论

2026-07-12 的 active-caller 复审纠正了此前“12 项结构目标全部落地”的过度结论。MAS 已进一步物理退役私有 provider/Temporal/readiness contract builder、domain-handler transport receipt 文件存储和六类 reference provider HTTP client，并通过 `contracts/domain_descriptor.json#/standard_agent_interface` 向 OPL 声明 workspace binding、runtime registration、progress aliases 与 routing hints。

当前目标形态仍是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`，但功能/结构收口仍为 `partial`：current-control/StageAttempt 聚合、Workspace/Stage Folder/status 物化、Display Pack 任意 subprocess transport 和 gate-clearing DAG 仍有 MAS active caller，需先由 OPL 提供对应稳定公共 carrier，再迁调用方并删除旧实现。Live evidence 仍后置且独立为 `partial_deferred`。

## 当前机器形态

| Surface | Current state |
| --- | --- |
| Identity | canonical id `mas` |
| Action catalog | 22 actions，含 `paper_mission`、display、integrity、status 与 domain-handler actions |
| Standard interface | MAS descriptor 声明 locator/direct-entry/runtime/progress/routing；OPL generic consumer 解析并生成/托管 |
| Interface owner | OPL 生成 CLI/MCP/Skill/product-entry/status/workbench；MAS 不持有第二套 descriptor builder |
| MAS runtime role | domain-handler intent/result + minimal authority functions；transport receipt 由 OPL Runway/Ledger 持久化 |
| Environment | MAS 声明 requirements；OPL `env prepare/run` 负责准备与执行 |
| Next action | `StageOutcome -> NextActionEnvelope` |
| Foundry series | OPL canonical policy + MAS refs-only consumer contract；MAS 无本地 Framework 依赖 |
| Framework Python | OPL 托管 `src/opl_framework` carrier；MAS manifest / lock 不锁 OPL implementation |
| Required capability package | `mas-scholar-skills`；MAS manifest 声明 hard dependency、ABI、11 Skill + 8 module exports；生命周期归 `opl packages` |
| Scientific providers | OPL Connect 负责 provider invocation/retry/cache/receipt；MAS 只消费 receipt 并作医学 gate 判断 |
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
- MAS provider/Temporal/readiness/skeleton/workspace-evidence contract bundle；
- MAS domain-handler dispatch receipt 哈希、幂等与文件存储；
- MAS Crossref/OpenAlex/Semantic Scholar/Crossmark/Publisher HTTP transport；
- legacy next-action producer family。
- MAS-local StageRun projector 与残留 `stage_artifact_index` 通用 ref/text helper；MAS 仅保留 stage profile、医学 taxonomy、owner receipt / typed blocker validator 与 authority function，通用 StageRun / artifact projection 由 OPL Stagecraft / Workspace 托管。

`runtime_control/**`、`runtime_protocol/**` 与 MAS-local runtime-state authority/storage path 已清零；通用 runtime identity/readback 归 OPL StageRun、current-control 与 StateIndex refs owner。当前剩余实现只可作为待迁 active caller，不再视为长期合理私有平台。

## 功能/结构尾项

| Tail | 当前状态 | 关闭条件 |
| --- | --- | --- |
| current-control / StageAttempt readback | `partial` | OPL canonical readback carrier 覆盖 identity、attempt refs 与 currentness；MAS 只保留 domain impact |
| Workspace / Stage Folder / status materialization | `partial` | OPL Workspace/Stagecraft/Ledger 提供 Python 或 generated caller，迁移 profile/status active caller |
| Display Pack subprocess transport | `partial` | OPL Runway 提供任意 domain command 的 env/run-context/receipt carrier；MAS 保留 renderer 与医学 visual verdict |
| gate-clearing DAG | `partial` | OPL Stagecraft 提供依赖图、parallel wave、fingerprint skip、failure propagation 公共接口 |
| StateIndex ref normalization/hash | `partial` | OPL Ledger/Workspace 公共 normalizer 可由 MAS carrier 直接消费 |

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
