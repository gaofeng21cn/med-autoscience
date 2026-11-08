# 外部研究来源的权限边界

本文只定义 MDS/DeepScientist 来源的使用范围。MAS/OPL 当前架构见 [架构](../../architecture.md)。

MDS 与 DeepScientist 可以作为历史来源、显式归档导入、上游方法学习和冻结对照材料。它们不是 MAS 默认 runtime、诊断服务、WebUI、研究 owner 或质量裁决者。已有来源元数据见 [来源记录](../../references/med-deepscientist/source_provenance.json)，其中旧能力分类只解释当时采集的来源，不定义当前实现清单。

吸收外部方法时记录 source ref、许可、保留范围、当前接收 owner 和可验证结果。医学知识、质量与科研方法进入 MAS 或 ScholarSkills；通用执行、恢复、工具传输与 UI 进入各平台 owner。不得恢复 MAS 私有运行面或平行接口。

历史 fixture、覆盖率、scorecard、provider completion 和 archive import 不签发当前 source readiness、quality、publication、artifact 或 memory authority。当前 authoring、review 与 owner receipt 必须使用当前输入和相应合同。

旧 MDS 行为等价矩阵、导入 wrapper 和 controller API 已退出当前文档入口。需要审计历史实现时使用 Git 或冻结来源，不新增兼容别名。
