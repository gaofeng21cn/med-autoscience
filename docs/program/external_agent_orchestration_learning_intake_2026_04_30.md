# External Agent Orchestration Learning Intake 2026-04-30

这份记录对应 Lane A：把外部 agent orchestration 项目 `Symphony` 与 `agency-agents` / `NEXUS` 的学习结果转成 MAS repo-tracked intake record。目标是吸收可验证的编排纪律，不引入新的 MAS owner。

## Source Snapshot

- source SHA: `openai/symphony@58cf97d`
- source SHA: `msitarzewski/agency-agents@783f6a7`
- source links: Symphony README/SPEC/WORKFLOW
  - [Symphony README](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/README.md)
  - [Symphony SPEC](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/SPEC.md)
  - [Symphony WORKFLOW](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/WORKFLOW.md)
- source links: Agency README/NEXUS strategy/handoff templates
  - [Agency README](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/README.md)
  - [NEXUS strategy](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/nexus-strategy.md)
  - [handoff templates](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/coordination/handoff-templates.md)

## Decision Matrix

| Lesson | Decision | MAS mapping | Boundary |
| --- | --- | --- | --- |
| Symphony single orchestrator state for claimed/running/retrying work units | `adopt_contract` | MAS should keep `study_runtime_status` / `runtime_watch` / `controller_decisions/latest.json` as the visible work-unit 状态 spine for long-running studies. | This does not make Symphony the MAS runtime owner. |
| Symphony per-issue isolated workspace and cwd enforcement | `adopt_contract` | Preserve MAS workspace isolation and explicit artifact pickup paths so external callers know which workspace owns a run. | No generic workspace reset policy is imported. |
| Symphony retry/backoff/reconciliation semantics | `adopt_contract` | Encode retry/backoff/reconciliation as controller-visible runtime recovery discipline: retry is a state with evidence, not a hidden loop. | MAS controller remains the decision owner. |
| Symphony workflow prompt and workpad conventions | `adopt_template` | Reuse the structured workpad idea for MAS operator notes, validation evidence, blocker state, and handoff to human review. | Do not require Linear as the only workpad or source of truth. |
| Symphony structured logs and optional status/API surface | `adopt_template` | Treat observability as durable status projection: active run, retry delay, workspace path, token/runtime totals, recent events, and cleanup status should be readable. | Optional dashboard/API ideas remain template-level only. |
| NEXUS structured handoff documents | `adopt_template` | Map structured handoff into MAS task intake, reviewer response, bundle handoff, and operator pickup notes. | Persona routing language is not imported. |
| NEXUS evidence-over-claims quality gates | `adopt_contract` | Reinforce MAS `publication_eval/latest.json` and publication gate semantics: AI reviewer gate and evidence-over-claims must govern manuscript readiness, not agent self-report. | No external QA persona becomes publication judgment owner. |
| NEXUS retry cap and escalation templates | `watch_only` | Useful as a reference for bounded retries and explicit escalation records. | MAS already has controller decisions and runtime escalation records; import only after a concrete gap appears. |
| Linear as a required tracker entry | `reject` | 不引入 Linear 必需入口. MAS may consume external tracker context, but study truth stays in MAS durable surfaces. | External tracker state cannot replace MAS study state. |
| Symphony scheduler as top-level MAS owner | `reject` | 不引入 Symphony scheduler 作为 MAS owner. Symphony is a reference for orchestration discipline only. | MAS study truth/publication judgment/controller decision owner stays unchanged. |
| Agency generic persona inventory and NEXUS persona routing | `reject` | 不引入 generic persona library / NEXUS persona 库. MAS needs medical-quality contracts, not a broad agent catalog. | MAS reviewer and controller roles stay repo-owned. |

## Why This Is Valuable To MAS

1. 长期自治：Symphony shows a concrete model for daemon-like continuation, bounded turns, retry queues, and operator-readable recovery state. MAS should keep strengthening its own long-running study runtime around the same visible lifecycle discipline.
2. work-unit 状态：The useful abstraction is not the issue tracker itself; it is a normalized work unit with claim, running, retrying, completion, terminal, and handoff states. MAS maps that to `program_id` / `study_id` / `quest_id` / `active_run_id`.
3. 隔离 workspace：Per-work-unit workspace ownership and cwd enforcement map directly to MAS study workspace isolation, artifact inventory, and restore-point projection.
4. retry/backoff/reconciliation：Retries should have attempt count, reason, delay, and reconciliation outcome. MAS should avoid invisible loops and should keep recovery judgments in controller-readable records.
5. observability：Operators need a compact state surface with active sessions, retry delays, runtime totals, recent events, workspace path, and cleanup status. This aligns with MAS `runtime_watch` and `study_progress` projection.
6. structured handoff：NEXUS handoff templates are valuable because they force context, deliverable, evidence, quality criteria, blockers, owner, and next receiver into a stable format.
7. evidence-over-claims：NEXUS quality gates reinforce MAS's current rule that readiness must be supported by evidence, review ledger, `publication_eval/latest.json`, and artifact state rather than narration.
8. AI reviewer gate：The NEXUS "default needs evidence" posture matches MAS's AI reviewer gate: manuscript readiness requires an evidence-backed reviewer judgment, not mechanical projection alone.

## Explicit Reject / Watch Record

- 不引入 Linear 必需入口：Linear can remain a source example, but MAS cannot depend on Linear for the default study workflow.
- 不引入 Symphony scheduler 作为 MAS owner：Symphony scheduler semantics are reference material for orchestration learning, not a replacement for MAS controller/runtime surfaces.
- 不引入 generic persona library / NEXUS persona 库：MAS should keep domain roles tied to medical research, review, controller, and publication contracts.
- 不改变 MAS study truth/publication judgment/controller decision owner：external orchestration lessons must land as MAS-owned contracts/templates only.
- `watch_only`: NEXUS retry caps, escalation formats, and phase reports are useful references, but MAS should import them only through existing `runtime_escalation_record.json`, `controller_decisions/latest.json`, and publication gate surfaces.

## MAS Landing Rule

The acceptable landing path is selective learning: adopt contracts that strengthen durable study runtime, publication-quality proof, and handoff surfaces; adopt templates that make operator pickup more structured; watch broad orchestration playbooks until a MAS-specific gap exists; reject any source pattern that moves authority away from MAS study truth, publication judgment, or controller decisions.
