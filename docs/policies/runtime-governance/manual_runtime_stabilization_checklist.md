# 手工测试与运行面稳定化清单

Owner: `MedAutoScience`
Purpose: `Define stable MAS runtime governance, dependency, owner-boundary, and stabilization policy.`
State: `active_policy`
Machine boundary: Human-readable runtime-governance policy only; runtime truth remains in contracts, OPL generated/read-model output, runtime ledgers, controller artifacts, live readback and owner receipts.

## 当前结论

MAS 已退役 repo-local CLI/MCP/runtime supervision/installer/workbench wrapper。本清单只核对 current generated action surface、MAS authority output 与 OPL runtime readback，不把旧命令当作人工验收入口。

MDS / DeepScientist 只作为 historical fixture、explicit archive import、backend audit、upstream learning 或 parity oracle reference；Hermes 只可指外部 runtime 项目/服务、显式 proof lane 或历史 provenance。

## 稳定功能面

| 功能面 | 当前入口 | 必须核对 | 不证明 |
| --- | --- | --- | --- |
| public Stage execution | six OPL-hosted Stage actions in `contracts/action_catalog.json` | action/schema/Stage manifest binding、workspace/study identity、StageRun receipt | runtime live、paper progress、quality verdict |
| stage tool use | Stage Tool Affordance Boundary | capability refs、permission/write scope、forbidden authority、tool result refs | tool success 等于 stage/domain completion |
| authority evaluation | host-only `paper_mission_authority_evaluate` | closed handler registry、pure callable、no user surface、authority output shape | public command、provider attempt、publication verdict |
| environment | OPL `env prepare/run` owner surface | requirement profile、artifact root、platform 与 execution receipt | MAS domain ready、visual quality |
| runtime health | OPL current-control/provider/attempt/worker readback | same-identity live attempt、lease、Temporal/worker liveness、terminal closeout | MAS stage completion、paper delta |
| publication/quality | MAS `publication_eval/latest.json`、quality gate/owner receipt | current study identity、source/artifact refs、owner authority | submission completed unless separately receipted |

六个公开 action 是 `direction_and_route_selection`、`baseline_and_evidence_setup`、`bounded_analysis_campaign`、`manuscript_authoring`、`review_and_quality_gate` 和 `finalize_and_publication_handoff`。具体 CLI/MCP/tool spelling 由 OPL 从 V2 catalog、schemas 与 Stage manifest 生成；不要在本文维护手写命令或固定顺序。

## Legacy / internal residue

以下名称已退出 V2 public/default surface，只允许出现在 internal residue inventory、active-caller migration、provenance/tombstone 或 no-resurrection 语境：

- `doctor`、`backend-audit`、`backend-upgrade`、`overlay-status`、`bootstrap`；
- `runtime domain-diagnostic-report`、`domain-health-diagnostic`、`paper-mission-owner-surface`、`owner-route-reconcile`；
- `study progress-projection`、`publication gate`、`study delivery-sync`；
- `mainline_status`、`mainline_phase`、`submit_study_task`、`launch_study`、`study_progress`、`study_state_matrix`、`paper_mission`、`domain_handler_export`、`domain_handler_dispatch`；
- `scientific_capability_registry`、`display_pack_*` 与 direct `MedAutoScienceDomainEntry.dispatch`；
- `ops/medautoscience/bin/*`、repo-local LaunchAgent/systemd/cron/docker service；
- `medautosci` parser、`medautosci-mcp` 与 repo-local JSON-RPC transport。

对应医学诊断、publication gate、delivery mutation、backend audit 等 pure/internal functions 只能在有 active caller、明确 authority boundary 和迁移门时暂留；它们不得包装成文档命令、第二 handler registry 或第二控制面。需要公开能力时，应优先进入现有 Stage Tool Affordance Boundary；只有独立 Stage 语义成立时才增加 Stage action。

## Live evidence gate

- `program_id`、`study_id`、`quest_id`、`active_run_id` 不得混写。
- OPL descriptor/interface ready 只证明结构 currentness。
- provider/queue/attempt complete 只证明 transport evidence。
- paper progress 只来自 canonical artifact/paper delta、MAS owner receipt、quality gate receipt、typed blocker、human gate 或 route-back。
- publication-ready、artifact mutation authorization、domain-ready 和 production-ready 必须有对应 fresh live/readback/artifact/receipt evidence。
- external workspace、legacy fork 或 archived runtime 的诊断结果不得恢复 MDS/Hermes 为默认 owner。

## 验证停止条件

人工检查只有在当前 action/interface readback、same-identity OPL runtime evidence、MAS owner surface 与 forbidden-write boundary一致时才可关闭。任何仅靠 docs、focused tests、queue empty、descriptor ready、package import 或旧 diagnostic output 的结论都保持 `not_proven`。

## 相关回归面

- [Runtime boundary](../../runtime/contracts/runtime_boundary.md)
- [Agent runtime interface](../../runtime/contracts/agent_runtime_interface.md)
- [Controllers](../../runtime/control/controllers.md)
- [Study runtime orchestration](../../runtime/control/study_runtime_orchestration.md)
- [Study truth kernel](../../runtime/projections/study_truth_kernel.md)
- [External runtime dependency gate](./external_runtime_dependency_gate.md)
- [MDS owner boundary](./mas_mds_owner_boundary_contract.md)
