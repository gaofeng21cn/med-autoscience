# MAS Medical Display

Owner: `MedAutoScience`
Purpose: `medical_display_entry`
State: `active_current_truth`
Machine boundary: 本文是人读入口。机器真相归 V2 Stage action catalog/manifest、Tool Affordance Boundary、MAS figure quality/artifact authority 与 OPL pack/runtime refs。

## Owner split

Medical display 遵循标准 OPL Agent 边界：

- MAS 持有医学 figure intent、claim/data refs、quality gate、visual audit与 artifact/publication authority。
- OPL 持有通用 pack install/registry/cache/lock、renderer transport、generated interfaces、StageRun与 hosted workbench。
- ScholarSkills/display pack source提供通用模板与专业能力；不得写 MAS claim/data/statistics truth。

MAS 不维护 repo-local display CLI、catalog generator、installer或 workbench shell。

## Stage affordance surface

Display 不再形成独立 public action family。普通执行由六个 OPL-hosted Stage action承载：

- `manuscript_authoring` 形成 figure intent/spec 并按需调用模板、renderer 与 composition 能力；
- `review_and_quality_gate` 消费 layout/visual/claim QC 与 independent review refs；
- `finalize_and_publication_handoff` 绑定 final display refs、package refs 与 owner authority。

OPL 通过 Stage Tool Affordance Boundary 发现 ScholarSkills/display pack、准备环境、执行 renderer 并运输 refs；MAS 只保留 figure intent、医学质量/artifact authority 与结果 refs，不维护 display handler、installer、catalog generator 或 renderer 副本。

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

- [Audit guide](./contracts/medical_display_audit_guide.md)
- [Visual audit protocol](./contracts/medical_display_visual_audit_protocol.md)
- [Figure route cookbook](./catalogs/medical_figure_route_cookbook.md)
- [Template backlog](./catalogs/medical_display_template_backlog.md)
- [Family roadmap](./portfolio/medical_display_family_roadmap.md)
- [Dependency environment boundary](./contracts/display_dependency_environment_os_target.md)
- [Architecture](../../architecture.md)
- [Runtime boundary](../../runtime/contracts/runtime_boundary.md)
