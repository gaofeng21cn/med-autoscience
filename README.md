# MedAutoScience

`MedAutoScience` 是一个面向医学研究者的自动科研平台入口。

它的目标不是把通用 AI 流程机械地跑完，而是围绕手头已有的专病数据与可公开获得的相关数据，稳定、可控地组织出可以投稿的医学论文。

## 项目定位

很多自动科研系统更像工程执行器，擅长把任务链跑通，但未必适合医学论文生产。

`MedAutoScience` 的定位不同：

- 优先判断一个方向是否值得继续投入，而不是默认把整条线做完
- 优先按医学期刊和临床读者的习惯组织研究，而不是按 AI/ML 论文习惯写作
- 优先形成完整的证据包，包括临床意义、工作量、可解释性、亚组、utility、外部验证或公开数据扩展
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
   临床风险分层 / 分类器。适合围绕临床结局建立高风险与低风险分层，并补齐 calibration、clinical utility、亚组与可解释分析。
2. `clinical_subtype_reconstruction`
   数据驱动亚型重构。适合把疾病异质性重构成更有临床意义的亚组，并进一步比较预后、治疗反应和生物学差异。
3. `external_validation_model_update`
   外部验证 / 模型更新。适合把已有模型或本地开发模型扩展到外部数据，强调 transportability、recalibration 和 updating。
4. `gray_zone_triage`
   灰区分诊 / reflex testing。适合不是简单二分类，而是要回答“谁可排除、谁可确诊、谁需进一步检查”的临床流程问题。
5. `llm_agent_clinical_task`
   基于通用大模型的临床任务智能体。适合窄任务、可benchmark、可做多种 prompt / reasoning / agent 变体比较的研究。
6. `mechanistic_sidecar_extension`
   机制扩展 sidecar。适合附着在更强的主临床路线之上，用公开组学、功能分析或知识库增强论文深度与工作量。

这 6 类不是要求每一篇论文都全部使用，而是作为默认优先进入 serious frontier 的研究路线库。

## 当前已经实现的能力

第一期版本已经具备以下骨架能力：

- 独立仓库与 workspace profile 机制
- `DeepScientist` skill overlay 安装与重覆写
- 对 `scout`、`idea`、`decision`、`write`、`finalize` 的医学特化前移约束
- publication gate 与 medical publication surface 两类论文质量门控
- runtime watch、submission minimal exporter、study delivery sync
- 医学写作前验约束，包括：
  - Methods 必填项 contract
  - 结果部分按研究问题组织，而不是按图表逐张复述
  - manuscript-safe reproducibility supplement
  - endpoint provenance note
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
- [policies/study_archetypes.md](policies/study_archetypes.md)
- [policies/research_route_bias_policy.md](policies/research_route_bias_policy.md)

## 当前边界

当前版本仍是第一期平台骨架。

已经完成的是：医学研究入口、策略偏置、写作前验约束、交付闭环和基本 CLI。

接下来会继续迁入：

- public-data sidecar
- ToolUniverse adapter
- 更完整的医学 study / portfolio / startup brief 模板
- 更细粒度的 publication profile
- 基于通用 LLM 的医学专用智能体研究支持
