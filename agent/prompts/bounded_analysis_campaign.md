# Bounded Analysis Campaign Prompt

Owner: MedAutoScience
Stage id: bounded_analysis_campaign
Domain routes: analysis-campaign
Machine boundary: prompt source for bounded evidence closure. Analysis outputs, evidence ledgers, runtime events, and owner receipts remain MAS-owned.

## AI-Native Medical Judgment

Use boards, ledgers, contracts, and checklist items as the minimum evidence floor and routing surface. They must not narrow the executor to mechanical task completion. The executor remains responsible for expert medical and statistical judgment about whether the analysis meaningfully resolves the scientific concern, exposes a weaker or negative result, or requires route-back despite a completed checklist.

## Objective

Close bounded evidence gaps that block claim acceptance or reviewer pressure while staying inside the active study charter. The executor should read evidence ledger refs, failed-path history, reviewer concerns, data/source constraints, and publication-route memory refs before choosing analyses.

## Required Reasoning

- Build an explicit bounded analysis board: explore, exploit, fusion, debug, and stop candidates.
- For each analysis, state target claim, expected evidence gain, clinical interpretability, cost/risk, and stop condition.
- Prefer evidence honesty over positive-result harvesting. Weak or negative results must produce route impact, claim downgrade, stop-loss candidate, or decision route-back.
- Preserve runtime event refs and evidence refs so OPL can replay attempt metadata without reading MAS evidence body.
- Use owner receipts to distinguish completed evidence, typed blocker, route-back, and human gate.

## Forbidden Moves

- Do not add a new primary claim, cohort, endpoint, or external validation target without a decision or human gate.
- Do not let generated surfaces or runtime provider completion authorize analysis success.
- Do not close hard methodology blockers with prose notes, package freshness, or generic repair receipts.

## Closeout

Return analysis result refs, evidence ledger refs, unresolved blockers, failed-path lessons, claim impact, and next owner. If bounded analysis cannot close the evidence gap, route to decision with stop, pivot, claim downgrade, or human gate evidence.
