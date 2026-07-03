---
name: analysis-campaign
description: Use when a MedAutoScience study needs bounded follow-up analysis to close evidence gaps, repair claim-evidence or display-to-claim support, or route a weak result back without expanding the study boundary.
---

# Analysis Campaign

Use this stage prompt when MAS routes the current work unit to
`analysis-campaign`.

## MAS Stage Projection Boundary (not Professional Skill source)

This file is the MAS-owned stage/runtime projection for Codex discovery. It is
not the Professional Skill source for statistical, data-governance, table,
figure, literature, or method playbooks. It decides the bounded route question,
required inputs, allowed output refs, route-back, and owner gate. Route
professional work through `contracts/capability_map.json` to MAS Scholar
Skills; do not duplicate specialist playbooks here.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_ROUTE_BIAS}}

{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

## Stage Contract

Before running or interpreting analysis, confirm:

- active study/work-unit identity and controller authorization;
- locked cohort, endpoint, comparator, time horizon, and claim boundary;
- targeted evidence gap, reviewer concern, or display-to-claim gap;
- source refs, evidence ledger refs, and failed-path refs;
- stop condition and next owner gate.

## Professional Skill Routes

Route professional method work to MAS Scholar Skills:

- `medical-statistical-review` for estimand, model/test, uncertainty,
  sensitivity, multiplicity, calibration, validation, and statistical-reporting
  candidates.
- `medical-data-governance` for source lineage, cleaning/normalization,
  missingness, derived variables, privacy/access, and version-impact candidates.
- `medical-table-design` for table-ready result and reporting-table candidates.
- `medical-figure-design` for display-to-claim and visual-evidence candidates.
- `medical-research-lit` for literature or citation refs that change the
  evidence boundary.

Specialist outputs are candidate refs only. MAS remains owner for evidence
ledger acceptance, analysis campaign closeout, claim downgrade, typed blockers,
human gates, owner receipts, current package, and publication readiness.

## Default Defense

- Do not expand the study charter or launch a new main claim from this prompt.
- Do not rerun consumed failed paths unless the current route explains what
  changed.
- Do not treat provider completion, script success, local plots, specialist
  output, or queue state as MAS evidence acceptance.
- Do not write study truth, paper body, publication eval, controller decisions,
  owner receipts, typed blockers, human gates, runtime queues, provider
  attempts, or current-package authority.

## Closeout Shape

Return one of:

- `bounded_analysis_evidence_ready_ref`;
- `claim_impact_ref`;
- `weak_or_negative_result_route_ref`;
- `failed_path_or_stop_loss_ref`;
- `source_or_methodology_blocker_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.
