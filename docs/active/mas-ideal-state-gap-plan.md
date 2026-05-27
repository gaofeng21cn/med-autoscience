# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、domain-handler receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-28`

## 文档读法

- 本文是 MAS 当前唯一 single Active Truth plan：维护当前唯一真相、目标态、已落地状态、结构边界、测试/证据差距、当前源码形态收口范围和历史索引。
- MAS 的 north-star 目标态读 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)。本文只保留面向执行的差距和顺序。
- [MAS 当前开发线路](./current-development-lines.md) 只作为内容线索引；若它与本文冲突，以本文为准，并把仍有效内容折回本文、核心 canonical docs 或 history/tombstone。
- dated closeout、receipt id、命令流水、旧 phase checklist、长 follow-through 清单和 proof 过程归档到 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)、[Plan Completion Ledger](../history/program/plan_completion_ledger.md) 或对应 `docs/history/**`。active 文档只保留当前结论和仍决定下一步的门槛。
- 差距按目标态判断。当前实现可运行只能作为迁移输入、风险和证据来源，不能反向定义 MAS 长期架构。

## 当前唯一真相

| 主题 | 当前结论 |
| --- | --- |
| MAS 身份 | MAS 是医学研究 domain agent，也是 OPL-compatible package。direct MAS app skill path 与 OPL-hosted path 必须回到同一套 MAS-owned stage、controller、durable truth、quality verdict、artifact authority、memory decision、owner receipt 和 typed blocker。 |
| 默认运行 | hosted autonomous runtime 默认由 OPL/Temporal 承担；OPL 持有 stage attempt、queue、wakeup、retry/dead-letter、resume、human-gate transport、provider query、worker residency 和 operator projection。`Codex CLI` 是 stage 内第一公民 executor；Codex App 只承担 direct entry / 人机操作面，不作为任务启动后的外围持续 driver。 |
| MAS authority | MAS 持有 study truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body 与 accept/reject/blocker decision、artifact/package authority、source readiness、owner receipt、safe action refs 和 typed blocker。 |
| OPL authority | OPL 持有通用 scheduler、queue、attempt ledger、generic transition runner、lifecycle/index、memory/artifact locator、restore/retention shell、observability、repair projection、generated CLI/MCP/Skill/product-entry/domain-handler/status/workbench wrapper 和 App/workbench shell。 |
| MDS / DeepScientist | 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。它不回到 MAS 默认 backend、quality owner、artifact authority 或 runtime owner。 |
| 当前机器面 | `agent/` 是 canonical medical research semantic pack；`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是主要 machine-readable truth。 |

## 目标态

MAS 的目标态是：

`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal medical authority functions`

这表示 MAS 只长期保留医学研究语义、stage pack、quality gate、publication/artifact/memory/source authority、domain transition、owner receipt 和必要医学 helper。通用 runtime platform、queue、attempt ledger、state-machine runner、memory/artifact locator、lifecycle/restore/retention、observability、workbench 和 generated entry/status wrapper 上收到 OPL Framework / shared family layer。

AI-first quality gate 必须由独立 reviewer/auditor agent invocation 关闭。程序函数只做 schema/provenance/authority refs 校验、持久化、owner receipt 签发、typed blocker、safe action refs 和 no-forbidden-write guard；脚本、regex、scorecard、file presence、queue completion 或 executor 自审不能替代医学质量判断。

## 当前完成进度

| Area | 当前进度 | 当前读法 |
| --- | --- | --- |
| Standard OPL Agent source shape | `standard_agent_source_shape_landed` | `agent/` pack、stage/action/memory/artifact contracts、generated surface handoff 与 production acceptance 已成为 MAS 当前机器面；`contracts/functional_privatization_audit.json` 与 focused tests 将 `functional_structure_gap_count` 固定为 `0`。product/status/workbench/domain-handler/controller/progress 相关 repo-local 代码只按 MAS domain handler target、authority function、owner receipt / typed blocker producer 或 refs-only projection input 读取，不再作为 active generic wrapper tail。 |
| Runtime owner split | `opl_owned_default` | 默认 hosted autonomous runtime 归 OPL/Temporal；MAS 保留 study truth、quality gate、artifact authority、owner receipt 和 typed blocker。 |
| Legacy runtime no-resurrection | `guarded` | `runtime_transport`、`mas_runtime_core*`、turn runner、worker lease 和旧 lifecycle writer 只能按 tombstone/provenance 或 OPL handoff refs 读取。 |
| DM002 anti-stall control loop | `next_owner_resolution_landed_opl_admission_pending` | `always resolve to next owner` 已进入 MAS read-model / owner-route / dispatch 当前口径：非终局状态必须投影为唯一 owner action、owner receipt、typed blocker、human gate 或 stop-loss；fresh DM002 AI reviewer currentness 已消费，当前剩余 blocker 是 OPL stage-attempt admission / owner-route scaleout，而不是 stale reviewer、stale liveness 或 external supervisor handoff。Product-entry manifest/read-model refresh 现在用轻量 mainline projection 与 import-light `product_entry` 顶层 discovery 支撑 OPL bounded live refresh，warm OPL managed env 下 5s live manifest 可 resolved 且不使用 projection cache；该路径只做 projection hygiene，不能成为 domain verdict、paper closure 或 artifact/package authority；首次 clean-runner uv project venv 建立和依赖下载仍归 OPL managed environment / App startup-maintenance 证据尾项。 |
| Domain owner evidence shape | `shape_landed_dm002_success_refs_observed_scaleout_pending` | guarded apply、owner-route、aftercare、body-free evidence packet、typed blocker shape、逐 paper-line owner-chain result 与 OPL owner-payload group return shapes 已可供 OPL refs-only ledger 消费；fresh DM002 guarded-apply proof 读到 MAS owner receipt success path、owner-chain refs、artifact movement refs、publication-route memory final proof 和 no-forbidden-write proof。该 proof 只是 body-free owner-chain evidence，不声明 paper closure、publication-ready、artifact mutation authorization 或 `current_package` 更新；更多真实 paper-line owner receipt / reviewer record / artifact movement 仍需扩面。 |
| Docs lifecycle | `single_active_truth_owner` | 本文持有当前进度、结构边界、证据 tail 和 foldback；dated closeout、命令流水和已完成清理 prompt 继续留在 history/provenance。 |

## 已落地

| Area | 当前状态 | 当前证据入口 | 当前读法 |
| --- | --- | --- | --- |
| MAS semantic pack / generated handoff | `landed_with_evidence_tail` | `agent/`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、product-entry stage descriptor | `agent/` 是 canonical semantic pack；stage descriptor 已投影 `codex_cli_launch_packet`、runtime event refs、quality refs、forbidden authority 和 `stage_contract.user_stage_log_contract`。用户阶段日志合同只要求 MAS typed closeout 输出用户可读领域语义或 typed blocker，供 OPL 投影 `stage_progress_log.user_stage_log`；它不授权 OPL 推断 paper/body 语义、写 MAS truth 或关闭 publication/artifact/export verdict。真实 stage attempt 与独立 reviewer/auditor receipt 仍属 evidence tail。 |
| Functional privatization boundary | `closed_functional_structure_gates_evidence_tail_remaining` | `contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`docs/status.md`、`tests/test_opl_standard_pack.py`、`tests/test_opl_family_contract_adoption.py` | `classification_gap_count=0`、`functional_structure_gap_count=0`、`active_private_generic_residue_count=0`、`repo_local_wrapper_tail_count=0`。MAS retained surfaces 只按 declarative pack、domain authority refs、minimal authority function、domain handler target、necessary medical helper 或 refs-only projection input 读取；former wrapper 物理删除仍需 owner receipt / stable typed blocker、no-active-caller 与 tombstone/provenance gate，不作为当前功能/结构 gap。 |
| Default runtime owner | `opl_owned_default` | runtime default/backend contract、product-entry manifest、domain-handler export/read-model | 默认 runtime ref / substrate 是 `opl_hosted_stage_runtime`，默认 backend 是 `opl_provider_backed_stage_runtime`，engine id 是 `opl-hosted-stage-runtime`；`default_autonomous_runtime` 默认启用，provider 为 `temporal`，wakeup/retry/resume owner 为 OPL。历史 `mas_runtime_core` 只能按 retired provenance / migration input 读取。 |
| Runtime / lifecycle no-alias retirement | `retired_no_alias_guarded` | `contracts/runtime/legacy-active-path-tombstones.json`、`contracts/runtime/mas-runtime-surface-retirement-inventory.json`、functional boundary audit | `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、`lifecycle_refs_adapter.py` 和旧 lifecycle refs SQLite writer 只能作为 tombstone/provenance、OPL handoff refs 或 standard Agent purity guard 读取。 |
| Runtime storage refs-only adapter boundary | `live_report_boundary_payload_landed` | `runtime_storage_maintenance` live reports、`contracts/functional_privatization_audit.json`、focused runtime storage tests | workspace audit、study-bound maintenance 与 orphan quest maintenance 已输出 `mas_runtime_storage_refs_only_adapter_boundary`，只携带 storage refs、cleanup/restore receipt refs、size refs 和 typed blocker；不声明 generic cleanup policy、restore readiness、publication readiness、paper closure、artifact mutation authorization 或 `current_package` 更新。 |
| Owner-route / dispatch currentness | `active_current_truth` | `docs/decisions.md` 2026-05-22/23 decisions、owner-route protocol contracts、domain-handler export/dispatch behavior | `mas-owner-route-attempt-protocol.v1` 要求 reason registry、priority lattice、currentness basis、source/work-unit/truth/runtime fingerprint 和 typed closeout boundary。它只授权 OPL transport，不授权 paper closure 或 package freshness。 |
| Always-resolve anti-stall loop | `landed_opl_admission_and_scaleout_pending` | `docs/decisions.md` 2026-05-27 decision、`docs/status.md`、runtime control/projection docs、owner-route / dispatch read-model behavior、product-entry import-light focused test | 非终局 study 已按 `owner_resolution_state` 投影到 `running`、`ready_for_owner_action`、`waiting_human`、`blocked_with_typed_owner`、`terminal_success` 或 `terminal_stop_loss`。DM002 的 stale AI reviewer currentness、stale external supervisor lifecycle 和 stale liveness/package-ready projection 已被收敛到 current write route-back；当前 blocker 是 `opl_stage_attempt_admission_required` / `next_owner=one-person-lab`。Manifest/read-model bounded refresh 通过轻量 product-entry mainline projection 与 import-light manifest discovery 减少 OPL/App currentness drift，不能写 MAS truth 或提升为 publication/artifact/package verdict。 |
| DM002 AI reviewer currentness | `reviewer_record_consumed_opl_admission_pending` | independent AI reviewer payload `/tmp/mas-dm002-ai-reviewer-record-20260526T120300Z.json`、`artifacts/publication_eval/ai_reviewer_responses/20260526T120300Z_publication_eval_record.json`、`artifacts/publication_eval/latest.json`、fresh owner-route reconcile | Fresh record `20260526T120300Z` 由独立 reviewer invocation 产生，并通过 MAS repo checkout owner CLI 物化。`publication_eval/latest.json` 保留完整 `reviewer_operating_system` trace，current manuscript digest 为 `sha256:60123b5035a8453589fe03bce1d2317f8867ae316b569c4364a5aa5ef94d6e61`，analysis harmonization currentness refs 已满足。AI reviewer verdict 仍为 `blocked`，primary claim supported，human review readiness blocked；owner route 已消费该 receipt 并 route back 到 write lane `dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass`。Fresh live projection 已清掉 stale `external_supervisor` repair lifecycle，observe 下剩余 blocker 是 `opl_stage_attempt_admission_required`、`next_owner=one-person-lab`。这关闭 stale reviewer currentness 和 stale supervisor lifecycle projection，不关闭 paper closure、publication-ready、artifact mutation authorization、OPL stage execution 或 `current_package` 更新。 |
| Domain dispatch / stage evidence payload | `domain_dispatch_closed_review_stage_success_refs_verified` | `domain_dispatch_evidence_record_payload`、`medautosci domain-handler dispatch-evidence-payload`、`medautosci domain-handler stage-evidence-payload`、focused body-free evidence refs tests、domain-handler owner-route/export dispatch tests、live guarded-apply domain-handler receipt、fresh OPL evidence-worklist、fresh multi-profile `medautosci real-paper-autonomy-guarded-apply-proof`、`mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json` | MAS payload 现在显式输出 `domain_owner_receipt_refs`、`owner_chain_refs`、`stage_expected_receipt_refs`、`stage_monitor_freshness_refs`、`stage_runtime_event_refs`、`no_regression_evidence_refs`、`typed_blocker_refs`、success / typed-blocker payload path、required return shapes 和 OPL action payload；默认无 owner receipt 时 fail-closed 生成 MAS-owned typed blocker，有真实 owner receipt refs 时进入 refs-only success payload，且不声明 domain ready、publication ready、artifact mutation authorization 或 `current_package` 更新。typed blocker ref 与 ledger hint 保留 stage/source identity token，避免同类 stage attempt 在 refs-only ledger 中碰撞；stage evidence handoff 会把真实 paper-line owner receipt / progress / artifact / human gate / stable blocker / no-forbidden-write refs 映射为 `stage_expected_receipt_refs` 与 `stage_monitor_freshness_refs`，供 OPL stage evidence record / verify 消费，不声明 domain ready。guarded-apply canary closeout 还会输出 `stage_expected_receipt_payload_summary`，只聚合真实 payload 已支撑的 `finalize_and_publication_handoff` success refs path 或 typed-blocker path，供 OPL App/operator 的 `domain_owner_payload_summary_refs` 读取和路由；它不合成其他未观测 stage，也不声明 paper、publication、artifact 或 production ready。`dispatch-evidence-payload` 保持 import-light，不要求 PDF 依赖进入 domain-dispatch owner surface，并能在 publication-gate route supersession、`runtime_recovery_not_authorized` 或 `runtime_recovery_retry_budget_exhausted` 挡住 default-executor dispatch 时返回 domain-owned typed blocker payload。`stage-evidence-payload` 消费 OPL `stage_evidence_workorder_packet`，为 `review_and_quality_gate` 输出 stage-production-evidence success payload 或 `real-paper-line-owner-receipt-or-monitor-freshness-pending` typed-blocker payload；它不写 paper / memory / artifact body，不生成 MAS owner receipt，不声明 stage ready。provider-hosted guarded-apply 已修复跨 profile `002-*` / `003-*` identity collision：`DM002` / `DM003` shorthand 只映射到 DM-CVD canonical study identity，full canonical ids 精确匹配。fresh multi-profile proof 观察到 4 条 success refs path 与 5 条 typed-blocker path。OPL refs-only ledger 已验证过 MAS default-executor dispatch 的 success refs path、retry-budget terminal blocker typed-blocker refs path 和 publication-gate route supersession typed-blocker refs path；本轮另 record/verify `review_and_quality_gate` stage-production-evidence success payload，receipt ref 为 `opl://external-evidence/medautoscience/stage_production_evidence:medautoscience:review_and_quality_gate`，`verified_receipt_count=1`，fresh OPL worklist 中该 stage open count 读为 `0`。后续真实 owner receipt 必须通过新的或 superseding owner-payload route 消费，已关闭 typed-blocker receipt 不能事后升级为 success receipt，已 verified 的 success refs receipt也不能写成 domain-ready 或 production-ready。 |
| Body-free evidence packet shape | `landed_multiprofile_success_and_blocker_refs_observed_scaleout_pending` | `paper_line_guarded_apply_evidence`、`body_free_evidence_packets`、`paper_line_owner_chain_results`、`paper_line_domain_dispatch_evidence_record_payloads`、`paper_line_owner_payload_summary`、`stage_expected_receipt_payload_summary`、production acceptance contract、fresh multi-profile guarded-apply proof、default multiline snapshot、DM002 single-line snapshot | progress delta、AI reviewer/gate、artifact movement、human gate/resume、stable typed blocker 和 no-forbidden-write proof 已有 refs-only packet shape；canary closeout 现在逐 study identity 绑定 owner receipt / stable blocker / progress / artifact / human-gate refs，并为每条 paper line 输出 OPL owner-payload workorder 可消费的 success refs path 或 typed-blocker path，同时按真实 payload 汇总 `finalize_and_publication_handoff` 的 stage expected receipt / monitor freshness / typed-blocker guidance。fresh multi-profile proof 的 `paper_line_owner_payload_summary` 为 `paper_line_count=9`、`success_payload_count=4`、`typed_blocker_payload_count=5`，`body_included=false` 且 readiness claims 全为 false。真实关闭仍需要 MAS owner chain 持续产出独立 reviewer/auditor record、human gate/resume、artifact/memory lifecycle receipt 或 stable typed blocker。 |
| Read-only transition materialization | `landed_with_live_receipt_tail` | `study_state_matrix` action、action catalog、product-entry / CLI / Skill / descriptor-only MCP projection | MAS 暴露 domain transition spec/cases；OPL generic runner 消费 spec。matrix pass 不等于 publication quality、artifact authority、submission readiness 或 paper closure。 |
| Legacy aliases | `direct_retired` | focused fail-closed tests、status / tombstone docs | T2E legacy display alias、submission-target `publication_profile` 输入 alias、旧 human-gate output alias 都不再作为当前输入 fallback；旧 workspace 走迁移、fail-closed 或 tombstone/provenance。 |
| Current operator naming hygiene | `current_owner_text_thinned` | `study_progress` parked operator projection、auto runtime parking、manual-hold intake、autonomy state surface focused tests | 当前用户可见停驻、manual hold、runtime parking 和 OPL handoff 文案只把 MAS / OPL runtime owner 写成当前执行主体；MDS / DeepScientist 只保留在 provenance、fixture、explicit archive import、backend audit、upstream learning、parity oracle 或旧输入测试语境。这不关闭真实 paper-line owner receipt、memory/artifact/lifecycle receipt 或 long-soak evidence tail。 |
| Progress Portal read-model materializer boundary | `domain_owned_read_model_materializer_no_active_workspace_helper` | `progress_portal_parts/workspace_carrier.py`、`mas_progress_portal_read_model_materializer_boundary`、focused Progress Portal materialization tests、active caller empty proof | Progress Portal 顶层只保留 MAS-owned payload / refs projection API；workspace 静态 HTML、study page 和 hosted package 物化保留为 read-model evidence。`medautosci workspace progress-portal`、`--serve`、`ops/mas/bin/start-web` 和本地 action endpoint 不再作为 active/default caller；保留模块不声明 workspace workbench owner、local HTTP service owner 或 runtime control owner。 |

## 当前功能/结构差距

当前没有 open functional / structural gap。`contracts/functional_privatization_audit.json` 的 `functional_followthrough_gap_summary` 和 focused tests 固定 `classification_gap_count=0`、`functional_structure_gap_count=0`、`remaining_functional_followthrough_gate_ids=[]`，剩余项归类为 `live_provider_paper_line_evidence_gates`。

下表只保留仍约束后续工作的 closed gate / guard；它们不能被重写成 active backlog，也不能被 OPL transport evidence 升级为 MAS paper closure。

| Gate / guard | 当前实际 | 后续约束 |
| --- | --- | --- |
| `generated_surface_default_owner_cutover` | OPL owns generated/default CLI/MCP/Skill/product-entry/status/workbench/domain-handler shells；MAS provides pack inputs、domain handler targets、authority refs、owner receipts、typed blockers 和 no-forbidden-write guard。 | 不把 MAS direct path、domain handler target 或 read-model projection 写回 MAS-owned generic wrapper。 |
| `standard_agent_purity_guard` | MAS repo source shape 已按 standard Agent purity 收口；former wrapper tail module ids 只作为 guarded provenance / delete-gate context 存在，`physical_delete_authorized=false`。 | 只有在 OPL generated/default parity、MAS owner receipt 或 stable typed blocker、no-active-caller proof 与 tombstone/provenance proof 同时成立时，才做物理删除；不新增 compatibility shim、alias、facade 或 wrapper。 |
| `domain_authority_refs_thinning` | storage、artifact、memory、source、owner-route、progress/status helper 只输出 refs、receipts、blockers、locators 或 diagnostic projection input。 | generic locator/index/projection shell 属于 OPL primitive；MAS retained path 只能是 domain authority refs、typed blocker、owner receipt 或必要医学 helper。 |
| `physical_source_morphology_guard` | legacy 名称只允许出现在 tombstone、history/provenance、旧状态输入降级测试、explicit archive/import fixture 或 standard Agent purity guard。 | current docs/tests/callers 不得把旧名读成 active runtime adapter、diagnostic fallback 或 compatibility alias；发现 generic queue、attempt ledger、scheduler、worker residency、runtime lifecycle owner 语义时按复活旧控制面处理，并删除污染 caller。 |
| `ai_first_quality_record_boundary` | quality gate contract 和 validator 边界已落地；真实 paper-line reviewer/auditor record scaleout 属于证据 tail。 | 程序只做 validator、materializer、receipt signer 和 guard；质量结论必须追到独立 reviewer/auditor invocation、context/task record、quality receipt、route-back 或 typed blocker。 |
| `no_resurrection_guard` | 防复活测试已收薄为 current contract、standard Agent purity guard、fail-closed、tombstone semantics、owner receipt 或 typed blocker；普通 dispatch/materializer 测试不再以 retired runtime action 为主角。 | 不新增 compatibility alias、normalizer、fallback 或只保护旧路径的聚合测试；发现 retired callable/action 回到 current registry 或 dispatcher 时 fail closed，并优先删除旧路径保护测试。 |

## 当前测试/证据差距

以下差距是 production evidence tail。它们不改变上面的结构口径，也不能声明 publication-ready、domain-ready、artifact mutation authorization 或 `current_package` 更新。

| 证据差距 | 需要看到的证据 |
| --- | --- |
| 真实 paper-line provider apply | multi-profile guarded-apply proof 已 fresh 观察到 9 条 paper line 的 MAS owner-chain return shape，其中 4 条为 owner receipt success path、5 条为 stable typed blocker path，并以 `contracts/production_acceptance/mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json` 固化为 body-free machine snapshot；default multiline snapshot 与 DM002 单线 snapshot 继续保留补充证据。上述 proof 不声明 paper closure、publication-ready、artifact mutation authorization 或 `current_package` 更新。继续补齐独立 reviewer/auditor record、human gate/resume、route decision、stop-loss、artifact/memory lifecycle receipt 或 stable typed blocker。 |
| owner-chain dispatch ledger scaleout | `domain_dispatch_evidence_record_payload` 已具备 OPL owner-payload group 所需 return shapes 与 refs-only payload path；guarded-apply canary closeout 也已输出逐 paper-line `paper_line_domain_dispatch_evidence_record_payloads`、`paper_line_owner_payload_summary` 和 `stage_expected_receipt_payload_summary`，让同一轮多条真实论文线可以分别选择 success refs path 或 typed-blocker path，并让 OPL 按 stage 记录 expected receipt / monitor freshness refs 或 typed blocker refs。真实 MAS owner receipt 进入 success refs path，stable blocker 进入 typed-blocker path，二者都保留 no-forbidden-write proof 且不声明 domain ready。OPL ledger 已验证过 MAS success refs path、retry-budget terminal blocker path 和 publication-gate route supersession typed-blocker path；本轮新增 `stage-evidence-payload` 后，MAS 也能把 `review_and_quality_gate` stage workorder 转为 refs-only success / typed-blocker payload，且本轮 success refs 已被 OPL record/verify，fresh OPL worklist 中该 stage open count 为 `0`。当前 live worklist 数字仍必须 fresh 读取。仍需把更多真实 owner-route / guarded-apply / aftercare / default-executor / stage-level handoff 做成同轮闭环：先取得 MAS owner receipt、stage receipt、monitor freshness receipt、current AI reviewer supersession 或 stable blocker，再经新的或 superseding OPL identity preflight record/verify；已关闭 typed-blocker receipt 不能事后升级为 success receipt，已 verified 的 success refs receipt也不能写成 domain-ready 或 production-ready。 |
| publication-route memory receipts | 多条真实 paper line 产生 accepted/rejected/blocked memory writeback receipts，并可被后续 stage 以 small-set refs 检索。 |
| artifact lifecycle receipts | 真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded receipt、rebuild/freshness proof 或 typed blocker。 |
| human gate / resume | approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。 |
| provider SLO long soak | 长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。 |
| family transition live receipt | `study_state_matrix` / OPL generic matrix runner 的 route/work-unit 能进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。 |

## 下一轮 Agent prompt

Objective:

- 推进 MAS 真实 paper-line / workspace production-evidence tranche。每轮先读取 live repo truth 和真实 workspace refs，再只关闭仍 open 的 evidence tail；已闭合内容折回本文、核心五件套或 machine-readable contracts。

Write scope:

- `docs/active/mas-ideal-state-gap-plan.md`、`docs/status.md`、核心五件套、`agent/` pack、MAS contracts、owner-route / domain-handler / product-entry / progress projection source、focused tests，以及只影响 MAS owner receipt / typed blocker / body-free evidence path 的 runtime/controller surfaces。

Live truth inputs:

- `AGENTS.md`、`TASTE.md`、核心五件套、本文、`docs/docs_portfolio_consolidation.md`、MAS north-star 目标态和当前开发线路。
- `contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`。
- live CLI / read-model：`scripts/verify.sh`、focused pytest、domain-handler export/dispatch、owner-route reconcile / dispatch、`study_progress`、OPL `agents interfaces --repo-dir <this-repo> --json`、OPL framework readiness / App drilldown / evidence-worklist outputs when the lane consumes OPL refs.
- 真实 study workspace refs：paper-line owner receipt、AI reviewer / auditor record、publication eval refs、artifact/package movement refs、memory writeback receipts、human gate / resume refs、stable typed blocker 或 no-forbidden-write refs。

Required actions:

- 优先扩面 `真实 paper-line provider apply`、`owner-chain dispatch ledger scaleout`、publication-route memory receipt、artifact lifecycle receipt、human gate/resume、provider SLO long-soak 和 family transition live receipt。
- 对 owner-chain dispatch ledger，下一轮应优先处理 fresh open 的 DM-CVD `003-dpcc-primary-care-phenotype-treatment-gap` / `run_quality_repair_batch` workorder：先通过 MAS owner route 产生 current AI reviewer supersession、owner receipt、stage receipt、monitor freshness receipt 或 stable typed blocker，再把同一 identity 的 success/blocker payload 提交给 OPL refs-only ledger。既有 verified receipt 只能作为 refs-only transport/projection evidence，不能把这些闭合写成 domain-ready 或 production-ready。
- 每个 closeout 都必须产生 MAS-owned owner receipt、stable typed blocker、reviewer/auditor record、artifact/memory/lifecycle receipt、human gate refs 或 no-forbidden-write refs；OPL provider completion、queue completion 或 refs-only ledger receipt 只能作为 transport/projection evidence。
- 若 evidence tranche 同时证明 former wrapper / alias / residue 已满足 OPL generated/default parity、MAS owner receipt 或 stable typed blocker、no-active-caller proof、focused tests 与 tombstone/provenance proof，直接删除对应旧面；否则保持当前 standard-agent source-shape 口径，不把物理删除未授权误写成功能/结构 gap。

Non-goals:

- 不写真实 study workspace artifact、paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body，除非该轮明确由 MAS owner authority 执行。
- 不把 OPL provider proof、descriptor ready、conformance pass、suite pass、queue completion、refs-only ledger verified 或 provider completion 写成 MAS paper closure、publication-ready、domain-ready、artifact mutation authorization 或 submission readiness。
- 不恢复旧 `runtime_transport/`、turn runner、worker lease、runtime lifecycle SQLite、MDS/DeepScientist 默认 backend、Hermes/local scheduler、workspace wrapper、compat alias、fallback 或只保护旧路径的聚合测试。

Verification commands:

- Docs-only：`rtk git diff --check`、`rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs`、`python3 /Users/gaofeng/workspace/opl-doc-governance/scripts/opl_doc_doctor.py doctor /Users/gaofeng/workspace/med-autoscience --format json`。
- 触及 source/contracts/runtime：`rtk scripts/verify.sh`；按触及面追加 focused `scripts/run-pytest-clean.sh ...`、`make test-meta` 或对应 owner-route / domain-handler / product-entry smoke。
- 消费 OPL refs 时追加 OPL 侧 read-model check：`rtk opl agents interfaces --repo-dir /Users/gaofeng/workspace/med-autoscience --json`、`rtk opl framework readiness --family-defaults --json`、`rtk opl runtime app-operator-drilldown --json`。

Completion gate:

- 本轮关闭的 evidence gap 已从本文重写为当前完成进度或移出 active path；仍 open 的真实 paper-line、memory/artifact/lifecycle、human gate/resume 和 provider SLO long-soak 留在“当前测试/证据差距”。
- 新增或修改的 owner receipt / typed blocker / evidence packet 有 live refs、focused verification 和 no-forbidden-write proof；OPL transport/read-model 证据没有被升级为 MAS domain verdict。
- worktree lane 已吸收回 `main` 或明确标记为近期写入/有未提交改动而保留；最终在 `main` checkout 完成最小充分验证。

Foldback target:

- Durable current truth 折回本文、`docs/status.md`、核心五件套、contracts 或 focused tests。
- dated closeout、receipt id、命令流水、workspace proof trace 和旧 phase checklist 进入 `docs/history/**`、runtime ledger、真实 workspace receipt 或提交历史；active docs 不保存执行流水。

## 当前收口完成门

- MAS repo 目标源码形态按 standard OPL Agent 收口；`generated_surface_default_owner_cutover`、`standard_agent_purity_guard`、`domain_authority_refs_thinning`、`domain_ref_consumer_physical_thinning` 等功能/结构 gate 已按 machine-readable contract 和 focused tests 关闭，当前不能再把 product/status/workbench/domain-handler/controller/progress 相关 repo-local retained path 写成 active generic wrapper tail。
- 本轮已把 owner-route default-executor materialize / dispatch 的重复 policy 常量收敛到 `default_executor_action_policy.py`，减少 `domain_action_request_materializer.py` 与 `domain_owner_action_dispatch.py` 的多重语义源；这只是 `owner_route_reconcile_materialize_dispatch_shell` 的拆薄证据，不把 repo-local wrapper tail 写成已删除或可删除。
- 本轮不触碰真实 study workspace artifact、paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body。
- 仍未闭合的真实 paper-line provider apply、publication-route memory、artifact lifecycle、human gate/resume 和 provider SLO long-soak 保留在“当前测试/证据差距”；former wrapper 物理删除只在 replacement parity、owner receipt / stable blocker、no-active-caller 和 tombstone/provenance proof 同时成立时作为 direct retirement 执行，不作为当前功能/结构 gap 保留。
- Durable current truth 折回本文、`docs/status.md`、核心五件套或对应 machine-readable contracts；dated closeout、receipt id、命令流水和旧 phase checklist 进入 `docs/history/**`、runtime ledger 或提交历史。

## 历史索引

| 需要追溯的内容 | 当前入口 |
| --- | --- |
| 当前状态摘要 | [当前状态](../status.md) |
| 架构与 owner 边界 | [架构概览](../architecture.md) |
| 不可变约束 | [不可变约束](../invariants.md) |
| 日期决策日志 | [关键决策记录](../decisions.md) |
| north-star 目标态 | [MAS 理想目标态](../references/positioning/mas_ideal_state.md) |
| 当前内容线索引 | [MAS 当前开发线路](./current-development-lines.md) |
| 文档生命周期治理 | [MAS 文档组合治理](../docs_portfolio_consolidation.md) |
| 2026-05 标准 Agent 文档过程归档 | [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md) |
| 历史完成台账 | [Plan Completion Ledger](../history/program/plan_completion_ledger.md) |

## Active / History Foldback

| 内容 | Foldback target | 规则 |
| --- | --- | --- |
| dated closeout、attempt / receipt id、命令流水、旧 phase checklist | `docs/history/program/` 或对应 `docs/history/<area>/` | 只保留 provenance；不得作为 current truth 或 active backlog。 |
| 已被 current owner surface 替代的旧 runtime/workbench/scheduler/alias 文案 | `docs/history/**` tombstone / provenance，或 machine-readable tombstone refs | active docs 只写当前 owner、删除门和 standard Agent purity guard。 |
| 已关闭功能/结构 gap | 本文 `已落地`，必要时加 compact tombstone pointer | 不保留旧 checklist chronology。 |
| 仍缺 live evidence 的能力 | 本文 `当前测试/证据差距` | 不回写成结构未完成，也不写成 production/domain ready。 |

## 当前不能写成

- 不能把 OPL provider proof、suite pass、queue completion、refs-only ledger receipt 或 provider completion 写成 MAS paper closure、publication-ready、domain-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 MAS production acceptance receipt 写成具体论文线 publication-ready；它只承认 structural / physical conformance 与 production-like receipt chain 的边界。
- 不能把 `mas_owner_receipt_present`、stable blocker、body-free evidence packet 或 OPL workorder preflight 写成 workspace mutation、artifact authority 放行、memory writeback success 或 paper closure。
- 不能把 MAS 已经没有任何私有程序面写成绝对清零；准确口径是私有面已收敛为 declarative pack / generated surface handoff、domain authority refs、minimal authority function 或 explicit tombstone/provenance refs。
- 不能把旧 `runtime_transport/`、turn runner、worker lease、runtime lifecycle SQLite、`lifecycle_refs_adapter.py`、MDS/DeepScientist、Hermes、local scheduler、workspace wrapper 或 `mas_runtime_core` 写成 MAS 默认 active runtime owner、active adapter、diagnostic fallback、compat alias 或 retained caller。
- 不能把 product-entry / workbench / owner-route / progress projection shell 写成长期 MAS generic workbench、queue、attempt ledger、retry/dead-letter、worker residency、terminal transport 或 lifecycle owner；它们当前只能输出 domain projection refs、owner receipt、typed blocker、authority refs 或 diagnostic refs。
- 不能把 `study_state_matrix` 或 OPL `family-transition-runner` matrix pass 写成 paper closure、publication quality、artifact authority、submission readiness 或 domain ready。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可由 repo tests、descriptor ready 或 conformance 替代。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出。
- 不能把 executor agent 自审、同一上下文内的执行后复核、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
