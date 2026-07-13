# 当前状态

Owner: `MedAutoScience`
Purpose: `current_status_summary`
State: `active_current_truth`
Machine boundary: 本文只总结 repo current state。具体 study/runtime 状态必须 fresh 读取 OPL StageRun/readback、MAS owner surfaces、workspace artifacts 与 receipts。

## 结论

2026-07-13 已落地 MAS-owned Stage quality-cycle profile：六个 canonical Stage
显式绑定独立 reviewer Attempt/session，`review_and_quality_gate` 固定为
cross-Stage Meta Review，六阶段到八个 paper-study physical Stage 的映射归一，
默认三轮语义修订预算与 provider/dispatch retry 分账。OPL Framework 仍负责
实际 StageAttempt/thread 编排和 session identity 校验；本文不把合同落盘写成
live runtime evidence。

同日已落领域侧 hosted authority callable：`mas.paper-mission-authority-evaluate`
只消费 host 注入且带 SHA 的 run/producer-attempt/output refs，以及 MAS source、
evidence、independent-review、repair 与 hard-gate records；它可返回 owner receipt、
route-back、quality debt、typed blocker 或 human gate，但没有 profile/path discovery、
文件/网络 I/O、queue/session/DAG、spawn、OPL/Codex 调用或 runtime ledger 权限。
MAS V2 contract 已通过 closed handler registry 绑定该 callable，六个公开 Stage action
也已完成 generated/default surface cutover。冻结双仓基线上的 fresh OPL readback 显示：
interfaces `ready`，8/8 generated default surfaces 与 8/8 retirement gates 已关闭，
scaffold `passed`；authority callable 的可达闭包没有任何 generic effect。仓库级
source-closure 仍被 534 个全部不可达的 legacy generic effects、27 条 unresolved edges
与 534 条 audit mismatch 阻断，不能据此授权物理删除。OPL hosted terminal smoke、
contained exact-result commit 与 readback 仍待最终集成验证；旧 `paper_mission`、
`domain_handler_export/dispatch`、`mainline_*`、status/read-model 与 queue-oriented 内部
caller 仍是待迁 residue，尚未获得物理删除结论。

2026-07-12 的 active-caller 复审纠正了此前“12 项结构目标全部落地”的过度结论。MAS 已进一步物理退役私有 provider/Temporal/readiness contract builder、domain-handler transport receipt 文件存储和六类 reference provider HTTP client，并通过 `contracts/domain_descriptor.json#/standard_agent_interface` 向 OPL 声明 workspace binding、runtime registration、progress aliases 与 routing hints。

当前目标形态仍是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`，但功能/结构收口仍为 `partial`：current-control/StageAttempt 聚合、Workspace/Stage Folder/status 物化、Display Pack 任意 subprocess transport 和 gate-clearing DAG 仍有 MAS active caller，需先由 OPL 提供对应稳定公共 carrier，再迁调用方并删除旧实现。Live evidence 仍后置且独立为 `partial_deferred`。

## 当前机器形态

| Surface | Current state |
| --- | --- |
| Identity | canonical id `mas` |
| Package candidate | immutable SemVer `0.2.1`；repo manifest/plugin/Python metadata 对齐，真实 publish/install/readback proof 仍后置 |
| Action catalog | V2 closed catalog：六个公开 Stage action + 一个无用户 surface 的内部 authority action |
| Standard interface | MAS descriptor 声明 locator/runtime/progress/routing；不再携带私有 command template；OPL generic consumer 解析并生成/托管 |
| Interface owner | OPL 生成 CLI/MCP/Skill/product-entry/status/workbench；MAS 不持有第二套 descriptor builder |
| MAS runtime role | domain-handler intent/result + minimal authority functions；transport receipt 由 OPL Runway/Ledger 持久化 |
| Environment | MAS 声明 requirements；OPL `env prepare/run` 负责准备与执行 |
| Next action | `Codex CLI selected stage -> nonbinding route context` |
| Foundry series | OPL canonical policy + MAS refs-only consumer contract；MAS 无本地 Framework 依赖 |
| Framework Python | OPL 托管 `src/opl_framework` carrier；MAS manifest / lock 不锁 OPL implementation |
| Required capability package | `mas-scholar-skills`；MAS manifest 声明 hard dependency、ABI、11 Skill + 8 module exports；生命周期归 `opl packages` |
| Scientific providers | OPL Connect 负责 provider invocation/retry/cache/receipt；MAS 只消费 receipt 并作医学 gate 判断 |
| Stage prompt model | 六个精简目标型 prompt；同 thread 自检仅为 `in_thread_refinement`，正式 Review 使用 fresh Attempt/session；专业/证据/authority 顺序由 Stage policy、domain Skill 与 quality gate 托底 |
| Quality cycle | `contracts/stage_quality_cycle_policy.json`；六个 policy 均满足严格 Framework schema，五个产出 Stage 默认三轮 repair + re-review，预算耗尽有 artifact 则带质量债推进 |
| Hosted authority | `contracts/domain_handler_registry.json` 已 closed-bind 纯 `paper_mission` callable；fresh closure 证明 callable 可达路径零 generic effect，OPL hosted terminal smoke 与 exact-result readback 待最终集成验证 |
| Meta Review | `review_and_quality_gate` 独立 StageRun；只诊断与 route-back，不在 reviewer thread 内修稿，也不递归 Review 自身；`strategy_retrospective` 仅为非权威策略复盘 |
| Test collection | pytest 原生递归收集 |
| Build isolation | `scripts/run-build-clean.sh`；旧 runtime/editable clean runner 已退役 |
| Legacy control plane | 已退出 V2 public/default surface；遗留内部 `domain_entry/mainline/read-model/queue` caller 仍待迁移与物理退役 |
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
| `paper_mission` private discovery/readback/persistence transport | `partial` | V2 default surface 已切到 registry-bound authority callable；fresh repo source-closure 因 534 个不可达 legacy generic effects 阻断，仍需 contained exact-result commit/readback、内部 caller 迁移和旧 transport 物理删除 |
| `mainline_status` / `mainline_phase` 私有产品状态 shell | `partial` | generated/default callers 已不再发布两个 MAS action；`opl_module_carrier` 仍以 module healthcheck 调用 `mainline-status`，需 OPL hosted status/workbench 与 framework-owned healthcheck parity、内部 caller 迁移和源码退役 |

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
