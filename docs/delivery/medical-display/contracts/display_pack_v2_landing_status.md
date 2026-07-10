# Display Pack v2 落地状态

Owner: `MedAutoScience`
Purpose: `display_pack_current_status`
State: `active_current_truth`
Machine boundary: 本文总结 current boundary。机器事实归 action catalog、display contracts、pack locks、render/QC artifacts与 owner receipts。

## 结论

Display Pack v2 的 repo/source/control-plane 结构已经落地，并收敛到 MAS domain actions + OPL pack/runtime substrate。它不是 repo-local CLI/runtime，也不表示模板市场、真实 paper display或 publication readiness已完成。

## Current surfaces

| Surface | Owner | 状态 |
| --- | --- | --- |
| Figure intent / claim-data refs / quality policy | MAS | `landed` |
| Display actions与 schemas | MAS declarative pack | `landed` |
| Pack install/registry/cache/lock | OPL / ScholarSkills | `landed substrate` |
| Environment prepare/run | OPL | `landed handoff` |
| Render transport / StageRun / hosted workbench | OPL | `landed substrate` |
| Layout/visual/claim QC refs | MAS + OPL transport | `landed` |
| Publication/artifact authority | MAS owner | `retained authority` |
| 真实 paper/publication evidence | live owner surfaces | `partial_deferred` |

## Standard actions

OPL generated interfaces消费 action catalog中的：

- `display_pack_capability_discover`
- `display_pack_figure_plan`
- `display_pack_orchestrate`
- `display_pack_preflight`
- `display_pack_render`

普通调用不再依赖 MAS 手写 argparse/MCP glue。新增 display mode时更新 catalog/schema/handler target，不新增 repo-local wrapper。

## Render boundary

Renderer可以是 R/ggplot2 subprocess或显式受控 adapter。R/Bioconductor需求由 MAS requirement profile声明，OPL environment substrate负责准备和运行。MAS 不在 workspace/import/installer内安装依赖。

Render结果至少保留：

- input/claim/data refs；
- pack/template/version/lock refs；
- renderer/environment refs；
- artifact hashes与 layout refs；
- QC/visual audit refs；
- owner/authority boundary。

## Authority

OPL pack lock、render attempt、golden match、layout QC或 hosted workbench projection不得：

- 修改 claim/data/statistics truth；
- 签 MAS owner receipt；
- 授权 artifact mutation；
- 关闭 publication/submission gate；
- 把 render success解释成 paper progress。

MAS visual/publication owner消费这些 refs后，才可形成 quality route、artifact decision或 stable typed blocker。

## Catalog 与 provenance

通用 pack/template source归 ScholarSkills/OPL维护。MAS 只保留 external source/substrate refs、domain action metadata与 forbidden-authority boundary；不跟踪 generated display catalog，也不把 retired alias当 current inventory。

## Live evidence tail

当前结构状态不能替代：

- 真实 paper figure/table render；
- independent visual/medical review receipt；
- claim-to-display closure；
- canonical package freshness；
- publication/submission owner verdict；
- long-running OPL render/runtime evidence。

这些证据到来前，Live evidence保持 `partial_deferred`。

## 相关入口

- [Medical display](../README.md)
- [Display Agent OS target](./display_pack_agent_os_target.md)
- [Visual audit protocol](./medical_display_visual_audit_protocol.md)
- [Runtime boundary](../../../runtime/contracts/runtime_boundary.md)
- [Active plan](../../../active/mas-ideal-state-gap-plan.md)
