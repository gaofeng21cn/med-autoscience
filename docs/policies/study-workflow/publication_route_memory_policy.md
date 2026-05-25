# Publication Route Memory Policy

Status: `active policy`
Date: `2026-05-12`
Owner: `MedAutoScience`
Purpose: keep reusable publication-route experience available to Codex-led stages without turning it into a mechanical recipe engine.
State: `active operating policy`
Machine boundary: this is a human-readable policy. Machine truth remains in `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, `stage_recall_index`, `study_charter`, evidence/review ledgers, controller decisions, publication eval, and generated artifacts.

## Conclusion

Publication routes such as clinical classifier / risk stratification, subtype reconstruction, external validation / model update, gray-zone triage, survey trend analysis, or mechanistic domain-handler extension should be maintained primarily as natural-language route memory.

They are not a programmatic recipe engine. Their role is to remind Codex CLI of reusable medical publication experience at the right stage, then let the stage produce context-specific research judgment, candidate routes, failed paths, and next actions.

The landed MAS shape is:

- rich natural-language route memory cards
- minimal searchable metadata for retrieval and governance
- stage-specific retrieval and injection
- typed closeout writeback
- controller/evidence guards around claims and publication authority

The incorrect shape is:

- a large prompt block containing every route
- a rigid schema that tries to precompute which paper must be written
- a scoring engine that generates the winning research route before stage work
- a checklist that turns exploratory medical research into fixed analysis execution

## Why Natural-Language Memory

High-yield publication routes are exploratory knowledge. They encode experience such as:

- which data affordances often support a publishable paper
- which figure/table packages usually make a route credible
- which routes survive moderate or weak main effects
- which routes often fail because evidence, external validation, or clinical value is too thin
- which journal or reviewer expectations tend to matter

This knowledge is valuable because Codex can reason with it. Over-structuring it too early removes that value: the system starts optimizing fields rather than thinking medically.

Therefore route memory should preserve rich prose, caveats, examples, and failure modes. Structure is allowed only where it helps discovery, provenance, stage targeting, freshness, and writeback routing.

## Route Memory Card Shape

Each reusable route memory card should remain readable as prose. A useful card is not just a route name plus two sentences. The current MAS seed/apply surface requires a maintainer-useful card body with:

- title and route family
- short description of the publication pattern
- `best_fit`: when it is worth considering
- `poor_fit`: when the route is likely misleading or weak
- `minimum_evidence_package`: the evidence package a stage should look for
- `analysis_pattern`: common analysis shape, still non-binding
- `table_figure_pattern`: common tables, figures, or display routes
- `claim_boundary`: what the route can and cannot claim
- `reviewer_risks`: recurring reviewer objections
- `pivot_or_stop_rules`: when to repair, reroute, downgrade, or stop
- `codex_stage_guidance`: short per-stage guidance for `scout`, `idea`, `decision`, `analysis-campaign`, and `review`
- `example_signals`: optional data signals that make the route promising
- `failure_modes`: common reasons the route fails
- `source_refs`: policy, prior card, receipt, or study provenance refs

Metadata should be minimal:

- stable `memory_id`
- route family tags
- stage applicability, such as `scout`, `idea`, `decision`, `analysis-campaign`, or `review`
- source/provenance refs
- status such as `draft`, `active`, `paper_proven`, `deprecated`
- freshness or review date

The metadata supports retrieval. The rich prose supports Codex CLI reasoning. Neither decides the research route.

Thin cards are rejected at seed apply time. This is a quality contract for memory usefulness, not a recipe engine. The required fields prevent the library from degrading into a list of labels; they do not prescribe exact code, model choice, statistical path, route score, or final manuscript claim.

## Stage Use

Route memory is consumed through stage packets, not through global prompt stuffing.

Recommended behavior by stage:

- `scout`: retrieve a few route memories that may fit the dataset and disease area; use them to widen or sharpen candidate questions.
- `idea`: compare route memories against actual data affordances, literature gaps, endpoint feasibility, and clinical value; produce selected and rejected candidate lines.
- `decision`: use route memories as background for route rationale, stop/pivot rules, and risk of weak evidence; final route must still come from stage output and controller decision.
- `analysis-campaign`: retrieve memory about common evidence gaps, figure/table packages, weak-result handling, and reviewer-facing repairs.
- `review`: retrieve memory about recurring critique patterns, claim restraint, citation gaps, and route-specific reviewer expectations.

The retrieved set should be small and stage-relevant. A practical default is top few cards, not the whole library.

Current contract posture: `publication_route_memory_stages` includes `decision` in addition to the exploratory stages. This means the decision stage may read a small natural-language `publication_route_memory_refs` set through `stage_knowledge_packet` for route rationale, stop/pivot context, and rejected-alternative memory. It does not make route memory a controller decision source of authority: the official go, stop, reroute, human-gate judgment, downstream owner, and publication authority remain controller-owned and evidence-bound.

## Writeback

New experience from a stage should be written back only when it is reusable beyond the current paper.

Good writebacks:

- a route worked only after adding external validation
- a classifier route failed because event count was too low for credible calibration
- a survey trend route needed guideline correspondence and access/reimbursement context
- a reviewer repeatedly expected decision-curve or subgroup evidence for a risk model
- a figure/table package made a route easier to argue

Bad writebacks:

- single-study results or conclusions
- claim support that belongs in the evidence ledger
- reviewer findings that belong in the review ledger
- publication readiness assertions
- raw analysis outputs, logs, or package state

`stage_memory_closeout_packet` should propose the writeback. `memory_write_router_receipt` should route it to the correct owner surface or reject it.

## Authority Boundaries

Route memory can inspire and inform. It cannot authorize.

It cannot:

- expand the study charter
- replace evidence refs
- replace AI reviewer judgment
- authorize quality ready, publication ready, finalize ready, or submission ready
- hide negative or failed paths
- force Codex CLI to follow a fixed recipe when stage evidence points elsewhere

Controller and quality surfaces remain responsible for boundaries, evidence, owner route, stop-loss, publication gate, and human gate.

## Relationship To Existing Archetypes

Existing `preferred_study_archetypes` and `research_route_bias_policy` are the first generation of route memory. In the earlier MAS implementation they were used as route bias and contract input, not as a full publication-route memory library.

The actual code path is:

- profiles carry `preferred_study_archetypes`;
- study payloads may carry `study_archetype` or `preferred_study_archetype`;
- `_medical_contract_support.resolve_study_archetype()` selects the archetype from study payload or profile;
- `medical_analysis_contract`, `medical_reporting_contract`, `medical_paper_readiness`, `medical_quality_operating_system`, and `statistical_discipline_runtime` use that archetype to choose or check analysis/reporting/readiness expectations;
- `overlay/installer.py` renders the archetype prose into the local overlay prompt/context through `render_archetype_block()`.

That means `study_archetypes.md` and `med_autoscience.policies.study_archetypes` were useful first-generation route hints, but they were not a memory body store, did not support workspace-specific accepted/rejected lessons, did not carry receipt provenance, and did not provide route-memory inventory/writeback management.

Current migration has moved those archetypes into the richer Markdown library as full natural-language route memory cards while preserving executor-level autonomy. The seed fixture only indexes that Markdown body. These cards should not become hard-coded workflows unless a specific route matures into a separate audited capability with its own evidence, tests, owner boundary, and failure behavior.

## OPL Boundary

This policy belongs to MAS because publication-route experience is medical domain knowledge.

OPL may provide family-level discovery, indexing, stage descriptor refs, handoff, receipts, projection, and storage mechanics for domain knowledge packs. OPL must not own the medical content, choose the publication route, or turn MAS route memory into OPL-level truth.

The same mechanism can later support other domains, such as grant strategy memory in MAG or visual deliverable pattern memory in RCA. The content owner remains the domain agent.

## Related Memory Candidates

The current migration audit found several MAS surfaces that look similar to reusable recipes but should not all be handled the same way:

| surface | correct handling |
| --- | --- |
| `preferred_study_archetypes` and route-bias prose | Treat as first-generation natural-language route memory seeds. |
| AI reviewer repair lessons, route-back rationales, weak-result / negative-result handling | Write back only reusable lessons through stage closeout memory proposals; current-paper findings stay in evidence/review/controller ledgers. |
| journal-family expectations, recurring reviewer critique, claim-restraint lessons | Keep as natural-language review / publication-route memory unless they become audited gate requirements. |
| medical display template catalog, renderer contracts, layout QC, input schemas | Keep as strong audited display contracts; do not downgrade to route memory. |
| figure/table selection rationale and visual audit lessons across papers | Good candidate for natural-language memory linked from stage knowledge packets. |
| paper progress reconciler, owner route, publication gate, AI reviewer verdict, canonical package freshness proof | Strong controller / quality / artifact truth; never memory authority. |

The practical migration rule is: when a lesson helps Codex decide what to explore, keep it as prose memory; when it decides whether an artifact, claim, gate, or package is valid, keep it as a structured MAS-owned contract or truth surface.

## Current Implementation Posture

MAS now exposes `publication_route_memory` as a MAS-owned domain memory surface:

- `publication_route_memory_pack` at `portfolio/research_memory/publication_route_memory/memory_pack.json`
- `publication_route_memory_apply_receipt` under `portfolio/research_memory/publication_route_memory/migration_receipts`
- `publication_route_memory_inventory` through `medautosci publication route-memory-inventory --workspace-root <workspace>` as the read-only, body-free-by-default inventory/export surface
- `stage_knowledge_packet.publication_route_memory_refs` as the small stage-entry retrieval set; it carries ids, route family, title, locator, receipt ref, authority boundary, and a concise `route_memory_summary`, not the whole card body
- `memory_write_router_receipt` mirrored under `portfolio/research_memory/publication_route_memory/writeback_receipts`
- `paper_soak_memory_apply_proof` under `artifacts/stage_knowledge/paper_soak_memory_apply_proof/latest.json` as the controlled read-only proof surface that links stage route-memory refs, typed closeout proposal refs, MAS router receipt refs, workspace writeback receipt refs, and OPL/Aion display receipt refs

The canonical repo memory body now lives in Markdown at `docs/policies/study-workflow/publication_route_memory_library.md`. It contains nine rich seed cards:

- `publication_route_memory_seed__clinical_classifier`
- `publication_route_memory_seed__clinical_subtype_reconstruction`
- `publication_route_memory_seed__negative_result_stoploss`
- `publication_route_memory_seed__external_validation_model_update`
- `publication_route_memory_seed__gray_zone_triage`
- `publication_route_memory_seed__llm_agent_clinical_task`
- `publication_route_memory_seed__mechanistic_domain_handler_extension`
- `publication_route_memory_seed__survey_trend_analysis`
- `publication_route_memory_seed__external_validation_rescue`

The companion `publication_route_memory_seed_fixture.json` is now a seed index / locator. It lists stable ids, route families, stage applicability, titles, status, and Markdown anchors. It is not the human-maintained memory body.

Accepted `workspace_reusable` lessons from typed stage closeout update the workspace `publication_route_memory_pack` as natural-language memory cards. When closeout payloads include rich card sections, MAS preserves those fields in the promoted card. This makes a MAS-accepted lesson available to later stage-entry retrieval while preserving idempotent writeback receipts and the context-only authority boundary. The workspace pack is generated/applied MAS state, not the first editing surface for maintainers.

MAS exposes these as callable owner surfaces through `publication-route-memory-apply-seed`, `publication-route-memory-inventory`, `stage-knowledge-packet`, `stage-memory-closeout-route`, and `paper-soak-memory-proof`. These commands are domain-owned execution/read/receipt surfaces; they do not make OPL the memory body owner or publication quality authority. The grouped public form for the inventory is `medautosci publication route-memory-inventory --workspace-root <workspace>`. By default it returns card metadata, locator refs, filters, receipt counts, OPL/Aion receipt inventory, ref-only operator grouping, stale/deprecated review summary, and authority boundary while excluding the rich body. `--include-card-body` is reserved for maintainer review and returns the prose sections such as `best_fit`, `minimum_evidence_package`, `table_figure_pattern`, `claim_boundary`, `reviewer_risks`, `pivot_or_stop_rules`, and `failure_modes`.

2026-05-12 fresh paper-line proof: DM002 read-only closeout consumed `publication_route_memory_seed__negative_result_stoploss` and carried MAS-owned writeback receipt refs under both the study stage-knowledge artifact root and workspace `portfolio/research_memory/publication_route_memory/writeback_receipts`. The `real-paper-autonomy-guarded-apply-proof` surface now promotes this into a final ref-level memory proof for DM002: consumed route-memory refs and MAS router/workspace/OPL-Aion receipt refs are visible, `body_included=false`, and missing live apply permission remains a typed blocker rather than an artifact delta claim. `paper_autonomy/guarded-apply` can now write a MAS domain-handler dispatch receipt that carries the same DM002 ref chain plus provider attempt id, idempotency key, source fingerprint, no-forbidden-write proof, and typed blocker refs. This proves the ref chain is usable for OPL/Aion projection and provider-hosted receipt closure. It does not let OPL read memory prose, accept/reject writebacks, or mutate workspace truth.

The repo still tracks only policy, contracts, Markdown canonical memory body, seed index, code and tests. Real memory packs, migration receipts, writeback proposals and router receipts belong to the MAS workspace or runtime artifact root. OPL may discover locator / freshness / receipt refs; it does not own memory bodies, apply migration, accept/reject writebacks, choose a publication route, or promote memory into evidence, review, controller, publication or artifact truth.

Decision-stage availability is read-only context. `stage_knowledge_packet.authority_boundary.can_replace_controller_decision` remains `false`; controller decisions continue to cite current evidence, unresolved risk, Stop-loss Memo context, human-gate status, and downstream owner requirements before any route change is official.

`paper_soak_memory_apply_proof` is also read-only. It can show that a paper-line stage consumed a small route-memory set, produced a typed writeback proposal, and received a MAS router accepted/rejected receipt. It must expose refs and counts, not memory card prose, paper artifact bodies, publication verdicts, or receipt instances stored in the repo.

## Planning Gate Classification

Publication-route memory 的后续规划入口是 [MAS Current Development Lines](../../active/current-development-lines.md)，不是单独的 production closure plan。当前属于 `functional_follow_through_gate`：基础 policy、Markdown body、seed index、workspace pack、CLI inventory、typed closeout proposal、router receipt 和 body-free OPL/Aion projection 已落地，后续要增加真实 paper-line receipts 和维护纪律。

| memory gate | gate class | current planning status | done evidence |
| --- | --- | --- | --- |
| `paper_line_receipt_scaleout` | `functional_follow_through_gate` | `planned; DM002 ref chain landed` | 多条 paper line 产生 accepted / rejected / route-back reusable lesson receipts，并可由 body-free inventory/export 读取。 |
| `cross_workspace_inventory_smoke` | `functional_follow_through_gate` | `planned; CLI inventory_landed` | 不同 workspace 的 pack、migration receipt、writeback proposal/receipt 都能以 body-free refs、counts、freshness 和 authority boundary 展示。 |
| `card_status_and_stale_review` | `functional_follow_through_gate` | `planned; rich_seed_library_landed` | card status、deprecated/stale reason、review date 和 maintainer body review 规则清晰；不引入 ordinary-user write UI。 |
| `memory_body_apply` | `production_evidence_gate_when_live_workspace_required` | `planned; body_owner_boundary_landed` | 真实 workspace/runtime owner 接受或拒绝 body/writeback apply；OPL/Aion 只持 locator、freshness 和 receipt refs。 |

本 policy 的非目标保持不变：不做 recipe engine、不做 winning-route scorer、不把 OPL 变成 memory body owner、不把 memory refs 升级为 publication quality 或 controller decision authority。

## Human Inventory And Maintenance

The human-facing entrypoint is `docs/policies/study-workflow/README.md`. It points to the governing policy, Markdown canonical library, first-generation archetype prose, repo seed index, workspace memory pack locator, and receipt/proposal locators.

Current route memories are intentionally split by authority:

| inventory item | location | authority |
| --- | --- | --- |
| first-generation route prose | `docs/policies/study-workflow/study_archetypes.md` | non-binding policy seed |
| canonical route memory body | `docs/policies/study-workflow/publication_route_memory_library.md` | maintainer-editable Markdown-first memory body |
| seed card index | `docs/policies/study-workflow/publication_route_memory_seed_fixture.json` | repo-source index and locator, not the memory body |
| active workspace cards | `portfolio/research_memory/publication_route_memory/memory_pack.json` | generated MAS workspace-owned memory pack |
| seed apply receipts | `portfolio/research_memory/publication_route_memory/migration_receipts` | MAS workspace-owned migration audit |
| typed writeback proposals | `portfolio/research_memory/publication_route_memory/writeback_proposals/stage_memory_updates.jsonl` | stage closeout proposal log |
| accepted/rejected writeback receipts | `portfolio/research_memory/publication_route_memory/writeback_receipts` | MAS router receipt authority |

2026-05-12 fresh workspace inventory example:

- workspace: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk`
- memory pack: `portfolio/research_memory/publication_route_memory/memory_pack.json`
- card count: `3`
- card ids: `publication_route_memory_seed__external_validation_rescue`, `publication_route_memory_seed__negative_result_stoploss`, `publication_route_memory_writeback__dm002-route-memory-proof`
- supporting files: `migration_receipts/publication_route_memory_seed_apply_a2e037207a33f455.json`, `writeback_proposals/stage_memory_updates.jsonl`, `writeback_receipts/dm002-paper-soak-memory-proof-20260512.json`

After applying the current Markdown library to a workspace, maintainers get a rich starting library of nine cards, not only the three DM002-era workspace cards. Existing workspaces may still show the older three-card pack until the library is re-applied or refreshed through MAS owner surfaces.

This is maintainable today because the canonical cards are Markdown prose. Cards contain route family, stage applicability, status, provenance, fit/poor-fit guidance, minimum evidence package, common analysis/display patterns, claim boundaries, reviewer risks, pivot/stop rules, and failure modes. It is not yet a polished human management UI. The next low-risk management surface should be a read-only inventory/export grouped by workspace, stage applicability, route family, status, source refs, and receipt refs. Write/edit of canonical repo experience happens in Markdown; workspace apply/writeback still goes through MAS owner surfaces until an audited editor with receipt generation exists.

The read-only CLI inventory is now that first management surface. Use it as the default operator and OPL/Aion ingestion entrypoint because it gives stable metadata, locator refs, and receipt summaries without copying the memory body:

```bash
medautosci publication route-memory-inventory --workspace-root <workspace>
medautosci publication route-memory-inventory --workspace-root <workspace> --stage decision
medautosci publication route-memory-inventory --workspace-root <workspace> --route-family weak_or_negative_result_handling --include-card-body
```

The first two forms are suitable for body-free projection. The `--include-card-body` form is for MAS maintainers inspecting or repairing the natural-language memory card itself.

Manual JSON editing is allowed only as maintainer-level repair for generated workspace packs, indexes, or receipts. It must preserve stable `memory_id`, route family, stage applicability, source/provenance refs, status/freshness, and receipt traceability. It must not become the primary way to edit natural-language experience, and it must not add current-paper claims, publication readiness, evidence verdicts, review findings, or artifact state as route memory.

## Migration Plan

Current landed state is `workspace_apply_closure_ready`.

MAS provides a repo-source Markdown library at `docs/policies/study-workflow/publication_route_memory_library.md` and a small seed index at `docs/policies/study-workflow/publication_route_memory_seed_fixture.json`. The Markdown library is the canonical body. The JSON index is not the memory store and is not a receipt instance. It exists to make migration and retrieval reviewable: reusable publication-route lessons stay natural-language-first, carry minimal searchable metadata, and point back to policy/stage provenance.

Actual migration happens in a MAS-owned workspace or runtime artifact root:

- target memory pack: `portfolio/research_memory/publication_route_memory`
- seed apply receipts: `portfolio/research_memory/publication_route_memory/migration_receipts`
- stage closeout writeback receipts: `portfolio/research_memory/publication_route_memory/writeback_receipts`

The migration owner is MAS. OPL may project `migration_plan_ref`, `seed_corpus_ref`, `memory_pack_locator`, `migration_receipt_locator`, `writeback_receipt_locator_ref`, and readiness. OPL must not apply the migration, accept/reject writebacks, store memory body text, or promote memory into evidence, review, controller, publication, or artifact truth.

The useful work now is:

- keep the route memory cards natural-language-first;
- keep `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, and `stage_recall_index` as the small controlled retrieval/writeback surfaces;
- expose candidate memory locators and owner boundaries through MAS-owned descriptor surfaces and workspace apply receipts;
- run seed migration only through MAS-owned workspace apply and receipt paths;
- preserve Codex CLI autonomy inside each stage.

Do not implement a separate publication recipe engine until a route has matured into an audited capability with clear evidence obligations, tests, owner boundary, and failure behavior.

## 2026-05-12 OPL Family Index Status

Current OPL discovery sees MAS, MAG, and RCA as resolved family memory descriptors:

- OPL `agents list --json` currently reports `aligned_count=3`, `missing_count=0`, `drift_detected_count=0`, `blocked_count=0`, `production_closure_gap_count=12`, and `provider_temporal_residency_gap_status=closed_by_fresh_proven_proof`.
- OPL `stages list --json` currently reports `resolved_planes_count=3` and `stages_count=18`.
- OPL `domain-memory list --json` currently reports `resolved_memory_descriptor_count=3` and `missing_memory_descriptor_count=0`.
- OPL `domain-memory inspect --domain mas --json` resolves `mas_publication_route_memory` from the MAS standard `domain_memory_descriptor`, with `opl_role=locator_projection_owner` and forbidden OPL authority over memory store, domain truth, quality verdict, artifact authority, route decision, and publication readiness.
- OPL `family-runtime status --json` now defaults to selected provider `temporal`; Temporal is the production required provider and fresh read model reports managed service / worker residency proof. `local_sqlite` remains available only as explicit dev/CI/offline diagnostic baseline and cannot replace production provider, domain daemon replacement, or paper-line readiness evidence.
- OPL roadmap now records Temporal provider core as landed: `StageAttemptWorkflow`, Codex/domain domain-handler activities, human/user/resume signals, attempt query, `attempt start|query|signal`, worker helper, lifecycle contract, and Temporal residency proof. The current OPL-side provider residency gate is closed by fresh `production_residency_proven` proof; the remaining OPL-side evidence gap is long-running provider SLO plus real domain activity / owner-chain soak.
- MAG/RCA also expose standard `family_domain_memory_ref.v1` descriptors for their grant-strategy and visual-pattern memory locators.
- This makes MAS publication route memory the MAS-side reference implementation for natural-language, stage-consumed publication-route memory, not a reason to move publication-route content into OPL or to build an OPL-owned recipe runtime.

Remaining MAS-side proof:

- keep DM002's real paper-line consumed-memory proof as the current read-only baseline and guarded-apply final ref proof;
- use provider-hosted guarded apply to publish only the ref-level chain from stage entry to typed closeout proposal, MAS `memory_write_router_receipt`, OPL/Aion read-only receipt refs, and MAS owner apply receipt / typed blocker refs;
- proceed to controlled apply only through MAS owner surfaces when the route-memory proof is paired with artifact delta, gate replay, reviewer judgment, route decision, human gate, stop-loss, or typed blocker evidence.

## Now / Next / Defer

Now:

- maintain the policy/index/seed/workspace locator documentation as the single human entrypoint;
- keep writing accepted reusable lessons into workspace `memory_pack.json` through MAS router receipts;
- use `publication-route-memory-inventory` / `publication route-memory-inventory` as the current read-only inventory/export surface;
- run the inventory against more real workspaces and keep card counts / receipt counts visible in closeout notes;
- add maintainer-level card status discipline for `active`, `draft_seed`, `deprecated`, and `stale_review_needed` without turning the body into a hard schema;
- keep OPL projection ref-only and body-free;

Next:

- generalize accepted/rejected writeback receipt evidence beyond DM002;
- add OPL/Aion App/workbench grouping by workspace, stage, route family, status, and receipt refs;
- run provider-hosted guarded apply proof for MAS paper lines using the same memory ref/writeback receipt chain when production provider residency / live apply gate is available;
- add stale-memory review and deprecation receipt flow after enough cards accumulate.

Defer:

- recipe engine, winning-route scorer, or hard schema for all publication routes;
- OPL-owned memory content store;
- full human editor until receipt generation, provenance, deprecation, and stale-memory review are audited.
