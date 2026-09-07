# Study Archetypes

Owner: `MedAutoScience`
Purpose: `study_route_taxonomy`
State: `active_reference`
Machine boundary: 本页是路线分类与来源定位，不能决定 route、质量或 memory 写入。
完整策略正文由 [Memory Library](./publication_route_memory_library.md) 持有；
seed index 与 memory descriptor 引用的 identity 不等于私有 overlay parser。

## clinical_classifier

临床分类或风险分层：适用于有可测 endpoint 和具体临床决策点的数据。
完整的 calibration、utility、leakage 和 claim 边界见
[Classifier Card](./publication_route_memory_library.md#publication_route_memory_seed__clinical_classifier)。

## clinical_subtype_reconstruction

临床亚型重构：研究可解释的异质性，需证明稳定性和临床意义。
见 [Subtype Card](./publication_route_memory_library.md#publication_route_memory_seed__clinical_subtype_reconstruction)。

## external_validation_model_update

外部验证或模型更新：价值在 transportability、recalibration 与更新收益。
见 [Validation Card](./publication_route_memory_library.md#publication_route_memory_seed__external_validation_model_update)。

## gray_zone_triage

灰区分诊：关注 rule-in/rule-out/indeterminate 分区、安全性和资源使用。
见 [Triage Card](./publication_route_memory_library.md#publication_route_memory_seed__gray_zone_triage)。

## llm_agent_clinical_task

有界 LLM/Agent 临床任务：公平 baseline、外部/时间验证、错误类型与任务边界。
见 [Clinical Task Card](./publication_route_memory_library.md#publication_route_memory_seed__llm_agent_clinical_task)。

## mechanistic_sidecar_extension

机制侧线：为主临床路线提供可验证的生物学支持，不把关联升级成因果。
见 [Mechanistic Card](./publication_route_memory_library.md#publication_route_memory_seed__mechanistic_sidecar_extension)。

## survey_trend_analysis

调查趋势与指南对应：先统一问卷、分母和时间点，区分使用、偏好与采用，
不能把横断面调查解释成疗效。
见 [Survey Card](./publication_route_memory_library.md#publication_route_memory_seed__survey_trend_analysis)。
