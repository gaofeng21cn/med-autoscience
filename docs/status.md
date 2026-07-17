# 当前状态

Owner: `MedAutoScience`
Purpose: `current_status_summary`
State: `active_current_truth`
Machine boundary: 本文只总结 repo current state。具体 study/runtime 状态必须 fresh 读取 OPL StageRun/readback、MAS owner results、workspace artifacts 与 receipts。

## 结论

MAS 的 repo/source/control-plane 已收敛为标准 OPL Agent：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + registry-bound minimal authority functions`

MAS 不再持有私有 scheduler、runner、queue、session store、lifecycle/SQLite、
StateIndex、status/workbench、CLI/MCP/product wrapper、provider/package transport、
NextAction、PaperRecovery、stage terminalizer 或私有 quality validator。通用能力由
OPL Pack / Connect / Runway / Ledger / Workspace / Console 提供；医学专业能力由
declarative pack、ScholarSkills、独立 Review 与三个最小 authority functions 提供，未作
功能降级。

这项结论只覆盖结构和 source closure，不等于 live runtime、paper progress、
publication/submission ready 或 production ready。

## 当前机器形态

| Surface | Current state |
| --- | --- |
| Identity | canonical agent/package id `mas`；machine domain id `medautoscience`；`med-autoscience` 只作 repo/package/plugin locator |
| Package | repo package manifest 声明 SemVer `0.2.13`；`mas-scholar-skills` 以 `>=0.2.0 <0.3.0` 为硬依赖，并提供 reference verification 与 scientific search adapter modules；exact installed resolution、content lock 与生命周期 currentness 统一归 `opl packages` fresh readback |
| Declarative pack | `agent/` 持有 primary skill、六个 Stage、prompts、knowledge 与 quality gates；plugin skill 是字节一致的分发镜像 |
| Action catalog | `family-action-catalog.v2`：六个公开 Stage action + 两个无用户 surface 的内部 authority actions |
| Generated surfaces | CLI、MCP、Skill、product-entry、status、workbench 与 default domain-handler surface 全由 OPL 生成或托管 |
| Runtime | StageRun、Attempt、Temporal、session、retry、StateIndex、storage/lifecycle、observability 与 transition materialization 全归 OPL |
| Route owner | decisive Codex Attempt 决定领域 route；OPL StageRun controller 只校验并物化 transition |
| Provider/resource | OPL Connect / Pack 生成 exact-path、digest-bound receipt；MAS 只消费 receipt 并作医学判断 |
| Publication handoff | `publication_generation` 强制同代绑定 package、submission status、publication evaluation、next action 与 projection manifest；MAS owner receipt 授权 OPL Pack 原子投影完整 submission tree，但不授权 publication/submission ready |
| Retained code | `evaluate_candidate_admission_authority`、`evaluate_paper_mission_authority` 与 `evaluate_agent_lab_self_evolution_closeout` 是仅有的非声明式 authority functions；不持有 runtime、session、lifecycle 或 transition 权限 |
| Source morphology | `src/med_autoscience/` 只保留 package init、三个 authority handlers、共享纯校验 helper 与 CSL assets |

## 0.2.13 validator Release Set 边界

`mas-validator-0.2.13` 只支持 exact-byte domain validation：generation manifest、
candidate admission、paper mission 与 Stage minimum-scope 记录必须在 ref、size、SHA、
generation、receipt inventory 和 typed verdict 上一致。机器 receipt 见
`contracts/mas_validator_release_set_receipt.json`，canonical source ref 为
`refs/tags/v0.2.13`。

该 Release Set 不是独立 trust root。自洽 hash 只能证明输入记录内部字节一致，不能证明
issuer 身份；若恶意 host 同时伪造完整 adjudicator、currentness、review 与 owner-ledger
记录，repo-local validator 本身不能识别。正式消费必须由 OPL Framework 提供 managed
authority-attempt 与 owner-ledger provenance gate，缺失时 fail closed。因此 package
validator ready 不等于 authoring、launch、publication 或 submission clearance；DM003
在 platform provenance gate 和 installed managed-source currentness 完成前仍不得启动
authoring。

## 结构验收

当前结构 readback 必须同时满足：

- generated/default interfaces 全部 ready；
- 8/8 default-caller retirement gates closed，active deletion worklist 为零；
- conformance passed；
- private-platform residue decision item 为零且 state 为 `verified_zero`；
- source closure unresolved edge、audit mismatch 与 unreachable/private generic residue 全为零；
- primary skill 与 plugin carrier 字节一致；
- repo hygiene 与 no-resurrection scan 通过。

OPL read model 不替 MAS 签发物理删除权，因此
`default_caller_delete_ready=false` 与 `no_further_opl_default_caller_delete_work=true`
可以同时成立：前者冻结 false-authority，后者证明已无结构工作单。

## MAS 保留 authority

MAS 保留的是领域语义，不是平台实现：

- medical study/source truth 与 evidence acceptance；
- independent Review 的医学质量判断；
- publication、submission、artifact 与 memory authority；
- owner receipt、route-back、quality debt、typed blocker 与 human gate。

这些能力通过声明、专业 Skill、review outcome 和 registry-bound authority result
进入 OPL，不通过 MAS-local runtime/controller 实现。

## Live evidence tail

State: `partial_deferred`

以下 claim 仍须 fresh owner/live evidence，当前不得声明 ready：

- OPL StageRun/Attempt same-identity readback 与 provider long-soak；
- 真实 paper line 的 owner receipt、stable typed blocker、human gate 或 artifact semantic delta；
- independent reviewer/auditor receipt 与 publication owner verdict；
- managed authority-attempt / owner-ledger provenance gate，证明 receipt issuer 不是
  developer checkout 或 host 自行声明；
- submission/current-package authority；
- restart/retry/dead-letter 与 production no-forbidden-write evidence。

contracts、tests、descriptor ready、projection clean、queue empty、candidate package 与
docs 不替代上述证据。

## 维护入口

- [项目概览](./project.md)
- [架构](./architecture.md)
- [不可变约束](./invariants.md)
- [关键决策](./decisions.md)
- [Active plan](./active/mas-ideal-state-gap-plan.md)
- [私有控制面退役记录](./history/standard-agent-private-control-plane-retirement.md)

## Agent Lab 自进化 closeout

MAS declarative pack 现已提供 SHA 绑定的 `write` Stage completion policy
projection、high-risk owner-gated mechanism promotion policy，以及
registry-bound target-owner closeout handler。这补齐了 fresh re-evaluation 的
MAS 语义与 owner consumption 缺口，但不表示 DM003 或任何论文已达到
publication/submission ready；被阻断的医学 scorecard 在 re-evaluation 中必须继续
保持 blocked。
