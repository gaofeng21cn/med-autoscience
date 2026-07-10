# MAS Medical Display

Owner: `MedAutoScience`
Purpose: `medical_display_entry`
State: `active_current_truth`
Machine boundary: 本文是人读入口。机器真相归 display actions/schemas、MAS figure quality/artifact authority 与 OPL pack/runtime refs。

## Owner split

Medical display 遵循标准 OPL Agent 边界：

- MAS 持有医学 figure intent、claim/data refs、quality gate、visual audit与 artifact/publication authority。
- OPL 持有通用 pack install/registry/cache/lock、renderer transport、generated interfaces、StageRun与 hosted workbench。
- ScholarSkills/display pack source提供通用模板与专业能力；不得写 MAS claim/data/statistics truth。

MAS 不维护 repo-local display CLI、catalog generator、installer或 workbench shell。

## Action surface

Display 由 action catalog 中五个标准 action表达：

- `display_pack_capability_discover`
- `display_pack_figure_plan`
- `display_pack_orchestrate`
- `display_pack_preflight`
- `display_pack_render`

OPL 从 catalog/schema 生成 CLI/MCP/Skill/product surface；MAS domain handlers只处理 figure intent、quality/authority boundary与结果 refs。

## Current flow

```text
current owner delta + claim/data refs
  -> figure intent / plan
  -> OPL pack resolve + environment prepare
  -> render attempt
  -> layout/visual/claim QC
  -> MAS visual audit and artifact authority
  -> publication-facing refs
```

R/Bioconductor requirement由 `contracts/runtime_environment_requirements.json` 声明，环境准备归 OPL `env prepare/run`。

## Ready boundary

Template resolved、render success、golden match、layout QC、workbench visible或 visual-audit scaffold都不单独等于 publication ready、submission ready、scientific claim authority或 artifact mutation authorization。最终结论必须回到 MAS owner receipt、quality/publication gate与 canonical artifact refs。

## 导航

- [Display Pack v2 status](./contracts/display_pack_v2_landing_status.md)
- [Display Agent OS target](./contracts/display_pack_agent_os_target.md)
- [Visual audit protocol](./contracts/medical_display_visual_audit_protocol.md)
- [Architecture](../../architecture.md)
- [Runtime boundary](../../runtime/contracts/runtime_boundary.md)
