# 关键决策记录

## 2026-05-22：owner dispatch currentness 必须同时消费 scan action_queue route 与同路径 dispatch 版本

- 决策：`domain-owner-action-dispatch` 解析当前 owner route 时，不能只读取 `artifacts/supervision/hourly/latest.json` 的 `studies[*].owner_route`。当当前 scan 将可执行 route 写在同一 study 的 `action_queue[*].owner_route` 上，且该 route 与 dispatch 的 idempotency/source/currentness basis 匹配并允许对应 action 时，必须作为 current owner route 执行。
- 决策：显式 `--action-types` 执行遇到同一 `refs.dispatch_path` 同 action 的 workspace consumer inline dispatch 与 study-level persisted dispatch 不一致时，选择规则必须按当前 scan owner route 和 paper-progress stall fingerprint 判定 currentness。当前版本优先于存储位置；不能固定“consumer latest 优先”或“persisted 文件优先”。
- 决策：managed-runtime 授权生成的 `unit_harmonized_external_validation_rerun` owner route 是合法 hard-methodology dispatch reason，必须在 owner reason registry 中保持可 dispatch，不得因 action-type alias 缺失把 `allowed_actions` 清空。
- 理由：DM003 暴露出 owner-route reconcile 正确投影 `return_to_ai_reviewer_workflow`，materializer 也物化了 dispatch，但 dispatcher 只看 study-level `owner_route`，忽略 `action_queue[*].owner_route`，导致合法 AI reviewer workflow 被 `current_owner_route_missing` 阻断。同期 DM002 覆盖了相反形态：consumer inline 可能旧、persisted 文件可能新；DM003 又覆盖了 persisted 文件旧、consumer inline 新。共同根因是 dispatcher 按存储位置判断 currentness，而不是按当前 scan/owner-route 证据判断。
- 影响：这是 MAS owner dispatch read-model/currentness 修复，不写任何 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。它只保证当前 owner-authorized action 能进入对应 owner callable；论文质量仍由 owner output、AI reviewer-backed publication eval 和 publication gate 判定。

## 2026-05-22：owner-route 必须清理已由当前 AI reviewer eval 关闭的 stale-record lifecycle

- 决策：`owner-route-reconcile` 遇到旧 `ai_repair_lifecycle.blocked_reason=ai_reviewer_record_stale_after_current_manuscript` 或 `ai_reviewer_record_stale_after_unit_harmonized_rerun` 时，若当前 `publication_eval/latest.json` 已投影为 present 的 AI reviewer-owned assessment，必须把该旧 lifecycle 和 `why_not_applied` 一并清空，不得继续保留 `next_owner=ai_reviewer`、`allowed_actions=[]` 的死锁 read-model。
- 决策：该清理只适用于当前 AI reviewer assessment 明确 present 且 owner 为 `ai_reviewer` 的路径；stable AI reviewer request 仍处于 requested/assigned，或仍缺 currentness proof 时，继续按 stale-record blocker 路由到 AI reviewer。
- 理由：DM002 暴露出 stale-record request lifecycle 已被新的 AI reviewer publication eval/currentness proof 消费后，owner-route 仍从旧 `ai_repair_lifecycle` 和 progress projection 中复活 stale blocker，导致 write route-back 无法继续推进。根因是 MAS owner-route read-model 的 resolved-currentness 清理缺口，不是 OPL queue/provider lifecycle，也不是单篇论文可手工 patch 的内容问题。
- 影响：这是 MAS owner-route / currentness read-model 修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。论文推进仍必须回到 MAS owner/controller/runtime 路径，并由 AI reviewer-backed eval、write owner delta 和 publication gate 判定。

## 2026-05-22：request-bound AI reviewer 复评必须绑定 live manuscript digest 与 stale-request currentness proof

- 决策：`request_bound_ai_reviewer_record` workflow 不得把既有 `medical_prose_review` record 直接标为 current；必须复用标准 medical prose currentness 校验，确认 request digest、manuscript ref、manuscript digest 与当前 live manuscript SHA-256 一致后，才允许物化 AI reviewer-backed `publication_eval/latest.json`。
- 决策：当 stable AI reviewer request 因 `ai_reviewer_record_stale_after_current_manuscript` 或 `ai_reviewer_record_stale_after_unit_harmonized_rerun` 被阻断时，lifecycle 只能由新的 AI reviewer-owned publication eval 关闭；该 eval 必须在 `reviewer_operating_system.currentness_checks` 中覆盖每个 `required_currentness_refs`，并且 ref 指向的 live file digest 与 currentness proof 一致。story-provenance leakage blocker 继续不可由 eval 自动消费。
- 理由：DM002 暴露出 stale medical prose review 可在 request-bound workflow 中绕过 live manuscript digest 校验，同时 lifecycle 对 stale-record blocker 一律不消费，导致系统既可能写出陈旧 AI reviewer eval，也可能在后续 owner-route 中空转。根因是 MAS AI reviewer currentness/read-model 合同缺口，不是 OPL queue/provider lifecycle，也不是单篇论文可手工修补的问题。
- 影响：这是 MAS AI reviewer workflow 与 request lifecycle read-model 修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。DM002 论文质量仍必须由更新后的 MAS owner/controller/runtime 正式推进，并以 AI reviewer-backed publication eval、write owner delta 与 publication gate 判定。

## 2026-05-22：AI reviewer record-production prompt 必须使用真实 request materializer CLI contract

- 决策：runtime turn prompt 中 `produce_ai_reviewer_publication_eval_record_against_current_*` 的后续 materializer 命令必须调用 `domain-action-request-materialize --mode developer_apply_safe --apply`，不得在该 subcommand 上生成已不受支持的 `--action-types return_to_ai_reviewer_workflow` 参数。action-specific dispatch 继续由随后的 `domain-owner-action-dispatch --action-types return_to_ai_reviewer_workflow --mode developer_apply_safe --apply --managed-runtime-worker` 承接。
- 理由：DM002 暴露出 AI reviewer managed worker 已成功物化 current publication-eval record，但 prompt 给出的 request materializer 命令与当前 CLI contract 漂移，导致 worker 先触发参数错误，再依靠读源码手动找到正确调用。根因是 MAS runtime prompt/CLI contract drift，不是 study truth、OPL queue/provider lifecycle 或单篇论文内容问题。
- 影响：这是 MAS runtime prompt contract 修复，不写 DM002 canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission-ready verdict。论文质量仍由 AI reviewer-backed `publication_eval/latest.json`、write owner delta 与 publication gate 判定。

## 2026-05-22：Owner-Route Attempt Protocol 统一 owner-route、currentness、reason registry 与 default-executor handoff

- 决策：MAS owner-route 控制层统一输出 `mas-owner-route-attempt-protocol.v1`。每条 owner route 必须携带 `owner_reason_contract`、`priority_lattice`、`currentness_contract` 和 `source_refs.owner_route_currentness_basis`；当前优先级固定为 hard methodology/source blocker、pending AI reviewer request、AI reviewer currentness、write route-back、package freshness、delivery/human handoff。
- 决策：`owner_reason_contract` 是 ready dispatch 的准入 registry。已登记 reason 才能生成可执行 handoff；未知 reason 在 owner route 上保留为 fail-closed blocker，并把 `allowed_actions` 清空。registry 现在覆盖 DM002/DM003 已暴露的 stale reviewer record、pending reviewer request、medical prose route-back、unit harmonization rerun、current package freshness、typed closeout / owner receipt pending 等 owner-chain reason。
- 决策：`domain_owner/default-executor-dispatch` pending task 必须导出完整 Owner-Route Attempt envelope：`domain_owner`、`action_type`、`work_unit_id`、`source_eval_id`（有 publication eval 时）、`source_fingerprint`、`owner_route_currentness_basis`、`allowed_write_surfaces`、`forbidden_surfaces`、`required_closeout_packet`、`completion_boundary` 和 `owner_reason_contract`。缺 registered reason、work-unit currentness、truth/runtime epoch 或 source fingerprint 时不进入 OPL pending task。
- 决策：OPL completion 继续只是 transport receipt。`required_closeout_packet` 和 `completion_boundary.provider_completion_is_domain_ready=false` 作为 handoff 硬合同输出；MAS 只有在消费 typed closeout refs 后才能产生 owner receipt、AI reviewer-backed eval、publication gate result 或 typed blocker。
- 理由：DM002/DM003 的症状分散在 stale AI reviewer record、旧 write route 抢 pending request、package freshness 和 typed closeout，但共同缺口是 MAS 没有统一的 owner-route / currentness / completion boundary 协议核。把 registry、lattice、currentness basis 和 default-executor envelope 收敛后，合法 owner route 可被 OPL 运输，未知或 stale route fail closed，不再靠局部 precedence 规则补洞。
- 影响：这是 MAS domain-control / handoff contract 修复，不写 DM002/DM003 study truth、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。OPL 当前 typed closeout、terminal sync、later redrive/accepted closeout 与 default-executor redrive owner 已有 focused coverage，本轮不修改 OPL。

## 2026-05-22：AI reviewer request currentness 不能只靠 stable latest path 消费

- 决策：当 `artifacts/supervision/requests/ai_reviewer/latest.json` 携带 `source_fingerprint` 时，AI reviewer-owned `publication_eval/latest.json` 不能仅因 `assessment_provenance.source_refs` 包含同一个 stable `latest.json` 路径就视为已消费该 request。消费证据必须显式携带同一 request fingerprint，或由 publication eval 逻辑时间不早于 request 时间证明。
- 决策：若 stable AI reviewer request 的 lifecycle 已携带 `ai_reviewer_record_stale_after_current_manuscript`、`ai_reviewer_record_stale_after_unit_harmonized_rerun` 或 manuscript story-provenance leakage blocker，旧 `publication_eval/latest.json` 的时间戳不得把该 request 投影为 `assessment_written`。owner-route 必须保留这些 blocker、`stale_record_ref` 与 `required_currentness_refs`，并把 record-production work unit 路由给 AI reviewer。
- 理由：DM002 暴露出 `quality_repair_batch` 覆写 stable AI reviewer request 后，旧 publication eval 仍引用同一路径，导致 request lifecycle 被误判为 `assessment_written`，owner route 不再派发 `return_to_ai_reviewer_workflow`。根因是 MAS currentness 判定把 stable path identity 当成了 content/version identity。
- 影响：这是 MAS request lifecycle / owner-route read-model 修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。论文质量仍由当前 AI reviewer-backed publication eval、owner receipt 与 publication gate 判定。

## 2026-05-22：当前 runtime-redrive route-back 优先于旧 progress active run 和 terminal package handoff

- 决策：当 `domain_transition.decision_type` 属于 `route_back_same_line`、`ai_reviewer_re_eval`、`publication_gate_blocker` 或 `bundle_stage_finalize`，且 status/liveness/truth 没有可靠 live worker 时，`study_macro_state`、`study-progress.user_visible_projection` 和 `owner-route-reconcile` 必须把当前 transition 投影为 owner repair 队列，不得从旧 `progress.supervision.active_run_id` 误判 live，也不得让旧 terminal delivery/package handoff 覆盖当前 route-back。
- 理由：DM002 暴露出 AI reviewer 已给出当前 write route-back 后，read model 仍可能同时显示 stale active run 或“当前包已经可直接交给用户审阅”，导致用户可见状态和 owner-route 与当前 publication_eval/quality route 不一致。根因是 MAS currentness/read-model precedence，而不是 OPL provider 或单篇稿件内容。
- 影响：这是 MAS study-progress / owner-route read-model 修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。论文质量仍由当前 write owner delta、AI reviewer-backed publication eval 与 publication gate 判定。

## 2026-05-22：AI reviewer domain transition 是 turn/resume/refresh currentness 的权威 fallback

- 决策：当 `progress_projection/status_payload.domain_transition` 明确为 `ai_reviewer_re_eval`、`controller_action=return_to_ai_reviewer_workflow`，且 `next_work_unit.unit_id=ai_reviewer_medical_prose_quality_review` 时，MAS 的 runtime turn prompt、resume/relaunch 前 controller-decision currentness、以及 AI reviewer workflow 后的 controller refresh 都必须把该 domain transition 作为权威 fallback。若 generic outer-loop tick request 因旧 `publication_eval`、`quality_repair_batch` 或 stale write route 返回 `medical_prose_write_repair` / `run_quality_repair_batch`，不得让旧 tick 覆盖当前 AI reviewer re-eval。
- 决策：`domain_transition_ai_reviewer_re_eval` 是上述 read-model transition 的稳定 owner-route reason，必须按 AI reviewer currentness reason 注册，允许 `return_to_ai_reviewer_workflow` 进入 request materializer 和 dispatch；不得因为 reason 名称不同于 `ai_reviewer_assessment_required` 而把当前 route 判为 unknown/stale。
- 决策：该 fallback 只适用于 AI reviewer re-eval domain transition；缺 stable study charter、缺 stable publication eval、缺 next work unit，或 `publication_supervisor_state.current_required_action=human_confirmation_required` / controller confirmation pending 时继续 fail closed，不绕过 human gate。
- 理由：DM003 暴露出 canonical story repair 已更新 `paper/draft.md` 后，read-model 正确投影 `domain_transition_ai_reviewer_re_eval`，但 runtime turn prompt 与 resume/refresh 路径仍通过旧 outer-loop tick request 吃到 `manuscript_story_repair` / `medical_prose_write_repair`，导致系统重复写作修复而没有进入 AI reviewer 复评。根因是 MAS currentness/authorization 使用了 stale generic tick，而不是 OPL provider 或单篇论文内容。
- 影响：这是 MAS runtime/controller authorization currentness 修复，不写 DM003 study truth、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。论文质量仍由后续 AI reviewer-backed publication eval 与 publication gate 判定。

## 2026-05-22：pending AI reviewer request 必须优先于旧 story/write route

- 决策：`ai_reviewer_request_lifecycle` 只能在 AI reviewer-owned `publication_eval/latest.json` 明确消费当前 `artifacts/supervision/requests/ai_reviewer/latest.json` 后进入 `assessment_written`。消费证据必须是 eval/provenance/source refs 包含该 request ref，或 eval 时间戳不早于 request 时间戳；缺 currentness evidence 时保持 request pending。
- 决策：owner-route reconcile 在 progress 尚未投影 `ai_reviewer_request_lifecycle` 时，必须直接从 stable AI reviewer request file 投影 lifecycle；pending request 要优先于旧 `route_back_same_line/write` story route，但仍排在 methodology/source-provenance/analysis-harmonization 等硬 blocker 之后。
- 决策：若 pending AI reviewer request 的 blocker 是 `ai_reviewer_record_stale_after_current_manuscript`，owner-route 必须把 `next_owner` 固定为 `ai_reviewer`，并保留 `stale_record_ref` 与 `required_currentness_refs` 进入 action packet；不得让旧 write/story residue 因 owner-route guard 把该 action 过滤为空。
- 理由：DM002 暴露出 `quality_repair_batch` 已物化新的 AI reviewer recheck request，但 stale AI reviewer eval 与旧 write route 继续抢占，导致系统重复派 `run_quality_repair_batch` 而没有回到 `return_to_ai_reviewer_workflow`。根因是 MAS request currentness 和 action priority，不是 OPL queue/provider lifecycle。
- 影响：这是 MAS owner-route/read-model currentness 修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。论文质量仍由当前 AI reviewer-backed publication eval、write owner delta 与 publication gate 判定。

## 2026-05-22：AI reviewer redrive controller decision 必须优先于旧 story-delta repair residue

- 决策：managed runtime turn prompt 在读取当前 `controller_decisions/latest.json` 时，若该 decision 是 runtime-authorizing 的 `return_to_ai_reviewer_workflow`，且 work unit 为 `ai_reviewer_recheck` / `ai_reviewer_medical_prose_quality_review` 或 fingerprint 以 `domain-transition::ai_reviewer_re_eval::` 开头，必须优先采用该 controller decision。旧 `quality_repair_batch/latest.json` 中仍与同一 `publication_eval/latest.json` 对齐的 `manuscript_story_surface_delta_missing` residue 不得抢占这类 fresh AI reviewer redrive。
- 决策：普通 story-surface delta blocker 仍可优先于 stale publication gate / gate-clearing decision；本规则只改变明确 AI reviewer redrive authorization 的 precedence，不把所有 controller decision 都提升到 story repair residue 之前。
- 理由：DM003 已完成 `medical_prose_write_repair` story-surface delta 后，study progress/domain transition 要求 `ai_reviewer_medical_prose_quality_review`，但 runtime prompt 被旧 story repair batch residue 抢成 `medical_prose_write_repair`，导致系统重复写作修复而没有进入 AI reviewer 复评。根因在 MAS runtime authorization precedence，不是 OPL queue/provider，也不是单篇论文内容问题。
- 影响：这是 MAS controller/runtime prompt authorization 修复，不写 DM003 study truth、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal` 或 `manuscript/current_package`。DM003 后续仍必须由 MAS runtime 重新进入 AI reviewer workflow，并以 AI reviewer-backed publication eval 与 publication gate 判定质量。

## 2026-05-22：workspace helper wrappers 必须绑定当前扁平 MAS CLI 入口

- 决策：workspace 初始化/升级生成的 `ops/medautoscience/bin/study-runtime-status` 必须直接调用当前 `progress-projection`，并把首个非 option 位置参数映射为 `--study-id`；`ops/medautoscience/bin/progress-portal` 与 `ops/mas/bin/start-web` 必须直接调用当前 `progress-portal`。workspace helper 不能依赖旧 `study-runtime-status` 命令或 grouped alias 作为稳定执行面。
- 理由：DM003 supervisor fresh check 暴露出 workspace helper 仍生成 `run_medautosci study-runtime-status` / `workspace progress-portal`，而当前实际 CLI 公共面已收敛为扁平命令。入口漂移会让前台监督误以为 MAS 没有可用状态面，进而退回手工命令或反复巡检。
- 影响：这是 MAS workspace entry surface 修复，不改变 study truth、runtime ownership、publication quality verdict 或 paper/package authority。Grouped commands 可继续作为 CLI public alias 存在，但 workspace helper 生成物要绑定可验证的当前命令。

## 2026-05-22：live managed lease 不能被 logical closeout 误清，medical prose closeout 要闭合 work-unit lifecycle

- 决策：`reconcile_stale_liveness` 遇到当前 run 已有 logical completion / closeout 时，必须先检查 run-scoped `worker_lease.json`；若该 run 仍有 fresh `monitor_state=live` managed lease 且 pid/heartbeat 判定为 live，则保持当前 run 为 live，不清 `active_run_id`、不终止 worker、也不把状态投影为 stale。真正无 lease、lease stale、旧非 managed stuck pid 或 orphan completed worker 仍按既有 cleanup/reconcile 规则处理。
- 决策：`medical_prose_write_repair` 与 `manuscript_story_repair` 同属 manuscript-facing story-surface work unit。completed closeout 若携带 `paper/draft.md` 与 `paper/build/review_manuscript.md` artifact refs，即使缺少 active-run/delivered-run marker，也可作为当前授权 work unit 的完成证据，被 `publication_work_unit_lifecycle` 采用并转回 publication gate recheck。
- 理由：DM003 暴露出两类会让论文质量推进失真的系统问题：一是 live MAS worker 正在修稿时，read model 可能因 closeout/receipt residue 把 active run 清成 `null`，诱发重复启动或误判停滞；二是 `medical_prose_write_repair` 已产生 manuscript surface delta 后，完成证据没有稳定闭合 work-unit lifecycle，导致相同写作修复被反复 redrive。修复必须落在 MAS runtime liveness / work-unit evidence adoption，而不是手工 patch DM003 paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal` 或 `manuscript/current_package`。
- 影响：该修复只改变 MAS owner-chain 对 live worker 与 completed manuscript repair closeout 的判定。DM003 是否达到高质量医学论文标准仍由当前稿件、AI reviewer-backed publication eval、publication gate、display/package freshness proof 与后续 MAS owner receipt 判定；本决策不声明论文 ready、不授权前台写 study truth，也不把 OPL generic runtime 职责回流给 MAS。

## 2026-05-22：completed writer closeout adoption 必须重建 repair execution evidence

- 决策：MAS 采纳 completed writer / work-unit closeout 时，必须把 closeout `artifact_refs` 作为 `repair_execution_evidence.changed_artifact_refs` 重建证据，并保留 closeout `source_refs` / `report_ref`。对 manuscript story/write repair，`paper/draft.md` 或 `paper/build/review_manuscript.md` 的 canonical story-surface delta 仍是必需完成证据。
- 决策：重建后的 evidence 只有在 evidence ledger、review ledger、publication gate replay 输入 ref 与 AI reviewer recheck request ref 都存在时，才允许成为 `progress_delta_candidate`；缺任一 owner ref 时继续 fail closed 为 pending/blocker。
- 理由：DM002/DM003 暴露出 Codex writer closeout 可以包含 canonical paper delta，但 MAS 只记录了 adoption/handoff，未把 delta 转成当前 `repair_execution_evidence`，导致后续 owner route/quality suite 仍把 write repair 当作未闭合。修复位置是 MAS owner evidence adoption，不是手工改 study truth，也不是放宽 publication gate。
- 影响：这是 MAS owner path / medical manuscript quality regression 修复，不写 DM002/DM003 canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission-ready verdict。正式质量结论仍由 AI reviewer-backed publication eval 与 publication gate 判定。

## 2026-05-22：Agent Lab 医学稿件质量 suite 必须投影 OPL 可消费的质量地板与 owner route refs

- 决策：`agent-lab-medical-manuscript-quality-suite` 生成的 refs-only suite 必须显式投影 `quality_floor_refs`、`owner_route_refs` 与 `failure_delta_refs`。这些 refs 至少覆盖 MAS 高质量医学稿件质量地板、当前 study 的 AI reviewer authority、write owner、publication gate，以及当前 prose/reviewer-feedback route-back 的 failure/evidence delta。
- 决策：该 suite 仍只允许 OPL / Agent Lab / opl-meta-agent 消费 refs、生成 developer patch work order、执行独立 review/canary 与 regression promotion 判断；不得把 OPL suite run、evolve 或 efficiency read-model 解释为医学质量 ready、publication verdict 或 study truth。
- 理由：DM003 暴露出 Agent Lab 能读取 MAS external suite，但 MAS suite 缺 OPL efficiency/evolution 可识别的质量地板、owner route 与 failure delta 证据组，导致“像高质量医学论文”的反馈无法稳定转化为可回归的 MAS 智能体能力缺口。正确修复位置是 MAS suite projection，而不是 OPL runner 放宽判断，也不是在 DM003 study surface 手工写入质量结论。
- 影响：这是 MAS Agent Lab medical manuscript quality suite / self-evolution projection 修复，不写 DM003 canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。论文质量仍由 MAS write owner delta、AI reviewer-backed publication eval 与 publication gate 判定。

## 2026-05-22：已消费 recheck request 的 AI reviewer route-back 优先于旧 story recheck

- 决策：`story_surface_recheck_transition` 只能在 completed story-surface delta 尚未被当前 AI reviewer eval 消费时投影 `return_to_ai_reviewer_workflow`。若 AI reviewer-owned `publication_eval/latest.json` 已有当前 `route_back_same_line` / `bounded_analysis` / `stop_loss` action，且 `assessment_provenance.source_refs` 明确包含 `repair_execution_evidence.ai_reviewer_recheck_request_ref`，domain transition 必须尊重当前 AI reviewer route-back owner。
- 理由：DM002 暴露出 canonical story repair 已触发 AI reviewer recheck，AI reviewer 随后给出新的 blocked/write route-back，但旧 `repair_execution_evidence.ai_reviewer_recheck_done=true` 仍让 story recheck transition 抢占，导致系统重复投 `ai_reviewer_re_eval` 而不能进入当前 write repair。
- 影响：这是 MAS read-model/currentness 修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。论文质量仍由当前 AI reviewer-backed route-back、write owner delta 与 publication gate 判定。

## 2026-05-22：medical overlay 必须物化 stage skill 引用的 companion block

- 决策：`install_medical_overlay` / `reapply_medical_overlay` / `materialize_runtime_medical_overlay` 在写入 stage `SKILL.md` 时，必须同步物化该 skill 依赖的显式 companion template，例如 `medical-research-stage-packet.block.md`。companion 依赖由 MAS overlay installer 中的显式 registry 持有，不通过扫描 Markdown 链接隐式推断。
- 决策：overlay status / runtime overlay audit 必须把 required companion block 纳入 readiness。已安装 overlay 的 `SKILL.md` 若匹配当前模板但 companion block 缺失或漂移，状态必须 fail closed 为 drifted，并由 reapply / materialize 修复；纯 upstream 未安装 skill 仍保持 `not_installed` 分类。
- 理由：DM003 write owner repair turn 暴露出 `medical-research-write/SKILL.md` 引用 `./medical-research-stage-packet.block.md`，但 runtime overlay 只物化 `SKILL.md` 和 manifest，导致 stage packet discipline 文件在 quest overlay 中悬空。worker 可退回显式 skill 文本继续工作，但这是 MAS stage-surface delivery 缺陷，不能靠单篇 study 手工补 runtime overlay 掩盖。
- 影响：这是 MAS overlay installer / stage skill surface 修复，不写 DM003 study truth、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal`、`manuscript/current_package` 或论文 ready verdict。论文质量仍由 MAS write owner delta、AI reviewer-backed publication eval 和 publication gate 判定。

## 2026-05-22：quality repair writer handoff 继承当前 owner route

- 决策：`quality_repair_batch` 生成 `quality_repair_batch_writer_handoff` 时，必须优先继承当前 dispatch/scan owner route；只有当 study、quest、next owner、blocked reason 与 allowed action 全部匹配时才可继承。不能用由 publication blockers 或内部 selected work unit 推导出的新 route 替换当前 owner route。
- 理由：DM002 暴露出 writer handoff 的 `quality-repair-writer-handoff::*` route 与当前 `run_quality_repair_batch` owner route 不一致时，study-level persisted dispatch 无法匹配 owner request，stale consumer inline dispatch 会再次抢占并触发 `paper_progress_stall_fingerprint_stale`。修复应保持 fail-closed currentness，不放宽 owner-route guard。
- 影响：domain owner dispatch 会把当前 owner route 传给 quality repair owner callable；writer handoff 继续只授权 Codex default writer attempt，不授权 MAS 直接改 `paper/submission_minimal`、`manuscript/current_package` 或 publication truth surface。

## 2026-05-22：default executor dispatch 必须显式要求 typed closeout packet

- 决策：所有 MAS `default_executor_dispatch_request`，包括 `run_quality_repair_batch` writer handoff 和通用 `domain_action_request_materializer` 生成的 Codex default executor dispatch，都必须携带 `required_closeout_packet`。该 contract 固定 `typed_closeout_required_for_completion=true`、`free_text_closeout_accepted=false`，并声明可接受的 `stage_attempt_closeout_packet`、`stage_memory_closeout_packet`、`domain_stage_closeout_packet` 形态和至少一个 `closeout_refs`。
- 决策：dispatch 的 `executor_prompt` / `prompt_contract` 必须要求 Codex 在完成 MAS owner-authorized work 或返回 typed blocker 后，以唯一终端 JSON object 输出 typed closeout。正文、进度说明、审稿意见、paper delta 或 free text 都不能作为 OPL provider completion 信号。
- 理由：DM003 暴露出 Codex writer 已产生 `paper/draft.md`、claim-evidence map 和 paper-facing delta，但 OPL Temporal provider 仍因 `closeout_packet=null` 返回 `typed_closeout_packet_required`，导致 provider completion 没有闭合。根因是 MAS dispatch packet 没把 typed closeout 作为硬输出契约写入 prompt/contract；OPL 的 fail-closed 行为是正确的。
- 影响：这是 MAS -> OPL handoff contract 修复，不写 DM003 canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission-ready verdict。论文质量仍需 write owner delta、AI reviewer-backed publication eval 和 publication gate 关闭；typed closeout 只证明 provider attempt 有可消费 owner receipt / artifact delta / typed blocker refs。

## 2026-05-22：显式 owner dispatch 必须用当前 persisted dispatch 覆盖旧 consumer inline payload

- 决策：`domain-owner-action-dispatch --action-types <action>` 读取到同一 `refs.dispatch_path` 的 consumer inline dispatch 与 study-level persisted dispatch 时，若 persisted dispatch 仍为 `dispatch_status=ready` 且匹配当前 owner request / owner route，必须用 persisted dispatch 覆盖 consumer inline payload。
- 决策：该覆盖只发生在同一路径、同 action、同 owner request 校验通过的 dispatch 上；不放宽 owner-route currentness、paper-progress stall guard、forbidden surfaces、developer_apply_safe 或 repeat suppression。
- 理由：DM002 暴露出 `quality_repair_batch` 已生成下一层 writer handoff 并刷新 study-level `default_executor_dispatches/run_quality_repair_batch.json`，但 workspace consumer 仍保留上一层 inline dispatch。显式执行时旧 inline payload 的 `paper_progress_stall.action_fingerprint` 抢占了当前 persisted dispatch，导致合法 write owner handoff 被 `paper_progress_stall_fingerprint_stale` 阻断。
- 影响：这是 MAS owner dispatch currentness 修复。它不直接写 canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`；只保证 MAS owner chain 能消费当前 writer handoff，并继续由 writer delta、AI reviewer-backed publication eval 与 publication gate 判定论文质量。

## 2026-05-22：default-executor handoff export 必须携带 owner-currentness refs

- 决策：`domain_owner/default-executor-dispatch` pending family task 不得只凭 `dispatch_status=ready` 暴露给 OPL。导出的 task 必须 refs-only 携带 `default_executor_dispatch_request`、`default_executor_prompt_contract`、`mas_default_executor_owner_receipt_contract`、`owner_route_currentness_basis`，并投影 dispatch refs / owner-route refs 中可验证的 currentness basis，例如 `source_eval_path`、`repair_execution_evidence_path`、`truth_epoch`、`runtime_health_epoch`、`work_unit_fingerprint`、`work_unit_id` 和 blocker reason。
- 决策：缺 `prompt_contract.owner_route` / top-level `owner_route` 或缺 `refs.dispatch_path` 的 bare ready dispatch 不生成 pending family task。OPL 只能排队带当前 owner-route basis 的 writer handoff；不能把裸 dispatch、旧 projection 或缺 currentness 的 request 当作可执行 writer attempt。
- 理由：DM002/DM003 共同暴露出“handoff 看起来 ready，但未必绑定当前稿件、当前 reviewer/request、正确 owner 和可追踪 attempt”的顶层缺口。default-executor export 是 MAS -> OPL 的跨层入口，必须达到 guarded-apply 同级别的 owner-receipt / currentness refs 强度。
- 影响：该变更只收紧 MAS sidecar export 的 refs-only contract；不内联医学内容，不启动 Codex，不写 OPL queue，不写 canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package` 或 submission package。

## 2026-05-22：quality repair upstream work unit 不得在 gate result 缺 selected unit 时丢失

- 决策：`quality_repair_batch` 已经通过 explicit `controller_route_context` 授权 upstream publishability repair work unit 时，`run_upstream_paper_repair_unit()` 的 work unit 选择必须先消费 `gate_clearing_result` 的 selected/current/explicit work unit；若 gate result 没有给出 selected upstream unit，则回退到当前 resolved route context 的 upstream work unit。
- 决策：这条回退只适用于 `UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS`，例如 `medical_prose_write_repair`。它不授权 bundle、delivery、submission package、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 `current_package` 写入。
- 理由：DM003 暴露出 `medical_prose_write_repair` 已由 AI reviewer / controller route 明确授权，但 gate-clearing batch 结果没有携带 `selected_publication_work_unit` 时，quality repair core 会把 upstream unit 解析为 `None`，随后只生成 `writer_worker_handoff`，没有 canonical `paper/draft.md` 或 `paper/build/review_manuscript.md` story-surface delta。`handoff_ready` 只能表示 writer dispatch ready，不能替代稿件增量。
- 影响：该修复确保 owner route 已明确的 medical prose write repair 能在 MAS owner path 内物化 canonical manuscript story surface 或继续返回 typed blocker；论文是否达到 high-quality medical draft 仍由 AI reviewer-backed publication eval 与 publication gate 判定。

## 2026-05-22：medical prose review request stale 时必须重建当前 request 而非复用旧评审

- 决策：`return_to_ai_reviewer_workflow` 遇到 `medical_prose_review_request_digest_mismatch`、`medical_prose_review_live_manuscript_digest_mismatch` 等 prose currentness blocker 时，`domain-owner-action-dispatch` 必须先通过 MAS-owned `materialize_medical_prose_review_request()` 物化当前稿件 digest 对应的 `artifacts/publication_eval/medical_prose_review_request.json`，并在 owner result 中记录 `medical_prose_review_request_rehydrated`、`rehydrated_request_ref` 与 rehydrate receipt。
- 决策：该 rehydrate 只生成 AI reviewer 输入 request，不写 `publication_eval/latest.json`，不写 `controller_decisions/latest.json`，不改 canonical paper，不重建 package，也不声明 quality ready。下一步仍必须由 AI reviewer 基于当前 request 和当前 manuscript 产出新的 `medical_prose_review.json` / publication eval record 后，才能回到 `return_to_ai_reviewer_workflow`。
- 理由：DM003 暴露出 currentness gate 已能拒绝旧 request / 旧 prose review，但如果只返回 blocker，不自动物化当前 request，系统会卡在“知道旧评审不能用，却没有生成下一轮 AI reviewer 输入”的状态。这个缺口和 DM002/DM003 的共同问题一致：ready / routed / blocked 必须绑定当前证据 refs 和 owner receipt，不能依赖旧投影。
- 影响：这是 MAS AI reviewer owner-chain 的 currentness / owner-receipt 修复，不放宽 publication gate，不授权人工或 OPL 写医学质量 verdict。DM003 后续仍需 AI reviewer 对当前稿件重新审阅，并由 publication gate 判定是否可进入下一阶段。

## 2026-05-22：medical prose review currentness 必须绑定当前稿件 digest

- 决策：`ai_reviewer_publication_eval_workflow` 消费 `artifacts/publication_eval/medical_prose_review.json` 时，除校验 prose review 与 request 的 `request_digest`、`manuscript_ref` 和 request manuscript digest 一致外，还必须读取当前 `manuscript` input ref 的 live 文件并计算 SHA-256。live manuscript digest 与 prose review provenance 的 `manuscript_digest` 不一致时，必须 fail closed 为 `medical_prose_review_live_manuscript_digest_mismatch`；live manuscript 缺失时必须 fail closed 为 `medical_prose_review_live_manuscript_missing`。
- 决策：`domain-owner-action-dispatch` 必须把上述错误投影为 `medical_prose_review_request_rehydrate_required` typed blocker，明确 `stale_medical_prose_review_reuse_allowed=false`、`quality_verdict_written=false`，并要求 `materialize_current_medical_prose_review_request` 与 `produce_ai_reviewer_medical_prose_review_against_current_manuscript` 后再回到 `return_to_ai_reviewer_workflow`。
- 理由：DM003 暴露出 write owner 已更新 canonical `paper/draft.md`，但 `return_to_ai_reviewer_workflow` 仍可把旧 `medical_prose_review.json` 包装成新的 `publication_eval/latest.json`。旧 currentness 只证明 review 和 request 互相一致，没有证明它们覆盖当前稿件，导致 AI reviewer-backed eval 看似刷新、实际复用旧 prose judgment。
- 影响：这是 MAS AI reviewer / publication-quality owner currentness 修复，不写 DM003 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。后续 DM003 必须先产生针对当前稿件 digest 的 AI prose review，再允许 AI reviewer workflow 写新的 publication eval。

## 2026-05-22：ready default-executor dispatch 必须作为 refs-only sidecar task 暴露给 OPL

- 决策：当 MAS materialize 出 `artifacts/supervision/consumer/default_executor_dispatches/*.json`，且该文件明确为 `surface=default_executor_dispatch_request`、`dispatch_status=ready`、`executor_kind=codex_cli_default`、`next_executable_owner=write` 时，`sidecar export` 必须生成 `domain_owner/default-executor-dispatch` pending family task。该 task 只携带 `dispatch_ref`、prompt contract ref、action type、dispatch authority、study / quest identity 和 authority boundary，不内联 request body。
- 决策：该 task 的 dispatch owner / queue owner 是 `one-person-lab`，domain truth owner 仍是 `med-autoscience`。MAS 不用 sidecar export 直接启动 Codex writer，不写 OPL queue 或 stage attempt；OPL 只能据此建立 Codex-default writer stage attempt，再由后续 MAS owner receipt、AI reviewer-backed publication eval 和 publication gate 判定论文进展。
- 理由：DM002 暴露出 MAS 已生成 writer handoff / default executor request，但 OPL hydrate 面看不到这个可执行 handoff，只能继续围绕旧 paper autonomy / aftercare / domain route task 打转。正确边界是 MAS 输出 refs-only writer dispatch request，OPL 承接 generic queue / attempt / provider lifecycle。
- 影响：这是 MAS owner-route handoff adapter 暴露修复，不写 DM002 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission-ready verdict。

## 2026-05-21：DM003 primary-care treatment-gap 稿件修复必须进入 write owner story-delta 回路

- 决策：`primary_care_gap` 是 MAS 支持的 observational manuscript family，报告规范默认解析为 STROBE。该 family 的 descriptive clinical treatment-gap / phenotype 稿件可以使用 clinical subtype reconstruction strong display shell，但不能把 display support、ledger update 或 QA 摘要当成正文完成证据。
- 决策：AI reviewer route-back 给出的 `medical_prose_write_repair` 与 `manuscript_story_repair` 同属 manuscript-facing story-surface work unit。若 `quality_repair_batch` 对当前 `publication_eval/latest.json` 返回 `manuscript_story_surface_delta_missing -> next_owner=write`，domain route scan / reconcile 必须保留原 work unit，并把 `run_quality_repair_batch` 物化给 write owner。完成证据必须是 canonical `paper/draft.md` 或 `paper/build/review_manuscript.md` delta，或者继续返回 typed blocker。
- 决策：`run_quality_repair_batch` 是 owner-route 可消费 action；domain owner dispatch 必须能从 persisted request `artifacts/supervision/requests/quality_repair_batch/latest.json` 恢复并执行该 action。旧 OPL owner lifecycle、completed-current-truth 残留或 platform redrive residue 不得吞掉当前 write route。
- 理由：DM003 暴露出初稿虽然有大样本、明确基层糖尿病管理场景和治疗覆盖缺口价值，但写作层仍像 AI 修复稿，且 phenotype derivation、recorded treatment-gap 术语、BP/data quality、baseline table、正式图表和防御性语言这些医学期刊要件没有被初稿前质量链路稳定吃进去。单纯写 reviewer_revision task intake 不能保证下一版稿件变好；MAS 必须把这类反馈沉淀成 family reporting contract、story-surface delta requirement 和 owner-route regression。
- 影响：这是 MAS 医学论文智能体 / owner-route / reporting contract 修复，不写 DM003 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。正式质量关闭仍由 write owner 产出正文 delta 后，经 AI reviewer-backed publication eval 与 publication gate 判定。

## 2026-05-22：AI reviewer 顶层 recommended action 是 route authority，prose currentness route target 只是覆盖证据

- 决策：当 AI reviewer-owned `publication_eval/latest.json` 的 `reviewer_operating_system.currentness_checks.medical_prose_review` 已证明 prose review 当前，且顶层 `recommended_actions[]` 明确给出 `route_back_same_line` / `bounded_analysis` / `stop_loss` owner action 时，controller/domain-transition 的 route authority 必须来自顶层 action，而不是 `medical_prose_review.route_target`。
- 决策：`medical_prose_review.route_target` 只用于证明该 prose review 不是普通 clear 状态、并可作为缺失顶层 action 时的 fail-closed 信号；它不得覆盖 AI reviewer 顶层 action 的 `route_target=write`、`next_work_unit` 或 `work_unit_fingerprint`。若顶层 action 缺失或指向 `review`，继续 fail closed，不合成 owner route。
- 理由：DM002 暴露出 current prose review metadata 仍标注 `route_target=analysis`，但同一 AI reviewer record 的顶层 action 已明确 `route_back_same_line -> write`，要求把 unit-harmonized rerun 吸收进 Abstract、Results、Methods、Table/Figure 和 claim-evidence map。旧 helper 要求 metadata target 与顶层 action target 相同，导致 current eval 被误投成 `ai_reviewer_re_eval`，循环复评而不能交给 write owner。
- 影响：这是 MAS AI reviewer / controller route authority 修复，不放宽 publication gate，不授权机械 ready verdict，不写 DM002 truth、paper、submission package、current package、`publication_eval/latest.json` 或 `.ds` runtime state；它只让 MAS owner chain 正确把当前 AI reviewer verdict 路由到 paper-write repair。

## 2026-05-22：quality_repair_batch handoff_ready 不是 story-surface 修复完成证据

- 决策：`quality_repair_batch.status=handoff_ready` 只表示 write-owner/default-executor handoff 已物化；若同一 record 的 `repair_execution_evidence.status=blocked`、`canonical_artifact_delta.meaningful_artifact_delta=false`，且 blocker 含 `manuscript_story_surface_delta_missing` 或 forbidden manuscript term residue，`domain-route-scan` 必须继续投影 `write/run_quality_repair_batch`。
- 决策：当前 story-surface writer blocker 必须优先于 `completed_current_truth` 与 parked truth 短路；旧 completion/resolved 投影不能吞掉同一 `publication_eval/latest.json` 下仍未产生 canonical `paper/draft.md` 或 `paper/build/review_manuscript.md` delta 的 write route。
- 理由：DM002 暴露出 `domain-route-reconcile` 已执行 `run_quality_repair_batch`，但 batch 顶层为 `handoff_ready`、nested repair evidence 仍 blocked，正文仍含 `validation surface` 禁用运行态措辞；旧 scan 只看顶层 `blocked_reason`，随后 action queue 变空，导致 write owner route 丢失。
- 影响：该修复只修 MAS currentness/read-model projection，不改 sidecar authority，不写 `paper/submission_minimal/`、`manuscript/current_package/`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission readiness verdict。论文质量仍需 write owner 产出 canonical story-surface delta，并由 AI reviewer-backed publication eval 与 publication gate 重新判定。

## 2026-05-22：terminal paper-progress stall 必须以当前 owner route 为准，不能让旧 dispatch fingerprint 吞掉合法 handoff

- 决策：`paper_progress_stall` 已进入 `terminal=true` 时，`domain_owner_action_dispatch` 必须先用当前 scan/latest owner route 判断该 action 是否是合法 terminal-stall handoff；若 `terminal_stall_handoff.owner_handoff_allowed(...)` 成立，就允许进入对应 MAS owner callable。旧 dispatch payload 携带的 `paper_progress_stall.action_fingerprint` 只对非 terminal 或 owner handoff 不合法的路径继续 fail closed。
- 决策：对 DM003 这类 `next_owner=write`、`allowed_actions=["run_quality_repair_batch"]`、`failure_signature=quest_waiting_opl_runtime_owner_route`、`next_work_unit=medical_prose_write_repair` 的路径，当前 terminal stall 是把控制权交还 write owner 的证据，不是禁止 write owner 产出 canonical manuscript story-surface delta 的理由。
- 理由：DM003 暴露出 MAS 已把 AI reviewer 的稿件质量反馈路由到 `write/medical_prose_write_repair`，但 default executor 先比较旧 dispatch stall fingerprint 与当前 scan stall fingerprint，返回 `paper_progress_stall_fingerprint_stale`，导致合法 write owner callable 被 terminal stall 投影挡住。DM002/DM003 的共同根因是 authoritative freshness 和 owner receipt 协议不够硬：queue、dispatch、stall 或 projection 不能替代当前 owner route、当前证据 refs 和 owner receipt。
- 影响：该修复不放宽非 terminal stale fingerprint guard，不写 `paper/`、`paper/submission_minimal/`、`manuscript/current_package/`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission readiness verdict。它只保证当前 terminal stall 下的合法 MAS owner handoff 能执行；正式论文质量仍需 canonical paper delta、AI reviewer-backed `publication_eval/latest.json` currentness、publication gate 和 owner receipt 闭合。

## 2026-05-22：analysis harmonization completed result 必须覆盖 AI reviewer route-back 所需证据

- 决策：`analysis_harmonization_owner_result` 不能仅凭 `unit_harmonized_rerun_completed=true` 判定 hard-methodology work unit 已关闭。completed result 必须指向或内联 `unit_harmonized_external_validation_rerun_evidence`，且该 evidence 必须包含 external-validation uncertainty intervals、observed-to-expected interval、Brier interval、calibration intercept/slope with 95% CI、以及 grouped calibration with observed-rate intervals；缺任一项时继续视为 required output pending。
- 决策：`analysis_harmonization_owner` 生成 unit-harmonized rerun evidence 时，必须把上述覆盖作为 owner output 的正式内容，并把 completed owner result 内联当前 evidence。若证据无法产出，应返回 typed blocker，而不是用 completed flag 关闭 route-back。
- 决策：`owner-route-reconcile` 可以把 controller work unit `unit_harmonized_validation_uncertainty_and_grouped_calibration` 映射到可执行 callable `unit_harmonized_external_validation_rerun`，但 action projection 必须同时保留 `controller_next_work_unit`、`controller_work_unit_id` 和 `executable_work_unit`，避免 OPL、Agent Lab、前台 supervisor 或后续 owner 把 controller 原始路线与可执行别名混淆。
- 理由：DM002 暴露出 analysis owner 的 rerun evidence 缺少 AI reviewer 明确要求的 uncertainty / calibration / grouped calibration 覆盖，但旧 completed-result gate 仍把它视为 satisfied，导致系统重复窄 rerun 后再被 AI reviewer route back。正确边界是 MAS owner-result quality contract，不是手工更新论文、publication eval、controller decision 或 OPL queue。
- 影响：这是 MAS 医学论文智能体 / owner-result / quality-suite 修复。它不写 DM002 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal`、`manuscript/current_package` 或 submission readiness verdict；后续论文质量仍由 MAS owner chain 重新执行并由 AI reviewer-backed publication eval 判定。

## 2026-05-22：owner-route-reconcile 必须投影当前 runtime-redrive domain transition

- 决策：`owner-route-reconcile` 的每个 study projection 必须显式带出当前 `progress_projection.domain_transition`，用于 supervisor、OPL sidecar、Agent Lab 和人工接力判断当前 owner route。该字段是 read model truth projection，不授权 OPL 或前台写 MAS study truth、publication eval、controller decision、paper、submission package 或 current package。
- 决策：`completion_evidence.completed_current_truth` 不能吞掉当前 runtime-redrive domain transition。只要 `domain_transition.decision_type` 属于 runtime-redrive 类型，例如 `route_back_same_line`、`ai_reviewer_re_eval`、`publication_gate_blocker` 或 `bundle_stage_finalize`，scan/action projection 必须继续让 domain transition oracle 生成 owner action 或 typed blocker，而不是把旧 completed/completion contract 当成终态。
- 理由：DM002 暴露出 `progress-projection` 已有 `route_back_same_line -> analysis-campaign/unit_harmonized_validation_uncertainty_and_grouped_calibration`，但 `owner-route-reconcile` 的 study 输出看不到 `domain_transition`；在 completed-truth 风险场景中，reconcile 还可能在 domain transition oracle 前短路，导致 owner action 消失。
- 影响：该变更只修 MAS read model / supervisor action projection，不放宽 quality gate，不绕过 OPL runtime owner，也不写 runtime-owned `.ds`、`publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal`、`manuscript/current_package` 或 submission readiness verdict。

## 2026-05-22：analysis-campaign route-back 必须物化为 analysis_harmonization_owner action

- 决策：当当前 `domain_transition` / controller route-back 为 `decision_type=route_back_same_line`、`route_target=analysis-campaign`，且 `next_work_unit.unit_id` 为 `unit_harmonized_validation_uncertainty_and_grouped_calibration` 或 `unit_harmonized_external_validation_rerun` 时，`owner-route-reconcile` 必须产出 `action_type=unit_harmonized_external_validation_rerun`，owner/request_owner/recommended_owner 固定为 `analysis_harmonization_owner`。
- 决策：该路径的 required output 是 unit-harmonized external-validation rerun evidence 或 `unit_harmonized_rerun_required` typed blocker；不得回落到泛型 `run_quality_repair_batch`，也不得把 `analysis-campaign` 这个 lane 名当成可执行 owner callable。
- 理由：DM002 暴露出 `study-progress` 已能显示 `analysis-campaign/unit_harmonized_validation_uncertainty_and_grouped_calibration`，但 `owner-route-reconcile` action queue 为空，导致 OPL sidecar 只能继续派发旧 paper autonomy / bundle tasks。真正缺口是 route-back 到 owner action 的 materialization，不是 OPL tick、bundle gate 或 paper repair executor。
- 影响：该变更不放宽 bundle downstream gate，不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical `paper/`、`paper/submission_minimal`、`manuscript/current_package` 或 submission readiness verdict；它只让现有 `analysis_harmonization_owner` callable 成为当前 hard-methodology work unit 的执行入口。

## 2026-05-22：paper repair sidecar 必须使用 runtime binding 的 canonical quest_id

- 决策：`paper_autonomy/repair-recheck` 进入 MAS owner 前，sidecar dispatch 必须优先读取 `studies/<study_id>/runtime_binding.yaml` 中的 canonical `quest_id`，再调用 `paper_repair_executor` / `quality_repair_batch`。OPL typed task payload 只能作为未绑定 study 的输入来源，不能覆盖已绑定 study 的 runtime identity。
- 决策：`quest-{study_id}` 只能作为缺少 runtime binding 时的最后构造值，不得在已绑定 MAS study 中成为 paper owner / gate locator 的实际 quest identity。
- 理由：DM003 暴露出错误的 `quest-003-dpcc-primary-care-phenotype-treatment-gap` 进入 paper repair evidence，导致 `quality_repair_batch` 用不存在的 runtime quest root 调 `publication_gate`，而 canonical `studies/003.../paper` 已完整却被误报为 `blocked_no_paper_root`。这属于 owner identity propagation bug，不是论文 paper surface 缺失。
- 影响：修复保持 OPL 只做 typed dispatch / transport receipt，不给 OPL 写 MAS truth 的权限；MAS paper owner 仍通过 canonical runtime binding、publication gate、repair receipt 和 AI reviewer verdict 推进。

## 2026-05-22：medical prose write repair 是上游 paper-write owner，不得继承 stale bundle route

- 决策：AI reviewer 当前 medical prose route-back 生成的 `medical_prose_write_repair` 是 upstream publishability repair work unit，control-plane route gate 必须授权为 `paper_write`。它可以在 `publication_supervisor_state.bundle_tasks_downstream_only` 和 `bundle_build_allowed=false` 时继续由 MAS managed owner 修 canonical paper / evidence / review / display-facing repair surfaces，但不能写 `paper/submission_minimal/`、`manuscript/current_package/`、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 submission readiness verdict。
- 决策：`quality_repair_batch` 收到 caller-provided `controller_route_context` 时，若当前 AI reviewer-backed `publication_eval/latest.json` 显式给出 upstream `route_back_same_line` work unit，例如 `medical_prose_write_repair`，必须用当前 publication eval 的 paper-write route 覆盖 stale `submission_minimal_refresh` / bundle route context。只有 downstream package/delivery work unit 才继续走 `bundle_build` / `delivery_sync` / `submission_materialize`。
- 决策：`paper_autonomy/repair-recheck` 调到 AI reviewer callable 后，若 `domain_owner_action_dispatch` 返回 blocked 或 repeat-suppressed execution，paper repair receipt 必须保留 `executions[].blocked_reason` / `repeat_suppressed` 作为 typed blocker，不得退化为泛型 `owner_callable_surface_blocked`。这让 OPL queue / Agent Lab / foreground supervisor 能看见真实 owner blocker，而不是误诊为 callable 缺失。
- 理由：DM003 暴露出医学论文写作质量反馈已经被 AI reviewer 转成 `medical_prose_write_repair`，但旧 controller route context 仍指向 bundle/package work unit，导致 `run_quality_repair_batch` 选择 `bundle_build` 并被 downstream-only gate 拦住。同时 AI reviewer callable blocked/repeat-suppressed 的具体原因被 receipt 丢成泛型 blocker，使前台难以判断是 owner request、repeat suppression 还是 callable surface 缺失。
- 影响：这是 MAS owner-route / paper repair contract 修复，不是 quality gate 放宽，也不是 OPL queue 或 provider lifecycle 修复。正式质量关闭仍必须由后续 AI reviewer-backed `publication_eval/latest.json`、publication gate replay、owner receipt 和 package freshness proof 共同完成。

## 2026-05-21：sidecar dispatch 幂等 receipt 必须绑定 owner capability fingerprint

- 决策：`sidecar dispatch` 的 dispatch receipt 幂等键必须同时覆盖 task identity、task source fingerprint 与 MAS owner capability fingerprint。owner capability fingerprint 由当前 action type 和 MAS sidecar / paper repair / domain owner dispatch 实现面生成；同一 owner 实现版本继续幂等，owner callable 或 dispatch capability 变化后必须重新执行 MAS owner surface，而不能复用旧 receipt。
- 决策：该 fingerprint 只控制 MAS sidecar dispatch receipt lifecycle，用于避免旧 `owner_callable_surface_missing`、旧 owner blocker 或旧 dispatch result 在 MAS owner callable 修复后继续 `idempotent_noop` replay。它不得放宽 `control_plane_route_gate`、不得把 downstream-only `bundle_build` 当作当前可执行 upstream repair，也不得写 DM002 study truth 或 delivery surface。
- 理由：DM002 暴露出 OPL family-runtime 已能用 profile-scoped MAS module dispatch 当前 task，但 MAS sidecar receipt 仍可能复用 owner callable 修复前的旧 blocker，导致 AI reviewer / paper repair owner route 无法重新进入 MAS owner chain。正确修复位置是 MAS sidecar receipt key，不是手工更新 queue、publication eval、controller decision 或 current package。
- 影响：该变更不写 `.ds` runtime state、`paper/`、`paper/submission_minimal`、`manuscript/current_package`、`artifacts/publication_eval/latest.json` 或 `artifacts/controller_decisions/latest.json`；只让 MAS owner implementation 变更后可以重新产出 fresh owner receipt、typed blocker 或 accepted dispatch result。

## 2026-05-22：analysis harmonization AI reviewer currentness 必须同时覆盖 ref identity 与 ref version/time

- 决策：`analysis_harmonization_owner` completed result 交回 `ai_reviewer_medical_prose_quality_review` 时，`publication_eval/latest.json` 只有在 AI reviewer-owned provenance 同时覆盖 required currentness refs 的路径身份，并且 eval 时间不早于这些 refs 的结构化时间或文件 mtime 时，才能视为当前。仅在 `source_refs` 中出现相同路径不足以关闭 re-eval。
- 决策：缺少 eval 时间戳而 required ref 可解析出时间时，必须 fail closed 到 `return_to_ai_reviewer_workflow`。缺少 required ref 时间时才允许用路径身份判断覆盖，避免凭空制造版本号，同时不把旧 eval 冒充为当前。
- 决策：`domain_action_request_lifecycle` 物化 AI reviewer request 时必须应用同一 currentness 规则。候选 `ai_reviewer_responses/*_publication_eval_record.json` 或预置 record 即使引用了 required refs，只要其 `emitted_at/generated_at/completed_at/finished_at/updated_at/created_at/recorded_at` 早于 required refs 的结构化时间或文件 mtime，就必须保留 `ai_reviewer_record_stale_after_unit_harmonized_rerun` blocker，等待新的 AI reviewer record。
- 决策：当 AI reviewer record 被 workflow 或投影层重新写入 `publication_eval/latest.json` 时，currentness 时间必须优先取 `eval_id` 或 reviewer trace id 中的评审逻辑时间；外层 `emitted_at` 只表示写入时间，不能证明 reviewer 消费了后来的 analysis evidence。
- 理由：DM002 暴露出旧 AI reviewer eval 的 `source_refs` 已包含 `analysis_harmonization/latest.json` 与 unit-harmonized rerun evidence 路径，但 eval 的 `emitted_at` 早于新 analysis owner result，导致 MAS 误判旧评审已覆盖新证据。
- 影响：这是 MAS AI reviewer owner-chain currentness 修复，不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical `paper/`、`submission_minimal`、`manuscript/current_package` 或 submission-ready verdict；它只让 controller/read-model 在旧 eval 早于新 evidence 时重新排 AI reviewer owner workflow。

## 2026-05-22：stale AI reviewer record 必须投影成 record-production handoff

- 决策：`return_to_ai_reviewer_workflow` 遇到 `ai_reviewer_record_stale_after_unit_harmonized_rerun` 时，executor receipt 必须携带结构化 `ai_reviewer_record_production_request`。该 request 指向 `produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization`、required currentness refs、required input refs、record-only 输出面 `artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json`，以及后续 `domain-action-request-materialize` 和 `domain-owner-action-dispatch`。
- 决策：该 handoff 仍然 fail-closed，不自动复用 stale record，不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、paper、submission package、current package 或 `.ds` runtime truth。真正医学判断仍由独立 AI reviewer record 产生，再由 MAS owner workflow 消费。
- 决策：Agent Lab medical manuscript quality suite 必须把 `ai_reviewer_record_production_handoff` 纳入 `opl-meta-agent` developer patch work order 和 editable surface refs，让“旧 record stale 后缺 record-production owner step”成为可回归的 MAS 智能体能力缺口。
- 理由：DM002 的 analysis rerun 完成后，request lifecycle 正确识别旧 AI reviewer record 已过期，但 dispatcher 只返回三条自然语言 next action，外层容易误诊为 OPL queue/provider 问题或普通不可执行 blocker。结构化 handoff 让前台、OPL Agent Lab 和 meta-agent 能看到真实 MAS owner 缺口，并按 record-only owner surface 推进。
- 影响：这是 MAS AI reviewer / Agent Lab 自进化 read-model 修复，不放宽 quality gate，不授权机械 ready verdict，也不替 AI reviewer 生成医学结论；它只把当前 blocker 转成可消费、可测试、可回归的 owner handoff。

## 2026-05-22：AI reviewer record 必须绑定当前 manuscript 版本

- 决策：`domain_action_request_lifecycle` 接受 request-bound `ai_reviewer_record` 前，若该 record 的 provenance 或 dimension evidence refs 指向当前 canonical manuscript（例如 `paper/draft.md` 或 `paper/build/review_manuscript.md`），record 的逻辑评审时间必须不早于该 manuscript 的当前结构化时间或文件 mtime；否则 fail closed 为 `ai_reviewer_record_stale_after_current_manuscript`。
- 决策：`return_to_ai_reviewer_workflow` 遇到 `ai_reviewer_record_stale_after_current_manuscript` 时，必须返回结构化 `ai_reviewer_record_production_request`，其 `request_kind=produce_ai_reviewer_publication_eval_record_against_current_manuscript`，并要求下一轮 record 消费当前 manuscript ref。它不得把旧 record 重新包装进 `publication_eval/latest.json`。
- 决策：当当前 stable AI reviewer request 已处于 stale-record lifecycle 时，domain transition 必须优先投影 `ai_reviewer_re_eval` record-production work unit，抢占旧 `publication_eval/latest.json` 的 write route-back；managed runtime prompt 必须把 `produce_ai_reviewer_publication_eval_record_against_current_manuscript` / `produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization` 解释为 AI reviewer record-only 执行合同。该合同只允许写 `artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json`，随后 rematerialize request 并 dispatch `return_to_ai_reviewer_workflow`。
- 决策：Agent Lab medical manuscript quality suite 必须暴露 `ai_reviewer_record_current_manuscript_binding` quality target、mechanism edit ref 和 regression suite ref，让“旧 AI reviewer record 复用在新稿件上”成为可回归的 MAS 智能体能力缺口。
- 理由：DM002 暴露出 2026-05-22 21:10 刷新的 Abstract 已包含核心 95% CI，但 `return_to_ai_reviewer_workflow` 在 21:12 仍把 2026-05-21 旧 request-bound AI reviewer record 中的 “Abstract lacks 95% CIs” 原样物化为最新 `publication_eval/latest.json`。这是 reviewer record currentness 漏洞，不是论文 surface 缺 CI。
- 影响：这是 MAS AI reviewer currentness / self-evolution 修复，不写 study truth、canonical paper、`paper/submission_minimal`、`manuscript/current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`；正式质量判断仍由新的 AI reviewer record 和 MAS owner workflow 生成。

## 2026-05-22：workspace profile merge 必须把 root keys 插在 TOML table 之前

- 决策：`medautosci init-workspace` 合并既有 workspace profile 时，缺失的 root-level entries 必须插入第一个 TOML table 之前，不得追加到文件末尾。
- 理由：DM002 workspace 的 local profile 已包含 `[explicit_archive_import_ref]`，旧 merge 会把 `developer_supervisor_mode`、`mas_developer_github_usernames` 和 `github_username` 追加进该子表；下一次 merge 又认为 root key 缺失并再次追加，最终 profile 出现 duplicate key，所有 MAS CLI 在 TOML parse 阶段失败。
- 影响：这是 MAS workspace bootstrap/profile hygiene 修复，不改 study truth、runtime state、paper surface、publication eval、controller decisions 或 current package；现有坏 profile 仍需一次性整理成 root-level 单份配置。

## 2026-05-22：current medical prose route-back 必须合成完整 AI reviewer publication eval record

- 决策：当 `artifacts/supervision/requests/ai_reviewer/latest.json` 没有携带完整 `ai_reviewer_record`，但当前 `artifacts/publication_eval/medical_prose_review.json` 是 AI reviewer-owned、request/manuscript current，并且 `route_back_recommendation.required=true` 指向 `write` 或 `analysis-campaign` 时，`return_to_ai_reviewer_workflow` 不得回退到旧 `publication_eval/latest.json` 或报 `ai_reviewer_record_incomplete`。MAS owner workflow 必须由 current prose review 合成完整 AI reviewer-backed `publication_eval/latest.json` route-back record，包含 `quality_assessment`、`future_facing_limitations_plan`、reviewer OS currentness、`route_back_same_line` recommended action 和 downstream-only package freshness。
- 决策：该合成路径仍走 `ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow`，继续执行 reviewer OS、medical prose currentness、future plan、schema、story-provenance 和 delivery-downstream 校验；不得放宽 publication gate，也不得直接改 `paper/`、`submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。
- 理由：DM003 暴露出 current `medical_prose_review` 已给出 `partial/revise -> write` 的高价值质量结论，但 request packet 未附完整 publication eval record，而旧 latest 是 clean-migration underdefined 投影且顶层缺 `future_facing_limitations_plan`。结果 dispatcher 不再 repeat-suppress 后仍 fail-closed 在 `ai_reviewer_record_incomplete`，没有把 reviewer 结论转成 write owner work unit。
- 影响：这属于 MAS AI reviewer / publication-quality owner 修复，不是 OPL queue、provider、retry 或 runner 修复。Agent Lab/quality suite 应把“current medical prose review route-back can materialize complete publication eval”作为回归能力，防止后续医学写作质量反馈只停留在 reviewer artifact 而不进入 controller truth。

## 2026-05-22：当前 medical prose review route-back 必须解除 AI reviewer dispatch repeat suppression

- 决策：`return_to_ai_reviewer_workflow` 的 required-output pending 判定不再只依赖监督 scan 中的 `ai_reviewer_assessment.missing=true`。当 `artifacts/supervision/requests/ai_reviewer/latest.json` 携带的 AI reviewer record 尚未写入 `publication_eval/latest.json`，或当前 `artifacts/publication_eval/medical_prose_review.json` 明确 `route_back_recommendation.required=true` 且 route target 为 `write` / `analysis-campaign` / `blueprint`、但 `publication_eval/latest.json` 的 reviewer OS 和 recommended action 还没有消费同一路由时，executor dispatch 与 request materializer 都必须把 required output 视为 pending，不得 repeat suppress。
- 决策：没有 AI reviewer request record、没有 current medical prose route-back、也没有 scan-level `ai_reviewer_assessment.missing=true` 的普通重复 dispatch 继续按 repeat-suppression 保护，不得因为 `publication_eval/latest.json` 缺失就无证据重跑。
- 理由：DM003 暴露出当前 AI reviewer prose review 已给出 `revise -> write` 的医学论文质量回退，但旧 `publication_eval/latest.json` 仍停在 clean-migration underdefined 状态；由于 owner-chain 只看 scan-level missing flag，dispatch 被 repeat-suppressed，无法把当前 reviewer 结论 materialize 成新的 publication eval 与 write owner work unit。
- 影响：这是 MAS AI reviewer owner-chain currentness 修复，不是 OPL queue/provider lifecycle 修复，也不是质量门槛放宽。该路径只让 MAS owner workflow 重新消费当前 AI reviewer output；它不手写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical `paper/`、`submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。

## 2026-05-21：当前 controller route-back 必须作为 refs-only sidecar task 暴露给 OPL

- 决策：当 `artifacts/controller_decisions/latest.json` 的当前非终止、非 human-gate 决策为 `decision_type=route_back_same_line`，且带有 `route_target` 与 `next_work_unit.unit_id` 时，`sidecar export` 必须生成 `domain_route/reconcile-apply` pending family task。该 task 的 `source` 为 `mas-controller-decision`，dedupe/source fingerprint 来自 controller decision identity、时间、route target、next work unit 与 work-unit fingerprint。
- 决策：该 sidecar task 只携带 refs 与 route metadata，包括 controller decision ref、route target、next work unit、blocking work units、work unit fingerprint 和 `authority_boundary=mas_owner_reconcile_only`。OPL 只能据此进行 queue/hydrate/dispatch transport，并通过 `sidecar dispatch` 回到 MAS owner surface；不得把它解释为论文质量 verdict、study truth、publication eval、controller decision 写入或 current package 刷新。
- 理由：DM002 暴露出 MAS controller 已给出 `analysis-campaign/unit_harmonized_validation_uncertainty_and_grouped_calibration` route-back，但 OPL hydrate 面无法消费新的 controller decision，只能看到旧 runtime owner-route 或旧 repair task，导致真实论文线停在 platform redrive。
- 影响：这是 MAS refs-only adapter / owner-route 暴露修复，不是 MAS 私有 runtime liveness、queue、retry/dead-letter 或 provider resume 修复。该路径不写 `.ds` runtime state、不写 `publication_eval/latest.json`、不写 `controller_decisions/latest.json`、不写 `paper/`、`submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。

## 2026-05-21：OPL/Temporal hosted autonomous runtime 是 MAS 默认运行口径

- 决策：MAS hosted path 的默认运行口径固定为 OPL/Temporal hosted autonomous runtime。任务启动后，durable stage attempt、queue、wakeup、retry/dead-letter、resume、worker residency 和 generic lifecycle/projection 由 OPL/Temporal 持有；MAS 不内置或恢复 generic daemon、scheduler、attempt loop、queue hydration、provider retry 或 resume owner。
- 决策：`Codex CLI` 是 stage 内默认 concrete executor，继续负责读取 MAS stage packet、调用 MAS controller/tool、产出分析、写作、修复、验证与 stage closeout；Codex App / MAS app skill 是 direct entry 和人机操作面，不是任务启动后的外围持续 driver。
- 决策：`runtime_backend_default_operation_contract.default_autonomous_runtime`、product-entry `provider_topology.default_autonomous_runtime`、product-entry/sidecar `managed_temporal_state_consistency.default_autonomous_runtime` 和 `runtime_transport_handoff_projection.default_caller_policy` 必须持续暴露该口径：`hosted_runtime_owner=one-person-lab`、`hosted_runtime_provider=temporal`、`wakeup_retry_resume_owner=one-person-lab`、`codex_app_outer_driver_required=false`、`mas_daemon_scheduler_attempt_loop_allowed=false`。
- 理由：MAS 是标准 OPL domain agent，应该保留医学研究 truth、stage semantics、AI reviewer / quality gate、publication route、artifact authority、owner receipt 和 typed blocker；长期在线调度、唤醒、retry、resume 和 attempt ledger 是 OPL Framework / Temporal 的 generic runtime 能力。
- 影响：后续 runtime/status/sidecar/product-entry/docs 变更若把 `mas_runtime_core`、Codex App 外围会话、local scheduler、Hermes cron 或 MAS runtime transport 写成默认 generic runtime owner，均视为边界回归。真实 paper-line 进展仍以 MAS owner receipt、progress delta、gate replay、human gate、stop-loss 或 stable typed blocker 为准。

## 2026-05-21：fresh domain transition 必须在 runtime turn 前物化为 controller decision

- 决策：当 `progress_projection` / `last_launch_report` 的当前路线是 `domain_transition_ai_reviewer_re_eval`，且 next work unit 是 `return_to_ai_reviewer_workflow` / `ai_reviewer_medical_prose_quality_review` 时，resume / relaunch preflight 必须先调用 MAS outer-loop 写出 non-dispatching `artifacts/controller_decisions/latest.json`，再启动 provider-backed runtime worker。
- 决策：runtime-core auto-continue 路径也必须执行同一 currentness preflight。`CodexExecTurnRunner.start_turn` 在生成 prompt、同步 `.ds/runtime_state.json:current_controller_authorization` 前，必须先把 current AI reviewer domain transition 物化为当前 controller decision；否则自动续跑会绕过 resume / relaunch preflight，继续消费 stale gate authorization。
- 决策：如果旧 `controller_decisions/latest.json` 仍指向 `run_gate_clearing_batch` / `publication_gate_recheck`，它不能继续成为新 turn 的 `current_controller_authorization`。worker prompt 的授权真相仍只来自 MAS controller decision；status read-model 只触发 preflight materialization，不直接授权论文质量或 package 写入。
- 理由：DM003 暴露出 latest reviewer revision 已触发 AI reviewer re-eval read-model，但新 run 仍从 stale controller decision 吃到旧 gate-clearing authorization，导致 runtime 反复跑 gate recheck，论文质量反馈没有进入 AI reviewer workflow。
- 影响：这是 MAS controller/currentness 修复，不是 OPL provider lifecycle 修复。OPL 仍负责 attempt、queue、retry/dead-letter 和 provider liveness；MAS 只保证医学 owner route 在每个 managed turn 前有当前 controller decision 可供 runtime worker 消费。

## 2026-05-21：runtime liveness / redrive 仲裁不得继续在 MAS 私有控制面扩写

- 决策：暂停并撤回把 `active_run_id` liveness 过滤、stopped/failed redrive 仲裁、provider resume 选择或 current AI reviewer route-back hydrate 继续写进 `study_outer_loop.py` / `domain_status_authority.py` / `domain_transition_arbitration.py` 的修复方向。MAS 只能输出医学 owner route、controller authorization refs、AI reviewer/publication gate verdict refs、owner receipt 和 typed blocker；通用 liveness、attempt、queue、redrive、hydration、retry/dead-letter 与 provider resume 由 OPL provider/runtime manager 承担。
- 理由：DM002 当前症状是 MAS 已有 AI reviewer-backed `route_back_same_line -> analysis-campaign/unit_harmonized_validation_uncertainty_and_grouped_calibration`，但 human/status 面仍被 `quest_waiting_platform_repair_redrive`、submission metadata parking 和 external_supervisor route 覆盖。这是 OPL runtime/provider 投影和任务 hydration 缺口，不能继续靠 MAS 私有 runtime/status arbitration 补洞。
- 影响：本轮不得新增 MAS runtime liveness patch。若需要推进真实论文线，应通过 OPL family runtime queue/attempt hydration 消费 MAS sidecar/domain route refs，再回到 MAS owner surface 产出 domain receipt 或 stable typed blocker；MAS repo 只允许补 domain pack、owner callable、quality gate、receipt schema、refs-only adapter 或边界台账。

## 2026-05-21：OPL owner-route handoff 不得写 `.ds` runtime state

- 决策：`owner_route_reconcile_platform_repair` 触发 `quest_waiting_opl_runtime_owner_route` 时，MAS 只能写 `artifacts/supervision/owner_route_handoff/latest.json` 这类 MAS-owned supervision artifact，并通过 `sidecar export` 暴露 `domain_route/reconcile-apply` pending task。它不得把 `last_opl_runtime_owner_route_handoff`、`wait_for_opl_runtime_owner`、`active_run_id=None` 或 `worker_running=False` 写回 `quest_root/.ds/runtime_state.json` / `.ds/events.jsonl`。
- 理由：`.ds/runtime_state.json` 是 generic runtime/provider 状态面；即使 MAS 不再直接 relaunch/resume，只要继续清 `active_run_id` 或写 continuation state，就仍在替 OPL 维护 runtime liveness/control-plane。正确边界是 MAS 发布 owner-route refs，OPL queue/attempt/provider 消费这些 refs。
- 影响：owner-route apply result 的 `allowed_write_surfaces` 收窄到 `artifacts/supervision/**` 与 autonomy repair lifecycle/action refs；OPL 通过 sidecar task hydration 读取 handoff artifact。该路径不写论文、publication eval、controller decisions、submission package、current package，也不声明 OPL 已完成 dispatch。

## 2026-05-21：Progress Portal 与 submission milestone runtime action 只产出 OPL owner-route

- 决策：Progress Portal `--enable-actions` 下的 `pause` / `resume` / `stop` 不再调用 MAS managed runtime backend，也不返回 `runtime_control_apply`。它只写 `mas_progress_portal_action_receipt`，`mode=runtime_owner_route_request`、`apply_status=owner_route_required`，并给出 `queue_owner=one-person-lab` 的 runtime owner handoff。
- 决策：`owner_route_reconcile_submission_milestone_park` 在刷新 MAS controller-owned parked decision 后，不再直接调用 `stop_quest`。如果 quest 尚未 stopped，它写 `owner_route_required` lifecycle 与 runtime stop handoff；只有已经 stopped 的状态才可记录 `already_stopped` parked lifecycle。
- 理由：pause/resume/stop、attempt lifecycle、queue hydration、retry/dead-letter 和 provider liveness 都是 OPL runtime owner 职责。MAS 只能决定医学/交付语义上的 submission milestone parking，并发布 OPL 可消费 handoff。
- 影响：这两条路径都不写 `.ds/user_message_queue.json`、不调用 generic runtime chat、不改 provider runtime state、不写 `paper/`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package` 或 submission package。OPL 消费 handoff 后仍必须回到 MAS owner chain 产出 owner receipt、progress delta、human gate、stop-loss 或 stable typed blocker。

## 2026-05-21：controller refresh 只能产出 OPL runtime-owner handoff

- 决策：`refresh_controller_decisions_for_current_publication_eval` 在物化 current controller decision 后，不再调用 `ensure_study_runtime`、不 pause/resume live worker、不写 `last_controller_decision_authorization` 到 `.ds/runtime_state.json`，也不向 `.ds/events.jsonl` 追加 runtime event。它只能返回 refs-only `runtime_owner_handoff`，其中包括 current work unit、fingerprint、proposed runtime-state delta、`queue_owner=one-person-lab` 与 authority boundary。
- 理由：AI reviewer route-back、publication aftercare、domain transition 和 bundle-stage closeout 都是 MAS domain truth / owner-route refs；真正的 queue hydration、provider attempt、retry/dead-letter、pending user message redrive、live prompt refresh 与 worker lifecycle 是 OPL generic runtime 职责。继续由 MAS 写 authorization 或触发 provider resume，会把 MAS 重新变成私有 runtime/control-plane owner。
- 影响：旧测试中“MAS 写 authorization 后请求 resume”的断言已改为“MAS 不调用 provider lifecycle API、不改 runtime state、只交给 OPL owner route”。`authorization_status` 使用 `owner_handoff_ready` / `pending_user_message_owner_handoff_ready`，`runtime_resume_status=owner_route_required`。论文、publication eval、controller decisions、current package 与 submission package 的权威仍由对应 MAS owner surface 决定。

## 2026-05-21：domain route-back 在 progress read-model 中优先于交付停驻投影

- 决策：`study_progress` 必须只读透传当前 `domain_transition`，并且当 `domain_transition` 指向当前 route-back owner / work unit 时，即使 `interaction_arbitration` 尚未存在，`auto_runtime_parked` 也不得把该状态投影为 submission metadata、package-ready handoff 或 manual-finish parking。
- 理由：DM002 暴露出医学 owner 已经给出 `analysis-campaign/unit_harmonized_validation_uncertainty_and_grouped_calibration` work unit，但人读进度面仍显示交付停驻，导致维护者看不到下一步应由哪个医学 owner 处理。这里需要修的是 MAS domain read-model 的可见性和优先级，不是让 MAS 接管 OPL 的 liveness、queue、attempt 或 provider resume。
- 影响：该修复只改变 `study_progress` / Progress Portal / product-facing projection 的只读显示。它不生成 runtime attempt，不写 `.ds/user_message_queue.json`，不调用 generic runtime chat，不写 `paper/`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package` 或 submission package，也不声明 OPL queue/provider 已消费 owner-route。

## 2026-05-21：旧 residue audit 不再作为 current product/sidecar surface 暴露

- 决策：已进入 tombstone/provenance 的旧 MDS / Hermes / local scheduler residue 不再通过 current product-entry manifest 或 sidecar export 暴露独立 audit surface。当前机器真相只保留 `legacy_retirement_tombstone_proof`、`functional_consumer_boundary.retired_legacy_residue_tombstones` 和 `contracts/runtime/legacy-active-path-tombstones.json`。
- 理由：旧 audit surface 已无 active caller，只是在 current manifest 上重复呈现 tombstone/provenance 结论，继续保留会让 product/sidecar 面看起来仍有 legacy cleanup entrypoint。清理后，测试改为断言旧 audit 字段不存在，并继续检查 tombstone proof 与 retired residue machine surface。
- 影响：这只删除已无 current caller 的 audit 程序面，不删除仍有 active domain / diagnostic caller 的 `runtime_transport/`、turn runner、worker lease、`lifecycle_refs_adapter.py`、workbench shell、owner-route handoff adapter 或 status projection。后者仍按 active caller proof、OPL parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 tombstone/provenance refs 的删除门推进。

## 2026-05-22：medical prose write repair 必须前移到 canonical 稿面 delta

- 决策：`medical_prose_write_repair` 是 upstream paper-write work unit，完成证据必须包含 canonical manuscript-facing delta，即 `paper/draft.md` 或 `paper/build/review_manuscript.md`。`quality_repair_batch_upstream` 不能为该 work unit 生成正文 repair note，也不能把已有稿面列入 `canonical_artifact_refs` 后让 `repair_execution_evidence` 当成本轮 changed ref；在缺少 write-owner 稿面 delta 时必须返回 `manuscript_story_surface_delta_missing -> next_owner=write`。
- 决策：ledger-only delta 对 `medical_prose_write_repair` 不再足够。即使 `claim_evidence_map`、`evidence_ledger`、`review_ledger` 和 AI reviewer request 已更新，若没有 `paper/draft.md` 或 `paper/build/review_manuscript.md` delta，`paper_repair_execution_evidence` 必须返回 `manuscript_story_surface_delta_missing`，不得声明 `progress_delta_candidate`。
- 决策：`manuscript_story_surface_delta_missing` blocker 的 owner-route 与 runtime prompt 不只适用于 `manuscript_story_repair`，也适用于 `medical_prose_write_repair`。当 AI reviewer-backed `publication_eval/latest.json` 推荐 `route_back_same_line -> write/medical_prose_write_repair`，且 quality repair batch 已给出 `next_owner=write` 的 story-surface blocker 时，controller currentness projection 必须保留 `medical_prose_write_repair` 这个 work unit，并把 `run_quality_repair_batch` 投给 write owner；不得把它硬编码回 `manuscript_story_repair`，也不得停在 publication-gate stale recheck。
- 决策：`run_quality_repair_batch` 是 owner-route 可消费 action。`domain-route-reconcile` 的 materializer/dispatcher 必须能把该 action 物化为 Codex default executor dispatch，并调用 MAS-owned `quality_repair_batch.run_quality_repair_batch`；执行结果若仍为 `manuscript_story_surface_delta_missing`，必须保留该 typed blocker 与 `next_owner=write`，不得伪装成论文质量已完成或 submission-ready。
- 决策：若当前 `publication_eval/latest.json` 与同一 `source_eval_id` 的 `quality_repair_batch/latest.json` 已形成 `manuscript_story_surface_delta_missing -> next_owner=write`，`owner-route-reconcile` 必须优先产出 write-owner `run_quality_repair_batch` owner route。旧 `ai_repair_lifecycle.blocked_reason=domain_transition_ai_reviewer_re_eval` 只能作为历史观测，不能把 `owner_route.next_owner` 覆盖回 `ai_reviewer`，也不能让 `action_queue=[]`。
- 决策：`domain_owner_action_dispatch` 写出的 `artifacts/supervision/consumer/default_executor_execution/latest.json` 是同一 owner route 的执行 receipt。若 receipt 中的 `action_type`、`idempotency_key` 或 owner-route currentness 与当前 `owner_route` 匹配，且 `execution_status=executed` 并带有 owner result / repair evidence 执行证据，`owner-route-reconcile` 必须消费该 receipt 并清空同一 action queue，直到新的 truth/currentness basis 出现。该消费只关闭重复投递，不授权 quality、submission、current package 或 publication-ready。
- 理由：DM002 暴露出 write-owner `run_quality_repair_batch` 已通过 default executor 产生 progress delta、gate replay 和 AI reviewer recheck 请求，但下一轮 scan 因未读取执行 receipt 继续投递同一 action。正确边界是消费 MAS owner receipt，不手工更新 queue，不把重复投递问题塞给 OPL provider 或单篇 paper surface。
- 理由：DM003 暴露出 medical prose route-back 被 MAS upstream repair 处理时只更新 ledger/request，用户看到的高质量医学初稿稿面没有前移。该规则把 prose/write repair 的 owner surface 与 `manuscript_story_repair` 对齐，防止 quality repair batch 用内部 ledger 变化替代正文修订。
- 影响：这是 canonical paper owner surface currentness 修复，不是医学质量 ready verdict。AI reviewer、publication gate 和后续 delivery owner 仍负责正式质量判断、publishability 与 submission-facing package；controller repair 只保证 write repair 不再 ledger-only 完成，也不把 MAS/controller/AI reviewer 内部运行态措辞写入论文正文。

## 2026-05-22：story-surface blocker 是 writer handoff ready，不是 terminal dispatch blocker

- 决策：`quality_repair_batch` 对 `manuscript_story_surface_delta_missing` 的本轮证据判断仍保持 fail-closed：没有 `paper/draft.md` 或 `paper/build/review_manuscript.md` delta 时，不得声明 paper repair completed、quality ready 或 submission-ready。但当该 blocker 已明确 `next_owner=write` 时，batch 的 owner result 必须返回 `status=handoff_ready`、`ok=true`、`blocked_reason=null`，并携带 `default_executor_dispatch_request` 形态的 `writer_worker_handoff`，要求 write owner 产出 canonical manuscript story-surface delta 或同名 typed blocker。
- 决策：上述 `writer_worker_handoff` 不能只嵌在 batch/sidecar receipt 里；`quality_repair_batch` 必须同时按 handoff 自带的 `refs.dispatch_path` 物化到 `artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json`，让 MAS default executor dispatcher 能以现有 owner-request 校验继续消费。没有该 dispatch 文件时，`will_start_llm_worker=true` 只是 transport receipt，不能视作 writer 已接手。
- 决策：`paper_repair_executor`、`domain_owner_action_dispatch`、runtime dispatch cost 和 MAS sidecar dispatch 必须把该 `handoff_ready` 视为可调度下游 worker 交接。sidecar 顶层 receipt 保持 `accepted=true`、`will_start_llm_worker=true`，并暴露 downstream writer handoff；不得把该 case 变成 OPL queue 的 terminal reject、retry/dead-letter 或 generic owner callable blocker。
- 决策：writer handoff 只能授权 canonical paper/write owner surface，例如 `paper/draft.md`、`paper/build/review_manuscript.md`、claim-evidence/evidence/review ledger；它继续禁止 `paper/submission_minimal/`、`manuscript/current_package/`、`publication_eval/latest.json`、`controller_decisions/latest.json`、current package、quality gate verdict 和 MAS platform/runtime surface 写入。
- 理由：DM002/DM003 暴露出 `manuscript_story_surface_delta_missing` 被错误提升为终态 blocked receipt，导致 OPL provider 层反复 retry/dead-letter，而真实缺口是 MAS write owner 还没有接过正文稿面修订。正确边界是 MAS 医学论文 owner-chain 继续交给 writer，不是 OPL queue/runtime 修复，也不是手工 patch 单篇论文。
- 影响：这是 MAS paper autonomy / owner dispatch / sidecar receipt 语义修复。它只把 same-owner write follow-through 变成可执行 worker handoff，不放宽 AI reviewer 或 publication gate，不授权直接改 DM002 study truth、delivery package、current package、publication eval、controller decision 或 submission readiness。

## 2026-05-22：medical prose writer materializer 产出 canonical 正文 delta

- 决策：`medical_prose_write_repair` 在 canonical paper inputs 足够时，不再停留在 ledger-only repair 或 writer handoff；MAS writer-owner materializer 必须从 `paper/` 下的 methods/cohort/display/treatment-gap/transition/table/evidence surfaces 生成 `paper/draft.md`，并同步 `paper/build/review_manuscript.md`。
- 决策：该 materializer 必须覆盖 observational phenotype treatment-gap family 的核心质量目标：phenotype derivation transparency、recorded treatment-review gap terminology、BP/data-quality assessment、baseline characteristics table、numeric abstract/results、restrained discussion 和无运行态正文语言。它不得读取或复制 `manuscript/current_package`、delivery mirror、旧 runtime archive、inspection package 或其他非 canonical authority surface。
- 决策：若同一 `source_eval_id` 的上一轮 `quality_repair_batch` 已因 `manuscript_story_surface_delta_missing` 阻塞，且当前 `paper/draft.md` 与 `paper/build/review_manuscript.md` 相对上一轮 blocker 记录的 story-surface fingerprint 已同步变化、无内部运行态术语、并具备 journal manuscript 基本结构，`medical_prose_write_repair` 必须保留该 writer-owned story delta，不得用 generator 模板覆盖更成熟正文。
- 决策：story-surface 完成证据必须在 mutation 后 live-read 当前 canonical files。`repair_execution_evidence.manuscript_surface_hygiene.story_surface_delta_refs` 和 `canonical_artifact_delta.artifact_refs` 记录的 fingerprint 必须来自当前 `paper/draft.md` / `paper/build/review_manuscript.md`，不能复用 pre-write、fixture、旧 template 或上轮 blocked fingerprint。对 `medical_prose_write_repair` 的 currentness-delta adoption，完成证据还必须复用同一套 writer-story guard：同一 `source_eval_id`、上一轮 story-delta blocker、两份 story surface 同步变化且内容一致、无运行态术语、具备 journal manuscript 基本结构；单边更新、内容不一致或非 journal 正文不得补成 `story_surface_delta_present`。
- 决策：DM003 observational phenotype treatment-gap writer materializer 的 Methods 必须显式覆盖 study design/cohort、variable definition and measurement、phenotype derivation and assignment、model/grouping framework、recorded treatment-review gap definitions、data quality assessment、validation framework 与 statistical analysis；Results 以临床估计和 denominator 为句子主语，display 只作证据引用。
- 决策：`paper_repair_executor` 的普通 text/claim repair 默认目标改为 `paper/draft.md`；只有旧 workspace 缺 `draft.md` 且存在 `paper/manuscript.md` 时，才保留 legacy manuscript 作为迁移期输入。`draft.md` 和 `build/review_manuscript.md` 的 artifact role 是 `canonical_manuscript_story_surface`，旧 `paper/manuscript.md` 不再是新路线的主 story surface。
- 理由：DM003 暴露出 MAS 工作流可以识别写作质量问题，却没有把反馈实际落成用户可见的正文变化。单靠 revision intake、ledger、AI reviewer request 或 handoff 不能保证初稿质量前移；write owner 必须能在当前 owner-chain 内把 canonical evidence 转成 journal-facing manuscript surface。
- 影响：这是 MAS manuscript autonomy 能力修复，不是单篇论文手工修稿，也不是质量放行。AI reviewer recheck 和 publication gate 仍负责判断 `medical_journal_prose_quality`、publishability 和 submission-facing readiness；package/current_package 仍需后续 owner 授权刷新。

## 2026-05-22：stage quality pack contract catalog 按自然边界拆分

- 决策：`stage_quality_contract.py` 继续作为 public contract/API owner，保留 `build_stage_quality_pack_contract`、projection builder、pack id 常量和 `CONTRACT_REF`；静态 pack catalog、promotion evidence、owner refs 与 required refs 迁入 `stage_quality_contract_parts/catalog.py`，由 `stage_quality_contract_parts/__init__.py` 做显式 re-export。
- 理由：DM003 writer materializer 修复触发 smoke `line_budget` gate，暴露 `stage_quality_contract.py` 已超过 preferred boundary 且没有 reviewed baseline。正确处理方式是按 quality-pack catalog 自然边界拆分，而不是新增白名单或放宽 line budget。
- 影响：这是结构治理修复，不改变 stage quality pack contract 的 public callable 或 authority boundary；OPL projection 仍只能消费 descriptor/ref/freshness locator，不能授权 MAS truth、quality verdict、publication readiness 或 submission readiness。

## 2026-05-21：provenance-limited rebuild handoff 必须覆盖旧 methodology decision

- 决策：当 `artifacts/controller/provenance_limited_harmonization/latest.json` 已产出当前 `unit_harmonized_rerun_required` typed handoff，并明确 `next_owner=analysis_harmonization_owner`、`next_work_unit=unit_harmonized_external_validation_rerun`，且该 owner result 晚于它消费的 source provenance、controller decision 与 rebuild task intake 时，`owner-route-reconcile` 必须优先排 `analysis_harmonization_owner`，不能再被旧 `source_provenance/latest.json` terminal blocker 拉回 `methodology_reframe_route_decision`。
- 理由：DM002 暴露出 MAS 已由 provenance-limited owner 消费 clean rebuild authorization 并交棒给 analysis owner，但 read model 仍先读取旧 source terminal blocker，导致 action queue 回退到上一轮 decision owner，阻断 unit-harmonized rerun。这里的 currentness 真相来自 MAS 医学 owner result 的时间顺序和 typed handoff，不是通用队列或控制面状态。
- 影响：这是 MAS 标准 OPL Agent 的 domain owner-chain currentness 修复，只影响医学 owner route/read-model。它不把 OPL provider、queue、attempt ledger、session lifecycle 或 Agent Lab control plane 回塞进 MAS；也不授权写 `paper/`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package`、submission package 或 submission-ready verdict。

## 2026-05-21：stopped controller work-unit 不再由 MAS 私有 redrive 仲裁

- 决策：撤回“stopped + controller_work_unit_pending 必须由 MAS `progress_projection` 返回 `resume / quest_waiting_platform_repair_redrive`”这一方向。MAS 在 stopped / failed / waiting / live 组合状态下只发布当前 controller authorization、domain route、owner receipt、typed blocker 和 OPL 可消费 owner-route refs；通用 liveness 判断、queue hydration、attempt retry、dead-letter、provider resume/relaunch 由 OPL runtime manager 承担。
- 理由：DM002 暴露的是 current work unit 没有被 OPL 通用 runtime/hydration/dispatch 消费，而不是 MAS 应继续扩写私有 runtime/status state machine。把 stopped redrive 写进 MAS status 会把 OPL 标准智能体边界退回 MAS 私有控制面。
- 影响：MAS 可以通过 `sidecar export` 暴露 `domain_route/reconcile-apply`、paper autonomy、publication aftercare 等 pending owner-route refs，并通过 `sidecar dispatch` 回到 MAS owner callable 产出 receipt / typed blocker；MAS 不直接写 `.ds/user_message_queue.json`，不调用 generic runtime chat 作为控制器授权投递，不声明 OPL queue 或 provider attempt 已完成。

## 2026-05-21：analysis harmonization completed 后必须显式交回 AI reviewer currentness

- 决策：当 `analysis_harmonization_owner` 的 completed result 明确 `next_owner=ai_reviewer`、`next_work_unit=ai_reviewer_medical_prose_quality_review`，且当前 `publication_eval/latest.json` 没有 AI reviewer-owned provenance 覆盖 `analysis_harmonization/latest.json` 与 rerun evidence refs，`owner-route-reconcile` 必须排 `return_to_ai_reviewer_workflow`。
- 决策：上述 completed owner handoff 是当前医学质量 owner route，必须优先于旧的 `quest_waiting_platform_repair_redrive` / `quest_waiting_opl_runtime_owner_route` runtime platform lifecycle。platform redrive 可以继续作为 OPL runtime owner 证据存在，但不得把 `next_owner` 改成 `one-person-lab` 并过滤掉 AI reviewer action。
- 理由：DM002 暴露出 unit-harmonized external-validation rerun 已完成后，旧 `publication_eval` 仍可能早于 rerun evidence，却被 parked/current-truth 投影吞掉，导致 AI reviewer 不复评新模型与 uncertainty 证据。
- 影响：该修复只生成 AI reviewer request / owner route，不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/`、`submission_minimal`、`manuscript/current_package` 或 submission-ready verdict。若 AI reviewer eval 已显式引用当前 analysis result 与 rerun evidence，则不重复排队。

## 2026-05-20：新 reviewer_revision 必须使旧 AI reviewer eval 失效

- 决策：若 latest task intake 是 `reviewer_revision`，且其 `emitted_at` 晚于当前 `publication_eval/latest.json`，即使当前 eval 的 `assessment_provenance.owner=ai_reviewer`，domain transition candidate 与 domain route scan 也必须把 AI reviewer assessment 标为 stale/missing，并路由到 `return_to_ai_reviewer_workflow`。
- 理由：DM002 暴露出用户最新医学论文质量反馈已进入 durable task intake，但旧 AI reviewer eval 仍被 read model 当作 current，导致 official quality loop 没有吸收新反馈。
- 影响：这是 MAS domain agent 的 AI reviewer currentness 规则，不是 OPL 基座控制面变更。它只请求 AI reviewer owner 重新评估；不授权脚本判断论文质量，不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、正文、submission package 或 `current_package`。

## 2026-05-20：当前 run 的 completed turn closeout 必须被 controller work unit 消费

- 决策：当当前 active run 写出 `artifacts/runtime/turn_closeouts/<active_run_id>.json`，且 closeout 为 `status=completed`、`meaningful_artifact_delta=true`、未带 `blocked_reason`，controller work-unit evidence adoption 必须把它作为当前授权的完成证据消费，并写入 `controller_work_unit_evidence_adoption` / `artifact_written`，而不是继续重放同一 `manuscript_story_repair` 或其他 generic work unit。
- 决策：只有 `<active_run_id>` 精确匹配的 turn closeout 才可被消费。历史 run、非当前 run 或不带 meaningful artifact delta 的 closeout 不得关闭当前 work unit；这些情况仍按现有 relay/dedupe/runtime-liveness 逻辑处理。
- 理由：DM002 暴露出 MAS write owner 已经更新 `paper/draft.md` 与 `paper/build/review_manuscript.md` 并写出有效 turn closeout，但 controller 只扫描 work-unit receipt / write / intake 等旧候选目录，未读取当前 run closeout，导致同一 `manuscript_story_repair` 被重复拉起。
- 影响：这是 owner receipt/currentness 消费修复，不是质量门槛放宽。它只阻止已完成 work unit 被重复执行；医学论文质量、AI reviewer verdict、publication gate、submission package 和 `current_package` 仍必须由对应 MAS owner 重新评估和刷新。

## 2026-05-20：manuscript story repair 的稿面 fingerprint delta 可被同一 blocker 消费

- 决策：`manuscript_story_repair` 与 `medical_prose_write_repair` 仍要求 `paper/draft.md` 或 `paper/build/review_manuscript.md` 作为 canonical story-surface delta。若上一轮同一 `source_eval_id` 已因 `manuscript_story_surface_delta_missing` 阻塞，`quality_repair_batch` 只能在当前稿面内容指纹相对上一轮 blocked batch 记录的 story-surface fingerprint 发生变化时，把稿面作为 canonical changed refs 消费。
- 决策：不得再用 `publication_eval/latest.json` mtime、gate replay mtime、ledger mtime 或“稿件比旧 eval 新”这类文件时间启发式推断 story repair 完成。缺少上一轮 blocked batch 的 surface fingerprint 时，必须继续 fail closed 到 write owner。
- 理由：DM002 暴露出 write owner 已修订 canonical 稿面但 gate batch 只返回 ledger refs；DM003 进一步暴露出早就晚于 stale `publication_eval/latest.json` 的旧稿面也可能被误读为当前 progress delta。这是 owner receipt/currentness 消费漏洞，不能通过放宽 quality gate 或脚本评价论文质量解决。
- 影响：初次 repair batch、stale 稿面、ledger-only delta 和非同一 `source_eval_id` 的旧 blocker 仍 fail closed。该机制只解除“稿面 delta 不可见”的机械 blocker；医学写作质量、publishability、submission readiness 与 package refresh 仍由 AI reviewer、publication gate 和对应 MAS owner 决定。

## 2026-05-20：manuscript story repair 必须证明正文稿面发生 delta

- 决策：`manuscript_story_repair` 不能只靠 `claim_evidence_map`、`evidence_ledger`、`review_ledger`、display/table/figure 生成物或 gate replay 变化声明完成。若该 work unit 没有把 `paper/draft.md` 或 `paper/build/review_manuscript.md` 作为 canonical changed artifact ref，`repair_execution_evidence` 必须返回 `status=blocked`、`progress_delta_candidate=false`、`canonical_artifact_delta.status=blocked`，并给出 `manuscript_story_surface_delta_missing`。
- 决策：`quality_repair_batch` 必须消费上述 blocked evidence，把批次顶层状态改为 `blocked`、`ok=false`、`next_owner=write`，不得继续把 gate-clearing batch 的局部 artifact delta 汇总成 completed repair。
- 理由：DM002 暴露出 `manuscript_story_repair` 多次只更新 claim/evidence/review ledger 和 display 生成物，正文 `paper/draft.md` 与 `paper/build/review_manuscript.md` 未变，却被 runtime 记录成 meaningful artifact delta。这样会让 owner-chain 看起来已经修复“干净 external-validation story”，但用户看到的稿件仍停在旧正文。
- 影响：这是 owner-surface currentness 和 typed blocker 规则，不是脚本式论文质量 verdict。它只防止错误 owner 用错 surface 关单；正式医学论文写作质量、publishability 和 submission readiness 仍由独立 AI reviewer、publication gate 与后续 delivery owner 决定。

## 2026-05-20：current AI reviewer route-back 必须压过重复 reviewer recheck

- 决策：当 `publication_eval/latest.json` 由 `assessment_provenance.owner=ai_reviewer` 产出，且 `reviewer_operating_system.currentness_checks.medical_prose_review.status=current`、`route_back_required=true`、`route_target` 指向非 `review` owner，同时顶层 `recommended_actions[]` 有匹配的 `route_back_same_line` controller action 时，controller refresh 和 domain transition 不能再把同一份 current eval 解释成 `ai_reviewer_re_eval`。
- 决策：上述 route-back 是 AI reviewer 已完成当前医学写作质量判断后的 owner route。`medical_journal_prose_quality` 仍可为 `blocked` 或 `partial`，但下一步应由 `write`、`analysis-campaign` 或 AI reviewer 指定的 owner 执行；只有缺 currentness 证明、缺匹配 recommended action、route target 为 `review`、或 reviewer OS trace 不合规时，才回到 AI reviewer recheck。
- 理由：DM002 暴露出 AI reviewer 已明确 `route_back_same_line -> write/manuscript_story_repair` 后，旧 `ai_reviewer_re_eval` domain transition 仍覆盖该 owner decision，导致系统重复复评或停在旧 review work unit，无法把“清理内部修复痕迹、重写干净 external-validation story”的任务交给 write owner。
- 影响：这是 owner-chain currentness 修复，不是质量 gate 放宽。AI reviewer 仍持有医学写作质量 verdict；controller 只负责消费 current reviewer OS route-back 并生成下一 owner 决策，不写 study truth、论文正文、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 `current_package`。

## 2026-05-20：AI reviewer 重新评估必须刷新 stale paper-authority receipt

- 决策：clean paper-authority migration 进入 `new_mas_authority_established` 后，如果当前 `publication_eval/latest.json` 已不再匹配 receipt 中记录的 AI reviewer eval，新一轮 AI reviewer workflow materialize 的 eval 必须刷新 `paper_authority_cutover/latest.json` 的 `new_mas_authority` 指针。已准确指向当前 eval 的 receipt 保持幂等。
- 理由：DM002 暴露出 stale receipt 会让 controller/status refresh 把 AI reviewer-owned eval 重新降回 publication-gate mechanical projection，导致 reviewer operating system 丢失，并让 owner-chain 反复回到 AI reviewer trace missing。
- 影响：AI reviewer 是 publication quality authority；mechanical projection 只能作为需要 AI reviewer 的输入或 blocker，不得覆盖当前 AI reviewer-owned eval。后续 controller decision refresh 必须消费 owner eval 及其 reviewer OS，再推进 write / gate / delivery owner。

## 2026-05-19：publication currentness 必须消费当前 owner receipt，且区分正文面与内部审阅面

- 决策：`analysis_claim_evidence_repair/latest.json` 若带有当前 work-unit fingerprint、`controller_action_invoked_first.action=run_quality_repair_batch`、完整 `targeted_publication_specificity_targets`、`canonical_artifact_delta.meaningful_artifact_delta=true`，并且 gate replay 已证明目标 blocker 被清除，controller work-unit evidence adoption 必须消费该 receipt，下一跳回到 publication gate recheck，不得继续向 runtime 重放同一 `analysis_claim_evidence_repair` fingerprint。
- 决策：`publication_surface_residue` 的 manuscript blocker 只扫描正文、figure/table catalog、paper-facing narrative/claim/evidence/reproducibility contracts 等会投向稿件的 surface。AI reviewer prose review、review ledger、statistical reviewer audit 和 structured disclosure audit 继续做 schema/quality 输入验证，但其中的 provenance、repair memory 或 reviewer diagnosis 不能被当作 manuscript forbidden-term blocker。
- 决策：`review_ledger.concerns[].status=resolved_upstream_package_refresh_pending` 是 canonical issue 已解决、仅等待下游 package refresh 的 closed-like 状态；它通过 review ledger schema validation，并在 reviewer-first readiness 中计入 resolved concern，而不是 open/in-progress blocker。
- 理由：DM002 最新轨迹中，analysis repair 已清掉 table/figure/claim map blocker，但旧 authorization 未被消费会导致同一 analysis work unit 反复重放；同时 AI reviewer provenance 里保留“raw-scale / unit-harmonization lesson”作为内部诊断，却被 publication surface 扫成正文 residue，制造假 blocker。review ledger 也已表达 canonical repair 完成但 package refresh 待下游执行，validator 不应因为未知 closed-like 状态把它降级为 schema failure。
- 影响：这不是 legacy compatibility 或宽松 normalizer；未知 receipt/status 仍 fail closed。只有带当前 fingerprint、明确 owner action、完整 targets 和 gate replay proof 的 receipt 才能被 consumption layer 采纳。错误分析轨迹仍不得进入正文；内部 reviewer/provenance 面可以保存原因和记忆，供 MAS/Agent Lab 自进化和 route-back 使用。

## 2026-05-19：quality repair 不能在正文残留或机械投影 ready 时声明进展

- 决策：`repair_execution_evidence` 的 manuscript surface hygiene 不只适用于 `manuscript_story_repair`，也适用于会影响主叙事闭环的 `analysis_claim_evidence_repair`、`figure_results_trace_repair` 和 `medical_prose_quality_analysis_source_documentation_repair`。这些 work unit 若在 canonical `paper/draft.md` 或 `paper/build/review_manuscript.md` 中检测到 invalid analysis history residue，只能返回 typed blocker，不能声明 `progress_delta_candidate`。
- 决策：`assessment_provenance.owner=mechanical_projection` 或 `ai_reviewer_required=true` 的 publication gate projection 不能把 `medical_journal_prose_quality` 标成 `ready`。即使 gate report 携带 `medical_prose_review_status=ready`，机械投影也必须降级为 `underdefined`，并把下一跳交回 AI reviewer currentness / manuscript-native prose review。
- 理由：DM002 暴露出两类同源漂移：analysis/claim-evidence repair 可以只更新 ledger 类 artifact 却让正文保留 raw-scale / preprocessing-error 叙事残留；同时机械 publication projection 可以带着“AI reviewer required”的 provenance 把主观医学写作质量显示为 ready。这会让 MAS 看起来通过质量闭环，但用户看到的论文仍保留错误故事或旧交付面。
- 影响：这是 MAS controller/read-model 的 safety floor，只负责 fail closed、route back 和回归保护；它不以脚本检查论文替代 AI reviewer，也不授权 publication ready、submission ready 或 `current_package` 更新。真正的医学论文写作质量仍由独立 AI reviewer / reviewer OS record、publication gate 和 owner receipt 闭合。

## 2026-05-18：AI reviewer dispatch 优先消费 current request record

- 决策：`return_to_ai_reviewer_workflow` 执行时，若 `artifacts/supervision/requests/ai_reviewer/latest.json` 已携带 AI reviewer-owned publication eval record，dispatch executor 必须先校验并消费该 request-attached record；只有 request 未携带 record 时，才允许回退读取 active `publication_eval/latest.json` 或 clean-migration interim record。
- 决策：旧 `publication_eval/latest.json` 即使是 `assessment_provenance.owner=ai_reviewer`，只要它缺 `future_facing_limitations_plan`、仍是 clean-migration underdefined projection，或早于当前 AI reviewer response record，就不得阻断 request record 物化。request record 仍需满足相同 fail-closed 要求：AI reviewer provenance 可接受、`quality_assessment` 存在、`future_facing_limitations_plan` 非空。
- 理由：DM002 暴露出 AI reviewer response 目录和 supervision request 已经携带当前 `partial/revise -> analysis` 质量结论，但旧 active latest 缺顶层 future plan，导致 executor 先报 `ai_reviewer_record_incomplete`，没有把当前 AI reviewer record 写回 publication eval truth。
- 影响：AI reviewer 仍是质量判断 owner；dispatch 只修正当前 owner record 的消费优先级，不从 prose review 文本临场拼 verdict，不放宽 record schema，不写 `paper/`、`controller_decisions/latest.json`、`manuscript/current_package` 或 submission readiness。

## 2026-05-18：runtime-guard stage 必须声明 runtime event refs 才能通过 OPL admission

- 决策：`family_stage_control_plane` 中所有 `trust_boundary.runtime_guard_required=true` 的 stage，必须在 `trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs` 中声明 machine-readable runtime event refs。缺 refs 时视为 MAS 结构/功能 gap，OPL admission finding 不能降格为纯测试/证据缺口。
- 决策：当前 6 个 MAS stage refs 固定为：`direction_and_route_selection` 回指 `runtime_event:domain_route_owner_route.direction_route_selected` 与 `runtime_event:controller_decisions.direction_route_selected`；`baseline_and_evidence_setup` 回指 `runtime_event:controller_decisions.baseline_evidence_ready` 与 `runtime_event:evidence_ledger.baseline_evidence_ready`；`bounded_analysis_campaign` 回指 `runtime_event:domain_health_diagnostic.bounded_analysis_evidence_ready` 与 `runtime_event:evidence_ledger.bounded_analysis_evidence_ready`；`manuscript_authoring` 回指 `runtime_event:controller_decisions.manuscript_draft_reviewable` 与 `runtime_event:canonical_manuscript.manuscript_draft_reviewable`；`review_and_quality_gate` 回指 `runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded` 与 `runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded`；`finalize_and_publication_handoff` 回指 `runtime_event:controller_decisions.publication_handoff_ready_or_route_back_recorded` 与 `runtime_event:artifact_authority.publication_handoff_ready_or_route_back_recorded`。
- 决策：只有 OPL proof bundle / admission 对当前 MAS manifest 返回 MAS stage `admitted`、`blockers_count=0`、`warnings_count=0` 后，文档才能继续声明当前 `functional_structure_gap_count=0`。若 proof 未跑或 admission blocked，必须重新打开 stage-control-plane functional gap。
- 理由：runtime guard stage 都会进入 OPL stage attempt / queue / provider replay 边界。OPL 可以托管 attempt、queue、projection 和 replay，但不能替 MAS 猜测 route decision、baseline/evidence readiness、analysis evidence closure、draft reviewability、AI reviewer gate receipt 或 publication handoff event；这些 refs 必须由 MAS domain-owned stage control plane 明确暴露。
- 影响：新增或修改 MAS stage descriptor 时，runtime event refs 与 owner receipt、typed blocker、quality/artifact authority refs 同步维护。程序和文档不得把 descriptor ready、repo tests 或 generic generated surface proof 写成 admission 已通过。

## 2026-05-18：显式 task_intake_kind 是结构化 intake 的权威输入

- 决策：`submit-study-task --task-intake-kind reviewer_revision` 必须直接 materialize `revision_intake` 与 `submission_revision_operating_contract`，即使 `task_intent` 是英文、方法学勘误或不含旧的“审稿意见/导师反馈/manuscript revision” marker。
- 决策：`publishability_stop_loss` 继续优先于 reviewer revision；显式 `reviewer_revision` 只负责同线重新激活并路由到 write 或 analysis owner，不授权前台直接写 `paper/`、`manuscript/current_package/`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。
- 决策：当同一 reviewer revision intake 明确出现 `analysis/harmonization`、`methodology correction`、`unit-harmonized`、`unit-standardized`、方法学勘误、方法学污染、单位统一/对齐或数据归一化对齐等强语义时，progress override 必须路由到 `analysis-campaign`，不能继续停在 prose/write owner。
- 决策：controller decision refresh 必须把这类方法学 route-back 物化为 `bounded_analysis`，并保留 AI reviewer recommended action 中显式给出的 `analysis-campaign` work unit。`medical_journal_prose_quality` 未 ready 不能把 HDL/unit harmonization、模型复现、校准或不确定性阻塞抢回 `ai_reviewer_re_eval/review`；publication gate 的通用 story blocker 也不能覆盖 explicit methodology work unit。
- 决策：`medical_prose_quality_analysis_source_documentation_repair` 是 AI reviewer 方法学回退的 upstream analysis/paper repair work unit。`quality-repair-batch` 和 control-plane route gate 必须把它授权为 `paper_write`，不能默认落到 `bundle_build`；下游 bundle gate 阻断不应阻止 MAS managed worker 写 canonical paper / analysis repair evidence 或 typed blocker。
- 决策：HDL/unit harmonization、unit-standardized model application、`harmonization_route_back` 或 `unit_harmonized_external_validation_rerun` 这类 specificity target 是 hard methodology target。它们不得被普通 `medical_prose_quality_analysis_source_documentation_repair` completed receipt、display materialization、package freshness、AI reviewer prose note 或 generic gate-clearing replay 关闭；`quality-repair-batch` 必须先写 `blocked_reason=unit_harmonized_rerun_required`，`next_owner=analysis_harmonization_owner`，`next_work_unit=unit_harmonized_external_validation_rerun`，再由对应 owner 产出 unit-harmonized rerun evidence 或 typed blocker。
- 理由：DM002 HDL 单位污染反馈暴露出入口缺陷：用户显式给了 `task_intake_kind=reviewer_revision`，但旧逻辑只按文本 marker 识别，导致英文方法学 correction 没有生成 `revision_intake`，可能被弱化为普通上下文消息。
- 理由：同一 DM002 反馈还暴露出第二层路由缺陷：即使 `revision_intake` 已 materialize，`analysis/harmonization rollback` 仍会因为旧 analysis marker 太窄而被路由成 `write/manuscript_story_repair`。方法学输入污染必须先由 analysis/harmonization owner 处理，不能靠写作层弱化措辞。
- 理由：后续 runtime refresh dry-run 暴露出第三层缺陷：read-model 已显示 `analysis-campaign`，但 controller refresh 仍可能生成 `manuscript_story_repair/write` 或 `ai_reviewer_medical_prose_quality_review/review`。这种不一致会让运行态继续修文字，无法重跑或 typed-block 污染的分析。随后 live run 又暴露第四层缺陷：runtime prompt 已拿到方法学 work unit，但 route gate 不认识该 work unit，`quality-repair-batch` 回落成 `bundle_build` 并被 downstream-only gate 拦住。
- 影响：上层 agent、OPL meta-agent 或 human operator 可以用结构化 kind 表达 intent，不必为了触发 MAS 路由而在自然语言里塞 marker。未知 kind 仍不自动升级，保持 fail-closed。

## 2026-05-18：paper-authority migration 只处理 canonical study root

- 决策：`paper_authority_clean_migration` 的 study discovery 只能来自 canonical study marker / supervisor scan 认可的 study root。`studies/*` 下仅因为存在旧 `manuscript/current_package`、旧 paper authority surface 或迁移 archive 的目录，不得被升级为 study。
- 决策：非 canonical 旧 paper authority residue 必须作为 `noncanonical_paper_authority_residue_dirs` 报告，包含 path、reason 与命中的 surface refs；它只用于清理诊断和 provenance，不进入 study quality、publication gate、delivery 或 clean migration apply 队列。
- 理由：DM-CVD workspace 中的 `idea-idea-3839d99b` 与 `paper-run-dfcc79d2` 是旧 MDS / worktree residue。旧 discovery 逻辑把“有旧 paper authority surface”误当作“这是一个 study”，导致无 `study.yaml` / `runtime_binding.yaml` 的历史目录被迁移流程当成论文单元。
- 影响：旧项目迁移继续 fail closed，但 fail closed 的对象必须是 canonical study。未知或残留目录不再触发论文质量闭环、交付重建或 AI reviewer route；清理这些目录应走 workspace maintenance / provenance cleanup，而不是 paper-line owner workflow。

## 2026-05-18：高质量医学论文自进化目标投影给 Agent Lab，但质量 verdict 仍归 MAS AI reviewer

- 决策：`是否像高质量医学论文` 是 MAS domain-owned、AI reviewer-backed 的质量 scorecard。MAS 可以把该目标作为 refs-only external suite 投影给 OPL Agent Lab，用于自进化、回归学习、stage attempt 改进和 candidate promotion control plane。
- 决策：Agent Lab suite 只能引用 `publication_eval/latest.json`、canonical paper、evidence/review ledger、task intake、人工 reviewer feedback、runtime event ledger、provider/executor/context isolation refs 或 claim/evidence/reviewer/display refs；不得写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical manuscript、`paper/submission_minimal`、`manuscript/current_package` 或 submission readiness verdict。
- 决策：ARIS 后续可吸收点进入 MAS Agent Lab suite 时必须保持 typed body-free：`runtime_event_ledger` 只输出 `.ds/events.jsonl`、`artifacts/runtime/events.jsonl`、supervision/controller event refs 的 refs/count/type metadata；`provider_switch_hygiene` 只读投影 executor/provider/context isolation/provider fallback refs；`claim_assurance_map` 只投影 claim/evidence/reviewer/display refs 并声明 `body_included=false`。MAS 持有 runtime event body、claim body、review verdict、AI reviewer quality verdict、publication gate 和 artifact/current_package authority；OPL 只消费 refs/metadata 来生成机制候选、promotion decision、canary 和 rollback refs。
- 决策：针对 DM002 这类外部验证论文，Agent Lab quality target 应把 AI reviewer / reviewer feedback 中的主观医学论文质量目标沉淀为 route-back evidence refs，例如 HDL harmonization and sensitivity、model reproducibility、visible Table 1 / Table 2 performance reporting、uncertainty intervals and validation metrics、NHANES weighting / unweighted framing、calibration / risk-collapse figure quality、internal quality-language purge。是否 closed 仍由 MAS AI reviewer 重新审稿并写回 current quality authority。
- 决策：Agent Lab quality target 必须按 study quality family 生成。DM003 这类 observational phenotype / treatment-gap 论文的 self-evolution target 是 phenotype derivation transparency、recorded treatment-gap terminology、BP/data-quality assessment、baseline characteristics table、formal figures/tables、numeric abstract with uncertainty、restrained discussion/prose、reference style、claim-evidence alignment without runtime language，以及 method/data-error route-back；不得复用 DM002 的 HDL、NHANES 或 calibration/risk-collapse target。`developer_patch_work_order.study_quality_target_family` 与 `study_quality_targets` 是 OMA/opl-meta-agent 的标准消费面，不是质量 verdict。
- 决策：`opl-meta-agent` 可作为开发者智能体消费该 blocked suite，并在 `med-autoscience` 源码仓直接修改 MAS 的 stage、skill、prompt、rubric、quality contract、tests 和 docs；被禁止的是写 DM002 study truth 或替 AI reviewer 宣布质量 ready，不是禁止修改 MAS 这个智能体产品本身。
- 决策：`developer_patch_work_order` 与 `target_editable_surface_refs` 必须显式覆盖 `AI-native expert judgment first, contracts as floor not ceiling`。`opl-meta-agent` 可以直接修改 MAS repo 的 stage、skill、prompt、rubric、contract、tests 和 docs，但 contract/rubric 只能产生下限 blocker、route-back 和 regression guard，不能授权 `medical_journal_prose_quality=ready`、submission readiness 或 publication quality closure。
- 决策：Agent Lab 自进化 suite 必须输出跨 stage 漏洞审计面，覆盖 `review`、`analysis-campaign`、`write`、`figure-polish` 和 `publication-gate`，用于追踪 reviewer feedback 是否在 stage 间丢失、方法学 blocker 是否被降格为 prose repair、机械 gate 是否覆盖 AI reviewer 判断、delivery/package 状态是否抢跑质量 route-back。
- 决策：internal error、debug history、runtime incident、provider/executor trace 只能作为 runtime diagnostics、incident learning 或 mechanism patch evidence refs。它们不得进入论文 main story，不得作为医学 claim 支撑，也不得替 AI reviewer、evidence ledger 或 review ledger 宣布质量 ready。
- 决策：预测模型 / 外部验证论文的 first-draft quality contract 必须把 TRIPOD/TRIPOD+AI 风格的报告要求前置到 `pre_draft_quality_runtime_state`：模型可复现性、变量单位和跨队列 harmonization、外部验证队列/transport policy、统计不确定性、Table 1 / Table 2、校准/风险分布图、NHANES 权重或 unweighted framing、以及内部质控语言清除。缺项时 route back 到 pre-draft/write owner；AI reviewer 仍负责最终医学写作质量 verdict。
- 决策：Agent Lab suite 必须把 hard methodology/unit-harmonization route 作为机制改进目标暴露给 `opl-meta-agent`，包括 `analysis_harmonization_owner` callable、runtime prompt contract、quality repair batch handoff、work-unit evidence adoption 和回归测试 refs。该 suite blocked 只表示 MAS 能力层需要 patch，不代表 DM002 医学质量 verdict；DM002 仍要由 MAS owner chain 重跑或 typed-block 后再进入 AI reviewer。
- 决策：`analysis_harmonization_owner` 产出的 `unit_harmonized_rerun_required` typed blocker 是该 hard methodology work unit 的合法 owner 输出。supervisor scan / owner-route read model 必须消费 `artifacts/controller/analysis_harmonization/latest.json`，把 DM002 保持在 `next_owner=analysis_harmonization_owner` 的 typed blocker 状态，不得重新排队同一个 `unit_harmonized_external_validation_rerun` 并制造假进度。
- 决策：当 `analysis_harmonization_owner` 证明 unit-harmonized rerun 需要原始 transported Cox model provenance，但当前 evidence 只有输入、指标摘要或 prose-level 方法描述时，必须进一步 handoff 到 `source_provenance_owner.recover_transport_model_provenance_or_typed_blocker`。该 owner 只能产出 canonical transport model provenance bundle 或 `transport_model_provenance_recovery_required` typed blocker；不得用重新拟合的替代模型、结果摘要或旧稿描述冒充原 development model，也不得写 DM002 paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package` 或 submission readiness verdict。
- 决策：`source_provenance_owner` 的恢复动作必须先做受控候选搜索并记录 `provenance_search`。搜索范围限于当前 study 的 artifacts/analysis/experiments/paper、对应 runtime quest、以及 workspace legacy archive provenance；supervision、controller、request、consumer 等控制面不得被当成候选模型来源。只有带 `surface=canonical_transport_model_provenance_bundle` 且同时包含系数、feature order/coding、5 年 baseline survival 或 hazard、penalty/tuning provenance、standardization/scaler state 和 original-result artifact ref 的 bundle 才能关闭该 owner。RESULT 摘要、prose 方法描述和 substitute refit 只能作为非关闭候选进入 typed blocker 证据。
- 决策：`source_provenance_owner` 的受控候选搜索必须有机器边界：按 root kind 记录 `root_scan_summaries`，限制递归深度、访问文件数和候选数，并排除 supervision/controller/request/consumer/source_provenance 等控制面目录。legacy archive 只能作为有界 provenance 查找面，不得对整棵历史 runtime/archive 做无界 `rglob`；深层随机 bundle 即使形似完整，也不能绕过 canonical/explicit surface 边界关闭 owner。
- 决策：`source_provenance_owner` 的 typed blocker 只有在包含当前搜索证据时才算 owner output satisfied。缺 `provenance_search.searched=true`、缺 `accepted_bundle_ref` 字段、或未显式声明 `result_summary_acceptance_allowed=false` 与 `substitute_refit_allowed=false` 的历史 blocker 必须被视为 stale/pending，并重新排队 `recover_transport_model_provenance`；已搜索但未找到完整 bundle 的 blocker 才能作为终态 source-provenance blocker 被消费。
- 决策：终态 source-provenance blocker 被消费后，read model 不得继续把 `next_owner` 投回 `source_provenance_owner`。它应投影为 `blocked_reason=methodology_reframe_required`、`next_owner=decision`，要求 controller/decision stage 重新选择路线：停止当前 transported-model claim、改写为 provenance-limited harmonization audit、重建可复现模型路线，或进入 human decision gate。
- 决策：`methodology_reframe_required` 不能停留在只读 owner-route。supervisor scan 必须生成 `methodology_reframe_route_decision`，consumer 必须把它交给 `decision` owner，dispatch executor 必须写 `artifacts/supervision/requests/decision/latest.json` 并物化 `controller_decisions/latest.json` 的同线 route-back decision。该 decision 只授权方法学重构路线，不写论文、包或质量 verdict。
- 决策：`methodology_reframe_route_decision` 物化后不得把 `methodology_reframe_route_decision` 自身作为 runtime 下一工作单元继续派发。controller decision 必须保留 `decision::methodology_reframe_route_decision` 作为决策 fingerprint，同时把 `next_work_unit` 指向可执行的 `analysis-campaign` 工作单元；对 DM002 这类终态 source-provenance blocker，默认路线是 `provenance_limited_harmonization_audit`。该路线只能物化 provenance-limited harmonization audit、reproducible-model rebuild route、stop-loss 或 human gate，不得回落为普通 prose/source-documentation repair。
- 决策：controller authorization 的 work-unit compact/read-model 不能丢弃 hard-methodology 约束字段。`hard_methodology`、`selected_route_option`、`terminal_source_provenance_blocker_consumed`、`current_transport_claim_must_not_be_used_as_medical_conclusion`、`required_owner`、`required_next_work_unit`、`typed_blocker` 和 `route_options` 是 runtime prompt 的机器合同字段，不是普通说明文本；若丢失，MAS worker 会把 DM002 误当成普通 prose/source-documentation repair 并再次产生假进度。
- 决策：runtime prompt 必须把 `provenance_limited_harmonization_audit` 识别为 hard methodology/provenance-limited reframe target，并显式禁止重跑已污染 transported-score analysis、禁止把当前 transportability failure estimates 当成医学结论、禁止用 AI reviewer rerun/package refresh/prose note 关闭该 work unit。
- 决策：`provenance_limited_harmonization_audit` 必须拥有独立 owner callable，而不是只存在于 controller decision 或 runtime prompt 中。`provenance_limited_harmonization_owner.provenance_limited_harmonization_audit_or_typed_blocker` 只能写 `artifacts/controller/provenance_limited_harmonization/latest.json`，消费 `controller_decisions/latest.json`、`analysis_harmonization/latest.json` 与 `source_provenance/latest.json`，并明确当前 raw transported-score 结果只能作为 harmonization/provenance failure 证据，不能作为医学 transportability 结论。若原始 transported-model provenance 仍未恢复，该 owner 必须 typed-block 到 clean reproducible rebuild authorization 或 stop-loss / human gate，不得回落到 prose repair、AI reviewer-only rerun、package refresh 或 submission readiness。
- 决策：supervisor scan / consumer / dispatch / output-readiness 必须把 `provenance_limited_harmonization_audit` 当作当前可执行 owner work unit 消费；但如果新的 `analysis_harmonization` 或 `source_provenance` owner result 晚于 methodology decision，必须重新排 `methodology_reframe_route_decision`，不能让 stale decision 进入 audit。
- 决策：`task_intake_kind=methodology_rebuild_authorization` 是 human-gate 对 clean reproducible-model rebuild route 的结构化授权。study truth kernel 必须把它 materialize 为 `task_intake` 事件和 `canonical_next_action=authorize_clean_reproducible_model_rebuild`，而不是继续把旧 `waiting_for_user` 或旧 publication gate projection 当作 dominant authority。
- 决策：human-gate rebuild authorization 只能把 provenance-limited blocker 推进到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。它不能直接证明 DM002 迁移失败、不能宣布 manuscript quality ready、不能写 `paper/`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package` 或 submission readiness。若授权晚于旧 `rebuild_reproducible_model_route_required` result，read model 必须使该旧 result 失效并重新执行 provenance-limited owner；新 owner result 必须消费授权并投射 `blocked_reason=unit_harmonized_rerun_required`、`next_owner=analysis_harmonization_owner`。
- 决策：clean rebuild route 中，新的 `analysis_harmonization_owner_result` 是 source-provenance handoff 的当前性触发器。若它晚于旧 `source_provenance_owner_result`，旧 source search blocker 不能被当作当前 satisfied output，必须重新排队 `source_provenance_owner.recover_transport_model_provenance_or_typed_blocker`。若它晚于旧 provenance-limited owner result，旧 provenance-limited `unit_harmonized_rerun_required` 也不能继续抢占 read model；否则 DM002 会出现 `action_queue=[]` 但仍需恢复模型 provenance 的假闭合。
- 决策：`methodology_reframe_route_decision` 必须把 human-gate clean rebuild authorization 当作真正路线选择，而不是继续硬编码 `provenance_limited_harmonization_audit`。当 `methodology_rebuild_authorization` 与终态 source-provenance blocker 同时当前时，decision owner 应选择 `selected_route_option=rebuild_reproducible_model_route`、`next_work_unit.unit_id=unit_harmonized_external_validation_rerun`、`required_owner=analysis_harmonization_owner`。该路线仍然只授权 unit-harmonized rerun 或 typed blocker，不恢复旧 Cox provenance、不写论文面、不放松质量门、不宣布 submission readiness。
- 决策：managed runtime turn authorization 必须消费已完成的 `provenance_limited_harmonization_owner_result` currentness。当旧 `controller_decisions/latest.json` 仍指向 `provenance_limited_harmonization_audit`，但该 audit owner result 已以 `unit_harmonized_rerun_required` 把下一步交给 `analysis_harmonization_owner/unit_harmonized_external_validation_rerun`，且 runtime state 持有下游 hard-methodology authorization 时，worker prompt 必须选择下游 authorization，不得再次派发旧 audit。该规则属于 MAS 医学 owner-chain read model/currentness，不属于 OPL provider、queue、attempt ledger、generic runner 或 session lifecycle 控制面。
- 决策：`analysis_harmonization_owner` 在 clean reproducible-model rebuild route 被授权后，可以用 frozen China/NHANES transportability inputs 重建 controller-owned unit-harmonized Cox evidence。HDL raw-scale mismatch 与旧 Cox provenance 不足在该路线下是 rebuild 触发证据，不再永久阻断正路径；但 owner 必须并列记录 raw-scale NHANES 与 HDL mmol/L 转换后 NHANES 的 external-validation metrics、Cox 系数、feature order、baseline survival 和软件 provenance，并显式声明旧 raw-scale transport claim 不得作为医学结论。该 completed receipt 只关闭 hard-methodology rerun work unit，后续医学论文结论仍必须由 AI reviewer / writing owner 基于新 evidence 重写。
- 决策：`analysis_harmonization_owner` 的 execution receipt 顶层必须投影 owner result 的实际 `next_owner` / `next_work_unit`。当 unit-harmonized rerun 因 Cox transport provenance 不足而返回 `blocking_owner_route.next_owner=source_provenance_owner` 时，runtime closeout 和 default executor execution 不得继续写回 `next_owner=analysis_harmonization_owner`，否则会反复重排同一个 hard-methodology work unit。这是 MAS domain owner handoff 规则，不属于 OPL provider、queue、attempt ledger 或 session lifecycle 控制面。
- 决策：DM002 高质量医学论文反馈进入 MAS 能力层时，必须先由 OPL Agent Lab suite 和 `opl-meta-agent` developer patch work order 形成 gap-to-patch traceability matrix，再改 MAS 源码、测试和文档。前台开发者不能绕过该工单自由发挥。
- 决策：本轮 work order `oma_developer_patch_work_order_99fdc0d34111` 覆盖 `medical_journal_prose_quality`、HDL harmonization、模型复现、Table 1/Table 2、uncertainty/validation metrics、NHANES framing、calibration/risk-collapse figures、internal-quality-language purge，以及 controller/read-model 对 analysis harmonization owner result 的消费。MAS 侧只改这些 traceable surfaces，不写 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、`manuscript/current_package` 或 submission readiness verdict。
- 决策：first-draft 不得把 `accepted analysis records`、`verified outputs`、`source-documentation gaps`、`before external submission`、`submission readiness` 等内部质量记录语言写入正文；这些只能作为 typed blockers、handoff 或 TODO 出现在论文外部 surface。HDL 单位异常、未验证 net benefit、缺置信区间、缺 Table 1/Table 2 正文渲染，均必须在写作前被 durable evidence 支持或 fail-closed route back。
- 决策：corrected data-processing mistake、contaminated run、raw-scale debug output 和 unit-harmonization repair history 不得成为正文 Results/Discussion 的主故事。论文主线必须从 cleaned valid evidence 组织；这类错误轨迹只能进入 provenance、handoff、typed blocker，或在可复现性确实需要时作为最小 Methods caveat。first-draft voice gate、AI reviewer hard rule、write skill 与 Agent Lab mechanism refs 都必须执行该规则。
- 理由：用户明确反对用 mechanical manuscript completeness/write-gate 脚本检查论文。正确做法是让 Agent Lab 学习和优化 MAS agent 的写作/审稿行为，同时保持医学质量判断由独立 AI reviewer artifact 和 publication owner 持有。
- 影响：新增 `agent-lab-medical-manuscript-quality-suite` 只 materialize refs-only Agent Lab suite。它可以帮助 OPL 发现和推进 MAS agent 改进候选，但不能替代 reviewer、不能授权投稿、不能 bypass live runtime owner guard。每次 self-evolution patch 必须留下测试 receipt、developer patch receipt、版本/commit 和 no-forbidden-write 证据。
- 影响：该 suite 必须同时输出 `mas_agent_lab_mechanism_evolution_inputs`，把 research wiki / failed-route memory 升级为 typed body-free `research_memory_graph`，把 analysis queue / campaign manifest 升级为 typed body-free `analysis_queue_manifest`，把 runtime event、provider hygiene 和 claim assurance 输入升级为 typed body-free refs/metadata surface，并保留 AI reviewer direct-evidence refs 接到 OPL Agent Lab 的 mechanism evolution surface。OPL 只能消费这些 graph/manifest/ledger/map refs 来生成机制 candidate、promotion decision、canary 和 rollback refs；不得读取或写入 MAS memory body、runtime event body、claim body、review verdict、publication eval、controller decisions、canonical manuscript、current package 或 submission readiness。

## 2026-05-18：AI-first quality gate 必须分离执行 agent 与 reviewer/auditor agent

- 决策：MAS / OPL stage quality gate 中，执行与审阅/审计必须是两个独立智能体任务。executor agent 负责 stage work、artifact/source/evidence refs 和 execution receipt；reviewer/auditor agent 必须通过独立 invocation、独立 context/task record 读取这些 refs，并产出 AI reviewer record、audit receipt、route-back reason 或 typed blocker。
- 决策：`Codex CLI` 可以作为 executor，也可以在另一次独立调用中承担 reviewer/auditor 角色；但同一 agent、同一上下文、同一 task record 内的“先执行再自审”不能关闭 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict`、artifact mutation authorization 或 publication gate。
- 决策：MAS private authority manifest 必须为每个 private authority surface 声明 `judgment_mode`，仅允许 `ai_first_stage_gate`、`ai_first_record_validator`、`mechanical_guard` 和 `refs_only_adapter`。`publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 和 `publication_route_memory_accept_reject` 是 `ai_first_stage_gate`；`artifact_mutation_authorization` 是消费 AI-first record 的 validator；`owner_receipt_signer` 与不输出医学 verdict 的 helper 只是 mechanical guard。
- 决策：程序输出策略固定为 `programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only`。缺少独立 reviewer/auditor receipt、复用 executor task/context/receipt、候选 record 来自 `mechanical_projection`、或缺必需 AI-first refs 时，程序只能返回 typed blocker / route-back，不能产生 pass、ready、publication readiness、source readiness 或 memory acceptance verdict。
- 理由：AI-first 质量门需要真正的 second-pass reasoning 和可审计 provenance。把 executor summary 改名为 reviewer output，会让质量门退化成自证，削弱 MAS reviewer-first、publication gate 和 OPL stage-led 分工。
- 影响：后续 stage skill、OPL generated surface、product-entry/sidecar projection、review ledger 和 focused tests 必须保留独立 reviewer/auditor invocation、task/context record 与 receipt chain；缺少独立记录时 fail closed 或 route back，不用规则分支、regex、普通脚本或自审补齐。

## 2026-05-17：旧论文项目迁移必须 clean paper-authority cutover，不做 legacy token 兼容读取

- 决策：旧 MDS / 旧 MAS 论文项目迁移到新 MAS 时，`publication_eval/latest.json`、AI reviewer response record、`controller_decisions/latest.json`、`current_package_freshness/latest.json`、`manuscript/current_package/`、`current_package.zip` 与 delivery manifest 这类会冒充当前质量/交付结论的 surface，必须通过 `paper-authority-clean-migration` 从 active truth 位置归档到 `artifacts/migration/paper_authority_cutover/history/...`，旧产物只保留 provenance 角色。
- 决策：迁移入口不得把旧 token 映射成新 schema，不得把未知旧 `gap_type`、旧 verdict 或旧 route token normalizer 写进 reader。旧 artifact 不合新 contract 时，正确路径是 fail closed，触发 AI reviewer / publication gate / artifact owner 重新物化；不是兼容读取。
- 决策：迁移后 `paper_authority_cutover/latest.json` 是 MAS-owned receipt，状态为 `awaiting_new_mas_authority`；supervisor scan 必须把它路由到 `return_to_ai_reviewer_workflow`。AI reviewer 重新写出新 schema publication eval 后，publication gate 与 delivery owner 再重建 submission/current package。
- 理由：DM002 暴露出 runtime binding 和 legacy physical cleanup 已完成，但论文级 active truth surface 仍停留在旧 eval/current package，导致新 MAS executor 仍读取旧质量/交付结论，用户看到的论文仍是 3 天前的旧版。局部 normalizer 只能绕过一个旧 token 阻塞，会继续保留兼容层和旧 truth 入口。
- 影响：`medical_prose_review` 可作为 AI reviewer 输入证据保留，但不能作为 current publication verdict。后续跨 workspace 迁移先跑 `medautosci publication clean-authority-migration --profile <profile> --dry-run`，确认后 `--apply`，再由 supervisor scan / dispatch 重走 owner 链路；不得直接手改 `manuscript/current_package` 当完成态。

## 2026-05-17：clean cutover 后缺 prose review 时只重建 request，不兼容读取旧评审

- 决策：`paper_authority_clean_migration` pending 时，`return_to_ai_reviewer_workflow` 必须由新 MAS 从 canonical `paper/`、study charter、evidence/review ledger 和 blueprint 物化新的 `medical_prose_review_request.json`。如果尚无新 `medical_prose_review.json`，只能写出 AI reviewer-backed、`medical_journal_prose_quality=underdefined`、human readiness blocked 的 `publication_eval/latest.json`，并把 reviewer OS 的 prose currentness 标成 clean migration 专用的 `requested`。
- 理由：旧项目的旧 prose review 只能证明历史上评过某版稿件；把它映射成新 currentness 会把 legacy artifact 重新变成 executable truth。干净迁移的第一跳应建立新 MAS authority 和下一步 owner，而不是制造当前 ready 判断。
- 影响：`reviewer_operating_system.currentness_checks.medical_prose_review.status=requested` 只允许在 `authority_source_signature=paper_authority_clean_migration`、有 request digest / manuscript digest 且 `route_back_required=true` 时出现。普通 AI reviewer closure 仍必须消费完整 current `medical_prose_review.json`，否则 fail closed；该路径不写 `current_package`、不放宽 publication gate、不授权 submission readiness。

## 2026-05-17：clean cutover 缺 canonical paper 输入时必须交给 write owner 重建

- 决策：`return_to_ai_reviewer_workflow` 若在 clean paper-authority cutover 后发现缺少合规 `paper/medical_manuscript_blueprint.json`，不得读取旧 blueprint、旧 prose review 或旧 package artifact，也不得把机械生成物复制成 canonical。executor 必须写出 typed blocker `canonical_paper_inputs_rehydrate_required`，`next_owner=write`，并声明 `legacy_artifact_reader_allowed=false`、`mechanical_blueprint_as_canonical_allowed=false`。
- 决策：supervisor scan / consumer / dispatch executor 必须把 `canonical_paper_inputs_rehydrate_required` 作为正式 owner-route action 交给 `write` owner。该 owner 只能先物化 `paper/medical_manuscript_blueprint_source.json`，作为重新写作和 AI author/reviewer 授权的输入；`paper/medical_manuscript_blueprint.json` 只有带合规 AI authorization / clearance 时才可成为 canonical。
- 决策：如果同一 clean cutover study 的 current publication supervisor 或 publishability gate 已明确 `scientific_anchor_missing` / `missing_publication_anchor` / `anchor_kind=missing`，上述 write rehydrate 必须让位给 `publication_gate_specificity_required`，并标记 `write_rehydrate_deferred=true`。write owner 只能重建已有科学结果的 manuscript inputs，不能从缺 main result / publication anchor 的空锚点生成蓝图。
- 决策：`publication_gate_specificity_required` 被当前 owner route 明确授权给 `publication_gate` 时，即使该 paper line 处于 terminal `paper_progress_stall` / same-fingerprint loop，dispatch executor 也必须执行 publication gate owner callable，物化具体 blocker targets 或继续 fail closed。terminal stall 和 repeat suppression 只能防止重复 LLM worker 或无意义重跑，不能压掉当前 publication gate controller handoff。
- 理由：旧论文项目缺 canonical blueprint 时，局部 token normalizer 或空壳 blueprint 会把历史投影重新抬成当前论文真相，正是 DM002 初稿质量漂移的根因之一。干净迁移应重建当前 paper owner 输入，而不是兼容旧 artifact。
- 影响：DM-CVD、Obesity、NF-PitNET 等旧论文项目迁入新 MAS 时，缺 canonical paper 输入会统一 route 到 write rehydrate，再回 AI reviewer / publication gate / delivery owner；quality repair batch 不能初始化空 `medical_manuscript_blueprint.json` / `medical_prose_review.json` / derived canonical shell 来清 gate，必须 fail closed 到该 owner-route。
- 影响：缺科学锚点的 study 先由 publication gate/controller owner 指明或恢复主结果锚点；只有锚点存在后，write rehydrate 才能继续。这不是 legacy 兼容层，也不是脚本评判稿件完整度，而是 owner 顺序约束。publication gate handoff 是非 LLM controller apply，放行它不会突破成本护栏、质量 gate 或 paper/package mutation guard。

## 2026-05-17：clean paper-authority migration 必须对已建立的新 MAS authority 幂等

- 决策：`paper-authority-clean-migration --apply` 只能在 study 仍有旧 active authority surface、缺 cutover receipt，或 `new_mas_authority_established` 的 active AI reviewer eval 已失效时执行归档/重写。若 receipt 已是 `new_mas_authority_established` 且 active `artifacts/publication_eval/latest.json` 仍匹配 receipt 指向的 AI reviewer eval，再次 `--apply` 必须是 no-op，不得把 receipt 打回 `awaiting_new_mas_authority`。
- 决策：若 receipt 仍是 `awaiting_new_mas_authority`，但新 MAS 已物化 clean-migration 专用的 AI reviewer interim eval，或 publication gate 写出 `mechanical_projection_used_as_quality_authority=false` 且 `ai_reviewer_required=true` 的非权威投影，迁移器不得把这些新 surface 再归档成 legacy。它们只能保留为 route-back / blocked evidence，继续等待 AI reviewer、publication gate 和 delivery owner 关闭；未知 provenance、缺 clean-migration currentness 或无 receipt 关联的 `publication_eval/latest.json` 仍按旧 active authority fail closed。
- 理由：DM002 暴露出 clean migration 重跑时会把已由新 MAS 建立的 AI reviewer-backed blocked/underdefined eval 当作待迁移面再次处理，导致质量闭环反复回到入口状态。彻底迁移不等于反复清空新权威；迁移入口必须只切旧权威，不吞掉新权威。
- 影响：重复迁移可以安全用于 DM-CVD、Obesity、NF-PitNET 等 workspace 的批量 closeout；它保留 fail-closed 语义，但不把当前新 MAS authority 归档为 legacy provenance。若 active eval 被机械 projection 或其他非 AI reviewer 面覆盖，仍按 stale authority 重新要求 AI reviewer，不做 legacy token normalizer。

## 2026-05-17：pending clean paper-authority cutover 必须阻止 delivery/package authority 重新物化

- 决策：`paper_authority_cutover/latest.json.status=awaiting_new_mas_authority` 或 `new_mas_authority_established` 但 active AI reviewer eval 已失效时，`paper/submission_minimal`、`manuscript/delivery_manifest.json`、`manuscript/current_package/`、`manuscript/current_package.zip` 与 `artifacts/controller/current_package_freshness/latest.json` 不得重新生成。即使 control-plane snapshot 或 controller route 允许 bundle/delivery 写入，也必须返回 `paper_authority_clean_migration_required`，交回 AI reviewer 先建立新 MAS quality authority。
- 理由：DM-CVD 003 暴露出 clean migration 后仍可由 delivery/package sync 重新生成 active authority surface，导致 dry-run 再次发现 5 个活跃交付面。这不是旧 token 兼容问题，而是 cutover 等待阶段缺少写入护栏。
- 影响：delivery owner 只能在 AI reviewer-backed publication eval 当前有效后重建 current package 和 freshness proof；pending cutover 阶段的 publication gate 投影、非权威 freshness 信息和旧 delivery surface 均不得成为当前交付真相。该规则不新增脚本式论文完整度检查，也不改变 AI reviewer 作为医学写作质量 owner 的边界。

## 2026-05-17：AI reviewer response record 必须随 request materialize 交给 owner executor

- 决策：`artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json` 中已有最新合规 AI reviewer-owned record 时，`materialize_ai_reviewer_request` 必须把该 record 附到 `artifacts/supervision/requests/ai_reviewer/latest.json`，并记录 `publication_eval_record_ref`。owner executor 不应从 prose review 文本临场拼 record，也不应在缺 record 时放宽执行。
- 2026-05-19 追加：AI reviewer 可通过 `publication materialize-ai-reviewer-record` 只物化 owner record 到 `artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json`，供 request lifecycle 发现与消费；该入口不写 `publication_eval/latest.json`。最终质量 truth 仍由 `return_to_ai_reviewer_workflow` 调用 `ai_reviewer_publication_eval_workflow` 后写入 `publication_eval/latest.json`。
- 理由：DM002 暴露出 reviewer 已产生 current `medical_prose_review.json` 与 publication eval record，但 supervisor request 只带 input refs，导致 `return_to_ai_reviewer_workflow` 被 `ai_reviewer_record_missing` 阻断，无法把 write route-back 物化为 controller truth。
- 影响：AI reviewer response 仍是质量判断 owner；request lifecycle 只负责 owner record discovery/attachment 与 provenance preservation，不新增机械写作 gate，不授权直接修改 `paper/`、`manuscript/current_package` 或 publication truth。

## 2026-05-19：AI reviewer currentness 优先于 stale repair batch

- 决策：当 `publication_eval/latest.json` 是 mechanical projection 且 `ai_reviewer_required=true` 时，domain transition 的 `ai_reviewer_re_eval` 不得被旧 `reviewer_revision` task-intake、旧 methodology 文本或 `quality-repair-batch` fallback 覆盖。只有当前 publication eval 自身仍明确给出 methodology/analysis route 时，analysis route 才能抢在 AI reviewer recheck 前执行。
- 决策：publication gate 的 specificity targets 若全部绑定到 `stale_submission_minimal_authority`、`stale_study_delivery_mirror`、submission hardening 或其他 delivery/authority blocker，不得按 `claim` / `figure` / `metric` target kind 派发 `analysis_claim_evidence_repair` 或 `figure_results_trace_repair`。这些 targets 只用于 delivery/authority owner 或继续要求 publication gate 为非 delivery blocker 补 specificity。
- 理由：DM002 清掉 raw-HDL 正文残留后，最新 gate 已转向 stale submission/delivery 和 AI reviewer currentness，但 runtime prompt 继续消费旧 `analysis_claim_evidence_repair`，造成 canonical evidence ledger 有增量而 stale package 没推进的循环。
- 影响：route owner 现在会先把主观医学写作质量交回 AI reviewer；delivery/authority blockers 不再伪装成分析修复工作单元。该修复不写 study truth、paper package、`publication_eval/latest.json` 或 `current_package`，只收紧 controller work-unit selection。

## 2026-05-19：内部方法学修正不能成为论文故事线

- 决策：医学文体 style corpus 升级为 `medical_journal_prose_style_v3`。AI reviewer 必须把 internal correction provenance、debug history、preprocessing repair history 与正式论文叙事分开：修正后的数据定义只在 Methods 或表注中按可复现需要说明，不能在摘要、Results、Discussion opening、Conclusion、title 或 figure legends 中写成贡献、novelty、main story 或 methodological lesson。
- 决策：`medical_prose_review_request` 可以暴露窄范围 `mechanical_safety_flags` 来标记这种内部方法学修正泄漏；这只是 evidence snippet / fail-closed safety guard。存在 blocking flag 时，AI reviewer 不能给 `overall_style_verdict=clear`，必须 route back 到 `write` 或更上游 owner。该规则不授权脚本判断整篇论文质量，也不允许 mechanical flag 产出 `medical_journal_prose_quality=ready`。
- 决策：`return_to_ai_reviewer_workflow` request materializer 附加历史 AI reviewer publication-eval record 前，必须复用 AI reviewer workflow 的 manuscript-story provenance guard。若旧 record 把 unit harmonization、raw-scale HDL 修复或内部 correction provenance 写成 novelty / contribution / main finding，只能写 `ai_reviewer_record_manuscript_story_provenance_leakage` typed blocker，并要求 AI reviewer 重新产出当前 record；不得把旧 record 重新附到 request 后再让 dispatch 失败。
- 理由：DM002 的 HDL-C 单位错误修正后，稿件把 “after unit-harmonized predictor preprocessing” 反复放进 Objective、Results、Conclusion 和 figure legend，导致内部修正路线变成论文主线。高质量医学论文应讲最终分析支持的干净科学故事，内部错误与修复路径留在 provenance、review 或 incident learning。
- 影响：旧 `medical_journal_prose_style_v2` prose review 会因 style currentness 过期而回到 AI reviewer；Agent Lab self-evolution suite 暴露 `internal_methodology_repair_becomes_manuscript_contribution` 漏洞和 `internal-methodology-repair-story-boundary` developer patch ref。MAS 不直接写 DM002 paper/package truth，后续仍由 write / AI reviewer / publication gate owner chain 推进。

## 2026-05-17：AI reviewer 的当前返写判断必须物化为 route-back truth

- 决策：`medical_prose_review` 已通过 request/manuscript digest currentness 校验时，`medical_journal_prose_quality.status != ready`、`overall_style_verdict != clear` 或 `route_back_recommendation.required=true` 不是 workflow failure，而是 AI reviewer-owned publication evaluation 的有效质量结论。`publication_eval/latest.json` 必须保留该 `route_back_same_line -> write` 判断，并在 `reviewer_operating_system.currentness_checks.medical_prose_review` 中记录 prose status、style verdict、route-back required 与 route target。
- 决策：clear publication gate / bundle-stage projection 不能覆盖一个 current、AI-owned、带 reviewer OS currentness 的 medical-prose write route-back eval。机械 projection 仍可刷新 stale、缺 owner provenance、缺 currentness proof 或与当前 gate 阻塞 fingerprint 不匹配的旧 eval。
- 理由：DM002 暴露出 AI reviewer 已判断稿件医学论文写作质量为 `partial/revise`，但 workflow 把 `medical_prose_review_route_back_required` 当作异常处理，随后旧 `publication_eval/latest.json` 继续显示 ready / continue bundle stage，导致用户看到的 manuscript 仍停在旧版本。
- 影响：AI reviewer 继续是主观医学写作质量 owner；程序逻辑只负责 currentness、owner、route 和 overwrite guard。该规则不新增机械写作检查，不授权前台手改 `paper/`、`manuscript/current_package` 或 publication truth，也不把 publication gate 的 clear 状态等同于投稿级写作质量 clear。

## 2026-05-17：managed runtime fresh prompt 必须同步当前 controller authorization

- 决策：当当前 `controller_decisions/latest.json` 明确为 `return_to_ai_reviewer_workflow`，且 `next_work_unit` 为 `ai_reviewer_recheck` 或 `ai_reviewer_medical_prose_quality_review` 时，MAS turn runner 在生成 fresh Codex prompt 前必须把该 controller decision 绑定到本次 `active_run_id`，并写入 `.ds/runtime_state.json:current_controller_authorization`。旧 `last_controller_decision_authorization` 只作为历史授权保留，不能覆盖当前 AI reviewer redrive。
- 理由：DM002 暴露出 prompt 已能看到 5/15 的 AI reviewer redrive，但 runtime state 仍停在更旧的 `analysis_claim_evidence_repair` 授权。managed worker 随后调用 `domain-route-execute-dispatch --managed-runtime-worker` 时会从 runtime state 校验同 run 授权；如果该层未同步，AI reviewer workflow 会被阻断或空跑，旧 `publication_eval ready` 也容易被误读为新质量闭环。
- 影响：fresh prompt、runtime state 与 dispatch executor 现在消费同一条 controller truth：`quest_id`、`study_id`、`active_run_id`、`controller_actions`、`work_unit_id` 与 `work_unit_fingerprint` 必须一致。该修复不授权前台直接写 paper/current_package，不放宽 publication gate，也不把机械 projection 转换为 AI reviewer 质量判断；它只确保 AI reviewer owner 能真正收到当前 work unit。
- 2026-05-17 追加：同步范围从 AI reviewer 专用扩展为所有当前 controller decision runtime action，包括 `run_quality_repair_batch` 与 `run_gate_clearing_batch`。fresh turn 必须优先消费 `controller_decisions/latest.json`，再把它绑定到本次 run；旧 `current_controller_authorization` / `last_controller_decision_authorization` 只能在没有当前 controller decision 时作为历史恢复输入。DM002 的 `manuscript_story_repair` 暴露出此前 prompt 和 runtime_state 会分裂：prompt 指向 quality repair，runtime_state 仍挂旧 AI reviewer 授权。现在这种状态必须在 turn 启动前收敛到同一个 current controller authorization。
- 2026-05-21 追加：如果旧 `last_explicit_user_wakeup.owner_handoff_authorization` 指向 `source_provenance_owner.recover_transport_model_provenance_or_typed_blocker`，但当前 study 已有 accepted terminal `source_provenance_owner_result`，且该 result 明确 `terminal_source_provenance_blocker=true`、`next_owner=decision`、`next_work_unit=methodology_reframe_route_decision`，fresh turn 不能继续把 prompt 绑定到旧 provenance recovery handoff。runner 必须改用当前 controller decision / runtime authorization 中的下一 work unit，并把旧 provenance recovery 视为已被 terminal blocker superseded。这样保证 source provenance owner 的 typed blocker 被 decision route 消费后，不会反复抢占 MAS managed runtime worker。

## 2026-05-17：active study config 迁移必须改配置，不兼容读取退役字段

- 决策：旧 study active config 中的 `manual_finish.compatibility_guard_only` 不再通过 reader normalizer 或 alias 读取。迁移入口是 `study-config-clean-migration`：它只把 active `study.yaml` 中这一个退役字段改名为 `manual_finish.manual_finish_guard_only`，并写 `artifacts/migration/study_config_clean_migration/latest.json` receipt；reader 继续在看到旧字段时 fail closed。
- 理由：DM-CVD 001 的 progress projection 被旧字段阻断。把 reader 放宽会把退役 schema 重新变成可执行 truth，与 clean migration 目标冲突。正确做法是让 active config 自身升级到新 schema，旧字段只在 migration receipt/history 中留下 provenance。
- 影响：该迁移不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package、runtime truth 或质量 verdict。未知旧字段、字段冲突或无法唯一定位的文本更新继续 fail closed，交给 config migration owner 修正，不能用兼容层掩盖。

## 2026-05-17：display payload 迁移不做旧模板字段重写

- 决策：gate-clearing batch 不再把旧 `time_to_event_grouped_inputs.json` 中的 cumulative-incidence `groups` payload 改写为另一个 template 后继续 materialize。若 `time_to_event_risk_group_summary` 绑定下出现这种旧 display payload，当前轮必须写出 `stale_legacy_time_to_event_grouped_payload` typed blocker，并交回 `time_to_event_direct_migration` 重新物化 canonical display input。
- 理由：旧 display payload 和旧 paper authority surface 一样只能作为 provenance。把 `template_id` 从 risk-group summary 改到 cumulative-incidence grouped 属于兼容读取，会让历史 artifact 继续成为 executable display truth。
- 影响：DM-CVD、Obesity、NF-PitNET 等旧论文项目迁入新 MAS 时，F3/Figure display surface 必须由 canonical analysis / direct-migration owner 重建；未知旧 display shape 继续 fail closed，不新增 normalizer、alias 或兼容测试。

## 2026-05-17：time-to-event direct migration 必须跟随当前 reporting contract，不回填旧 F5

- 决策：`time_to_event_direct_migration` 的核心必需显示项固定为 T2E discrimination/calibration、risk-group summary、decision curve 和 Table 2；F5 由当前 `display_registry.json` / reporting contract 决定。若当前 contract 仍要求 `multicenter_generalizability_overview`，direct migration 继续生成 `multicenter_generalizability_inputs.json`；若当前 contract 已切到 `center_transportability_governance_summary_panel` 且 study 存在当前 `analysis/clean_room_execution/20_transportability` 布局，direct migration 必须从 `metrics_summary.json`、`discrimination_report.md` 和 `risk_group_composition_report.md` 重新物化 F2/F3/F5，保留已有 F4/T2 current payload，缺任一当前输入则 fail closed。
- 决策：gate-clearing batch 发现 transportability reporting surface 需要 sync 且 time-to-event direct migration 也需要刷新时，必须先运行 `sync_transportability_reporting_surface`，再运行 `time_to_event_direct_migration`，最后 materialize display surface。同一轮已经排入 direct migration owner 时，不再追加 `stale_time_to_event_grouped_payload_blocker`；只有 direct migration owner 未排入而 stale grouped payload 仍存在时，才 fail closed 到该 blocker。
- 决策：`sync_transportability_reporting_surface` 的 currentness 判断必须以当前 resolved reporting contract 和当前 display stubs 为准。旧 `multicenter_generalizability_inputs.json` 的存在或缺失都不能参与当前 F5 materialization 判断；它只能作为历史文件留存或被后续清理。`time_to_event_grouped_inputs.json` 的 stale 判定必须看当前 risk-group binding 下是否仍是 `groups` 结构且缺 `risk_group_summaries`，不能依赖旧 template id 是否命中。
- 决策：repair unit 的 `skipped` 状态不得作为后续 fingerprint skip 的成功凭据。`skipped` 表示该 owner 上次没有执行有效物化；如果当前 repair plan 仍然需要同一个 owner，必须重新执行，即使历史 unit fingerprint 一样。只有实际成功类状态，例如 `updated`、`synced`、`ready`、`ok`、`materialized`，才能让后续匹配 fingerprint 的 owner unit 进入 `skipped_matching_unit_fingerprint`。
- 理由：DM-CVD 002 的 clean migration 卡点不是旧 token 需要 normalizer，而是当前 transportability reporting contract 已把 F5 升级为 `center_transportability_governance_summary_panel`，direct migration 仍硬要求旧 `multicenter_generalizability_overview`，导致新 MAS owner-chain 无法重新物化 F3/T2E 当前显示真相。旧 F5 不应被回填成当前 contract。
- 理由：DM-CVD 002 还暴露出另一层 currentness 缺陷：历史 `sync_transportability_reporting_surface` 结果为 `skipped`，但后续 batch 因 unit fingerprint 匹配把它当成成功执行，进而没有补 F5，只能落到 `stale_legacy_time_to_event_grouped_payload` blocker。把 no-op 缓存为成功会让旧 incomplete surface 冒充当前 truth。
- 影响：DM-CVD 002 这类跨队列 transportability 论文由新 MAS 的 reporting contract 决定 F5 owner surface；旧 multicenter F5 不再通过 sync owner 转译成当前 transportability governance F5。两种 F5 都缺失时继续 fail closed 为 missing display binding；未知旧 display shape 继续交给 owner 重建，不新增兼容读取层，不把 legacy artifact 读取、token 映射、路径 relocation 或 template-name normalizer 作为迁移路径。
- 影响：clean migration batch 会重新执行仍被计划的 owner，而不是复用历史 no-op；这不是 legacy compatibility shim，也不读取旧 payload 作为当前 truth。正常成功执行后的 fingerprint 幂等仍然有效，避免重复 materialize 已当前的 surface。

## 2026-05-17 / 2026-05-18：MAS consumer thinning 后保留功能/结构 follow-through

- 决策：`functional_consumer_boundary` 是 MAS consumer thinning lane 的分类与禁回流机器面。`active_private_generic_residue_count=0` 只能说明当前没有未分类的长期 MAS generic owner claim；不能把它读成 MAS 功能/结构差距为 0，也不能把 active caller cutover、generated surface 生产消费、refs-only adapter 收薄、legacy physical retirement、OPL App drilldown 或 lifecycle 对账降成单纯测试/证据问题。
- 决策：MAS 不再在仓内扩展 generic runtime、generic scheduler、generic queue、generic attempt ledger、generic transition runner、generic workbench、generic memory locator、generic artifact lifecycle 或 generic observability。现有 hand-written CLI/MCP/Skill/product-entry/sidecar/status/workbench/projection shell 只作为迁移桥或 domain handler target 读取；OPL generated/hosted surface 接住 active caller 后，非 authority 代码、旧 alias、facade、wrapper 和兼容测试直接删除或 tombstone。
- 决策：测试/证据差距单独记录真实 paper-line provider apply scaleout、publication-route memory receipt scaleout、artifact lifecycle receipt scaleout、human gate/resume、domain owner-chain receipt 和 provider SLO long soak。它们用于证明目标结构真实可用，但不能替代目标结构本身的迁移和清理。
- 理由：MAS 仍有多处 repo-local shell、SQLite/lifecycle、workspace/source、memory/artifact、Portal/workbench 和 domain route 代码路径。长期 owner 已被机器面限定，但分类不是迁移完成；把这些路径写成已完成会继续保护历史私有平台并污染后续 OPL standard agent。
- 影响：后续修改 gap plan、status、current development lines、product-entry、sidecar、supervision projection 或 focused tests 时，必须拆开写 `功能/结构差距` 与 `测试/证据差距`。若发现新 surface 重新持有 generic owner，应作为 regression 修复；若 replacement proof 与 no-active-caller proof 已成立，旧面直接退役，不新增 compat alias、facade、shim、wrapper 或兼容聚合测试。

## 2026-05-17：MAS package 外壳收敛为 OPL pack compiler 输入与 generated surface consumer

- 决策：MAS 不再把 CLI、MCP、Skill、product-entry、sidecar、status、workbench、projection shell 或 test-lane harness 视为长期手写 owner surface。它们在 `functional_consumer_boundary.generated_surface_handoff` 中统一声明为 OPL generated/hosted target 或 MAS handwritten migration bridge。
- 决策：MAS 的长期 repo-owned code surface 限定为 `minimal_authority_function_manifest` 中的 7 类 authority function：publication quality verdict、AI reviewer quality decision、artifact mutation authorization、publication-route memory accept/reject、source readiness verdict、owner receipt signer 和 medical helper implementation。其他程序外壳必须能说明 active caller、迁移桥理由、diagnostic cleanup 或 fixture/provenance 需求。
- 决策：`declarative_pack_compiler_input` 是新的机器输入面，汇总 domain descriptor、stage graph、action intents、domain transition table、publication-route memory policy、artifact authority policy、source readiness policy、owner receipt schema 和 no-forbidden-write contract，供 OPL pack compiler 派生通用外壳。OPL pack compiler 可以生成/托管 CLI/MCP/Skill/product-entry wrapper、sidecar、status、workbench 和 harness，但不能声明或生成 MAS domain authority。
- 理由：此前 MAS 已证明 functional consumer boundary，但仍容易把现有 hand-written thin shell 误读成 MAS 长期 owner。把 pack input、generated handoff 和 minimal authority functions 变成 machine-readable surface，可以让后续迁移按 active caller cutover 与 no-forbidden-write 证明推进，而不是继续扩写 MAS generic shell。
- 影响：后续新增或修改 CLI/MCP/Skill/product-entry/sidecar/status/workbench/projection/harness 时，必须先判断能否进入 OPL pack compiler/generated surface；留在 MAS 的代码只能服务 authority function、domain handler target、迁移桥、diagnostic cleanup 或 provenance/fixture。完成 cutover 前不得写成 generated surface 已替代现有 active caller；完成 cutover 后，无 authority function 的旧 shell 应删除或 tombstone。

## 2026-05-16：MAS 数据管理以 domain-owned substrate adapter/export surface 暴露给 OPL

- 决策：MAS 不把 workspace/source/artifact/memory 数据管理权上收到 OPL，也不让 OPL 读取或写入 body。`medautosci sidecar export` 新增 `opl_substrate_adapter`，只导出 opaque/index-only 的 `workspace_refs`、`source_refs`、`artifact_refs`、`memory_refs` 与 authority boundary，供 OPL generic substrate 做 locator、index、lifecycle 和 projection。
- 决策：authority boundary 固定为 MAS owns study truth, memory body, evidence/review ledgers, publication/artifact authority；OPL owns locator/index/lifecycle/projection only。`medautosci sidecar dispatch` 继续只接受 allowlisted task 并回到 MAS owner chain，显式拒绝 OPL 写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、evidence ledger、review ledger、memory body、publication authority 或 artifact authority。
- 理由：OPL 需要统一 runtime substrate 消费面，但 MAS 的医学研究质量、证据、审阅、记忆正文、投稿判断和产物权威不能变成 generic framework truth。把现有数据管理薄化为 refs/projection，能让 OPL 获得索引和生命周期能力，同时避免第二 truth owner。
- 影响：后续新增 workspace/source/artifact/memory export 先接入 `opl_substrate_adapter` 的 opaque refs；需要写 body、接受 memory writeback、刷新 publication eval、更新 controller decision 或重建 current package 时，必须走 MAS-owned surface 和 owner receipt。

## 2026-05-16：AI reviewer ready 必须绑定当前输入与交付刷新证明

- 决策：`medical_journal_prose_quality=ready` 不能只表示某个 AI reviewer artifact 曾经给过 clear。`medical_prose_review` 必须携带 `request_ref`、`request_digest`、`manuscript_ref` 与 `manuscript_digest`；`publication_eval/latest.json` 的 `reviewer_operating_system` 必须携带 `currentness_checks.medical_prose_review` 和 `currentness_checks.current_package_freshness`。若 prose review 对应旧 request、旧 manuscript，或 current package freshness 的 `source_eval_id` 不匹配当前 eval，MAS 必须 fail-closed 到 AI reviewer / write / delivery owner，不能把旧评审证据重新包装成 bundle-stage ready。
- 决策：当 AI reviewer workflow 自身因 `current_package_freshness_source_eval_id_mismatch` 阻断时，下一轮 supervisor scan 先交给 `artifact_os` 执行 `current_package_freshness_required`，刷新 current package projection 与 freshness proof，再回到 AI reviewer / bundle-stage。这个顺序修复只处理 owner currentness，不把脚本或 freshness proof 变成医学写作质量判断。
- 决策：AI reviewer clear verdict 必须包含 IMRAD 关键段落的 section-level diagnosis 和 representative rewrite evidence。概括性“稿件足够正式”不能关闭医学期刊写作质量。
- 理由：DM002 暴露出 `publication_eval/latest.json` 于 2026-05-16 更新为 ready，但 human-facing `manuscript/current_package` 仍停在 2026-05-13，且被引用的 `medical_prose_review.json` 早于最新 request。这个状态不是论文质量闭环，而是旧 reviewer surface、bundle-stage metadata 和交付投影之间的 authority drift。
- 影响：AI reviewer 仍是主观医学质量 owner；程序化逻辑只校验证据身份、新鲜度和 owner route，不替代医学审稿判断。任何后续质量闭合都必须证明“AI reviewer 审的是这版稿件，交付包也是这次 eval 后的刷新结果”。

## 2026-05-16：Phenotype / treatment-gap 初稿质量门槛前移到 pre-draft runtime

- 决策：`clinical_subtype_reconstruction`、`phenotype_real_world`、`treatment_gap` 等 observational phenotype paper 必须在 `study_charter.paper_quality_contract.structured_reporting_contract` 和 `paper/medical_reporting_contract.json` 中自动物化 phenotype derivation、recorded treatment-gap、baseline characteristics 与 data-quality reporting obligations。`pre_draft_quality_runtime_state` 在授权 first full draft 前必须读取 charter-owned structured reporting checklist；若这些报告项未闭合，`full_drafting_authorized=false`，route back 到 `pre_draft_writing_readiness`。
- 决策：`ai_reviewer_re_eval` 在 domain transition 中优先于 generic `publication_gate_blocker`；`publication_eval` 若是 `mechanical_projection` 或 `medical_journal_prose_quality` 未 ready，必须回到 AI reviewer workflow。`medical_prose_review_status=ready` 也必须从 medical publication surface 透传到 publication eval action；缺失或 underdefined 时，clear gate 不能继续 write-stage / bundle-stage advancement。若当前 `manuscript/current_package/` 已由 current delivery manifest 标记为用户可见里程碑包，domain transition 必须先投影 `delivered_package_handoff`，停止 live runtime 并等待显式用户 wakeup；该 handoff 不是 AI reviewer 质量闭环，也不授权 submission-ready verdict。
- 理由：DM-CVD 003 显示，MAS 已有初稿质量政策、STROBE/AI reviewer 边界和后置 `medical_reporting_audit`，但 phenotype/treatment-gap 结构化报告合同没有进入初稿前授权链路，导致 phenotype derivation 不透明、treatment-gap 术语过强、BP/data-quality、baseline table、图表正式度和防御性语言问题在交付后才由用户发现。单纯写 `reviewer_revision` intake 只能修补当前稿，不能提高下一篇初稿质量。
- 影响：后续 DPCC 类论文在写整稿前必须先关闭或 route-back 这些 deterministic reporting blockers；AI reviewer 仍持有医学期刊 prose、publishability 与 submission-facing quality judgement。机械 checklist 只负责 fail-close 与 evidence routing，不得替代 AI reviewer 授权质量。

## 2026-05-15：完成态消费、AI reviewer provenance 与 owner handoff 必须进入 transition matrix

- 决策：MAS 论文控制面把三类真实卡死模式纳入 domain transition table / matrix tests。第一，DM002 这类 reviewer rebuttal route coverage 已 `coverage_complete=true`、11/11 route covered、active upstream repair 为 0 且 publication gate clear 时，旧 reviewer-revision/task-intake work unit 必须让位给 finalize / bundle-stage owner，不能继续派 `review_matrix` / `action_plan` coverage 检查；bundle-stage finalize 也不能继续沿用旧 `publication_gate_blocker_review` 这类 review work unit，必须投到明确的 submission authority / delivery sync closure。第二，DM003 这类 gate clear 但 `publication_eval` 仍是 mechanical projection 且 `ai_reviewer_required=true` 时，必须先回 AI reviewer workflow，不能被 active runtime 或 finalize-looking action 抢跑。第三，Obesity 这类 AI reviewer 已给出 blocked verdict / must-fix gaps 且 gate 仍 blocked 时，必须按 publication gate blocker / bounded repair 处理；如果旧 work unit 已 `owner_handoff + terminal_consumed=true`，runtime prompt 不能继续携带旧授权重新执行同一指纹。
- 理由：三篇真实 paper line 证明问题不是 Codex CLI 不会执行明确指令，而是 MAS 分散判断没有把“论文证据面已经完成/需要下一个 owner/仍被 gate 真阻断”消费成下一条 transition。局部 completion receipt、active run、controller decision、publication eval、task intake 和 lifecycle handoff 任何一层抢占都会制造几十小时同 stage 打转。
- OPL/MAS 边界：OPL 以后应提供通用 state-machine runner、幂等 tick、attempt/retry/dead-letter、human gate transport、dispatch receipt 与 matrix runner；MAS 继续持有 domain transition spec、AI reviewer / publication gate / claim-evidence-display / artifact authority 的解释和 oracle fixtures。OPL 可以执行 MAS 声明的 transition spec，但不能把 mechanical projection 或 provider completion 写成医学质量结论。
- 影响：新增状态转换必须先落 matrix case，再改实现。`study-state-matrix` 对单 study projection error 采用 fail-closed 行并继续投影其他 study，避免一个旧配置字段让整个 workspace transition surface 失明；旧配置本身仍是错误，不被兼容为有效配置。

## 2026-05-14：Domain transition table 集中管理，OPL 提供通用状态机执行底座

- 决策：MAS 的论文控制面状态转换必须收口成 MAS-owned domain transition table / transition matrix，而不是继续分散在 `publication_work_units`、`study_outer_loop`、`owner_priority`、`controller_authorization` 等局部判断点里各自解释下一步。transition table 的输入至少包括 `publication_supervisor_state`、publication gate report、`publication_eval/latest.json` 推荐动作、task intake、controller decision authorization 与 runtime liveness；输出必须固定 `decision_type`、`route_target`、`next_work_unit`、`controller_action`、owner、idempotency/fingerprint 和 fail-closed blocker。
- 理由：DM002/DM003/Obesity 等真实 paper line 反复暴露同类问题：状态转换概念上清晰，但实现分散会让 gate clear、bundle-stage、publishability blocked、stale authority、task-intake residue 和 runtime recovery 各层互相覆盖。集中 transition table 能把“输入状态组合 -> route/work_unit/action”的行为变成可审计矩阵，并用 table-driven oracle tests 防止同类漂移。
- OPL/MAS 边界：通用状态机执行底座、transition schema、幂等 tick、attempt/retry/dead-letter、human gate transport、dispatch receipt、transition matrix runner 和 cross-domain parity 可以上移到 OPL framework。医学研究语义不得上移：`stale_submission_minimal_authority`、`publication_gate`、`bundle_stage_blocked`、claim/evidence/display blocker、AI reviewer judgement、submission authority、paper quality 与 artifact/package authority 仍由 MAS 定义并测试。OPL 执行 MAS 声明的 transition spec；MAS 持有 domain transition table 和 oracle fixtures。
- 影响：后续控制面修复不能只补单点 if/else。凡新增或修改状态转换，必须同步更新 MAS domain transition table / matrix tests；当 OPL framework 的通用 state-machine runner 可用时，MAS 应把现有 domain transition table 作为 domain spec 接入 OPL runner，而不是让 OPL 重新解释医学状态。

## 2026-05-10：MAS 对齐 OPL Temporal-backed production runtime，Temporal 为 OPL 生产必需 substrate

- 决策：MAS 与 OPL 的长期托管口径从 Hermes-first 更新为 Temporal-backed OPL family runtime：`OPL Product Entry -> OPL stage-led family runtime provider -> MAS sidecar export/dispatch -> MAS domain entry/projection`。Temporal 是 OPL production online runtime 的必需 substrate；`Hermes-Agent` / `hermes_agent` 只作为显式非默认 Agent executor/proof backend、hosted proof lane 或历史 provenance 保留，不再作为目标 24h session/wakeup substrate、provider fallback 或安装模块；local provider 只作为 MAS direct/local diagnostics 或 OPL dev/CI/offline baseline。
- 理由：MAS 需要长期自治、human gate、retry/dead-letter、route-back 和 progress projection，但医学研究 stage、AI reviewer、publication gate、evidence/review ledger、route decision 与 artifact/package authority 必须仍由 MAS 持有。Temporal/provider 可以改善运行可靠性，但不能成为第二研究 truth owner。
- 影响：`medautosci sidecar export|dispatch` 继续是 OPL provider 到 MAS owner surface 的受控桥接；OPL/Temporal/Hermes/local provider 只能 enqueue、dispatch、signal、query、投影 attempt/receipt，不得写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package、evidence ledger、review ledger 或 artifact gate。2026-05-10 Hermes-first MAS sidecar bridge 决策保留为迁移背景，但后续新投入按 Temporal-backed production runtime 解释。

## 2026-05-10：Hermes-first OPL family runtime 与 MAS sidecar bridge

- 状态：已被同日 Temporal-backed production runtime 决策 supersede。保留本段用于解释 Hermes-first sidecar bridge 的迁移背景和当前 legacy provider 口径。

- 历史决策：当时的迁移假设是让外部 `Hermes-Agent` 由 OPL 管理，承担常驻 gateway、cron/webhook wakeup、session store、delivery/notification、approval transport 与 family queue tick；OPL 持有 typed family queue / dispatch contract；MAS 持有 study truth、publication judgment、quality gate、artifact/package authority 和 domain recovery decision。
- 当前生命周期处置：这不是当前目标 topology。当前 OPL-hosted production path 以 Temporal-backed OPL family runtime 为生产必需 substrate；`Hermes-Agent` / `hermes_agent` 只保留为显式非默认 Agent executor/proof lane、诊断/provenance 或历史迁移背景。任何当前文档或代码入口都不得把本段写成 Full online target。
- 保留价值：本段只解释 `sidecar export|dispatch` 为什么成为 OPL provider 到 MAS owner surface 的受控桥。sidecar 仍禁止写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package 或 artifact gate；这些 truth 只能由对应 MAS owner surface 产生。MAS local scheduler 已物理退役为 tombstone/provenance-only，不再作为可执行 diagnostic bridge 暴露；默认 scheduler owner 已迁到 OPL provider/runtime manager，Full online readiness 仍由 OPL 侧 Temporal provider readiness 判定。

## 2026-05-10：MAS 作为 OPL stage-led framework 上的独立 domain agent

- 决策：MAS 的 OPL 对齐口径固定为：MAS 是可直接由 Codex App skill 调用、也可由 OPL stage-led family framework 托管的独立 medical research domain agent。OPL 只持有 stage descriptor discovery、typed queue、wakeup、handoff、receipt、approval/retry/dead-letter、trace/projection 和 parity；MAS 持有医学 stage pack、prompt/skill、study truth reducer、evidence/review ledger、AI reviewer、publication gate、route decision 和 artifact/package authority。
- 理由：MAS 的价值在医学研究自治与论文质量闭环。如果把研究路线、质量判断或 publication readiness 上收到 OPL，会制造第二 truth owner，也会削弱 Codex CLI 在 MAS stage 内的自主探索能力。OPL 应提供 durable framework 能力，不能成为 MAS 的领域大脑。
- 影响：direct MAS skill path 保持一等入口；经 OPL 调用时必须回到同一套 MAS-owned CLI/MCP/product-entry/controller/stage surface。后续流程优化优先改 MAS stage policy、prompt、skill、AI reviewer、quality gate 和 route/decision receipt；不得把医学研究思路写成 OPL 机械脚本分流。

## 2026-05-11：OPL 是完整 stage-led 智能体运行框架，MAS 是医学论文 domain agent

- 决策：OPL 的新定位固定为完整智能体运行框架，而不是只做入口聚合或 product-entry facade。OPL 可以作为外部依赖承载 MAS：它负责 stage attempt、provider abstraction、queue/wakeup、retry/dead-letter、human-gate signal/query、attempt receipt、projection、shared lifecycle/index/restore primitives 和跨 domain skeleton。`Stage` 是大型任务步骤；Agent executor 是 stage 内最小执行单位，`Codex CLI` 是当前第一公民 concrete executor。
- 理由：MAS 已经在 monolith closeout 中验证了医学论文 domain 的 runtime、lifecycle、artifact、restore、stage knowledge 和质量闭环经验，但这些“智能体运行外围”不应长期由 MAS 私有维护。上收 OPL 能减少 MAS/MAG/RCA 重复底座，同时保持 MAS 对医学研究、论文质量和交付 authority 的唯一所有权。
- 影响：MAS 文档必须把 OPL 作为可依赖运行框架表达，同时继续禁止 OPL/Temporal/Hermes/local provider 写 MAS study truth、publication judgement、quality gate、current package、evidence/review ledger 或 artifact authority。MAS direct skill / local diagnostic path 可以独立运行；一旦进入 OPL-hosted production path，Temporal readiness 是必需前提。MAS 是 OPL family 中的医学论文/研究 domain agent；旧 MDS/DeepScientist/Hermes-first/外部 runtime 完善线只能作为 history、provenance、显式 executor/proof diagnostic、backend audit、upstream intake 或 parity reference 出现。

## 2026-05-10：Autonomy continuation ticket 成为 read-model 到执行闭环的桥

- 决策：`slo_status=breach`、`runtime_liveness_status=parked`、`runtime_decision=blocked` 或 `safe_reconcile_ready` 不能只停留在 read model。只要 controller 未给出 `stop_loss` / terminal stop，且没有 hard human confirmation gate，MAS sidecar export 必须生成一条幂等 `pending_family_tasks[]`，默认 task kind 为 `domain_route/reconcile-apply`。
- 理由：成熟长期 agent 工程的核心不是常驻进程本身，而是 durable identity、持久状态、可恢复 task、checkpoint、retry/dead-letter、human gate 与事件唤醒。Temporal 强调 crash-proof durable execution；Pydantic AI durable execution 明确面向 restart、long-running 和 human-in-the-loop；Cloudflare Agents 也把长期 agent 表达为 durable identity + SQLite state + schedules/fibers，而不是一直运行的进程。MAS 对应落点是把“发现了问题”转成 domain-owned executable ticket，再由 OPL provider 在线底座唤醒、入队和派发。
- 影响：`pending_family_tasks` 是 MAS 授权 OPL 入队的唯一跨仓自动推进桥。OPL 可以 enqueue / retry / dead-letter / notify / dispatch，但不能解释医学质量或直接写 truth。MAS sidecar dispatch 收到 `domain_route/reconcile-apply` 后，必须回到 MAS 自己的 `domain_route_reconcile` owner chain，执行 `scan -> consume -> execute-dispatch -> rescan`，并用 receipt 说明是否启动 Codex worker、是否 blocked、是否 no-op 或是否需要 human gate。

## 2026-05-10：Paper Progress SLO 成为自动推进闭环的最高运行目标

- 决策：MAS 自动运行的最高 SLO 固定为“论文是否产生可验证增量”，而不是 worker 是否 live、controller 是否写 packet、gate audit 是否刷新。有效进度只认 canonical manuscript/table/figure/result 变化、submission source/current package freshness proof、AI reviewer judgement 更新、publication gate replay 后 owner 前进。live worker 超过 grace window 仍无 meaningful artifact delta 时，必须投影为 `live_no_paper_delta` / `paper_progress_stall`，并进入 controller-owned redrive 或 owner handoff。
- 决策：`paper_progress_reconciler` 成为 paper-line 推进判断的单一 controller-style reconcile surface。它每次 tick 从当前 truth surfaces 重算 `desired_state`、`current_state`、`delta`、`decision` 与 `action_receipt`，不依赖旧 repair packet、旧 handoff 文案或上一轮补丁记忆。`domain-route-reconcile` 必须携带该 receipt；dry-run 不 dispatch，apply 只在 callable owner、fresh source fingerprint、非 human gate 与可解释 owner route 成立时写 outbox receipt。
- 决策：Paper work unit 采用 transaction contract。每个 work unit 必须能在 `owner_callable_registry` / owner route / batch lifecycle 中解释 `owner`、`callable_surface`、`required_inputs`、`required_outputs`、`artifact_delta_predicate`、`gate_replay_target`、`idempotency_key` 与 `source_fingerprint`。terminal success 需要同时有 owner receipt、required output、artifact delta 或 gate replay result；repeat suppression 只能阻断重复派单，不能阻断 handoff 到下一 owner。
- 决策：work-unit outbox 是幂等与安全重试的唯一落账面。`paper_work_unit_outbox` 对相同 `idempotency_key` + 相同 intent 返回等价 replay receipt；同 key 不同 intent fail-closed；同 `source_fingerprint` 已启动 worker 时写 `duplicate_source_fingerprint` receipt，不重复启动 worker，也不阻断 owner handoff / gate replay。SQLite refs index 表 `paper_work_unit_receipts` 只索引 receipt 和 cursor，不成为 paper/publication authority。
- 决策：owner callable registry 是 owner 可执行性的机器锚点。当前注册 owner 包括 `MAS/controller`、`ai_reviewer`、`publication_gate`、`quality_repair_batch`、`gate_clearing_batch` 与 `delivery_sync`；`owner_callable_surface_missing` 只能成为 controller-consumable blocker 或 repo-level missing callable blocker，不能把 `requires_user_input=false` 的 `waiting_for_user` 投影成真实用户等待。
- 决策：`PaperProgressState` 的用户面状态固定为七类：`progressing`、`awaiting_controller_redrive`、`blocked_controller_route`、`awaiting_callable_owner`、`awaiting_human`、`downstream_only`、`terminal_delivered`。所有进度入口至少投影 `actual_write_active`、`package_delivered`、`meaningful_artifact_delta`、`next_owner`、`why_not_progressing` 与 `safe_reconcile_command`；Progress Portal workspace dashboard 只做 human-facing projection，不写 truth。
- 决策：runtime retry budget exhausted 不再直接等于 external supervisor。若 paper work unit、owner route、source fingerprint、quality/publication gate 可解释，reconciler 先给 `MAS/controller` recovery lease reset / redrive；只有 route 缺失、callable 缺失或 repo-level owner gap 无法解释时，才暴露 repo-level blocker。Obesity 这类 `supervisor_only=true` 且有 artifact delta 的 live worker 显示为 `supervisor_only/live_quality_repair`，delivery missing 保持 downstream。
- 理由：三篇论文的共同失败模式是控制面有活动但论文无增量。成熟控制面经验也指向同一结论：Kubernetes controller 通过 current/desired state reconcile 推进状态；AWS idempotent API 通过 caller intent token 让 retry 安全，并用 timeout / retry / backoff / jitter 控制重试风暴；Temporal Activity 要求可恢复业务 activity 自身具备 timeout、heartbeat、retry 与 idempotency；SRE SLO adoption 要把 SLO 贴近用户旅程。MAS 的用户旅程就是论文资产是否产生可验证增量，对应落点是 owner route、idempotency key、source fingerprint、artifact delta predicate 与 gate replay proof。
- 影响：DM002 的 retry-budget / controller route 卡点应被投影为 controller redrive 或唯一 repo-level blocker；DM003 的 `blocked_turn_closeout_waiting_for_owner` / `owner_callable_surface_missing` 在 `requires_user_input=false` 时由 registry repair 或 MAS/controller 消费；Obesity 的 AI reviewer queue 由 callable `ai_reviewer` 消费，publishability 未放行前 delivery 缺失只能作为 downstream blocker 展示。repo capability landed 不等于 live controlled apply completed；真实三篇论文仍要在 repo gates 全绿后用 artifact delta、gate replay、owner 前进和 freshness proof 单独验收。
- 参考：[Kubernetes controller](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；[AWS timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter)；[Temporal Activity definition](https://docs.temporal.io/activity-definition)；[Google SRE SLO adoption](https://sre.google/static/pdf/SloAdoptionAndUsageInSre.pdf)。

## 2026-05-19：runtime transport 物理代码只能作为 OPL handoff 的 domain bridge

- 决策：`product-entry-manifest` 与 sidecar export 必须暴露 `runtime_transport_handoff_projection`。该投影逐项约束 `mas_runtime_core`、turn runner、worker lease、domain route scan/consume/dispatch/reconcile 和 `lifecycle_refs_adapter.py`：它们只能作为 domain owner receipt adapter、refs-only refs index、guarded apply / typed blocker、safe action projection 或 standalone diagnostic，不得声明 generic scheduler、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 或 workbench owner。
- 理由：MAS 历史 runtime transport 与 lifecycle refs SQLite 仍有 tracked physical code 和 focused tests。直接按文件存在与否判断会误导审计：这些文件既不能继续被理解为 MAS 私有 runtime 基座，也不能在 domain direct path、receipt parity 和 OPL replacement parity 未证明时盲删。
- 影响：当前 default online runtime owner 仍是 OPL / Temporal provider；MAS 只保留 domain receipt、typed blocker、artifact/publication authority 和 diagnostic bridge。后续物理删除、archive 或 tombstone 必须满足 no-active-default-caller、OPL replacement parity、domain receipt parity 和 history tombstone gate；未满足前，tracked 文件的存在不构成 MAS generic runtime owner claim。

## 2026-05-16：默认 domain SLO scheduler projection owner 迁到 OPL replacement

- 决策：`runtime-supervision-status`、`runtime-ensure-supervision` 和 `runtime-remove-supervision` 的默认 `--manager` 是 `opl`，输出 `scheduler_owner=opl_provider_runtime_manager` 与 `adapter_id=opl_family_runtime_provider`。默认入口只投影或委托 OPL `family_scheduler_replacement`，不安装、不刷新、不触发 MAS-owned LaunchAgent。MAS 保留 `outer_supervision_slo` 的 paper-progress 解释、owner receipt、typed blocker、safe action refs 和 no-forbidden-write evidence。
- 理由：OPL 已提供 runtime manager / provider SLO / family queue / intake / attempt ledger replacement surface；MAS 长期应收窄为 medical research authority pack + thin program surface。继续把本机 LaunchAgent 写成默认 scheduler owner 会让 MAS 持有通用 cadence、job registry 和 scheduler lifecycle，和 OPL-led family framework 分层冲突。
- 影响：`local` 已从公开 CLI manager choices 移除，只保留 tombstone/provenance refs；显式 Hermes 只保留 status/remove cleanup，不再作为 ensure/create/refresh/trigger scheduler path。workspace bootstrap 改为默认委托 OPL replacement，不再安装 MAS local scheduler。`no_active_caller_proof.default_caller_count=0` 是当前退役门槛：默认 CLI、workspace bootstrap、product-entry、sidecar 和 MCP 都不得再调用 local install path；local adapter 不允许 install、status、remove、trigger、loaded-state 或 install-proof 输出；Hermes adapter 不允许 install、refresh、trigger 或写 tick script。该迁移不等于真实 Temporal long soak、paper-line closure、artifact mutation 授权或 publication-ready。

## 2026-05-17：MAS functional privatization 分类进入机器边界

- 决策：MAS repo 内非知识层功能不再按长期 `opl_owned_replacement` / `retire_tombstone` 或旧 A/B/C owner 口径维护；`functional_consumer_boundary` 和 `mas-functional-consumer-followthrough` lane 通过 `functional_module_inventory` 记录代码路径级清单，并改用四类可执行处置：`declarative_pack_generated_surface`、`refs_only_adapter`、`minimal_authority_function`、`legacy_cleanup_physical_retired`。当前 18 项计数为 generated surface 7、refs-only adapter 6、minimal authority function 3、physical-retired legacy 2。workspace/source intake、workbench/portal shell、domain route scan/dispatch、generic CLI/MCP/product wrappers、scheduler lifecycle、queue/attempt/retry/dead-letter 和 generic transition runner 进入 declarative pack / OPL generated surface handoff；runtime lifecycle SQLite、paper work-unit outbox、storage maintenance、publication-route memory transport、artifact lifecycle audit 和 terminal attach 只保留 refs-only adapter；study truth、publication quality verdict 和 artifact authority 保持 minimal authority function；local LaunchAgent scheduler install path 与 workspace-local watch wrappers 已物理退役为 tombstone/provenance refs。
- 理由：MAS 历史上吸收了 runtime lifecycle、storage maintenance、artifact audit、portal/workbench、terminal attach 和 scheduler 等通用外围能力。它们的经验可以作为 OPL replacement contract 和 adapter proof，但长期 owner 不能继续留在 MAS，否则会重新制造 MAS-owned generic persistence/lifecycle/workbench/storage platform。
- 影响：`runtime_lifecycle.sqlite` 降格为 MAS domain lifecycle refs index / refs-only adapter；它可以索引 MAS owner receipt、surface ref、restore/retention proof 和 locator，消费 OPL lifecycle index refs，但不能写 domain truth，也不能被写成 MAS generic persistence、generic lifecycle 或 restore-retention engine。`paper_work_unit_outbox` 这类仍在 MAS 内的索引面只允许保留 paper work-unit identity、publication gate context、artifact delta obligations 和 owner receipt refs；queue/outbox/retry/attempt 的通用语义应由 declarative pack / generated surface 消费。新增 CLI/MCP/Skill/product-entry/sidecar surface 若触及 generic 能力，必须先接入 pack compiler / generated surface 或 refs-only adapter；legacy cleanup 项按无 active caller、无 fixture/provenance 必需和 replacement proof 直接退役，不新增兼容别名。

## 2026-05-16：现有论文 workspace active binding 必须清理旧 MDS 污染

- 决策：`workspace-monolith-migrate --apply` 生成的 active profile、`runtime_binding.yaml` 和 migrated `quest.yaml` / `runtime_state.json` 必须使用 MAS active layout：`runtime/`、`runtime/quests/<quest_id>`、`mas_runtime_core` 与 `mas-runtime-core`。旧 `med_deepscientist_*` root、旧 `research_backend_id` / `research_engine_id`、legacy diagnostic、旧 quest root、旧 runtime root、旧 confirmed baseline absolute path 和旧 metric contract absolute path 只能进入 `historical_fixture_ref` / `explicit_archive_import_ref` 的 read-only provenance。
- 理由：现有论文项目如果继续在 active binding 或 quest snapshot 中携带旧 MDS backend/root/state-machine 字段，OPL/MAS consumer 会把旧状态机、旧 baseline absolute ref 或旧 local runtime 误读成当前 owner，从而污染新 MAS domain authority pack 和 thin program surface。
- 影响：迁移器和 focused tests 必须阻断旧 MDS active path 回流；真实 paper truth surface 仍由 MAS controller/runtime/canonical artifact flow 持有，不允许用 migration apply 手工 patch `current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json`、paper/submission package、runtime SQLite 或 restore archive。缺 OPL provider/runtime/workbench surface 时写 handoff / contract expectation，不在 MAS 内重建 generic scheduler、runner、queue 或 workbench。

## 2026-05-16：legacy physical cleanup 只能通过 gated archive/tombstone apply

- 决策：旧 `ops/med-deepscientist` 物理根不能按目录存在与否直接删除；必须先跑 `workspace-legacy-physical-cleanup-audit`，证明 active runtime replacement 成立、旧 workspace-local service wrapper 已清空、且 profile、runtime binding / quest snapshot、monolith migration ledger、delivery manifest、controller decision / publication eval 等 targeted surface 不再需要旧物理根。通过 gate 后，`workspace-legacy-physical-cleanup-apply --dry-run|--apply` 只能把旧 physical root 移到 `runtime/archives/legacy_mds/<timestamp>/` 或创建 absent-root tombstone，并把 targeted provenance refs 改写到 archive/tombstone/ref-only surface；它不改 paper/package/controller/runtime truth。
- 理由：现有论文 workspace 已经完成 active runtime 迁移，但旧物理根和历史读模仍会污染后续 operator 判断、status read model 或 migration proof。用 MAS-controlled apply surface 统一 archive/tombstone/profile/guidance/layout/wrapper/artifact provenance rewrite，可以保留历史信息，同时避免旧 MDS state-machine 路径回流到 active MAS architecture。
- 影响：5 个真实 profile 已完成 closeout：AS biologics、DM-CVD workspace/local、NF-PitNET 的旧 physical root 已归档，Obesity 已 tombstone；post audit 均为 `reference_counts={}`、`next_required_action=no_legacy_physical_cleanup_required`。apply surface 明确不写 `current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json` 当前 authority、paper/submission package、runtime SQLite、restore archive 或 generic runtime state。后续只把它作为 drift guard 和新增 legacy ref cleanup surface，不能把 archive proof 写成 paper closure、publication ready 或 OPL provider live proof。

## 2026-05-09：历史 MAS supervision scheduler contract，local 曾是默认 adapter

- 决策：当时的 `MAS supervision scheduler contract` 只允许解释为 MAS standalone/local diagnostics 的 outer supervision owner；`local` 曾是 MAS 本地默认 scheduler adapter，macOS 落到 MAS-owned LaunchAgent。OPL Full online runtime 的 family-level wakeup 由 OPL family runtime provider 承担，再通过 MAS sidecar dispatch 进入 domain owner surface。
- 理由：fresh repo 状态显示 scheduler 应承担单一、可替换的 adapter 工作：生成 tick script、注册/更新/触发/删除 job、提供 job registry/latest run/session projection 和 liveness。它不持有研究执行、turn continuation、publication judgment、quality authority 或 study truth。成熟工程实践也要求 scheduler 只生产可审计触发，幂等、并发、missed-run、receipt 和 migration 由系统 contract 明确表达。
- 影响：这条历史决策已被 2026-05-16 replacement 决策覆盖为默认 OPL owner；本段只保留 provenance。两层 readiness 必须继续分开显示，避免把 provider、Hermes 或旧 local LaunchAgent 写成 MAS study truth 或质量 owner。

## 2026-05-08：MAS monolith closeout 取代外部 MDS 默认运行依赖

- 决策：`med-autoscience` 是唯一日常 repo、唯一研究入口和默认 operation owner。外部 `med-deepscientist` checkout 不再是 MAS 默认 study/status/progress/cockpit operation 的运行必需依赖；保留的 MDS / DeepScientist 价值只能作为显式 backend audit、explicit archive import reference、upstream intake 或 parity oracle 出现。
- 理由：no-history physical absorb 已把 source provenance、author guard、capability parity fixtures、retained capability absorb 与 default-runtime-retirement 落到 repo-level guard；继续把 MDS 写成默认 backend 会重新制造第二 owner 和安装依赖漂移。
- 影响：未来从 MDS / DeepScientist 学习或引入能力，必须记录 source ref/hash、snapshot checksum、license refs、capability classification、remaining surface inventory、MAS owner、authority boundary、tests、parity proof 与 no-history contributor audit；classification 只允许 `mas_owned`、`rewrite_in_mas`、`fixture_only`、`retire`、`external_source_archive_only`。`publication_eval/latest.json`、`controller_decisions/latest.json`、`progress_projection`、`domain_health_diagnostic`、paper/manuscript/current_package 与 artifact rebuild proof 不得被 MDS 写回或授权。

## 2026-05-07：Controller work-unit evidence adoption 只识别受控证据，不改变 AI-first 质量 owner

- 决策：controller work-unit evidence adoption 固定为 objective evidence / freshness / currentness 的识别与路由机制，不成为论文质量、投稿 readiness 或 AI reviewer judgement 的替代 owner。`cold_archive`、`report_history`、runtime report store 和 restore proof 只能作为 restore / report evidence source；它们可以证明某个受控 work unit、artifact 或 runtime event 曾经发生，也可以参与 currentness/freshness 判断，但不能直接关闭 `publication_eval/latest.json`、`controller_decisions/latest.json`、AI reviewer workflow 或 submission-facing quality gate。若 worker 已完成受控 work unit，supervisor 的下一步是 gate recheck、owner route 前进或转交下一 owner，不得重复派发同一 work unit。
- 理由：DM002/DM003 的 fresh 只读状态显示，两条线当前都需要从 `progress_projection`、`study_progress`、`runtime_supervision/latest.json`、`publication_eval/latest.json` 与 `controller_decisions/latest.json` 判断是否 live、是否 stale、是否需要人工介入；repo 修复或 lifecycle/archive proof 成立不等同于 study 已恢复。机械脚本若把 archived report、history replay 或 fresh timestamp 当成质量 authority，会重新制造“同一 work unit 被反复执行”或“旧包被误读为当前包”的风险。
- 影响：domain route、consumer 和 execute-dispatch 只能采用带 stable work-unit fingerprint、owner、required output surface 与 freshness/currentness proof 的 evidence。NF-PitNET 003 不因本次 DM002/DM003 风险核对被触碰；DM002/DM003 必须用 fresh runtime truth surfaces 判断 live managed runtime、stale supervision、no-live-worker 和 publication gate blocker。前台检测到 live managed runtime 或 `execution_owner_guard.supervisor_only=true` 时进入 supervisor-only；若只是 repo-side fix landed、archive proof verified 或 report history 可恢复，仍只能表述为平台/证据面状态，不能宣称 study 已恢复或论文包已放行。

## 2026-05-06：宏观状态、owner route 与文件生命周期进入同一 current-truth 合同

- 决策：MAS 用户宏观状态固定为 `writer_state/user_next/reason` 三段短枚举，materialized surface 是 `artifacts/runtime/study_macro_state/latest.json`；`owner_route` 固定为 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。request handoff、default executor dispatch 和 executor 都必须校验 route、allowed action 与 idempotency key。终局止损文件生命周期采用 `terminal_study_file_lifecycle_plan` dry-run surface，只有不可重开 `stop_loss` 才能标记 runtime history 精简候选，物理 apply 仍要求 manifest、sha256 与 restore proof。
- 理由：近期 DM001、DM002、NF002/NF003 与 stop-loss workspace 的故障显示，runtime liveness、publication gate、AI reviewer、dispatch executor 和 storage cleanup 若各自使用局部判断，会在修复一层后暴露下一层漂移。成熟控制面把 current/desired state 收敛、幂等重试 token、refs index 和 manifest/checksum preservation 分开处理；MAS 的落点是文件 authority + reducer + owner route + SQLite refs index receipt。
- 影响：`study-state-matrix` 优先读取 materialized macro state；`study_progress` 默认读不再物化 AI-first ledgers；consumer request handoff 与 executor 都受 owner route gate 约束；runtime health 显式 source signature 幂等；cleanup apply 消费 retention report 时必须重新校验 target sha256。`user_next=none/reason=stop_loss/reopen_allowed=false` 可以开启 terminal file lifecycle dry-run，但不能裸删历史文件。
- 参考：[Kubernetes controller reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS Builders Library idempotent API client request token](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；[SQLite Application File Format](https://www.sqlite.org/appfileformat.html)；[RFC 8493 BagIt manifest/checksum contract](https://www.rfc-editor.org/rfc/rfc8493)。

## 2026-05-05：Repo Markdown / README prose 不再由 pytest 锁定措辞

- 决策：repo-tracked Markdown / README prose 进入 `documentation_review_only` 分类，由人工/Agent review 负责，不再用 pytest 脚本读取文档并断言标题、链接、段落、固定短语或 intake 表格内容。preflight 对 docs-only 变更不规划 pytest 命令；workflow、配置、源码、测试、JSON/YAML/TOML contract、生成器输出、运行时模板和生成产物行为仍按对应 owner surface 验证。
- 理由：文档是接力和审阅材料，脚本锁措辞会把表达、锚点和链接变成伪 contract，导致小文案变更触发无关失败，也会诱导后续 Agent 为了测试去 patch 文档。真正需要机器门禁的是可执行行为、schema、CLI/MCP/API、reader/export/restore contract 和 runtime/product surface。
- 影响：退役现有纯 Markdown/README wording tests；`dev_preflight_contract` 保留 `documentation_review_only` 分类以显式识别 docs-only 变更，但其 planned commands 为空。后续新增测试不得重新引入 repo docs wording anchors；若文档内容需要可验证约束，应先把约束上升为结构化 contract、代码生成器、schema 或运行时资产，再测试该 contract/生成结果。

## 2026-05-05：Runtime lifecycle 历史与索引采用 SQLite refs index，authority surface 继续保留文件形态

- 决策：MAS/MDS 的 runtime lifecycle、storage audit、watch state、run/report history 与 retention ledger 进入 SQLite refs index 方向；SQLite 只持有可索引历史、摘要、游标、路径引用、checksum 与投影缓存，不替代 `publication_eval/latest.json`、`controller_decisions/latest.json`、`progress_projection`、`runtime_binding.yaml`、dataset manifest、restore index、paper/manuscript/current_package 等 authority 或交付产物。
- 理由：真实 `.ds` 膨胀来自运行态 mirror、日志、run/codex home/history/worktree 与 audit 历史产生的大量小文件，而不是 Git 源码仓本身。SQLite 官方把应用状态文件格式、pile-of-files 替代、事务更新、并发读取与小对象聚合列为成熟适用场景；Git 的 `untracked-cache`、`fsmonitor`、`sparse-index` 只能改善 Git working tree/index 扫描，不能解决 MAS/MDS 自己生成的 runtime 小文件生命周期。
- 影响：新增 runtime/storage/history 能力时，默认把“latest / canonical authority / human delivery”继续写成可恢复文件，把“append-heavy telemetry / historical report index / retention ledger / cursor pagination / compact projection”写入 SQLite refs index。SQLite 文件必须是可重建或可导出索引层；任何需要医学质量、publication readiness、artifact authority 或 restore safety 的判断仍回到 MAS durable truth surface 和 MDS restore contract。
- 参考：SQLite Application File Format、SQLite WAL、SQLite Archive / SQLAR、SQLite small-blob filesystem benchmark；Git `update-index` 的 untracked-cache/fsmonitor 与 sparse-checkout sparse-index 文档。

## 2026-05-20：manuscript story repair 必须由 write owner 跟进到正文 surface

- 决策：`manuscript_story_repair` 的完成证据必须包含 canonical manuscript story surface delta，即 `paper/draft.md` 或 `paper/build/review_manuscript.md`。当 controller repair packet 返回 `blocked_reason=manuscript_story_surface_delta_missing` 且 `next_owner=write` 时，MAS managed worker 必须继续作为 write owner 修订正文 surface；该 closeout 不得 parked 为等待用户，也不得由 ledger-only delta 宣称完成。
- 理由：DM002 暴露出 quality repair batch 能正确更新 claim/evidence/review ledger，但没有改正文稿面，随后 runtime 把同 owner 的缺口停成 blocked closeout，造成“质量闭环完成但论文不变”的假进度。这个缺陷属于 MAS write-owner follow-through 合同和 runtime completion 语义，不是单篇论文的人工补丁问题。
- 影响：Codex runtime prompt 会对 `manuscript_story_repair` 注入 follow-through contract，要求先跑 controller command，再在 same-owner story-surface blocker 下继续修订 `paper/draft.md` / `paper/build/review_manuscript.md`。runtime completion 会把 `manuscript_story_surface_delta_missing -> write` 识别为 `runner_incomplete` 并继续 redrive；外部 owner 的 blocked closeout 仍保持等待 owner/user 的原语义。该规则只保证 owner-chain 不假完成，不替代 AI reviewer 或 publication gate 的医学质量 verdict。

## 2026-05-02：MAS AI-first Research OS 成为长线目标架构

- 决策：长线目标固定为 `MAS AI-first Research OS`。MAS 作为唯一 research / quality / publication / artifact / user-visible truth owner；MDS 已收敛为显式 backend audit、explicit archive import reference、upstream intake 与 parity oracle companion。机械系统只负责 evidence、status、completeness、blocker、projection 与 replay；AI reviewer workflow 持有科学质量、医学写作质量、publishability 与 submission-facing readiness。
- Authority anchor：AI reviewer artifacts 持有科学质量；机械系统只负责 evidence、status、completeness、blocker、projection 与 replay。
- 理由：近期论文修复证明，机械 gate 先给 ready、下游再补救会把质量风险推迟到最贵的阶段。AI-first 的真实落点应前移到 pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 与真实论文 soak，而不是在文档层增加措辞约束。
- 影响：新增架构、质量、运行、产物、观测或 MDS 吸收能力时，必须回到 [MAS AI-first Research OS Architecture](./references/mainline/ai_first_research_os_architecture.md) 的 owner / authority / proof 口径；MDS no-history absorb 只允许在 parity proof、owner cutover、rollback surface 与质量不降级证明成立后以 MAS-authored snapshot 落地。当前 no-history absorb 已关闭为 repo-level guard/parity/default-dependency-retirement；更大的 runtime core ingest、controlled cutover 或平台结构调整仍需独立 gate。本决策不新增文档 wording gate，不修改测试或 preflight contract。

## 2026-05-01：StudyTruthKernel 成为 study 级用户可见真相 reducer

- 决策：`StudyTruthKernel` 固定为 MAS study 级运行真相 reducer。`progress_projection` 与 `study-progress` 可以投影 shadow snapshot，但 `artifacts/truth/latest.json` 只能由显式 reconcile、controller tick 或 materialize 调用刷新。
- 理由：近期 stopped / finalize / package authority / reviewer revision / publication gate 事故证明，多个 read-model 各自解释 next action 会制造 authority drift。把 dominance rules 收口到单一 reducer，才能让 package authority、publication gate 解释、delivery state 和 human gate 输出一致。
- 影响：后续 truth/gate/status 事故必须同时补 reducer rule、fixture test 与 runbook entry；`MDS` 输出只能作为 runtime/native/review event 进入 MAS truth event，再由 MAS reducer 产生用户可见动作。

## 2026-05-01：RuntimeHealthKernel 成为 runtime liveness 与 recovery reducer

- 决策：`RuntimeHealthKernel` 固定为 `(study_id, quest_id)` 的运行健康 reducer。`runtime_health_snapshot` 负责 worker liveness、retry budget、recover/relaunch/escalate 语义；`last_launch_report` 只能保留最近动作摘要，不再作为 live worker authority。
- 理由：恢复链路曾把 stale run handle、fresh supervisor tick、daemon probe 和 worker liveness 混成一类状态，容易无限 recovering 或误报 live。运行健康必须用 event history 和有限状态机收口。
- 影响：`runtime domain-health-diagnostic --apply`、`runtime reconcile-health` 与 controller tick 才能 materialize health；runtime health 只能驱动 runtime action，不得反向覆盖 `StudyTruthKernel.canonical_next_action`、publication gate、package authority 或 delivery state。

## 2026-05-05：Supervisor request ownership 与 submission milestone parking 收口到 request-only / controller-stop 边界

- 决策：portable supervisor scan 可以生成外层可消费的 request packet，但 `publication_gate_specificity_required` 的 owner 固定为 `publication_gate`，`return_to_ai_reviewer_workflow` 的 owner 固定为 `ai_reviewer`，supervisor consumer 只写 owner handoff task、consumer packet 和 default executor dispatch。第三步 `domain-route-execute-dispatch` 只能在 prompt contract 与 forbidden surfaces 完整时调用 owner-authorized repo surface，或写明 blocked reason。对 stopped submission/finalize milestone，supervisor 只能刷新 controller-owned parked decision、确认或停止 runtime 资源，并把 repair lifecycle 写成 `state=parked` / `authority=controller_stop`。
- 理由：近期 supervisor parking 与 request queue 修复证明，如果外层 scan/consumer 直接推断 publication quality、AI reviewer judgement 或 paper package 状态，会重新制造第二 owner。外层工程代理需要的是清晰的 request owner、required output surface 和 forbidden surface，而不是替代 MAS quality/publication authority。
- 影响：`domain-route-consume`、`artifacts/supervision/consumer/*` 与 `artifacts/supervision/requests/*` 都是 handoff/request/dispatch surface；它们不得修改 `paper/current_package` 或 `manuscript/current_package`，不得放宽 quality/publication gate。`domain-route-execute-dispatch` 可以调用 `publication_gate` owner surface 物化 gate-owned `publication_eval/latest.json`，但不能合成 AI reviewer judgement；AI reviewer output 仍必须来自结构化 reviewer workflow。submission milestone parking 不授权人工 patch；后续稿件反馈仍必须走 durable revision intake 与 MAS-controlled relaunch/resume。

## 2026-05-05：Supervisor scan 采用 current truth owner-route reconcile 合同

- 决策：`owner-route-reconcile` 固定为 controller-style reconcile loop。它每轮先读取当前 `progress_projection`、`study_progress`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 `StudyTruthKernel` epoch，再产出唯一 `owner_route`。`runtime liveness`、retry budget、publication gate、AI reviewer 与 dispatch executor 都只能作为 current truth 输入或 owner action，不得各自用局部判断覆盖当前 owner。若当前 controller decision 与 publication work-unit fingerprint 对齐，且 controller action 明确要求同线 runtime redrive，no-live / retry-exhausted 只能路由给 `mas_controller`，不能升级成 `external_supervisor`。
- 理由：DM001/DM002/DM003/NF002 的连续故障显示，单点修补 stopped、package handoff、AI reviewer 或 executor 都会暴露另一层漂移。成熟控制面通常把 current state 与 desired state 的收敛放在一个 reconcile loop 中；幂等重试需要调用方意图 token；可重试 activity 必须有稳定 idempotency key。MAS 的对应合同就是 `truth_epoch + source_fingerprint + next_owner + allowed_actions`。
- 影响：`owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。consumer 只能传播 route；executor 执行前必须比对最新 route，并拒绝 `owner_route_stale` 或 `owner_route_next_owner_mismatch`。同一 scan 即使生成多个候选 action，`allowed_actions` 也只包含当前 `next_owner` 可执行的动作；其他 action 只能留作观测或下一轮 owner，不得被同 tick executor 抢跑。runtime redrive 还必须把当前 controller decision 和同 fingerprint 的 actionable publication targets 写入 runtime authorization，避免 MDS 因缺可执行 target 把当前 work unit 再次判成 gate pending。完成态、completion evidence owner、auto-runtime parked、manual hold 与 stop-loss 都必须通过同一 route 投影，避免 stale lifecycle、publication gate 或 AI reviewer 队列重新打开已完成或已停驻论文线。
- 2026-05-15 补充：MAS-owned `domain-transition::*` fingerprint 是 controller-owned transition authority，不要求反向伪装成 `publication_eval.recommended_actions`。live Codex CLI prompt 的读取链路固定为 `domain_transition_table -> controller_decisions/latest.json -> runtime_state.last_controller_decision_authorization -> prompt`；只要 controller decision 已物化、未要求 human confirmation、fingerprint work-unit id 与 `next_work_unit.unit_id` 匹配、action type 落在该 transition 的白名单内，就可以 relay 到 runtime authorization。旧 prompt、旧 task-intake、旧 publication action 或旧 default executor dispatch 都不得覆盖这条当前 controller authority。由于 Codex CLI prompt 是 run 启动时的一次性快照，controller refresh 后还必须检查 active run 的 `prompt.md` 是否含当前 work-unit fingerprint 或 work-unit id；若仍是旧 prompt 或缺 prompt，MAS 需要通过受控 pause/resume 强制 fresh turn，不能把新 authorization queue 到旧执行器进程。
- 2026-05-15 追加：fresh prompt 只是第一层 postcondition；第二层 postcondition 是 prompt 内的 callable action 也必须消费当前 authorization。MAS managed Codex CLI worker 调用 `domain-route-execute-dispatch` 时使用受限 `--managed-runtime-worker` 通道：只有环境标记、quest root、quest id、run id、`worker_running=true`、`active_run_id` 和 `current_controller_authorization` / `last_controller_decision_authorization.controller_actions` 全部匹配，executor 才能用当前 controller authorization 重建 action owner route。若 consumer latest 已被后续监管 tick 清空，而 fresh managed prompt 仍显式请求同一 controller action，executor 可以从当前 authorization 合成受限 dispatch 壳再校验执行；外层 developer heartbeat / 人工 CLI 仍必须走 `developer_apply_safe` GitHub/user-config gate，旧 default executor dispatch 不能在 managed worker 内覆盖当前 controller transition authority。
- 参考：[Kubernetes Controllers current/desired state reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS Builders Library “Making retries safe with idempotent APIs”](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；Temporal Activity idempotency and retry guidance。

## 2026-05-18：display materialization 必须保留表格 claim binding

- 决策：`materialize_display_surface` 重建 paper table catalog 时，必须保留已有 `claim_ids`，或从 `claim_evidence_map.json` 的 `display_bindings` / `display_refs` / `table_bindings` 派生表格 claim binding；不得把 T1/T2 这类主文表的 claim binding 重写为空。
- 理由：DM002 的质量修复线暴露出 MAS controller 已经写入 T1/T2 claim binding 后，display materializer 会在 gate replay 中清空表格 claim binding，导致 `T1_T2_claim_bindings` 反复保持 open。这个问题属于 MAS 基座 materialization contract 缺陷，不应由单篇论文手工 patch table catalog 解决。
- 影响：quality-repair-batch / gate-clearing replay 产出的 display-to-claim closure 必须以 controller materialization 后的 catalog 为准；表格 claim binding 是 paper-facing evidence surface 的一部分，后续显示物化、publishability gate 和 AI reviewer recheck 都不能把它降级为 optional metadata。

## 2026-05-20：controller work unit 可消费同一投递 run 的 turn closeout

- 决策：`controller_work_unit_evidence_adoption` 在处理 generic completed work unit 时，候选 `turn_closeout` 不只限当前 `active_run_id`，也包括同一 control-intent ledger 中本次授权之后已 `delivered` 的 run id。候选仍必须是 `status=completed`、`meaningful_artifact_delta=true`、未 blocked、时间不早于当前 authorization，并匹配当前 work unit / route / delivered run identity。
- 决策：同一 control-intent business key 下若已有 `artifact_written` 后又出现新的 `delivered` 事件，旧 adoption 不再视为当前完成证据；controller 必须重新扫描最新 delivered-run closeout，避免旧 closeout 长期盖住后续更完整的 manuscript repair 或 gate recheck 证据。这是 evidence currentness 修复，不是质量 gate 放宽。
- 决策：若 managed worker 已在当前授权之后写出 `turn_closeouts/<run_id>.json`，但 control-intent ledger 缺少对应 `delivered` 事件，controller 仍可采纳该 closeout；采纳条件必须同时满足 completed、meaningful artifact delta、unblocked、时间不早于当前授权，且当前 work unit 的已知 canonical surface 合同被满足。例如 `manuscript_story_repair` 必须同时引用 `paper/draft.md` 与 `paper/build/review_manuscript.md`。未知 work unit 或未知 surface delta 仍然 fail closed。
- 理由：DM002 暴露出 managed runtime 在上一轮已写出 `paper/draft.md` / `paper/build/review_manuscript.md` 的 completed closeout 后，下一轮 active run 先启动，controller 只看当前 active run 会漏掉刚完成的 owner receipt，导致同一 `manuscript_story_repair` 被重复派发。
- 影响：这是 owner receipt / currentness 消费修复，不放宽 publication gate、AI reviewer 或医学质量判断；旧决策、未投递 run、blocked closeout、无 meaningful manuscript delta 的记录仍不能关闭当前 work unit。

## 2026-05-21：paper autonomy repair-recheck 必须兑现已声明 owner callable

- 决策：`paper_autonomy/repair-recheck` 进入 MAS sidecar 后，`paper_repair_executor` 必须识别 reviewer refinement work unit 中已声明的 MAS owner callable。`quality_repair_batch.run_quality_repair_batch` 交给 quality-repair batch owner 执行；`ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow` 交给 AI reviewer owner dispatch 执行。只有缺 profile/context 或 callable 真不存在时，才允许返回 typed blocker。
- 理由：DM003 route-back 暴露出系统性缺口：reviewer refinement 已正确生成 `quality_repair_batch` / `ai_reviewer` callable surface，OPL provider 也已把 task 送达 MAS sidecar，但 executor 仍按旧的 structured patch 局部路径返回 `owner_callable_surface_missing`，导致论文质量修复停在“看见问题但不执行 owner”的状态。

## 2026-05-21：embedded AI reviewer callable 必须自带 owner-dispatch envelope

- 决策：`paper_repair_executor` 收到 `ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow` callable 时，必须先物化 MAS-owned AI reviewer request 与同源 ready default-executor dispatch，再把该 dispatch 作为 inline consumer payload 交给 `domain_owner_action_dispatch`。不得要求上游 OPL queue 预先生成 study-level consumer dispatch，也不得让 dispatcher 凭 action type 跳过 request/owner-route/currentness 校验。
- 理由：DM003 暴露出 `ai_reviewer_recheck` 已进入 paper repair executor、但 `domain_owner_action_dispatch` 没有可消费 dispatch 时返回 `execution_count=0` 的空执行，随后被误报为 `owner_callable_surface_blocked`。embedded callable 是 MAS owner contract 的一部分，转换点必须提供完整 request/dispatch envelope；失败时应得到执行级 blocker，例如 `ai_reviewer_request_missing`、`ai_reviewer_record_missing` 或 `repeat_suppressed`，而不是空 executions fallback。
- 影响：repair executor 继续禁止直接写 `manuscript/current_package`、质量放行或投稿授权；它只负责把已声明 owner callable 接到 MAS owner surface，并写 owner receipt / typed blocker。单篇论文反馈必须转化为可回归的 owner-callable dispatch 测试，避免后续再由人工发现“写入 task intake 但不推进修复”的问题。

## 2026-05-22：DM002 显式写作修复 work unit 与 Agent Lab 质量目标

- 决策：`dm002_same_line_publication_paper_repair` 是 DM002 当前 AI reviewer route-back 的 manuscript story-surface work unit。`quality_repair_batch`、`gate_clearing_batch`、control-plane route gate、upstream paper repair materializer 与 `repair_execution_evidence` 必须把它当作 upstream paper-write repair，而不是折叠为 generic `analysis_claim_evidence_repair`；完成证据必须包含 `paper/draft.md` 或 `paper/build/review_manuscript.md` canonical story-surface delta。
- 理由：DM002 暴露出 generic gate-clearing 可以更新 ledger/display surfaces，却不重写当前医学稿件，随后 AI reviewer 仍判定 Abstract、Methods、Results、calibration/grouped calibration 与内部语言没有吸收当前修改意见。显式 write work unit 必须保留 owner 语义和 manuscript delta requirement。
- 影响：DM002 的 deterministic writer 只消费 MAS-owned analysis harmonization evidence 与 paper tables/figures，生成 clean external-validation manuscript story；不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal` 或 `manuscript/current_package`，也不授权 quality/submission readiness。

- 决策：Agent Lab / opl-meta-agent 可消费的 `prediction_model_external_validation` quality target refs 必须显式包含 methods reproducibility、numeric abstract/results with uncertainty、uncertainty metrics、calibration/grouped calibration intervals、NHANES unweighted framing、claim-evidence/display alignment without runtime language、internal-language scrub。该 contract 只指导 MAS repo patch 与 regression，不是 publication quality verdict。
- 理由：本轮 DM002 反馈不能只沉淀为单篇 writer fix；它应成为 MAS quality suite 的 repeatable regression，使后续类似 prediction-model external-validation 稿件在写作前或 reviewer route-back 后暴露同类缺口。
- 影响：`contracts/agent_lab_handoff.json` 与 `agent_lab_medical_manuscript_quality` family targets 必须保持这些 refs；OPL/Agent Lab 只能消费 refs、发出 developer work order 或 typed blocker，不能直接写 study truth 或宣布论文 ready。

## 2026-05-01：医学稿件初稿质量前移为 manuscript-native prose 合同

- 决策：first draft 质量不再只依赖 `medical_publication_surface` 后置拦截；`study_charter.paper_quality_contract.structured_reporting_contract.first_draft_quality_contract` 与 quality OS 必须在写作前提供 IMRAD section purpose、reporting-guideline obligations、clinical question / population / timepoint / outcome / display-to-claim map，以及 manuscript-native medical journal prose 要求。
- 理由：真实稿件修订暴露出 MAS 初稿可能把 controller checklist、figure/table anchor、author-confirmation placeholder、claim-boundary 标签和 operations/review 语言带进正文。医学论文初稿必须从临床问题、研究设计、结果解释和投稿读者问题出发。
- 影响：写作 route 在判断 draft ready 前必须检查这些输入；缺少支撑时 route back 到同线写作修复或有限补充分析。`medical_publication_surface` 继续作为 safety net，而不是主写作策略。

## 2026-04-26：稿件反馈后的 stopped milestone 统一视为 revision reactivation

- 决策：已达投稿包、submission-ready 或 finalize 里程碑后，如果收到用户、导师或审稿层面的稿件反馈，必须把该反馈作为同一 study 的 `reviewer_revision` reactivation intake 处理。`stopped` 状态和 `current_package` 存在只说明旧里程碑曾经成立，不能授权 Codex 前台直接修改 `manuscript/current_package/` 后宣称完成。
- 理由：003 / 004 类 manuscript revision 暴露出重复误判风险：Agent 容易把“quest 已停车”误读成“当前包可人工小修”。这会绕开 MAS/MDS 的 study truth、claim-evidence、review ledger 和 package regeneration 链路。
- 影响：`submit-study-task` 对非 live reviewer revision 要返回 reactivation guidance；workspace AGENTS、agent-entry templates、legacy write/finalize overlays 和 invariants 都必须显式要求先 durable intake，再 MAS-controlled relaunch/resume，最后从 canonical paper authority 重新生成 `current_package`。

## 2026-04-26：初稿质量升级扫描进入 study charter 与 reviewer-first route-back

- 决策：`study_charter.paper_quality_contract` 固定新增 first-draft quality contract；写作 route 在判断 draft ready 前必须扫描已验证数据资产是否支持更强的时间点、角色/人群、中心/地理、指南对应、亚组/关联分析和现实采用约束叙事。若当前初稿过轻且不改变锁定 claim 边界，默认 route back 到 `analysis-campaign` 做有限补充分析。
- 理由：近期 manuscript 修改反馈暴露出一个系统性问题：初稿如果只按已有结果描述成稿，容易漏掉数据资产本身已经能支撑的更强 paper shape。把这类反馈上收到 MAS 合同层，可以在初稿前阻断“描述性够用”的低质量出口。
- 影响：后续 `survey_trend_analysis`、写作 route、reviewer-first 检查与 evidence/review 合同都必须先问“数据资产还能否支撑更强且可验证的论文形态”，再决定写作、有限补充分析或 human gate。

## 2026-04-26：OPL Runtime Manager 作为薄运行管理层接入 MAS projection

- 状态：已被 2026-05 的 OPL stage-led family runtime provider 与 Temporal-backed production substrate 口径 supersede。保留本段用于追溯薄管理层阶段。

- 历史决策：MAS 与 OPL 的长线对齐曾采用 `OPL Runtime Manager / opl family-runtime -> configured family runtime provider -> MAS sidecar export/dispatch -> MAS domain entry/projection` 的分层口径。当前读法应收口为 `OPL Product Entry -> OPL stage-led family runtime provider -> MAS sidecar export/dispatch -> MAS domain entry/projection`。MAS 只暴露 task registration、runtime_control projection、status/artifact locator、approval/wakeup boundary、sidecar guarded dispatch 与现有 durable truth surface；旧 `OPL Runtime Manager` 只作为历史薄管理层名词保留，不成为 MAS 研究 truth 或执行器 owner。历史 Hermes online substrate 口径只作为迁移背景；`Hermes-Agent` 当前只作为显式非默认 Agent executor adapter / proof lane。
- 理由：这能先获得长期托管、唤醒、健康检查和跨域状态索引的收益，同时保留 MAS 自己的 study authority、publication gate 与 evidence/review ledger。若未来需要自有长期常驻 sidecar，也能沿 Runtime Manager 的 adapter/projection contract promotion，而不重写 MAS domain truth。
- 影响：后续涉及 OPL handoff、runtime_control、product-entry manifest、status projection、sidecar export/dispatch 或 hosted lane 的文案，都必须使用 OPL stage-led family runtime provider / hosted integration 口径；MAS durable truth surface 仍是唯一研究真相。

## 2026-04-21：公开主语固定为独立 domain agent，单一 app skill 承接稳定 surface

- 决策：`Med Auto Science` 的对外第一身份固定为“可被 Codex 或其他通用 agent 直接调用的独立 medical research domain agent”；其单一 MAS app skill 承接稳定 callable surface；`OPL` 只承担 OPL stage-runtime session/runtime/projection 编排与 shared modules/contracts/indexes。
- 理由：公开主语直接决定用户入口与 owner 语义。将 MAS 固定为独立 domain agent，并把稳定 surface 收口到单一 app skill，才能避免把 MAS 误写成 OPL 内部模块，也避免把桥接载荷写成第一主语。
- 影响：README 与核心 docs 必须明确 domain agent、单一 app skill、CLI/workspace commands 和 durable surface 的主次关系；`OPL handoff`、`product-entry manifest` 与 OPL stage-led framework 术语只作为集成和运行框架边界，不作为对外第一身份。

## 2026-04-11：历史 docs 骨架与分层

- 历史决策：以 `project / architecture / invariants / decisions / status` 作为 docs 核心骨架，并将其余文档收口到 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/`。
- 理由：避免文档平铺，确保入口明确、角色清晰、可维护。
- 影响：删除冗余的 `documentation-governance.md`，统一文档规则入口。
- 当前读法：本决策的核心骨架仍有效；目录 taxonomy 已被 2026-05 文档组合治理 supersede。当前 recurring material 使用 `active/public/product/runtime/delivery/source/policies/specs/references/history`，旧 `program/` 与 `capabilities/` 只作为历史迁移来源或 path-stable provenance 读取。

## 2026-04-11：OMX 退役并归档

- 决策：OMX 只作为历史材料保留在 `docs/history/omx/`，`.omx/` 禁止作为当前 workflow 入口。
- 理由：避免历史工具状态干扰 repo-tracked 真相。
- 影响：OMX 相关材料仅保留为参考，不进入当前运行路径。

## 2026-04-11：冻结 runtime backend interface

- 决策：`MedAutoScience` controller 只通过 `runtime backend interface contract` 访问 managed runtime backend，不把 `med-deepscientist` 具体实现名作为 controller 判定真相，也不把外部 MDS checkout 当成默认 operation dependency。
- 理由：为 Hermes 等新 backend 接入提供稳定 contract，先完成 backend abstraction，再进入 controlled cutover。
- 影响：`runtime_binding.yaml` 增加 backend-generic 字段；显式声明但未注册的 backend 必须 fail-closed 阻断。

## 2026-04-11：目标 runtime 方向优先于旧 substrate 延长线

- 决策：后续新增投入默认服务“OPL Temporal-backed family runtime，Temporal 作为 production required substrate”这条目标形态，而不是继续把旧默认 substrate 或 Hermes-first 路线深磨成长期产品方向。
- 理由：历史基线和过渡实现仍然有价值，但它们应作为迁移桥、回归基线与 provenance 存在，不能反向决定主线目标。
- 影响：所有后续 tranche 都必须明确区分“当前 repo-verified baseline”与“长线目标”，并保持 display 独立支线不被主线误伤。

## 2026-04-11：当前仓内的 `Hermes` 只代表 repo-side seam，不代表上游集成已落地

- 决策：仓内保留的 `Hermes` 命名，只能表示 repo-side outer-runtime seam / shim / contract owner，不得写成“上游 `Hermes-Agent` 已成为当前 runtime owner”。
- 理由：迁移期曾经通过受控 `MedDeepScientist` backend 承接长时执行，但当前 no-history physical absorb 已关闭外部 MDS 默认依赖；文档与命名必须诚实反映这条 closeout。
- 影响：后续所有 runtime 文档都必须把“目标中的上游 `Hermes-Agent`”“MAS-owned default operation surface”和“显式可选 MDS diagnostic / intake / oracle refs”拆开表述；display / paper-facing asset packaging 独立线继续排除在当前 tranche 外。

## 2026-04-12：固定 runtime substrate 与 research executor 分层

- 决策：外层 runtime substrate / orchestration owner 必须与 MAS-owned research owner surface 分层；OPL-hosted production path 由 Temporal-backed OPL family runtime 承担，Temporal 是 production required provider，`Hermes-Agent` 只保留为显式非默认 Agent executor adapter 或 executor/proof lane，不得替代 MAS-owned research owner surface 或把外部 MDS repo 重新变成默认执行脑。
- 理由：当前真正高风险的不是“没有统一执行脑”，而是“没有统一长期在线 runtime substrate”。若在外层 runtime ownership 尚未稳定前，就强制把 backend 内部的 `Codex + skills` 执行生态整体替掉，最容易出现功能降级。
- 影响：后续继续学习 `MedDeepScientist` / DeepScientist 时，必须按 source provenance、executor route、owner boundary、contract 与 parity proof 决定是否吸收；不允许把“接入 Hermes”偷换成“已完成研究执行 owner 替换”。

## 2026-04-20：方向锁定后的质量与自治默认收口到 MAS

- 决策：方向锁定之后，普通科研推进、论文质量判断、reviewer concern 排序、证据充分性判断与 `bounded_analysis` 一类有限补充分析推进，默认由 `MAS` 自主完成；human gate 收口到重大边界与最终投稿前审计。
- 理由：长时间自治和医学论文质量需要同一 owner、同一 study truth 和同一审计边界，`MAS` 已经持有 study authority、workspace authority、证据推进与人工接手点，适合承担默认裁决权。
- 影响：后续 program、status、runtime 与 eval 文档都要按这个 owner 边界写作；`MDS` 只保留显式 backend audit、explicit archive import reference、行为等价 oracle 与上游 intake buffer。

## 2026-04-20：study charter 承载质量总合同

- 决策：study charter 成为医学质量总合同入口，统一冻结研究问题、claim、证据强度、有限补充分析边界、review 与 submission hygiene 约束；`paper evidence ledger` 与 `review ledger` 作为该合同的执行记录与审阅记录。
- 理由：论文质量提升依赖一份前置、持续、可审计的合同，后续 evidence/review ledger 围绕这份合同推进，才能把设计、分析、审阅和投稿收口到同一条 `MAS` 主线。
- 影响：后续涉及 evidence、review、submission hygiene、bounded analysis 的 owner 叙事，都要显式回指 study charter contract，而不是分散写成独立局部机制。
