# Bounded Analysis Campaign Prompt

Owner: MedAutoScience
Stage id: bounded_analysis_campaign
Next stage: manuscript_authoring
Machine boundary: this prompt directs bounded scientific analysis. Evidence
ledgers, study truth, runtime events, and owner receipts remain MAS-owned.

## Objective

Close the evidence gaps that matter to the active claim, reviewer concern, or
methodology route. Return reviewable evidence and its claim impact without
expanding the accepted study boundary.

## Good Work

- Before claim-bearing analysis, state the question, estimand or target quantity,
  accepted cohort/source/endpoint/comparator boundary, expected evidence gain,
  and stop or route-back condition.
- Choose the statistical, data-governance, literature, table, and figure methods
  that best answer the question. `medical_research_execution.md` owns specialist
  routing; the executor may iterate or parallelize where dependencies allow.
- Bind accepted results to current source, run, code/provenance, evidence, and
  claim-impact refs. Classify impact as confirm, weaken, refute, narrow,
  downgrade, stop, or route-back.
- Record weak, negative, failed, stale, or duplicate paths before retrying or
  selecting a replacement analysis, so unsuccessful routes remain reproducible
  evidence rather than disappearing from the campaign.
- Methods drafting and evidence interpretation may proceed iteratively. No
  substantive claim may outrun its accepted evidence refs.

## Boundaries

Do not add a primary claim, cohort, endpoint, comparator, validation target, or
methodology route without decision or human authority. Compute completion,
specialist candidates, prose, package freshness, and tests cannot close source,
methodology, evidence, or quality gates.

## Handoff

Return `bounded_analysis_evidence_ready` with result, evidence-ledger,
claim-impact, failed-path, specialist-candidate, and next-owner refs. A usable
analysis delta may advance as `completed_with_quality_debt`; record the debt and
block promotion or ready claims. Route back to baseline for source/provenance
repair, to direction for claim or method changes, or return a typed blocker or
human gate when no consumable delta can be produced safely.
