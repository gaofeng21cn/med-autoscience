# AI-first 论文自治闭环

Status: `active_target_and_acceptance_owner`
Date: `2026-05-16`
Owner: `MedAutoScience`
Purpose: `paper_autonomy_acceptance_contract`
State: `active_target_and_acceptance_owner`
Machine boundary: 本文是人读目标和验收合同。机器真相继续归 `study_charter`、evidence/review ledger、`publication_eval/latest.json`、`controller_decisions/latest.json`、`progress_projection`、`domain_health_diagnostic`、domain-handler receipt、owner-route receipt、manuscript/package rebuild proof 和真实 workspace artifact refs。

完整历史记录见 [2026-05-10 AI-first paper autonomy full record](../history/program/ai_first_paper_autonomy_closure_program_2026_05_10_full_record.md)。历史 full record 只用于追溯当时的 lane、证据和外部工程参考；当前执行口径以本文、[MAS 当前开发线路](./current-development-lines.md) 和 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) 为准。

## 当前定位

本文是 MAS 论文自治的目标和验收面。它定义 MAS 要在真实 paper line 上交付什么证据：AI reviewer finding、repair work unit、canonical artifact delta、publication gate replay、AI reviewer recheck、route decision、human gate、stop-loss 或明确 typed blocker。

它不持有 OPL provider 实现、One Person Lab App UI、通用 queue / attempt ledger / retry-dead-letter / human-gate transport，也不维护旧 MDS/Hermes/local scheduler 的退役清单。通用运行外围归 OPL Framework；MAS 持有医学研究 truth、paper quality、publication judgment、reviewer repair、route decision、evidence/review ledger、canonical manuscript/package authority 和 owner receipt。

## 当前状态

repo-level 论文自治 loop 已具备 callable surface、owner receipt 和 focused proof，但仍处在 production evidence gate：

| 面 | 当前状态 | owner |
| --- | --- | --- |
| reviewer finding -> repair | `repo_surface_landed` | MAS reviewer / repair owner surfaces |
| canonical delta / gate replay / reviewer recheck | `repo_surface_landed` | MAS publication gate、AI reviewer workflow、artifact authority |
| route decision / weak-result handling | `repo_surface_landed` | MAS route decision 与 controller decision surfaces |
| stage knowledge / publication-route memory | `repo_contract_and_read_model_landed` | MAS stage knowledge packet、closeout packet、memory router receipt |
| provider-hosted paper apply | `dm002_owner_receipt_refs_observed_scaleout_pending` | OPL provider transport + MAS domain-handler / owner chain |
|真实 paper closure | `evidence_gated_live_soak` | live MAS study truth surfaces |

当前可以声明的是：MAS 有 provider-guarded apply receipt surface、route-memory consumed / writeback ref chain、多条真实 paper line 的 guarded proof surface、DM002 owner receipt success refs、OPL production proof ingestion 和 no-forbidden-write boundary。不能声明 OPL provider proof、queue completion、repo tests、provider attempt completion 或单条 DM002 success refs 等于 paper closure、submission readiness 或 publication-ready。

## 验收合同

一次真实 autonomous work unit 只有在 MAS owner surface 中留下以下任一结果时，才计入论文自治进展：

- manuscript、table、figure、result、package、evidence ledger 或 review ledger 的 canonical delta；
- publication gate replay 后 owner 前进；
- AI reviewer judgment update；
- route decision、claim downgrade、bounded repair、switch-line、stop-loss 或 human gate；
- typed blocker，且 blocker 明确缺失的 owner、input、permission 或 scientific constraint。

Worker liveness、queue item、status refresh、provider completion、只读 projection 和文档状态都只是支撑信号，不是 paper progress。

## Gate 分类

| gate | class | 当前状态 | 可接受证据 |
| --- | --- | --- | --- |
| `live_paper_owner_chain` | `production_evidence_gate` | `planned; guarded surfaces landed` | MAS truth surface 中的 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 typed blocker。 |
| `provider_hosted_guarded_apply` | `production_evidence_gate` | `surface_landed; live soak pending` | OPL attempt ref + MAS domain-handler dispatch receipt + MAS owner receipt + no-forbidden-write proof；provider completion alone 不计入。 |
| `human_gate_resume` | `production_evidence_gate` | `owner_boundary_landed` | MAS controller/runtime 记录 gate reason、resume/refusal、next owner 和 blocker；OPL signal 只是 transport。 |
| `publication_route_memory_writeback` | `functional_follow_through_gate` | `implemented; scaleout pending` | Stage closeout proposal、MAS router accepted/rejected/blocked receipt、body-free refs、operator grouping 与 stale/deprecated review summary。 |
| `stage_review_index_instance` | `functional_follow_through_gate` | `locator proof landed; live instances pending` | live attempt 产出 review page/index refs、freshness、claim impact、next owner 或 blocker；review/index 不授权 publication readiness。 |

## 与其他 owner 文档的关系

- P1 / Workbench 产品化读 [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md)。
- OPL framework、provider、domain-handler 和 standard Agent runtime boundary 读 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)、[MAS 当前开发线路](./current-development-lines.md) 和 [Runtime Boundary](../runtime/contracts/runtime_boundary.md)。
- P3 / MDS provenance、monolith closeout、archive/parity guard 读 [MAS/MDS Owner Boundary Contract](../policies/runtime-governance/mas_mds_owner_boundary_contract.md) 和 [MDS absorb guard history](../history/program/mas_single_project_mds_absorb_guard_2026_06_07.md)。
- P3a / `domain_authority_refs_index`、retired-runtime SQLite/file provenance、restore proof 和 stale runtime-control drift guard 读 [Domain Authority Refs Index Guard](../runtime/domain_authority_refs_index_guard.md)。

新增实现细节先按 [Program Portfolio Consolidation](./program_portfolio_consolidation.md) 和 [MAS 当前开发线路](./current-development-lines.md) 归类，再落到实际 owner 文档；本文只保留论文自治目标、验收口径和 live evidence gate。
