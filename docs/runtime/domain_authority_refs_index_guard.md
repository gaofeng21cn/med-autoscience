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
| Runtime state canonical surface | `materialized_canonical_runtime_state` | `runtime/quests/<quest>/artifacts/runtime/state/runtime_state.json`; `.ds/runtime_state.json` is legacy compatibility/provenance only |
| MAS refs-only state index pilot | `opt_in_storage_maintenance_pilot` | `artifacts/runtime/mas_refs_only_state_index_pilot.sqlite` indexes cursor/index/lifecycle/outbox/receipt refs only, replacing only the current `quest_root` slice on rebuild |
| Restore-proof canary | `bounded_retain_source_canary` | `artifacts/runtime/runtime_storage_maintenance/restore_proof_canary/*.json` and bounded archive/restore proof refs |
| Restore-proof compaction | `stopped_cold_bucket_compaction_available` | `.ds/runs` and `.ds/codex_homes` may be sharded into restore-proof archives after explicit cold-window gate |
| Runtime/event/report history | `opl_owned_or_provenance_only` | OPL attempt/provider ledger for runtime truth; MAS refs index for owner receipts/blockers only |
| Quest Git retirement | `current projects verified` | migration/cutover ledgers and restore manifests |
| Workspace root Git retirement | `current projects verified` | workspace root Git retirement ledgers |
| MAS-first new workspace layout | `landed` | workspace/bootstrap/profile contracts |
| Explicit archive/import reference | `retained diagnostic` | MAS archive/provenance surfaces |
| Live paper truth | `outside SQLite authority` | MAS study/publication/artifact owners |

## 当前机器合同入口

本文只做人读 guard。当前机器合同和回归证据入口是：

- `med_autoscience.runtime_protocol.domain_authority_refs_index.domain_authority_refs_index_contract()`：声明 `role=refs_only_domain_authority_receipt_index`、`generic_persistence_owner=one-person-lab`、`generic_runtime_owner=one-person-lab`，并固定 `stores_body=false`、`stores_domain_truth=false`、`runtime_control_owner=one-person-lab`；
- `med_autoscience.runtime_protocol.quest_state.materialize_runtime_state_surface()`：把 legacy `.ds/runtime_state.json` 物化到 canonical `artifacts/runtime/state/runtime_state.json`，报告只含路径、sha256、status 和 blocker，不含 runtime-state JSON body，不删除 legacy 文件；
- `contracts/state_index_kernel_adoption.json#/mas_refs_only_pilot` 和 `contracts/stage_artifact_kernel_adoption.json#/state_index_kernel_adoption/mas_refs_only_pilot`：声明 MAS 当前只在 `runtime maintain-storage --refs-only-state-index-pilot` / `runtime storage-audit --apply --refs-only-state-index-pilot` 下写 opt-in SQLite pilot，路径为 `artifacts/runtime/mas_refs_only_state_index_pilot.sqlite`，只索引 cursor / index / lifecycle / outbox / receipt refs；
- `contracts/functional_privatization_audit.json` 和 `contracts/test-lane-manifest.json`：把 `domain_authority_refs_index` 固定为 domain authority refs 分类，不允许写回 generic runtime lifecycle / persistence owner；
- `tests/test_runtime_protocol_quest_state.py`、`tests/test_runtime_storage_maintenance_cases/runtime_refs_only_state_index_pilot.py`、`tests/test_runtime_storage_maintenance_cases/runtime_storage_maintenance_compaction_git.py`、`tests/test_stage_artifact_kernel_adoption_contract.py`、`tests/test_opl_family_persistence_adapter.py`、`tests/test_opl_standard_pack.py`、`tests/test_test_lane_governance.py`：覆盖 runtime state canonical materialization、refs-only pilot、adoption surface、standard-agent purity boundary 和 test-lane manifest mirror。

这些入口是当前 truth surface；本文的职责是解释边界和漂移处理，不新增 SQLite schema、runtime lifecycle engine、queue、attempt ledger 或 provider state 语义。

## Authority Boundary

MAS domain authority refs SQLite may hold:

- owner receipt refs、typed blocker refs、domain intent / owner-route locator refs、artifact/source/status locator refs、cleanup/terminal gate receipt refs、archive refs、checksum refs、migration/export provenance 和 projection cache refs;
- route lineage、workspace allocation、snapshot metadata、revision summaries 和 Canvas/progress projection refs，仅当它们可从 authority surfaces 重建且不承担 runtime attempt truth。

MAS domain authority refs SQLite must not hold or authorize:

- OPL queue / attempt ledger / provider state / retry-dead-letter / worker liveness / current control state;
- medical quality, publication readiness, submission readiness, study truth, controller decision truth, AI reviewer verdict, evidence/review ledger truth, dataset manifest truth, canonical manuscript/package truth, or current-package edit authority.

MAS refs-only state index pilot has the same authority boundary. It may store path refs, file hashes, byte size, mtime, ref family, index version and rebuild epoch for canonical `artifacts/runtime/state/runtime_state.json`, legacy `.ds/runtime_state.json`, runtime cursor/index files, paper work-unit outbox receipts and runtime owner/dispatch receipt refs. Canonical runtime state is indexed as `lifecycle`; legacy `.ds/runtime_state.json` is indexed as `legacy_lifecycle` when canonical exists, and as `lifecycle` only during pre-materialization compatibility. A rebuild replaces only rows for the current `quest_root`, so one workspace SQLite can accumulate refs for multiple paper quests without cross-quest deletion. It must not store JSON body, manuscript body, artifact body, owner receipt authority, publication eval body, controller decision body, evidence/review ledger body, memory body or quality verdict. The pilot row count is not a stage-completion, paper-progress, publication-ready, artifact-authority or restore-ready signal.

Stable commands:

- `medautosci runtime maintain-storage --profile <profile> --study-id <study_id> --refs-only-state-index-pilot`
- `medautosci runtime maintain-storage --profile <profile> --study-id <study_id> --refs-only-state-index-pilot --refs-only-state-index-only`
- `medautosci runtime maintain-storage --profile <profile> --quest-root <quest_root> --refs-only-state-index-pilot`
- `medautosci runtime maintain-storage --profile <profile> --quest-root <quest_root> --refs-only-state-index-pilot --refs-only-state-index-only`
- `medautosci runtime maintain-storage --profile <profile> --study-id <study_id> --restore-proof-canary --restore-proof-canary-entry-limit <n> --restore-proof-bucket <bucket> --include-parked-controller-stop`
- `medautosci runtime maintain-storage --profile <profile> --quest-root <quest_root> --restore-proof-canary --restore-proof-canary-entry-limit <n> --restore-proof-bucket <bucket> --include-parked-controller-stop`
- `medautosci runtime maintain-storage --profile <profile> --study-id <study_id> --restore-proof-compaction --restore-proof-bucket runs --restore-proof-bucket codex_homes --restore-proof-max-shards <n> --include-parked-controller-stop`
- `medautosci runtime maintain-storage --profile <profile> --quest-root <quest_root> --restore-proof-compaction --restore-proof-bucket runs --restore-proof-bucket codex_homes --restore-proof-max-shards <n> --include-parked-controller-stop`
- `medautosci runtime maintain-storage --profile <profile> --legacy-ds-root <path/to/.ds> --restore-proof-compaction --restore-proof-bucket runs --restore-proof-bucket codex_homes --restore-proof-max-shards <n>`
- `medautosci runtime storage-audit --profile <profile> --all-studies --apply --refs-only-state-index-pilot`

Use `--refs-only-state-index-only` when the purpose is to rebuild the refs-only SQLite pilot on a very large `.ds` tree. In that mode MAS intentionally skips legacy backend storage maintenance and recursive size summaries, records `legacy_backend_status=skipped_by_refs_only_state_index_only`, and writes `size_before` / `size_after` as explicit skipped summaries. This is the preferred live canary path for million-file runtime roots because it indexes refs without doing physical compaction, GC, body migration, paper mutation or artifact cleanup.

Every `runtime maintain-storage` call also attempts body-free canonical runtime-state materialization before runtime snapshot and SQLite indexing. The materialization path copies a valid legacy `.ds/runtime_state.json` into `artifacts/runtime/state/runtime_state.json`; if canonical already exists with the same hash it reports `already_materialized`, and if canonical has diverged with newer/same mtime it reports `canonical_runtime_state_diverged` rather than overwriting. This is a migration bridge away from the `.ds` name, not a permission to delete legacy `.ds/runtime_state.json` while direct legacy readers still exist.

Use `--restore-proof-canary` when the purpose is to prove archive/restore mechanics on a bounded sample before any physical slimming. This canary samples at most `--restore-proof-canary-entry-limit` files or symlinks per selected runtime bucket, writes a bounded archive, source manifest, restore proof, plan and receipt under `artifacts/runtime/runtime_storage_maintenance/restore_proof_canary/`, and retains all source runtime payload. It records `actual_release_bytes=0`, `source_retained=true`, `mutated_runtime_payload=false`, and `pruned_paths=[]`. For parked `paused` / `stopped` roots it still requires `--include-parked-controller-stop`; do not use `--allow-live-runtime` to bypass this gate.

Use `--restore-proof-compaction` only for an explicit stopped-cold bucket scope. `runs` and `codex_homes` are compacted as child-level source groups, not as one giant archive, so `--restore-proof-max-shards <n>` can process a bounded shard window and be rerun until `remaining_source_group_count=0`. Each shard writes an archive, source manifest, restore proof and body-free `archive_refs` row before deleting the compacted source group. The selected bucket directory is removed only when it becomes empty. This is physical runtime payload compaction, not refs-only indexing, paper progress, publication readiness, artifact authority, memory cleanup or study truth mutation.

If a selected bucket contains empty child directories after all payload-bearing groups were already archived, rerun the same `--restore-proof-compaction` command. The `nothing_to_archive` result still prunes empty child directories and then the empty selected bucket directory. It must not remove any child that contains a file, symlink or other payload.

Use `--legacy-ds-root` only for historical archive or nested bare `.ds` roots that no longer have a valid `quest.yaml` owner surface. It still requires `--restore-proof-compaction`, writes archive tarballs, source manifests, restore proofs, owner-root `domain_authority_refs.sqlite` rows and workspace-level refs-only rows, and refuses `.ds` roots outside the selected profile workspace. It must not be used as a shortcut for active quest runtime roots that can be handled with `--quest-root`.

The safe live sequence for million-file `.ds` roots is:

1. `--refs-only-state-index-pilot --refs-only-state-index-only` to rebuild refs-only SQLite without recursive size scan.
2. `--restore-proof-canary --restore-proof-canary-entry-limit <small n> --restore-proof-bucket runs|codex_homes --include-parked-controller-stop` to produce bounded restore proof while retaining source payload.
3. Sharded `--restore-proof-compaction --restore-proof-max-shards <n>` after owner/operator confirms the stopped-cold window and target bucket scope.

Verification:

- `scripts/run-pytest-clean.sh tests/test_runtime_storage_maintenance_cases/runtime_refs_only_state_index_pilot.py -q`
- `scripts/run-pytest-clean.sh tests/test_runtime_storage_maintenance_cases/runtime_restore_proof_canary.py -q`
- `scripts/run-pytest-clean.sh tests/test_cli_cases/runtime_storage_commands.py -q`
- `scripts/run-pytest-clean.sh tests/test_stage_artifact_kernel_adoption_contract.py -q`

Live canary evidence:

- `2026-06-04` DM002 `002-dm-china-us-mortality-attribution` ran `runtime maintain-storage --refs-only-state-index-pilot --refs-only-state-index-only` against `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk`.
- Result: `status=maintained`, `legacy_backend_status=skipped_by_refs_only_state_index_only`, `quest_runtime_before.status=paused`, `quest_runtime_after.status=paused`, `active_run_id=null` before and after, and both size summaries were `status=skipped` with `skip_reason=refs_only_state_index_only`.
- SQLite proof: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/artifacts/runtime/mas_refs_only_state_index_pilot.sqlite` existed, table `small_file_refs` had 3 rows, ref families were `lifecycle=1` and `outbox=2`, `body_included` min/max were both `0`, and schema columns did not include `body`, `content` or `payload`.
- Report refs: `studies/002-dm-china-us-mortality-attribution/artifacts/runtime/runtime_storage_maintenance/20260604T004827Z.json` and `studies/002-dm-china-us-mortality-attribution/artifacts/runtime/runtime_storage_maintenance/latest.json`.
- Read this as storage/index evidence only. It is not a paper-progress, publication-ready, stage-completion, artifact-authority, restore-ready, retention, GC or compaction receipt.

Live compaction evidence:

- `2026-06-04` DM002 `002-dm-china-us-mortality-attribution` ran sharded restore-proof compaction against the stopped quest root `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/runtime/quests/002-dm-china-us-mortality-attribution`.
- Scope was limited to `.ds/runs` and `.ds/codex_homes`; `study.yaml`, `publication_eval/latest.json`, `controller_decisions/latest.json`, manuscripts, paper source, memory body and artifact bodies were not compaction targets.
- Fresh physical check after compaction read `.ds/runs` missing and `.ds/codex_homes` missing.
- `domain_authority_refs.sqlite` contained `archive_ref_total=1811` for that quest root, with `runs=1191`, `codex_homes=620`, `other=0`, all as refs-only archive provenance.
- Restore-proof archive root was `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/runtime/quests/002-dm-china-us-mortality-attribution/artifacts/runtime/runtime_storage_maintenance/restore_proof_archives/runtime_bucket_compaction`, observed size `19G`.
- OPL Stage Folder closeout was materialized under `medautoscience/state-index-canary/dm-cvd/dm002-runtime-state-index`, stage `runtime_payload_compaction`, attempt `compaction-2026-06-04`, owner receipt ref `mas-runtime-storage-payload-compaction:002-dm-china-us-mortality-attribution:20260604T032820Z`.
- Read this as runtime payload storage closure for the selected cold buckets. It is not paper progress, publication-ready status, owner-route success, domain-ready status, memory acceptance, artifact mutation authorization or production readiness.

Full historical runtime payload closeout evidence:

- `2026-06-04` all discovered MAS `.ds` quest roots and historical `.ds` archive residues under the known local MAS workspaces were inventoried. Coverage included AS biologics, DM-CVD, NF-PitNET, Obesity, the legacy DM003 `ops/med-the study team` orphan path, `runtime/archives/legacy_mds/**/.ds`, and nested `.ds/python_pycache/**/.ds` payload residues.
- Fresh physical verification after compaction found no remaining `.ds/runs` or `.ds/codex_homes` bucket under `/Users/gaofeng/workspace/LinZM/as_biologics_workspace`, `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk`, `/Users/gaofeng/workspace/Yang/NF-PitNET`, or `/Users/gaofeng/workspace/Yang/Obesity`.
- Archive refs by quest root: DM002 `1811` (`runs=1191`, `codex_homes=620`), DM003 `1841` (`runs=1349`, `codex_homes=492`), DM004 `8` (`runs=4`, `codex_homes=4`), Obesity `1637` (`runs=968`, `codex_homes=669`). Other discovered roots had no `runs` / `codex_homes` payload to compact.
- Legacy archive / nested `.ds` follow-through added `364` archive refs across historical owner roots. Final refs-only archive row scan across the four local MAS workspaces read `remaining_runs_or_codex_homes_count=0`, `archive_ref_row_total=6025`, and `archive_ref_quest_root_count=14`.
- Refs-only SQLite index-only maintenance was run for the three newly compacted payload roots before physical compaction: DM003, DM004 and Obesity. The SQLite role remains refs-only and body-free.
- OPL Stage Folder closeout was materialized under `medautoscience/state-index-full-migration/all-workspaces/historical-runtime-payload-compaction`, stage `all_runtime_payload_compaction`, attempt `full-migration-2026-06-04`, owner receipt ref `mas-runtime-storage-full-payload-compaction:all-discovered-runtime-quests:20260604T044000Z`.
- Read this as full local historical runtime payload storage closure for discovered `runs` / `codex_homes` buckets. It is not paper progress, publication-ready status, owner-route success, domain-ready status, memory acceptance, artifact mutation authorization or production readiness.

Canonical runtime state and active cache closeout evidence:

- `2026-06-04` live maintenance materialized canonical `artifacts/runtime/state/runtime_state.json` for all active Yang MAS quest roots found under DM-CVD, Obesity and NF-PitNET: four DM-CVD quests, one Obesity quest and four NF-PitNET quests.
- The three workspace-level refs-only SQLite pilots were rebuilt after the quest-slice indexing fix. Direct SQLite verification read DM-CVD `quest_count=4` with `family_counts={"lifecycle":4,"legacy_lifecycle":4}`, Obesity `quest_count=1` with `family_counts={"lifecycle":1,"legacy_lifecycle":1}`, and NF-PitNET `quest_count=4` with `family_counts={"lifecycle":4,"legacy_lifecycle":4}`. All had `body_included_values=[0]`.
- Active runtime cache residue was compacted by restore-proof path for DM002, DM003, DM004 and Obesity `python_pycache` buckets. Fresh Yang-wide physical check after follow-through read no `.ds/runs`, `.ds/codex_homes` or `.ds/python_pycache` buckets.
- Yang-wide `.git` count after full cleanup was `11`. The remaining entries are historical archive / uv-cache / framework-reference / PPT roots, not current MAS runtime payload explosion. Removing them needs a separate restore-proof or explicit archive-retirement policy; they are not paper progress blockers.
- Fresh `study progress` for DM002 and DM003 after the storage migration succeeded through the MAS profile and new runtime-state surface. A later `stage-artifact-materialize --apply` run materialized both studies into `artifacts/stage_outputs/<stage_id>/`: each study now has 8 stage directories, 40 stage-native refs files, and 8 refs-only `stage_artifact_delta` rows in `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/artifacts/runtime/domain_authority_refs.sqlite.paper_work_unit_receipts`. Fresh `stage_artifact_index` reads both studies as `current_stage=08-publication_package_handoff`, all 8 stages `artifact_delta_present`, and `next_owner_action={}`. This closes the stage-folder missing-output tail; it is still not a paper closure, quality verdict, publication-ready status, artifact mutation authorization or current-package update.
- After explicit user wakeup, OPL provider readiness was repaired and the current DM002/DM003 dispatch tasks were approved narrowly, not as a blanket approval of old waiting tasks. Post-approval OPL ticks selected one task per study and admitted running Temporal attempts: DM002 `sat_5d11d86ff9a1ee5b379030ee` for `run_quality_repair_batch`, DM003 `sat_fe0c6a536fc5c9e21bca6389` for `run_gate_clearing_batch`. Owner-route observe projected both as `running_provider_attempt=true`. This proves the migrated workspace can be located and continued through MAS/OPL surfaces; it is not a publication verdict, artifact mutation authorization or paper closure.
- The current paper owner route must be read separately from the stage-folder kernel. A `2026-06-04` fresh `study-progress` read after stage materialization shows DM002 still has runtime envelope `current_stage=queued`, paper stage `publishability_gate_blocked`, next owner `ai_reviewer`, and running proof for `sat_5d11d86ff9a1ee5b379030ee` / `return_to_ai_reviewer_workflow`. The same read shows DM003 has runtime envelope `current_stage=queued`, paper stage `analysis-campaign`, next owner `external_supervisor`, action `run_gate_clearing_batch`, admission pending, and no current running provider proof. These are owner-route / publication-supervision states, not stage-directory missing-output blockers.

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
