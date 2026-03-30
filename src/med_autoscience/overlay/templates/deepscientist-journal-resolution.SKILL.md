---
name: journal-resolution
description: Use when a submission target does not already map to a supported publication profile and the journal requirements must be resolved from official sources.
---

# Journal Resolution

Use this skill to convert an unresolved journal target into a controlled, evidence-backed submission profile.

{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}

{{MED_AUTOSCIENCE_CONTROLLER_FIRST}}

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

## Exit condition

This skill is complete only when downstream writing and export can say one of two precise things:

1. the journal target is now mapped to a supported `publication_profile`; or
2. the journal target remains blocked because the official requirements do not yet map to a supported exporter profile.
