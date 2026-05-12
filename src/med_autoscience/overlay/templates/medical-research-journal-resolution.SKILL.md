---
name: journal-resolution
description: Use when a submission target does not already map to a supported publication profile and the journal requirements must be resolved from official sources.
---

# Journal Resolution

Use this skill to convert an unresolved journal target into a controlled, evidence-backed submission profile.

{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}

{{MED_AUTOSCIENCE_CONTROLLER_FIRST}}

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

## Research Harness clean-room boundary

Research Harness is only a clean-room template lesson for this skill.
It is not a MedAutoScience dependency, runner, database, dashboard, MCP surface, or verdict authority.
Use any RH-derived lesson only to sharpen MAS-owned stage surfaces, blocker wording, and durable artifact expectations.

## Purpose

This skill exists to stop venue-specific drafting from drifting into guesswork.

This is not a venue-selection workflow.
Only use this skill after a primary journal target has already been chosen from an evidence-backed shortlist.

If a target journal is not already represented by a supported `publication_profile`, do not improvise the package format, reference style, section order, or template requirements from memory.

Resolve the journal only from official sources, then write the result back into durable quest files.

## Allowed sources

Use only official journal or publisher sources such as:

- official author guidelines
- official template pages
- official manuscript template pages
- official Word or LaTeX templates
- official reference-style tables
- official submission checklists

If the official requirements are split across multiple official pages, reconcile them explicitly.

## Forbidden behavior

- Do not use this skill to decide which journal should be targeted.
- Do not generate a shortlist from journal homepages alone.
- Do not infer journal requirements from memory.
- Do not treat third-party blog posts or community notes as authoritative.
- Do not export a venue-specific package until the unresolved target has been converted into a structured resolved target.

## Required durable outputs

Leave behind both:

- `paper/submission_target_resolution.md`
- `paper/submission_targets.resolved.json`

`paper/submission_target_resolution.md` should explain:

- which journal target was resolved
- which official sources were used
- what template and reference-style requirements were confirmed
- what remained unclear or blocked

`paper/submission_targets.resolved.json` should contain the structured resolved target that downstream export steps can consume.

At minimum, the resolved target must make explicit:

- `journal_name`
- `publication_profile` when a supported one exists
- `citation_style`
- `template_source`
- `official_guidelines_url`
- `package_required`
- `story_surface`

## Resolution policy

- If the official evidence cleanly maps to an existing supported `publication_profile`, use that profile.
- If no supported profile exists yet, record a blocked resolution result instead of fabricating one.
- If the journal belongs to a known family with shared templates but distinct citation branches, record the family and the citation branch separately.

## Submission-surface blocker semantics

Journal resolution does not judge whether the paper is scientifically ready.
It records venue requirements that downstream writing and finalize stages must enforce as blockers:

- `numeric_trace_blocker`: if official journal instructions require exact cohort counts, trial/model reporting numbers, statistical estimate formats, confidence intervals, p-values, or data-sharing identifiers that the study cannot trace to durable sources, mark the resolved target as blocked for package export.
- `claim_evidence_blocker`: if the venue requires structured statements, highlights, significance summaries, graphical abstracts, or reporting forms that restate claims, those claims must bind to `paper/claim_evidence_map.json` or an equivalent MAS-owned claim ledger before export.
- `display_to_claim_blocker`: if the venue constrains figure/table count, graphical abstract content, supplementary display placement, or reporting forms, record how those requirements bind displays to claims; unresolved display-to-claim mapping blocks venue-specific packaging.
- `reporting_guideline_gate`: if official instructions require TRIPOD, STROBE, CONSORT, PRISMA, EQUATOR-listed, or journal-specific checklists, record the required checklist and block target resolution or package export until the checklist surface is present and passable.

## Exit condition

This skill is complete only when downstream writing and export can say one of two precise things:

1. the journal target is now mapped to a supported `publication_profile`; or
2. the journal target remains blocked because the official requirements do not yet map to a supported exporter profile.
