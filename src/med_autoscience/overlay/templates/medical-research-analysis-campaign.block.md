<!-- MED_AUTOSCIENCE_APPEND_BLOCK:analysis-campaign -->

## medical analysis-campaign gate

Treat follow-up campaigns as publication-strength evidence building, not as endless metric polishing.

{{MED_AUTOSCIENCE_ROUTE_BIAS}}

{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

Hard startup-boundary rules for this stage:

- If `startup_contract.startup_boundary_gate.allow_compute_stage` is not `true`, do not start follow-up campaigns, do not expand ablation grids, and do not burn compute on robustness passes.
- Read `startup_contract.required_first_anchor`; route immediately to that anchor instead of continuing compute-heavy work, and return through `decision` only after the startup blockers are cleared in durable artifacts.
- If `startup_contract.baseline_execution_policy == "skip_unless_blocking"`, analysis-campaign work is blocked unless a named framing or evidence blocker truly requires one bounded diagnostic recovery step.
- Do not execute legacy implementation code from `refs/` or historical directories unless `startup_contract.legacy_code_execution_allowed` is `true`.

Stage contract for this route:

- Purpose: close a named publication-relevant evidence gap with bounded follow-up work.
- Minimum credible work: record the target gap and campaign scope, finish at least one publication-relevant slice, and write the result back into the named evidence surface.
- Stop when: the named gap is closed, or the budget boundary / major boundary signal is reached and durably recorded.
- Route back: when the remaining question becomes route-level rather than compute-level, record the gap and route through `decision`; when the evidence is ready for manuscript consolidation, route to `write`.

Prioritize campaign slices that materially strengthen a medical manuscript, such as:

- calibration / threshold / utility analysis
- subgroup and heterogeneity analysis
- explainability, error taxonomy, or case-review work
- external validation or public-data-supported extension
- mechanistic / contextual sidecar support when the primary clinical line is already credible

Down-rank campaigns whose only value is a tiny discrimination bump with little clinical meaning.
