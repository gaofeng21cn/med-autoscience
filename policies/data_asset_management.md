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

如果 `datasets/<family>/<version>/dataset_manifest.yaml` 存在，系统会把它视为该版本的 release contract 来源，并登记：

- `dataset_id`
- `raw_snapshot`
- `generated_by`
- `main_outputs`
- `notes`
- `release_contract`

同时会补充一层基于目录本身计算出来的 `inventory_summary`，用于记录：

- 文件数
- 总大小
- 声明主输出是否真实存在

推荐在 `dataset_manifest.yaml` 中显式维护 `release_contract`，用于描述这次私有数据更新的性质，例如：

- `update_type`
- `change_summary`
- `qc_status`
- `owner`
- `source_centers`

## 2. 公开数据扩展模块

用于记录可用于以下目的的公开数据：

- 外部验证
- 队列扩展
- 机制 / 功能扩展
- 基准迁移

默认登记位置：

- `portfolio/data_assets/public/registry.json`

这部分强调的是“有明确用途再引入”，而不是为了堆工作量而装饰性加入。

当前 public registry 使用 schema v2，并建议显式维护：

- `dataset_id`
- `source_type`
- `accession`
- `disease`
- `modality`
- `endpoints`
- `roles`
- `target_families`
- `target_dataset_ids`
- `target_study_archetypes`
- `cohort_size`
- `license`
- `access_url`
- `status`
- `rationale`
- `notes`

其中：

- `roles` 当前用于表达 `external_validation`、`cohort_extension`、`mechanistic_extension`、`benchmark_transfer`
- 至少应有一类 target scope，用于说明该公开数据面向哪些 family / dataset / archetype
- registry 中只有通过校验的 public dataset 才会进入 impact 评估

## 3. 数据影响评估

用于评估：

- 某个 study 当前绑定的数据版本是否已经落后于最新私有版本
- 某个 study 是否已经存在可用的公开数据支持
- 当某个 study 落后于最新私有版本时，是否已经生成从旧版本到最新版本的差异报告

默认输出位置：

- `portfolio/data_assets/impact/latest_impact_report.json`

私有版本差异报告默认写入：

- `portfolio/data_assets/private/diffs/<family>/<from_version>__<to_version>.json`

当 quest 已进入 runtime 时，平台还会额外提供 quest 级 `data_asset_gate`，用于在以下情形下阻断无意义继续推进：

- 当前 study 绑定的是落后于最新私有版本的旧 freeze
- 当前 study 已出现新的 public-data 扩展机会，但尚未明确是否纳入

## 4. ToolUniverse 适配

`ToolUniverse` 在 `MedAutoScience` 中不是主控，而是外部工具适配层，主要承担：

- 知识检索
- 功能分析
- 通路 / 调控解释

它的价值在于让功能分析和知识扩展进入正式平台，而不是散落为临时脚本。

## 当前原则

- 私有数据演进优先级高于公开数据扩展
- 数据更新必须可追踪、可落盘、可评估对现有 study 的影响
- 私有版本差异必须尽量基于显式 manifest 和目录事实，不依赖推测性分类
- 公开数据只有在能增强证据强度时才纳入
- ToolUniverse 是外挂，不替代 `DeepScientist` 主控
