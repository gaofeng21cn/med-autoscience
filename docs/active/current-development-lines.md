# MAS 当前开发线路

Owner: `MedAutoScience`
Purpose: `active_line_index`
State: `active_support_index`
Machine boundary: 本文是人读索引。唯一结构完成度入口是 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)。

## 当前主线

MAS repo 当前只维护两类工作：

1. `Declarative Medical Research Pack`
   - stages、prompts、knowledge、quality gates；
   - 六个公开 Stage action、一个内部 registry-bound authority action、V2 schemas 与 domain route/profile；
   - runtime environment requirement profile；
   - primary skill 与 plugin carrier currentness。

2. `Minimal Medical Authority Functions`
   - study/source truth；
   - AI reviewer/publication quality；
   - artifact/memory authority；
   - owner receipt、typed blocker、human gate、route-back。

CLI、MCP、product-entry、status、workbench、runtime lifecycle、StateIndex、storage/health 和环境 provisioning 归 OPL generated/hosted surfaces，不再是 MAS 开发线。

## Active lines

| Line | Owner | 当前工作 |
| --- | --- | --- |
| Pack currentness | MAS | action/schema/stage/skill declarations 与 OPL compiler input 同步 |
| Medical authority | MAS | 最小 authority function、forbidden-write guard、owner receipts |
| Generated interfaces | OPL | 从 catalog 生成 CLI/MCP/Skill/product/status/workbench |
| Runtime platform | OPL | StageRun、StateIndex、queue/attempt、lifecycle/storage、observability |
| Live evidence | MAS + OPL owners | fresh runtime/paper/quality/publication receipts；独立后置 |
| Structural closeout | MAS + OPL maintainers | V2 public/default cutover 已关闭；遗留 internal callers/source-closure/物理删除与最终双仓吸收仍待关闭 |

## 已关闭结构线

OE-01 至 OE-12 中 OE-03、OE-11 仍为 `partial`。旧 bootstrap、pytest aggregation、StateIndex pilot、installer、retirement subsystem、workbench、Tool Arsenal、CLI/MCP glue 与 legacy next-action producer 已退出 public/default surface；仍有 active caller 的 `domain_entry/mainline/read-model/queue` 源码只能作为迁移 residue，不能写成已物理退役。

`scripts/run-build-clean.sh` 继续承担正式 build-isolation；已退役的是旧 runtime/editable clean runner，不得把两者混写。Provider、paper progress、reviewer/publication、submission 与 production readiness 仍是独立 `partial_deferred` evidence tail。

## 维护规则

- 新需求先判断是 domain declaration/authority，还是 OPL platform responsibility。
- Platform requirement 写成 OPL-owned contract/ref，不在 MAS 新建 wrapper。
- Live evidence 不用 docs、tests、dry-run 或 projection 替代。
- 历史过程读 Git 与 `docs/history/`，不回填到 active docs。

## 导航

- [Active truth plan](./mas-ideal-state-gap-plan.md)
- [Project](../project.md)
- [Architecture](../architecture.md)
- [Status](../status.md)
- [Runtime boundary](../runtime/contracts/runtime_boundary.md)
