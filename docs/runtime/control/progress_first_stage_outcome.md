# Progress-First Stage Outcome Runbook

Owner: `MedAutoScience`
Purpose: `operator_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 operator / docs runbook。机器真相继续归 MAS controller/read-model output、OPL current-control-state、owner receipts、typed blockers、runtime artifacts、publication eval、controller decisions 和真实 workspace evidence。本文不授权手写 runtime-owned study truth、paper body、publication verdict、controller decision、submission package 或 `current_package`。

## 适用范围

本 runbook 用于 DM002 / DM003 这类 Progress-first / AI-first 论文线停滞判断：系统已经能看到 receipt、currentness、read-model、provider handoff 或 `current_executable_owner_action`，但 operator 需要判断当前 stage 是否真正前进、是否应 admission 到 OPL/provider/scheduler，还是仍卡在 hard gate。

它不用于声明终局 readiness。publication-ready、submission-ready、paper closure、artifact authority、memory authority 和 `current_package` 更新仍只能来自对应 MAS owner surface、AI reviewer / publication gate verdict、owner receipt 和 artifact/package freshness proof。

Stage Operating Layer 是 Progress-first 的第一读面：非终局 stage 首屏必须只读呈现 `stage_kernel_projection` 派生的 current stage、artifact roles、missing outputs、accepted receipts、semantic validation、consumability、lineage、retention / restore、current pointer、blocker、next owner 和 provider liveness。`stage_artifact_index` / Stage Deliverable Index 仍然重要，但它是 derived refs-only locator projection，不是 study truth、artifact truth、quality verdict 或 publication readiness authority。缺 `stage_kernel_projection` 时，Workbench / Progress Portal 必须 fail-closed 为 pending lane；不得从 `stage_artifact_index`、controller/read-model/currentness、telemetry、evidence-tail 或 repair 诊断推断 primary progress。

SQLite / State Index Kernel 的读法同样只属于 operating index：`contracts/stage_artifact_kernel_adoption.json#/state_index_kernel_adoption` 声明 MAS 是 OPL SQLite sidecar 小文件治理的首要 candidate，但 SQLite 只能承载 refs、locator、cursor、checksum、source fingerprint、receipt/blocker/restore refs 和 bounded preview hash。`domain_authority_refs.sqlite`、paper work-unit outbox 或任何 legacy runtime lifecycle SQLite 不能作为 stage completion、paper progress、publication quality、artifact authority 或 owner receipt authority；它们只能加速查找、去重、恢复和 operator read-model rebuild。

## 非终局 stage outcome

非终局 stage 只能落到以下六类 outcome；不得用 `done`、`complete`、`healthy`、`all clear`、`ready` 这类泛化词关闭 stage。

| outcome | 含义 | operator 下一步 |
| --- | --- | --- |
| `running` | OPL current-control / runtime liveness 明确 `running_provider_attempt=true`，且存在 active stage attempt、run 或 workflow ref。 | 监督 active attempt；不要重复 materialize、dispatch 或 owner-route reconcile 同一 work unit。 |
| `ready_for_owner_action` | `current_executable_owner_action` 完整，hard gate 缺席，但尚未观察到 provider running proof。 | admission 到 OPL/provider/scheduler 或 MAS owner callable；若只写出 handoff，下一 owner 是 provider admission。 |
| `waiting_human` | 当前 owner surface 明确 human gate、approval、pause/resume 或不可由 AI/provider 继续的人工决策。 | 等人工决定；不得用 provider redrive 绕过。 |
| `blocked_with_typed_owner` | MAS-owned typed blocker 明确 current owner、work unit、source/runtime/truth currentness refs、forbidden-write proof 或 no-progress reason。 | 交给 blocker owner、mechanism repair、human gate 或 stop-loss candidate；不得重跑同义 receipt/reconcile。 |
| `terminal_success` | 当前非终局 work unit 已产出可消费 owner receipt、paper/artifact delta、reviewer/gate delta、stable typed blocker 或 next owner handoff，并且后续 owner 已可被投影。 | 消费 receipt 并进入下一 owner；不能把它升级成 publication/submission ready。 |
| `terminal_stop_loss` | same owner/work unit/source currentness 已耗尽 redrive budget，或 hard blocker 无法在当前 lane 内解除。 | 记录 stop-loss owner、原因和允许重开条件；不得继续 ordinary dispatch loop。 |

`receipt_consumed` 是观测状态，不是 `ready_for_owner_action`。它必须立刻让位给下一 owner projection、typed blocker、human gate、running proof 或 stop-loss；若没有下一项，问题归入 read-model/currentness 修复，而不是继续消费同一 receipt。

display / matrix / workbench 不拥有 current work-unit 决策权。Progress-first MVP 允许多个 candidate producer 继续写出 `current_executable_owner_action`、`current_execution_envelope`、OPL queue、`domain_transition` 或 `next_forced_delta`，但 operator outcome 必须从 canonical `current_work_unit` 读取当前 work unit，并把旧散字段只当作 provenance 或 ignored diagnostic。`admission_pending` 与 `running_provider_attempt` 必须分账：前者表示可进入 OPL/provider/scheduler 或 MAS owner callable admission，后者只在 strict live provider proof 成立时为 true，OPL attempt handle 本身不是 running proof。

OPL current-control handoff 导出的 `provider_admission_candidates[]` 是 queue / attempt / provider transport 的启动候选，不是新的 MAS truth。候选必须由 current-control action / owner-route currentness 匹配 canonical `current_work_unit` identity 后产生；ready dispatch 只证明 callable carrier、action/owner 和 dispatch authority 可用。若候选缺 work-unit identity、缺 dispatch authority、与 canonical current work unit 不匹配，或被 terminal closeout / typed blocker / human gate supersede，operator outcome 必须 fail closed 到 currentness / typed owner，而不是 broad redrive。

fresh `study_progress.current_owner_ticket` 也不能自证 currentness。只有 owner route / current action / current work unit / ticket work unit 带 strong source fingerprint、work-unit fingerprint、action fingerprint 或 `source_eval_id` 时，它才能生成 dispatchable owner action。若只有 `study-progress-current-owner-ticket::*` synthetic id、generated_at、source_ref 或 action family，operator outcome 是 weak currentness diagnostic；selector 必须忽略它，不得生成 request task 或 default executor dispatch。

当 OPL / provider 在 study 的 `paper/review` 或等价 MAS owner-authorized review surface 写出 stage closeout，并且 closeout 证明 canonical story-surface delta 已 materialized，Progress-first controller 必须优先把它作为 consumed owner receipt 处理。即使 closeout 自身缺少 `truth_epoch`、`work_unit_id` 或 `work_unit_fingerprint`，只要能从 `stage_packet_ref` 恢复 current owner route，并且 action 是当前质量修复 work unit、owner result 已执行、story-surface hygiene clear，就应退役对应 writer handoff，把 projection 推进到下一 owner，例如 AI reviewer re-eval 或 gate replay。缺 story-surface delta、typed blocker、manuscript digest mismatch 或 stale closeout 仍按 nonconsumable redrive 处理。

同一条 consumed writer handoff 判断必须同时约束 materializer 和 dispatch selector。即使 persisted consumer dispatch 仍留在 `artifacts/supervision/consumer/default_executor_dispatches/` 或 consumer latest read-model 中，只要对应 `run_quality_repair_batch` 已被 owner-authorized closeout 消费，默认 dispatch 不得再选择、执行或用它覆盖当前 AI reviewer / gate / downstream owner action。若 materializer 已投影下一 owner，而 dispatch 仍选择旧 repair handoff，这是 dispatch arbitration currentness bug，应回 MAS controller/read-model 修复，不得手删 study-local dispatch 文件。

这条消费规则不只适用于 `quality_repair_batch_writer_handoff`。任何 default executor dispatch 只要带当前 owner route，且 `artifacts/supervision/consumer/default_executor_execution/latest.json` 或 execution ledger 已有同 action、同 owner-route currentness 的可消费 receipt，例如 `run_quality_repair_batch` 已产生 `progress_delta_candidate`、changed artifact refs、AI reviewer recheck request 或 gate replay refs，selector 就必须把该 dispatch 从 current selection 中移除。后续推进应来自 receipt 触发的下一 owner projection、AI reviewer / gate request、typed blocker 或 stop-loss，而不是重复执行同一个 repair action。

当 OPL provider attempt 已 terminal，但 MAS `work_unit_ledger` 仍保留同一 dispatch key 的 `opl_runtime_handoff_required` 时，operator outcome 不是 `running`，也不是等待同一 provider 自行持续推进。MAS `domain-health-diagnostic` 必须消费同一 `action_type`、`work_unit_id`、`work_unit_fingerprint`、terminal status 和非空 `closeout_refs` 的 `default_executor_execution` evidence，把旧 handoff 关闭为 `default_executor_closeout_after_opl_runtime_handoff`，再重新判定唯一 next work unit。若 closeout 是 paper-facing delta，进入下一 owner / reviewer / gate；若 closeout 是 stable typed blocker，投影为 `blocked_with_typed_owner`；若只是 transport/result refs，则计为 platform repair 并要求 MAS current work-unit reducer 给出下一 owner、typed blocker、human gate 或 stop-loss。

同一 scan 同时看到旧 provider attempt terminal closeout 和不同 identity 的新 owner action / provider admission candidate 时，terminal closeout 只压旧 running 投影，不得吞掉新 handoff。DHD materialized current-control 必须把旧 `running_provider_attempt`、`active_run_id`、`active_stage_attempt_id`、`active_workflow_id` 清空，标记 `stale_running_projection_suppressed=true`，并把 terminal evidence 挂到新 work-unit 的 `terminal_closeout_precedence_evidence`；新 work unit 继续按 `provider_admission_pending`、next owner handoff、typed blocker 或 human gate 裁决。OPL queue 侧的同 identity running row 若已绑定 terminal attempt，只能修正为 stale transport closeout observed / idempotent noop，清 lease，不 duplicate hydrate，不启动新 provider attempt。

当 `progress_first_monitoring_summary.latest_terminal_stage` 或 `latest_terminal_stage_log` 已记录同一 `action_type + work_unit_id` 的 `repeat_suppressed`、typed blocker 或 stop-loss terminal closeout 时，operator outcome 是 `terminal_stop_loss` / `blocked_with_typed_owner`，不是 `ready_for_owner_action`。该 terminal closeout 必须成为 canonical `current_work_unit.typed_blocker`，默认 blocker=`anti_loop_budget_exhausted`，并压住同一 work unit 的 provider admission candidate、action queue、stale handoff 和旧 default-executor dispatch。只有新的 work-unit identity、MAS owner receipt、quality gate receipt、human gate、route-back evidence 或 owner-authorized next owner 出现后，才能进入下一轮 admission。

DHD scoped dry-run / apply 只对本次扫描 study 产生 active queue。未扫描 study 的历史 action queue 或 handoff 只能保留为 audit-only residue；它不能增加 `provider_admission_pending_count`，不能出现在 active `action_queue`，也不能驱动 OPL tick。这个规则用于避免“局部检查一篇 study，却被另一篇旧 residue 触发 provider admission”的跨 study 误启动。

当 progress projection 已证明当前 study 存在 fresh meaningful paper/artifact delta，且同一 scan 仍有可执行 owner action 时，旧 `progress_first_owner_redrive_budget_exhausted` 只能作为 no-loop residue 标注为 stale superseded。Progress-first 优先推进当前 owner action、next-owner handoff 或 provider admission；只有缺 fresh delta、缺可执行 owner action、缺 typed blocker 或缺 hard-source 的重复 nonconsumable closeout 才保持 `terminal_stop_loss`。

当 OPL current-control 的 study-level `owner_route` 只是 truth snapshot / reconcile placeholder，且 `next_owner` 为空、`allowed_actions` 为空，或对当前 dispatch 不满足 owner-route match / route-allows-action 时，它只能作为 fail-closed 诊断背景，不能压住同一 study `action_queue` 中可 dispatch 的当前 owner route。dispatch selector 和 execution owner-route lookup 必须优先使用能匹配当前 dispatch、允许当前 action、带 required output surface 的 action-queue route；只有 action-queue route 缺席或不 dispatchable 时，才把 study-level route 返回给执行层生成明确 blocker。若 AI reviewer / gate / write owner action 已在 `action_queue` 中 ready，而默认 dispatch 因非 dispatchable study-level route 返回 `execution_count=0`，这是 read-model arbitration bug，不是论文目录需要手工迁移或论文 surface 可直接修改的许可。

当 `domain_transition` 已消费上一个 receipt 并明确 `controller_action` 指向下一 owner action，例如 `return_to_ai_reviewer_workflow`，但 OPL current-control 还没有把该 action 放入 `action_queue` 时，已 materialized 的 ready consumer dispatch 仍可作为当前 owner action authority。selector 必须用 consumed-transition route 的 action type、next owner、work unit id / fingerprint 校验 dispatch route；校验通过后按 dispatch 自带 owner route 执行，并在 execution payload 中标记 `owner_route_basis=consumed_transition_owner_action`。这条规则不适用于 publication gate replay 的 stale 防线；gate replay 仍要求严格 source-fingerprint / work-unit currentness，不能用宽松 bridge 执行旧 gate dispatch。

当 `return_to_ai_reviewer_workflow` 的第一次执行已经把 stale `publication_eval/latest.json` 路径转化为 `ai_reviewer_record_production_handoff`，并将 persisted dispatch 的 `required_output_surface` 改为 `artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json` 时，后续默认 dispatch selector 必须优先选择这个 persisted record-only handoff。workspace-level `artifacts/supervision/consumer/latest.json` 中仍残留的旧 inline dispatch 只是 stale read-model，不得覆盖 persisted handoff、不得再次生成同义 handoff，也不得把 handoff-ready 误记为论文内容进展。若 selector 仍显示 `dispatch_authority=consumer_default_executor_dispatch` 且 required output 回到 `artifacts/publication_eval/latest.json`，这是 dispatch arbitration currentness bug，应回 MAS controller 修复。

每个 Progress-first owner action 必须带可机器校验的 target surface。若 AI reviewer 或 domain transition 的推荐动作使用 publication decision 语义，例如 `route_back_same_line`，但实际 executor action 在 `controller_action_type=run_quality_repair_batch`，owner route 仍必须从 executor action policy 推导 `target_surface` / `target_surface_source`，并在 `next_forced_delta` 中显示 `target_surface_specificity=explicit_owner_route_target`。缺 explicit target surface 时 study-state-matrix 应 fail-close 为 `owner_route_target_surface_required`，不得把它当作 queued/running 或继续重复 receipt reconcile。

当 `domain-action-request-materialize` 把当前 AI reviewer record 或 gate result 桥接成新的 owner route，并在 dispatch 本体写入完整 `owner_route.currentness_contract`、`allowed_actions`、`required_output_surface` 和 bridge authority 时，dispatch 执行层可以把该 dispatch 自带 owner route 作为 current route 使用。条件是同一 dispatch 通过 owner-route match、route-allows-action 和 owner-route attempt protocol；通过后应标记 `owner_route_basis=dispatch_owner_route_bridge` 并立即执行 owner callable 或生成 typed blocker。不得因 OPL scan read-model 尚未同步同一个 bridge route 而返回 `current_owner_route_missing`，也不得回到下一轮 read-model reconcile。

## 分账规则

paper / deliverable progress 只承认五类 owner delta：

- MAS owner receipt。
- canonical paper / artifact delta。
- independent AI reviewer、auditor 或 publication-gate delta。
- stable typed blocker，且 blocker 明确 owner、work unit 和缺失 evidence。
- next owner handoff，且 handoff 带 current owner、work unit、required output surface、source refs 与 write boundary。

以下内容只能记为 platform repair / observability：telemetry、duration/token/cost 补齐、stage-log accounting、dispatcher hydration、receipt reconciliation、read-model currentness hygiene、OPL refs-only ledger record/verify、provider liveness/projection refresh、Portal wording/card 修复、bounded product-entry refresh。

terminal stage accounting 的 duration / token / cost 可以来自 closeout 顶层，也可以来自合同规定的 `paper_stage_log` / `user_stage_log` / `stage_log_summary`。当顶层 telemetry 缺失但 stage log telemetry 完整时，read-model 可以投影为 observed，并合并顶层与 stage-log refs；这只关闭 observability/read-model 缺口，不改变 owner outcome，不给 paper-progress credit，也不证明 provider running 或 publication readiness。

同一轮同时出现 paper delta 和 platform repair 时，token / time 分账优先归 platform repair；paper / deliverable delta 只记录真实 owner delta 的 surface refs，不把平台修复耗时混报成论文推进。

Stage Operating Layer 分账进一步约束 stage MVP：`stage_kernel_projection` 是 Workbench primary progress 的当前 truth source；`stage_artifact_index` / Stage Deliverable Index 更新本身只算 derived locator/projection，除非它引用了新的 canonical paper / artifact delta、owner receipt、reviewer/gate delta、stable typed blocker、human gate、route-back 或 stop-loss。physical stage folder 只有通过 current pointer promotion、semantic receipt validation、consumability gate、lineage 和 retention / restore 检查后，才可被写成 current artifact progress；仅刷新 currentness、telemetry、read-model、receipt reconcile、provider liveness 或 evidence-tail 分类时，记为 platform repair / observability；不能写成 Stage Operating Layer landed，也不能显示成 primary progress。

## Co-Scientist Affordance 分账

Progress-first 的 Co-Scientist affordance 只优化“下一步更快、更准、更少重复”，不创造独立 progress 类别。它不是默认增强层；只有 `current_delta_declares_or_implies_affordance_need` 成立时才即时调用。Operator 读取这层 signal 时按以下规则分账：

| signal | 可计入 | 不可计入 |
| --- | --- | --- |
| `next-delta tournament` | next owner selection evidence、route advisory、no-loop suppression hint。 | paper progress、route blocker、admission gate、publication readiness。 |
| `bounded micro-candidate generation` | 当前 work unit 的候选 repair / analysis / display / review target refs。 | 独立 stage completion、质量闭环、后台 paper-line progress。 |
| `critique-as-repair-hint` | reviewer gap list、repair target surface、route-back briefing。 | AI reviewer verdict、quality closure、publication gate closeout。 |
| `reusable lesson extraction` | failed-path recall、negative result reuse、rejected candidate context、memory routing hint。 | memory accept/reject verdict、artifact authority、paper progress。 |
| `triggered meta-review` | route arbitration brief、stop-loss candidate、human-gate suggestion。 | 每轮必经 admission gate、route blocking layer、publication readiness。 |
| `opportunistic knowledge prefetch` | context hydration、literature/source/journal refs availability、reviewer briefing support。 | paper progress、quality score、readiness proof、hard blocker。 |

缺少、陈旧或失败的 prefetch / tournament / meta-review / reusable lesson extraction 只算 observability 或 platform repair，不能压住已经可执行的 `current_executable_owner_action`。只有这些 signal 暴露了真实 hard gate，例如 missing source/data、forbidden write、human gate、missing owner callable 或 irreversible mutation，才按 Hard gates 归类；否则下一步仍应推进 owner action、reviewer request、memory writeback receipt、typed blocker、route-back 或 stop-loss。

Light-derived external-pattern advisory 遵循同一 Progress-first 规则，详见 [Light External Pattern Intake Runbook](./light_external_pattern_intake.md)。Light 的 progress passport、checkpoint、references/scripts/assets 分层、source map / literature matrix、experiment matrix / reproducibility plan、manuscript / rebuttal modes、PRISMA flow、style fingerprint、argument review、locator audit、figure export / integrity / panel template 和 mode registry 只能被 MAS 吸收为 skill-content 方法：它们帮助下一 owner 更快拿到 ref ledger、source-readiness hint、reviewer/writing hint、citation integrity hint、display QA hint 和 bounded mode discipline。它们不创造 progress 类别，不关闭 AI reviewer verdict、publication gate、quality gate、artifact authority 或 owner receipt，不安装 Light，不复制 27-skill router，也不把 Light `db09`、score、checklist、期刊规格表、font defaults 或 API 表写成 MAS truth。

| Light skill-level signal | Progress-first 记账 | 非阻塞条件 |
| --- | --- | --- |
| progress passport / advisory ref ledger | `verified_asset_ref`、`collision_check_ref`、`refusal_rehearsal_ref`、`fresh_evidence_gate_ref` 或 next owner briefing。 | 缺失时默认是 observability / platform repair；不得压住已完整的 `current_executable_owner_action`。 |
| checkpoint decision / confirm gates | human gate、AI reviewer request、route-back、typed blocker 或 closeout evidence 的表达模板。 | 只有命中 MAS hard gate 时阻断；普通 checklist / self-check 失败只生成 repair hint 或 reviewer briefing。 |
| source map / literature matrix | `source_search_discipline_ref`、`literature_matrix_ref`、source-readiness note 或 stage knowledge packet hint。 | 缺模板或矩阵默认是 platform repair；只有当前 owner 必须消费 source/evidence ref 且缺失会阻止 owner output 时才升级。 |
| experiment matrix / reproducibility plan | `experiment_matrix_backlink_ref`、analysis repair hint 或 artifact lineage hint。 | 缺实验矩阵不阻塞无关 owner action；只有当前实验、复现、artifact lineage 或 publication gate route 需要该 ref 时升级。 |
| PRISMA flow | systematic review / meta-analysis 的 source-readiness hint 和计数自洽 ref。 | 非系统综述 work unit 不要求 PRISMA；缺 PRISMA 不阻塞 narrative review、idea scout 或快速 source prefetch。 |
| manuscript / rebuttal modes | manuscript target surface、write-boundary hint、reviewer response briefing、commitment ledger 或 mode ref。 | mode 不是 MAS route table；缺 mode 模板不阻塞写作或审稿 admission，除非当前 action 缺 explicit target surface / forbidden-write boundary / reviewer-comment ref。 |
| style fingerprint | author voice / polishing / reviewer-writing hint。 | 不授权写 paper body；缺失不阻塞写作、修订、reviewer request 或 gate replay。 |
| argument review | claim-evidence-boundary、hedging、section-role 和 AI disclosure repair hint。 | 不替代独立 reviewer / auditor；缺失默认是 manuscript repair hint。 |
| citation locator audit | claim-source integrity hint；在 citation-backed claim 或 publication gate 场景可成为 route-required ref。 | DOI / metadata / locator 缺口只有影响当前 owner output 或 hard gate 时升级；开放索引缺失不能单独写成 citation failure。 |
| figure export / integrity / panel template | figure manifest、target journal / column、final size、editable font、source-data/statistics/export QA、panel map 或 display reviewer hint。 | Light 期刊规格、font defaults 和 panel examples 只作 watch/adopt template；缺 export / panel ref 只在当前 figure claim、caption disclosure 或 publication hard gate 需要时升级。 |
| bounded mode registry | skill / app entrypoint 的小任务档位约束。 | mode registry 不是 MAS route table；stage/action/dispatch 仍以 MAS pack、controller 和 OPL current-control 为准。 |

缺 Light-derived advisory 默认只算 observability / platform repair；只有当前 delta 明确 route-required ref 缺失，并且缺失影响 source/data/evidence、owner-route identity、forbidden write boundary、irreversible mutation 或 reviewer/publication hard gate 时，才能生成 typed blocker。该 blocker 必须命名缺失 ref family，并指明解除 owner。

## Progress-first safety envelope

`contracts/progress_first_safety_envelope.json` 是当前 MAS / OPL 普通推进的安全信封。它的目标不是增加一轮 preflight，而是把高代价漂移提前固定成可测试不变量：什么能关闭、什么只能提示、什么必须 fail closed。普通 live path 仍只走 `current_owner_delta -> current medical stage goal -> concrete paper / evidence / reviewer / gate delta -> ProgressDeltaReceipt / OwnerReceipt / TypedBlocker -> next current_owner_delta`。

五类风险按以下方式排查和预防：

| risk | 典型失败形态 | 预防口径 |
| --- | --- | --- |
| `false_completion` | script success、queue completion、provider completion、generated surface ready、score / ranking 或 executor 自审被写成完成。 | 只有 MAS owner receipt、stable typed blocker、human gate、route-back、independent reviewer/auditor record、publication gate receipt 或 canonical paper/artifact delta 能改变推进状态；其他信号只能做 evidence / diagnostic。 |
| `pseudo_evidence` | refs-only ledger、旧日志、sidecar memory、外部分数或 copied summary 被当成 source/evidence/reviewer/publication truth。 | evidence 必须以 source / evidence / review / decision-trace / failed-path / fresh-evidence / receipt / blocker ref 进入；缺 route-required ref 时生成命名 ref family typed blocker，非必需 advisory 缺失不阻塞。 |
| `stale_read_model` | 旧 projection、旧 action queue、Stage Native `next_action`、stale current-control 或 consumed dispatch 重新进入默认路径。 | default path 只从 canonical `current_work_unit` 派生；旧读面只能进入 ignored diagnostic / provenance，不能创建第二下一步。 |
| `duplicate_receipt` | 已消费 receipt、重复 readiness surface 或旧 work unit 被再次 dispatch。 | receipt 必须绑定 study / quest / stage / work-unit id / fingerprint / action / source fingerprint / idempotency key；消费后必须让位给 next owner、typed blocker、human gate、running proof 或 stop-loss。 |
| `artifact_authority_drift` | file presence、manifest、locator index、lifecycle report、restore plan、Workbench view 或 current package path 被当成 artifact mutation / publication 权限。 | artifact authority 只能来自 artifact package authority receipt、rebuild / lineage proof、owner-authorized mutation receipt 或 stable artifact blocker；locator / lifecycle 更新默认只算 platform repair。 |

这五类检查属于 contract / meta / explicit audit lane，不是每个 owner delta 的 live preflight。普通 executor 只做 JIT 检查：当前 delta 需要的 source/data/evidence、owner-route identity、forbidden write boundary、不可逆 mutation 授权和 reviewer/publication hard gate。未命中这些 hard gate 时，继续推进 current owner action。

## 无摩擦混合模式

Light、Co-Scientist 和 EvoScientist / EvoSkills 的吸收方式统一为 `current_owner_native_jit_affordance`。默认 ordinary path 没有常驻 sidecar、没有每轮 advisory scan、没有默认 tournament、没有默认 meta-review、没有默认 prefetch 或 memory scan；系统只推进当前 `current_owner_delta`。

这些机制只在当前 owner action、owner route、route-back、typed blocker、independent reviewer / publication gate 或 stop-loss 判断显式声明，或 current delta / gate 形态本身隐含需要某个 ref family、repair context、briefing 或 arbitration 时即时调用：

- Light 是外部 pattern ref library；只在当前 delta 需要时读取基础 advisory refs，或读取 source / data / citation / PRISMA / figure / experiment / statistics / overclaim / argument / style 等 optional skill-content refs。
- Co-Scientist 是 stage 内 strategy affordance；只在当前 owner 显式要求或 current delta 形态隐含需要候选、对比、ranking、evolution、meta-review 或 overview 时产出对应 refs。
- EvoScientist / EvoSkills 是 learning / tool affordance pattern；只在当前 owner 显式要求或 current delta 形态隐含需要工具提示、失败路径复用、observation ref 或 stop-loss hint 时调用。

每次即时调用必须绑定 current work-unit identity、target surface、requested ref family / question、owner policy、bounded output shape 和 `no_new_default_next_action`。调用缺失、失败、超时、低置信或没命中 memory 时默认 no-op，继续 current owner action；它不得回退成“先把外部 skill map / memory / tournament / prefetch 补齐再推进”的流程。

数量上限只是已触发即时调用后的扩散上限，不是低摩擦的设计来源。低摩擦来自能力默认可用、额外流程默认不运行、current delta 显式或由形态隐含需要时自动触发：只有当前 delta 需要、且缺失会影响 source/data/evidence、owner-route identity、forbidden write boundary、不可逆 mutation，或独立 reviewer / publication gate 时，才升级为 typed blocker。升级后的 typed blocker 必须命名缺失 ref family、route-back owner、current work-unit identity、repair condition 和 avoided forbidden shortcut。

## AI-first admission

AI-first 的 admission 锚点是 `current_executable_owner_action`，不是 `next_system_action` 文案。

当 `current_executable_owner_action` 已同时具备以下字段，且 hard gate 缺席时，Progress-first operator 必须把下一步交给 OPL/provider/scheduler 或 MAS owner callable：

- current owner。
- controller action / allowed action。
- work unit id 或 work-unit fingerprint。
- required output surface。
- source refs，包括 truth/runtime/source/eval currentness basis。
- allowed write boundary 与 forbidden write boundary。
- dispatchable owner-route attempt envelope。

`provider_attempt_start_requested` / `admission_requested` 表示可交给 provider 或 owner callable；它不是 running proof。只有 OPL current-control 明确 `running_provider_attempt=true` 且存在 active stage attempt、run 或 workflow ref 时，才能写成 `provider_attempt_running_proven=true` 或 `running`。

如果 admission request 已写出但缺 running proof，下一 owner 是 OPL worker / scheduler / provider attempt admission。不要把控制权退回 MAS receipt reconcile、read-model hydration、telemetry completeness、doctor explanation 或 operator wording review。

若同一 study 同时存在 provider admission candidate 与 blocked managed action，必须先读 dispatch / DHD action 上的 `execution_gate`。`execution_gate.gate_kind=developer_supervisor` 且 `blocked=true` 时，provider admission 状态是 `pending_but_execution_gate_blocked`，`running_provider_attempt=false`，解除 owner 是 developer-supervisor / user config / repo-write policy 对应的授权路径；不得把它读成 OPL idle bug、provider running、queue redrive 请求或论文进展。default executor dispatch 应同时暴露 `provider_admission_effect=not_admitted_until_execution_gate_clears`，让 operator 明确 candidate 已存在但不能 hydrate / tick / redrive。

Provider admission pending 必须由强 identity 判断，不能由 `action_id`、action family、旧 queue label 或 handoff 文案判断。强 identity 至少包含 study、action、work-unit id / fingerprint、dispatch ref、`route_identity_key`、`attempt_idempotency_key` 和 strong `owner_route_currentness_basis`。缺这些字段时，operator outcome 是 currentness diagnostic / typed blocker candidate，不是可启动 provider admission。

strict running proof 一旦成立，operator 顶层读面必须进入 `runtime_running_watch`：canonical `current_work_unit` / `current_execution_envelope` / `progress_first_monitoring_summary` 或 OPL handoff 任一面给出 `running_provider_attempt`，且同一 active stage attempt 没有 terminal closeout 时，`current_stage` 应显示 `managed_runtime_active`，`active_run_id` 应保留 provider attempt ref，parked / preflight / release-resource 字段只能作为被 supersede 的诊断，不得留在 `operator_status_card` 的默认面。该状态的唯一动作是监督当前 attempt；不要重复 DHD apply、hydrate、tick 或 queue redrive 同一 work unit。

`not_running`、`stopped`、terminal workflow completed、queue completed、default executor `handoff_ready` 和旧 active/run 字段都不是 running proof。workflow completed 也不算论文进展；只有 DHD apply 或等价 MAS authority consumer 消费 terminal closeout 后，fresh `study progress` 产生 owner receipt、typed blocker、paper/artifact delta、reviewer/gate delta 或 next handoff，才计入对应 Progress-first outcome。

attempt terminal completed 后，即使旧 read-model 仍残留 `active_run_id` 或 `running_provider_attempt=true`，matching terminal closeout 必须压过 running projection。`study_progress` 只负责显示 terminal-aware read model；它不消费 closeout。消费 closeout、释放旧 handoff、推导唯一 next owner / typed blocker / changed surface 的入口仍是 `runtime domain-health-diagnostic --apply` 或同等 MAS authority consumer。

2026-06-12 DM002 / DM003 运行态监督口径：若 fresh `study progress` 与 `domain-health-diagnostic --dry-run` 同时显示 `active_run_id=null`、`running_provider_attempt=false`、`provider_admission_pending_count=0`、`provider_admission_candidates=[]` 和 `action_queue=[]`，当前论文线没有 active provider work。DM002 类 `anti_loop_budget_exhausted` 按 `terminal_stop_loss` / `blocked_with_typed_owner` 处理，DM003 类 `medical_paper_readiness_missing` 按 current typed blocker 处理；下一步归 blocker owner、human/operator gate、route-back、新 work-unit identity 或 owner receipt，而不是继续同一 `run_quality_repair_batch`、heartbeat 或 quest-running 读面。

fresh `current_work_unit.status=typed_blocker` 或 `current_execution_envelope.typed_blocker` 先于旧 `domain_transition`、旧 current-control queue 和 stale StageRun projection 裁决。旧 transition 只有在没有 fresh typed blocker、或存在同 currentness identity 的合法 readiness / repair follow-up action 时才可 materialize；否则只进 ignored diagnostic，不触发 OPL tick。

`medical_paper_readiness_missing` 的旧 envelope / queue / handoff 不能单独授权 stage-native repair redrive。只有 canonical `current_work_unit` 同时满足 `status=typed_blocker` 或 `state.state_kind=typed_blocker`、`work_unit_id=complete_medical_paper_readiness_surface` 或空、且 `state.stale_queue_or_handoff_can_override` 非 true 时，带 authority binding 的 stage-native `run_quality_repair_batch` / `run_gate_clearing_batch` 才能被视为从 readiness blocker 派生。若 fresh barrier 缺 current-work-unit readiness identity，或 current work unit 已标记 stale override，operator outcome 是 currentness/platform repair diagnostic；下一步必须等 DHD / MAS authority consumer 产出新的 current work unit、owner receipt、typed blocker、human gate、route-back 或 owner-authorized next action。

Codex 前台会话的硬边界是 MAS/OPL 采信权，不是物理编辑能力。前台或人工可以在文件层手改 manuscript / package，但没有 MAS owner callable、OPL StageRun context、owner receipt、quality gate receipt、stable typed blocker、human gate、route-back evidence、同一 current identity 的 strict provider running proof，或被 MAS/OPL 消费的 canonical changed surface ref 时，`study_progress`、`current_work_unit`、provider admission 和 recovery claim 必须把这些旁路结果当作 ignored diagnostic，而不是论文线恢复。前台会话的 ordinary role 是读取 live truth、修改 repo contracts/docs/tests、补缺失 MAS owner callable / current-work-unit-bound derived repair action，或监督 OPL StageRun / provider attempt。

Terminal `stage_artifact_index.next_owner_action=publication_handoff_owner_gate` 已具备完整 current owner action 时，Progress-first admission 的下一步是 OPL provider execution authorization / attempt lease / closeout receipt binding，随后才由 MAS owner callable 产出 `handoff_owner_receipt.json` 或 `receipts/typed_blocker.json`。缺少这组 OPL binding 时，operator outcome 应是 `blocked_with_typed_owner`，typed blocker owner=`one-person-lab`，reason=`opl_execution_authorization_required`；不得退回旧 writer repair、旧 gate replay、generic owner-route hydration 或 repeat receipt reconcile。

## DM002 / DM003 recovery execution boundary

DM002 / DM003 recovery 的执行边界固定为 MAS owner callable / domain-handler dispatch / OPL StageRun provider attempt。Codex 前台会话可以读 live truth、改 repo docs/contracts/tests、实现缺失的 MAS owner callable 或 derived repair action、运行验证和监督 StageRun；它不能把绕过 MAS/OPL 的 manuscript、package、runtime-owned study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、OPL queue 或 provider attempt 修改写成可采信 recovery。若发现缺少 callable，结论是补 repo-level callable / repair action 或输出 typed blocker，不是 paper-local shortcut。机器合同见 `contracts/stage_route_reconcile_contract.json` 的 Codex executor route policy。

recent non-authoritative recovery sample（debug context only）：

下表只记录 2026-06-13 的近期样本，用于说明 operator 应如何读 blocker / admission / running proof；它不是当前 truth，也不能用于 acceptance。每次监督、恢复或验收前必须 fresh 读取 `study progress`、DHD `--dry-run`、OPL current-control / attempt ledger，并按 `contracts/stage_route_reconcile_contract.json#/dm002_dm003_recovery_acceptance_policy` 的 fresh truth / readback policy 裁决。

| study | recent sample | owner | ordinary recovery |
| --- | --- | --- | --- |
| DM002 | `anti_loop_budget_exhausted`，`provider_admission_pending_count=0` | `one-person-lab` | stop-loss 已生效；不得同 work-unit redrive。只能等 successor work-unit / StageRun identity、human gate、route-back evidence、新 owner receipt / quality gate receipt，或新的 stable typed blocker identity。 |
| DM003 | `medical_paper_readiness_missing`，`provider_admission_pending_count=0` | `MedAutoScience` | readiness blocker 必须被具体 MAS owner callable、带 current-work-unit binding 的 derived repair action、命名缺失 ref family 的 stable typed blocker，或 human gate 消费。blocker-only 不得自授权执行 `complete_medical_paper_readiness_surface`。 |

禁止路径包括：前台 Codex 直接“修论文”、重放旧 provider admission、同 work-unit default-executor dispatch、旧 gate replay、用 `active_run_id` / provider completion / queue empty 证明恢复、手写 runtime/study artifact，或把 docs-only 结论当 live paper progress。

recovery 验收必须至少读回以下证据族之一：MAS owner receipt、quality gate receipt、canonical changed surface ref、stable typed blocker、human gate、route-back evidence，或同一 current identity 的 strict provider running proof。验收 readback 必须包含 DM002/DM003 fresh `study progress`、DHD `--dry-run`、`provider_admission_pending_count`，以及 owner receipt / typed blocker refs；缺这些证据时只能说 docs/contracts 已更新，不能说 paper-line 已恢复。机器合同见 `contracts/stage_route_reconcile_contract.json#/dm002_dm003_recovery_acceptance_policy`。

## Hard gates

preflight 只保留以下 hard gates：

- `human_gate`：需要用户、PI、医生、外部编辑或显式 approval/resume。
- `developer_supervisor_execution_gate`：当前 owner action / provider admission candidate 已存在，但 developer-supervisor mode、user config、GitHub user gate 或 repo-write policy 未满足 `developer_apply_safe`；解除者是 developer-supervisor 授权路径，不是 OPL hydrate / tick / redrive。
- `opl_execution_authorization_required`：当前 owner action 已可 dispatch，但缺 OPL provider attempt、attempt lease、execution authorization decision 或 closeout receipt binding；owner=`one-person-lab`，解除者是 OPL provider admission / lease / closeout binding。
- `forbidden_authority_write`：当前 action 会写 MAS 禁止 surface，例如未授权的 study truth、runtime-owned state、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission/current package 或非当前 owner 的 paper surface。
- `missing_owner_callable`：当前 owner/action 没有可调用 MAS owner callable、domain-handler dispatch 或 OPL provider entry。
- `missing_source_or_data`：当前 work unit 的必需 source/data/evidence ref 缺失，无法形成 owner output 或 typed blocker。
- `irreversible_mutation`：会执行不可逆数据、artifact、submission、cleanup、external side effect 或权限变更，需要显式授权。

不属于 hard gate 的缺口必须单独列为 observability/platform repair：telemetry 缺失、token/cost 缺失、read-model 字段不完整、Portal 文案漂移、diagnostic completeness、低信息 scheduler tombstone、当前性解释缺口。只有这些缺口影响 owner-route identity、required source/data 或 forbidden write boundary 时，才按对应 hard gate 归类。

## DM002 / DM003 stable verification commands

以下命令只读或 MAS controller-authorized；运行前先确认 profile 指向 DM-CVD workspace，不要手写 DM-CVD workspace truth。若 workspace root 下没有已持久化 profile，先用临时 profile 运行只读 smoke；临时 profile 只描述 workspace 路径，不写 study truth、runtime-owned state、paper、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 package。

```bash
rtk git status --short --branch
```

```bash
DM_CVD_ROOT=/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk
DM_CVD_PROFILE="$(mktemp "${TMPDIR:-/tmp}/dm-cvd-mas-profile.XXXXXX.toml")"
cat >"${DM_CVD_PROFILE}" <<'EOF'
name = "dm-cvd-mortality-risk-workspace"
workspace_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk"
runtime_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/runtime/quests"
studies_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies"
portfolio_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio"
default_publication_profile = "general_medical_journal"
default_citation_style = "AMA"
enable_medical_overlay = true
EOF
```

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile "${DM_CVD_PROFILE}" \
  --study-id 002-dm-china-us-mortality-attribution \
  --format json
```

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile "${DM_CVD_PROFILE}" \
  --study-id 003-dpcc-primary-care-phenotype-treatment-gap \
  --format json
```

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic \
  --profile "${DM_CVD_PROFILE}" \
  --studies 002-dm-china-us-mortality-attribution 003-dpcc-primary-care-phenotype-treatment-gap \
  --request-opl-stage-attempts \
  --dry-run
```

上述 dry-run 是只读 admission/status smoke。`--request-opl-owner-route-reconcile` 是安全推进 tick，CLI 要求显式 `--apply`，避免 operator 把会写 refs-only reconcile/materialize/dispatch surface 的动作误当成纯只读检查。

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic \
  --profile "${DM_CVD_PROFILE}" \
  --studies 002-dm-china-us-mortality-attribution 003-dpcc-primary-care-phenotype-treatment-gap \
  --request-opl-stage-attempts \
  --request-opl-owner-route-reconcile \
  --apply
```

Use `--apply` only when the lane is explicitly allowed to drive MAS controller refs-only owner-route reconcile/materialize/dispatch. It must not write runtime-owned study truth, canonical paper body, `publication_eval/latest.json`, `controller_decisions/latest.json`, submission/current package, memory body or artifact body outside MAS owner-authorized surfaces.

When validating a docs-only change in this repo, use documentation review plus git diff/status. Do not run live `--apply` only to prove this runbook.

## Durable closeout template

以下模板用于 docs/runbook/closeout lane 交接。它只记录 repo 文档改动、验证证据和后续 owner；不得手写 live study truth、runtime-owned state、canonical paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal/`、`manuscript/current_package/` 或 submission package。

```markdown
### Artifact-first MVP closeout

- Scope:
  - Updated docs:
  - Source-of-truth surfaces read:
  - Explicit non-write surfaces:
- Artifact-first rule landed:
  - Stage artifact refs / `stage_artifact_index` are the MVP progress core:
  - typed closeout / read-model / currentness / evidence-tail / provider liveness are enhancement, audit, or scheduling layers:
  - OPL App workbench displays refs-only and does not write MAS truth:
- Landed commits:
  - <main session fill>
- Verification evidence:
  - documentation review:
  - git diff/status:
  - optional docs/link check:
- Residual risk / next owner:
  - <main session fill>
```

### Artifact-first MVP closeout - 2026-06-03 repo integration

- Scope:
  - Updated docs: `docs/active/stage_surface_standardization_program.md`, `docs/runtime/control/progress_first_stage_outcome.md`, `docs/active/opl_app_mas_runtime_workbench_program.md`.
  - Source-of-truth surfaces read: `agent/stages/stage_route_contract.yaml`, `contracts/stage_control_plane.json`, progress-first controller/projection tests.
  - Explicit non-write surfaces: no live study truth, runtime-owned state, canonical paper body, `publication_eval/latest.json`, `controller_decisions/latest.json`, `paper/submission_minimal/`, `manuscript/current_package/`, or submission package was edited.
- Artifact-first rule landed:
  - Stage artifact refs / `stage_artifact_index` are the MVP progress core and are projected into study progress, Progress Portal, and OPL domain-pack workbench descriptors.
  - typed closeout / read-model / currentness / evidence-tail / provider liveness are enhancement, audit, or scheduling layers.
  - OPL App / workbench surfaces display refs-only stage artifacts and cannot write MAS truth, publication readiness, quality verdict, paper body, or package outputs.
  - 2026-06-03 stage-native contract follow-through: `stage_artifact_index` now projects stage folder contract, manifest requirements, receipt requirements, and fail-closed artifact classification. 2026-06-03 physical kernel follow-through: MAS now declares and consumes the OPL physical Stage Folder Kernel locator from `contracts/mas-paper-study-stage-pack.json`, reading `current.json`, stage `latest`, attempt `manifest.json`, receipt file, manifest hash refs, lineage refs, and conformance refs from `OPL_STATE_DIR/runtime-state/domains/med-autoscience/deliverables/mas-paper-study/<study_id>/paper-study`. Legacy declared refs can still seed migration / historical projection, but missing OPL physical manifest, receipt, hash, or pointer keeps the artifact out of current progress.
- Landed commits:
  - `1878effb` Add artifact-first stage index kernel.
  - `43e80918` Prioritize artifact-first owner actions in progress monitoring.
  - `792b2230` Project artifact-first stage index to workbench surfaces.
  - `49d43aa3` Document artifact-first MVP runtime rules.
  - Integration cleanup commit keeps line-budget advisory reporting clean by moving runtime storage maintenance tests to a cases module and extracting artifact-first monitoring helpers.
- Verification evidence:
  - `rtk scripts/run-pytest-clean.sh tests/test_stage_artifact_index.py -q` -> 4 passed.
  - `rtk scripts/run-pytest-clean.sh tests/study_progress_cases/current_executable_owner_action.py -q` -> 18 passed.
  - `rtk scripts/run-pytest-clean.sh tests/study_progress_cases/stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_review_opl_projection_reference.py -q` -> 5 passed.
  - `rtk scripts/run-pytest-clean.sh tests/test_product_entry.py -q -k stage_control_plane_descriptor` -> 1 passed, 105 deselected.
  - `rtk scripts/run-pytest-clean.sh tests/test_runtime_storage_maintenance.py -q` -> 31 passed.
  - `rtk make test-meta` -> 282 passed, 4193 deselected.
  - `rtk scripts/verify.sh` -> repo hygiene audit passed; smoke entrypoints / line budget advisory tests passed.
- Residual risk / next owner:
  - This closeout does not declare any study publication ready, submission ready, or final paper quality ready.
  - DM002/DM003 live-study smoke remains read-only follow-through evidence, not a prerequisite for the repo-level artifact-first MVP integration.

### Stage-Native Artifact Operating Layer closeout - 2026-06-04 repo integration

- Scope:
  - Updated docs: `docs/active/mas-ideal-state-gap-plan.md`, `docs/active/stage_surface_standardization_program.md`, `docs/runtime/control/progress_first_stage_outcome.md`.
  - Updated contract: `contracts/stage_artifact_kernel_adoption.json`.
  - Updated source/projection: state index kernel, semantic receipt validator, promotion audit helper, lineage / retention drilldown, study progress `stage_kernel_projection`, Progress Portal / Workbench `stage_operating_layer`.
  - Explicit non-write surfaces: no live study truth, runtime-owned state, canonical paper body, `publication_eval/latest.json`, `controller_decisions/latest.json`, `paper/submission_minimal/`, `manuscript/current_package/`, memory body, artifact body, submission package, or OPL `current.json` was edited.
- Operating-layer rule landed:
  - `stage_artifact_index` remains a rebuildable derived locator projection.
  - `stage_kernel_projection` is the primary Workbench progress source and now exposes `state_index`, `promotion`, and `lineage_retention` drilldowns.
  - Semantic receipt validation is body-free and fail-closed; typed blocker is a domain outcome, not runtime failure.
  - Promotion audit is read-only and cannot promote or rewrite current pointer.
  - Lineage / retention drilldown never authorizes cleanup; cleanup / restore still needs owner-authorized receipt.
  - Workbench cross-domain soak is display-only and cannot authorize MAS/MAG/OMA/RCA readiness or artifact mutation.
- Verification evidence:
  - `rtk scripts/run-pytest-clean.sh tests/test_opl_state_index_kernel.py tests/test_opl_stage_promotion_runtime.py tests/test_mas_stage_semantic_receipts.py tests/test_opl_stage_lineage_retention.py tests/study_progress_cases/stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_kernel_cross_domain_soak_projection.py tests/test_stage_artifact_kernel_adoption_contract.py -q` -> 25 passed.
  - Full verification and final commit id are recorded by the main session after absorb / cleanup.
- Residual risk / next owner:
  - This closeout does not declare any study publication ready, submission ready, final paper quality ready, memory writeback success, artifact mutation authorization, or live provider long-soak completion.
  - Remaining evidence tail is real paper-line owner delta, independent reviewer/auditor scaleout, live cross-domain soak, human gate / resume and owner-authorized artifact lifecycle apply.

## 错误路径

不要再走以下路径：

- 把 `active_run_id` 当作 running proof。running proof 只来自 OPL current-control / runtime liveness 的 `running_provider_attempt=true` 和 active attempt/run/workflow ref。
- 把 `next_system_action` 文案当作 admission authority。authority 必须来自 `current_executable_owner_action` 与 owner-route attempt envelope。
- 把 `receipt_consumed` 显示成 `ready_owner_action` 或等待 owner pickup。它应触发下一 owner projection 或暴露 currentness 缺口。
- 在 provider-hosted `paper/review` closeout 已证明 story-surface delta materialized 后，继续导出同一个 `run_quality_repair_batch` writer handoff。应消费 receipt、退役 handoff，并投影下一 owner。
- 在 materializer 已消费旧 writer handoff 后，dispatch selector 仍从 persisted/consumer dispatch fallback 执行同一个 `run_quality_repair_batch`。应过滤已消费 handoff，并执行当前 owner action。
- 在 default executor execution receipt 已证明同一 owner route 的 `run_quality_repair_batch` 产生 paper/artifact delta 后，dispatch selector 仍把同一个普通 consumer dispatch 当作 ready action。应消费 execution receipt 并等待/投影下一 owner，不能重复 repair。
- 在 OPL provider attempt 已 terminal 且 `default_executor_execution` 带同 action / work-unit / fingerprint closeout refs 后，仍把旧 `opl_runtime_handoff_required` 当作当前 queued/handoff truth，或继续等待 provider 持续运行。应关闭旧 handoff，交还 MAS current work-unit reducer 重新给出唯一 next work unit。
- 在 progress projection 已证明 fresh meaningful paper/artifact delta 且当前 owner action 仍可执行时，继续把旧 `progress_first_owner_redrive_budget_exhausted` 当作当前 typed blocker。应标注 stale superseded 并推进 owner action / handoff / provider admission。
- 当 study-level `owner_route` 是非 dispatchable placeholder，而 `action_queue` 已有当前 owner action route 时，仍让默认 dispatch 返回空 execution。应让 action-queue route 成为当前 dispatch authority，不能继续重复 read-model reconcile。
- 当 consumed `domain_transition.controller_action` 已指向下一 owner action，且 consumer dispatch 已 ready，但 `action_queue` 暂空时，仍因 consumed transition 非空而清空 fallback dispatch。应按 consumed-transition owner action bridge 执行当前 dispatch，不能让论文推进等待下一轮同义 reconcile。
- 在 `ai_reviewer_record_production_handoff` persisted dispatch 已存在后，继续让 stale `consumer/latest.json` inline dispatch 覆盖它，导致重复写 handoff 而不是把 AI reviewer record-production owner action 交给下一 owner。应优先 persisted record-only handoff，并把旧 inline 当作 read-model lag。
- 把 provider handoff 写出当作 provider attempt 已启动。缺 running proof 时只能写 `provider_handoff_written_admission_pending`。
- 把 telemetry、duration/token/cost、Portal card wording、read-model hygiene、refs-only ledger record/verify 当成 paper progress。
- 把 `provider_admission_pending_count>0` 但 `execution_gate.blocked=true` 的状态当成 running、idle bug 或 hydrate/redrive 请求。应先解除 developer-supervisor / user config / repo-write gate，或记录 typed blocker / human gate。
- 把 `paper_stage_log` 中补齐的 duration/token/cost 当成论文产出或 quality verdict。它只是 terminal stage accounting 的 observability fallback。
- 把 `next-delta tournament`、`bounded micro-candidate generation`、`critique-as-repair-hint`、`reusable lesson extraction`、`triggered meta-review` 或 `opportunistic knowledge prefetch` 当成 admission gate、route blocking layer、quality closure、publication readiness、artifact authority 或 paper progress。它们只能在当前 owner / gate 明确需要时辅助 route selection、reviewer gap finding 和 failed-path memory reuse。
- 把 Light 的 skill router、`db09`、知识库、verification log、review score、自审 checklist 或外部 API 表当成 MAS runtime、study truth、source readiness truth、AI reviewer verdict、publication gate、artifact authority、paper progress 或默认 dispatch blocker。Light-derived signal 只能作为 bounded advisory ref；缺失时不得阻塞不相关 owner action。
- 用显式 `--action-types` 作为正常 Progress-first 必需步骤；它只用于诊断、限流或人工指定，默认 dispatch 必须消费 current ready dispatch。
- 用 broad recursive scan、mtime、旧 request lifecycle、旧 generated_at、stale consumer dispatch 或旧 package freshness proof 覆盖当前 owner/work-unit currentness。
- 手工写 DM-CVD study truth、runtime-owned state、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal/`、`manuscript/current_package/` 或 submission package 来关闭 currentness 问题。
- 把 repo-side docs/code fix landed 推断成 live study 已恢复。每次状态判断都必须重新读取 live study/runtime surfaces。
