# MAS Product Surfaces

Owner: `MedAutoScience`
Purpose: `product_surface_index`
State: `active_current_truth`
Machine boundary: 本文是人读 product boundary。机器真相归 action catalog、generated surface handoff、domain handler results、OPL hosted readback 与 MAS owner receipts。

## 当前产品形态

MAS 不维护 repo-local product shell。产品入口由 OPL 从 MAS pack 生成或托管：

- CLI / MCP / Skill / product-entry；
- status read model / workbench drilldown；
- action transport 与 functional harness。

MAS 提供六个公开 Stage action、candidate admission 与 paper mission 两个无用户 surface 的内部 registry-bound authority actions、V2 schemas、body-free refs、owner receipts、typed blockers 与 authority refs。self-evolution closeout 只通过 closed handler registry 托管，不形成用户入口。

## 默认论文入口

公开论文推进从六个 OPL-hosted Stage action 中选择；candidate admission、paper mission 与 self-evolution closeout handlers 只供 host 内部调用，不是用户命令。默认控制链是：

`Codex CLI selected stage -> nonbinding route context -> OPL readback -> MAS owner consumption`

Product/workbench 不得从 queue、attempt、provider、旧 current work unit、PaperRecovery 或 UI 文案推断 current owner、paper progress 或 readiness。

## Workbench boundary

OPL hosted workbench 可以显示：

- stage/mission refs；
- owner receipt、typed blocker、human gate refs；
- evidence/artifact/authority refs；
- runtime diagnostics 与 currentness。

它不得写 study truth、publication eval、controller decision、canonical paper、artifact body、memory body 或 submission package。MAS 不再提供 repo-local cockpit、Portal、HTML/Markdown renderer 或 terminal action shell。

## Inspection package

Inspection package 是 human-inspection-only artifact：OPL 可以运输和展示它的 locator、
freshness、blocked context 与 feedback route，MAS owner chain 决定如何修订 canonical
paper。它不能授权 publication/submission、清除 quality gate、写 controller decision、
替代 canonical/current package，或用 materialized/export success 声明 ready。

## Live evidence

Product interface resolved、action schema valid、workbench visible 或 read model clean 都不等于 paper progress、quality ready、publication ready、runtime ready 或 production ready。对应 claim 必须读取 fresh owner/live/artifact receipt。

## 导航

- [Project](../project.md)
- [Status](../status.md)
- [Architecture](../architecture.md)
- [Runtime boundary](../runtime/contracts/runtime_boundary.md)
