# 架构概览

Owner: `MedAutoScience`
Purpose: `architecture_current_truth`
State: `active_current_truth`
Machine boundary: [contracts](../contracts/README.md)、源码与真实 owner receipts 持有实现事实。

## 组成与数据流

MAS 是声明式医学研究 Package：`agent/` 提供 Stage、专业知识、提示词和质量规则；
`contracts/` 提供公开接口、Schema、环境需求与 handler bindings；
`src/med_autoscience/` 提供必须在医学 owner 内完成的 authority 判断。
Framework 编译并托管通用接口，Stage executor 消费这些声明和 ScholarSkills 能力，
独立 reviewer 判断质量，MAS owner 消费与研究 identity 绑定的结果。

canonical agent/package id 是 `mas`，machine domain id 是 `medautoscience`；
`med-autoscience` 是仓库与 plugin locator。Package、carrier 和 executor 各自独立：
Codex Plugin 是分发投影，Codex CLI 是当前正式 executor，二者不定义医学身份或安装真相。

## Owner 边界

| Owner | 持有的事实与行为 |
| --- | --- |
| MAS | study/source、医学判断、quality/publication、artifact 和 memory authority；领域结果与 receipt |
| OPL Framework | Package discovery/activation 聚合、生成接口、StageRun/Attempt、环境、provider transport、runtime ledger 与通用投影 |
| OPL App | 用户产品和 UI，消费公开 state/action 与 MAS contribution |
| ScholarSkills | 可发现的专业方法、模板与工具；不签 MAS verdict |

`mas-scholar-skills` 是 required capability dependency。依赖 presence 与所需入口可调用性
决定 MAS composition readiness；完整 Package 安装需实际 carrier readback，
不能从 plugin 文件存在、共享 release snapshot 或文档推导。

MAS 只消费 host 注入的 runtime/provider payload，校验 study、route、Attempt 与 authority
identity；不启动私有 runtime、解析 OPL binary 或自行发起 provider transport。
Framework Python helper 来自 `OPL_FRAMEWORK_PYTHON_ROOT` 指向的 Framework
`python/`，本仓不 vendoring 或锁定 Framework implementation。

## 执行与领域函数

公开能力由六个 canonical Stage action 承载；六个 host-only authority action 和独立
self-evolution closeout 共绑定七个 registry handler。完整接口和绑定表仅由
[Agent Runtime Interface](./runtime/contracts/agent_runtime_interface.md) 解释。

源码还包含纯校验 helper、CSL assets，以及 attempt-local bounded-analysis snapshot
adapter；后者读取并核验统计输入，不能签 Review verdict 或写通用 runtime。
`plugins/med-autoscience/bin/mas-app-contribution` 产生只读 App contribution，
不构成第二套 workbench 或状态 owner。

Stage 内 refinement、独立 Review/repair、跨 Stage Meta Review、decisive Attempt 路由与
机械 Final Handoff 的唯一流程说明是 [Stage / Route / Handoff](./runtime/stage_route_handoff_standard.md)。
Review scope currentness 和 revision consumption 见
[质量循环](./runtime/control/progress_first_quality_loop.md)。

## 可见状态与领域真相

`standard_agent_interface.inventory_projection` 声明 workspace
`workspace_index.json#/studies` 的只读字段映射。它回答论文库存与 MAS 业务状态；
OPL execution ledger 回答运行中的 Stage/Attempt，telemetry ledger 回答已归属的用量。
缺失 execution/telemetry 不能删除业务库存或改写 MAS 研究状态。
机器消费 JSON；`STUDY_STATUS.md` 只是人读 lifecycle ref。

App contribution 将业务 identity、状态和 artifact refs 交给公开 consumer。
[集成说明](./references/integration/mas-runtime-detail-contribution.md)
解释 producer 与 consumer 的验收边界；源码验证不能替代真实 App readback。

## 扩展与证据

新增能力先更新声明与 Schema，再使用 OPL generated/hosted surface。
只有无法声明化的医学 authority 才加入 closed registry；不得建立私有 parser、
installer、scheduler、queue、session store、currentness 或 renderer transport。

软件机制的 self-evolution closeout 仅消费验证完成的 work-order draft，
返回 domain receipt、no-regression evidence 或 typed blocker；不能授权论文 quality、
publication、submission 或 export。

当前证据入口见 [状态](./status.md)，长期禁止边界见 [约束](./invariants.md)，
研究工作区事实分层见 [Workspace](./source/study_workspace_target_state.md)。
