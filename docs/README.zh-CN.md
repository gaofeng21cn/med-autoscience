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

## 目录地图

| 目录 | 用途 |
| --- | --- |
| [runtime](./runtime/README.md) | 运行时合同、控制面、读模型、展示合同和活跃设计。 |
| [program](./program/README.zh-CN.md) | Program 生命周期组合：论文自治目标、产品化/框架化实现依托、已落地基础 owner 文档和 program 级协调。 |
| [capabilities](./capabilities/README.zh-CN.md) | 能力族文档，例如 medical display。 |
| [references](./references/README.zh-CN.md) | 支撑参考、定位、集成说明、parity 材料和验证记录。 |
| [policies](./policies/README.md) | 稳定内部规则和长期运行边界。 |
| [history](./history/README.zh-CN.md) | dated snapshot、provenance、退役 board、归档计划和过程稿。 |

这张表是生命周期层级。核心文档与 runtime / policy owner surface 承担当前真相；`program` 承担目标、实现依托和已落地基础的组合治理；`references` 承担支撑上下文；`history` 承担 provenance 和退役材料。

## 阅读规则

先读核心文档，再进入对应子目录索引。详细文件清单由各子目录 README 承担，本页只保留短导航。

`README*` 和 `docs/**` 是人读面。代码、测试、runtime status 和 contract 应依赖 schema、durable JSON、source path 或 `runtime:*`、`program:*`、`policy:*`、`human_doc:*` 等语义 ID，不应把 Markdown prose 文案钉成机器接口。
