# 文档索引

[English](./README.md) | **中文**

这个目录是 `Med Auto Science` 的第二层技术阅读面。
仓库首页应优先写给医生、医学专家和潜在用户。
而这里负责承接其后的 runtime、program、能力线和治理材料。

## 按读者类型进入

| 读者 | 建议起点 | 目的 |
| --- | --- | --- |
| 潜在用户、医生、医学专家 | [仓库首页](../README.zh-CN.md) | 先理解系统是干什么的，再决定是否进入技术细节 |
| 技术规划者、架构读者、方向同步读者 | [项目概览](./project.md)、[当前状态](./status.md)、[架构](./architecture.md)、[不可变约束](./invariants.md)、[关键决策](./decisions.md) | 快速抓住当前真相、边界和主线方向 |
| 开发者与维护者 | `docs/runtime/`、`docs/program/`、`docs/capabilities/`、`docs/references/`、`docs/policies/`、`docs/history/omx/` | 查看实现相关材料、操作说明和历史记录 |

## 当前基线

- `OPL` 是家族级顶层 GUI 与管理壳。
- `Med Auto Science` 是这个壳下面的一级医学 domain module / agent。
- `Codex` 是 MAS 默认交互与执行表面，通过 `CLI`、`MCP` 和 controller 命令推进工作。
- 上游 `Hermes-Agent` 是外部备用模式与长期在线网关，负责 supervised runtime continuity。
- MAS 默认回路是 `product-frontdesk` -> `workspace-cockpit` -> `submit-study-task` -> `launch-study` -> `study-progress`。
- 医学展示支线继续作为下游能力线分开维护。
- 历史 program 记录、运行边界形成说明与已吸收迁移 proof 继续留在 `docs/program/`、`docs/references/` 与 `docs/history/omx/` 中供维护者追溯。

## 技术工作集

开始改仓库状态前，先读这些文件：

- [项目概览](./project.md)
- [当前状态](./status.md)
- [架构](./architecture.md)
- [不可变约束](./invariants.md)
- [关键决策](./decisions.md)

## 默认公开入口

- [仓库首页](../README.zh-CN.md)

仓库首页和这份索引共同构成默认公开入口。
对外文档应继续保持中英双语镜像。

## 仓库跟踪的技术文档

### Runtime 合同与控制面

- [Agent 运行接口](runtime/agent_runtime_interface.md)
- [Agent 入口模式](runtime/agent_entry_modes.md)
- [运行句柄与持久表面合同](runtime/runtime_handle_and_durable_surface_contract.md)
- [Runtime backend interface 合同](runtime/runtime_backend_interface_contract.md)
- [运行事件与 outer-loop 输入合同](runtime/runtime_event_and_outer_loop_input_contract.md)
- [运行事件与 outer-loop 输入实施计划](runtime/runtime_event_and_outer_loop_input_implementation_plan.md)
- [运行边界](runtime/runtime_boundary.md)
- [Runtime 核心收敛与受控 cutover](runtime/runtime_core_convergence_and_controlled_cutover.md)
- [Runtime 核心收敛与受控 cutover 实施计划](runtime/runtime_core_convergence_and_controlled_cutover_implementation_plan.md)
- [运行时监督外环](runtime/runtime_supervision_loop.md)
- [Study runtime 控制面](runtime/study_runtime_control_surface.md)
- [Study runtime 编排](runtime/study_runtime_orchestration.md)
- [Workspace knowledge 与 literature 合同](runtime/workspace_knowledge_and_literature_contract.md)
- [Workspace knowledge 与 literature 实施计划](runtime/workspace_knowledge_and_literature_implementation_plan.md)

### 能力线文档

- [医学展示平台主线](capabilities/medical-display/medical_display_platform_mainline.md)
- [医学展示面审计指南](capabilities/medical-display/medical_display_audit_guide.md)
- [医学展示面模板目录](capabilities/medical-display/medical_display_template_catalog.md)
- [医学展示面家族路线图](capabilities/medical-display/medical_display_family_roadmap.md)
- [医学展示面视觉审计协议](capabilities/medical-display/medical_display_visual_audit_protocol.md)

### 当前 program 与维护工作面

- [Research Foundry 医学执行地图](program/research_foundry_medical_execution_map.md)
- [Research Foundry 医学主线](program/research_foundry_medical_mainline.md)
- [External Runtime Dependency Gate](program/external_runtime_dependency_gate.md)
- [Merge And Cutover Gates](program/merge_and_cutover_gates.md)
- [项目修复优先级地图](program/project_repair_priority_map.md)
- [仓库 CI 预检](program/repository_ci_preflight.md)
- [Study progress projection](program/study_progress_projection.md)

### 追溯记录

- [Research Foundry 医学维护者阶段参考](references/research_foundry_medical_phase_ladder.md)
- [Hermes backend continuation board](program/hermes_backend_continuation_board.md)
- [Hermes backend activation package](program/hermes_backend_activation_package.md)
- [MedDeepScientist 解构地图](program/med_deepscientist_deconstruction_map.md)
- [手动 runtime 稳定化清单](program/manual_runtime_stabilization_checklist.md)
- [真实课题 relaunch 验证记录](program/real_study_relaunch_verification.md)
- [OMX 历史资料索引](history/omx/README.zh-CN.md)

### MAS 用户回路与内部桥接参考

- 面向用户的 MAS 回路从 `product-frontdesk` 开始，经由 `workspace-cockpit`，再使用 `submit-study-task`、`launch-study` 和 `study-progress`。
- `product-entry-manifest` 与 `build-product-entry` 继续作为 `OPL` 与其他自动化 caller 使用的 machine-readable bridge。
- [轻量产品入口与 OPL Handoff](references/lightweight_product_entry_and_opl_handoff.md)

### 参考资料

- [Domain Harness OS 定位](references/domain-harness-os-positioning.md)
- [Research Foundry 定位](references/research_foundry_positioning.md)
- [Research Foundry 与 Med Auto Science 的仓库拆分边界](references/repo_split_between_research_foundry_and_med_autoscience.md)
- [工作区架构](references/workspace_architecture.md)
- [病种 workspace 快速起步](references/disease_workspace_quickstart.md)
- [轻量产品入口与 OPL Handoff](references/lightweight_product_entry_and_opl_handoff.md)
- [系列项目文档治理清单](references/series-doc-governance-checklist.md)

### 稳定内部规则

- [内部规则索引](policies/README.md)
- [运行模型规则](policies/platform_operating_model.md)
- [数据资产管理](policies/data_asset_management.md)
- [研究路线偏置规则](policies/research_route_bias_policy.md)
- [发表门控规则](policies/publication_gate_policy.md)

### 仓库历史

- [OMX 历史资料索引](history/omx/README.zh-CN.md)

## 文档规则

- 继续把 [仓库首页](../README.zh-CN.md) 保持成医生和非技术专家可读的入口。
- 继续把公开文档保持成中英双语镜像。
- runtime、program、能力线和 policy 文档可以技术化，但不要再反客为主占据公开首页。
- 历史材料可以保留，但不能再写成当前默认 workflow。

## 治理说明

- 文档治理统一冻结在 [系列项目文档治理清单](references/series-doc-governance-checklist.md)、技术工作集和仓库跟踪的 contract/doc surface 中，而不再只写在 `AGENTS.md`。
- `README*` 与 `docs/README*` 是默认公开入口。
- `docs/runtime/`、`docs/program/`、`docs/capabilities/` 与 `docs/references/` 是仓库跟踪的技术材料。
- `docs/policies/` 收口稳定内部规则。
- `docs/history/omx/` 只作为历史归档入口。
