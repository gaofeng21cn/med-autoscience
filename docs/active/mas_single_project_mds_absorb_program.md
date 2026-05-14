# MAS Single-Project MDS Absorb Program

Status: `landed foundation owner doc; provenance archive parity guard active`
Date: `2026-05-11`
Owner: `MedAutoScience`
Purpose: preserve the current MAS monolith outcome, MDS retained-role decisions, provenance rules, archive/import boundaries, and parity oracle boundaries.
Machine boundary: this is a human-readable owner/provenance document. Machine truth remains in MAS runtime/controller/quality/artifact surfaces, source provenance records, parity fixtures, explicit archive/import readers, archive/import ledgers, and live workspace evidence.

Full historical record: [2026-05-10 MAS/MDS absorb full record](../history/program/mas_single_project_mds_absorb_program_2026_05_10_full_record.md).

## Current Role

This document is P3 in the MAS program portfolio. P3 is no longer an active implementation queue. It is the landed foundation owner for MAS monolith, MDS provenance, retired compatibility surfaces, and future source-intake classification.

The current state is:

- MAS is the single default repo, user entry, app skill, CLI/MCP/product-entry surface, runtime owner, quality owner, and artifact owner for medical research work.
- External `med-deepscientist` / `DeepScientist` is retained only as source provenance, historical fixture, explicit archive import, backend audit, upstream learning, and parity oracle reference.
- MAS daily operation does not require the external MDS repo, MDS daemon, MDS WebUI, MDS workspace-local service, or MDS Git runtime lifecycle.
- MAS default independence is landed. Full behavior equivalence with every old MDS daemon/WebUI interaction is not claimed.

## Current Owner Split

| concern | current owner | P3 disposition |
| --- | --- | --- |
| Study truth and next owner | MAS controller/study truth surfaces | retained in MAS |
| Publication and quality verdict | MAS AI reviewer, publication gate, evidence/review ledgers | retained in MAS |
| Runtime health and recovery | MAS Runtime OS, worker wrapper, owner-route dispatch, local diagnostics | retained in MAS; provider hosting belongs to P2/OPL |
| Artifacts and package authority | MAS Artifact OS and canonical manuscript/package rebuild proof | retained in MAS |
| Old MDS code/history | external archive/provenance reference | no-history import only; no default dependency |
| Old MDS capability signals | parity fixtures or audit oracles | cannot authorize quality or submission readiness |
| Old MDS paths | explicit archive/import or provenance readers | no new default writer |

## Landed Facts

P3 has already closed these implementation lines:

- MAS-first workspace layout is the default: `runtime/quests/`, `runtime/archives/`, `runtime/restore_index/`, `artifacts/runtime/`, and `ops/mas/`.
- Default visible runtime/profile fields use MAS-owned naming. Old `med_deepscientist_*` fields are historical fixture, explicit archive import, or backend-audit references.
- MCP/product-entry/progress defaults no longer route through old MDS modes as hidden fallback.
- Source provenance, author audit, retained-capability fixtures, and parity matrices are tracked as MAS-authored no-history records.
- Functional monolith closeout moved default operation, visualization, runtime core, diagnostics, learning, and retained capability surfaces into `med-autoscience`.
- Behavior-equivalence gaps are documented as explicit gaps or retired-by-design surfaces; they do not reopen external MDS as a runtime owner.

## Guard Rules

Future work that references MDS or DeepScientist must first classify the reference:

| classification | allowed use |
| --- | --- |
| `source_provenance` | explain source ref/hash/license and no-history origin |
| `historical_fixture` | keep a frozen example for regression/parity |
| `explicit_archive_import` | restore or inspect an old workspace/archive by explicit operator action |
| `backend_audit` | compare behavior without making MDS the default backend |
| `upstream_learning` | study new upstream ideas, then re-own any accepted pattern in MAS or OPL |
| `parity_oracle_reference` | compare retained capability semantics without granting authority |

Disallowed uses:

- making external MDS a default runtime, default diagnostic, default runner, WebUI dependency, or hidden fallback;
- letting old MDS paper/package/coverage signals authorize MAS quality or submission readiness;
- importing MDS history or upstream authors into MAS default-branch contributor graph;
- writing new MAS functionality under MDS-first names or paths.

## Relationship To Other Program Layers

P3 supports P0, P1, and P2 by keeping the foundation clean:

- P0 paper autonomy can rely on MAS-owned quality, route, repair, and artifact authorities.
- P1 OPL App Runtime Workbench can consume MAS projections without consulting old MDS UI or workspace services.
- P2 OPL framework alignment can host MAS through sidecar/receipts without reviving MDS daemon semantics.
- P3a runtime lifecycle guards keep root/quest Git and old `.ds` runtime payloads from returning as default state surfaces.

New runtime/product implementation should not be added to this file. If it is paper-loop acceptance, use P0. If it is App/workbench productization, use P1. If it is OPL provider/framework alignment, use P2. If it is runtime lifecycle, restore proof, or Git retirement drift, use P3a.

## Verification And Evidence

P3 claims should be verified through:

- source provenance and author audit records;
- retained capability and MDS behavior parity fixtures;
- MAS runtime/controller/product-entry/Progress Portal contract tests;
- explicit archive/import and provenance-reader tests;
- live workspace evidence only when discussing a specific workspace.

Repo documentation is not proof that a real paper line progressed. P3 only proves ownership, provenance, archive/import boundaries, and parity reference boundaries.

## Historical Content Disposition

The previous long record combined final topology, dated closeouts, lane tables, functional monolith campaign details, paper autonomy stability notes, and workspace migration rules. It has been archived as a full record because those details remain useful evidence and audit trail.

Current readers should use this document for the stable P3 state and guard rules, then jump to the archived record only when they need dated implementation evidence or original lane naming.
