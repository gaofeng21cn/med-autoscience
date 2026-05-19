# Baseline And Evidence Setup Prompt

Owner: MedAutoScience
Stage id: baseline_and_evidence_setup
Domain routes: baseline, experiment
Machine boundary: prompt source for reproducible baseline and primary evidence setup. Source body, study truth, and artifact authority remain MAS-owned durable surfaces.

## Objective

Establish whether the selected study line has reproducible source, cohort, endpoint, comparator, and baseline support. The executor should verify the active study charter, data contract, source readiness refs, baseline lineage, statistical plan, and controller decision refs before running or accepting evidence setup.

## Required Reasoning

- Confirm the source can support the active claim boundary without importing hidden body content into OPL projection surfaces.
- Record cohort, endpoint, comparator, measurement window, missingness, inclusion/exclusion, and reproducibility assumptions.
- Produce baseline or primary-result refs with run context and enough provenance for reviewer/auditor replay.
- Distinguish source readiness, source body, and source provenance. OPL may index refs; MAS owns readiness verdict and body interpretation.
- Route to bounded analysis only when baseline evidence can support the current claim or a named bounded repair.

## Forbidden Moves

- Do not treat file presence, script completion, or queue completion as source readiness verdict.
- Do not replace canonical data/source refs with prose summaries.
- Do not advance when baseline support changes the clinical claim boundary without a decision or human gate.

## Closeout

Return baseline artifact refs, source readiness verdict refs or typed blockers, run context, unresolved evidence gaps, and owner receipt. If the source is unavailable or provenance is incomplete, close with a source-readiness blocker and next owner rather than a ready verdict.
