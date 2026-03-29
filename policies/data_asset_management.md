# Data Asset Management

`MedAutoScience` 默认把医学研究中的数据看成持续演进的研究资产，而不是一次性静态输入。

这层能力分为四部分：

## 1. 私有数据版本登记

用于管理本地数据资产的演进，包括：

- 临床队列补充
- 随访刷新
- 个别字段的补全或纠错
- 多中心追加

第一期默认扫描面是 `datasets/<family>/<version>/`，并把版本登记写入：

- `portfolio/data_assets/private/registry.json`

## 2. 公开数据扩展模块

用于记录可用于以下目的的公开数据：

- 外部验证
- 队列扩展
- 机制 / 功能扩展
- 基准迁移

默认登记位置：

- `portfolio/data_assets/public/registry.json`

这部分强调的是“有明确用途再引入”，而不是为了堆工作量而装饰性加入。

## 3. 数据影响评估

用于评估：

- 某个 study 当前绑定的数据版本是否已经落后于最新私有版本
- 某个 study 是否已经存在可用的公开数据支持

默认输出位置：

- `portfolio/data_assets/impact/latest_impact_report.json`

## 4. ToolUniverse 适配

`ToolUniverse` 在 `MedAutoScience` 中不是主控，而是外部工具适配层，主要承担：

- 知识检索
- 功能分析
- 通路 / 调控解释

它的价值在于让功能分析和知识扩展进入正式平台，而不是散落为临时脚本。

## 当前原则

- 私有数据演进优先级高于公开数据扩展
- 数据更新必须可追踪、可落盘、可评估对现有 study 的影响
- 公开数据只有在能增强证据强度时才纳入
- ToolUniverse 是外挂，不替代 `DeepScientist` 主控
