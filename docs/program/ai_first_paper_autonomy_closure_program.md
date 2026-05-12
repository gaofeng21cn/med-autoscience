# AI-first Paper Autonomy Closure Program

Status: `active target and acceptance owner`
Date: `2026-05-11`
Owner: `MedAutoScience`
Purpose: define the current MAS paper-autonomy objective, acceptance gates, and live-soak evidence requirements.
Machine boundary: this is a human-readable program owner. Machine truth remains in `study_charter`, `paper/evidence_ledger.json`, `paper/review_ledger.json`, `artifacts/publication_eval/latest.json`, `artifacts/controller_decisions/latest.json`, `study_runtime_status`, `runtime_watch`, runtime supervision receipts, owner-route dispatch receipts, manuscript/package rebuild proof, and live study artifact refs.

Full historical record: [2026-05-10 AI-first paper autonomy full record](../history/program/ai_first_paper_autonomy_closure_program_2026_05_10_full_record.md).

## Current Role

This document is P0 in the MAS program portfolio. P0 is the target and acceptance contract for AI-first paper autonomy. It states the research outcome MAS must deliver and the evidence that can prove progress on a real paper line.

P0 was created before the current OPL framework split was clear. During implementation, the target proved larger than a MAS-only runtime problem. The current answer is:

- `MAS` owns medical research truth, paper quality, publication judgment, reviewer repair, route decisions, evidence/review ledgers, and canonical manuscript/package authority.
- `OPL` owns the Codex-first, stage-led agent runtime framework that can host MAS as a domain agent: stage attempt, queue, wakeup, receipt, recovery, approval/human gate transport, lifecycle primitives, projection, and shared indexes.
- P0 remains the MAS target. P1 and P2 are the implementation dependencies that make the target usable as a product and durable as a framework-backed runtime. P3 and P3a are completed foundations that keep the MAS monolith, provenance, runtime lifecycle, and restore-proof boundary stable.

## Current State

The repo-level MAS paper loop is implemented enough to be called, tested, and inspected:

| area | current state | owner |
| --- | --- | --- |
| AI reviewer finding to repair | `repo surface landed` | MAS reviewer/refinement/repair owner surfaces |
| Repair execution | `repo surface landed` | `paper_repair_executor`, canonical paper sources, ledgers, owner receipts |
| Gate replay and reviewer recheck request | `repo surface landed` | MAS publication gate and AI reviewer workflow |
| Weak/negative result route decision | `repo surface landed` | MAS route decision and controller decision surfaces |
| Stage knowledge and memory packets | `repo contract/read-model landed` | MAS stage knowledge packet, closeout packet, memory write router, recall index |
| Real paper closure | `evidence-gated live soak` | live MAS study truth surfaces |
| Product visibility | `depends on P1` | OPL App Runtime Workbench consuming MAS projections |
| Durable hosted runtime | `depends on P2` | OPL stage-led framework and provider-backed runtime consuming MAS sidecar/receipts |

The important distinction is that `repo surface landed` means MAS has the callable contracts, owners, receipts, and tests needed for the loop. It does not mean every real paper line has already reached submission-facing closure.

2026-05-12 fresh live-soak calibration:

- DM002 currently produces an OPL-ingestable typed closeout with `domain_ready_verdict=ai_reviewer_re_eval`, MAS-owned publication gate / controller decision / repair evidence refs, and `next_owner=analysis-campaign`.
- DM003 currently produces an OPL-ingestable typed closeout with `domain_ready_verdict=artifact_delta` and `next_owner=write`.
- Obesity currently produces an OPL-ingestable typed closeout with `domain_ready_verdict=artifact_delta` and `next_owner=write`.
- DM002 also proves a publication-route memory read/writeback ref chain: consumed memory ref `publication_route_memory_seed__negative_result_stoploss` plus MAS-owned stage/router writeback receipt refs.
- The calibration is read-only: `writes_performed=false`, `writes_real_workspace=false`, and OPL is forbidden from writing publication eval, controller decisions, current package, publication quality verdict, artifact authority, or memory body.

This means the current three-paper evidence has crossed the read-only acceptance threshold. It still has not crossed the production-hosted guarded-apply threshold.

## Acceptance Contract

MAS paper autonomy is accepted only when a real eligible paper line can repeatedly show one of the following outcomes after an autonomous work unit:

- manuscript, table, figure, result, package, evidence ledger, or review ledger delta;
- publication gate replay with owner progress;
- AI reviewer judgment update;
- route decision, claim downgrade, bounded repair, switch-line, stop-loss, or human gate;
- typed blocker that names the missing owner/input/permission/scientific constraint.

Worker liveness, queue existence, status refresh, or provider attempt completion are supporting evidence. They do not count as paper progress by themselves.

## Program Relationship

| layer | current role | relationship to P0 |
| --- | --- | --- |
| P0 | paper autonomy target and acceptance | defines outcome, quality boundary, and live-soak proof |
| P1 | OPL App MAS Runtime Workbench | turns P0 progress, blockers, route decisions, artifacts, terminal/logs, and safe actions into a user-facing product surface |
| P2 | OPL stage-led/provider runtime alignment | gives P0 durable stage attempt, queue, wakeup, recovery, approval, receipt, lifecycle, and projection support through OPL |
| P3 | MAS monolith / MDS absorb landed foundation | keeps MAS as the single default medical-research owner and keeps MDS as provenance/audit/reference |
| P3a | runtime lifecycle / SQLite / Git-retirement landed foundation | keeps runtime lifecycle authority, archive/restore proof, and legacy workspace drift handling stable |

Implementation details should live with the layer that owns them: P1 for App/workbench, P2 for OPL framework/provider, P3/P3a for landed foundation guards, and P0 for paper-loop acceptance.

## Active Responsibilities

P0 currently owns these responsibilities:

- Keep the paper loop target clear: reviewer finding -> repair work unit -> canonical delta -> gate replay -> AI reviewer recheck -> route decision or closure.
- Keep negative, weak, contradictory, or blocked analysis visible through claim downgrade, bounded repair, switch-line, stop-loss, failed-path evidence, or human gate.
- Keep stage-led research autonomy natural-language-first: Codex CLI explores inside a bounded stage packet; route engines compare, route, audit, and materialize decisions, but do not replace research reasoning.
- Keep publication-route memory as experience cards and writeback receipts, not a rigid recipe engine and not a quality authority.
- Keep quality authority in MAS-owned study charter, evidence ledger, review ledger, AI reviewer, publication gate, controller decisions, and canonical paper sources.

Related responsibilities live in these owner documents:

- OPL App UI, terminal panels, action sheets, and runtime workbench layout belong to [P1](./opl_app_mas_runtime_workbench_program.md).
- OPL provider, Temporal worker, family queue, stage attempt ledger, retry/dead-letter, shared lifecycle primitive, and domain-agent skeleton migration belong to [P2](./opl_temporal_mas_runtime_retirement_program.md) and OPL master docs.
- MDS provenance, monolith closeout, workspace layout, root/quest Git retirement, restore proof, and old workspace drift belong to [P3/P3a](./mas_single_project_mds_absorb_program.md) and [Runtime Lifecycle SQLite Migration](./runtime_lifecycle_sqlite_migration_program.md).

## Current Verification

Use these evidence levels in order:

1. Real study surfaces: `study_progress`, `study_runtime_status`, `runtime_supervision/latest.json`, `controller_decisions/latest.json`, `publication_eval/latest.json`, paper artifacts, gate/reviewer receipts.
2. MAS owner receipts: repair execution, route decision, gate replay request, AI reviewer recheck request, stage memory closeout and write-router receipts.
3. Repo contract tests: sidecar/repair/reviewer/route/stage-memory focused tests and `make test-meta`.
4. OPL/provider evidence: stage attempt and queue receipts only after they reference MAS owner receipts and do not write forbidden MAS truth surfaces.
5. Production hosted evidence: provider attempt query, Codex/domain activity receipt, typed closeout, MAS owner receipt, no-forbidden-write proof, and an artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker in MAS truth surfaces.

Docs, queue tasks, provider status, and worktree activity are never publication-quality proof.

## Historical Content Disposition

The previous long record mixed target definition, completed repo work, implementation lanes, external framework comparisons, and real-paper soak requirements. It has been archived as a full record because it is still useful provenance, but it is no longer the current reading surface.

Use the archived record only for:

- detailed 2026-05-10 closeout evidence;
- original lane names and historical acceptance examples;
- external engineering reference provenance;
- future audits that need to reconstruct why P0 split into MAS target plus OPL framework/product dependencies.

New implementation detail should enter the current owner document that actually owns it: P0 for paper loop acceptance, P1 for App/workbench productization, P2 for OPL framework/provider alignment, P3/P3a for monolith/runtime lifecycle guard evidence.
