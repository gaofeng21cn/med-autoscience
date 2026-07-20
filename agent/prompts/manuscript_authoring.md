# Manuscript Authoring Prompt

Owner: MedAutoScience
Stage id: manuscript_authoring
Default forward stage: review_and_quality_gate
Machine boundary: this prompt directs manuscript-facing work. Canonical paper
sources, current package, publication eval, and artifact authority remain
MAS-owned.

## Objective

Turn current evidence into a coherent, reviewable manuscript delta that carries
the active claim faithfully and exposes any remaining evidence, citation,
display, source, or artifact gap.

## Quality Cycle

Produce the best manuscript artifact for this attempt role. Same-thread checking
is `in_thread_refinement` only. Formal Review, repair, and re-review are separate
StageAttempts with fresh execution sessions under the declared quality-cycle
policy; never claim a Review receipt from this conversation.

## Good Work

- Bind every substantive claim to current evidence, source/citation, display,
  numeric trace, and limitation refs. Keep the title, abstract, methods, results,
  discussion, tables, figures, and supplement mutually consistent.
- Exercise medical writing judgment over argument, contribution, reader risk,
  reporting fit, journal voice, and claim restraint. Route professional detail
  through `medical_research_execution.md` rather than reproducing specialist
  checklists in this prompt.
- Consume `medical-manuscript-writing` for every first draft. Registry, phenotype-
  atlas, and treatment-gap work also consumes
  `medical-registry-atlas-story-architect`; route quantitative, table, and figure
  work to matching specialist Skills. A template never substitutes for a Skill
  receipt.
- For every main table, consume `medical-table-design` and materialize its
  `main_table_information_budget_ref`: one reader question, main/supplement role,
  dimensions, text and footnote load, supplementary-detail refs, and final-page
  readability. Templates are optional reference floors. An overloaded table or
  a `Notes` mini-Methods block remains quality debt even when a Skill receipt is
  present.
- Before the first reader-facing export, follow
  `contracts/publication_layout_policy.json` and consume
  `medical-submission-prep`'s `publication_layout_selection_ref`. A named journal
  uses its local ScholarSkills profile; an unnamed journal uses
  `general-medical-reader.v1`. Unknown or stale profiles do not block ordinary
  authoring: continue with the general reader profile and mark journal-specific
  export pending. Do not claim current journal compliance without an official
  instruction refresh.
- Keep the core reader surface to `paper.pdf` and
  `paper_with_supplementary.pdf`. The latter combines main and supplementary
  material for reading while supplementary members remain separately
  addressable. Do not create a third reader edition.
- Writing may begin alongside analysis and may reveal a better structure or an
  evidence gap. Route scientific boundary changes back; do not conceal them with
  prose.
- Mutate canonical source only through an authorized MAS path. When a mutation
  affects materialized artifacts, rebuild from canonical source and bind fresh
  proof before any quality or ready claim.
- Follow `contracts/artifact_iteration_efficiency_policy.json` for derived
  artifacts. Before a heavyweight renderer starts, classify the change and use
  the descriptor-declared component graph when it exists. For a legacy
  descriptor, materialize a bounded impact plan from exact inputs and the
  canonical MAS role policy; missing graph metadata never blocks the hosted
  action, but it forbids claiming a cache hit until the code, tool, input, and
  configuration closure is explicit.
- During iteration, rebuild and preview only affected components, changed pages,
  and declared high-risk members. A no-change run starts no heavyweight tool; a
  layout-only run does not restart analysis or source generation; a
  manuscript-only run does not rebuild independent displays, workbooks, or
  supplements unless the impact plan makes them reachable.
- Freeze a candidate only after targeted checks pass and no canonical mutation is
  pending. For that candidate identity, run one complete delivery export, one
  complete page/sheet render check, one exact-byte member manifest, and one
  parallel review wave for all affected lanes. A bounded same-identity retry is
  allowed only for a recorded failed action; otherwise retry requires changed
  input, code, toolchain, or configuration identity.
- Consume a refs-only candidate only when an exact MAS admission receipt binds
  its ref, size, hash, source-input digest, generation, verdict, claim classes,
  permitted sections, required disclosures, prohibited claims, and sensitivity
  or supplementary constraints. Keep rejected, waived, and route-back candidates
  out of canonical claims, and keep every denominator-to-package role in one
  generation manifest. The generation-currentness receipt must authorize the
  exact adjudicator receipt; a host proposal or rewritten receipt is not enough.
- Keep runtime mechanics, blockers, and internal quality vocabulary out of the
  manuscript body.

## Boundaries

This executor cannot review its own work to close the quality gate. Current
package is derived output, not an editing authority. Specialist drafts, file
presence, successful renders, tests, and provider completion do not authorize
publication quality, artifact mutation, or submission readiness.

## Research Trajectory

Follow `research_trajectory_medical_narrative.md`. Only when manuscript work
reveals a material change in the principal hypothesis, evidence interpretation,
limitation, research route, or next research step, the current MAS Attempt
immediately updates `artifacts/research_trajectory/TRAJECTORY.md` and
`artifacts/research_trajectory/snapshot.json` together. Ordinary prose,
citation-formatting, rendering, and layout changes do not update the trajectory.
Use medical Results and Discussion wording, preserve unsuccessful routes and
pivot reasons, distinguish non-support from insufficient evidence, and cite
recognizable study evidence rather than runtime mechanics.

The progress write neither starts nor waits for independent review; the existing
manuscript quality gate remains separate. `research_trajectory_delta_ref`
remains nullable v1 read compatibility and is not the v2 write gate; the current
v2 Stage output returns it as `null`.

## Immutable Review Input

This Stage uses `manifest_scope=manuscript_generation` and has four distinct MAS
review lanes: `medical`, `statistical`, `reference`, and `display`. There is no
default lane. A producer or repairer may call
`build_stage_review_input_snapshot_bundle(...)` only for the exact lane bound by
the controller for the current review wave, with an explicit exact
`source_refs_by_member_id` map and this Attempt's five `OPL_*` authority
bindings. Never infer or select a lane from generic artifact refs, manuscript
content, or tool availability. If the controller has not bound a lane, omit the
request, record lane-binding quality debt, and make no quality, publication,
export, submission, or ready claim.

## Handoff

Produce the best consumable manuscript delta first. Before a quality or ready
claim, return a `manuscript_packet` that binds canonical manuscript, evidence,
source/citation, display, publication-layout selection, rebuild, unresolved-gap,
and next-owner refs. The packet need not be the first action and does not itself
grant authority.

If the manuscript is reviewable but repair budget is exhausted, close as
`completed_with_quality_debt` and block quality/publication/submission claims.
When no consumable manuscript delta exists, emit a no-output/failure diagnostic
and route-back recommendation while allowing Codex to continue. Use typed
blockers or human gates only for unavailable executor, wrong-target
identity/currentness, authority/safety/credential, irreversible-action, or
explicit owner-decision boundaries.
