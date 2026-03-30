<!-- MED_AUTOSCIENCE_APPEND_BLOCK:review -->

## medical manuscript review gate

Audit the draft as a medical paper, not as an AI/ML benchmark report.

Default review checkpoints:

- Methods mandatory items are explicit: center, time window, study design, ethics, inclusion / exclusion criteria, endpoint definition, variable definitions, missing-data strategy, modeling workflow, software package and version
- any method-facing label such as `knowledge-guided`, `causal`, `mechanistic`, or `calibration-first` has a manuscript-verifiable operational definition
- Results are organized by research question and clinical answer, not figure-by-figure
- internal model names, engineering labels, and runtime-only terminology are removed from manuscript-facing text
- endpoint provenance caveats are surfaced when they materially affect interpretation
- manuscript-safe reproducibility supplement exists when the paper is prediction- or model-heavy
