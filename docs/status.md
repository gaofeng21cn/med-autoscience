# 当前状态

文档更新时间：`2026-06-03`
最近一次已记录 live runtime audit：`2026-06-02`

Owner: `MedAutoScience`
Purpose: `current_truth_summary`
State: `active_current_truth`
Machine boundary: 本文是人读 current-state 摘要。机器真相继续归 `agent/` pack、`contracts/`、CLI/MCP/API 行为、product-entry manifest、domain-handler receipt、runtime/controller durable surfaces、真实 workspace artifact、owner receipt 和 generated artifact proof。具体 study 当前状态必须 fresh 读取 live `study_progress`、workspace artifacts、controller decisions、publication eval、OPL current-control 和 owner receipts。

Plugin native profile pointer: `contracts/opl-native-profile.json` 只声明 OPL Flow / OPL Doc 插件同步与 drift 检查所需的 repo-native profile；它不是 MAS medical truth、runtime truth、publication verdict、artifact authority、owner receipt 或 production-ready 证据。

Progress-first / AI-first operator runbook: [Progress-First Stage Outcome Runbook](./runtime/control/progress_first_stage_outcome.md) 是当前 DM002/DM003 同类 receipt/currentness/read-model/preflight 空转的稳定人读入口；它固定非终局 stage outcome、paper/deliverable 与 platform repair 分账、AI-first admission、hard gates、live verification commands 和错误路径。该 runbook 不写 study truth，也不替代 live `study_progress`、OPL current-control、owner receipt、AI reviewer verdict 或 publication gate。

## 读法

- 本文只保留当前状态摘要、owner 边界、open evidence tail 和禁止误写口径。
- dated closeout、receipt id、OPL worklist 数字、命令流水、same-day follow-through 和过程性 proof 不再写入本文；本轮文档生命周期清理记录见 [Docs lifecycle governance closeout 2026-06-03](./history/program/docs_lifecycle_governance_closeout_2026_06_03.md)。
- 若本文与 live runtime/controller/workspace output 冲突，以 live output 为准；若本文与 [MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md) 冲突，以 gap plan 对执行顺序和 evidence tail 的归属为准。

## 当前角色

`Med Auto Science` 是医学研究 domain agent，也是 OPL-compatible package。单一 MAS app skill 是 direct path 的稳定入口；经 OPL 托管时，OPL/Temporal 是默认 hosted autonomous runtime，承载 stage attempt、queue、wakeup、retry/dead-letter、resume、human gate transport、generated surface、projection 和 App/workbench shell。Codex App 只承担 direct entry / 人机操作面，不作为任务启动后的外围持续 driver。

MAS 持有医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body/writeback decision、artifact/package authority、source readiness、owner receipt、typed blocker 和 safe action refs。OPL 不写 MAS study truth、memory body、publication verdict、artifact authority 或 `current_package`。

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能通过 OPL 显式接入，并只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不是 MAS 默认 backend。

历史 MAS-local scheduler/backend、runtime lifecycle/SQLite、workspace wrapper 和 alias 材料只在 `docs/history/**`、explicit archive/import reference 或 parity oracle 语境读取；当前默认面是 OPL/Temporal hosted runtime 加 MAS domain authority refs、owner receipts、typed blockers 和 minimal authority functions。

## 最近一次已记录 DM002 / DM003 runtime truth

以下是 `2026-06-02` live audit 和后续 owner-chain follow-through 的当前文档摘要；具体 study owner、action、route key、stage attempt 和 blocker 必须重新运行 live 命令确认。

| Study | 已记录状态 | 当前读法 |
| --- | --- | --- |
| DM002 `002-dm-china-us-mortality-attribution` | 已消费 current AI reviewer record 后，next owner 投影到 `write/run_quality_repair_batch`；current work unit 是 current reviewer record consumption 后的 prose/gate/package replay lane。 | 这是 writer handoff / typed blocker / owner receipt 等待态，不是 publication-ready、paper closure、artifact authority 或 `current_package` 更新。 |
| DM003 `003-dpcc-primary-care-phenotype-treatment-gap` | AI reviewer record-production owner handoff 已推进到 gate-clearing；后续 read-model 修复已消费 executed gate-clearing stable output、清理 stale provider-attempt liveness，并把下一步重新投影到当前 owner action。 | 这是 owner-chain currentness / read-model 修复后的下一 owner 等待态；没有 live `active_run_id` 时不能写成 provider 正在跑，也不能写成 publication-ready。 |

本轮记录的 DM002/DM003 修复类别包括：

- AI reviewer record-bound publication eval schema hygiene。
- gate-clearing receipt identity / currentness consumption。
- stale provider-attempt liveness invalidation。
- current AI reviewer record consumption handoff bridge。
- default-executor closeout ingestion 和 scoped reconcile 收紧。

这些修复只改变 MAS read-model/currentness、owner-route/materializer/dispatcher 和 refs-only operator surface；除 MAS owner-authorized materialize / dispatch / reconcile surface 外，不手工写 paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body。

## 当前机器事实

| Surface | 当前事实 |
| --- | --- |
| Semantic pack | `agent/` 是 canonical medical research semantic pack。 |
| Machine contracts | `contracts/foundry_agent_series.json`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是当前主要 machine-readable truth。 |
| Direct / hosted path | Direct MAS app skill path 与 OPL-hosted path 共享同一 MAS-owned stage、controller、durable truth、quality verdict、artifact authority、owner receipt 和 typed blocker。 |
| Hosted runtime | Hosted autonomous runtime 默认由 OPL/Temporal 承担；MAS 不持有 generic daemon、scheduler、attempt loop、queue、retry/dead-letter、resume、worker residency、generic lifecycle/index 或 App/workbench shell。`domain_owner_action_dispatch` 与 `paper_repair_executor` 只能在收到 OPL provider attempt、lease 或 receipt proof 时执行 `apply`；缺失时返回 `opl_execution_authorization_required` typed blocker。 |
| Generated surfaces | OPL generated / hosted surfaces 可以生成或托管 CLI / MCP / Skill / product-entry / status / workbench descriptor，并 dispatch allowlisted MAS task；它们不能写 MAS study truth、publication-route memory body、AI reviewer verdict、publication verdict、artifact authority、source body 或 `current_package`。 |
| Workspace lifecycle | 开发 checkout 只承载 semantic pack、机器合同、authority-function descriptor/receipt refs、domain handler/native helper 和人读治理；真实 workspace state、runtime artifact、receipt instance、paper/package/export artifact 与缓存/venv/pycache/pytest 副产物必须进入受控 study workspace/runtime artifact root 或用户级 runtime state。 |
| State index pilot | MAS refs-only 小文件治理 pilot 已作为 opt-in storage maintenance surface 落到 `med_autoscience.runtime_protocol.refs_only_state_index_pilot`，通过 `runtime maintain-storage --refs-only-state-index-pilot` 或 `runtime storage-audit --apply --refs-only-state-index-pilot` 写 `artifacts/runtime/mas_refs_only_state_index_pilot.sqlite`。该 SQLite 只保存 cursor/index/lifecycle/outbox/receipt ref 的路径、哈希、大小、mtime、index version 和 rebuild epoch，不保存 study truth、publication eval、controller decisions、manuscript、artifact body、memory body、owner receipt authority 或质量 verdict，也不计 stage completion / paper progress。 |
| Standard Agent purity | `standard_agent_purity` 是 current product-entry / domain-handler / read-model 默认口径：MAS 目标形态是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。当前 retained code 只按 domain handler target、authority function、owner receipt / typed blocker producer 或 refs-only projection input 读取；repo-local dispatcher / repair executor 不再作为 MAS-private attempt loop 或 consumer 读取。 |
| Legacy names | MDS / DeepScientist、Hermes、legacy scheduler、`runtime_transport`、`mas_runtime_core*`、旧 lifecycle writer 和旧 alias 只能作为 provenance、explicit archive import、backend audit、parity oracle、tombstone 或旧输入测试语境读取；不作为当前 runtime owner、adapter、fallback、compatibility alias 或 active caller。 |
| Legacy restore diagnostic wrapper | `src/med_autoscience/runtime_protocol/legacy_restore_import_diagnostics.py` 已作为仅供测试导入的 redundant wrapper 物理退役；legacy restore / explicit archive import 诊断能力继续由 canonical `paper_artifacts.resolve_paper_bundle_manifest(..., legacy_restore_import_diagnostic=True)` 与 `quest_state.find_latest_legacy_restore_import_diagnostic_main_result_path` 持有。 |

## 当前功能/结构状态

当前 MAS 目标源码形态按标准 OPL Agent 收口为三类长期 surface：

| 类别 | 当前口径 |
| --- | --- |
| `declarative_medical_pack` | `agent/` 和 contracts 声明医学 stage、prompt、skill、knowledge、quality gate、action catalog、receipt refs 和 forbidden authority boundary。 |
| `opl_generated_hosted_surfaces` | OPL 承担 generated / hosted CLI、MCP、Skill、product-entry、status、workbench、projection shell、attempt、queue、retry/dead-letter、watch shell、generic state-machine runner、locator/index/lifecycle 和 operator workbench。 |
| `minimal_authority_functions` | MAS 保留医学 study truth、publication/source/memory/artifact verdict、AI-first record validator、owner receipt signer、typed blocker materializer、safe action refs 和 body-free domain authority refs。 |

`contracts/functional_privatization_audit.json` 当前固定 `classification_gap_count=0`、`functional_structure_gap_count=0`、`remaining_functional_followthrough_gate_ids=[]`、`active_private_generic_residue_count=0`、`repo_local_wrapper_tail_count=0`。这表示结构/功能 gap 当前关闭；它不等于真实 paper closure、publication-ready、artifact mutation authorization、provider long-soak 或 domain/production ready。

| Guard | 当前约束 |
| --- | --- |
| `generated_surface_default_owner_cutover` | 不把 MAS direct path、domain handler target 或 read-model projection 写回 MAS-owned generic wrapper。 |
| `standard_agent_purity_guard` | 旧 wrapper tail 只作为 guarded provenance / delete-gate context；不新增 compatibility shim、alias、facade 或 wrapper。 |
| `domain_authority_refs_thinning` | storage、artifact、memory、source、owner-route、progress/status helper 只输出 refs、receipts、blockers、locators 或 diagnostic projection input。 |
| `state_contract_thinning_guard` | 稳定控制面只承认 `macro_state`、`owner_route`、`receipt_or_blocker` 和 `evidence_refs`；长 reason 和 supersession reason 只能作为 diagnostic detail。 |
| `ai_first_quality_record_boundary` | 程序只做 validator、materializer、receipt signer 和 guard；质量结论必须追到独立 reviewer/auditor invocation、context/task record、quality receipt、route-back 或 typed blocker。 |

## 当前测试/证据差距

以下差距是 production evidence tail。它们不改变上面的结构口径，也不能声明 publication-ready、domain-ready、artifact mutation authorization 或 `current_package` 更新。

| 证据差距 | 当前状态 | 仍需看到 |
| --- | --- | --- |
| 真实 paper-line provider apply | multi-profile guarded-apply、DM002 canary、research evidence pack read-model/schema/canary 已证明 refs-only owner-chain shape、stable blocker 和 fail-closed 审计链可见。 | 更多真实 paper line 产出 owner receipt、paper/artifact delta、independent reviewer/auditor record、human gate/resume、route decision、stop-loss、artifact/memory lifecycle receipt 或 stable typed blocker。 |
| owner-chain dispatch ledger scaleout | `domain_dispatch_evidence_record_payload` 与 OPL refs-only identity preflight / record / verify 已覆盖 success refs path 和 typed-blocker path。 | 只处理 fresh OPL worklist 重新暴露且能绑定 MAS current owner delta 的 workorder；已 verified typed-blocker receipt 不能升级成 success receipt，success refs receipt 也不能写成 domain-ready 或 production-ready。 |
| publication-route memory receipts | Router/writeback refs 已进入 body-free evidence packets、paper-line result、domain-dispatch payload 和 stage expected refs。 | 多条真实 paper line 持续产生 accepted/rejected/blocked writeback receipts，并由 owner route 明确 memory accept/reject/blocker 结论。 |
| artifact lifecycle receipts | Artifact lifecycle report / retention plan 已输出 bounded refs、physical-thinning handoff 和 stable typed blocker refs-only shape。 | OPL apply receipt、真实 cleanup/restore/freshness apply receipt 或 MAS artifact mutation permission；不能由 report/plan 直接授权 cleanup 或 artifact mutation。 |
| human gate / resume | Stage replay human-gate refs 已有 MAS-owned body-free typed blocker path，`finalize_and_publication_handoff` 有 refs-only success path。 | Human approval、resume chain receipt、新 owner success receipt 或 paper closure。 |
| provider SLO long soak | Provider/runtime read-model 能投影 live attempt、blocked closeout 和 admission/running distinction。 | 长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。 |
| family transition live receipt | `study_state_matrix` 可把 MAS-owned domain transition table materialize 给 OPL generic matrix runner。 | Route/work-unit 进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。 |

## 当前源码形态收口

MAS repo 的长期源码形态已经按 strict purity 口径收敛为标准 OPL Agent source shape：declarative pack、OPL generated/hosted surfaces、minimal authority functions、domain handler target、domain authority refs、owner receipt、typed blocker 和 refs-only evidence。

当前 source/test morphology 的完成口径只说明入口、case、helper 和 guard 回到 preferred boundary；它不生成 MAS owner receipt，不关闭 paper-line、memory/artifact/lifecycle、domain-ready 或 production-ready。dated line-budget、test split、helper deletion、receipt/worklist follow-through 和 closeout 过程不再写入本文，必要时读提交历史、focused tests、machine contracts 或 history closeout。

Progress-first consumed-receipt read-model、owner action selection、same-tick materialize/dispatch、closeout-first handoff、route obligation descriptor、publication route-back checklist、research evidence pack projection 和 evidence tail closure summary 是当前 active read-model / controller 口径。它们只让 operator 看见下一 owner、target surface、typed blocker、receipt consumption 和 evidence ref family；不能把 projection 或 refs-only ledger 写成 publication-ready、artifact mutation authorization、paper closure 或 `current_package` 更新。

Medical quality regression lane 已收口为 `make test-medical-quality-regression`。该 lane 只验证 MAS 可消费的质量/进度语义、owner-route 和 refs-only blocker 形状，不写真实 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package`、paper body、memory body 或 artifact body，也不授权 publication-ready、paper closure、domain-ready 或 production-ready。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能声明 MAS production acceptance receipt 等于具体论文线 publication-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 descriptor ready、conformance passed、classification closed、provenance proof 或 selected proof 写成 production ready、paper closure 或物理源码清零。
- 不能把 OPL `stage_production_evidence_receipt_record|verify` 写成 MAS production ready；它只是 expected receipt / monitor freshness 的 refs-only record/verify route。
- 不能把 MDS/DeepScientist、Hermes、non-default executor proof lane 或 workspace archive 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录、receipt id、OPL worklist 数字或历史 full record 当成 current truth。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 当前执行地图：[MAS 当前开发线路](./active/current-development-lines.md)
- Runtime 边界：[Runtime boundary](./runtime/contracts/runtime_boundary.md)
- Progress-first runbook：[Progress-First Stage Outcome Runbook](./runtime/control/progress_first_stage_outcome.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 本轮文档生命周期 closeout：[Docs lifecycle governance closeout 2026-06-03](./history/program/docs_lifecycle_governance_closeout_2026_06_03.md)
