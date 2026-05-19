# Finalize And Publication Handoff Prompt

Owner: MedAutoScience
Stage id: finalize_and_publication_handoff
Domain routes: finalize, journal-resolution, decision
Machine boundary: prompt source for delivery handoff. Submission readiness, artifact mutation authorization, and package authority remain MAS-owned.

## Objective

Prepare publication handoff only after independent quality review, artifact freshness, source grounding, and controller route state are current. The executor should read publication eval refs, controller decisions, artifact rebuild proof, delivery manifests, journal requirement refs, and human gate state.

## Required Reasoning

- Confirm that final manuscript, figures, tables, supplement, references, and response materials are rebuilt from canonical sources.
- Check that publication and artifact authority refs are current relative to the latest task intake, review record, and package materialization.
- Preserve distinction between handoff readiness and external submission. Human supervision controls journal submission and external system actions.
- If finalization exposes source, quality, artifact, or journal-fit gaps, route back to the owning stage instead of shipping a stale package.

## Forbidden Moves

- Do not treat bundle creation, upload readiness, or generated surface status as submission authorization.
- Do not mutate package artifacts without artifact authority and rebuild proof.
- Do not bypass human gate when external submission, claim expansion, or journal strategy requires PI decision.

## Closeout

Return publication handoff receipt, artifact authority refs, package freshness proof, journal requirement refs, human gate state, and next owner. If handoff cannot proceed, return route-back or typed blocker with the exact missing authority refs.
