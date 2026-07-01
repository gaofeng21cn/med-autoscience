# Next Action Control Plane

Owner: `MedAutoScience`
Purpose: `next_action_control_plane_design`
State: `source_control_plane_landed_live_evidence_tail_open`
Machine boundary: 本文是人读控制面设计与退役说明。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、runtime/controller durable surfaces、真实 workspace artifact、OPL StageRun / transition receipt、MAS owner receipts、typed blockers 和 human gates。本文不授权手写 runtime transport state、provider execution record、Yang authority、`publication_eval/latest.json`、`controller_decisions/latest.json`、paper body 或 current package。

## 目标

Stage outcome 已收敛为单一完成面；下一步控制面也必须收敛为单一 envelope。目标链路是：

```text
StageOutcome -> NextActionEnvelope
```

当前人读入口只写作 `entry surface -> canonical NextActionEnvelope -> OPL receipt -> MAS owner consumption`。`StageOutcome` 只回答当前 stage 的 terminal 或 handoff outcome；`NextActionEnvelope` 只回答当前唯一 next action。若 next action 交给 OPL，`OPL TransitionReceipt` 只回答 OPL 是否接收、运行、拒绝或关闭了该 next action 的 generic transition；它是 transport receipt-only evidence 和 MAS owner-consumption input，不参与选择默认 next action。三者必须共享同一 study / stage / work-unit identity、source refs、idempotency key 和 authority boundary。

任何旧 work-unit allowlist、progress projection、OPL transport 队列 / StageAttempt 推断、materializer exact-id registry 都不能重新成为默认 next action owner。它们只能作为 history、provenance、observability-only diagnostics、migration input 或 no-resurrection guard。

## 三件套

### StageOutcome

`StageOutcome` 是 MAS stage closeout 的当前单一完成面。它只能落到 owner receipt、typed blocker、human gate、next stage transition、route-back / successor handoff 或等价 MAS owner-answer shape。它不负责选择多个 candidate，也不从 queue、attempt、progress projection 或 diagnostic residue 推断下一步。

Stage outcome 的有效输入必须绑定：

- `study_id`、`stage_id` 或对应 `PaperMissionRun` identity。
- `work_unit_id` 或 `work_unit_fingerprint`。
- source / runtime / eval currentness refs。
- terminal evidence refs，例如 owner receipt、typed blocker、human gate、route-back evidence、artifact delta 或 OPL terminal closeout readback。
- forbidden-write boundary。

缺少这些绑定时，stage outcome 只能给出 typed blocker、human gate 或 read-model/currentness repair handoff，不能生成默认 executable next action。

### NextActionEnvelope

`NextActionEnvelope` 是 StageOutcome 之后的唯一 next action envelope。它的职责是把 stage outcome 归一化成一个可交给 MAS owner callable 或 OPL transition runtime 的动作，不再让多个读面同时声明“下一步”。

Envelope 最小字段语义：

| 字段族 | 要求 |
| --- | --- |
| identity | `study_id`、`stage_id`、`work_unit_id` / fingerprint、route identity、idempotency key。 |
| action family | 面向 owner / module / stage 的稳定动作族，例如 `quality_repair_batch`、`gate_clearing_batch`、`paper_mission/stage-outcome`。 |
| exact work-unit binding | 当前 work unit 的精确 id / fingerprint / source refs；缺失时不能 dispatch，只能 diagnostic ignored 或 typed blocker。 |
| owner boundary | MAS owner、OPL transition owner、human owner 或 blocker owner。 |
| target surface | required output surface / receipt shape / blocker shape / human decision shape。 |
| allowed writes | 仅限该 owner surface 授权的写集。 |
| forbidden writes | Yang authority、runtime transport state、provider execution record、publication eval、controller decision、paper body、current package、owner receipt / typed blocker authority file 等非本 envelope 授权面。 |
| evidence refs | StageOutcome ref、source refs、currentness refs、contract refs、readback refs。 |
| claim boundary | `can_claim_paper_progress`、`can_claim_runtime_ready`、`can_claim_submission_ready` 等必须默认 false，除非对应 owner receipt / live readback 单独证明。 |

Envelope 必须是单一的。若同一 StageOutcome 可导出多个 candidate，应先在 MAS owner surface 内完成选择或产出 human gate；不能把候选集直接暴露给 OPL transport 队列、StageAttempt registry、progress projection 或 materializer registry 做隐式仲裁。

### OPL TransitionReceipt

`OPL TransitionReceipt` 是 OPL generic runtime 对 NextActionEnvelope 的接收和 closeout receipt。它属于 OPL runtime / transition owner，只证明 generic transport、admission、running、terminal closeout、retry/dead-letter 或 provider observation。它不得写 MAS study truth、publication quality、artifact authority、owner receipt、typed blocker authority、human gate、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 current package。

OPL receipt 回到 MAS 时，只能作为 StageOutcome 或 MAS owner consumer 的 input ref。MAS 必须再消费 receipt，给出 owner receipt、typed blocker、human gate、route-back evidence、artifact delta、successor handoff 或 no-progress / repair blocker。OPL completion、queue empty、attempt terminal、provider reachable 或 transition receipt clean 都不能直接变成 paper progress、runtime-ready、publication-ready 或 submission-ready。

## Action family 与 exact work-unit id

`action_family` 是路由和模块发现用的稳定族名；`exact work-unit id` 是当前执行授权边界。二者不能互相替代。

- `action_family` 可以用于选择 MAS owner、OPL capability module、default executor skill、runbook 或 prompt family。
- 精确 work-unit id / fingerprint 必须用于 dispatch、idempotency、currentness、repeat suppression、receipt consumption、provider admission 和 terminal closeout matching。
- 同 action family 下的新 work unit 不能消费旧 work-unit receipt、旧 closeout、旧 provider running row 或旧 typed blocker，除非 StageOutcome / MAS owner consumer 明确给出 successor / supersession 关系。
- exact-id registry 只能作为 diagnostic / provenance / migration helper；它不能在缺 StageOutcome binding 时自造 next action。

若只有 action family、缺 exact work-unit binding，`NextActionEnvelope` 状态应为 `diagnostic_ignored`、`owner_route_binding_required`、`typed_blocker` 或 `human_gate`，不得进入 default dispatch。

## MAS / OPL 边界

MAS 持有：

- study truth、stage semantics、PaperMission truth。
- publication quality、AI reviewer / auditor judgment。
- artifact / package authority、source readiness、memory accept/reject。
- MAS owner receipt、typed blocker、human gate、route-back / successor handoff。
- `NextActionEnvelope` 的 domain meaning、allowed / forbidden write boundary 和 claim boundary。

OPL 持有：

- StageRun / attempt / queue / provider lifecycle。
- command/event/outbox、retry/dead-letter、resume、worker residency。
- generic transition receipt、current-control projection、App/workbench shell。
- capability invocation substrate、locator/index/projection of refs。

MAS 可以把 NextActionEnvelope 交给 OPL transition runtime；OPL 只能返回 transition receipt / runtime observation。OPL 不选择医学 owner，不签 MAS owner receipt，不创建 MAS typed blocker，不授权 paper mutation，不声明 publication / submission readiness。

## 默认 read-model 投影

默认读面必须从单一 envelope 投影，而不是从散落字段重算：

```text
StageOutcome
  -> NextActionEnvelope
  -> current_owner_delta / study-progress / product-entry / workbench projection
  -> OPL TransitionReceipt readback
  -> MAS owner consumption / next StageOutcome
```

投影规则：

- 首屏只显示一个 current next action、一个 owner、一个 target surface 和一个 blocking reason 或 receipt ref。
- `progress_projection`、`study_progress`、`current_owner_delta`、product-entry、domain-handler export、MCP 和 workbench 都只能投影同一 envelope 或其 readback。
- 旧 `current_work_unit`、owner route、action queue、provider admission candidate、progress projection details 可以作为 envelope evidence / diagnostic details，但不能成为第二默认 next action。
- 缺 envelope 时，读面必须显示 `next_action_envelope_missing` 或对应 typed blocker / human gate；不得从 OPL queue、attempt、materializer registry 或 exact-id list 补一个隐式 next action。
- existing read model 已携带 canonical `NextActionEnvelope` 时，artifact-first mission summary、PaperMission readback missing fallback、human approval fallback、current-work-unit helper、provider-admission helper 和 materializer carrier normalization 都只能投影或补齐该 envelope；不得重新生成一个新的 fallback next action 覆盖它。新 study / 新 work-unit 即使没有旧 exact-id registry mapping，也必须通过 envelope 的 `action_family` 投影到 OPL/MAS transition contract，不能退回 exact work-unit id authority。

## 旧面退役策略

以下旧面默认退役为 history / provenance / diagnostic：

| 旧面 | 当前允许语境 | 禁止语境 |
| --- | --- | --- |
| work-unit allowlist / exact-id route table | retired tombstone、migration audit、no-resurrection guard、测试 fixture、diagnostic detail；旧 exact id 只能作为 provenance input 解析到 `action_family`，且必须显式 `work_unit_id_is_not_selector=true`。 | default next action selector、dispatch decision source、paper progress proof、per-study route authorization。 |
| progress projection scattered next action | read-model detail、human explanation、observability-only debug ref。 | current next action SSOT、owner receipt / typed blocker proof、runtime-ready proof。 |
| OPL transport 队列 / StageAttempt 推断 | provider transport observation、TransitionReceipt input、observability-only stale/running diagnostic。 | MAS owner action selection、paper progress、publication-ready、submission-ready。 |
| materializer exact-id registry | historical matching、migration parity、idempotency diagnostic。 | 缺 StageOutcome / Envelope 时自造 dispatch 或 admission。 |
| domain diagnostic / owner-route / owner-callable legacy chain | history、migration input、consume/readback diagnostic。 | product default paper mainline、active public projection alias、compatibility route。 |

Retirement 不要求先物理删除所有历史文件。删除或收薄旧面前必须先证明没有 active caller，或已有 StageOutcome / NextActionEnvelope / OPL TransitionReceipt replacement parity。未达到物理删除门时，旧面必须显式标注 `diagnostic_only`、`history_provenance_only`、`retired_tombstone`、`no_default_caller` 或 `work_unit_id_is_not_selector=true`。

History cleanup rule：`docs/history/**`、旧 dated closeout、fixture 说明和迁移审计中保留旧词本身不是问题；这些词保留的是 provenance。cleanup 的目标是 current docs / README / status / decisions / active runtime control docs 不再把旧词写成默认入口、current owner、provider admission authority、ready evidence 或 paper progress proof。若旧词仍需出现在当前入口，必须同段标出 replacement route、retired / superseded / observability-only diagnostic 语境和 forbidden claim boundary。

Active wording rule：当前 / active 文档和 product/read surface 中若出现 `current_work_unit`、`current_execution_envelope`、`current_executable_owner_action`、PaperRecovery、provider admission、delivery mirror、queue / attempt 或 StageAttempt 语言，只能表示 observability-only diagnostic drilldown、transport observation、history provenance 或 no-resurrection guard。默认 entry surface 必须回到 canonical `StageOutcome -> NextActionEnvelope`，再看同 identity 的 OPL receipt 是否被 MAS owner surface 消费；默认完成判断只能来自 MAS owner consumption：owner receipt、typed blocker、human gate、route-back evidence、artifact delta、successor handoff，或明确 fresh live readiness proof。上述旧词本身不得写成 default owner/action、provider admission authority、delivery/submission completion、paper progress、publication-ready、submission-ready、runtime-ready、`current_package` authority 或 queue attempt success proof。

Superseded wording rule：2026-06-29 之前的决策、设计、runbook 和 closeout 段落即使没有逐段 tombstone，也受本文件的退役策略约束。旧段落中的命令式表达只保留当时的 repair provenance；读者必须先套用 `superseded / diagnostic / tombstone / provenance` 语境，再判断是否有更新的 `StageOutcome -> NextActionEnvelope` 绑定。没有该绑定时，不得把旧 `provider admission`、`action_queue`、`StageAttempt`、`current_work_unit` 或 `current_executable_owner_action` 语言提升为产品默认下一步、完成判断或 ready proof。

该规则的机器合同入口是 `contracts/runtime/legacy-active-path-tombstones.json` 的 `current_surface_wording_policy`。文档和 product/read surface 可以解释旧词，但不能把旧词重新提升为默认 authority、ready evidence 或 compatibility route；需要 live acceptance 时必须回到 fresh readback / owner receipt / typed blocker / human gate / route-back / artifact delta。

## 2026-06-29 源码侧退役切片

- `autonomy_state_surface` 已物理切断 `domain_next_action_projection` 默认返回字段；该 surface 只保留 `authority_snapshot.canonical_next_action`，不再携带旧 projection 作为可读 next-action 候选。
- `domain_next_action_projection.py` 已在无 active caller 后物理删除；旧字符串只允许出现在 history/docs/tests 的 no-resurrection 断言中。
- `authority_route_gate` 已删除 per-work-unit / per-study exact-id route allowlist。controller route 授权只看 canonical `action_family`；旧 work-unit id 可作为 provenance/currentness input 帮助解析 family，但 gate/readback 字段固定 `work_unit_id_is_not_selector=true`。
- `story_surface_work_units` 仍保留 legacy exact id registry 作为 provenance-to-family resolver 和 no-resurrection guard；它不是 route decision source、dispatch decision source 或 paper progress proof。
- `stage_outcome_authority` 已退役 `control/next_action.json` / `stage_native_workspace_next_action` 作为默认 dispatch selector。`stage_native_dispatch_selection.next_action()` fail closed；`persisted_dispatches` 不再从旧 stage-native workspace next-action 推导 effective action type、selected dispatch 或 blocking bypass；owner route basis 只接受带 canonical `NextActionEnvelope` identity 的 dispatch。
- `domain_action_request_materializer` 与 `study_progress` 已把旧 stage-native workspace next-action 降为 diagnostic-only。即使旧文件携带 OPL boundary 或 current-work-unit binding，也只能进入 ignored / diagnostic reason `stage_native_workspace_next_action_retired_use_next_action_envelope`；默认 `build_canonical_owner_action_projection()` 入口已经 fail closed，不再从 `stage_native_current_owner_action`、loose `current_work_unit`、domain transition、PaperRecovery 或 stage artifact fallback 生成 ready owner action。旧 selector 源码已物理删除；该模块只保留 fail-closed 入口和展示用 next-step 文案 helper。
- `study_progress` 在 canonical `NextActionEnvelope` 存在时，会从默认顶层 read model 清除旧 `current_work_unit`、`current_executable_owner_action`、provider-admission candidate / pending counter、transition-request candidate / pending counter、`progress_first_monitoring_summary`、`current_execution_envelope` 和 `current_execution_evidence`。这些旧面不再能在 envelope 之后复活为第二 current owner/action；顶层只保留 legacy next-action retired 诊断说明和 `stage_native_current_owner_action` 的 diagnostic-only 视图。需要查看旧 provider admission / OPL transport / execution evidence 时，只能通过显式 diagnostic / operator drilldown 读取。
- `domain_action_request_materializer` 中的 `current_execution_envelope` 不再以 `authoritative` 语义命名或输出旧 `superseded_by_current_execution_envelope` reason。当前允许语义仅是 `current_execution_blocks_legacy_queue_only`：typed blocker、parked、running provider attempt 或 executable-owner legacy state 只能阻断旧 per-study / top-level queue 复活，ignored reason 固定为 `legacy_queue_blocked_by_current_execution_envelope`，不得被读成默认 next-action authority。
- `stage_outcome_authority` 中从 consumer latest 读取到的 `transition_request_pending` 只允许作为显式 blocker projection 返回。该 projection 必须携带 `dispatch_role=transition_request_blocker_projection`、`blocker_dispatch_only=true`、`default_next_action_authority=false`、`mas_dispatch_authority=false`、`dispatch_ready_for_execution_authority=false`、`can_select_next_action=false` 和 `can_start_provider_attempt=false`；它可以解释为什么 request 仍等 OPL runtime / owner receipt，但不能启动 provider attempt、选择默认 next action 或声明 MAS dispatch authority。
- OPL StageRun currentness identity 已把 MAS request / NextAction identity 与 StageAttempt identity 分开：`idempotency_key` 只来自 `next_action_id` 或 request idempotency；`attempt_idempotency_key` 仅作为 StageAttempt / provider receipt identity，不再兜底 MAS request identity。

该切片声明 repo-source / 默认控制面收口已落地：旧 stage-native workspace next-action、exact work-unit allowlist、projection fallback、loose current-owner fallback、attempt id fallback 都不能再作为默认 next action / owner selector；缺 `NextActionEnvelope` 时默认行为是 fail closed，而不是回到 legacy selector。它不声明 OPL runtime / DM002 / DM003 live readiness、submission-ready、publication-ready 或 paper progress。

## 2026-06-30 superseded successor diagnostic boundary

直接物理删除所有 superseded successor diagnostic producer 的候选曾被拒绝吸收：active observability-only diagnostic / successor projection caller 当时仍存在，过宽删除会破坏 current-control/current-work-unit regression。当前可维护边界改为先关闭 authority 复活路径：

- `terminal_next_forced_delta` 产出的 owner-successor projection 固定携带 `canonical_next_action_authority=false` 与 `projection_role=superseded_successor_diagnostic`。
- `tests/test_next_action_legacy_authority_retirement.py` 固定 retired producer 和已删除 package 不能复活。

该边界曾允许 `owner_action_diagnostics` 继续服务 observability-only diagnostic、owner-successor provenance、no-resurrection guard 或 migration readback，但禁止它们成为默认 `NextActionEnvelope`、默认 owner selector、dispatch authority、submission-ready evidence 或 paper progress proof。当前该 package 已物理删除；不得通过新增 compat shim、fallback alias 或第二套 projection 延长旧路径。

2026-06-30 follow-through：`owner_action_diagnostics.repair_progress` 已物理删除；其唯一 active consumer 迁到 `current_work_unit_parts.repair_progress_action` 内的 owner-consumption guard，输出仍明确 `canonical_next_action_authority=false`，但不再作为 `owner_action_diagnostics` producer 存在。`owner_action_diagnostics.non_advancing_terminal_closeout` 也已迁到 `current_work_unit_parts.non_advancing_terminal_closeout`，`owner_action_diagnostics.action_types` 已内联到唯一 consumer。随后 `owner_action_diagnostics.paper_recovery` 的唯一 active refresh consumer 迁到 `current_work_unit_parts.paper_recovery_successor` / `paper_recovery_projection`，旧 producer 文件物理删除；2026-07-01 follow-through 又删除 `owner_action_diagnostics/` 空 package marker。`tests/test_next_action_legacy_authority_retirement.py` 固定这些旧入口和旧 package 不能复活。

Historical physical deletion probe：`origin/main@af282e179` 上的窄删除试验删除 `gate_followthrough.py`、`publication_repair.py`、`stage_artifact_index.py`、`stage_kernel_readiness.py` 后，retirement guard 自身通过；当时旧聚合入口 `tests/study_progress_cases/current_executable_owner_action.py` 的 73 failed / 55 passed 只是 superseded baseline，不是 current contract 或当前 canonical test entry。当前删除门是 `retire_or_migrate_active_diagnostic_consumer`：这些 producer 不是 default authority，旧聚合入口也不是 current contract。仍有价值的 user-visible wording / behavior 回归应迁到 canonical envelope 或 MAS owner-consumption readback；当前 canonical user-visible entry 是 `tests/study_progress_cases/user_visible_projection.py`（经 `tests/test_study_progress.py` 汇入），它断言 MAS owner recovery diagnostic / current owner handoff 文案，且 user-facing summary 不再出现未标注的 PaperRecovery / Paper recovery 语义。

## 2026-07-01 completion audit current wording

当前完成度审计按两本账读取：`source/control-plane` 已落地默认 NextAction authority、fail-closed 行为、synthetic route guard、OPL handoff identity fixture 和合同/文档口径；`live acceptance` 仍必须由对应 owner/live surface 单独证明。2026-07-01 fresh verification 覆盖：NextAction / synthetic / authority-route / domain-materializer / legacy-retirement focused tests `59 passed`，current-work-unit / autonomy / execution-envelope / legacy-active-path retirement `32 passed`，PaperRecovery contract/state `37 passed`，provider-admission current-control `72 passed`，domain-action materializer `30 passed`，`make test-meta` `465 passed`，`scripts/verify.sh` passed。后续 source morphology follow-through 又把 `paper_recovery_state.py` 的 terminal closeout projection 拆入 `paper_recovery_state_parts/terminal_closeout_projection.py`，入口降到 995 行；`make line-budget` 当前报告 37 个 advisory。该数字只说明 repo-wide source morphology tail，不声明 live paper/runtime acceptance。

| 项目 | 当前完成度 | 证据口径 | tail / 禁止替代 |
| --- | --- | --- | --- |
| 默认 NextAction authority | `done` for source/control-plane | 默认链路只承认 `StageOutcome -> NextActionEnvelope`，旧 exact-id、stage-native workspace next-action、legacy projection、unknown/unmapped action family 和 attempt id fallback 不能再选择默认 next action；未知 family fail closed 到 MAS typed-blocker owner，而不是猜成 prose repair。 | 不声明 DM002/DM003 live owner action、provider running、paper progress 或 submission-ready。 |
| fail-closed 缺 envelope 路径 | `done` for source/control-plane | 缺 `NextActionEnvelope` 时只能进入 diagnostic ignored、typed blocker、human gate 或 repair handoff；旧 selector 不得补隐式 action。 | queue empty、domain diagnostic dry-run、projection clean 或 focused tests 不能替代 owner/live readback。 |
| synthetic route / false-claim guard | `done` for regression surface | synthetic fixture、authority-route DM004 新 study fixture 和 no-resurrection guard 只证明旧面不能复活为默认 authority，且新 work-unit 不需要 exact-id mapping。 | synthetic route 不等于真实 OPL StageRun、真实 provider attempt、paper artifact delta 或 DM002/DM003 governed acceptance。 |
| canonical envelope preservation | `done` for source/control-plane | existing `study_progress.progress_projection.next_action` 已是 canonical envelope 时，artifact-first summary 不再用 `paper_mission_readback_missing` / `human.approval` fallback 覆盖它；materializer carrier / transition request projection 可从 study-level envelope 保留 `action_family=runtime.opl_route`，不要求旧 exact work-unit mapping。 | 这只证明 read-model / materializer source path 的 canonical carrier 保留；不证明 OPL 已运行、owner 已接受或论文可提交。 |
| contract docs / current wording | `done` for docs/current-plan | 本文、`README.zh-CN.md`、`docs/status.md`、`docs/active/mas-ideal-state-gap-plan.md` 和 `docs/decisions.md` 固定完成度分账和 forbidden claim boundary；当前人读入口已把 OPL transport receipt、queue / attempt / provider readiness 和 owner hint 标为 diagnostic / observed wording，不再写成默认 next action、stage completion 或 provider admission authority。 | docs、tests、`scripts/verify.sh`、product wording 或 `git diff --check` 只证明文档/源码约束，不得写成 publication-ready、submission-ready、UI live acceptance 或 current-package ready。 |
| historical producer physical deletion | `partial` | `owner_action_diagnostics.repair_progress`、`owner_action_diagnostics.non_advancing_terminal_closeout`、`owner_action_diagnostics.action_types` 和 `owner_action_diagnostics.paper_recovery` 已物理删除 / 迁移；`owner_action_diagnostics/` 空 package marker 也已删除。provider-admission 的 study-level legacy current-action fallback producer 和 domain-handler current-control transition-request task producer 已物理删除，缺 envelope 时不再从散落 study current fields 补默认 candidate。PaperRecovery obligation projection 已拆出并 fail closed：没有 canonical next-action source 时，不再从 top-level legacy `current_executable_owner_action` / `current_execution_envelope` 补 owner、action 或 work-unit。`paper_recovery_state.py` 又把 terminal closeout matching、provider-admission consumed closeout、closeout refs 和 suppressed diagnostic surfaces 搬入 parts 文件，减少主 reducer 复污染面积。`current_execution_envelope` 在 materializer 中只命名为 legacy queue blocker，transition-request pending projection 在 stage-outcome authority 中只返回 blocker-only / no-default-next-action 字段。剩余 tail 是更广义的 legacy current-work-unit / current-execution identity/readback helper 与 source morphology 退役，不是默认 producer。 | 不为保留 producer 新增 compatibility shim、fallback alias 或第二套 projection；显式 `action_queue`、request-only transition 和 receipt/currentness identity helper 只能作受控 diagnostic / readback，不得重新成为默认 authority。 |
| 大文件/source morphology 边界 | `partial` | `paper-mission` 大入口已继续拆出 one-shot migration、drive、materialized readback 和 candidate-package readback helper；`paper_mission_commands.py` 当前已降到 805 行，低于 1000 行 preferred advisory；`runtime_surface_retirement.py` 已把 runtime-health validator 拆到 `runtime_surface_retirement_parts/runtime_health_kernel_validators.py`，主文件降到 951 行；`paper_recovery_state.py` 已把 terminal closeout projection 拆到 `paper_recovery_state_parts/terminal_closeout_projection.py`，主文件降到 995 行。drive/readback focused tests `16 passed`；runtime-surface focused tests `22 passed`；paper-recovery focused tests覆盖 `56 passed` 与相关 policy/provider-admission tests `19 passed`；`make line-budget` 当前仍报告 37 个 advisory。 | 大文件收薄不写 runtime state、owner receipt、typed blocker authority、paper body、publication eval、controller decision 或 current package；line-budget advisory 也不能替代 live acceptance。 |
| UI / workbench live 标签 | `done` for source wording; `tail_open` for live acceptance | Product/workbench/status markdown 默认标签已改为 diagnostic / observed wording；live 标签是否被真实 owner action 消费仍另账。 | UI 可见、trace 可见、zero worklist、operator text 或 wording clean 不能成为 progress、submission-ready 或 runtime-ready evidence。 |
| DM002/DM003 live paper acceptance | `tail_open` | 只能由 fresh `paper-mission inspect` / `study_progress`、OPL StageRun readback、owner receipt、quality gate receipt、stable typed blocker、human gate、route-back 或 canonical artifact delta 关闭。 | docs/tests/verify、candidate package、refs-only ledger、queue empty、provider completion 或 historical canary 不得替代。 |

## 验收标准

本文档落地只声明 docs/control-plane design landed，不声明代码、runtime、study 或 paper live lane 完成。后续实现验收应分账：

| 验收项 | 通过证据 |
| --- | --- |
| 文档控制面落地 | 本文存在，`docs/decisions.md` 有 2026-06-29 决策，`docs/status.md` / `docs/architecture.md` 有入口引用。 |
| 默认 next action 单一 | repo/source/control-plane 后续代码或合同能从 StageOutcome 投影唯一 NextActionEnvelope，并让各入口消费同一 envelope。 |
| 旧面退役 | tombstone / retired docs / caller audit 证明旧 work-unit allowlist、progress projection、OPL transport 推断、exact-id registry 不再作为 default next action selector；源码切片需证明默认 surface 不再返回 legacy projection，route gate 不再以 exact id 授权，仍保留的 superseded successor diagnostic producer 明确 `canonical_next_action_authority=false`。 |
| MAS / OPL 边界 | OPL TransitionReceipt 只作为 generic runtime receipt；MAS owner consumer 单独给出 owner receipt、typed blocker、human gate、route-back、artifact delta 或 successor handoff。 |
| read-model parity | `study_progress`、product-entry、domain-handler、MCP / workbench 投影同一 envelope，不从散字段恢复第二 next action。 |
| live readiness | fresh `paper-mission inspect` / `study_progress`、StageOutcome、OPL TransitionReceipt readback、owner receipt、typed blocker、human gate 或 artifact delta 单独证明；docs / focused tests / queue empty 不可替代。 |

## 当前状态

当前状态是 `source_control_plane_landed_live_evidence_tail_open`：StageOutcome 后的 next-action 默认控制面已经收口到 `NextActionEnvelope` / `action_family` / OPL transition receipt 边界；旧 stage-native workspace next-action、legacy projection、exact-id route allowlist、unknown/unmapped action family、loose current-work-unit fallback、provider-admission study-level fallback 和 OPL attempt-id fallback 不能再决定默认 next action；缺 envelope 或缺可识别 action family时默认 fail closed；synthetic route / false-claim guard 和合同文档口径已落地，authority-route 也有 DM004-style 新 work-unit fixture 证明 canonical `action_family` 才是 route authority。`owner_action_diagnostics.repair_progress`、`owner_action_diagnostics.non_advancing_terminal_closeout`、`owner_action_diagnostics.action_types` 和 `owner_action_diagnostics.paper_recovery` 已物理删除 / 迁移，`owner_action_diagnostics/` 空 package marker 也已删除；provider-admission 的 study-level legacy fallback producer 和 domain-handler current-control transition-request task producer 已退役，PaperRecovery obligation projection 缺 canonical next-action source 时也不会从 legacy top-level action/envelope 复活 owner、action 或 work-unit；`paper_recovery_state.py` 的 terminal closeout projection 已拆到 parts，主 reducer 低于 1000 行；显式 queue / request-only / currentness identity readback 仍只作受控 diagnostic 路径；`current_execution_envelope` 在 materializer 中只阻断 legacy queue，`transition_request_pending` projection 在 stage-outcome authority 中只作为 blocker-only / no-default-next-action 读面；当前人读入口已把 OPL transition receipt、queue / attempt / provider readiness 和 owner hint明确为 transport / diagnostic wording，不再当作默认 next-action authority；`paper-mission` CLI 已继续拆出 one-shot migration、drive、materialized readback 和 candidate-package readback helper，`paper_mission_commands.py` 已降到 805 行；`runtime_surface_retirement.py` 已拆出 runtime-health validator 并降到 951 行。仍开放的是更广义的 legacy diagnostic consumer / current-work-unit / current-execution identity helper、剩余 source morphology 收薄和 live evidence tail：更激进删除已由 73-failure probe 证明会撞到旧聚合测试/consumer，必须先迁移有保留价值的行为或删除对应 consumer；真实 DM002/DM003 runtime receipt、owner receipt、typed blocker、human gate、route-back、artifact delta、publication / submission readiness 必须 fresh 读取对应 owner surface，不能由源码退役、focused tests、`scripts/verify.sh` 或文档状态代替。
