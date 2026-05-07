# 文档索引

[English](./README.md) | **中文**

这个目录是 `Med Auto Science` 的技术阅读层。
仓库首页继续优先写给医生、课题负责人和医学研究团队。
这里负责承接产品边界、操作入口、运行合同和维护记录。

## 按读者类型进入

| 读者 | 建议起点 | 目的 |
| --- | --- | --- |
| 潜在用户、医生、医学专家 | [仓库首页](../README.zh-CN.md) | 先判断这个系统能解决什么问题，再决定是否进入技术细节 |
| 技术规划者、架构读者、方向同步读者 | [项目概览](./project.md)、[当前状态](./status.md)、[架构](./architecture.md)、[不可变约束](./invariants.md)、[关键决策](./decisions.md) | 快速抓住当前角色、边界和运行方式 |
| 开发者与维护者 | `docs/runtime/`、`docs/program/`、`docs/capabilities/`、`docs/references/`、`docs/policies/`、[历史归档索引](./history/README.zh-CN.md) | 查看实现相关材料、治理记录和历史脉络 |

## 这一层负责什么

- 仓库首页负责解释 `Med Auto Science` 适合什么问题、谁来用、怎么开始。
- 核心五件套负责解释产品边界、当前状态、架构、不变量和关键决策。
- `docs/runtime/`、`docs/program/`、`docs/capabilities/`、`docs/references/`、`docs/policies/` 保存实现、维护和历史技术材料。

## 当前阅读基线

- `Med Auto Science` 是面向专病研究的医学研究 domain agent，配有单一 MAS app skill，也承担论文交付工作台角色。
- 默认用户最关心的是研究问题、工作区语境、人话进度和文件交付。
- `CLI`、`MCP`、`controller` 属于操作与自动化入口。
- 稳定可调用面通过单一 MAS app skill 对外承接，包含本地 CLI、workspace commands / scripts、durable surface 与 repo-tracked contract。
- `product-frontdesk`、`workspace-cockpit`、`study-progress` 与 product-entry manifest 继续是单一 app skill 之下的内部 command/projection contract，不是独立公开产品入口。
- `OPL` 集成、product-entry manifest 和其他机器可读桥接面都属于集成或参考层。
- `OPL Runtime Manager` 是目标形态中的 family-level 薄运行管理层，位于外部 `Hermes-Agent` substrate 之上；它可以消费 MAS task registration、runtime-control projection、status/artifact locator 与 wakeup/approval 边界，但不持有 MAS study truth。
- `Hermes-Agent` 只保留在显式可选 hosted runtime 或 reference-layer 语境中，不改写默认 capability contract。
- `MedDeepScientist` 在迁移期继续是受控后端、行为等价 oracle 和 upstream intake buffer；MAS 继续是唯一 research / publication owner。
- MAS standalone GitHub Release / 独立 installer 不是当前用户安装通道；分发叙事应指向当前 OPL 管理模块路径，或未来 OPL Packages/GHCR module 坐标。
- AI-first 是当前可运行质量线的方向，落在 pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 和真实论文 soak 上，不通过测试或 preflight contract 约束文档措辞。
- `StudyTruthKernel` 与 `RuntimeHealthKernel` 是当前 study truth 与 runtime health 的 read-model reducer；普通读取只生成 shadow projection，materialized snapshot 必须由显式 reconcile、controller tick 或 runtime watch apply 写入。
- `study_macro_state/latest.json` 与 `owner_route` 承载用户宏观状态和可执行 owner 票据。`study-state-matrix`、supervisor consume、dispatch execution 与 lifecycle projection 都应收敛到这些 surface，而不是各自局部重算。
- Artifact retention 是文件生命周期投影，不是 authority。终局 stop-loss 精简只能先生成 dry-run plan，后续任何物理 apply 都必须有 manifest、sha256、restore index 与 restore proof。
- 初稿质量作为写作前运行关注点处理：MAS 应生成医学期刊可读的 manuscript-native prose，而不是 controller notes、figure/table anchor scaffold 或正文里的行政占位。
- 产物证明采用 canonical-source-first：manuscript、figures、tables 和 package 都应能从 canonical source 重建后再作为交付证据。
- 真实论文 soak 仍是 AI-first 线的主要证据缺口；文档应明确这个缺口，不把目标层能力写成已经全部证明的当前事实。
- Workspace Git/storage 边界已经进入当前维护合同：root Git 显式 opt-in 且只作为 maintenance-only 边界，generated/runtime artifacts 明确排除，storage-audit repair 按实际 apply strategy 报告释放量。
- Runtime lifecycle 历史与索引进入 SQLite sidecar 方向；SQLite 负责 report/state/storage audit 的索引、历史、摘要与游标，authority surface、restore metadata 和论文交付产物继续保持文件形态。
- 历史迁移术语和旧命名继续留在参考层或历史层。

## 技术工作集

开始改仓库状态前，先读这些文件：

- [项目概览](./project.md)
- [当前状态](./status.md)
- [架构](./architecture.md)
- [不可变约束](./invariants.md)
- [关键决策](./decisions.md)
- [文档组合治理](./docs_portfolio_consolidation.md)

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
- [Study truth kernel](runtime/study_truth_kernel.md)
- [Runtime health kernel](runtime/runtime_health_kernel.md)
- [Study macro state 与 owner route](runtime/study_macro_state_and_owner_route.md)
- [Artifact retention operations contract](runtime/artifact_retention_operations_contract.md)
- [Artifact inventory projection](runtime/artifact_inventory_projection.md)
- [Canonical artifact contract](runtime/canonical_artifact_contract.md)
- [Study runtime 控制面](runtime/study_runtime_control_surface.md)
- [Study runtime 编排](runtime/study_runtime_orchestration.md)
- [Workspace knowledge 与 literature 合同](runtime/workspace_knowledge_and_literature_contract.md)
- [Workspace knowledge 与 literature 实施计划](runtime/workspace_knowledge_and_literature_implementation_plan.md)

### 能力线文档

- [能力线文档索引](capabilities/README.zh-CN.md)
- [医学展示平台主线](capabilities/medical-display/medical_display_platform_mainline.md)
- [医学展示文档组合治理](capabilities/medical-display/medical_display_portfolio_consolidation.md)
- [医学展示 active board](capabilities/medical-display/medical_display_active_board.md)
- [医学展示面审计指南](capabilities/medical-display/medical_display_audit_guide.md)
- [医学展示面模板目录](capabilities/medical-display/medical_display_template_catalog.md)
- [医学展示面家族路线图](capabilities/medical-display/medical_display_family_roadmap.md)
- [医学展示面视觉审计协议](capabilities/medical-display/medical_display_visual_audit_protocol.md)

### 项目推进与维护记录

- [MAS/MDS 自治操作系统 program](program/mas_mds_autonomy_operating_system_program.md)
- [Program portfolio consolidation](program/program_portfolio_consolidation.md)
- [MAS/MDS 统一增强 program](program/mas_mds_unified_enhancement_program.md)
- [Runtime lifecycle SQLite 迁移 program](program/runtime_lifecycle_sqlite_migration_program.md)
- [MAS 单项目 MDS 吸收 program](program/mas_single_project_mds_absorb_program.md)
- [MAS 单项目质量与自治主线](program/mas_single_project_quality_and_autonomy_mainline.md)
- [MedDeepScientist 解构地图](program/med_deepscientist_deconstruction_map.md)
- [外部运行时依赖门禁](program/external_runtime_dependency_gate.md)
- [Merge And Cutover Gates](program/merge_and_cutover_gates.md)
- [项目修复优先级地图](program/project_repair_priority_map.md)
- [课题进度投影](runtime/study_progress_projection.md)
- [Program 历史归档](history/program/README.zh-CN.md)

### 集成参考

- [轻量产品入口与 OPL 交接](references/lightweight_product_entry_and_opl_handoff.md)
- [病种 workspace 快速起步](references/disease_workspace_quickstart.md)
- [工作区架构](references/workspace_architecture.md)

### 参考资料

- [Domain Harness OS 定位](references/domain-harness-os-positioning.md)
- [Research Foundry 定位](references/research_foundry_positioning.md)
- [Research Foundry 与 Med Auto Science 的仓库拆分边界](references/repo_split_between_research_foundry_and_med_autoscience.md)
- [系列项目文档治理清单](references/series-doc-governance-checklist.md)

### 稳定内部规则

- [内部规则索引](policies/README.md)
- [运行模型规则](policies/platform_operating_model.md)
- [数据资产管理](policies/data_asset_management.md)
- [研究路线偏置规则](policies/research_route_bias_policy.md)
- [发表门控规则](policies/publication_gate_policy.md)
- [AI-first 质量边界规则](policies/ai_first_quality_boundary.md)
- [医学稿件初稿质量规则](policies/medical_manuscript_first_draft_quality.md)

### 追溯记录

- [Program 目录](program/)
- [References 目录](references/)
- [历史归档索引](history/README.zh-CN.md)
- [能力线历史归档](history/capabilities/README.zh-CN.md)
- [Superpowers 过程草稿归档](history/superpowers/README.zh-CN.md)

## 文档规则

- 继续把 [仓库首页](../README.zh-CN.md) 保持成医生和非技术专家可读的入口。
- 继续把公开文档保持成中英双语镜像。
- 运行时、推进记录、能力线和规则文档可以技术化，但公开首页继续围绕研究工作区、进度和文件组织。
- 历史材料继续可读，当前默认用户路径继续聚焦研究问题、工作区推进和论文交付。
- 文档负责把当前行为、运行方向和证据缺口讲清楚；不要用测试或 preflight contract 约束文档措辞。

## 治理说明

- 文档治理统一冻结在 [系列项目文档治理清单](references/series-doc-governance-checklist.md)、技术工作集和仓库跟踪的合同文档表面中，而不再只写在 `AGENTS.md`。
- `README*` 与 `docs/README*` 是默认公开入口。
- `docs/runtime/`、`docs/program/`、`docs/capabilities/` 与 `docs/references/` 是仓库跟踪的技术材料。
- `docs/policies/` 收口稳定内部规则。
- `docs/history/` 只作为历史归档入口。
