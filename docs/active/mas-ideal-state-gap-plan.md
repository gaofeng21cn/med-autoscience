# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读完成度矩阵。机器事实归 contracts、source、tests、OPL generated/readback surfaces、workspace artifacts 与 owner receipts。
Date: `2026-07-14`

## 目标态

MAS 的 repo 目标形态固定为：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + one registry-bound authority function`

canonical agent/package id 是 `mas`，machine domain id 是 `medautoscience`。OPL 从 MAS pack、action catalog、schemas 与 handler registry
生成或托管通用 interface/runtime；MAS 只持有医学语义声明、专业能力依赖与一个
无法上收的纯 authority function。

## 当前结论

功能/结构差距已经关闭。旧私有控制面、runtime、transport、wrapper、validator
和第二真相源均已物理退役；source closure、default-caller closure 与
no-resurrection guard 是关闭门。Live Evidence 独立为 `partial_deferred`，不反向
恢复 MAS-local 平台，也不把结构完成包装为 ready。

## Plan Completion Audit

| 条目 | 状态 | 完成度 | Fresh executable evidence |
| --- | --- | ---: | --- |
| Declarative Medical Research Pack | `done` | 100% | pack/action/schema validation、six-Stage interface readback |
| OPL generated/hosted default surfaces | `done` | 100% | interfaces ready；8/8 retirement gates closed；0 active worklist |
| 私有 runtime/controller/transport 物理退役 | `done` | 100% | exact source morphology、repo hygiene、active machine no-resurrection scan |
| 唯一 authority function 边界 | `done` | 100% | closed registry、strict schemas、terminal/no-effect focused tests |
| OPL Pack/Connect receipt consumption | `done` | 100% | exact path/digest contract、false-authority consumer tests |
| Route owner 拆分 | `done` | 100% | decisive Attempt semantic decision + OPL controller materialization contracts |
| Package/ScholarSkills 闭包 | `done` | 100% | MAS `0.2.7`、ScholarSkills exact lock `0.2.3`（range `>=0.2.0 <0.3.0`）、required capability ABI 与两个 package-owned Connect adapter modules |
| Core docs 与历史归位 | `done` | 100% | current docs 无 active private-control-plane claim；单一 history tombstone |
| Live runtime / paper / release evidence | `partial_deferred` | 0% | 必须由真实 StageRun、owner receipt、artifact、publication/release readback后置提供 |

这里的 `100%` 只表示对应 repo/source/contract 条目有 fresh executable evidence；
不跨越最后一行的 live/release authority。

## 物理形态

`src/med_autoscience/` 只允许：

- package init；
- `authority_handlers/paper_mission.py`；
- CSL assets。

`agent/` 持有 rich declarative pack，`agent/stages/stage_route_contract.yaml` 是唯一
Stage route YAML source；Python wheel 不携带第二份 route mirror。`contracts/` 持有 machine inputs、schema 与
false-authority boundaries；`runtime/authority_functions/` 只解释唯一 handler ABI，
不包含 runtime engine。

## 已上收的通用能力

| 通用能力 | Owner |
| --- | --- |
| CLI / MCP / Skill / product/status/workbench | OPL generated/hosted surfaces |
| StageRun / Attempt / session / Temporal / retry | OPL Runway / Ledger |
| workspace / source / StateIndex / artifact locator | OPL Workspace / Ledger / Vault |
| provider invocation / credentials / retry / receipt | OPL Connect |
| package / environment / submission resource materialization | OPL Pack / environment substrate |
| route transition validation/materialization | OPL StageRun controller |

MAS 不为这些能力保留 wrapper、facade、compatibility alias、diagnostic runtime 或
本地 persistence。

## 保留的领域能力

- canonical primary skill 与 plugin carrier mirror；
- Stage/route/prompt/knowledge/quality-gate declarations；
- ScholarSkills 专业能力闭包；
- independent Review 与 publication/artifact/memory policy；
- 一个 registry-bound paper-mission authority function。

新增非声明式实现必须先证明无法由 OPL primitive 或 declarative pack表达，并进入
`contracts/authority_kernel_inventory.json`，写清 active caller、allowed/forbidden
writes、不能上收原因、receipt/blocker/ref 输出和 retirement gate。

## Live evidence tail

State: `partial_deferred`

| Claim | 必需证据 |
| --- | --- |
| OPL runtime ready | same-identity StageRun/Attempt readback、provider running、restart/retry/dead-letter/long-soak |
| Paper progress | MAS owner receipt、stable typed blocker、human gate、route-back 或 paper/artifact semantic delta |
| Quality/publication ready | independent reviewer/auditor receipt、publication owner verdict 与 current artifact refs |
| Submission/current package ready | submission authority、fresh manifest/package receipt 与 owner readback |
| Production ready | live runtime/readback 与 production no-forbidden-write proof |

## 后续维护规则

1. 普通 action 只改 catalog/schema/Stage binding，由 OPL 生成 interface。
2. 通用 runtime、index、lifecycle、environment、observability、resource provision 和 workbench需求直接路由 OPL。
3. 旧路径只保留 Git/history provenance 与 machine no-resurrection guard，不新增 compatibility 入口。
4. Live evidence 写回对应 runtime/owner/release surface，不混入结构完成度。

## 相关入口

- [当前状态](../status.md)
- [架构](../architecture.md)
- [不可变约束](../invariants.md)
- [Runtime boundary](../runtime/contracts/runtime_boundary.md)
- [私有控制面退役记录](../history/standard-agent-private-control-plane-retirement.md)
