# 架构概览

Owner: `MedAutoScience`
Purpose: `architecture_and_product_boundary`
State: `active_current_truth`
Machine boundary: [contracts](../contracts/README.md)、源码、action catalog、generated surface handoff、OPL hosted readback 与真实 owner receipts 持有实现事实。

## 组成与数据流

MAS 是声明式医学研究 Package：`agent/` 提供 Stage、专业知识、提示词和质量规则；`contracts/` 提供公开接口、Schema、环境需求与 handler bindings；`src/med_autoscience/` 提供必须在医学 owner 内完成的 authority 判断。Framework 编译并托管通用接口，Stage executor 消费这些声明和 ScholarSkills 能力，独立 reviewer 判断质量，MAS owner 消费与研究 identity 绑定的结果。

canonical agent/package id 是 `mas`，machine domain id 是 `medautoscience`，`med-autoscience` 是仓库与 plugin locator。Package、carrier 和 executor 各自独立：Codex Plugin 是分发投影，Codex CLI 是当前正式 executor，二者不定义医学身份或安装真相。仓库采用单源布局（`agent/`、`contracts/`、`src/`、`runtime/` 仅在仓根维护一份权威源码，`plugins/med-autoscience/` 在 Git 中只保留薄载体壳，完整镜像载体按需由 `scripts/materialize_plugin_carrier.py` 在构建期物化到 gitignored 路径）。

## Owner 边界与 OPL 合同映射

| Owner | 持有的事实与行为 |
| --- | --- |
| MAS | study/source、医学判断、quality/publication、artifact 和 memory authority；领域结果与 receipt |
| OPL Framework | Package discovery/activation 聚合、生成接口、StageRun/Attempt、环境、provider transport、telemetry、runtime ledger 与通用投影 |
| OPL App | 用户产品和 UI，消费公开 state/action 与 MAS contribution |
| ScholarSkills | 可发现的专业方法、模板与工具；不签 MAS verdict |

| MAS 声明 | Framework 消费内容 | MAS 保留的 authority |
| --- | --- | --- |
| `contracts/domain_descriptor.json` | Package/domain identity、workspace binding、inventory projection | 论文库存、业务状态、study root |
| `contracts/action_catalog.json` 与 `domain_handler_registry.json` | Stage interface 与 closed authority dispatch | 医学结果、receipt 与 forbidden-write 判断 |
| `contracts/stage_quality_cycle_policy.json` | Attempt 角色、预算、Review protocol | rubric、finding、领域路由和 quality 判断 |
| `contracts/durable_knowledge_catalog.json` | policy/body locator、body-free metadata、receipt refs | memory 正文、accept/reject 与研究策略 |
| `contracts/runtime_detail_contribution_contract.json` | selected-work-item identity 与 activity-log 结果 | 研究 trajectory 与业务状态 |
| `contracts/foundry_agent_series.json` | canonical policy refs、fingerprint 与领域 delta | 医学领域扩展 |

`mas-scholar-skills` 是 required capability dependency。依赖 presence 与所需入口可调用性决定 MAS composition readiness；完整 Package 安装需实际 carrier readback，不能从 plugin 文件存在、共享 release snapshot 或文档推导。

`contracts/runtime_environment_requirements.json` 的 `runtime_profile_sources.display` 声明 ScholarSkills 中的 renderer dependency Profile。普通 `opl env prepare --domain mas --profile display` 由 Framework 解析这份领域声明；医学绘图依赖的包内位置不再写在通用 CLI 中。

MAS 只消费 host 注入的 runtime/provider payload，校验 study、route、Attempt 与 authority identity；不启动私有 runtime、解析 OPL binary 或自行发起 provider transport。Framework Python helper 来自 `OPL_FRAMEWORK_PYTHON_ROOT` 指向的 Framework `python/`，本仓不 vendoring 或锁定 Framework implementation。

## 产品与 Workbench 边界

MAS 不维护 repo-local product shell、cockpit、Portal、HTML/Markdown renderer 或终端 action shell。CLI、MCP、Skill、product-entry、status read model、workbench drilldown 与 action transport 由 OPL 从 MAS pack 生成或托管：

- **公开论文入口**：从 `contracts/action_catalog.json` 的六个 Stage action 选择（`direction_and_route_selection`、`baseline_and_evidence_setup`、`bounded_analysis_campaign`、`manuscript_authoring`、`review_and_quality_gate`、`finalize_and_publication_handoff`），控制链为 `Codex CLI selected stage -> nonbinding route context -> OPL readback -> MAS owner consumption`。
- **Host-only 内部动作**：qualification work-item provisioning、study initialization、study lifecycle reactivation、candidate admission、build-dependency currentness 与 paper mission 六个 catalog action 及 `self_evolution_closeout` 只通过 closed handler registry 托管，不构成用户命令。
- **Workbench 与 Inspection Package 边界**：OPL hosted workbench 可显示 stage/mission refs、owner receipt、typed blocker、human gate、evidence/artifact refs、runtime diagnostics 与 currentness，但不得写 study truth、publication eval、controller decision、canonical paper、artifact body、memory body 或 submission package；不得从 queue、attempt、provider 或 UI 文案推断 current owner 或 readiness。Inspection package 仅作人类审阅材料，不能授权 publication/submission 或清除 quality gate。

`plugins/med-autoscience/bin/mas-app-contribution` 产生只读 App contribution（不构成第二套 workbench 或状态 owner），具体输入与渲染边界见 [Runtime Detail Contribution](./references/integration/mas-runtime-detail-contribution.md)。

## 知识来源与执行边界

MAS 产品知识由 `contracts/durable_knowledge_catalog.json` 登记，采用 OPL 的 `scope`（product/owner/topic/project）与 `content_kind`（mechanism/policy/state/decision）合同。已有 Obsidian 或 Markdown 资料库可直接绑定为主源，研究原始数据、文献、论文与分析结果继续由业务工程维护，`memory/portfolio/data_assets/` 仅作数据资产治理投影。读取、来源变更与写回边界见 [知识与记忆政策](./policies/domain_memory_markdown_first_policy.md)。

- 公开 Stage 接口与七个 closed registry handler 的边界见 [Runtime 边界](./runtime/runtime_boundary.md)。
- Stage 内 refinement、独立 Review/repair、跨 Stage Meta Review、decisive Attempt 路由与机械 Final Handoff 见 [Stage / Route / Handoff](./runtime/stage_route_handoff_standard.md)。
- Review scope currentness 与 revision consumption 见 [质量循环](./runtime/progress_first_quality_loop.md)。
- `standard_agent_interface.inventory_projection` 声明 `workspace_index.json#/studies` 只读映射（回答业务库存与状态，机器消费 JSON，`STUDY_STATUS.md` 仅为人读 ref），不因缺失 execution/telemetry ledger 改写研究状态。

## 扩展与证据

新增能力先更新声明与 Schema，再使用 OPL generated/hosted surface；只有无法声明化的医学 authority 才加入 closed registry。软件机制的 self-evolution closeout 仅消费验证完成的 work-order draft，返回 domain receipt、no-regression evidence 或 typed blocker，不能授权论文 quality、publication、submission 或 export。

当前证据入口见 [状态](./status.md)，长期禁止边界见 [约束](./invariants.md)，研究工作区事实分层见 [Workspace 职责与接入](./source/study_workspace_target_state.md)。
