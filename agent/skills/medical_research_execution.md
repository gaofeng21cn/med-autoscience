# Medical Research Execution Skill Policy

Owner: MedAutoScience
Skill role: domain execution policy for Codex stage work executors
Machine boundary: this policy guides executor behavior. It does not own study truth, quality verdicts, source readiness verdicts, memory body acceptance, artifact authority, or submission readiness.

## Execution Scope

Use this skill when Codex is executing MAS stage work in `direction_and_route_selection`, `baseline_and_evidence_setup`, `bounded_analysis_campaign`, `manuscript_authoring`, or `finalize_and_publication_handoff`. The executor may inspect MAS-owned refs, reason over them, run allowlisted MAS tasks, and emit execution receipts, evidence refs, artifact/source refs, route-back reasons, human gate requests, or typed blockers.

The executor must treat all medical research work as claim-boundary work. A cohort change, endpoint change, source substitution, model target change, external validation change, or journal-route change is a route decision, not a local implementation detail.

## Required Inputs

- Study charter, task intake, controller decisions, and active route refs.
- Source readiness refs, source provenance refs, data/cohort/endpoint refs, and source locator metadata.
- Evidence ledger refs, run context refs, runtime event refs, failed-path refs, and reviewer concern refs.
- Publication-route memory refs and memory writeback receipt refs when available.
- Canonical manuscript, claim-evidence, citation, display, artifact rebuild, and package refs when the stage touches delivery.
- Journal-family quality pack refs when the stage touches writing, review, finalization, response, or presentation: `journal_response_pack`, `manuscript_argument_pack`, `statistical_reporting_pack`, `data_availability_fair_pack`, `citation_integrity_pack`, `figure_evidence_contract_pack`, `paper_reader_grounding_pack`, and `paper_presentation_pack`.

## Allowed Work

- Interpret medical and statistical meaning across current refs.
- Produce current result refs, evidence refs, canonical manuscript refs, artifact rebuild refs, and owner execution receipts.
- Classify outcomes as completed evidence, no-op with currentness proof, route-back, typed blocker, or human gate request.
- Use OPL generated surfaces only as locator, status, and allowlisted dispatch surfaces.
- Use MAS native helpers only when their outputs remain refs, receipts, progress deltas, or typed blockers.
- Use Co-Scientist-style affordances only when the current owner action, owner route, route-back, typed blocker, reviewer gate, publication gate, human gate, or stop-loss decision explicitly requests a ref family, briefing, repair question, or arbitration need.

## Professional Dependencies And External Skills

- Codex chooses tools, iteration, substitutions, and safe parallelism. A
  professional policy may require order where reversing it would invalidate a
  claim, lose provenance, bypass authority, reuse stale review, or perform an
  irreversible action.
- Claim-bearing analysis requires an accepted study/source boundary and a stated
  question, estimand or target quantity, and stop condition. Feasibility
  exploration may occur earlier and may route the study back for revision.
- Record failed or negative paths before retrying. Drafting may proceed alongside
  analysis, but substantive claims must remain bound to accepted evidence.
- Work that changes canonical deliverables follows authority -> canonical-source
  mutation -> rebuild -> fresh proof or risk-matched independent review ->
  handoff. External submission remains human-authorized.
- Use installed `mas-scholar-skills` routes for ordinary professional work.
  Acquire a new external Skill only for a named or demonstrated coverage gap.
  Inspect its identity, provenance, permissions, data/credential scope, and
  compatibility before sync. Search and comparison order is not prescribed, and
  an already inspected compatible installation may be reused directly.
- External and specialist outputs are refs-only candidates until consumed by the
  MAS owner path; they never become source, quality, artifact, or submission
  authority by installation or execution alone.

## Artifact Iteration Efficiency

- Apply `contracts/artifact_iteration_efficiency_policy.json` whenever work
  builds, renders, reviews, archives, or projects a manuscript package. Use a
  descriptor-declared component graph when available. For legacy descriptors,
  the MAS executor materializes a bounded impact plan from exact inputs and the
  canonical role policy; a host does not infer dependencies, and missing graph
  metadata does not block hosted-action liveness.
- Use content-addressed component reuse only when input, builder-code, toolchain,
  configuration, and output hashes all match. Whole-descriptor identity is
  provenance, not a component cache key, and mtime alone is never currentness
  proof. An unchanged run starts no heavyweight renderer and rewrites no
  projection.
- Keep iterative preview separate from candidate freeze. Preview only affected
  components, changed pages, and declared high-risk members. Layout-only and
  manuscript-only changes cannot trigger unrelated analysis, source, display,
  workbook, or supplement work.
- After targeted checks pass, freeze one candidate identity and perform one
  complete export, complete render inspection, exact-byte inventory, archive,
  and affected-lane review wave. Independent lanes may run in parallel; aggregate
  their findings before repair. Projection happens only after a current MAS owner
  result and stays outside candidate freeze.
- Reuse a v2 review receipt only through MAS-owned
  `reused_unchanged_scope` currentness with identical scope policy and rubric plus
  complete origin provenance. Dispatch all changed lanes together; never replay
  unchanged scientific lanes merely because delivery layout, archive, locator,
  or package-governance bytes changed.
- Record phase, change class, elapsed time, cache hits, rebuilt/reused outputs,
  external invocation count, bytes hashed/copied, and failure reason. Allow at
  most one same-identity retry for a recorded failed action; then change the
  relevant identity or route to the owner instead of silently looping.

## Medical Judgment Requirements

- Keep claims tied to evidence, source, and citation refs.
- Preserve weak, negative, failed, or uncertain findings as route evidence.
- Emit failed-path / decision-trace refs for negative results, failed attempts, route switches, claim narrowing, methodology route-back, and stop-loss outcomes. The executor may summarize the lesson, but the durable handoff must stay refs-only and must not copy evidence, memory, artifact, or paper body.
- Do not run advisory exploration, next-delta tournaments, strategy retrospectives, memory scans, or knowledge prefetch by default. The ordinary path is current owner delta, concrete evidence/paper/reviewer/gate delta, receipt or typed blocker, and the next current owner delta.
- When an explicit current-owner need invokes a Co-Scientist-style affordance, bind it to the current work unit identity, target surface, requested ref family or question, owner policy, bounded output shape, and `no_new_default_next_action`. Secondary caps apply only after that JIT invocation: at most three micro-candidates, one next-delta tournament, three reviewer repair hints, and one reusable refs-only lesson.
- Treat opportunistic knowledge prefetch as a JIT, non-blocking ref collection affordance for the declared next owner only when explicitly requested. If it would delay dispatch, skip it and preserve the owner delta; if a route-required ref is missing, emit the route's normal typed blocker.
- Name the clinical interpretation and reviewer risk of each material result.
- Prefer claim narrowing, stop-loss, or route-back over unsupported positive-result harvesting.
- Record when source provenance, artifact rebuild proof, or reviewer currentness is missing.
- Treat nature-skills-derived journal-family packs as MAS-native quality floors and reviewer rubrics, not as vendor dependency, runtime dependency, default skill source, publication readiness authority, or template authority.
- Route journal-family pack work through MAS ScholarSkills' existing
  professional skills instead of expanding MAS stage policy into parallel
  checklists. The pack-to-skill foldback is owned by
  `mas-scholar-skills/references/professional-quality-ref-templates.md#mas-journal-family-pack-foldback`.
- For registry, phenotype-atlas, or treatment-gap signals, route refs-only pack
  production and integrated professional judgment through MAS ScholarSkills'
  `medical-statistical-review`, then consume the canonical
  `ehr_registry_signal_validity_ref` in its `registry_signal_validity_pack`.
  `medical-registry-atlas-story-architect` may contribute optional framing refs
  but cannot produce or own the pack alone. Keep the professional checklist in
  ScholarSkills; MAS only freezes signal identity, consumes refs, applies claim
  boundaries, and emits the owner outcome.
- MAS execution only requires consumed pack refs, candidate output refs,
  route-back or owner-gate handoff refs, and the owner receipt / typed blocker /
  reviewer record / human gate that consumes them. Reviewer-response,
  manuscript-argument, statistical-reporting, Data Availability, citation,
  figure/table, reader-grounding, and presentation details stay in the
  corresponding `medical-*` professional skill.

## Forbidden Work

- Do not write MAS study truth, publication eval verdicts, source body, memory body, artifact authority, current package, or submission readiness from this skill.
- Do not use script success, file presence, queue completion, generated interface readiness, provider completion, or test pass as medical readiness.
- Do not use publication-route memory as evidence or as a quality verdict.
- Do not self-review the executor's own output to close an AI-first quality gate.
- Do not let checklist or template completion replace AI judgment about medical support, reader risk, citation strength, figure integrity, or journal fit.
- Do not let JIT-invoked next-delta tournaments, micro-candidates, critique hints, memory lessons, strategy retrospectives, or prefetch status admit a route, close a quality gate, promote a stage, authorize publication/submission readiness, generate a default next owner, or mutate study truth, artifacts, memory, or current package state.

## Required Output Shape

Every execution must return one of these semantic outcomes:

- owner receipt with input refs, output refs, changed refs, currentness proof, and next owner.
- typed blocker with blocker type, missing refs, route-back owner, and required repair.
- route-back request with owner, work unit, reason, decision-trace refs, failed-path refs, and consumed failed-path refs when applicable.
- human gate request with decision needed, scope impact, and refs.
- no-op with currentness proof explaining why no mutation was needed.
- `completed_with_quality_debt` with a consumable delta and explicit debt refs;
  debt blocks quality, publication, export, and submission-ready claims, not the
  stage transition.

When journal-family packs are in scope, the output must name consumed pack refs,
the ScholarSkills specialist route, produced candidate refs or route-back refs,
and the MAS owner receipt, reviewer record, typed blocker, or human gate that
consumes them. The output should not restate the specialist checklist; it should
link to the foldback route and preserve the authority boundary.

When a registry signal is in scope, the output must name the consumed
`registry_signal_validity_pack`, its `ehr_registry_signal_validity_ref`, its
frozen `clinical-gap` or `data-audit` identity, the executed validation and
sensitivity refs, explicit waiver ref, or claim-downgrade ref that governs
interpretation, and the MAS owner or reviewer outcome that consumes those refs.

When no consumable scientific delta exists, emit a no-output/failure diagnostic,
preserve failed-path lineage, and let Codex select advance, repeat, reverse, or
route-back. Use a typed blocker only for wrong-target identity/currentness,
authority, safety, credential, irreversible-action, unavailable-executor, or
explicit human-decision boundaries. Diagnostics never replace medical authority.
