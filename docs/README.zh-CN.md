# 文档索引

[English](./README.md) | **中文**

这个目录是 `Med Auto Science` 的技术阅读层。仓库首页继续作为医生、PI 和医学研究团队的默认入口。

## 先读这里

| 需求 | 入口 |
| --- | --- |
| 产品角色与边界 | [项目概览](./project.md) |
| 当前运行真相 | [当前状态](./status.md) |
| 架构与 owner 边界 | [架构](./architecture.md) |
| 不可变约束 | [不可变约束](./invariants.md) |
| 持久决策 | [关键决策](./decisions.md) |
| 文档生命周期规则 | [文档组合治理](./docs_portfolio_consolidation.md) |

## OPL 系列分层

OPL 系列项目的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.zh-CN.md`。其中维护 OPL Framework 的全局目标、全局差距、通用能力上收边界、App/workbench 目标和跨仓开发顺序。

MAS 本仓只维护医学研究 domain agent 的目标、当前差距、study/publication/artifact authority、direct MAS app skill path、OPL-hosted sidecar/projection/receipt 边界，以及哪些通用 runtime、memory、artifact lifecycle、workbench 和 observability primitive 应上收到 OPL。MAG、RCA、MDS 或 OPL-owned App/workbench 的并行 backlog 不在 MAS 文档中维护。

## 目录地图

| 目录 | 用途 |
| --- | --- |
| [active](./active/README.md) | 当前执行、当前计划、当前差距与 active baton；旧 `program/` 内容由这里维护。 |
| [public](./public/README.md) | MAS 对外公开叙事和用户第一阅读层。 |
| [product](./product/README.md) | MAS app skill、direct product entry、operator/workbench-facing 指南。 |
| [runtime](./runtime/README.md) | 运行时合同、控制面、读模型、展示合同和活跃设计。 |
| [delivery](./delivery/README.md) | manuscript、package、submission/export 与医学研究交付 authority。 |
| [source](./source/README.md) | study workspace、source readiness、source truth consumption 与 external research intake。 |
| [policies](./policies/README.md) | 稳定内部规则和长期运行边界。 |
| [specs](./specs/README.md) | 当前仍有效的技术规格索引；旧 spec 需标清 active/history。 |
| [references](./references/README.zh-CN.md) | 支撑参考、定位、集成说明、parity 材料和验证记录。 |
| [history](./history/README.zh-CN.md) | dated snapshot、provenance、退役 board、归档计划和过程稿。 |

这张表采用 OPL-family canonical docs taxonomy。旧 `program/` 与
`capabilities/` 目录已物理退役；program-baton 内容进入 `active/`，
medical-display 能力族进入 `delivery/medical-display/`。

## 阅读规则

先读核心文档，再进入对应子目录索引。详细文件清单由各子目录 README 承担，本页只保留短导航。

`README*` 和 `docs/**` 是人读面。代码、测试、runtime status 和 contract 应依赖 schema、durable JSON、source path 或 `runtime:*`、`program:*`、`policy:*`、`human_doc:*` 等语义 ID，不应把 Markdown prose 文案钉成机器接口。
