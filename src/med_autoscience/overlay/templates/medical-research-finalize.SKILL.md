---
name: finalize
description: Use when the quest is ready to consolidate final claims, limitations, recommendations, summary state, and graph exports before stopping or archiving.
---

# Finalize

Use this stage prompt when MAS routes the current work unit to `finalize`.

## MAS Stage Projection Boundary

This file is the MAS-owned finalize/runtime projection for Codex discovery, not
the source of truth for professional submission, writing, review, figure, table,
statistics, literature, or data-governance skill content. It decides whether the
line can close, pause, hand off, or route back; professional methods route to
MAS Scholar Skills and remain refs-only candidates until MAS owner gate accepts
them.

{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

## Stage Contract

Before finalizing, confirm:

- active study/work-unit identity and controller route;
- current claim-evidence ledger, review ledger, publication eval, controller
  decision, artifact rebuild proof, and human gate state;
- canonical manuscript, figure, table, supplement, response, delivery manifest,
  package freshness, and source-readiness refs when present;
- whether the result is stop/archive, continue-later, paper handoff, or
  submission-prep route-back.

## Professional Skill Routes

Route professional detail to MAS Scholar Skills:

- `medical-submission-prep` for package, checklist, cover letter, highlight,
  graphical abstract, response material, and portal handoff candidates.
- `medical-manuscript-review` for final adversarial critique and route-back
  candidates.
- `medical-manuscript-writing` for last-mile candidate prose repair.
- `medical-research-lit` for citation/export and source-support candidates.
- `medical-statistical-review` for final numeric trace and statistical reporting
  candidates.
- `medical-table-design` and `medical-figure-design` for table/figure export,
  display-to-claim, and visual QA candidates.
- `medical-data-governance` for Data Availability, FAIR metadata, access,
  privacy, source-lineage, and source-readiness candidates.

Specialist outputs are candidate refs only. MAS remains owner for final claim
closure, publication handoff, submission readiness, owner receipts, typed
blockers, human gates, current package, and publication readiness.

## MAS Stage Responsibilities

- Keep closure labels scoped: `draft-ready`, `paper-ready`, and
  `submission-ready` require the matching MAS owner evidence.
- Preserve supported, partially supported, unsupported, deferred, weakened, and
  failed-path claims in a final claim or closure surface.
- Name blockers instead of converting incomplete paper/package state into a
  closure label.
- Keep external submission, PI strategy, portal credentials, claim expansion, and
  journal strategy human-gated.
- When a study-backed paper closure already includes
  `paper/submission_minimal/audit/submission_manifest.json`, require the
  workspace `sync-delivery --stage finalize` path or return the named delivery
  sync blocker.

## Forbidden Shortcuts

- Do not finalize from chat memory, package/file presence, provider completion,
  specialist output, or checklist pass alone.
- Do not label a line `submission-ready` without current submission-minimal,
  terminology-redline, independent-review, source, artifact, and package
  authority refs required by MAS.
- Do not write publication eval, controller decisions, owner receipts, typed
  blockers, human gates, current package, runtime queues, or provider attempts
  from this prompt.

## Closeout Shape

Return one of:

- `final_or_pause_ready_summary_ref`;
- `final_claim_ledger_ref`;
- `publication_handoff_candidate_ref`;
- `continue_later_resume_packet_ref`;
- `submission_package_route_back_ref`;
- `missing_study_delivery_wrapper_ref`;
- `final_delivery_sync_failed_ref`;
- `final_delivery_manifest_missing_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.

## Exit Criteria

Exit only when closure/handoff refs are current and auditable, or the receipt
names the exact blocker, route-back owner, required refs, validation method, and
resume surface.
