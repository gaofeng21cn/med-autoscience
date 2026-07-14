# 标准 Agent 私有控制面退役记录

Owner: `MedAutoScience`
Purpose: `retired_private_control_plane_provenance`
State: `history_tombstone`
Machine boundary: 本文只记录退役分类和替代 owner，不是 runtime、route、receipt、readiness 或兼容接口。

## 退役结论

MAS 已收敛为 `Declarative Medical Research Pack + OPL generated/hosted surfaces + one registry-bound authority function`。旧私有 CLI、MCP、product wrapper、scheduler、runner、queue、session store、lifecycle/SQLite、StateIndex、status/workbench、provider transport、package/environment provisioner、NextAction、PaperRecovery、stage terminalizer 和 callable validator 已从 active source 与 machine contracts 物理删除。

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
| 医学 truth、quality、artifact、publication 与 owner answer | MAS declarative policy + independent Review + registry-bound authority function |

`skill` 与 `domain_handler` 出现在默认 surface 退役清单中，指的是 MAS
repo-local wrapper / default caller 已退役，不是删除领域输入。Canonical primary
skill 继续作为 declarative pack source 并由 OPL 生成/托管；
`evaluate_paper_mission_authority` 继续作为 registry-bound 医学 authority function
被 OPL host 调用。两者都不拥有 CLI、MCP、session、lifecycle、transport 或
transition materialization。

## 唯一保留实现

`src/med_autoscience/authority_handlers/paper_mission.py::evaluate_paper_mission_authority` 是唯一保留的非声明式 authority function。它只消费 host 注入的 exact refs，执行确定性医学 authority evaluation，并返回 owner receipt、route-back、quality debt、typed blocker、human gate 或 invalid-host-input；它不做文件、网络、进程、runtime、package、session 或 transition 操作。

## Receipt 边界

OPL Connect / Pack / Runway receipt 只证明对应 transport、materialization 或 attempt 事实，不等于医学 verdict、publication/submission readiness、MAS owner receipt 或 live paper progress。任何 live claim 仍需 fresh StageRun/Attempt refs、独立 Review receipt 和 MAS owner acceptance evidence。

旧路径的逐文件 provenance 由 Git history 持有。不得为兼容、诊断或测试恢复已删除的 active implementation 或 machine contract。
