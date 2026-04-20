<!-- MED_AUTOSCIENCE_APPEND_BLOCK:review -->

## medical manuscript review gate

Audit the draft as a medical paper, not as an AI/ML benchmark report.

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

Default review checkpoints:

- Methods mandatory items are explicit: center, time window, study design, ethics, inclusion / exclusion criteria, endpoint definition, variable definitions, missing-data strategy, modeling workflow, software package and version
- any method-facing label such as `knowledge-guided`, `causal`, `mechanistic`, or `calibration-first` has a manuscript-verifiable operational definition
- Results are organized by research question and clinical answer, not figure-by-figure
- internal model names, engineering labels, and runtime-only terminology are removed from manuscript-facing text
- endpoint provenance caveats are surfaced when they materially affect interpretation
- manuscript-safe reproducibility supplement exists when the paper is prediction- or model-heavy

Review should update the medical owner surfaces, not only prose comments.

For every major concern, record in `paper/review/review.md`, `paper/review/revision_log.md`, or the equivalent `review_ledger`:

- affected claim or section
- evidence path or missing evidence path
- required disposition: `accept_as_is`, `downgrade_claim`, `route_back_write`, `route_back_analysis`, or `route_back_decision`
- which readiness label is blocked: `draft-ready`, `paper-ready`, or `submission-ready`

Use the medical review pass to enforce:

- claim wording drops immediately when evidence weakens or caveats widen; downgrade the claim wording in the draft and ledger in the same pass
- route-back goes to the narrowest earlier stage that can close the gap while keeping the locked study direction honest
- reviewer concern ordering follows `study_charter`, the current route recommendation, and the current evidence package
