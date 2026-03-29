# MedAutoScience

`MedAutoScience` 是一个面向医学研究者的自动科研平台入口。

它的目标不是把通用 AI 流程机械地跑完，而是围绕手头已有的专病数据与可公开获得的相关数据，稳定、可控地组织出可以投稿的医学论文。

## 项目定位

很多自动科研系统更像工程执行器，擅长把任务链跑通，但未必适合医学论文生产。

`MedAutoScience` 的定位不同：

- 优先判断一个方向是否值得继续投入，而不是默认把整条线做完
- 优先按医学期刊和临床读者的习惯组织研究，而不是按 AI/ML 论文习惯写作
- 优先形成完整的证据包，包括临床意义、工作量、可解释性、亚组分析、临床效用、外部验证或公开数据扩展
- 优先止损与换题，不在明显偏弱、难发表的方向上空转

## 适用数据

`MedAutoScience` 面向的并不只是单一表格型临床数据，也包括：

- 临床结构化数据
- 影像、病理及其他多模态数据
- 组学或功能分析相关数据
- 本地队列配合公开数据集的扩展分析

## 默认优先的研究模式

当前版本已经把以下 6 类相对稳定、可扩展、容易组织成完整医学论文的研究模式沉淀为正式策略：

1. `clinical_classifier`
   临床风险分层 / 分类器。适合围绕临床结局建立高风险与低风险分层，并补齐校准、临床效用、亚组分析与可解释分析。
2. `clinical_subtype_reconstruction`
   数据驱动亚型重构。适合把疾病异质性重构成更有临床意义的亚组，并进一步比较预后、治疗反应和生物学差异。
3. `external_validation_model_update`
   外部验证 / 模型更新。适合把已有模型或本地开发模型扩展到外部数据，强调可迁移性、再校准与模型更新。
4. `gray_zone_triage`
   灰区分诊 / 追加检查分流。适合不是简单二分类，而是要回答“谁可排除、谁可确诊、谁需进一步检查”的临床流程问题。
5. `llm_agent_clinical_task`
   基于通用大模型的临床任务智能体。适合窄任务、可做规范基准评测、可比较多种提示词 / 推理方式 / 智能体结构变体的研究。
6. `mechanistic_sidecar_extension`
   机制扩展支持模块。适合附着在更强的主临床路线之上，用公开组学、功能分析或知识库增强论文深度与工作量。

这 6 类不是要求每一篇论文都全部使用，而是作为默认优先进入主研究候选面的路线库。

## 数据资产层

医学研究的数据通常不是静态输入，而是持续演进的资产。

当前版本已经把这件事上升成正式模块，分成三层：

- 私有数据版本登记
  用于管理本地队列补充、随访刷新、字段补全、多中心并入等私有数据演进。
- 公开数据扩展模块
  用于登记可用于外部验证、机制扩展、队列扩展的公开数据集。
- 影响评估
  用于判断某个 study 当前使用的数据版本是否已经落后，以及是否已有可用的公开数据支持。

对应命令包括：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli data-assets-status --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli assess-data-asset-impact --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli tooluniverse-status --workspace-root /path/to/workspace
```

这些命令会把数据资产元信息统一放到 `portfolio/data_assets/` 下，作为后续选题、重跑、扩展验证和论文组织的稳定依据。

## 当前已经实现的能力

第一期版本已经具备以下骨架能力：

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
- 医学写作前验约束，包括：
  - Methods 必填项约束
  - 结果部分按研究问题组织，而不是按图表逐张复述
  - 稿件安全的复现补充材料
  - 终点来源说明
  - 内部命名、工程腔与未定义方法学标签拦截

## 这个平台如何工作

可以把它理解成三层：

- `MedAutoScience`
  面向医学用户的主入口，负责研究策略、门控、论文约束和交付组织
- `DeepScientist`
  底层自动科研执行引擎
- `Codex`
  执行协调者，负责把平台策略落实到具体任务推进中

也就是说，医学用户面对的应该始终是 `MedAutoScience`，而不是直接操作底层执行引擎。

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

当前版本仍是第一期平台骨架。

已经完成的是：医学研究入口、策略偏置、写作前验约束、交付闭环和基本 CLI。

接下来会继续迁入：

- 更细粒度的私有数据更新契约
- 更完整的公开数据接入工作流
- ToolUniverse 的正式任务级调用链
- 更完整的医学 study / portfolio / startup brief 模板
- 更细粒度的 publication profile
- 基于通用 LLM 的医学专用智能体研究支持
