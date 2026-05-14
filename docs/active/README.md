# Active Docs

Owner: `MedAutoScience`
Purpose: `active_execution_and_gap_index`
State: `active_support`
Machine boundary: Human-readable index. Machine truth stays in contracts, schemas, source, runtime ledgers, study workspaces, publication artifacts, and owner receipts.

This directory is the canonical OPL-family location for current MAS execution, current plans, current gaps, active baton, and closeout evidence.

The former `docs/active/` active-baton layer has been physically retired.
Current MAS execution maps, paper-autonomy target docs, framework migration
owners, productization enablers, stage-form programs, and landed foundation
guard docs live in this directory. `program_id` and `human_doc:program_*`
remain semantic identifiers only; they do not imply a physical `docs/active/`
directory.

Start with:

- [Docs Guide](../README.md)
- [Status](../status.md)
- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)
- [MAS Current Development Lines](./current_development_lines.md)
- [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md)
- [MAS Stage Surfaces](../runtime/contracts/stage_surfaces.md)

## Current Active Layers

| Layer | document | current role |
| --- | --- | --- |
| Target / acceptance | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | Defines the MAS paper-autonomy target and final acceptance contract: reviewer findings, repair units, gate replay, route decisions, stage knowledge/memory, live paper soak, and quality boundaries. |
| Current execution priority | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | Framework-first migration line: finish the OPL agent framework, migrate MAS, partition and preserve new/old capabilities, then retire old default dependencies and compatibility surfaces. |
| Cross-cutting stage form | [MAS Stage Surface Standardization Program](./stage_surface_standardization_program.md) | Keeps every MAS stage expressed through a consistent stage card, route contract, prompt/skill surface, tool surface, knowledge packet, closeout obligation, one-page Stage Deliverable Review Page / Index, quality gate, and OPL projection boundary. |
| Product enabler | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | Productization lane that follows framework migration and makes migrated MAS/OPL state visible and controllable through the OPL App Runtime Workbench. |
| Landed foundation | [MAS single-project MDS absorb program](./mas_single_project_mds_absorb_program.md) | Landed monolith/provenance owner doc. It preserves current boundary and guard rules; the full historical record lives in `docs/history/program/`. |
| Landed foundation | [Runtime lifecycle SQLite migration program](./runtime_lifecycle_sqlite_migration_program.md) | Landed runtime-lifecycle guard doc. It preserves current SQLite/file authority, quest/root Git retirement, and drift rules; the full historical record lives in `docs/history/program/`. |

Actual development proceeds by content block, not by completing every section of
an old whole-file plan. The full old P1/P2 records are archived; the active
files keep owner boundaries, priority, and executable content lanes.

## Placement Rule

- `docs/active/`: current plans and owner docs that still need execution order,
  owner gates, closeout evidence, or landed provenance.
- `docs/runtime/`: runtime contracts, control surfaces, projections, display
  contracts, and active designs that are becoming technical runtime/API/contract
  surfaces.
- `docs/delivery/`: manuscript, package, submission/export, and medical-display
  delivery support.
- `docs/references/`: support references, parity, integration notes, MDS
  learning, verification ledgers, and mainline assessments.
- `docs/policies/`: stable internal rules and long-lived
  workflow/governance policy.
- `docs/history/program/`: old full records, closeouts, activation packages,
  dated recurring intake snapshots, and superseded plans.

If content still decides what happens next, who owns closeout, or what counts
as done, keep it in `docs/active/`. If it has become a runtime/interface
constraint, move it to `docs/runtime/`; if it is background, comparison,
learning, or evidence, use `docs/references/`; if it only preserves historical
context, use `docs/history/`.
