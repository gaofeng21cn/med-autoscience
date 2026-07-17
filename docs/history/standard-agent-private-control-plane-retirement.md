# 标准 Agent 私有控制面退役记录

Owner: `MedAutoScience`
Purpose: `retired_private_control_plane_provenance`
State: `history_tombstone`
Machine boundary: 本文只记录退役分类和替代 owner，不是 runtime、route、receipt、readiness 或兼容接口。

## 退役结论

本记录保存 MAS 私有控制面退役时的 owner 迁移与 no-resurrection 边界。当前结构摘要不由本历史文档持有；请读 [当前状态](../status.md) 与 [Active Truth](../active/mas-ideal-state-gap-plan.md)。旧私有 CLI、MCP、product wrapper、scheduler、runner、queue、session store、lifecycle/SQLite、StateIndex、status/workbench、provider transport、package/environment provisioner、NextAction、PaperRecovery、stage terminalizer 和 callable validator 已从 active source 与 machine contracts 物理删除。

替代 owner 如下：

| 退役能力 | 当前 owner |
| --- | --- |
| CLI / MCP / Skill / product-entry / status / workbench | OPL generated/hosted surfaces |
| StageRun / Attempt / session / Temporal lifecycle / retry | OPL Runway / Ledger |
| StateIndex / storage / lifecycle / observability | OPL Framework |
| provider invocation / credentials / retry / receipt transport | OPL Connect |
| package、environment 与 submission resource materialization | OPL Pack / environment substrate |
| 语义 route decision | decisive Codex Attempt |
| transition materialization | OPL StageRun controller |
| 医学 truth、quality、artifact、publication 与 owner answer | MAS declarative policy + independent Review + registry-bound authority functions |

`skill` 与 `domain_handler` 出现在默认 surface 退役清单中，指的是 MAS
repo-local wrapper / default caller 已退役，不是删除领域输入。Canonical primary
skill 继续作为 declarative pack source 并由 OPL 生成/托管；closed registry 当前绑定
candidate admission、paper mission 与 self-evolution closeout 三个医学 authority
functions。它们都不拥有 CLI、MCP、session、lifecycle、transport 或 transition
materialization。

## 保留实现边界

三个 authority handlers 只消费 host 注入的 exact refs，执行确定性医学 authority
evaluation，并返回 contract-bound result；共享 helper 只做纯校验。它们不做文件、
网络、进程、runtime、package、session 或 transition 操作。精确 callable 与 schema
以 `contracts/domain_handler_registry.json`、`contracts/action_catalog.json` 和当前 source
为准，本历史文档不复制第二份 handler catalog。

## Receipt 边界

OPL Connect / Pack / Runway receipt 只证明对应 transport、materialization 或 attempt 事实，不等于医学 verdict、publication/submission readiness、MAS owner receipt 或 live paper progress。任何 live claim 仍需 fresh StageRun/Attempt refs、独立 Review receipt 和 MAS owner acceptance evidence。

旧路径的逐文件 provenance 由 Git history 持有。不得为兼容、诊断或测试恢复已删除的 active implementation 或 machine contract。
