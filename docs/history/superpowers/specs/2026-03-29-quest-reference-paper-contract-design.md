# Quest Reference Paper Contract Design

## Context

`MedAutoScience` 的定位已经明确为一个 `Agent-first, human-auditable` 的医学自动科研运行层，而不是面向研究者直接操作的工具箱。

在这个定位下，“我要模仿这几篇成熟论文的研究套路”不应只作为自由文本提示存在，也不应被建模成长期稳定的 study 级资产。它更适合作为某条 quest 的局部运行时 contract，由 agent 消费，由人审核，并允许在推进过程中被明确降级、替换或废弃。

## Problem

当前框架已有两类相关能力：

- `preferred_study_archetypes`：抽象层面的高产出医学研究套路
- `scout / idea / write` 阶段中的 literature survey / related-work / writing map

但目前缺少一个正式、可审计的 quest 级输入位点，用来表达：

- 哪几篇具体论文是当前 quest 的参考锚点
- 想借鉴这些论文的哪一部分
- 哪些部分禁止照搬
- 在不同 stage 上，这些参考论文应当如何约束 agent

结果是 agent 只能把“参考论文”当作一般文献处理，无法稳定区分：

- 当前 quest 的显式参考锚点
- 普通 related work
- 只可借鉴表面叙事、不可反推实验的模板论文

## Goal

引入 quest 级 `reference_papers` contract，使 agent 能稳定地把参考论文作为局部研究约束来消费，并且让人类能清楚审计：

- agent 参考了什么
- 借鉴了哪些套路
- 放弃了哪些不适配部分
- 是否在没有证据支持时错误地把模板论文反向施压到实验和写作上

## Non-goals

- 不把参考论文提升为长期 study 级资产层
- 不建设面向人类交互的复杂论文管理工具箱
- 不在这一轮实现自动下载、自动解析 PDF 正文或文献抽取流水线
- 不把参考论文当作写作阶段的强模板，更不允许其倒逼实验结果

## Product Decision

### 1. Contract 层级

`reference_papers` 只作为 `quest.yaml -> startup_contract` 的局部约束存在。

这样做的原因：

- 它只服务于当前 quest，而不是整个 study 的长期方向
- 即使一开始想模仿，也可能由于数据、终点、结果强度或实际可实现性不匹配而中途废弃
- quest 级更符合 agent 的运行时决策粒度

### 2. 输入形态

允许同时支持：

- URL / DOI / PMID / PMCID / arXiv id 等远程定位符
- 本地 PDF 路径

但运行时 contract 的本体是结构化 `reference_papers` 清单，而不是附件本身。论文原文只是 source，不是 contract 本体。

### 3. Stage 约束强度

`reference_papers` 对不同阶段的约束强度固定为：

- `scout`: required
- `idea`: required
- `write`: advisory

这不是每篇论文独立可配的自由策略，而是整个 contract 的统一语义，目的是保持行为可预测。

### 4. Agent 行为原则

当 quest 存在 `reference_papers` 时：

- `scout` 必须显式把这些论文纳入 framing、evaluation package、baseline neighborhood 的判断
- `idea` 必须显式比较候选方向与这些论文的关系，说明是继承、偏离还是放弃
- `write` 只能在真实证据支持时借鉴图表组织、章节结构和叙事骨架，不得为了贴合模板论文反推缺失分析

### 5. 审计原则

agent 不能只“看过”这些论文，必须留下可审计的对照痕迹，至少要能回答：

- 这篇论文在当前 quest 里是什么角色
- 借鉴了哪些套路
- 哪些内容被明确禁止照搬
- 如果最后没有跟随它，为什么没有跟随

## Contract Shape

每条 `reference_papers` 记录需要表达以下信息：

- 识别信息：`id`、`title`
- 来源定位：远程 locator 或本地 `pdf_path`
- 角色：例如 `anchor_paper`、`closest_competitor`、`adjacent_inspiration`
- 借鉴合同：要借鉴的研究套路、评估包、图表包、叙事骨架等
- 禁借合同：不得照搬的疾病特异结论、阈值、机制解释等
- 备注：当前 quest 下的适配说明

该 contract 应保持宽容输入、严格归一：

- 允许来源字段不完全一致
- 但至少必须能唯一定位到论文
- agent 读取后应得到稳定、结构化的归一结果

## Runtime Surface

本轮不把该能力做成人类交互式工具链，而是做成 agent 可调用、可审计的运行时能力：

- 解析 quest 中的 `reference_papers`
- 输出结构化摘要
- 将 contract 说明注入 `scout / idea / write` overlay

读操作和审计操作可以通过 controller / CLI 暴露，但它们的定位是 agent audit hook，而不是人类主入口。

## Recommended Durable Outputs

当 quest 使用 `reference_papers` 时，agent 至少应形成这些耐久痕迹：

- `artifacts/scout/reference_paper_contract.md` 或等价摘要
- `artifacts/idea/reference_paper_alignment.md` 或等价对照说明
- 写作阶段若借鉴论文表面结构，应在写作笔记中显式说明借鉴边界

这些文件不是由本仓库强制生成的静态模板，而是由 overlay 指导 runtime agent 形成的推荐审计痕迹。

## Implementation Design

### A. Parser Layer

新增独立的 `reference_papers` 解析模块：

- 从 `quest.yaml -> startup_contract.reference_papers` 读取
- 兼容顶层 `reference_papers` 作为兼容入口
- 校验最小定位信息是否存在
- 统一角色、借鉴字段、禁借字段与来源摘要

### B. Controller Layer

新增只读 controller：

- 输入 `quest_root`
- 输出解析后的 contract 摘要与审计友好 JSON

它的职责只是稳定暴露 contract，不负责论文抓取、PDF 抽取或文献解析。

### C. Overlay Integration

在 `scout`、`idea`、`write` 三个 stage 模板中加入 reference paper contract 说明块。

该说明块不内嵌某个 quest 的具体论文内容，而是定义统一运行规则：

- 如果 quest 有 `reference_papers`，agent 必须先读取并解释它
- `scout/idea` 强约束，`write` 弱约束
- 不允许把参考论文当成当前结果的替代证据
- 不允许把不适配部分静默忽略，必须说明偏离原因

### D. Template Surface

在 startup brief 模板中补出 `Reference papers` 段，帮助 quest 创建时留下显式入口，但不把它提升为 profile 或 study 级默认配置。

## Why This Fits The Product

这个设计符合 `MedAutoScience` 的产品定位：

- 它表达的是研究意图 contract，而不是人工操作步骤
- 它约束的是 agent 如何组织研究，而不是给人提供一个论文管理 UI
- 它保留了人类审核权，但把大部分执行与对齐工作交给 agent
- 它允许 quest 内动态调整，不会误伤整个 study 的长期治理

## Acceptance Criteria

1. quest 可以通过 `startup_contract.reference_papers` 声明参考论文
2. 解析层能稳定读取并归一远程 locator / 本地 PDF 两类来源
3. controller 能输出清晰的审计摘要
4. `scout / idea / write` overlay 明确包含 reference paper contract 规则
5. `scout / idea` 的规则文本体现强约束
6. `write` 的规则文本体现 advisory 约束，并明确禁止倒逼结果
7. startup brief 模板存在 reference paper 入口
