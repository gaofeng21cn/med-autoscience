# External Agent Orchestration Learning Intake 2026-04-30

这份记录对应 Lane A：把外部 agent orchestration 项目 `Symphony` 与 `agency-agents` / `NEXUS` 的学习结果转成 MAS repo-tracked intake record。目标是吸收可验证的编排纪律，不引入新的 MAS owner。

## Source Snapshot

- source SHA: `openai/symphony@58cf97d`
- source SHA: `msitarzewski/agency-agents@783f6a7`
- source links: Symphony README/SPEC/WORKFLOW
  - [Symphony README](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/README.md)
  - [Symphony SPEC](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/SPEC.md)
  - [Symphony WORKFLOW](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/WORKFLOW.md)
  - [Symphony logging guide](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/docs/logging.md)
  - [Symphony token accounting guide](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/docs/token_accounting.md)
  - [Symphony path safety](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/lib/symphony_elixir/path_safety.ex)
  - [Symphony orchestrator](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/lib/symphony_elixir/orchestrator.ex)
  - [Symphony status dashboard](https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/lib/symphony_elixir/status_dashboard.ex)
- source links: Agency README/NEXUS strategy/handoff templates
  - [Agency README](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/README.md)
  - [NEXUS strategy](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/nexus-strategy.md)
  - [handoff templates](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/coordination/handoff-templates.md)
  - [NEXUS phase 3 build loop](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/playbooks/phase-3-build.md)
  - [NEXUS phase 4 hardening gate](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/playbooks/phase-4-hardening.md)
  - [NEXUS phase 6 operate loop](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/playbooks/phase-6-operate.md)
  - [Evidence Collector](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/testing/testing-evidence-collector.md)
  - [Reality Checker](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/testing/testing-reality-checker.md)
  - [Experiment Tracker](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/project-management/project-management-experiment-tracker.md)
  - [Agentic Identity Trust](https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/specialized/agentic-identity-trust.md)

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
| Symphony logging and token-accounting guides | `adopt_contract` | MAS runtime observability should use stable event keys, `session_id` / `active_run_id` identity, absolute token totals, context-window separation, and rate-limit projection. | Token/runtime metrics remain telemetry, not quality or publication authority. |
| Symphony dashboard snapshots and status API presenter | `adopt_template` | Use snapshot-style evidence for operator projections and regression tests around visible runtime state. | Dashboard/API surfaces stay read-only projection. |
| Symphony workspace lifecycle hooks and path safety | `adopt_contract` | Future hosted/external workers need canonical path boundary checks, symlink-aware containment, and explicit cleanup evidence before teardown. | Do not import PR-closing or Linear-specific teardown automation. |
| Symphony trust boundary, secret handling, and hook safety | `adopt_contract` | Future hosted/external workers must declare trust posture, approval/sandbox posture, credential scope, secret redaction, hook timeout, and fail-closed authorization before any study write. | Do not treat workspace isolation alone as sufficient safety, and do not log credentials or grant broad external tracker/tool access by default. |
| NEXUS Dev-QA loop and phase hardening gate | `adopt_contract` | Convert to MAS bounded medical repair/review loops: `PASS` / `FAIL` / `NEEDS_REVIEW`, retry budget, escalation, and AI reviewer-backed publication eval. | Do not import non-medical production-readiness labels as paper quality authority. |
| NEXUS Experiment Tracker statistical discipline | `adopt_template` | Map hypothesis, data quality, sample size/power/precision, endpoint, subgroup, and early-stop discipline into analysis-campaign planning. | Product A/B testing metrics are not imported into medical evidence decisions. |
| Agentic identity/trust proof model | `watch_only` | Useful future reference for cross-runtime delegation, identity proof, trust decay, and tamper-evident audit records; current MAS can still borrow the rule that authorization must be evidence-backed and fail-closed. | Current MAS uses controller authorization and durable records; no cryptographic identity layer is introduced in this intake. |

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
- `watch_only`: agentic identity/trust, cryptographic delegation, cross-framework identity translation, trust score service, and tamper-evident audit bundles are valid future concerns for external hosted workers, but this round keeps them outside MAS runtime implementation until a concrete cross-runtime authorization gap appears.
- `reject`: broad NEXUS phase taxonomy, marketing/product/sales launch playbooks, visual website screenshot QA defaults, product A/B testing terminology, and generic role catalogs are no longer MAS-actionable after mapping their reusable structure into medical route gates, evidence refs, runtime telemetry, and bounded repair loops.
- `adopt_contract`: Symphony trust boundary / secret handling / hook safety is MAS-actionable for future hosted workers because it constrains what must be true before an external process can write. The landing is a safety preflight contract, not a new sandbox engine or identity service.

## Continued Learning Saturation Protocol

“一直学到没有可以学的为止”在 `MAS` 中定义为 MAS-actionable saturation，而不是逐字复制外部项目。

每一轮继续学习必须满足以下步骤：

1. 固定 source SHA，并记录新增 source file coverage。
2. 将每条 lesson 分类为 `adopt_contract`、`adopt_template`、`watch_only` 或 `reject`。
3. 只有能改变 `controller_charter`、`runtime`、`eval_hygiene`、operator projection、agent-entry contract 或 meta tests 的 lesson 才能进入 landing lane。
4. 已经落成同等 MAS contract 的 lesson 标记为 `saturated_by_existing_contract`，不得反复新增同义文档。
5. 只剩外部 owner、tracker-specific mechanics、generic persona routing、marketing/product lifecycle、non-medical QA label 或重复表述时，当前 source snapshot 视为 `MAS-actionable saturated`。

本轮 deeper audit 后的 saturation record：

| Source area | Coverage | MAS-actionable result | Saturation status |
| --- | --- | --- | --- |
| Symphony README/SPEC/WORKFLOW | orchestrator state, workspace, retry, observability, workpad | already landed in runtime work-unit and control surface docs | `saturated_by_existing_contract` |
| Symphony logging/token accounting | stable lifecycle keys, `session_id`, absolute token total, context-window separation, rate-limit snapshot | land as runtime telemetry contract | `new_contract_landed` |
| Symphony path safety/workspace lifecycle | canonical path, symlink-aware boundary, before/after hooks, cleanup evidence | land as hosted/external worker hygiene rule | `new_contract_landed` |
| Symphony trust boundary/secret handling/hook safety | explicit trust posture, approval/sandbox posture, secret redaction, hook timeouts, scoped external access | land as hosted worker safety preflight | `new_contract_landed` |
| Symphony dashboard/status snapshots/API presenter | read-only snapshot, running/retrying counts, token/rate/workspace projection | land as observability-only regression evidence | `new_template_landed` |
| NEXUS handoff templates | context, acceptance criteria, evidence, owner, next receiver | already landed in structured medical handoff | `saturated_by_existing_contract` |
| NEXUS Dev-QA loop / Reality Checker | bounded attempts, default not-ready posture, evidence required before readiness | land as bounded medical repair and AI reviewer default-needs-review rule | `new_contract_landed` |
| NEXUS Experiment Tracker | hypothesis, data quality, statistical confidence, guardrails | land as analysis-campaign planning discipline, not product A/B testing | `new_template_landed` |
| Agentic identity/trust | identity proof, authorization proof, trust decay, tamper-evident logs | watch for future hosted runtime authorization gap; borrow fail-closed authorization discipline now | `watch_only` |
| Generic persona library and broad phase catalog | role catalog, marketing/sales/product lifecycle, non-medical QA persona labels | no further MAS owner value after extraction | `reject_saturated` |

## MAS Landing Rule

The acceptable landing path is selective learning: adopt contracts that strengthen durable study runtime, publication-quality proof, and handoff surfaces; adopt templates that make operator pickup more structured; watch broad orchestration playbooks until a MAS-specific gap exists; reject any source pattern that moves authority away from MAS study truth, publication judgment, or controller decisions.
