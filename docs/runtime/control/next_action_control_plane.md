# Next Action Control Plane

Owner: `MedAutoScience`
Purpose: `next_action_control_plane_design`
State: `source_control_plane_landed_live_evidence_tail_open`
Machine boundary: 本文是人读控制面设计与退役说明。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、runtime/controller durable surfaces、真实 workspace artifact、OPL StageRun / transition receipt、MAS owner receipts、typed blockers 和 human gates。本文不授权手写 runtime queue、provider attempt、Yang authority、`publication_eval/latest.json`、`controller_decisions/latest.json`、paper body 或 current package。

## 目标

Stage outcome 已收敛为单一完成面；下一步控制面也必须收敛为单一 envelope。目标链路是：

```text
StageOutcome -> NextActionEnvelope
```

`StageOutcome` 只回答当前 stage 的 terminal 或 handoff outcome；`NextActionEnvelope` 只回答当前唯一 next action。若 next action 交给 OPL，`OPL TransitionReceipt` 只回答 OPL 是否接收、运行、拒绝或关闭了该 next action 的 generic transition；它是 transport receipt-only evidence 和 MAS owner-consumption input，不参与选择默认 next action。三者必须共享同一 study / stage / work-unit identity、source refs、idempotency key 和 authority boundary。

任何旧 work-unit allowlist、progress projection、OPL queue / attempt 推断、materializer exact-id registry 都不能重新成为默认 next action owner。它们只能作为 history、provenance、diagnostic、migration input 或 no-resurrection guard。

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
| forbidden writes | Yang authority、runtime queue/provider attempt、publication eval、controller decision、paper body、current package、owner receipt / typed blocker authority file 等非本 envelope 授权面。 |
| evidence refs | StageOutcome ref、source refs、currentness refs、contract refs、readback refs。 |
| claim boundary | `can_claim_paper_progress`、`can_claim_runtime_ready`、`can_claim_submission_ready` 等必须默认 false，除非对应 owner receipt / live readback 单独证明。 |

Envelope 必须是单一的。若同一 StageOutcome 可导出多个 candidate，应先在 MAS owner surface 内完成选择或产出 human gate；不能把候选集直接暴露给 OPL queue、attempt registry、progress projection 或 materializer registry 做隐式仲裁。

### OPL TransitionReceipt

`OPL TransitionReceipt` 是 OPL generic runtime 对 NextActionEnvelope 的接收和 closeout receipt。它属于 OPL runtime / transition owner，只证明 generic transport、admission、running、terminal closeout、retry/dead-letter 或 provider observation。它不得写 MAS study truth、publication quality、artifact authority、owner receipt、typed blocker authority、human gate、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 current package。

OPL receipt 回到 MAS 时，只能作为 StageOutcome 或 MAS owner consumer 的 input ref。MAS 必须再消费 receipt，给出 owner receipt、typed blocker、human gate、route-back evidence、artifact delta、successor handoff 或 no-progress / repair blocker。OPL completion、queue empty、attempt terminal、provider reachable 或 transition receipt clean 都不能直接变成 paper progress、runtime-ready、publication-ready 或 submission-ready。

## Action family 与 exact work-unit id

`action_family` 是路由和模块发现用的稳定族名；`exact work-unit id` 是当前执行授权边界。二者不能互相替代。

- `action_family` 可以用于选择 MAS owner、OPL capability module、default executor skill、runbook 或 prompt family。
- exact work-unit id / fingerprint 必须用于 dispatch、idempotency、currentness、repeat suppression、receipt consumption、provider admission 和 terminal closeout matching。
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

## 旧面退役策略

以下旧面默认退役为 history / provenance / diagnostic：

| 旧面 | 当前允许语境 | 禁止语境 |
| --- | --- | --- |
| work-unit allowlist / exact-id route table | retired tombstone、migration audit、no-resurrection guard、测试 fixture、diagnostic detail；旧 exact id 只能作为 provenance input 解析到 `action_family`，且必须显式 `work_unit_id_authority=false`。 | default next action selector、dispatch authority、paper progress proof、per-study route authorization。 |
| progress projection scattered next action | read-model detail、human explanation、debug ref。 | current next action SSOT、owner receipt / typed blocker proof、runtime-ready proof。 |
| OPL queue / attempt 推断 | provider transport observation、TransitionReceipt input、stale/running diagnostic。 | MAS owner action selection、paper progress、publication-ready、submission-ready。 |
| materializer exact-id registry | historical matching、migration parity、idempotency diagnostic。 | 缺 StageOutcome / Envelope 时自造 dispatch 或 admission。 |
| domain diagnostic / owner-route / owner-callable legacy chain | history、migration input、consume/readback diagnostic。 | product default paper mainline、active public projection alias、compatibility route。 |

Retirement 不要求先物理删除所有历史文件。删除或收薄旧面前必须先证明没有 active caller，或已有 StageOutcome / NextActionEnvelope / OPL TransitionReceipt replacement parity。未达到物理删除门时，旧面必须显式标注 `diagnostic_only`、`history_provenance_only`、`retired_tombstone`、`no_default_caller` 或 `work_unit_id_authority=false`。

## 2026-06-29 源码侧退役切片

- `autonomy_state_surface` 已物理切断 `domain_next_action_projection` 默认返回字段；该 surface 只保留 `authority_snapshot.canonical_next_action`，不再携带旧 projection 作为可读 next-action 候选。
- `domain_next_action_projection.py` 已在无 active caller 后物理删除；旧字符串只允许出现在 history/docs/tests 的 no-resurrection 断言中。
- `authority_route_gate` 已删除 per-work-unit / per-study exact-id route allowlist。controller route 授权只看 canonical `action_family`；旧 work-unit id 可作为 provenance/currentness input 帮助解析 family，但 gate/readback 字段固定 `work_unit_id_authority=false`。
- `story_surface_work_units` 仍保留 legacy exact id registry 作为 provenance-to-family resolver 和 no-resurrection guard；它不是 route authority、dispatch authority 或 paper progress proof。
- `stage_outcome_authority` 已退役 `control/next_action.json` / `stage_native_workspace_next_action` 作为默认 dispatch selector。`stage_native_dispatch_selection.next_action()` fail closed；`persisted_dispatches` 不再从旧 stage-native workspace next-action 推导 effective action type、selected dispatch 或 blocking bypass；owner route basis 只接受带 canonical `NextActionEnvelope` identity 的 dispatch。
- `domain_action_request_materializer` 与 `study_progress` 已把旧 stage-native workspace next-action 降为 diagnostic-only。即使旧文件携带 OPL boundary 或 current-work-unit binding，也只能进入 ignored / diagnostic reason `stage_native_workspace_next_action_retired_use_next_action_envelope`；默认 `build_current_executable_owner_action()` 入口已经 fail closed，不再从 `stage_native_current_owner_action`、loose `current_work_unit`、domain transition、PaperRecovery 或 stage artifact fallback 生成 ready owner action。旧 selector 源码已物理删除；该模块只保留 fail-closed 入口和展示用 next-step 文案 helper。
- `study_progress` 在 canonical `NextActionEnvelope` 存在时，会从默认顶层 read model 清除旧 `current_work_unit`、`current_executable_owner_action`、provider-admission candidate / pending counter、transition-request candidate / pending counter、`progress_first_monitoring_summary`、`current_execution_envelope` 和 `current_execution_evidence`。这些旧面不再能在 envelope 之后复活为第二 current owner/action；顶层只保留 `legacy_next_action_authority_retired` 诊断说明和 `stage_native_current_owner_action` 的 diagnostic-only 视图。需要查看旧 provider admission / queue / execution evidence 时，只能通过显式 diagnostic / operator drilldown 读取。
- OPL StageRun currentness identity 已把 MAS request / NextAction identity 与 attempt identity 分开：`idempotency_key` 只来自 `next_action_id` 或 request idempotency；`attempt_idempotency_key` 仅作为 StageAttempt / provider receipt identity，不再兜底 MAS request identity。

该切片声明 repo-source / 默认控制面收口已落地：旧 stage-native workspace next-action、exact work-unit allowlist、projection fallback、loose current-owner fallback、attempt id fallback 都不能再作为默认 next action / owner selector；缺 `NextActionEnvelope` 时默认行为是 fail closed，而不是回到 legacy selector。它不声明 OPL runtime / DM002 / DM003 live readiness、submission-ready、publication-ready 或 paper progress。

## 验收标准

本文档落地只声明 docs/control-plane design landed，不声明代码、runtime、study 或 paper live lane 完成。后续实现验收应分账：

| 验收项 | 通过证据 |
| --- | --- |
| 文档控制面落地 | 本文存在，`docs/decisions.md` 有 2026-06-29 决策，`docs/status.md` / `docs/architecture.md` 有入口引用。 |
| 默认 next action 单一 | repo/source/control-plane 后续代码或合同能从 StageOutcome 投影唯一 NextActionEnvelope，并让各入口消费同一 envelope。 |
| 旧面退役 | tombstone / retired docs / caller audit 证明旧 work-unit allowlist、progress projection、queue/attempt 推断、exact-id registry 不再作为 default next action selector；源码切片需证明默认 surface 不再返回 legacy projection，route gate 不再以 exact id 授权。 |
| MAS / OPL 边界 | OPL TransitionReceipt 只作为 generic runtime receipt；MAS owner consumer 单独给出 owner receipt、typed blocker、human gate、route-back、artifact delta 或 successor handoff。 |
| read-model parity | `study_progress`、product-entry、domain-handler、MCP / workbench 投影同一 envelope，不从散字段恢复第二 next action。 |
| live readiness | fresh `paper-mission inspect` / `study_progress`、StageOutcome、OPL TransitionReceipt readback、owner receipt、typed blocker、human gate 或 artifact delta 单独证明；docs / focused tests / queue empty 不可替代。 |

## 当前状态

当前状态是 `source_control_plane_landed_live_evidence_tail_open`：StageOutcome 后的 next-action 默认控制面已经收口到 `NextActionEnvelope` / `action_family` / OPL transition receipt 边界；旧 stage-native workspace next-action、legacy projection、exact-id route allowlist、loose current-work-unit fallback 和 OPL attempt-id fallback 不能再决定默认 next action。仍开放的是 live evidence tail：真实 DM002/DM003 runtime receipt、owner receipt、typed blocker、human gate、route-back、artifact delta、publication / submission readiness 必须 fresh 读取对应 owner surface，不能由源码退役、focused tests 或文档状态代替。
