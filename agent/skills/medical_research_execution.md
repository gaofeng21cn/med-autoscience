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

## Medical Judgment Requirements

- Keep claims tied to evidence, source, and citation refs.
- Preserve weak, negative, failed, or uncertain findings as route evidence.
- Name the clinical interpretation and reviewer risk of each material result.
- Prefer claim narrowing, stop-loss, or route-back over unsupported positive-result harvesting.
- Record when source provenance, artifact rebuild proof, or reviewer currentness is missing.
- Treat nature-skills-derived journal-family packs as executable quality floors and reviewer rubrics, not as publication authority or template instructions.
- For reviewer response work, require stable comment ids, response tracker refs, action mapping refs, author-input flags, response readiness refs, output refs, typed blocker or owner receipt.
- For manuscript argument work, require paper type logic, one-sentence argument, section job map, claim-evidence boundary refs, paragraph flow review, hedging/overclaim review, output refs, typed blocker or reviewer record.
- For statistical reporting work, require sample size and denominator refs, effect size / confidence interval / p value refs, missingness and exclusion refs, model performance / calibration / external validation refs, multiplicity / sensitivity / subgroup / assumption refs, software and reproducibility refs, output refs, typed blocker or owner receipt.
- For Data Availability work, require dataset-location refs, restricted-access route refs, repository identifier refs, dataset citation refs, FAIR metadata refs, Data Availability output refs, typed blocker or owner receipt.
- For citation work, require claim-segment ids, candidate citation refs, citation support grades, metadata-only support flags, reference/export notes, output refs, typed blocker or owner receipt.
- For figure/table work, require core-claim mapping, evidence chain, panel role, source-data refs, statistics refs, export contract refs, QA-risk refs, output refs, typed blocker or owner receipt.
- For source-grounded reader or presentation work, require source maps, page/block anchors, figure-near-claim refs, evidence spine refs, selected figure assets, speaker-notes context, output refs, typed blocker or owner receipt.

## Forbidden Work

- Do not write MAS study truth, publication eval verdicts, source body, memory body, artifact authority, current package, or submission readiness from this skill.
- Do not use script success, file presence, queue completion, generated interface readiness, provider completion, or test pass as medical readiness.
- Do not use publication-route memory as evidence or as a quality verdict.
- Do not self-review the executor's own output to close an AI-first quality gate.
- Do not let checklist or template completion replace AI judgment about medical support, reader risk, citation strength, figure integrity, or journal fit.

## Required Output Shape

Every execution must return one of these semantic outcomes:

- owner receipt with input refs, output refs, changed refs, currentness proof, and next owner.
- typed blocker with blocker type, missing refs, route-back owner, and required repair.
- route-back request with owner, work unit, reason, and refs.
- human gate request with decision needed, scope impact, and refs.
- no-op with currentness proof explaining why no mutation was needed.

When journal-family packs are in scope, the output must name the consumed pack refs and either the produced output refs or the typed blockers for missing response, manuscript argument, statistical reporting, Data Availability, citation support, figure source-data/statistics/export QA, reader-grounding, or presentation-grounding evidence.

Ambiguous completion is invalid because it lets runtime progress replace medical authority.
