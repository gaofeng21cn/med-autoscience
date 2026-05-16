# Runtime Lifecycle SQLite Migration Program

Status: `landed foundation owner doc; runtime lifecycle and restore-proof guard active`
Date: `2026-05-11`
Owner: `MedAutoScience runtime lifecycle read-model/index boundary`
Purpose: preserve the current runtime lifecycle authority model, SQLite/file boundary, root/quest Git retirement status, restore-proof archive rules, and drift handling process.
Machine boundary: this is a human-readable owner/provenance document. Machine truth remains in runtime lifecycle SQLite databases, migration ledgers, restore indexes, archive manifests, compatibility exports, runtime/controller surfaces, and live workspace evidence.

Full historical record: [2026-05-08 runtime lifecycle SQLite migration full record](../history/program/runtime_lifecycle_sqlite_migration_program_2026_05_08_full_record.md).

## Current Role

This document is P3a in the MAS program portfolio. P3a is the landed runtime lifecycle foundation under P3. It is no longer a broad planning board for all runtime, MDS absorb, or paper autonomy work.

The current role is narrower and concrete:

- keep SQLite as runtime lifecycle/read-model/index authority;
- keep paper/study/publication/artifact truth in MAS file and controller authority surfaces;
- keep root Git and quest Git out of default MAS workspace/runtime lifecycle;
- preserve restore-proof archive, migration ledger, compatibility export, and explicit archive import rules;
- handle new drift with fresh inventory, archive, restore proof, and verification.

## Current State

| area | current state | owner |
| --- | --- | --- |
| Runtime lifecycle index | `landed` | `artifacts/runtime/runtime_lifecycle.sqlite` and related runtime stores |
| Runtime/event/report history | `landed as index/read model` | MAS runtime lifecycle read-model/index boundary |
| Quest Git retirement | `current projects verified` | migration/cutover ledgers and restore manifests |
| Workspace root Git retirement | `current projects verified` | workspace root Git retirement ledgers |
| MAS-first new workspace layout | `landed` | workspace/bootstrap/profile contracts |
| Explicit archive/import reference | `retained diagnostic` | MAS compatibility/provenance surfaces |
| Live paper truth | `outside SQLite authority` | MAS study/publication/artifact owners |

## Authority Boundary

SQLite may hold:

- runtime lifecycle state, event indexes, run/session summaries, cursor metadata, report indexes, retention action ledgers, archive refs, checksum refs, compatibility export provenance, and projection caches;
- route lineage, workspace allocation, snapshot metadata, revision summaries, and Canvas/progress read models when they are rebuildable from authority surfaces.

SQLite must not hold or authorize:

- medical quality, publication readiness, submission readiness, study truth, controller decision truth, AI reviewer verdict, evidence/review ledger truth, dataset manifest truth, canonical manuscript/package truth, or current-package edit authority.

Files and archives remain authoritative for:

- `publication_eval/latest.json`, `controller_decisions/latest.json`, `study_runtime_status`, `runtime_watch`, study charter, evidence ledger, review ledger, manuscripts, tables, figures, packages, delivery mirrors, dataset manifests, restore manifests, and archive payloads.

## Current Drift Handling

When a current or legacy workspace shows new `.ds`, quest `.git`, root `.git`, old MDS path, runtime payload, or compatibility fallback drift, the handling order is:

1. Fresh inventory: identify state, active run, worker liveness, owner, path class, file/byte counts, remotes/locks/worktrees when Git exists, and authority surfaces touched.
2. Safety gate: live/running/unknown-owner paths are audit-only unless a controller-authorized or operator-confirmed safe window exists.
3. Archive and restore proof: produce archive, manifest, sha256, restore command, source path list, and verification result before removal.
4. Compatibility export: preserve explicit read/restore diagnostics when needed.
5. Verify: prove current MAS status/progress/runtime surfaces still read from MAS authority, not from root Git, quest Git, old `.ds`, or old MDS path.

Do not describe newly discovered drift as “the migration plan is still active” unless the root cause is a live writer or contract regression. Most post-closeout drift is a maintenance event under this P3a guard.

## Relationship To P3 And P2

P3a is a runtime lifecycle foundation for P3. It does not own product entry, MDS code absorb, no-history import, functional monolith closeout, OPL provider cutover, or paper-loop acceptance.

Reusable lessons from P3a may move upward into OPL framework primitives under P2:

- lifecycle ledger patterns;
- artifact locator/index patterns;
- retention and cleanup receipts;
- restore-proof and migration ledger patterns;
- provider cache/index cleanup gates.

When lifted to OPL, these remain framework metadata and receipts. MAS study truth, publication truth, quality truth, and artifact authority stay in MAS.

## Verification And Evidence

Use these evidence surfaces:

- `artifacts/runtime/lifecycle_migration/*.json`;
- workspace root Git retirement ledgers;
- quest Git cutover ledgers;
- restore manifests and sha256 records;
- compatibility export records;
- focused runtime lifecycle and repository hygiene tests;
- live workspace read-only evidence when discussing a particular workspace.

`git status`, Git log, quest Git refs, or old worktree lists are not MAS runtime status sources.

## Historical Content Disposition

The previous long record combined SQLite design rationale, dated workspace closeouts, root/quest Git cutover ledgers, schema sketches, lane tables, and implementation checklists. It has been archived as a full record because those details are useful provenance.

Current readers should use this document for today’s runtime lifecycle boundary and drift process, then open the archived full record only when they need dated migration evidence, old lane names, schema rationale, or exact workspace closeout details.
