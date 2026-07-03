---
name: journal-resolution
description: Use when a submission target does not already map to a supported exporter profile and the journal requirements must be resolved from official sources.
---

# Journal Resolution

Use this stage prompt when MAS routes an unresolved journal target to
`journal-resolution`.

## MAS Stage Projection Boundary

This file is the MAS-owned submission-stage/runtime projection for Codex
discovery, not the source of truth for professional submission-prep skill
content. It resolves official venue requirements into MAS-owned durable refs.
Use `medical-submission-prep` for professional submission package patterns only
after the target requirements are resolved.

{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}

{{MED_AUTOSCIENCE_CONTROLLER_FIRST}}

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

## Stage Contract

Before resolving a target, confirm:

- the primary target journal is already selected by MAS route/decision refs;
- no supported exporter profile already satisfies the target;
- official sources are available for author guidelines, templates, reference
  style, reporting forms, and package requirements;
- the next owner gate that will consume the resolved target.

## Professional Skill Routes

Route professional method work to MAS Scholar Skills:

- Use `medical-submission-prep` for package-pattern candidates, checklist
  candidates, cover-letter/highlight/response-material candidates, and unresolved
  submission-package route-backs.
- Use `medical-research-lit` when official target rules affect citation/export
  refs.
- Use `medical-table-design`, `medical-figure-design`,
  `medical-statistical-review`, and `medical-data-governance` when journal
  requirements bind table, figure, numeric trace, reporting guideline, Data
  Availability, FAIR, privacy/access, or source-readiness refs.

Specialist outputs are candidates only. MAS remains owner for target resolution,
package authority, submission readiness, human gates, and current package.

## Allowed Sources

Use only official journal or publisher sources: author guidelines, template
pages, Word/LaTeX templates, reference-style instructions, reporting forms, and
submission checklists. If official requirements conflict, record the conflict as
a blocker instead of guessing.

## Required Outputs

- `paper/submission_target_resolution.md`
- `paper/submission_targets.resolved.json`

The structured result must state journal name, official source refs, supported
or missing exporter profile, citation style, template source, package
requirements, story surface, unresolved blockers, and next owner gate.

## Forbidden Shortcuts

- Do not use this stage to select a journal.
- Do not infer journal requirements from memory or third-party notes.
- Do not export or mutate a venue-specific package from unresolved requirements.
- Do not treat resolved target refs as scientific readiness, publication
  quality, package authority, or submission authorization.

## Closeout Shape

Return one of:

- `submission_target_resolved_ref`;
- `unsupported_exporter_profile_blocker_ref`;
- `official_requirement_conflict_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.
