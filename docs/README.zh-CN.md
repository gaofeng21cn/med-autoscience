# 文档索引

[English](./README.md) | **中文**

这里是 `Med Auto Science` 的双语文档索引，也是默认的 GitHub 对外入口。
内容与项目定位保持一致：该仓库在共享 `Unified Harness Engineering Substrate` 上支撑医学 `Research Ops` 的领域承载操作系统（Domain Harness OS），本地执行呈现为 Codex 默认 host-agent runtime 的形态；其 formal-entry matrix 固定为默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`，当前仓库主线按 `Auto-only` 理解。

## 统一文档治理

- 所有对外文档都必须同时提供英文 `.md` 与中文 `.zh-CN.md`，并保持同步更新。
- 内部设计、技术、规划与备忘文档默认使用中文，除非明确提升到双语公开面。
- 术语可以保留英文，但应避免无意义的中英混写，确保语句保持通顺。
- `docs/README*` 应保持统一结构与措辞，清晰区分双语公开入口与内部内容。
- 详情可参考 [文档治理规则](documentation-governance.md)。

## 默认对外双语公开面

- [仓库首页](../README.zh-CN.md)

这份索引与仓库首页共同构成默认的 GitHub 双语公开面。
任何需要对外公开的文档，都必须进入这个公开面并配备英文与中文镜像。

## 当前主线与阻塞包

当前 repo-tracked runtime 主线在仓内已经吸收完成。
当前最诚实的 repo-side 停车结论是 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`，而不是还有一条正在仓内继续实现的 active tranche。

- [Research Foundry 医学执行地图](research_foundry_medical_execution_map.md)
- [Research Foundry 医学主线](research_foundry_medical_mainline.md)
- [Integration Harness Activation Package](integration_harness_activation_package.md)
- [External Runtime Dependency Gate](external_runtime_dependency_gate.md)
- [Merge And Cutover Gates](merge_and_cutover_gates.md)
- [医学展示平台主线](medical_display_platform_mainline.md)（展示面独立工作线，不属于当前 runtime 主线）

## 仓库跟踪的内部操作文档

### 面向医学操作同事

- [病种 workspace 快速起步](disease_workspace_quickstart.md)
- [医学展示面审计指南](medical_display_audit_guide.md)
- [医学展示面模板目录](medical_display_template_catalog.md)

### 面向技术 / AI 执行同事

- [Unified Substrate 下的 Domain Harness OS 定位](domain-harness-os-positioning.md)
- [Agent 运行接口](agent_runtime_interface.md)
- [运行句柄与持久表面合同](runtime_handle_and_durable_surface_contract.md)
- [项目修补优先级图](project_repair_priority_map.md)
- [运行时事件与 Outer-Loop 输入合同](runtime_event_and_outer_loop_input_contract.md)
- [Runtime Core 收敛与受控 Cutover](runtime_core_convergence_and_controlled_cutover.md)
- [运行时监管外环合同](runtime_supervision_loop.md)
- [运行时事件与 Outer-Loop 输入实施计划](runtime_event_and_outer_loop_input_implementation_plan.md)
- [Runtime Core 收敛与受控 Cutover 实施计划](runtime_core_convergence_and_controlled_cutover_implementation_plan.md)
- [手工测试与运行面稳定化清单](manual_runtime_stabilization_checklist.md)
- [前台研究进度投影](study_progress_projection.md)
- [Workspace 知识与文献合同](workspace_knowledge_and_literature_contract.md)
- [Workspace 知识与文献实施计划](workspace_knowledge_and_literature_implementation_plan.md)
- [Agent 入口模式](agent_entry_modes.md)
- [Open Harness OS 架构边界](open_harness_os_architecture.md)
- [Outer-Loop 唤醒与决策循环](outer_loop_wakeup_and_decision_loop.md)
- [Open Harness OS 冻结计划](open_harness_os_freeze_plan.md)
- [主线集成与清理节奏](mainline_integration_and_cleanup.md)
- [Research Foundry 医学执行地图](research_foundry_medical_execution_map.md)
- [Research Foundry 医学主线](research_foundry_medical_mainline.md)
- [Research Foundry 定位](research_foundry_positioning.md)
- [Research Foundry 与 Med Auto Science 的仓库拆分边界](repo_split_between_research_foundry_and_med_autoscience.md)
- [运行边界](runtime_boundary.md)
- [工作区架构](workspace_architecture.md)
- [上游 Intake 指南](upstream_intake.md)
- [仓库 CI 预检](repository_ci_preflight.md)
- [Codex Plugin 接入](codex_plugin.md)
- [Codex Plugin 发布指南](codex_plugin_release.md)
- [文档治理规则](documentation-governance.md)

### Legacy / 历史参考

- [Legacy OMX worktree 启动与收尾操作规约](omx_worktree_startup_and_closeout.md)（仅历史参考，不是当前 active workflow 入口）

## 稳定内部规则

- [内部规则索引](policies/README.md)
- [运行模型规则](policies/platform_operating_model.md)
- [数据资产管理](policies/data_asset_management.md)
- [研究场景类型](policies/study_archetypes.md)
- [研究路线偏置规则](policies/research_route_bias_policy.md)
- [发表门控规则](policies/publication_gate_policy.md)

## 文档边界

- `README*` 与 `docs/README*`：默认对外双语公开面。
- `bootstrap/`、`controllers/`、详细 `docs/*.md`：默认内部操作文档，中文优先，除非明确推广。
- `docs/policies/`：稳定内部规则，默认中文维护。
- `docs/superpowers/`：本地 AI/Superpowers 的计划、草稿与过程产物，应保持未跟踪。
