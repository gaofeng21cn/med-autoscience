<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="MedAutoScience Logo" width="132" />
</p>

<h1 align="center">MedAutoScience 医学自动科研平台</h1>

<p align="center"><strong>A publication-oriented platform from disease data to submission-ready manuscripts</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/Position-Medical%20Research%20Platform-0B8BD9" alt="Position Medical Research Platform" />
  <img src="https://img.shields.io/badge/Docs%20%2F%20Manuscripts-Chinese%20Docs%20%2F%20English%20Manuscripts-1E8FB3" alt="Docs Chinese Docs / English Manuscripts" />
</p>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="MedAutoScience 主示意图" width="100%" />
</p>

`MedAutoScience` 的目标，不是把通用 AI 流程机械地跑完，而是围绕手头已有的专病数据与可公开获得的相关数据，稳定、可控地组织出可以投稿的医学论文。

它面向的不是单一分析脚本，而是完整的医学研究生产链：选题筛选、数据资产管理、建模与统计分析、公开数据扩展、功能分析、稿件组织与投稿交付。

## 这个项目解决什么问题

很多自动科研系统更像工程执行器，能把任务链跑通，但未必适合医学论文生产。

`MedAutoScience` 聚焦的是另一件事：

- 先判断某个方向是否值得继续投入，而不是默认把整条线做完
- 先按医学期刊和临床读者的逻辑组织研究，而不是按通用 AI/ML 论文习惯成文
- 先形成完整证据包，包括临床意义、工作量、可解释性、亚组分析、临床效用、外部验证与公开数据扩展
- 先止损与换题，不在明显偏弱、难发表的方向上空转

## 适合哪些数据

- 临床结构化数据
- 影像、病理及其他多模态数据
- 组学或功能分析相关数据
- 本地队列结合公开数据集的扩展分析
- 持续更新的私有临床数据资产，如补病例、补随访、补字段、多中心并入

## 平台核心组成

| 层级 | 角色 | 说明 |
| --- | --- | --- |
| 用户入口 | `MedAutoScience` | 面向医学研究者的主入口，负责研究策略、门控、数据资产治理和论文交付组织 |
| 执行引擎 | `DeepScientist` | 底层自动科研执行引擎 |
| 协调层 | `Codex` | 把平台策略落实到具体任务推进中的协调执行者 |
| 外部工具 | `ToolUniverse` | 作为知识检索、功能分析、通路与调控解释的外挂工具层 |

## 当前已经实现的能力

- 独立仓库与 workspace profile 机制
- `DeepScientist` 医学技能覆盖层安装与重覆写
- 对 `scout`、`idea`、`decision`、`write`、`finalize` 的医学特化前移约束
- 发表门槛控制与医学写作表面检查两类论文质量门控
- 运行监控、最小投稿包导出、正式交付同步
- 数据资产层：
  - 私有数据版本登记
  - 公开数据扩展模块
  - study 级数据影响评估
  - ToolUniverse 适配状态探测
- 医学写作前验约束：
  - Methods 必填项约束
  - Results 按研究问题组织，而不是按图表逐张复述
  - 稿件安全的复现补充材料
  - 终点来源说明
  - 内部命名、工程腔与未定义方法学标签拦截

## 默认优先的研究模式

当前版本已经把以下 6 类相对稳定、可扩展、容易组织成完整医学论文的研究模式沉淀为正式策略：

| Archetype | 中文说明 | 适合的论文方向 |
| --- | --- | --- |
| `clinical_classifier` | 临床风险分层 / 分类器 | 风险分层、临床效用、亚组分析、可解释分析 |
| `clinical_subtype_reconstruction` | 数据驱动亚型重构 | 异质性重构、亚组差异、预后与治疗反应比较 |
| `external_validation_model_update` | 外部验证 / 模型更新 | 可迁移性、再校准、模型更新 |
| `gray_zone_triage` | 灰区分诊 / 追加检查分流 | 流程分诊、确诊/排除/灰区设计 |
| `llm_agent_clinical_task` | 临床任务智能体 | 窄任务评测、提示词 / 推理方式 / 智能体结构比较 |
| `mechanistic_sidecar_extension` | 机制扩展支持模块 | 公开组学、功能分析、知识库增强 |

这些模式不是要求每一篇论文都全部使用，而是作为默认优先进入主研究候选面的路线库。

## 数据资产层

医学研究的数据通常不是静态输入，而是持续演进的资产。

`MedAutoScience` 把这件事上升成正式模块，分成四部分：

1. 私有数据版本登记  
   管理本地队列补充、随访刷新、字段补全、多中心并入等私有数据演进。

2. 公开数据扩展模块  
   登记可用于外部验证、机制扩展、队列扩展的公开数据集。

3. 影响评估  
   判断某个 study 当前使用的数据版本是否已经落后，以及是否已有可用的公开数据支持。

4. ToolUniverse 适配  
   将知识检索、功能分析、通路与调控解释纳入正式平台，而不是散落为临时脚本。

对应命令包括：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli data-assets-status --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli assess-data-asset-impact --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli tooluniverse-status --workspace-root /path/to/workspace
```

这些命令会把数据资产元信息统一放到 `portfolio/data_assets/` 下，作为后续选题、重跑、扩展验证和论文组织的稳定依据。

## 最小部署

这部分主要写给 Codex 或其他 AI 执行者。

```bash
git clone <repo-url> med-autoscience
cd med-autoscience
cp profiles/workspace.profile.template.toml profiles/my-study.local.toml
# 编辑 profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli overlay-status --profile profiles/my-study.local.toml
```

如果 `doctor` 中这些字段为 `true`，通常说明 workspace 已正确接入：

- `workspace_exists`
- `runtime_exists`
- `studies_exists`
- `portfolio_exists`
- `deepscientist_runtime_exists`

更细的部署说明见 [bootstrap/README.md](bootstrap/README.md)。

## 仓库文档

- [bootstrap/README.md](bootstrap/README.md)
- [policies/data_asset_management.md](policies/data_asset_management.md)
- [policies/study_archetypes.md](policies/study_archetypes.md)
- [policies/research_route_bias_policy.md](policies/research_route_bias_policy.md)

## 当前边界

当前版本仍是第一期平台骨架，已经完成医学研究入口、策略偏置、写作前验约束、交付闭环和数据资产基础层。

后续会继续迁入：

- 更细粒度的私有数据更新契约
- 更完整的公开数据接入工作流
- ToolUniverse 的正式任务级调用链
- 更完整的医学 study / portfolio / startup brief 模板
- 更细粒度的 publication profile
- 基于通用大模型的医学专用智能体研究支持
