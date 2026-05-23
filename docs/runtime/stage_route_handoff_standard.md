# MAS Stage / Route / Handoff 标准

Status: `active_runtime_support`
Owner: `MedAutoScience`
Purpose: `stage_route_handoff_standard`
State: `active_support`
Machine boundary: 本文是 MAS 面向 OPL stage-led runtime 的人读标准。机器 truth 继续归 `agent/` semantic pack、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、sidecar export/dispatch receipt、domain transition table、owner receipt、typed blocker、publication eval、controller decision 和真实 workspace artifact。
Date: `2026-05-21`

## 结论

`stage` 和 `route` 不是同一层对象。MAS 可以声明 stage 语义与 route 语义，但 MAS 不负责 route 与 route 之间的 generic 调度。

- `stage` 是 OPL provider-backed attempt 的大型研究步骤与 admission 单位。
- `route` 是 MAS 医学 owner-chain 的 domain transition recommendation，表示下一步 owner、route-back、human gate、typed blocker 或 owner action。
- `handoff` 是 MAS 给 OPL 的 body-free refs-only 交接包，用来让 OPL hydrate queue、创建 stage attempt、执行 retry/dead-letter、唤醒 provider 或生成 operator workorder。
- 机器入口是 sidecar owner-route pending task 上的 `route_transition_contract` 与 `stage_graph_handoff`：前者给 OPL 读 allowed / forbidden refs 与 owner 边界，后者给 OPL 读 `journal-resolution` / `finalize` 这类 route 的 stage graph hints。
- `domain_owner/default-executor-dispatch` 的机器入口是 `Owner-Route Attempt Protocol` envelope。MAS 必须在 envelope 中给出当前 `domain_owner`、`action_type`、`work_unit_id`、currentness basis、allowed / forbidden write surfaces、typed closeout requirement 和 completion boundary；OPL 只能用它 hydrate queue/attempt/provider transport。

MAS repo 内不再扩展私有 queue、scheduler、checkpoint、resume、retry/dead-letter、worker liveness arbiter、route graph runner 或 generic state-machine runtime。OPL 当前若承载能力不足，应补 OPL stage graph / transition runner / runtime manager / App read model，而不是在 MAS 回补私有 runtime。

## 固定术语

| 术语 | Owner | MAS 可做什么 | MAS 不能做什么 |
| --- | --- | --- | --- |
| `stage` | OPL runtime owns lifecycle; MAS declares semantics | 声明 prompt、knowledge、quality gate、expected receipt、monitor refs、forbidden authority、医学成功条件。 | 持有 attempt ledger、provider checkpoint、retry/dead-letter、worker residency 或 stage runner。 |
| `route` | MAS declares domain semantics; OPL transports | 给出 next owner、route-back reason、allowed action、guard refs、typed blocker、owner receipt expectation。 | 把 route 当小 stage、直接调度下一 route、写 runtime liveness/redrive truth。 |
| `domain_transition` | MAS domain truth | 用 domain transition table / study state matrix 表达医学状态和 guard。 | 作为 generic state-machine runner 或 publication-ready verdict。 |
| `owner_route_handoff` | MAS produces refs; OPL consumes | 写 body-free handoff artifact，暴露给 sidecar export 和 OPL queue hydrate。 | 写 `.ds/runtime_state.json` 的 generic owner-route latch，清 active run，改 worker running，直接 resume/stop/pause runtime。 |
| `owner_route_attempt_protocol` | MAS declares domain execution envelope; OPL transports | 声明 registered reason、priority lattice、currentness basis、allowed/forbidden surfaces、typed closeout packet 和 provider/domain completion boundary。 | 把 provider completion 当作 MAS owner receipt，或让 OPL 判断医学质量、publication ready、package freshness、study truth。 |
| `authority_function` | MAS | 执行医学方法学、AI reviewer verdict、artifact mutation authorization、memory accept/reject、owner receipt signing。 | 承担 OPL queue、provider lifecycle、App/workbench generic shell。 |
| `child_graph` | OPL | MAS 只声明子任务语义、guard、receipt refs。 | MAS 不实现 child graph scheduler。 |

## 当前 MAS stage 与 route

当前 stable stage 是 6 个大型研究步骤：

1. `direction_and_route_selection`
2. `baseline_and_evidence_setup`
3. `bounded_analysis_campaign`
4. `manuscript_authoring`
5. `review_and_quality_gate`
6. `finalize_and_publication_handoff`

当前 route contract 包含 10 个 domain route：

1. `scout`
2. `idea`
3. `baseline`
4. `experiment`
5. `analysis-campaign`
6. `write`
7. `review`
8. `finalize`
9. `decision`
10. `journal-resolution`

这些 route contract 里出现的 `durable_outputs_minimum`、`hard_success_gate`、`memory_closeout_obligations` 是 domain obligation 和 owner receipt expectation，不是 route 自己拥有 runtime attempt lifecycle。

## OPL 承载方式

MAS 在 OPL 中应按下面链路运行：

```text
MAS route / transition / authority refs
  -> sidecar export pending family task
  -> OPL family-runtime queue hydrate
  -> OPL provider-backed stage attempt
  -> OPL transition runner / stage graph
  -> MAS authority function or owner action dispatch
  -> MAS owner receipt / typed blocker / route-back / human gate ref
  -> OPL receipt ledger + App/operator read model
```

route 之间的调度由 OPL 负责：

- OPL 读取 MAS `family_transition_spec`、`study_state_matrix`、route contract、stage control plane 和 owner-route handoff。
- OPL 执行 transition / guard / matrix runner，并在 queue / stage attempt ledger 中记录 provider receipt、closeout、dead-letter、retry 和 human gate。
- MAS owner callable 返回医学 owner receipt、typed blocker、no-op currentness proof、route-back reason、human gate schema 或 artifact/memory/source refs。
- OPL 只能存 refs 和调度下一 attempt；它不能写 MAS study truth、publication verdict、artifact body、memory body、`current_package` 或 submission readiness。

## 指定杂志格式整理任务

客户指定投稿杂志后，格式整理不是 MAS 私有的小 stage 串行脚本。正确运行链路是：

1. MAS 在 `journal-resolution` / `finalize` route 中声明目标 journal、author guideline refs、format requirement refs、submission package boundary、artifact authority boundary 和 human gate 条件。
2. OPL 创建或继续 `finalize_and_publication_handoff` stage attempt；如果需要内部拆分，拆为 OPL stage graph nodes，例如 `journal_requirements_resolution`、`format_delta_plan`、`artifact_mutation_authorization`、`independent_format_review`、`submission_package_handoff`。
3. MAS authority function 只在需要医学/投稿权威判断时运行：确认目标 journal 要求、判断 manuscript/table/figure/package 变更是否符合医学语义和 publication gate、签 owner receipt 或 typed blocker。
4. artifact/package mutation 必须由 MAS artifact authority 授权并产生 receipt；OPL 只调度 attempt、保存 refs、触发 reviewer/auditor、人类审批和 App/operator projection。
5. 独立 reviewer/auditor record 不能由同一 executor 自审关闭；format ready / submission handoff 只能由 MAS owner receipt、independent review record、人类 gate receipt 或 stable typed blocker 关闭。

这解释了“交付完里程碑投稿包后，客户指定投稿杂志，按指定杂志改格式”到底属于什么流程：它是 `finalize_and_publication_handoff` stage 下的 `journal-resolution` / `finalize` route transition，并由 OPL stage graph 调度子节点；MAS 保留目标 journal 解释、artifact mutation authority、publication gate 和 owner receipt。

## Handoff Packet 规则

允许输出：

- `domain_route_ref`
- `owner_route_ref`
- `owner_route_attempt_envelope`
- `owner_reason_contract`
- `owner_route_currentness_basis`
- `task_kind`
- `dedupe_key`
- `source_scope_refs`
- `artifact_scope_refs`
- `workspace_scope_refs`
- `runtime_event_refs`
- `expected_owner_receipt_refs`
- `typed_blocker_refs`
- `human_gate_schema_ref`
- `authority_boundary`
- `no_forbidden_write_ref`
- `required_closeout_packet`
- `completion_boundary`

禁止输出：

- study truth body
- paper body 或 manuscript body
- publication verdict body
- AI reviewer verdict body
- artifact body / package body
- memory body
- `current_package` mutation
- runtime queue state、retry state、dead-letter state、worker liveness truth

## Owner-Route Attempt Protocol

MAS default-executor handoff 必须先通过 `mas-owner-route-attempt-protocol.v1`：

1. `owner_reason_contract` 必须来自 MAS registry。未注册 reason 不能生成 ready dispatch。
2. `priority_lattice` 固定为 hard methodology/source blocker、pending AI reviewer request、AI reviewer currentness、write route-back、package freshness、delivery/human handoff。
3. `owner_route_currentness_basis` 至少绑定 work unit fingerprint、truth epoch、runtime health epoch、owner reason 和 source fingerprint；有 current publication eval 时同步带 `source_eval_id`。
4. envelope 必须声明 `allowed_write_surfaces`、`forbidden_surfaces`、`required_closeout_packet` 和 `completion_boundary.provider_completion_is_domain_ready=false`。
5. OPL 只记录 attempt started/completed/blocked/failed、typed closeout refs、stdout/session/provider timing；MAS 消费 closeout refs 后再决定 owner receipt、AI reviewer eval、publication gate、package freshness或 typed blocker。

## 并行落地 Lane

下面是一步到位目标下可并行推进的 MAS lane。每条 lane 必须独立 worktree、独立验证，完成后吸收回 main 并清理临时 worktree/branch。

| lane | 目标 | 完成门槛 |
| --- | --- | --- |
| `route_contract_clarity` | route contract 与 stage control plane 文档明确 route 不是 runtime unit。 | docs/status、runtime index、migration inventory 都指向同一标准；无新增机器 truth。 |
| `owner_route_handoff_no_write` | sidecar/export/dispatch 只写 body-free handoff 和 dispatch receipt。 | focused tests 证明不写 `.ds/runtime_state.json`、`.ds/user_message_queue.json`、publication eval、controller decisions、`current_package`。 |
| `journal_resolution_flow` | 指定 journal 格式整理进入 `journal-resolution` / `finalize` route + OPL stage graph。 | 目标 journal refs、format delta refs、artifact authority receipt、independent review/human gate/typed blocker 可被 OPL ingest。 |
| `executor_reviewer_auditor_split` | executor、reviewer、auditor 分离成独立 OPL invocations。 | quality/format/publication gate 不允许同一 invocation 自审关闭。 |
| `transition_matrix_consumption` | MAS `study_state_matrix` / transition table 持续暴露给 OPL runner。 | OPL runner pass 只证明 matrix 可消费；真实 owner receipt/typed blocker 才能关闭 route。 |
| `runtime_control_plane_physical_retirement` | runtime_transport、SQLite lifecycle、worker lease、status/workbench shell 中的通用 runtime 控制面按 no-alias 退役；剩余只允许 domain authority refs、owner receipt、typed blocker 和 OPL handoff refs。 | 新投影不得声明 MAS generic queue、attempt ledger、scheduler、retry/dead-letter、worker residency、runtime lifecycle 或 read-model owner。 |
| `paper_line_canary` | 真实 paper-line 证明 OPL attempt -> MAS owner chain。 | 产出 progress delta、AI reviewer/gate receipt、artifact movement、human gate、stop-loss、owner receipt 或 stable typed blocker。 |

## 禁止误写

- 不把 `route` 写成 MAS 自己调度的小 stage。
- 不把 transition runner pass 写成 publication-ready、submission-ready 或 artifact-ready。
- 不把 OPL provider completion 写成 MAS owner receipt。
- 不把 owner-route handoff 写成 runtime liveness/redrive 仲裁。
- 不把旧 runtime/control adapter 写成 MAS generic runtime owner、compat alias、diagnostic fallback 或当前 active caller gate。
- 不用同一 agent execution + 自审关闭 AI-first quality gate。
