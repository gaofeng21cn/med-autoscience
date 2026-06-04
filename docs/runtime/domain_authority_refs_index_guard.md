# Domain Authority Refs Index Guard

Status: `standard_agent_purity_guard`
Date: `2026-05-26`
Owner: `MedAutoScience domain authority refs boundary`
Purpose: `domain_authority_refs_no_runtime_lifecycle_resurrection_guard`
State: `active_support`
Machine boundary: 本文是人读 owner / provenance guard。机器真相继续归 OPL current control state / provider attempt ledger、MAS domain authority refs index、owner receipts、typed blockers、artifact/source/quality refs、migration ledgers、restore indexes、archive manifests、runtime/controller surfaces 和 live workspace evidence。

完整历史记录：[2026-05-08 runtime lifecycle SQLite migration full record](../history/program/runtime_lifecycle_sqlite_migration_program_2026_05_08_full_record.md)。

## 当前定位

本文是旧 runtime lifecycle SQLite 退役后的 active guard，不再是 broad planning board，也不再把 MAS SQLite / read-model / lifecycle surface 写成当前 runtime owner。它只保存 domain authority refs index、SQLite/file boundary、root/quest Git retirement、restore-proof archive 和 drift handling 的当前 guard。

当前职责：

- SQLite 只可作为 MAS domain authority refs index：owner receipt refs、typed blocker refs、artifact/source/status locator refs、restore/archive provenance refs；
- paper / study / publication / artifact truth 留在 MAS file authority 与 controller authority surfaces；
- root Git 和 quest Git 不回到默认 MAS workspace/runtime lifecycle，也不作为 OPL stage/runtime attempt truth；
- restore-proof archive、migration ledger、lifecycle export 和 explicit archive import 规则继续保留；
- 新 drift 通过 current inventory、archive、restore proof 和 verification 处理。

## 当前状态

| 面 | 当前状态 | owner |
| --- | --- | --- |
| Domain authority refs index | `standard_agent_refs_index` | `artifacts/runtime/domain_authority_refs.sqlite` and body-free refs |
| MAS refs-only state index pilot | `opt_in_storage_maintenance_pilot` | `artifacts/runtime/mas_refs_only_state_index_pilot.sqlite` indexes cursor/index/lifecycle/outbox/receipt refs only |
| Runtime/event/report history | `opl_owned_or_provenance_only` | OPL attempt/provider ledger for runtime truth; MAS refs index for owner receipts/blockers only |
| Quest Git retirement | `current projects verified` | migration/cutover ledgers and restore manifests |
| Workspace root Git retirement | `current projects verified` | workspace root Git retirement ledgers |
| MAS-first new workspace layout | `landed` | workspace/bootstrap/profile contracts |
| Explicit archive/import reference | `retained diagnostic` | MAS archive/provenance surfaces |
| Live paper truth | `outside SQLite authority` | MAS study/publication/artifact owners |

## 当前机器合同入口

本文只做人读 guard。当前机器合同和回归证据入口是：

- `med_autoscience.runtime_protocol.domain_authority_refs_index.domain_authority_refs_index_contract()`：声明 `role=refs_only_domain_authority_receipt_index`、`generic_persistence_owner=one-person-lab`、`generic_runtime_owner=one-person-lab`，并固定 `stores_body=false`、`stores_domain_truth=false`、`runtime_control_owner=one-person-lab`；
- `contracts/state_index_kernel_adoption.json#/mas_refs_only_pilot` 和 `contracts/stage_artifact_kernel_adoption.json#/state_index_kernel_adoption/mas_refs_only_pilot`：声明 MAS 当前只在 `runtime maintain-storage --refs-only-state-index-pilot` / `runtime storage-audit --apply --refs-only-state-index-pilot` 下写 opt-in SQLite pilot，路径为 `artifacts/runtime/mas_refs_only_state_index_pilot.sqlite`，只索引 cursor / index / lifecycle / outbox / receipt refs；
- `contracts/functional_privatization_audit.json` 和 `contracts/test-lane-manifest.json`：把 `domain_authority_refs_index` 固定为 domain authority refs 分类，不允许写回 generic runtime lifecycle / persistence owner；
- `tests/test_runtime_storage_maintenance_cases/runtime_refs_only_state_index_pilot.py`、`tests/test_stage_artifact_kernel_adoption_contract.py`、`tests/test_opl_family_persistence_adapter.py`、`tests/test_opl_standard_pack.py`、`tests/test_test_lane_governance.py`：覆盖 refs-only pilot、adoption surface、standard-agent purity boundary 和 test-lane manifest mirror。

这些入口是当前 truth surface；本文的职责是解释边界和漂移处理，不新增 SQLite schema、runtime lifecycle engine、queue、attempt ledger 或 provider state 语义。

## Authority Boundary

MAS domain authority refs SQLite may hold:

- owner receipt refs、typed blocker refs、domain intent / owner-route locator refs、artifact/source/status locator refs、cleanup/terminal gate receipt refs、archive refs、checksum refs、migration/export provenance 和 projection cache refs;
- route lineage、workspace allocation、snapshot metadata、revision summaries 和 Canvas/progress projection refs，仅当它们可从 authority surfaces 重建且不承担 runtime attempt truth。

MAS domain authority refs SQLite must not hold or authorize:

- OPL queue / attempt ledger / provider state / retry-dead-letter / worker liveness / current control state;
- medical quality, publication readiness, submission readiness, study truth, controller decision truth, AI reviewer verdict, evidence/review ledger truth, dataset manifest truth, canonical manuscript/package truth, or current-package edit authority.

MAS refs-only state index pilot has the same authority boundary. It may store path refs, file hashes, byte size, mtime, ref family, index version and rebuild epoch for `.ds/runtime_state.json`, runtime cursor/index files, paper work-unit outbox receipts and runtime owner/dispatch receipt refs. It must not store JSON body, manuscript body, artifact body, owner receipt authority, publication eval body, controller decision body, evidence/review ledger body, memory body or quality verdict. The pilot row count is not a stage-completion, paper-progress, publication-ready, artifact-authority or restore-ready signal.

Stable commands:

- `medautosci runtime maintain-storage --profile <profile> --study-id <study_id> --refs-only-state-index-pilot`
- `medautosci runtime maintain-storage --profile <profile> --study-id <study_id> --refs-only-state-index-pilot --refs-only-state-index-only`
- `medautosci runtime maintain-storage --profile <profile> --quest-root <quest_root> --refs-only-state-index-pilot`
- `medautosci runtime maintain-storage --profile <profile> --quest-root <quest_root> --refs-only-state-index-pilot --refs-only-state-index-only`
- `medautosci runtime storage-audit --profile <profile> --all-studies --apply --refs-only-state-index-pilot`

Use `--refs-only-state-index-only` when the purpose is to rebuild the refs-only SQLite pilot on a very large `.ds` tree. In that mode MAS intentionally skips legacy backend storage maintenance and recursive size summaries, records `legacy_backend_status=skipped_by_refs_only_state_index_only`, and writes `size_before` / `size_after` as explicit skipped summaries. This is the preferred live canary path for million-file runtime roots because it indexes refs without doing physical compaction, GC, body migration, paper mutation or artifact cleanup.

Verification:

- `scripts/run-pytest-clean.sh tests/test_runtime_storage_maintenance_cases/runtime_refs_only_state_index_pilot.py -q`
- `scripts/run-pytest-clean.sh tests/test_cli_cases/runtime_storage_commands.py -q`
- `scripts/run-pytest-clean.sh tests/test_stage_artifact_kernel_adoption_contract.py -q`

Live canary evidence:

- `2026-06-04` DM002 `002-dm-china-us-mortality-attribution` ran `runtime maintain-storage --refs-only-state-index-pilot --refs-only-state-index-only` against `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk`.
- Result: `status=maintained`, `legacy_backend_status=skipped_by_refs_only_state_index_only`, `quest_runtime_before.status=paused`, `quest_runtime_after.status=paused`, `active_run_id=null` before and after, and both size summaries were `status=skipped` with `skip_reason=refs_only_state_index_only`.
- SQLite proof: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/artifacts/runtime/mas_refs_only_state_index_pilot.sqlite` existed, table `small_file_refs` had 3 rows, ref families were `lifecycle=1` and `outbox=2`, `body_included` min/max were both `0`, and schema columns did not include `body`, `content` or `payload`.
- Report refs: `studies/002-dm-china-us-mortality-attribution/artifacts/runtime/runtime_storage_maintenance/20260604T004827Z.json` and `studies/002-dm-china-us-mortality-attribution/artifacts/runtime/runtime_storage_maintenance/latest.json`.
- Read this as storage/index evidence only. It is not a paper-progress, publication-ready, stage-completion, artifact-authority, restore-ready, retention, GC or compaction receipt.

Files and archives remain authoritative for:

- `publication_eval/latest.json`, `controller_decisions/latest.json`, `progress_projection`, `domain_health_diagnostic`, study charter, evidence ledger, review ledger, manuscripts, tables, figures, packages, delivery mirrors, dataset manifests, restore manifests, archive payloads, owner receipts and typed blockers.

OPL remains authoritative for generic stage/runtime control:

- route hydration、queue、stage attempt ledger、provider start/query、retry/dead-letter、human gate transport、operator `current_control_state` 和 provider completion interpretation.

## Current Drift Handling

When a current or legacy workspace shows new `.ds`, quest `.git`, root `.git`, old MDS path, old runtime lifecycle SQLite payload, or legacy restore import diagnostic drift, the handling order is:

1. Fresh inventory: identify state, owner, path class, file/byte counts, remotes/locks/worktrees when Git exists, and authority surfaces touched. OPL current control state owns live attempt/liveness truth.
2. Safety gate: live/running/unknown-owner paths are audit-only unless an OPL control-state receipt plus MAS owner receipt / typed blocker confirms a safe window.
3. Archive and restore proof: produce archive, manifest, sha256, restore command, source path list, and verification result before removal.
4. Lifecycle export: preserve explicit read/restore diagnostics when needed.
5. Verify: prove current MAS status/progress/domain authority refs still read from MAS authority and OPL current control state, not from root Git, quest Git, old `.ds`, old MDS path, or retired runtime lifecycle stores.

Do not describe newly discovered drift as “the migration plan is still active” unless the root cause is a live writer or contract regression. Most post-closeout drift is a maintenance event under this P3a guard.

## Relationship To P3 And P2

P3a is now a retired-runtime-provenance guard for P3. It does not own product entry, MDS code absorb, no-history import, functional monolith closeout, OPL provider cutover, paper-loop acceptance, or MAS runtime scheduling.

Reusable lessons from P3a may move upward into OPL framework primitives under P2:

- domain authority refs ledger patterns;
- artifact locator/index patterns;
- retention and cleanup receipts;
- restore-proof and migration ledger patterns;
- provider cache/index cleanup gates.

When lifted to OPL, these remain framework metadata and receipts. MAS study truth, publication truth, quality truth, artifact authority, owner receipts and typed blockers stay in MAS.

## Verification And Evidence

Use these evidence surfaces:

- `artifacts/runtime/lifecycle_migration/*.json`;
- workspace root Git retirement ledgers;
- quest Git cutover ledgers;
- restore manifests and sha256 records;
- lifecycle export / domain authority refs records;
- focused domain authority refs and repository hygiene tests;
- live workspace read-only evidence when discussing a particular workspace.

`git status`, Git log, quest Git refs, old worktree lists, retired runtime lifecycle SQLite rows, or recovery-intent snapshots are not MAS runtime status sources.

## Historical Content Disposition

The previous long record combined SQLite design rationale, dated workspace closeouts, root/quest Git cutover ledgers, schema sketches, lane tables, and implementation checklists. It has been archived as a full record because those details are useful provenance.

Current readers should use this document for today’s domain authority refs boundary and retired-runtime drift process, then open the archived full record only when they need dated migration evidence, old lane names, schema rationale, or exact workspace closeout details. The archived full record is provenance only and must not be used to restore MAS-owned runtime lifecycle, read model, scheduler, worker lease or recovery intent control surfaces.
