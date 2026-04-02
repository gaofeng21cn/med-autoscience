<!-- MED_AUTOSCIENCE_APPEND_BLOCK:baseline -->

## medical baseline gate

Baseline work for a medical-data quest should preserve a strong paper route, not become an endless reproduction diary.

{{MED_AUTOSCIENCE_ROUTE_BIAS}}

{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}

Hard startup-boundary rules for this stage:

- If `startup_contract.startup_boundary_gate.allow_compute_stage` is not `true`, do not run baseline code, do not start new training, and do not expand comparator work.
- Read `startup_contract.required_first_anchor`; route immediately to that anchor instead of continuing compute-heavy work, and return through `decision` only after the startup blockers are cleared in durable artifacts.
- If `startup_contract.baseline_execution_policy == "skip_unless_blocking"`, baseline may inspect already-produced evidence only when a named decision is blocked by missing or unusable comparator evidence.
- Do not execute legacy implementation code from `refs/` or historical directories unless `startup_contract.legacy_code_execution_allowed` is `true`.

Before declaring a baseline trustworthy, make the medical contract explicit:

- target cohort, endpoint, and time horizon
- whether the baseline supports a clinically interpretable comparison surface
- whether the baseline route leaves room for calibration, utility, subgroup, explainability, or external-validation follow-up
- software package, version, and configuration surface when the baseline may later enter manuscript Methods

If baseline work is consuming effort without improving the eventual clinical paper package, route back through `decision` instead of expanding low-yield comparator work.
