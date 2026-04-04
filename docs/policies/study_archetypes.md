# Study Archetypes

默认 `preferred_study_archetypes`：

- `clinical_classifier`
- `clinical_subtype_reconstruction`
- `external_validation_model_update`
- `gray_zone_triage`
- `llm_agent_clinical_task`
- `mechanistic_sidecar_extension`

它们不是所有课题的强制目标，而是默认优先进入主研究候选面的高产出论文套路。

`clinical_classifier`

- 适合有明确临床结局、可以做风险分层和临床效用分析的任务
- 目标论文包包括区分度、校准、决策曲线、亚组分析、可解释分析、外部验证

`clinical_subtype_reconstruction`

- 适合疾病内部异质性明显、但单一固定临床因子未必足以讲出完整故事的任务
- 目标论文包包括亚型构建、稳定性评估、亚型间临床差异、预后/疗效比较，以及亚型识别器

`external_validation_model_update`

- 适合已有模型、本地模型或文献模型可被带到外部数据中重新评估与更新的任务
- 目标论文包包括外部验证、可迁移性、再校准、模型更新，以及不同病例构成下的稳健性比较

`gray_zone_triage`

- 适合临床上真正需要回答“谁可排除、谁可确诊、谁需进一步检查/随访”的流程型任务
- 目标论文包包括分诊阈值、确诊/排除/灰区分析、流程对比、安全性与资源利用分析

`llm_agent_clinical_task`

- 适合可被定义为临床任务的场景，例如诊断支持、结构化抽取、分诊或决策支持
- 目标论文包包括基线对照、提示词/推理/智能体变体、亚组、错误类型、病例级解释、外部验证

`mechanistic_sidecar_extension`

- 适合作为更强主临床路线的增强包，而不是孤立主线
- 目标论文包包括通路 / 调控 / 功能分析、公开组学支持，以及模型或亚型定义出的临床分组的机制解释
