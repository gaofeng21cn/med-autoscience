# MDS Capability Parity Matrix

MDS 的长线角色已经降为 frozen source archive / historical fixture / explicit legacy diagnostic / provenance reference。MAS 吸收 MDS 能力时按 capability / remaining surface 推进，不按目录搬迁。

MDS 不能授权 medical quality。医学论文质量、publication readiness、controller decision 与最终 package state 都由 MedAutoScience 持有；MDS 只能提供 historical fixture、source provenance、mechanical signal fixture 和 explicit legacy diagnostic 输入。

2026-05-08 no-history physical absorb closeout 已把当前 retained capability 固定为 MAS-owned proof bundle：source provenance 见 `docs/references/med-deepscientist/source_provenance.json`，当前 snapshot 为 `med-deepscientist@35976b7d6e3b99b15b57ec44ff5f5d959b342ecc`，archive sha256 为 `f8dc31822dc52ecc6e073f54c8b5c95cd46646e299a67cd1c1f6f7f3764e0d5b`。该 closeout 没有导入上游 git history；MDS 独立 checkout 只保留为 frozen source archive、historical fixture 和 explicit legacy diagnostic / provenance reference。

2026-05-08 functional monolith inventory 追加机器可读分类，固定在 `med_autoscience.controllers.mds_capability_parity` 与 `docs/references/med-deepscientist/source_provenance.json`。允许分类只有 `mas_owned`、`rewrite_in_mas`、`fixture_only`、`retire`、`external_source_archive_only`；旧 `absorb` / `oracle` / `compat` 不再是 machine-readable cutover contract 值。

2026-05-08 behavior equivalence audit 追加 `mds_behavior_equivalence_matrix`。该矩阵明确区分 `default_independence` 与 `full_mds_daemon_behavior_equivalence`：MAS 默认 operation 不依赖外部 MDS repo / daemon / WebUI，但默认监管是 `Hermes gateway cron` 每 300 秒调用一次 `watch-runtime --max-ticks 1`，不是 MDS resident HTTP/WebSocket daemon 的完整行为复刻。详细差异见 [MDS Behavior Equivalence Gap Matrix](./mds_behavior_equivalence_gap_matrix.md)。

2026-05-08 Runtime Turn Lifecycle correction 把旧 MDS daemon 的连续科研主循环落成 MAS-owned runtime surface：`runtime_core_daemon` 和 `worker_runner_lifecycle` 现在归类为 `mas_owned`。`runtime_watch` / supervisor / Hermes cron 只负责 reconcile、wakeup、redrive 和 stale recovery；真正的连续执行由 `schedule_turn`、`complete_turn_and_normalize`、runner monitor、delayed auto-continue timer、worker lease、turn receipt 和 user message queue 决定。

2026-05-08 Runtime Continuity closeout 在 behavior matrix 中追加 `runtime_continuity_completion` 合同：`runtime_session` 只读投影 worker/session/freshness，`recovery_intent` 记录 controller-owned recovery intent，`runtime_reconcile_trigger` 只输出 safe reconcile 推荐和 blocked reasons，`runtime_continuity` 投到 progress/cockpit/product-entry/Portal/MCP/OPL。该合同明确 `external_mds_repo_required=false`、`mds_daemon_required=false`，并固定 `quality_ready_authorized=false`、`publication_ready_authorized=false`、`submission_ready_authorized=false`。

## Capability Matrix

| Capability | Classification | MDS role | MAS owner | Parity proof | Medical quality authority |
| --- | --- | --- | --- | --- | --- |
| runtime execution | `mas_owned` | backend | Runtime OS | runtime execution replay and recovery regression suite | blocked for MDS |
| artifact inventory | `fixture_only` | behavior oracle | Artifact OS | artifact inventory projection parity fixtures | blocked for MDS |
| paper contract health | `fixture_only` | mechanical oracle | Quality OS | backend preflight parity without quality-ready authority | blocked for MDS |
| manuscript coverage | `fixture_only` | mechanical oracle | Quality OS | mechanical coverage fixtures with AI preflight required | blocked for MDS |
| prompt stage discipline | `mas_owned` | behavior oracle | Quality OS | stage prompt contract parity and prompt-only gate audit | blocked for MDS |
| memory / lesson store | `retire` | behavior oracle | Evaluation OS | lesson intake and incident learning parity fixtures | blocked for MDS |

## Remaining Surface Inventory

The functional monolith inventory is machine-readable as `mds_remaining_surface_inventory`. It classifies workflow-level surfaces rather than unique functions, and it does not import upstream history.

| Surface | Classification | MAS owner | MDS final role |
| --- | --- | --- | --- |
| runtime core daemon | `mas_owned` | Runtime OS | external source archive only |
| quest lifecycle | `mas_owned` | Runtime OS | historical oracle fixture only |
| worker and runner lifecycle | `mas_owned` | Runtime OS | external source archive only |
| channels, connectors, and transport | `rewrite_in_mas` | Runtime OS | explicit legacy diagnostic only |
| MCP surface | `retire` | MAS MCP | retired surface |
| TUI and Web visual status | `rewrite_in_mas` | Progress Portal | explicit legacy diagnostic only |
| GitOps workspace state | `retire` | Runtime lifecycle | retired surface |
| skills and overlay templates | `fixture_only` | MAS app skill | historical fixture only |
| team and multi-agent coordination | `fixture_only` | Controller | historical oracle fixture only |
| upstream source archive | `external_source_archive_only` | Governance | external source archive only |

## Behavior Equivalence Matrix

The behavior matrix is machine-readable as `mds_behavior_equivalence_matrix`. It classifies workflow behavior rather than functions, and it intentionally blocks overclaiming MAS as fully equivalent to the MDS resident daemon.

| Surface | Equivalence class | MAS default action |
| --- | --- | --- |
| daemon residency | `purpose_equivalent_with_different_timing` | Use MAS with scheduler-latency awareness. |
| supervision cadence | `purpose_equivalent_with_different_timing` | Use 300s Hermes gateway cron one-shot tick for outer supervision only. |
| turn completion continuation | `behavior_equivalent` | Use MAS Runtime Turn Lifecycle Kernel. |
| quest create/resume/pause/stop | `behavior_equivalent` | Use MAS Runtime OS. |
| live worker/session tracking | `purpose_equivalent_with_different_timing` | Use durable liveness/read-model state. |
| crash recovery and auto-resume | `purpose_equivalent_with_different_timing` | Use MAS tick or explicit watch/ensure runtime. |
| queued user messages/mailbox | `partially_equivalent` | Use durable task intake and controller handoff. |
| progress visibility | `behavior_equivalent` | Use MAS Progress Portal / study-progress / cockpit. |
| WebUI/WebSocket/terminal streaming | `not_equivalent_retired` | Retired from default MAS operation. |
| connector/channel background delivery | `not_equivalent_retired` | Retired from default MAS operation. |
| MCP surface | `purpose_equivalent_with_different_timing` | Use MAS MCP adapter to owner surfaces. |
| GitOps state management | `not_equivalent_retired` | Use SQLite lifecycle and restore proof. |
| memory and lesson store | `partially_equivalent` | Use MAS memory / incident-learning read models. |
| team and multi-agent coordination | `historical_fixture_only` | Keep as historical fixture/reference. |
| artifact interaction handoff | `partially_equivalent` | Use Artifact OS locator and handoff refs. |
| daemon lifecycle controls | `not_equivalent_retired` | Use Hermes cron supervision controls. |
| workspace-local host service | `not_equivalent_retired` | Clean retired service evidence; do not install. |

`turn_completion_continuation` 是本轮重新评估后的关键变化：旧 MDS 的 runner completion 后状态归一化和下一 turn 调度，已经落在 MAS Runtime Turn Lifecycle Kernel；`Hermes gateway cron` 只剩 outer supervision / stale recovery cadence。`runtime_continuity_completion` 是 session tracking 和 crash recovery intent 的 landed refinement，但仍保留 scheduler-bound timing 差异，不宣称 resident daemon equivalence。

## Parity Proof Requirements

### runtime execution

- MAS contract: `study_runtime_status` / `runtime_watch` 持有 runtime decision 与 recovery visibility。
- MDS oracle: MDS quest execution trace 只能作为 backend behavior fixture 被 replay。
- Proof: MAS recovery decision 必须匹配或显式 supersede replayed MDS behavior。

### runtime core daemon / turn lifecycle

- MAS contract: `mas_runtime_core` 暴露 `schedule_turn`、`complete_turn_and_normalize`、`inspect_turn_lifecycle`，并把 `chat_quest` 和 `resume_quest` 接到同一 turn kernel。
- MDS oracle: MDS `schedule_turn` / `_normalize_status_after_turn` 的语义被保留为 behavior oracle。
- Proof: turn completion 必须清理 `active_run_id` / `worker_running`，优先处理 queued user messages，按 `auto` 延迟调度并由 kernel timer 消费 `auto_continue`，并在 human/terminal gate 停住；inspect/watch 只做到期 delayed turn 的 crash-recovery drain。

### worker and runner lifecycle

- MAS contract: `MasTurnRunner` 记录 worker lease、run receipt、claimed user messages、idempotency key 与 per-quest serialization。
- MDS oracle: MDS one-worker-per-quest turn worker 和 active run lifecycle 作为 behavior fixture。
- Proof: active worker 期间追加 turn 只进入 pending/queue，当前 turn 完成后先 drain queued user messages 再 drain pending worker reason；stale JSON liveness 会被归一为 not live；recovery redrive 必须产生 MAS turn receipt。

### artifact inventory

- MAS contract: MAS artifact inventory 是 consumer-facing projection owner。
- MDS oracle: MDS artifact layout 只作为 legacy inventory compatibility fixture。
- Proof: MAS inventory 保留 discoverability，同时不把 delivery authority 交给 MDS。

### paper contract health

- MAS contract: publication gate 与 controller decisions 持有 paper readiness。
- MDS oracle: MDS contract checks 只是 mechanical preflight observation。
- Proof: MDS health signal 不能把 paper 提升为 medical-quality ready。

### manuscript coverage

- MAS contract: AI review 与 publication eval 持有 medical manuscript quality。
- MDS oracle: MDS coverage count 只是 mechanical completeness signal。
- Proof: Coverage parity 可以触发 review request，不能授权 final quality。

### prompt stage discipline

- MAS contract: MAS controller stage 持有 allowed prompt transition。
- MDS oracle: MDS stage prompt 只提供 behavior example 与 violation fixture。
- Proof: parity import 后 MAS stage discipline 仍然 explicit、auditable。

### memory / lesson store

- MAS contract: MAS incident learning 持有 reusable lessons 与 operator-visible memory。
- MDS oracle: MDS lessons 是 parity 和 regression case 的 intake material。
- Proof: lesson 被作为 evidence 导入，不能作为 autonomous quality decision。

## Cutover Rule

每个能力都必须先有 MAS consumer contract、MDS behavior fixture、quality gate not relaxed 证明、rollback surface，以及旧 MDS authority surface 的 fixture-only 标记或退休记录。

`mds_capability_cutover_gate` 没有完整 proof bundle 时必须 fail-closed：`owner_switch_allowed=false`，`cutover_status=blocked_pending_parity_proof_bundle`。这避免 remaining surface 只靠 landed contract 描述就被误报为已完成 owner switch。

MDS paper contract health 和 manuscript coverage 永远不能授权医学论文质量 ready；它们只提供 backend preflight 或 mechanical oracle 信号。

当前 `tests/test_mds_capability_parity.py` 和 `tests/test_mds_retained_capability_absorb.py` 共同固定：

- 每个 retained fixture 必须带 provenance ref、oracle input 和 MAS proof bundle。
- MAS owner surface 必须显式 match 或 supersede MDS behavior。
- `quality_authority_granted`、`publication_ready_authorized`、`submission_ready_authorized` 对 MDS mechanical signal 必须保持 `false`。
- 保留 `deepscientist` 字样的代码只能落在 legacy / compat / oracle diagnostic 语义下；machine-readable capability classification 使用 `mas_owned` / `rewrite_in_mas` / `fixture_only` / `retire` / `external_source_archive_only`。

## Manifest Projection

`inspect_med_deepscientist_repo_manifest(...)` 可以暴露 parity / deconstruction summary，帮助 operator 知道当前 MDS fork 是否是受控 backend/oracle 参考面。这个 projection 不会把 MDS 提升成 quality owner；其中的 medical quality authority owner 固定为 `MedAutoScience`，且 `medical_quality_authority_granted_to_mds=false`。
