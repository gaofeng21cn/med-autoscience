# AI-First Figure Design And Integrity Companion

Purpose: guide AI-first manuscript figure design and verify that manuscript figures and tables honestly support their bound claims before figure, write, review, analysis-campaign, or finalize work closes. This is MAS-owned companion content, not a runtime graphics linter, router, database, or display authority.

MAS authority remains in `paper/display_registry.json`, `paper/figure_semantics_manifest.json`, display-to-claim maps, evidence ledgers, review ledgers, and publication evaluation. Use this template progress-first: inspect figures that affect active claims, repair or route them, and record blockers instead of polishing around unsupported displays. Do not use local image presence, chat notes, or exported previews as publication authority.

Use Nature Figure-style progressive disclosure and K-Dense-style manifest and QA ideas only as references inside the MAS owner path. Do not create a parallel display owner or `opl-scholar-display` entry.

## Design companion

- Figure intent:
- Supported claim or reviewer concern:
- What the figure must not claim:
- Panel structure and order:
- Required statistics, uncertainty, and annotations:
- Visible text kept in the figure:
- Details moved to caption, manifest, review ledger, or route-back note:
- Renderer family selected: `python` / `r_ggplot2` / `html_svg`
- Renderer selection rationale:
- Render command or script ref:
- Render-inspect-revise evidence:
- Owner gate status: accepted / route-back / typed blocker / human gate

## Audit header

- `study_id`:
- `quest_id`:
- `active_run_id`:
- Figure or table ids:
- Display registry ref:
- Figure semantics manifest ref:
- Claim-evidence map ref:
- Reviewer concern or route reason:

## Integrity checks

| display_id | bound claim_id | source artifact | renderer family | integrity issue | severity | action | MAS owner surface |
|---|---|---|---|---|---|---|---|
|  |  |  | python / r_ggplot2 / html_svg | axis truncation / dual axis / missing uncertainty / stale data / unsupported claim / palette issue / caption overclaim | blocker / major / minor / note | repair display / downgrade claim / route analysis-campaign / route write / route review / human gate |  |

## Closeout

- Displays accepted as current:
- Displays needing regeneration:
- Claims needing downgrade:
- Figure/table blockers:
- Next MAS route:
