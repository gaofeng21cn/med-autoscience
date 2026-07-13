# Baseline And Evidence Setup Prompt

Owner: MedAutoScience
Stage id: baseline_and_evidence_setup
Next stage: bounded_analysis_campaign
Machine boundary: this prompt prepares reproducible source and evidence refs.
Source body, study truth, source-readiness verdicts, and artifact authority remain
MAS-owned.

## Objective

Establish a reproducible baseline, comparator, source/provenance chain, and
primary evidence basis for the selected route. Produce a supportable claim
boundary or an exact source/evidence repair route.

## Good Work

- Resolve cohort, inclusion/exclusion, endpoint, exposure or model target,
  comparator, measurement window, missingness, censoring, and reproducibility
  assumptions to the degree required by the intended claim.
- Bind baseline and primary-result candidates to input versions, run context,
  code/provenance, source readiness, and evidence-ledger refs so another agent can
  replay the basis.
- Keep source body, provenance, locator metadata, and readiness verdict distinct.
- A versioned baseline and accepted source/claim boundary are prerequisites for
  claim-bearing analysis. Exploratory feasibility work may precede or revise them,
  but cannot be promoted as claim-bearing evidence until these prerequisites hold.
- If the evidence changes the scientific question, endpoint, cohort, or intended
  claim, route back to direction instead of silently adopting the change.
- Use `medical_research_execution.md` for professional methods and specialist
  routing. Tool order is flexible inside the above scientific dependencies.

## Boundaries

File presence, script or provider completion, queue state, tests, and specialist
output do not establish source readiness. Do not replace canonical source refs
with prose summaries or advance a changed claim boundary without decision or
human authority.

## Handoff

Return `baseline_evidence_ready` with current baseline, source, comparator,
provenance, run-context, evidence-gap, and claim-impact refs plus the next owner.
A consumable evidence delta may close as `completed_with_quality_debt`; the debt
must block quality, publication, and submission-ready claims. If no consumable
delta exists, return a no-output/failure diagnostic with missing refs and a
route-back recommendation, then allow Codex to continue. Use a typed blocker or
human gate only for a real hard boundary.
