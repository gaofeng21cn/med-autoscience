# Product 文档

Owner: `MedAutoScience`
Purpose: `domain_product_entry_support`
State: `active_support`
Machine boundary: 人读索引。可调用真相继续归 MAS app skill、CLI/MCP/API、contracts、source 与 product-entry manifests。

本目录承接 MAS direct app-skill、product-entry 与 operator 指南。它不持有 study truth、publication verdict、manuscript/package authority 或 OPL framework primitive。

当前入口先看：

- [项目概览](../project.md)
- [架构](../architecture.md)
- [Runtime docs](../runtime/README.md)
- [Inspection package 产品契约](inspection_package.md)
- [Progress Portal 展示合同](../runtime/display/progress_portal.md)
- [OPL App MAS Runtime Workbench Program](../active/opl_app_mas_runtime_workbench_program.md)
- [Progress Portal OPL App Integration](../references/integration/progress_portal_opl_app_integration.md)

## 当前边界

MAS product surface 只解释 direct app-skill、product-entry、Progress Portal、owner-route handoff、sidecar dispatch refs 和 OPL App/workbench 消费边界。当前机器真相显示：

- `contracts/generated_surface_handoff.json` 声明 CLI、MCP、Skill、product-entry manifest、sidecar export/dispatch、status read model、workbench drilldown 和 test harness 的 generated/default owner 是 `one-person-lab`；MAS 只提供 domain handler、domain refs、owner receipt、typed blocker、authority refs 和必要医学 helper。
- `contracts/functional_privatization_audit.json` 把 generic scheduler、daemon、queue、attempt ledger、generic runner、generic workbench、memory locator、artifact lifecycle 和 observability 归为 OPL / shared-family owner；MAS 不能把 repo-local product/status/workbench shell 写成长期 generic platform。
- `contracts/test-lane-manifest.json` 的 `mas-workbench-projection` 与 `mas-functional-consumer-followthrough` 只允许 App/workbench 消费 MAS refs-only projection 和 action receipt，不允许写 study truth、publication eval、controller decisions、terminal commands、current package、evidence/review ledger、memory body 或 artifact authority。
- Progress Portal 只保留 MAS-owned 静态 read-model / display materializer 与 OPL handoff refs；`medautosci workspace progress-portal`、`--serve`、`--enable-actions` 和 `ops/mas/bin/start-web` 不是当前入口。Portal 写 display/read-model artifact，不写 paper/package、publication gate、controller decision 或 provider runtime state。

## 当前文档职责

| 文档 | 当前职责 | 不承载 |
| --- | --- | --- |
| `README.md` | 本目录入口和 product/workbench owner 边界。 | 不维护执行计划、proof ledger 或 current gap matrix。 |
| `inspection_package.md` | inspection package 产品契约。 | 不授权 publication verdict 或 artifact authority。 |
| `../runtime/display/progress_portal.md` | MAS Progress Portal read-model/display materializer 合同和 OPL handoff refs。 | 不定义 OPL App 主工作台 UI，不写 study truth，不提供 generic runtime drilldown owner，不恢复 repo-local HTTP service。 |
| `../active/opl_app_mas_runtime_workbench_program.md` | MAS refs-only projection 进入 OPL App/workbench 的 active support owner。 | 不复制通用 workbench，不定义 publication readiness。 |
| `../references/integration/progress_portal_opl_app_integration.md` | Progress Portal 与 OPL App 集成参考。 | 不成为 active backlog 或机器接口。 |

## 阅读规则

- 若要判断当前 MAS product/status/workbench 是否已完成 default caller cutover，读 [MAS 理想目标态差距与完善计划](../active/mas-ideal-state-gap-plan.md) 的 `workbench_sidecar_status_cutover`，再读 contracts 和 focused tests；不要从本文或 Portal UI 文案推断完成。
- 若要实现 App-native MAS study workbench，先读 `opl_app_mas_runtime_workbench_program.md` 和 OPL App 仓合同；本仓只提供 MAS refs、receipt、blocker、source refs 和 forbidden-write 规则。
- 若要审计 Progress Portal，按 display contract 读取：Portal 是 MAS-owned read-model/display materializer 和 OPL handoff refs surface，长期主用户工作台归 OPL App。
