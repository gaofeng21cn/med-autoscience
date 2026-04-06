# Docs

[English](./README.md) | **中文**

这里是 `Med Auto Science` 的双语文档索引。

公开口径统一按下面这条理解：

- 对外：`Med Auto Science` 是 `Research Foundry` 主线中的首个成熟医学实现
- 在运行层：它承担医学 `Research Ops` gateway 与 domain harness OS
- 在联邦层：当前公开链路是 `One Person Lab -> Research Foundry -> Med Auto Science`

## 默认对外双语公开面

- [仓库首页](../README.zh-CN.md)

这份双语索引和仓库首页一起构成默认 GitHub 公开面。
任何要提升到这个公开面的正文文档，都必须同时具备英文 `.md` 与中文 `.zh-CN.md` 镜像，并保持同步更新。

## 仓库跟踪的内部操作文档

下面这些文档仍然会继续保留在仓库里，但默认属于内部操作文档，因此当前按中文维护；除非被显式提升到双语公开面，否则不作为 GitHub 默认公开正文。

### 面向医学操作同事

- [病种 workspace 快速起步](disease_workspace_quickstart.md)
- [医学展示面审计指南](medical_display_audit_guide.md)
- [医学展示面模板目录](medical_display_template_catalog.md)

### 面向技术同事 / AI 执行者

- [Agent Runtime Interface](agent_runtime_interface.md)
- [Agent Entry Modes](agent_entry_modes.md)
- [Open Harness OS 架构边界](open_harness_os_architecture.md)
- [Outer-Loop 唤醒与决策循环](outer_loop_wakeup_and_decision_loop.md)
- [Open Harness OS 冻结计划](open_harness_os_freeze_plan.md)
- [主线集成与清理节奏](mainline_integration_and_cleanup.md)
- [Research Foundry 医学主线执行地图](research_foundry_medical_execution_map.md)
- [Research Foundry Medical Mainline](research_foundry_medical_mainline.md)
- [Research Foundry 定位](research_foundry_positioning.md)
- [Research Foundry 与 Med Auto Science 的 repo 拆分边界](repo_split_between_research_foundry_and_med_autoscience.md)
- [Runtime Boundary](runtime_boundary.md)
- [Workspace Architecture](workspace_architecture.md)
- [Upstream Intake Guide](upstream_intake.md)
- [Repository CI Preflight](repository_ci_preflight.md)
- [Codex plugin 接入](codex_plugin.md)
- [Codex plugin 发布说明](codex_plugin_release.md)

## 稳定内部规则

- [Policies 索引](policies/README.md)
- [运行模型 Policy](policies/platform_operating_model.md)
- [数据资产策略](policies/data_asset_management.md)
- [默认研究场景](policies/study_archetypes.md)
- [研究路线偏置](policies/research_route_bias_policy.md)
- [Publication Gate Policy](policies/publication_gate_policy.md)

## 文档边界

- `README*` 与 `docs/README*`：默认对外双语公开面
- `bootstrap/`、`controllers/` 与详细 `docs/*.md`：默认仓库跟踪的内部操作文档
- `docs/policies/`：默认仓库跟踪的稳定内部规则
- `docs/superpowers/`：本地 AI / Superpowers 的计划、草稿与过程产物，保持未跟踪
