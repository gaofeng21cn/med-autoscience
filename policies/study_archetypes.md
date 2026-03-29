# Study Archetypes

默认 `preferred_study_archetypes`：

- `clinical_classifier`
- `llm_agent_clinical_task`

它们不是所有课题的强制目标，而是默认优先进入 serious frontier 的高产出论文套路。

`clinical_classifier`

- 适合有明确临床结局、可以做风险分层和 clinical utility 的任务
- 目标 paper package 包括 discrimination、calibration、decision curve、亚组分析、可解释分析、外部验证

`llm_agent_clinical_task`

- 适合可被定义为临床任务的场景，例如诊断支持、结构化抽取、分诊或决策支持
- 目标 paper package 包括 baseline 对照、prompt/推理/agent 变体、亚组、错误类型、病例级解释、外部验证
