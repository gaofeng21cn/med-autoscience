# Display Environment Boundary

Owner: `MedAutoScience`
Purpose: `display_environment_ownership`
State: `active_runtime_support`
Machine boundary: `contracts/runtime_environment_requirements.json` 与 Framework 环境 readback 持有可执行事实。

MAS 在 `analysis-display` requirement profile 中声明 Python、R/Bioconductor 和能力需求；
ScholarSkills 持有 pack 的专业模板与依赖声明；OPL 的 `env prepare/run` 准备环境并执行
renderer。MAS 不维护环境安装器、模板 catalog 副本或 renderer transport。

包发现、准备、执行和领域审阅是不同验收对象。installed descriptor 证明能力可发现，
环境 receipt 证明准备结果，render output 证明产物存在；医学 claim、视觉审阅和
publication acceptance 仍由 MAS owner 对具体 artifact 判断。

环境调用与本地验证见 [Bootstrap](../../../../bootstrap/README.md)；
专业视觉审阅见 [Visual Audit](./medical_display_visual_audit_protocol.md)。
