# Bounded Analysis Campaign Prompt

Owner: MedAutoScience
Stage id: bounded_analysis_campaign
Stage kind: creation
Domain routes: analysis-campaign
Next stage: manuscript_authoring
Machine boundary: prompt source for bounded evidence closure. Analysis outputs,
evidence ledgers, runtime events, and owner receipts remain MAS-owned.

## Stage Objective

Close only the evidence gaps that block the active claim, reviewer response, or
methodology route. The stage must return evidence impact or a route-back; it
must not expand the study boundary or turn completed compute into scientific
success.

## Inputs

- Baseline/evidence receipt from `baseline_and_evidence_setup`.
- Current study charter, cohort, endpoint, comparator, source refs, and
  controller decisions.
- Evidence ledger, claim-evidence map, failed-path refs, runtime event refs,
  reviewer concerns, and analysis queue/campaign refs when present.

## Specialist Skill Routes

Use external MAS Scholar Skills for professional method detail; keep their
outputs as refs-only candidates until MAS owner gate accepts them:

- `medical-statistical-review`: estimand, model/test fit, sensitivity,
  multiplicity, calibration, validation, and statistical reporting candidates.
- `medical-data-governance`: cohort/source lineage, derived-variable,
  missingness, privacy/access, version-impact, and source-readiness candidates.
- `medical-table-design`: table-ready result, Table 1, model-performance, and
  reporting-table candidates.
- `medical-figure-design`: display-to-claim, figure intent, and visual evidence
  candidates.
- `medical-research-lit`: literature or citation refs that change the evidence
  boundary.

## MAS Stage Responsibilities

- State the bounded route question and stop condition before work starts.
- Tie every candidate to the active claim, reviewer concern, source refs, and
  expected evidence gain.
- Record result impact as confirm, weaken, refute, narrow, downgrade, stop, or
  route-back.
- Preserve weak, negative, failed, stale, and duplicate paths as decision-trace
  refs instead of rerunning them silently.
- Keep OPL/provider output, specialist output, and local scripts as evidence
  candidates, not MAS truth.

## Forbidden Shortcuts

- Do not add a new primary claim, cohort, endpoint, comparator, validation
  target, or methodology route without decision or human-gate authority.
- Do not close methodology/source/evidence blockers with prose, queue state,
  package freshness, script success, or specialist-skill output alone.
- Do not edit paper body, current package, publication eval, controller
  decisions, owner receipts, typed blockers, human gates, runtime queues, or
  provider attempts from this stage prompt.

## Receipt And Route-Back

Return analysis result refs, evidence ledger refs, claim-impact refs,
failed-path/decision-trace refs, specialist candidate refs consumed or requested,
and next owner. Valid outcomes are:

- `bounded_analysis_evidence_ready` with current source/run/evidence refs.
- route-back to `decision` for stop, pivot, claim downgrade, scope expansion, or
  methodology reframe.
- route-back to `baseline_and_evidence_setup` for source/provenance gaps.
- route-back to `manuscript_authoring` when evidence is sufficient but prose or
  display explanation must be repaired.
- stable typed blocker or human gate with exact missing refs, owner, validation
  condition, and resume surface.

## Done Criteria

- Every accepted result has current source, run, evidence, and claim-impact refs.
- Specialist method outputs are cited as candidates, not authority.
- Next stage is `manuscript_authoring`, or the receipt contains an exact
  route-back/blocker/human gate.
