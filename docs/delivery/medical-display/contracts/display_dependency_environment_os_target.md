# Display Environment Boundary

Owner: `MedAutoScience`
Purpose: `display_environment_ownership`
State: `active_runtime_support`
Machine boundary: `contracts/runtime_environment_requirements.json` 与 Framework 环境 readback 持有可执行事实。

MAS 的 `analysis-display` 默认只绑定 Rscript；具体分析显式声明外部包。ScholarSkills
持有专业模板的 `requirement_profile_ids` 和对应依赖配置，MAS 从当前 provider 读取并
将选中配置的完整并集交给 OPL `env prepare/run`。普通图不连带安装热图、降维等
专用包。MAS 不维护环境安装器、模板 catalog 副本或 renderer transport。

任务内脚本合并、批量绘图的性能与一致性准入、结果绑定及失败边界统一由
[执行策略](../../../../agent/skills/medical_research_execution.md#task-environment-routing)
说明；批量执行本身不改变单图医学与视觉审阅义务。

包发现、准备、执行和领域审阅是不同验收对象。installed descriptor 证明能力可发现，
环境 receipt 证明准备结果，render output 证明产物存在；医学 claim、视觉审阅和
publication acceptance 仍由 MAS owner 对具体 artifact 判断。

环境调用与本地验证见 [Bootstrap](../../../../bootstrap/README.md)；
专业视觉审阅见 [Visual Audit](./medical_display_visual_audit_protocol.md)。
