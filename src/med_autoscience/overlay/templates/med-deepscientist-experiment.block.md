<!-- MED_AUTOSCIENCE_APPEND_BLOCK:experiment -->

## medical experiment gate

Judge main experiments by the strength of the eventual medical paper package, not only by one engineering metric.

{{MED_AUTOSCIENCE_ROUTE_BIAS}}

{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

Hard startup-boundary rules for this stage:

- If `startup_contract.startup_boundary_gate.allow_compute_stage` is not `true`, do not launch experiments, do not queue training, and do not open analysis loops that depend on new compute.
- Read `startup_contract.required_first_anchor`; route immediately to that anchor instead of continuing compute-heavy work, and use `decision` only after the startup blockers are cleared in durable artifacts.
- If `startup_contract.baseline_execution_policy == "skip_unless_blocking"`, treat any experiment request as blocked unless a named framing or evidence blocker truly requires one bounded recovery step.
- Do not execute legacy implementation code from `refs/` or historical directories unless `startup_contract.legacy_code_execution_allowed` is `true`.

For medical quests, the default downstream evidence package should explicitly consider:

- calibration and threshold behavior
- clinical utility / net-benefit / workflow impact when relevant
- subgroup heterogeneity and clinically legible risk-group contrasts
- explainability or case-level attribution surfaces when relevant
- external validation, public-data extension, or mechanistic sidecar opportunities when feasible

If labels such as `knowledge-guided`, `causal`, or `mechanistic` are used, leave an operational definition in durable artifacts.

If the current result is weak and the remaining path would mostly package weakness, do one bounded diagnostic step at most, then route through `decision` rather than looping on tiny gains.
