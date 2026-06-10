# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、domain-handler receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-06-03`

## 文档读法

- 本文是 MAS 当前唯一 single Active Truth plan：维护当前唯一真相、目标态、已落地状态、功能/结构差距、测试/证据差距、近期完善计划、完成门和历史索引。
- MAS 的 north-star 目标态读 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)。本文只保留面向执行的差距和顺序。
- [MAS 当前开发线路](./current-development-lines.md) 只作为内容线索引；若它与本文冲突，以本文为准，并把仍有效内容折回本文、核心 canonical docs、runtime/contracts/policies 或 history/tombstone。
- [MAS / OPL Stage Native 状态机设计](./mas-opl-stage-native-state-machine.md) 是 Stage Native 后的下一层顶层设计与当前 foundation landing 记录：保留 stage folder artifact/evidence 面，把 Stage 状态收敛到最小 StageRun Kernel，把 Stage transition authority 收敛到 MAS owner receipt / typed blocker。它不新增 MAS controller system，不替代本文；MAS 主干已落地 StageRun profile / projection / focused synthetic canary foundation，并在 canonical path follow-through 中把 stage folder 文件名收敛到 `stage_manifest.json`、`receipts/owner_receipt.json`、`receipts/typed_blocker.json` 等当前口径。2026-06-05 DM002 / DM003 live canary 已通过 refs-only `stage-artifact-materialize` 推进到 terminal `08-publication_package_handoff` owner gate，但不声明 live paper line、publication verdict、submission-ready 或 `current_package` 已完成。
- [Co-Scientist Stage / Route 重构设计与执行规格](../runtime/designs/coscientist_stage_route_restructure.md) 是 Stage-native scientific work system 的 runtime-facing 执行规格和 provenance。2026-06-05 其剩余可学习点已落到 `agent/` semantic pack、machine-readable contracts、progress-first owner ticket projection、focused tests、runtime docs 和本文：`next-delta tournament`、`bounded micro-candidate generation`、`critique-as-repair-hint`、`budgeted memory`、`triggered meta-review`、`opportunistic knowledge prefetch` 只帮助 route 选下一步、reviewer 找缺口、memory 复用失败路径；它不替代本文的 single Active Truth owner，也不表示真实 paper-line 已关闭、production-ready 或任何 authority 已转移。
- [EvoScientist Progress-First Intake](../runtime/designs/evo_scientist_progress_first_intake.md) 记录 EvoScientist / EvoSkills 的 upstream learning foldback、完整目标态 sidecar execution architecture 与 repo 可调用执行面。EvoScientist v0.1.4 的 auxiliary model for background memory workers / tool selector 与 fire-and-forget observation memory，以及 EvoSkills v1.0.0 的 IDE / IVE / ESE research lifecycle memory，只作为 `ordinary progress spine` 的 async learning sidecar / auxiliary helper / fail-open tool selector / failed-path taxonomy / routing eval / stop-loss candidate；当前已落地 refs-only writer、CLI observe/read-latest、`study_progress` materialize hook 和 refs-only index family。它们不能阻断 ordinary progress spine，不能持有 MAS authority，不能替代 independent reviewer/auditor。`remaining_learning_plan=false` 是稳定机器口径，后续只允许按合同做生产 scheduler 或真实 evidence scaleout。
- [当前状态](../status.md) 只维护 current-state 摘要；dated closeout、receipt id、OPL worklist 数字、命令流水、旧 phase checklist、same-day follow-through 和 proof 过程进入 `docs/history/**`、runtime ledger、真实 workspace receipt 或提交历史。
- 差距按目标态判断。当前实现可运行只能作为迁移输入、风险和证据来源，不能反向定义 MAS 长期架构。

## 当前唯一真相

| 主题 | 当前结论 |
| --- | --- |
| MAS 身份 | MAS 是医学研究 domain agent，也是 OPL-compatible package。direct MAS app skill path 与 OPL-hosted path 必须回到同一套 MAS-owned stage、controller、durable truth、quality verdict、artifact authority、memory decision、owner receipt 和 typed blocker。 |
| 默认运行 | Hosted autonomous runtime 默认由 OPL/Temporal 承担；OPL 持有 stage attempt、queue、wakeup、retry/dead-letter、resume、human-gate transport、provider query、worker residency 和 operator projection。`Codex CLI` 是 stage 内第一公民 executor；Codex App 只承担 direct entry / 人机操作面，不作为任务启动后的外围持续 driver。 |
| MAS authority | MAS 持有 study truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body 与 accept/reject/blocker decision、artifact/package authority、source readiness、owner receipt、safe action refs 和 typed blocker。 |
| OPL authority | OPL 持有通用 scheduler、queue、attempt ledger、generic transition runner、lifecycle/index、memory/artifact locator、restore/retention shell、observability、repair projection、generated CLI/MCP/Skill/product-entry/domain-handler/status/workbench wrapper 和 App/workbench shell。 |
| MDS / DeepScientist / EvoScientist / EvoSkills | 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning、smoothness learning、progress accelerator / audit sidecar 和 parity oracle reference。可吸收经验是单循环、少默认门、持续产出、UI 体感、background memory worker、tool selector、observation memory 和 research lifecycle skill taxonomy；它们不回到 MAS 默认 backend、quality owner、artifact authority、memory authority 或 runtime owner。 |
| 当前机器面 | `agent/` 是 canonical medical research semantic pack；`contracts/foundry_agent_series.json`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是主要 machine-readable truth。 |
| 控制面收薄 | 稳定 execution contract 收敛为 `macro_state + owner_route + receipt_or_blocker + evidence_refs`。长 runtime/status reason、supersession reason、publication supervisor phase 和 operator/workbench 文案只做 diagnostic/read-model detail，不再成为跨入口执行授权。 |
| SQLite / State Index Kernel | MAS 是小文件 compaction 的首要 domain candidate，但长期 owner 是 OPL State Index Kernel。`contracts/stage_artifact_kernel_adoption.json#/state_index_kernel_adoption` 固定：SQLite sidecar 只存 refs、locator、cursor、checksum、source fingerprint、idempotency key、receipt/blocker/restore refs 和 bounded preview hash；study truth、publication eval、controller decisions、manuscript、package、evidence/review ledger、memory、artifact body、quality verdict 和 owner receipt authority 继续归 MAS 文件/receipt truth。 |
| StageRun Kernel foundation | Stage Native 目录产出思路保留为 artifact/evidence plane；MAS 主干已新增 `contracts/stage_run_kernel_profile.json`、`contracts/stage_run_canary_evidence.json`、`src/med_autoscience/controllers/stage_run_kernel.py` 和 `study_progress` StageRun projection binding，并把 materializer / index 收敛到 canonical `stage_manifest.json`、`receipts/owner_receipt.json`、`receipts/typed_blocker.json`、`inputs/consumed_artifact_refs.json`、`lineage/prov.json`、`projection/current_owner_delta.json` 路径，用最小 StageRun 状态壳表达 stage folder / manifest / receipt / blocker 派生状态；focused AI reviewer canary tests 已覆盖 owner receipt、typed blocker 与 provider terminal 不等于 domain accepted。2026-06-06 MAS terminal publication handoff apply 侧补齐 OPL execution authorization / closeout binding 消费：缺 OPL provider attempt / lease / execution authorization 时 fail closed 且不改 MAS owner receipt / typed blocker；有授权时只写 stage-native `handoff_owner_receipt.json` 或 `receipts/typed_blocker.json`，并把 refs-only `closeout_binding`、`current.json`、`latest_owner_answer_ref`、`hard_gate.owner_answer_*` 和 `delta_id` 绑定到 StageRun / manifest / current pointer / source fingerprint / idempotency key。MAS 只用 `OwnerReceipt` / `TypedBlocker` 关闭 Stage 和授权 route；`latest.json`、progress projection、Portal/workbench 只能是 receipt-derived read model。StageRun canary 还要求 candidate / grounded reflection / comparative selection / evolution and revision / meta-review / independent quality gate 只作为 Stage 内 advisory refs-only evidence，并验证旧 scheduler、runner、session store、status shell、workbench wrapper 没有重新获得 transition authority；controlled canary operator summary、overclaim boundary 和 legacy runtime residue guard 已作为 operator read-model-only contract/test 固定为 `platform_repair_controlled_fixture`，不授权 transition、closeout、quality/export 或 live resume；`contracts/stage_run_canary_evidence.json` 的 scope 是 `controlled_fixture_not_live_domain_progress`，不声明 DM002 / DM003 live domain progress。 |
| Ordinary progress handoff | `contracts/stage_run_kernel_profile.json#/ordinary_progress_handoff`、`contracts/stage_artifact_kernel_adoption.json#/stage_run_kernel_profile_binding` 与 `agent/stages/stage_route_contract.yaml#/ordinary_progress_handoff_policy` 已把普通推进主干机器化：默认 root 是 `current_owner_delta` / `stage_run_current_owner_delta`，executor 普通 step 可返回 `ProgressDeltaReceipt`，其 tier 固定为 `T0_progress_delta`，只记录 changed / produced / consumed refs、progress classification、next owner 和 next required delta。 | 该合同只解决“完成一个 concrete delta 后如何继续接力”，不授权 domain ready、publication-ready、submission-ready、quality/export ready、artifact mutation、memory accept/reject、production ready 或 physical delete；完整 Stage transition、delivery artifact 和 production evidence 继续分别走 `OwnerReceipt` / `TypedBlocker`、T2 delivery artifact、T3 production evidence 与 terminal gates。 |

## 目标态

MAS 的目标态是：

`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal medical authority functions`

这表示 MAS 只长期保留医学研究语义、stage pack、quality gate、publication/artifact/memory/source authority、domain transition、owner receipt 和必要医学 helper。通用 runtime platform、queue、attempt ledger、state-machine runner、memory/artifact locator、lifecycle/restore/retention、observability、workbench 和 generated entry/status wrapper 上收到 OPL Framework / shared family layer。

AI-first quality gate 必须由独立 reviewer/auditor agent invocation 关闭。程序函数只做 schema/provenance/authority refs 校验、持久化、owner receipt 签发、typed blocker、safe action refs 和 no-forbidden-write guard；脚本、regex、scorecard、file presence、queue completion 或 executor 自审不能替代医学质量判断。

控制面目标同步收薄为 `macro_state + owner_route + receipt_or_blocker + evidence_refs`。程序只决定当前 owner、allowed action、forbidden writes、idempotency 和 receipt/blocker；开放式医学语义、写作修订、质量判断和路线判断交由 prompt、skill、executor、独立 reviewer/auditor 与 evidence refs 承接。

## 当前完成进度

| Area | 当前进度 | 当前读法 |
| --- | --- | --- |
| Standard OPL Agent source shape | `standard_agent_source_shape_landed` | `agent/` pack、stage/action/memory/artifact contracts、generated surface handoff 与 production acceptance 已成为 MAS 当前机器面；`contracts/functional_privatization_audit.json` 与 focused tests 将 `functional_structure_gap_count` 固定为 `0`。 |
| Runtime owner split | `opl_owned_default` | 默认 hosted autonomous runtime 归 OPL/Temporal；MAS 保留 study truth、quality gate、artifact authority、owner receipt 和 typed blocker。 |
| Workspace target-state cleanup | `ops_bridge_retired_visual_clean_landed` | 新 workspace / bootstrap / monolith migration 不再生成 `ops/mas` 私有 runtime bridge；`ops/medautoscience/` 是唯一 MAS workspace ops 入口，`ops/mas/progress/` 只保留 Progress Portal 静态只读投影。`workspace-target-state-cleanup --visual-clean` 可归档已知 legacy study/ops residue，并对未分类 entry fail closed；这是 platform repair，不是 paper-line progress。 |
| Legacy runtime no-resurrection | `guarded` | `runtime_transport`、`mas_runtime_core*`、turn runner、worker lease 和旧 lifecycle writer 只能按 tombstone/provenance 或 OPL handoff refs 读取。 |
| DM002 / DM003 anti-stall control loop | `medical_paper_readiness_stop_loss_surface_followthrough_landed_live_owner_closeout_pending` | `always resolve to next owner`、AI reviewer currentness consumption、owner-route/read-model/liveness 优先级、closeout ingestion、gate-clearing receipt consumption 和 stale provider-attempt invalidation 已进入当前口径；2026-06-05 两篇先按用户要求 queue hold，随后 Stage Native live canary 用 refs-only materializer 把 stage artifact read-model 推进到 terminal `08-publication_package_handoff`。2026-06-06 fresh workspace evidence 显示 terminal handoff 已写出 MAS-owned `medical_paper_readiness_not_ready` typed blocker，并绑定 provider attempt、active lease、execution authorization decision、stage manifest、current pointer、source fingerprint 和 idempotency key；`projection/current_owner_delta.json` 当前指向 `MedAutoScience / complete_medical_paper_readiness_surface`。MAS repo 已落地该 owner callable / default-executor policy / owner-route reason / dispatch tests：它优先按当前 `medical_paper_readiness.next_action.surface_key` 消费同 surface 的 dispatch / request / ref payload，物化 canonical surface 或写 stable owner blocker，避免 stale dispatch 重放。2026-06-06 follow-through 已落地 `literature_provider_runtime`、`study_line_selection`、`archetype_analysis_contract`、`bounded_analysis_candidate_board` 四个 surface 的 owner-authored payload / materializer、surface/action scoped idempotency 和 closeout-binding result shape；2026-06-07 follow-through 继续落地 `stop_loss_memo` owner surface、verified literature materialization fallback provenance、current readiness surface 优先级和 stop-loss stale dispatch rejection，不写 paper、package、publication truth 或 quality verdict。Fresh read-only check 显示 readiness 已继续推进到 DM002 `ready_count=6/13`、下一 surface `target_journal_writing_layer`，DM003 `ready_count=1/13`、下一 surface `literature_scout`。当前 live owner closeout 仍要由 DM002 / DM003 owner run 产出匹配 StageRun/source/idempotency 的 owner receipt、quality gate receipt、typed blocker、human gate 或 route-back evidence；publication truth 仍不声明 blocked/partial 已关闭、publication-ready 或 package-ready。补偿链 retirement / tombstone 统一按 `contracts/runtime/legacy-active-path-tombstones.json#/stage_native_compensation_retirement_gate` 判断。 |
| Domain owner evidence shape | `shape_landed_live_scaleout_pending` | guarded apply、owner-route、body-free evidence packet、typed blocker shape、paper-line owner-chain result、domain-dispatch payload 和 OPL refs-only return shapes 已可消费；这些仍只是 refs/receipt/projection shape，不声明 paper closure、publication-ready、artifact mutation authorization、memory accept/reject 结论或 `current_package` 更新。 |
| Research evidence pack read-model / schema / canary | `read_model_schema_canary_evidence_landed_not_publication_ready` | read-model、schema validation、Progress Portal / runtime workbench stage review projection 和 canary expectation 已同口径 fail closed；它们只关闭最低科研审计链的可读 / 可校验 / fail-closed 证据。 |
| Docs lifecycle | `single_active_truth_owner_reconfirmed_2026_06_03` | 本文持有 current gap / completion plan；`docs/status.md` 持有 current-state summary；`docs/docs_portfolio_consolidation.md` 持有 docs lifecycle rules；dated closeout 与命令流水归 history/provenance。 |
| Progress-first Co-Scientist 增益层 | `agent_contract_source_tests_docs_landed_not_authority` | 六项机制已落到 `agent/stages/stage_native_semantic_pack.yaml`、`agent/stages/stage_route_contract.yaml`、hypothesis portfolio contract、StageRun profile、`current_owner_ticket.progress_enhancement_policy`、focused tests、本文、runtime design、handoff standard、operator runbook、invariants 和 status：它们是 advisory / refs-only / budgeted 推进增强层，只服务 next owner selection、reviewer gap finding 和 failed-path memory reuse；缺失或失败时不能阻断可执行 owner action，命中真实 hard gate 时必须转成 typed blocker / human gate / route-back / stop-loss。 |
| EvoScientist / EvoSkills progress sidecar | `repo_callable_worker_landed_not_authority` | EvoScientist v0.1.4 的 auxiliary background memory workers / tool selector / fire-and-forget observation memory 与 EvoSkills v1.0.0 的 IDE / IVE / ESE lifecycle memory 已折回为完整 nonblocking current-owner-following sidecar architecture，并落地 repo callable worker：`write_evo_scientist_sidecar_observation`、`medautosci evo-scientist-sidecar observe/read-latest`、`study_progress` materialize hook、`artifacts/runtime/evo_scientist_sidecar/` refs-only observation/latest，以及 refs-only state index family `evo_scientist_sidecar_ref`。`tool_selector_helper`、`observation_memory_sidecar`、`failed_path_taxonomy`、`routing_eval`、`attempt_budget_stop_loss` 都只能产生 refs-only hint、reviewer briefing、memory reuse candidate、route hint 或 no-loop signal；critical path 不等待 sidecar，缺失、失败、超时、预算耗尽或低置信时不得阻断 current owner action。 |
| Progress-first safety envelope | `contract_tests_runbook_landed_not_live_preflight` | `contracts/progress_first_safety_envelope.json` 已把错误完成、伪证据、旧 read-model、重复 receipt 和 artifact authority 漂移固定为五类风险，并把 Light / Co-Scientist / EvoScientist / EvoSkills 的混合模式收敛为 `current_owner_following_advisory_sidecar`：fail-open、refs-only、budgeted、JIT hard-gate only，不生成默认下一步，不阻塞 current owner action，不关闭 quality / publication / artifact / memory authority。该面由 focused meta test 和 runbook/decision/status 承载；它是 safety / audit hardening，不是 paper-line progress、publication-ready、domain-ready 或 production-ready。 |

当前 platform lane 的近期收口点是 `complete_medical_paper_readiness_surface`：把 owner action、accepted payload、payload-missing stable blocker、surface artifact path、readiness rebuild 和 OPL execution authorization / closeout binding 写成单一路径。`literature_provider_runtime`、`study_line_selection`、`archetype_analysis_contract`、`bounded_analysis_candidate_board` 和 `stop_loss_memo` 已进入该路径；下一层 functional tail 是继续按当前 readiness next action 扩展 owner-authored surface 或产出 stable blocker。2026-06-07 follow-through 补齐 `domain-owner-action-dispatch --payload-file/--payload-json`，使 OPL/App 生成的 refs-only consumer payload 可以进入 MAS dispatch selector，并复用已有 owner callable closeout-binding 链路；同日补齐 verified `publication_eval/literature_materialization.json` fallback，使 PubMed live fetch 失败但已有 verified PubMed records 时仍能生成 provider-backed payload 与 response ledger。这些只是 transport / read-model / owner-surface repair，不写 study truth。Fresh read-only check 显示 OPL worklist / cockpit current-owner identity 已重新收敛；MAS `study progress` 可投影 current executable owner action，但 active attempt id 会随 live owner run 变化，不能单独作为 owner answer。不得把 CLI transport、zero open worklist、typed blocker context、current owner action、active attempt 或结构 conformance 升级为 owner answer / domain ready。DM002 / DM003 live paper execution 不在本轮，由会话 `019e92c8-b940-7313-940b-ea892820d322` 继续处理；本轮不声明 paper readiness、publication-ready、submission-ready、quality verdict、`current_package` fresh、domain-ready 或 production-ready。这个收口是 Stage Native / StageRun / current owner delta 黄金路径上的默认面压缩，不是推倒重构，也不是恢复 MAS generic runtime loop。

2026-06-09 顶层规划更新：MAS paper-line 默认推进采用 `ordinary progress spine + audit sidecar`。普通路径只看 `current_owner_delta -> current medical stage goal -> concrete paper/evidence/reviewer/gate delta -> ProgressDeltaReceipt / OwnerReceipt / TypedBlocker -> next current_owner_delta`。`complete_medical_paper_readiness_surface` 和后续 readiness surface 只能按 just-in-time delta 读取：当前缺哪个 surface，就补哪个 surface 或写 stable typed blocker；不得把 literature provider、study line、analysis contract、bounded board、journal layer 等 readiness inventory 重新变成“全部补齐后才允许继续写作/分析”的前置大门。OPL refs-only ledger、read-model reconcile、closeout binding、restore proof、long-soak、cleanup 和 production evidence 进入 audit sidecar；只有触发 owner / authority / execution authorization / closeout binding / irreversible mutation / publication-submission-delivery claim / human gate 时才升级为 hard gate。MDS / DeepScientist 的可取之处是流畅运行的单循环和少默认门；EvoScientist / EvoSkills 的可取之处是 background memory worker、tool selector、observation memory 和 lifecycle skill taxonomy 的旁路加速；它们都不能重新定义 MAS runtime、quality、memory 或 artifact authority。

## 已落地

| Area | 当前状态 | 当前证据入口 | 当前读法 |
| --- | --- | --- | --- |
| MAS semantic pack / generated handoff | `landed_with_evidence_tail` | `agent/`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、product-entry stage descriptor | `agent/` 是 canonical semantic pack；真实 stage attempt 与独立 reviewer/auditor receipt 仍属 evidence tail。 |
| Functional privatization boundary | `closed_functional_structure_gates_evidence_tail_remaining` | `contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`tests/test_opl_standard_pack.py`、`tests/test_opl_family_contract_adoption.py` | `classification_gap_count=0`、`functional_structure_gap_count=0`、`active_private_generic_residue_count=0`、`repo_local_wrapper_tail_count=0`；former wrapper 物理删除仍需 owner receipt / stable typed blocker、no-active-caller 与 tombstone/provenance gate。 |
| Purpose-first adapter thinning | `machine_guard_landed_evidence_tail_remaining` | `contracts/foundry_agent_series.json#/purpose_first_adapter_thinning_policy`、`tests/test_opl_standard_pack.py` | retained product/workbench/status/read-model surface 只能作为 refs-only adapter、domain handler target、minimal authority function、migration input 或 tombstone/provenance 读取；物理删除统一要求 replacement parity、no-active-caller、owner receipt / typed blocker、no-forbidden-write 与 tombstone/provenance。 |
| Default runtime owner | `opl_owned_default` | runtime default/backend contract、product-entry manifest、domain-handler export/read-model | 默认 runtime ref / substrate 是 `opl_hosted_stage_runtime`，默认 backend 是 `opl_provider_backed_stage_runtime`；历史 `mas_runtime_core` 只能按 retired provenance / migration input 读取。 |
| Runtime / lifecycle no-alias retirement | `retired_no_alias_guarded` | `contracts/runtime/legacy-active-path-tombstones.json`、`contracts/runtime/mas-runtime-surface-retirement-inventory.json`、functional boundary audit | `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、旧 lifecycle refs SQLite writer 只能作为 tombstone/provenance、OPL handoff refs 或 standard Agent purity guard 读取。 |
| Owner-route / dispatch currentness | `active_current_truth` | `docs/decisions.md`、owner-route protocol contracts、domain-handler export/dispatch behavior | `mas-owner-route-attempt-protocol.v1` 要求 reason registry、priority lattice、currentness basis、source/work-unit/truth/runtime fingerprint 和 typed closeout boundary；它只授权 OPL transport，不授权 paper closure 或 package freshness。 |
| Progress-first admission and accounting | `landed_with_live_evidence_tail` | [Progress-first Stage Outcome Runbook](../runtime/control/progress_first_stage_outcome.md)、`study_progress`、`study-state-matrix`、Progress Portal、MCP compact | 非终局 study 必须投影到唯一 owner action、owner receipt、typed blocker、human gate 或 stop-loss；platform repair 不计 paper/deliverable progress。 |
| Research evidence pack projection | `landed_not_publication_ready` | schema validation、read-model projection、Progress Portal / runtime workbench stage review、canary expectation | 只证明最低科研审计链可读、可校验、可 fail closed；真实 publication-ready 仍需 MAS owner receipt、独立 reviewer/auditor record、publication gate / human gate 和 artifact/memory/lifecycle authority receipt。 |
| StageRun Kernel foundation | `profile_projection_controlled_canary_and_live_stage_artifact_gate_landed_publication_handoff_owner_answer_binding_landed_real_evidence_tail_open` | MAS `contracts/stage_run_kernel_profile.json`、`contracts/stage_run_canary_evidence.json`、`contracts/stage_artifact_kernel_adoption.json#/stage_run_kernel_profile_binding`、`src/med_autoscience/controllers/stage_run_kernel.py`、`src/med_autoscience/controllers/study_progress_parts/stage_kernel_projection.py`、`src/med_autoscience/controllers/stage_artifact_materializer.py`、`src/med_autoscience/controllers/stage_artifact_index.py`、`src/med_autoscience/controllers/domain_owner_action_dispatch_parts/action_execution_parts/publication_handoff.py`、`tests/stage_run_kernel_cases/test_ai_reviewer_stage_run_kernel.py`、`tests/test_stage_artifact_index.py`、`tests/stage_artifact_index_cases/test_legacy_contract_residue.py`、`tests/test_stage_run_kernel_profile_contract.py`、`tests/test_domain_owner_action_dispatch_cases/publication_gate_dispatch.py`；OPL refs-only StageRun substrate / CLI / conformance 以 OPL repo live state 为准 | 已关闭 StageRun Kernel 的 MAS foundation，并补齐 terminal publication handoff callable 与 owner-answer binding：stage folder / manifest / role artifact / owner receipt / typed blocker 是当前 transition 口径；canonical stage folder 文件名已采用 `stage_manifest.json`、`owner_receipt.json`、`typed_blocker.json`、`consumed_artifact_refs.json`、`prov.json`、`current.json` 和 `current_owner_delta.json`；provider completion、file presence、`latest.json`、read-model 和 active_run_id 不能关闭 Stage。`publication_handoff_owner_gate` apply 缺 OPL execution authorization 时 fail closed，不写 MAS owner receipt / typed blocker；有授权时只写 stage-native handoff receipt / typed blocker 与 refs-only closeout binding，不写 publication eval、controller decision、paper 或 package。Co-Scientist candidate generation、grounded reflection、comparative selection、evolution / revision、meta-review 和 independent quality gate 已进入 controlled canary evidence fixture，全部是 refs-only / advisory boundary；operator summary、overclaim boundary 与 legacy runtime residue guard 已由 focused contract test 锁定为 read-model-only / fail-closed guard。2026-06-05 DM002 / DM003 live canary 已把 stage artifact current pointer 推进到 terminal publication handoff gate，并把旧 contract 文件降为 `legacy_orphan_residue` 而非 blocking orphan。真实 workspace owner receipt / typed blocker、human gate / route-back 和 real owner-chain evidence 仍开放；gate 未满足时，重复 reconcile / materialize / dispatch 补偿路径只能保留 tombstone、provenance 和 delete-gate context，不做物理退役。 |
| ARK-inspired research workflow intake | `contract_landing_in_progress` | [ARK Research Workflow Intake](../references/mainline/ark_learning_intake.md)、reviewer issue/progress ledger、display artifact manifest、source citation authority pack | 只吸收 review loop、goal anchor、issue repair validation、API-first citation、figure manifest、page adjustment 和 human-intervention UX 的 MAS-native contract shape；不引入 ARK runtime、SQLite authority、conda project model、Telegram/webapp service、代码或依赖。 |

## 当前功能/结构差距

当前没有 open functional / structural gap。`contracts/functional_privatization_audit.json` 的 `functional_followthrough_gap_summary` 和 focused tests 固定：

| Metric | 当前值 |
| --- | --- |
| `classification_gap_count` | `0` |
| `functional_structure_gap_count` | `0` |
| `remaining_functional_followthrough_gate_ids` | `[]` |
| `active_private_generic_residue_count` | `0` |
| `repo_local_wrapper_tail_count` | `0` |

下表只保留仍约束后续工作的 closed gate / guard；它们不能被重写成 active backlog，也不能被 OPL transport evidence 升级为 MAS paper closure。

新增或保留 MAS-local adapter 时，默认下一步必须是 `paper_progress_delta_or_mas_owned_typed_blocker`。platform repair、read-model currentness、provider completion、schema/descriptor conformance 和 generated surface readiness 只能作为证据尾项或 refs-only 投影；缺真实 paper / research / reviewer / human-gate delta 时返回 MAS-owned typed blocker，不写成结构 gap 已关闭或 paper progress。

| Gate / guard | 当前实际 | 后续约束 |
| --- | --- | --- |
| `generated_surface_default_owner_cutover` | OPL owns generated/default CLI/MCP/Skill/product-entry/status/workbench/domain-handler shells；MAS provides pack inputs、domain handler targets、authority refs、owner receipts、typed blockers 和 no-forbidden-write guard。 | 不把 MAS direct path、domain handler target 或 read-model projection 写回 MAS-owned generic wrapper。 |
| `standard_agent_purity_guard` | MAS repo source shape 已按 standard Agent purity 收口；former wrapper tail module ids 只作为 guarded provenance / delete-gate context 存在。 | 只有在 OPL generated/default parity、MAS owner receipt 或 stable typed blocker、no-active-caller proof 与 tombstone/provenance proof 同时成立时，才做物理删除；对同一 work unit 的补偿链退役还必须满足 `stage_native_compensation_retirement_gate` 的 live evidence / same work-unit binding。不新增 compatibility shim、alias、facade 或 wrapper。 |
| `domain_authority_refs_thinning` | storage、artifact、memory、source、owner-route、progress/status helper 只输出 refs、receipts、blockers、locators 或 diagnostic projection input。 | generic locator/index/projection shell 属于 OPL primitive；MAS retained path 只能是 domain authority refs、typed blocker、owner receipt 或必要医学 helper。 |
| `state_index_kernel_adoption` | OPL 持有 SQLite sidecar / state index / read-model kernel；MAS 只作为 primary small-file compaction candidate 和 refs-only index source。 | legacy `.ds`/runtime mirror、runtime lifecycle refs、paper work-unit receipts、owner-route/dispatch receipts、artifact locator、retention/restore 和 operator read-model 可进入 OPL sidecar index；`domain_authority_refs.sqlite` 只能是 domain authority refs adapter，不能写成 MAS generic persistence/lifecycle/queue/read-model owner。 |
| `state_contract_thinning_guard` | 稳定控制面只承认 `macro_state`、`owner_route`、`receipt_or_blocker` 和 `evidence_refs`；长 reason 和 supersession reason 只能作为 diagnostic detail。 | 新增执行判断必须进入 owner route 或 typed blocker，不得通过扩展 `StudyRuntimeReason`、publication supervisor phase 或 operator 文案绕开 owner ticket。 |
| `physical_source_morphology_guard` | legacy 名称只允许出现在 tombstone、history/provenance、旧状态输入测试、explicit archive/import fixture 或 standard Agent purity guard。 | current docs/tests/callers 不得把旧名读成 active runtime adapter、diagnostic fallback 或 compatibility alias；发现 generic queue、attempt ledger、scheduler、worker residency、runtime lifecycle owner 语义时按复活旧控制面处理。 |
| `ai_first_quality_record_boundary` | quality gate contract 和 validator 边界已落地；真实 paper-line reviewer/auditor record scaleout 属于证据 tail。 | 程序只做 validator、materializer、receipt signer 和 guard；质量结论必须追到独立 reviewer/auditor invocation、context/task record、quality receipt、route-back 或 typed blocker。 |

## 当前测试/证据差距

以下差距是 production evidence tail。它们不改变上面的结构口径，也不能声明 publication-ready、domain-ready、artifact mutation authorization 或 `current_package` 更新。

| 证据差距 | 当前状态 | 需要看到的下一层证据 |
| --- | --- | --- |
| 真实 paper-line provider apply | multi-profile guarded-apply、DM002 canary、research evidence pack read-model/schema/canary 已证明 refs-only owner-chain shape、stable blocker 和 fail-closed 审计链可见。 | 更多真实 paper line 产出 owner receipt、paper/artifact delta、independent reviewer/auditor record、human gate/resume、route decision、stop-loss、artifact/memory lifecycle receipt 或 stable typed blocker。 |
| Co-Scientist-inspired Stage / Route 重构 | 执行规格已归入 [Co-Scientist Stage / Route 重构设计与执行规格](../runtime/designs/coscientist_stage_route_restructure.md)；StageRun profile 已补充 canary 级机器边界：candidate generation、reflection、review、meta-review、ranking、proximity、evolution 只能作为 Stage 内 advisory evidence refs，不能定义硬编码 workflow、关闭 quality gate 或 promote stage。2026-06-05 `next-delta tournament`、`bounded micro-candidate generation`、`critique-as-repair-hint`、`budgeted memory`、`triggered meta-review`、`opportunistic knowledge prefetch` 已进一步固定为 progress-first 增益层，并进入 semantic pack、portfolio validator/contract、current owner ticket projection、generated stage control plane、StageRun profile 与 focused tests。 | 后续只扩面真实 owner-chain evidence，必须继续证明这些机制只帮助 route 更快选下一步、reviewer 更快发现缺口、memory 复用失败路径；不得把 admission gate、quality closure、publication readiness、artifact authority、route blocking layer、platform repair、prefetch 或 review score 计为 paper progress。真实 owner-chain evidence、paper/artifact delta、memory/artifact lifecycle receipt、human gate/resume 和 independent reviewer/auditor record 仍开放。 |
| EvoScientist / EvoSkills progress-first intake | [EvoScientist Progress-First Intake](../runtime/designs/evo_scientist_progress_first_intake.md) 已把 auxiliary background memory workers、tool selector、fire-and-forget observation memory 和 IDE / IVE / ESE lifecycle memory 折为完整目标态 sidecar execution architecture，并落地 repo callable refs-only writer、CLI observe/read-latest、`study_progress` materialize hook 和 refs-only index family。 | 机器合同、projection 和 family adoption contract 已固定 `remaining_learning_plan=false`、`mainline_waits_for_sidecar=false`、`sidecar_completion_required_for_dispatch=false`、`sidecar_completion_required_for_quality_gate=false`，并指向 `artifacts/runtime/evo_scientist_sidecar/` observation refs。后续 production scheduler / OPL worker scaleout 只能继续证明这些 sidecar fail open、refs-only、budgeted、current-owner-following；不得把 sidecar completion、tool selector score、observation memory、failed-path taxonomy 或 lifecycle skill match 写成 owner receipt、quality verdict、paper progress、memory accept/reject、artifact authority、production-ready 或 independent reviewer/auditor output。 |
| StageRun Kernel 收敛 | 顶层设计和 foundation landing 已归入 [MAS / OPL Stage Native 状态机设计](./mas-opl-stage-native-state-machine.md)。MAS 已有 StageRun profile contract、controlled canary evidence fixture、adoption binding、stage folder projection helper、`study progress` projection binding、AI reviewer synthetic canary tests、canonical stage folder path follow-through、controlled canary operator summary / overclaim boundary / legacy runtime residue guard focused contract，以及 `publication_handoff_owner_gate` callable / dispatch tests；2026-06-06 MAS apply 侧已能消费 OPL execution authorization 并写 owner-answer closeout binding / current pointer / current owner delta，随后 live workspace owner evidence 已进入 MAS typed blocker follow-up。2026-06-07 `complete_medical_paper_readiness_surface` 已从 `owner_delta_result` closeout binding 推进到 stage-native owner-answer materialization：可信授权、完整 StageRun identity binding 和 `apply` 下可把 readiness result 写回 terminal `08-publication_package_handoff` 的 `receipts/owner_receipt.json` / `receipts/typed_blocker.json`、`current.json` 与 `projection/current_owner_delta.json`，并 fail closed 拒绝缺授权、缺完整 binding、缺 MAS stage manifest 或 dry-run 写入。OPL 侧 StageRun substrate / CLI / conformance 以 OPL repo live state 为准。 | `complete_medical_paper_readiness_surface` owner surface 的 repo-side StageRun closeout materialization gap 已关闭：`literature_provider_runtime`、`study_line_selection`、`archetype_analysis_contract`、`bounded_analysis_candidate_board` 和 `stop_loss_memo` 已证明 accepted operator payload或 owner-authored payload、stale dispatch rejection、canonical surface write、readiness rebuild、owner_delta_result closeout binding、readiness `surface_key` source identity、verified materialization provenance、no-forbidden-write 边界和 stage-native owner-answer write-back。剩余 tail 是真实 paper-line owner evidence scaleout、独立 reviewer/auditor record、human gate/resume、provider SLO long soak、后续 readiness surface completion，以及补偿链退役证据。当前 readout 中 DM002 下一 surface 是 `target_journal_writing_layer`，DM003 下一 surface 是 `literature_scout`。补偿链退役只按 `stage_native_compensation_retirement_gate`：四类 live evidence 必须对同一 work unit 一致；未通过时只保留 tombstone/provenance/delete-gate context。 |
| DM002 / DM003 paused paper line | 2026-06-05 已执行 OPL queue hold / human gate pause closeout；dated 证据见 [DM002 / DM003 paper-line pause closeout 2026-06-05](../history/program/dm002_dm003_paper_line_pause_closeout_2026_06_05.md)。随后 stage-native refs-only materialization 不等于 OPL hold release、provider resume 或 queue approval。 | 恢复 provider/queue 前必须 fresh 读取 OPL current-control 并按 hold/release/human approval surface 操作；不得用全局 tick 或手写 workspace truth 恢复。Stage-native terminal handoff 只要求 publication owner receipt / typed blocker / human gate，不授权 publication-ready。 |
| owner-chain dispatch ledger scaleout | `domain_dispatch_evidence_record_payload` 与 OPL refs-only identity preflight / record / verify 已覆盖 success refs path 和 typed-blocker path。2026-06-07 MAS CLI payload transport 已补齐；同日补齐 `complete_medical_paper_readiness_surface` readiness owner callable 的 dispatch-evidence payload exporter coverage，避免新 owner surface 落地后仍因 exporter action allowlist 漏项形成 refs-only worklist 残项。Fresh worklist readout 已显示 `open_worklist_item_count=0` / `domain_dispatch_evidence_workorder_count=0`；MAS `study progress` 可投影 current executable owner action，且 live active attempt id 可能随 owner run 波动。 | 在 fresh OPL worklist 暴露可绑定 MAS current owner delta 的 workorder 后，先取得 MAS owner receipt、stage receipt、monitor freshness receipt、current AI reviewer supersession、human-gate receipt 或 stable blocker，再经新的或 superseding OPL identity preflight record/verify。`current_executable_owner_action`、active attempt 和 zero-open refs-only worklist 只是合法下一 owner / running / accounting 线索，不是 owner answer；未产出 receipt/blocker 前不允许 apply owner answer 或声明 domain-ready。 |
| publication-route memory receipts | Router/writeback refs 已进入 body-free evidence packets、paper-line result、domain-dispatch payload 和 stage expected refs。 | 多条真实 paper line 持续产生 accepted/rejected/blocked writeback receipts，并由 owner route 明确 memory accept/reject/blocker 结论。 |
| artifact lifecycle receipts | Artifact lifecycle report / retention plan 已输出 bounded refs、physical-thinning handoff 和 stable typed blocker refs-only shape。 | OPL apply receipt、真实 cleanup/restore/freshness apply receipt 或 MAS artifact mutation permission；不能由 report/plan 直接授权 cleanup 或 artifact mutation。 |
| human gate / resume | Stage replay human-gate refs 已有 MAS-owned body-free typed blocker path，`finalize_and_publication_handoff` 有 refs-only success path。 | Human approval、resume chain receipt、新 owner success receipt 或 paper closure。 |
| provider SLO long soak | Provider/runtime read-model 能投影 live attempt、blocked closeout 和 admission/running distinction。 | 长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。 |
| family transition live receipt | `study_state_matrix` 可把 MAS-owned domain transition table materialize 给 OPL generic matrix runner。 | Route/work-unit 进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。 |
| independent reviewer/auditor record scaleout | AI-first quality gate boundary 和 record validator 已落地。 | 真实 paper-line reviewer/auditor invocation、独立 context/task record、quality receipt、route-back 或 typed blocker，不得由 executor 自审替代。 |

## 下一轮 Agent prompt

- Write scope: MAS active truth owner、current status summary、owner-route/read-model
  currentness、paper-line evidence tail、publication-route memory/artifact lifecycle refs、
  human gate/resume、provider long-soak 和 docs lifecycle foldback。
- Non-goals: 不把 OPL provider proof、suite pass、queue completion、refs-only receipt、
  product-entry projection、doctor pass 或 descriptor readiness 写成 MAS paper closure、
  publication-ready、domain-ready、artifact mutation authorization、memory writeback success
  或 `current_package` 更新；不恢复旧 private runtime、compat alias、facade、wrapper 或
  fallback 文案。
- Live truth inputs: 读取 MAS `agent/` pack、contracts、owner-route/domain-handler
  exports、runtime/controller/read-model surfaces、study workspace refs、product-entry
  manifest、focused tests、OPL refs-only worklist/readouts、runtime ledgers、owner receipts
  和 typed blockers；dated closeout、receipt id 和旧 worklist 数字只作 provenance。
- Required actions:
  1. 当前 platform lane 继续收口 `complete_medical_paper_readiness_surface` 的 owner
     action、accepted provider-backed operator payload、payload-missing stable typed blocker、
     surface artifact path、readiness rebuild 和 closeout binding；`literature_provider_runtime`、
     `study_line_selection`、`archetype_analysis_contract`、`bounded_analysis_candidate_board`、`stop_loss_memo` 已进入该路径，后续按当前
     `readiness.next_action.surface_key` 扩展或 fail closed。DM002 / DM003 真实 paper-line execution
     由会话 `019e92c8-b940-7313-940b-ea892820d322` 处理，本轮不把平台 foldback 写成
     paper-line progress。
  2. 维护 Co-Scientist-inspired Stage / Route landed surface：`agent/` Stage-native
     semantic pack、machine contracts、route supervisor/read-model、focused tests 和
     runtime docs 已作为当前 Stage/Route 形态输入；progress-first 增益层已落入
     semantic pack、machine contracts、owner ticket projection 和 focused tests，且仅包含
     `next-delta tournament`、`bounded micro-candidate generation`、
     `critique-as-repair-hint`、`budgeted memory`、`triggered meta-review` 和
     `opportunistic knowledge prefetch` 六项 advisory 机制。后续只扩面真实
     owner-chain evidence，不能把 advisory ranking/proximity、platform repair、
     provider completion、prefetch、review score 或 route tournament 结果升级为
     MAS authority。EvoScientist / EvoSkills 学习点只作为 async learning sidecar、
     auxiliary helper、fail-open tool selector、observation memory 和 failed-path taxonomy
     继续折回；不得把 sidecar 缺失、失败或低置信写成 admission blocker。
  3. 对 read-model/currentness/dispatcher/lifecycle apply 类问题，先判断是否只是
     platform repair；没有同步产生 domain delta 或 stable typed blocker时，只能记录为
     platform repair，并把下一 owner 指回 MAS paper/artifact/reviewer/human gate 或
     OPL generic lifecycle apply。
  4. 对 owner-chain dispatch ledger，只处理 fresh OPL worklist 中可绑定 MAS current
     owner delta 的 workorder；已 verified 的 OPL typed-blocker receipt 不能事后升级为
     success receipt，已 verified success refs receipt 也不能写成 domain-ready 或
     production-ready。
  5. 对 publication-route memory receipt，优先取得真实 accepted/rejected/blocked
     writeback receipt 或 stable typed blocker，并证明 receipt refs 经 owner result、
     domain-dispatch payload、stage expected refs 与 body-free packet role 可复验，且不读取
     memory body、不越过 publication verdict。
  6. 对 artifact lifecycle receipt，优先从 stable typed blocker refs scaleout 前进到
     owner-authorized physical thinning、真实 workspace cleanup/restore/retention/rebuild/
     freshness apply receipt 或 artifact mutation permission，并证明 refs 进入
     reproducibility / stage expected / domain-dispatch payload，且不越过 artifact authority。
  7. 对文档治理，active/core 文档只保留 current conclusion、open gate、owner、
     machine boundary 和下一步；过程 proof、receipt id、命令流水和 dated worklist 数字继续归
     history/provenance。
- Verification commands: docs-only 维护运行 `rtk git diff --check`、
  `rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs README.md README.zh-CN.md contracts tests` 和必要的
  docs/path inventory；触及 StageRun profile / canary contract 时至少运行
  `rtk scripts/run-pytest-clean.sh tests/test_stage_run_kernel_profile_contract.py`；
  触及 broader source/contracts/runtime 时运行 `rtk scripts/verify.sh`
  及对应 focused `scripts/run-pytest-clean.sh ...`、`make test-meta` 或 OPL read-model check。
- Completion gate: 本轮输出必须归类为 domain delta、stable typed blocker 或 platform
  repair；platform repair 不写成 paper-line progress 或 production evidence closure；所有
  open paper-line、memory/artifact/lifecycle、human gate/resume、provider SLO long-soak 和
  independent reviewer/auditor record 继续留在当前测试/证据差距。
- Foldback target: durable 当前结论折回本文、核心五件套、runtime/contracts/policies 或
  owner docs；dated proof、receipt id、OPL worklist 数字、命令流水和 closeout 过程折回
  `docs/history/**`、runtime ledger、真实 workspace receipt 或提交历史。

## Stage-Native Kernel 完成后的下一层 TODO

本节只在 OPL Stage-Native Artifact Kernel 已完成后作为下一轮 active backlog 读取。完成条件包括：OPL 持有统一 stage folder contract，`stage.json`、`attempt.json`、`manifest.json`、`receipt.json`、`current.json` schema 已落地；`stage_artifact_index` 已降级为 derived projection；MAS/MAG/OMA/RCA 只提供 declarative domain pack 和最小 authority functions；controller/read-model/currentness 只做 repair、projection 和 diagnostic，不再决定 current stage。

2026-06-03 follow-through：MAS 当前已消费 OPL physical Stage Folder Kernel，并把 `stage_kernel_projection` 作为 Progress Portal / Workbench primary progress 的派生输入。当前完成口径提升为：physical stage folder 只有在 `current.json` 指向 latest attempt、manifest / owner receipt / domain decision receipt 成立、consumability gate 通过、lineage events / graph 可定位、retention / restore refs 覆盖时，才可被投影为 current artifact progress。`stage_artifact_index` 继续是 rebuildable diagnostic projection；缺 semantic receipt、stale current pointer、缺 retention / restore 或缺 lineage 时必须 fail closed，并产生下一 owner / blocker，而不是退回 controller/read-model currentness。

2026-06-04 operating-layer follow-through：下一层 repo-side operating layer 已从 isolated lanes 吸收到 main。`stage_kernel_projection` 现在同时投影 refs-only State Index、current pointer promotion audit、lineage / retention drilldown；Progress Portal / Workbench 首屏消费这些字段，并可投影 MAS/MAG/OMA/RCA cross-domain soak summary。`mas_stage_semantic_receipts` 提供 body-free semantic receipt validator，覆盖 source readiness、reviewer quality、publication gate、artifact package authority、memory accept / reject、typed blocker 与 medical owner receipt。上述 surface 都是只读 projection / validator / audit helper：不写 `current.json`、MAS study truth、canonical paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、artifact body、memory body 或 submission package；也不声明 publication ready、submission ready、quality ready 或 artifact mutation authorization。

完成上述重构后，剩余风险不再是 controller/read-model 阻塞 MAS 推进，而是 Stage Kernel 自身是否能长期承担 artifact operating layer。下一轮 TODO 按以下顺序处理：

1. `manifest_receipt_semantic_validation`：repo-side validator 已落地为 `src/med_autoscience/controllers/mas_stage_semantic_receipts.py`，只校验 `receipt_ref`、schema refs、capability refs 和 domain semantic refs；格式合法但语义缺失时 fail closed 或形成 typed blocker。后续证据尾项是更多真实 paper-line receipt 进入该 shape。
2. `current_pointer_promotion_model`：repo-side audit helper 已落地为 `src/med_autoscience/controllers/opl_stage_promotion_runtime.py`，显式检查 `attempt output -> manifest valid -> receipt accepted -> current pointer promoted -> projection rebuilt`，并覆盖 partial commit、rollback、stale pointer、orphan output 和 historical pointer tombstone。它只读 audit，不提升 projection 为 current pointer 写权限。
3. `legacy_stage_taxonomy_migration`：repo-side read-model 已落地到 `stage_artifact_index`。顶层 `legacy_taxonomy_migration` 继续持有旧 MAS `scout/idea/baseline/experiment/analysis-campaign/write/review/finalize` 到 paper/study artifact stages 的 migration manifest / role mapping；每个 stage state 现在额外投影 `legacy_taxonomy_migration_read_model`，包含 `migration_status`、`backfilled_current_pointer`、`tombstone_or_provenance_*`、`workbench_dual_truth_forbidden` 和 fail-closed `next_owner_action`。缺 current pointer backfill 或 tombstone/provenance 时只投影下一 owner/action，不把 legacy route 显示成 current truth；Workbench 仍只能显示 `paper_study_stage_pack` 单一 current truth。开放证据尾项是真实 workspace / Workbench soak 继续证明这些字段被消费且不声明 paper progress。
4. `lineage_graph_unification`：repo-side drilldown 已落地为 `src/med_autoscience/controllers/opl_stage_lineage_retention.py`，按 `stage_attempt_manifest_receipt_current_pointer` event model 汇总 lineage events、lineage graph、manifest、receipt、current pointer、restore proof 和 retention policy。UI / controller / read-model 只能消费该 refs-only family，不另造 provenance。
5. `artifact_consumability_gate`：物理文件和 content hash 只证明 artifact 存在且未变；能否进入下一 owner 还必须检查 input role、source/current truth、receipt authority、lineage、retention/restore policy 和 domain validation。
6. `workbench_information_hierarchy`：Progress Portal / Workbench 已把 `stage_operating_layer` 固定为 primary progress，并把 state index、promotion audit、lineage / retention、cross-domain soak 与 provider liveness 分层展示；repair/currentness/telemetry/evidence-tail 仍是 secondary diagnostics，不能被 UI 写成 progress 或 readiness。
7. `retention_restore_gc_protocol`：repo-side retention gate 已 fail closed：projection 永远不授权 cleanup，缺 restore contract、receipt 指向不可恢复 artifact 或 current pointer 指向 orphan output 都进入 blocker / drilldown。真实 cleanup / restore apply 仍必须等待 MAS artifact authority 或 OPL owner-authorized receipt。
8. `cross_domain_soak`：Workbench read-only projection 已覆盖 MAS/MAG/OMA/RCA lane shape、running、no-live-run、blocked 和 stale-controller-with-artifact-delta 分类。通过真实 domain lane 重建 DB、App/workbench、artifact gallery、stage_progress_log 和 next owner 仍是 evidence tail，不由 fixture 或 repo tests 声明 domain readiness。

下一层完成口径：OPL 成为 artifact operating layer；Stage Kernel 负责事实重建，Domain Authority 负责裁决，Policy Engine 负责权限，Workbench 只读展示派生视图。任何 index、controller、read-model 或 App surface 重新获得第一真相权，都按架构回归处理。

## 验证与完成门

Docs-only 维护：

- `rtk git diff --check`
- `rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs README.md README.zh-CN.md contracts tests`
- 必要的 docs/path inventory 检查。

触及 source/contracts/runtime 时才追加：

- `rtk scripts/verify.sh`
- 按触及面追加 focused `scripts/run-pytest-clean.sh ...`、`make test-meta` 或对应 owner-route / domain-handler / product-entry smoke。
- StageRun profile / canary contract 维护至少运行 `rtk scripts/run-pytest-clean.sh tests/test_stage_run_kernel_profile_contract.py`。
- 消费 OPL refs 时追加 OPL 侧 read-model check：`rtk opl agents interfaces --repo-dir /Users/gaofeng/workspace/med-autoscience --json`、`rtk opl framework readiness --family-defaults --json`、`rtk opl runtime app-operator-drilldown --json`。

Completion gate:

- 本轮输出能归类为 domain delta / stable typed blocker / platform repair；platform repair 没有被写成 paper-line progress 或 production evidence tail closure。
- 仍 open 的真实 paper-line、memory/artifact/lifecycle、human gate/resume、provider SLO long-soak 和独立 reviewer/auditor record 留在“当前测试/证据差距”。
- 新增或修改的 owner receipt / typed blocker / evidence packet 有 live refs、focused verification 和 no-forbidden-write proof；OPL transport/read-model 证据没有被升级为 MAS domain verdict。
- worktree lane 已吸收回 `main` 或明确标记为近期写入/有未提交改动而保留；最终在 `main` checkout 完成最小充分验证。

## 历史索引

| 需要追溯的内容 | 当前入口 |
| --- | --- |
| 当前状态摘要 | [当前状态](../status.md) |
| 架构与 owner 边界 | [架构概览](../architecture.md) |
| 不可变约束 | [不可变约束](../invariants.md) |
| 日期决策日志 | [关键决策记录](../decisions.md) |
| north-star 目标态 | [MAS 理想目标态](../references/positioning/mas_ideal_state.md) |
| 下一 `/goal` 执行规格 | [Co-Scientist Stage / Route 重构设计与执行规格](../runtime/designs/coscientist_stage_route_restructure.md) |
| 当前内容线索引 | [MAS 当前开发线路](./current-development-lines.md) |
| 文档生命周期治理 | [MAS 文档组合治理](../docs_portfolio_consolidation.md) |
| docs lifecycle coverage | [MAS Docs Portfolio Coverage Ledger](../history/docs-portfolio-coverage-ledger/README.md) 与 [MAS broader docs portfolio SSOT closeout 2026-06-07](../history/program/mas_broader_docs_portfolio_ssot_closeout_2026_06_07.md) |
| 2026-05 标准 Agent 文档过程归档 | [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md) |
| 历史完成台账 | [Plan Completion Ledger](../history/program/plan_completion_ledger.md) |

## Active / History Foldback

| 内容 | Foldback target | 规则 |
| --- | --- | --- |
| dated closeout、attempt / receipt id、命令流水、旧 phase checklist、OPL worklist 数字 | `docs/history/program/` 或对应 `docs/history/<area>/` | 只保留 provenance；不得作为 current truth 或 active backlog。 |
| 已被 current owner surface 替代的旧 runtime/workbench/scheduler/alias 文案 | `docs/history/**` tombstone / provenance，或 machine-readable tombstone refs | active docs 只写当前 owner、删除门和 standard Agent purity guard。 |
| 已关闭功能/结构 gap | 本文 `已落地`，必要时加 compact tombstone pointer | 不保留旧 checklist chronology。 |
| 仍缺 live evidence 的能力 | 本文 `当前测试/证据差距` | 不回写成结构未完成，也不写成 production/domain ready。 |

## 当前不能写成

- 不能把 OPL provider proof、suite pass、queue completion、refs-only ledger receipt 或 provider completion 写成 MAS paper closure、publication-ready、domain-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 MAS production acceptance receipt 写成具体论文线 publication-ready；它只承认 structural / physical conformance 与 production-like receipt chain 的边界。
- 不能把 `mas_owner_receipt_present`、stable blocker、body-free evidence packet 或 OPL workorder preflight 写成 workspace mutation、artifact authority 放行、memory writeback success 或 paper closure。
- 不能把 MAS 已经没有任何私有程序面写成绝对清零；准确口径是私有面已收敛为 declarative pack / generated surface handoff、domain authority refs、minimal authority function 或 explicit tombstone/provenance refs。
- 不能把旧 `runtime_transport/`、turn runner、worker lease、runtime lifecycle SQLite、`lifecycle_refs_adapter.py`、MDS/DeepScientist、Hermes、local scheduler、workspace wrapper、`mas_runtime_core`、compat alias、fallback 或只保护旧路径的聚合测试写成 MAS 默认 active runtime owner、active adapter、diagnostic fallback、compat alias 或 retained caller。
- 不能把 product-entry / workbench / owner-route / progress projection shell 写成长期 MAS generic workbench、queue、attempt ledger、retry/dead-letter、worker residency、terminal transport 或 lifecycle owner；它们当前只能输出 domain projection refs、owner receipt、typed blocker、authority refs 或 diagnostic refs。
- 不能把 `study_state_matrix` 或 OPL `family-transition-runner` matrix pass 写成 paper closure、publication quality、artifact authority、submission readiness 或 domain ready。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可由 repo tests、descriptor ready 或 conformance 替代。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出。
- 不能把 executor agent 自审、同一上下文内的执行后复核、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 progress-first Co-Scientist 增益层写成 admission gate、quality closure、publication readiness、artifact authority、route blocking layer、paper progress、production-ready 或真实 paper-line closeout；`next-delta tournament`、bounded candidates、repair hints、budgeted memory、triggered meta-review 和 opportunistic prefetch 都只服务推进选择、评审定位和失败路径复用。
- 不能把 EvoScientist / EvoSkills sidecar 写成 MAS 默认 runtime owner、executor backend、tool authority、memory authority、quality owner、admission gate、route blocking layer、paper progress、owner receipt、quality verdict、publication-ready、artifact authority、production-ready 或 independent reviewer/auditor output；async learning、tool selector、observation memory、failed-path taxonomy 和 lifecycle skill match 都只能作为 fail-open progress accelerator / audit sidecar。
- 不能把 dated specs、dated closeout、follow-through 记录、receipt id、OPL worklist 数字或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
