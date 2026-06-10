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

## Medical Judgment Requirements

- Keep claims tied to evidence, source, and citation refs.
- Preserve weak, negative, failed, or uncertain findings as route evidence.
- Emit failed-path / decision-trace refs for negative results, failed attempts, route switches, claim narrowing, methodology route-back, and stop-loss outcomes. The executor may summarize the lesson, but the durable handoff must stay refs-only and must not copy evidence, memory, artifact, or paper body.
- Do not run advisory exploration, next-delta tournaments, meta-review, memory scans, or knowledge prefetch by default. The ordinary path is current owner delta, concrete evidence/paper/reviewer/gate delta, receipt or typed blocker, and the next current owner delta.
- When an explicit current-owner need invokes a Co-Scientist-style affordance, bind it to the current work unit identity, target surface, requested ref family or question, owner policy, bounded output shape, and `no_new_default_next_action`. Secondary caps apply only after that JIT invocation: at most three micro-candidates, one next-delta tournament, three reviewer repair hints, and one reusable refs-only lesson.
- Treat opportunistic knowledge prefetch as a JIT, non-blocking ref collection affordance for the declared next owner only when explicitly requested. If it would delay dispatch, skip it and preserve the owner delta; if a route-required ref is missing, emit the route's normal typed blocker.
- Name the clinical interpretation and reviewer risk of each material result.
- Prefer claim narrowing, stop-loss, or route-back over unsupported positive-result harvesting.
- Record when source provenance, artifact rebuild proof, or reviewer currentness is missing.
- Treat nature-skills-derived journal-family packs as MAS-native quality floors and reviewer rubrics, not as vendor dependency, runtime dependency, default skill source, publication readiness authority, or template authority.
- For reviewer response work, require stable comment ids, response tracker refs, action mapping refs, difficult-case routing refs, appeal-like routing refs, author-input flags, response readiness refs, output refs, typed blocker or owner receipt. Difficult-case coverage includes impossible or out-of-scope experiments, reviewer factual errors, conflicting reviewer requests, major statistical critiques, ethics/compliance/data-integrity critiques, transfer-after-review, and rejection challenge / appeal-like cases.
- For manuscript argument work, require paper type logic, one-sentence argument, section job map, claim-evidence boundary refs, paragraph flow review, hedging/overclaim review, output refs, typed blocker or reviewer record.
- For statistical reporting work, require sample size and denominator refs, effect size / confidence interval / p value refs, missingness and exclusion refs, model performance / calibration / external validation refs, multiplicity / sensitivity / subgroup / assumption refs, software and reproducibility refs, output refs, typed blocker or owner receipt.
- For Data Availability work, require dataset-location refs, restricted-access reason and access route refs, repository or persistent identifier refs, dataset citation refs, public metadata for restricted data when possible, FAIR metadata refs, licence / rights / provenance / README refs, Data Availability output refs, typed blocker or owner receipt.
- For citation work, require strict journal-family scope refs when Nature / CNS support is requested, claim-segment ids, English concept search claims, candidate citation refs, citation support grades, metadata-only support flags, publisher or abstract verification refs, reference-manager export notes for the selected ENW / RIS / Zotero RDF output, output refs, typed blocker or owner receipt.
- For figure/table work, require core conclusion, figure archetype, selected backend, final size, panel map, evidence hierarchy, panel role, source-data refs, statistics refs, export contract refs, QA-risk refs, output refs, typed blocker or owner receipt. Backend/export/QA coverage must make renderer choice, source-data linkage, statistical annotation, image-integrity risk, export format, and reviewer-risk checks explicit.
- For source-grounded reader work, require full-paper source maps, stable page/block anchors, caption/table/figure anchors, figure-near-claim refs, source-grounded follow-up refs, output refs, typed blocker or owner receipt.
- For presentation work, require evidence spine refs, selected figure asset refs, asset-manifest refs, crop QA refs, PPTX package/reopen QA refs, slide overflow/readability QA refs, speaker-notes context, output refs, typed blocker or owner receipt.

## Forbidden Work

- Do not write MAS study truth, publication eval verdicts, source body, memory body, artifact authority, current package, or submission readiness from this skill.
- Do not use script success, file presence, queue completion, generated interface readiness, provider completion, or test pass as medical readiness.
- Do not use publication-route memory as evidence or as a quality verdict.
- Do not self-review the executor's own output to close an AI-first quality gate.
- Do not let checklist or template completion replace AI judgment about medical support, reader risk, citation strength, figure integrity, or journal fit.
- Do not let JIT-invoked next-delta tournaments, micro-candidates, critique hints, memory lessons, meta-review summaries, or prefetch status admit a route, close a quality gate, promote a stage, authorize publication/submission readiness, generate a default next owner, or mutate study truth, artifacts, memory, or current package state.

## Required Output Shape

Every execution must return one of these semantic outcomes:

- owner receipt with input refs, output refs, changed refs, currentness proof, and next owner.
- typed blocker with blocker type, missing refs, route-back owner, and required repair.
- route-back request with owner, work unit, reason, decision-trace refs, failed-path refs, and consumed failed-path refs when applicable.
- human gate request with decision needed, scope impact, and refs.
- no-op with currentness proof explaining why no mutation was needed.

When journal-family packs are in scope, the output must name the consumed pack refs and either the produced output refs or the typed blockers for missing response edge-case routing, manuscript argument, statistical reporting, Data Availability restricted-access / FAIR metadata, strict citation support / export, figure backend / source-data / statistics / export QA, full-paper reader source-map / block-anchor grounding, or presentation PPTX QA / asset-manifest evidence.

Ambiguous completion is invalid because it lets runtime progress replace medical authority.
