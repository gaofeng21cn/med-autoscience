# Docs

这里是 `MedAutoScience` 面向 GitHub 与外部读者的公开文档入口。

公开口径统一按下面这条理解：

- 对外：`MedAutoScience` 是 `Research Ops Gateway`
- 对内：它由医学自动科研 `Harness OS` 驱动
- 在 `OPL` 顶层语义里：它是 `Research Ops` 的 domain gateway，而不是 `OPL` 本体

## 面向医学用户

- [README](../README.md)
- [病种 workspace 快速起步](disease_workspace_quickstart.md)
- [医学展示面审计指南](medical_display_audit_guide.md)
- [医学展示面模板目录](medical_display_template_catalog.md)

## 面向技术同事 / AI 执行者

- [Agent Runtime Interface](agent_runtime_interface.md)
- [Agent Entry Modes](agent_entry_modes.md)
- [Runtime Boundary](runtime_boundary.md)
- [Workspace Architecture](workspace_architecture.md)
- [Upstream Intake Guide](upstream_intake.md)
- [Repository CI Preflight](repository_ci_preflight.md)
- [Codex plugin 接入](codex_plugin.md)
- [Codex plugin 发布说明](codex_plugin_release.md)

## 平台规则

- [Policies 索引](policies/README.md)
- [运行模型 Policy](policies/platform_operating_model.md)
- [数据资产策略](policies/data_asset_management.md)
- [默认研究场景](policies/study_archetypes.md)
- [研究路线偏置](policies/research_route_bias_policy.md)
- [Publication Gate Policy](policies/publication_gate_policy.md)

## 文档边界

- `docs/`：公开文档
- `docs/policies/`：稳定、长期公开保留的规则文档
- `docs/superpowers/`：本地 AI / Superpowers 文档、开发计划、设计草案与过程痕迹，不进入 Git 跟踪面
