# Display Pack v2 落地状态

Owner: `MedAutoScience`
Purpose: `display_pack_current_status`
State: `active_current_truth`
Machine boundary: 本文总结 current boundary。机器事实归 action catalog、display contracts、pack locks、render/QC artifacts与 owner receipts。

## 结论

Display Pack v2 的 domain semantics、artifact/quality contract 与 Stage Tool Affordance Boundary 已落地；公开执行收敛到 OPL-hosted Stage actions + OPL package/runtime substrate。旧 MAS direct display actions/handlers 尚有内部 caller，属于待迁 residue，不能写成已物理退役。该结构不表示真实 paper display 或 publication readiness 已完成。

## Current surfaces

| Surface | Owner | 状态 |
| --- | --- | --- |
| Figure intent / claim-data refs / quality policy | MAS | `landed` |
| Stage Tool Affordance Boundary | OPL + MAS declarative pack | `landed public/default path` |
| Pack install/registry/cache/lock | OPL / ScholarSkills | `landed substrate` |
| Environment prepare/run | OPL | `landed handoff` |
| Render transport / StageRun / hosted workbench | OPL | `landed substrate` |
| Layout/visual/claim QC refs | MAS + OPL transport | `landed` |
| Publication/artifact authority | MAS owner | `retained authority` |
| Legacy `display_pack_*` direct actions/handlers | MAS migration residue | `not public; physical retirement pending caller migration` |
| 真实 paper/publication evidence | live owner surfaces | `partial_deferred` |

## Public/default execution

Display 在 V2 中由以下 Stage 承载：

- `manuscript_authoring`：形成 figure intent/spec，并通过 affordance 调用模板、renderer 与 composition；
- `review_and_quality_gate`：消费 deterministic QC、visual audit 与 claim-display consistency refs；
- `finalize_and_publication_handoff`：绑定 final display、package 与 owner authority refs。

普通调用不再依赖 MAS 手写 argparse/MCP glue，也不直接调用 `display_pack_*`。新增 display mode时更新 ScholarSkills capability descriptor、Stage Tool Affordance Boundary 与 MAS domain quality/authority contract；只有出现独立开放判断、owner 或 quality gate 时才新增 Stage。

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
