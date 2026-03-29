# Data Asset Management

`MedAutoScience` 默认把医学研究中的数据看成持续演进的研究资产，而不是一次性静态输入。

这层能力默认不是给人手工维护 `registry.json` 用的，而是给 `Codex` 这类 Agent 提供稳定的 mutation / refresh 接口，再把结果回显给人类审核。

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

当 Agent 已经把新数据放到 `datasets/<family>/<version>/` 下时，推荐通过结构化 update payload 调用：

- `action = "upsert_private_release_manifest"`

由平台统一写入或更新 `dataset_manifest.yaml`，然后自动 refresh registry / impact / startup readiness。

这里采用严格 mutation 语义：

- `datasets/<family>/<version>/` 必须已经存在
- `manifest.main_outputs` 指向的文件必须真实存在
- 不允许把“空目录 + YAML”登记成可用 release

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
- `status = rejected` 的 public dataset 不再进入扩展机会评估

当 Agent 需要新增或更新 public dataset 时，推荐通过结构化 update payload 调用：

- `action = "upsert_public_dataset"`
- `action = "update_public_dataset_status"`

这里不会用静默纠正去掩盖输入错误：

- 非法 `status` 直接拒绝
- 非法 `roles` 直接拒绝
- mutation log 需要能对上原始 payload 与真实 mutation 结果

## 3. 数据影响评估

用于评估：

- 某个 study 当前绑定的数据版本是否已经落后于最新私有版本
- 某个 study 是否已经存在可用的公开数据支持
- 当某个 study 落后于最新私有版本时，是否已经生成从旧版本到最新版本的差异报告

默认输出位置：

- `portfolio/data_assets/impact/latest_impact_report.json`

私有版本差异报告默认写入：

- `portfolio/data_assets/private/diffs/<family>/<from_version>__<to_version>.json`

数据 mutation 的审计日志默认写入：

- `portfolio/data_assets/mutations/<timestamp>_<action>.json`

这组日志属于正式审计链路，而不是“成功后顺手写一下”的附属文件：

- mutation 开始前就会先占位写入
- mutation 本身失败会记录 `mutation_failed`
- mutation 已落地但 refresh 失败会记录 `refresh_failed`
- 只有 mutation 与 refresh 都成功，才会记录 `applied`

当 quest 已进入 runtime 时，平台还会额外提供 quest 级 `data_asset_gate`，用于在以下情形下阻断或提醒无意义继续推进：

- 当前 study 绑定的是落后于最新私有版本的旧 freeze
- 当前 study 绑定的私有 release 契约未闭合
- 当前 study 已出现新的 public-data 扩展机会，但尚未明确是否纳入

其中：

- 私有数据过期 / 契约未闭合属于 hard block
- public-data 扩展机会属于 advisory

## 4. ToolUniverse 适配

`ToolUniverse` 在 `MedAutoScience` 中不是主控，而是外部工具适配层，主要承担：

- 知识检索
- 功能分析
- 通路 / 调控解释

它的价值在于让功能分析和知识扩展进入正式平台，而不是散落为临时脚本。

## 当前原则

- 私有数据演进优先级高于公开数据扩展
- 数据更新必须可追踪、可落盘、可评估对现有 study 的影响
- 数据 mutation 必须优先通过 Agent 可调用的结构化接口完成，而不是直接编辑 registry
- 数据 mutation 不允许通过静默纠偏掩盖输入错误
- 私有版本差异必须尽量基于显式 manifest 和目录事实，不依赖推测性分类
- 公开数据只有在能增强证据强度时才纳入
- ToolUniverse 是外挂，不替代 `DeepScientist` 主控
