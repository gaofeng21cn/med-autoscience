# MAS Runtime 与 Handler 边界

Owner: `MedAutoScience`
Purpose: `runtime_owner_interface_retention_and_state_index_ssot`
State: `active_current_truth`
Machine boundary: 可执行真相归 `contracts/action_catalog.json`、`agent/stages/manifest.json`、`contracts/domain_handler_registry.json`、`contracts/runtime_environment_requirements.json`、OPL runtime readback 与 MAS owner receipts。

MAS 不是 runtime platform。Runtime 分工、公开与内部 handler 接口、artifact 保留操作与 StateIndex no-resurrection 边界统一归本页维护。

## Runtime 分工与 Progress Authority

| 职责域 | Owner | 禁止越权边界 |
| --- | --- | --- |
| scheduler / queue / attempt ledger / retry / dead-letter / resume / StageRun | OPL | 不得写 study truth、publication eval、controller decision、授权 canonical artifact mutation、接受/拒绝 memory body 或签 MAS owner receipt |
| StateIndex / workspace locator / lifecycle / storage / observability / env prepare & run | OPL | 不得把 queue/attempt/provider/UI/projection 状态解释成 paper progress 或 quality verdict |
| hosted CLI / MCP / Skill / product-entry / status / workbench | OPL | 仅投影 body-free refs 与 owner answer；不得自造 MAS verdict |
| 医学 policy / study truth / source readiness / AI reviewer & publication quality / artifact & memory authority / owner receipt / typed blocker / human gate | MAS | 不得建立通用 scheduler、runner、queue、attempt ledger、StateIndex、lifecycle store、手写 CLI/MCP transport 或私有环境安装器 |

默认控制链固定为：

`Codex CLI selected stage -> nonbinding route context -> OPL transport/readback -> MAS owner consumption`

## 公开与内部入口

- **六个公开 Stage action**：direction、baseline、analysis、manuscript、review、handoff 的完整 action id 与 schema 由 `contracts/action_catalog.json` 定义，binding 指向 `agent/stages/manifest.json`；CLI/MCP/Skill/product spelling 由 OPL 生成。
- **六个 host-only authority action 与七个 closed-registry callable**：catalog 中的 qualification work-item provisioning、study initialization、study lifecycle reactivation、candidate admission、build-dependency currentness 与 paper mission 仅供 host 调用（用户 surfaces 为 `null`）；`contracts/domain_handler_registry.json` 绑定上述六项与 Agent Lab `self_evolution_closeout`，共七个 callable（另包含 attempts 级只读 `bounded_analysis` snapshot adapter 与独立只读 `mas-app-contribution` producer）。
- **Handler 调用与回读**：Host 在创建 StageRun/Attempt 前解析 workspace/study identity 并执行 lifecycle admission（`contracts/study_initialization_contract.json`、`contracts/study_lifecycle_reactivation_contract.json`）；handler 只消费 host 提供的身份、exact refs、authority context 与当前证据，返回领域 result 或受限 CAS/materialization 授权，不执行文件、网络、进程、session、runtime lifecycle 或 Stage transition；Host 物化后必须回传 receipt。Attempt 协议见 [Stage / Route / Handoff](./stage_route_handoff_standard.md)。
- **Environment 与依赖**：MAS 在 `contracts/runtime_environment_requirements.json` 声明要求，OPL 负责 `env prepare/run`；Package 使用 `opl packages` 公开入口，ScholarSkills 缺失或所需能力不可调用只阻断 MAS（selected build 还须核对所需 validator 符号）。

## Artifact 保留操作与 StateIndex 边界

- **Artifact 保留与物理操作**：OPL 可生成 retention plan、checksum、manifest、restore proof、archive locator 与 lifecycle receipt，并在获得合法授权后执行 scoped cleanup；MAS 持有医学 artifact 分类、mutation authorization 与 owner result。cache/重建投影须在 exact target hash、rebuild source 与 restore/readback 齐全时才可删除；canonical source、data release、audit log 与 human handoff 默认保留；cold archive 须有 manifest、checksum、restore command 与 verified restore proof；terminal stop-loss 不自动授权删除 authority surface；MAS 不保留 repo-local cleanup apply、SQLite compactor 或 storage adapter。
- **StateIndex no-resurrection**：MAS-local StateIndex、SQLite lifecycle、body-free adapter 与 index projection builder 已全部退役（见 `contracts/durable_knowledge_catalog.json`、`contracts/state_index_kernel_adoption.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 与 [关键决策](../decisions.md#私有控制面退役边界与-provenance)）。允许进入 OPL StateIndex/Ledger 的仅为 StageRun/Attempt/artifact/source/rubric/package refs、MAS owner receipt/blocker/human-gate/route-back/quality-debt refs 与 archive/checksum/restore provenance refs；发现任何退役 database/adapter/wrapper 恢复为 active caller 即视为 regression 并直接删除。

## 验证与 Accept 边界

Repo 边界由 `scripts/verify.sh`（[仓库与运行治理](../policies/repo_and_runtime_operations.md)）、`tests/test_standard_agent_boundary.py`、source closure、default-callers 与 residue-decisions 保护；Contract/schema、focused tests、descriptor ready、projection clean、queue empty 和 dry-run 只证明结构行为。Runtime ready 需 fresh OPL readback，paper/quality/publication/cleanup/restore 结论需 fresh MAS owner、independent Review、exact hash/receipt 与 artifact readback。开放差距见 [开放计划](../active/mas-ideal-state-gap-plan.md)。
