# Delivery 文档

Owner: `MedAutoScience`
Purpose: `medical_research_delivery_support`
State: `active_support`
Machine boundary: 人读索引。交付 authority 继续归 study workspaces、artifact/package contracts、generated submission material、source、runtime evidence 与 owner receipts。

本目录承接 MAS manuscript、package、submission/export、review/publication gate 与 delivery 支撑。可跨 MAS/MAG/RCA 复用的通用 artifact lifecycle primitive 应记录为 MAS-to-OPL 上收候选。

Delivery active board 只允许保存当前交付能力族的唯一 owner round、phase、下一步和退出条件。已吸收 round、外部 exemplar intake、旧 owner brief、长增量清单和 closeout proof 归 `docs/history/**` 或 delivery provenance，不在 active board 中累积。

当前入口先看：

- [架构](../architecture.md)
- [当前状态](../status.md)
- [Runtime docs](../runtime/README.md)
- [Standard Domain Agent Skeleton](../runtime/contracts/standard_domain_agent_skeleton.md)
- [Inspection package 交付契约](inspection_package.md)

## Standard Agent Delivery Boundary

标准 OPL Domain Agent skeleton 只声明 delivery / artifact 相关 repo-source anchors 和 locator-only 边界。真实 manuscript、figure/table、submission package、`current_package`、publication eval、controller decisions、artifact mutation receipt 和 rebuild proof 仍归 MAS workspace / artifact authority surfaces，不进入 repo skeleton。

OPL generated / hosted surfaces 可以展示或运输 artifact locator refs、owner receipt refs、inspection-package pointer、artifact lifecycle report、retention candidate 和 typed blocker refs。它们不能授权 artifact mutation、package freshness、publication quality、submission readiness、delivery sync、cleanup / restore / retention apply 或 App release readiness。

若 delivery 文档、display pack 或 inspection package 只证明存在 derived artifact、blocked snapshot、review pointer 或 read-only projection，它只能作为 human inspection / evidence input；不能被写成 canonical artifact authority、source readiness verdict、publication gate closeout 或 `current_package` freshness proof。
