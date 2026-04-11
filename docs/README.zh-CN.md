# 文档索引

[English](./README.md) | **中文**

这里是 `Med Auto Science` 的双语文档索引，也是默认的 GitHub 对外入口。对外文档必须提供中英双语镜像，内部技术与规划材料默认中文，除非明确提升到双语公开面。文档治理规则统一收口在 [`AGENTS.md`](../AGENTS.md)。

## 核心骨架

以下五份是稳定知识骨架（默认中文，除非补齐双语镜像）：

- [项目概览](project.md)
- [架构概览](architecture.md)
- [不可变约束](invariants.md)
- [关键决策记录](decisions.md)
- [当前状态](status.md)

## 默认对外双语公开面

- [仓库首页](../README.zh-CN.md)

## 当前主线与阻塞包

当前 repo-tracked runtime 主线已经吸收完成。
当前最诚实的 repo-side 停车结论是 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`，不是正在仓内继续实现的 active tranche。

## Runtime 合同与控制面

- [Agent 运行接口](runtime/agent_runtime_interface.md)
- [Agent 入口模式](runtime/agent_entry_modes.md)
- [运行句柄与持久表面合同](runtime/runtime_handle_and_durable_surface_contract.md)
- [运行时事件与 Outer-Loop 输入合同](runtime/runtime_event_and_outer_loop_input_contract.md)
- [运行时事件与 Outer-Loop 输入实施计划](runtime/runtime_event_and_outer_loop_input_implementation_plan.md)
- [Runtime Core 收敛与受控 Cutover](runtime/runtime_core_convergence_and_controlled_cutover.md)
- [Runtime Core 收敛与受控 Cutover 实施计划](runtime/runtime_core_convergence_and_controlled_cutover_implementation_plan.md)
- [Workspace 知识与文献合同](runtime/workspace_knowledge_and_literature_contract.md)
- [Workspace 知识与文献实施计划](runtime/workspace_knowledge_and_literature_implementation_plan.md)
- [运行时监督外环](runtime/runtime_supervision_loop.md)
- [Study runtime 控制面](runtime/study_runtime_control_surface.md)
- [Study runtime 编排](runtime/study_runtime_orchestration.md)
- [Outer-Loop 唤醒与决策循环](runtime/outer_loop_wakeup_and_decision_loop.md)
- [交付面合同地图](runtime/delivery_plane_contract_map.md)
- [运行边界](runtime/runtime_boundary.md)

## 能力族

### 医学展示（Medical display）

- [医学展示平台主线](capabilities/medical-display/medical_display_platform_mainline.md)
- [医学展示面审计指南](capabilities/medical-display/medical_display_audit_guide.md)
- [医学展示面模板目录](capabilities/medical-display/medical_display_template_catalog.md)
- [医学展示面家族路线图](capabilities/medical-display/medical_display_family_roadmap.md)
- [医学展示面视觉审计协议](capabilities/medical-display/medical_display_visual_audit_protocol.md)
- [Sidecar 图表路线](capabilities/medical-display/sidecar_figure_routes.md)

## Program 与 Gates

- [Research Foundry 医学执行地图](program/research_foundry_medical_execution_map.md)
- [Research Foundry 医学主线](program/research_foundry_medical_mainline.md)
- [Integration Harness Activation Package](program/integration_harness_activation_package.md)
- [External Runtime Dependency Gate](program/external_runtime_dependency_gate.md)
- [Merge And Cutover Gates](program/merge_and_cutover_gates.md)
- [Open Harness OS 冻结计划](program/open_harness_os_freeze_plan.md)
- [主线集成与清理节奏](program/mainline_integration_and_cleanup.md)
- [上游 Intake 指南](program/upstream_intake.md)
- [仓库 CI 预检](program/repository_ci_preflight.md)
- [真实课题 relaunch 验证记录](program/real_study_relaunch_verification.md)
- [项目修补优先级图](program/project_repair_priority_map.md)
- [研究进度投影](program/study_progress_projection.md)
- [手工测试与运行面稳定化清单](program/manual_runtime_stabilization_checklist.md)

## 参考资料

- [Domain Harness OS 定位](references/domain-harness-os-positioning.md)
- [Domain gateway 与 Harness OS 概览](references/domain_gateway_harness_os.md)
- [Research Foundry 定位](references/research_foundry_positioning.md)
- [Research Foundry 与 Med Auto Science 的仓库拆分边界](references/repo_split_between_research_foundry_and_med_autoscience.md)
- [Open Harness OS 架构边界](references/open_harness_os_architecture.md)
- [工作区架构](references/workspace_architecture.md)
- [病种 workspace 快速起步](references/disease_workspace_quickstart.md)
- [Codex plugin 接入](references/codex_plugin.md)
- [Codex plugin 发布说明](references/codex_plugin_release.md)

## 稳定内部规则

- [内部规则索引](policies/README.md)
- [运行模型规则](policies/platform_operating_model.md)
- [数据资产管理](policies/data_asset_management.md)
- [研究场景类型](policies/study_archetypes.md)
- [研究路线偏置规则](policies/research_route_bias_policy.md)
- [发表门控规则](policies/publication_gate_policy.md)

## 历史归档

- [OMX 历史资料索引](history/omx/README.zh-CN.md)（仅历史参考，不是当前 active workflow 入口）

## 文档边界

- `README*` 与 `docs/README*`：默认对外双语公开面。
- `docs/capabilities/`、`docs/program/`、`docs/runtime/`、`docs/references/`：仓库跟踪的操作文档，默认中文维护。
- `docs/policies/`：稳定内部规则，默认中文维护。
- `docs/history/omx/`：OMX 历史资料入口，只做归档，不再承担活跃 workflow。
- `docs/superpowers/`：本地 AI/Superpowers 的计划、草稿与过程产物，应保持未跟踪。
