# Documentation Portfolio Consolidation

Status: `active docs governance`
Date: `2026-05-06`
Owner: `MedAutoScience`

## 结论

`docs/` 也应按 portfolio 管理，不能让 active contract、执行计划、历史 intake、参考材料和本地过程稿混在同一阅读层。当前目标不是减少信息，而是让默认阅读路径变短，让历史材料进入 `docs/history/`，让 active owner surface 更清楚。

默认阅读顺序固定为：

1. `docs/README.md` / `docs/README.zh-CN.md`
2. core five：`project.md`、`status.md`、`architecture.md`、`invariants.md`、`decisions.md`
3. active contracts：`runtime/`、`policies/`
4. active program board：`program/program_portfolio_consolidation.md`
5. support references：`references/`
6. historical archive：`history/`

## Directory Roles

| directory | role | active rule |
| --- | --- | --- |
| `docs/` root | public technical entry and core truth | 只保留 README、core five 和 docs portfolio governance。 |
| `docs/runtime/` | runtime contracts and implementation-facing control surfaces | 当前可执行合同、schema、control surface 和 still-active implementation plan 留在这里。已完成 implementation plan 后续迁入 history。 |
| `docs/policies/` | stable internal rules | 保持稳定规则，不放一次性计划或 closeout。 |
| `docs/program/` | active development-plan layer | 只保留 portfolio entry、MAS absorb execution plan、runtime/Git/SQLite subplan；policy、reference、ledger 和 historical records 放到对应目录。 |
| `docs/capabilities/` | capability-family docs | 每个 capability family 应有自己的 active board 和 portfolio map；historical exemplar/intake 迁入 `history/capabilities/`。 |
| `docs/references/` | background, positioning, integration reference | 只放仍有解释价值的 reference，不承载 active execution gate。 |
| `docs/history/` | archived historical records | 只读材料、旧 program、old process plans、完成包和 historical specs。 |
| `docs/history/superpowers/` | legacy local process draft archive | 只保存 repo-tracked 历史 plan/spec；新的本地 AI/Superpowers 草稿默认不跟踪。 |

## Active Root Set

这些文件构成默认 docs truth：

| file | role |
| --- | --- |
| `README.md` / `README.zh-CN.md` | docs entry for technical readers |
| `project.md` | project role and product boundary |
| `status.md` | current operational truth and active tranche |
| `architecture.md` | current architecture and owner boundary |
| `invariants.md` | non-negotiable constraints |
| `decisions.md` | durable decisions and rationale |
| `docs_portfolio_consolidation.md` | docs portfolio governance |

## Active Program Set

The active `docs/program/` set is intentionally small:

| role | files |
| --- | --- |
| directory index | `README.md`, `README.zh-CN.md` |
| portfolio entry and execution queue | `program_portfolio_consolidation.md` |
| execution program | `mas_single_project_mds_absorb_program.md` |
| runtime / Git / SQLite subprogram | `runtime_lifecycle_sqlite_migration_program.md` |

Supporting material lives outside `docs/program/`:

| support class | directory |
| --- | --- |
| stable operating rules and gates | `docs/policies/` |
| MDS parity, completion ledger, quality/autonomy narrative, repair references | `docs/references/` |
| MedDeepScientist recurring learning and upstream intake references | `docs/references/med-deepscientist/` |
| retired boards, closeouts, dated recurring intake snapshots, activation packages | `docs/history/program/` |

## Active Capability Set

The active `docs/capabilities/` set is organized by capability family:

| family | active entry | history |
| --- | --- | --- |
| medical display | `capabilities/medical-display/medical_display_portfolio_consolidation.md` | `history/capabilities/medical-display/README.md` |

## Current Archive Actions

This consolidation already moved these tracked files from `docs/program/` to `docs/history/program/`:

| archived family | files |
| --- | --- |
| AI-first closeout | `ai_first_operationalization_closeout.md`, `ai_first_usable_closeout_projection.md`, `ai_first_closeout_handoff_governance.md` |
| DeepScientist dated recurring-lane snapshots | `deepscientist_learning_intake_2026_04_25.md`, `deepscientist_learning_intake_2026_04_28.md`, `deepscientist_learning_intake_2026_04_30.md`, `deepscientist_learning_intake_2026_05_05.md` |
| external / open research dated recurring-lane snapshots | `external_agent_orchestration_learning_intake_2026_04_30.md`, `paper_orchestra_learning_intake_2026_05_02.md`, `open_auto_research_learning_intake_2026_05_04.md` |
| superseded plans | `open_harness_os_freeze_plan.md`, `journal_package_builtins_upgrade_plan.md`, `research_foundry_medical_mainline.md`, `research_foundry_medical_execution_map.md` |
| activation / cutover boards | `integration_harness_activation_package.md`, `hermes_backend_activation_package.md`, `hermes_backend_continuation_board.md`, `upstream_hermes_agent_fast_cutover_board.md` |
| retired MAS/MDS boards | `mas_mds_autonomy_operating_system_program.md`, `mas_mds_unified_enhancement_program.md` |
| capability history | `docs/history/capabilities/medical-display/medical_display_arsenal_history.md`, `medical_display_family_baseline_program.md`, `medical_display_g_pathway_integrated_composite_owner_brief.md`, `paperplothub_exemplar_intake.md`, `paperplothub_exemplar_exhaustion_ledger.md` |
| process drafts | `docs/history/superpowers/plans/`, `docs/history/superpowers/specs/` |

Current support relocations:

| target layer | files |
| --- | --- |
| `docs/policies/` | `external_runtime_dependency_gate.md`, `mainline_integration_and_cleanup.md`, `manual_runtime_stabilization_checklist.md`, `mas_mds_owner_boundary_contract.md`, `merge_and_cutover_gates.md`, `repository_ci_preflight.md` |
| `docs/references/` | `mas_single_project_quality_and_autonomy_mainline.md`, `mds_capability_parity_matrix.md`, `plan_completion_ledger.md`, `project_repair_priority_map.md`, `real_study_relaunch_verification.md` |
| `docs/references/med-deepscientist/` | DeepScientist recurring learning, method, provenance, deconstruction, and upstream intake references |

If business code or behavior tests still reference a narrative docs path, treat that as a migration bug: retire the machine path dependency first, replace it with a stable ref or durable surface, then archive the narrative file when links are reviewed. Docs tooling may still classify `docs/` paths as documentation-only without reading Markdown prose as truth.

## Future Consolidation Candidates

The next cleanup waves should be explicit and small:

| area | candidate action | blocker |
| --- | --- | --- |
| `docs/program/` future board requests | admit only through `program/program_portfolio_consolidation.md` | reject duplicate boards when an existing active owner doc is sufficient |
| `docs/runtime/` implementation plans | move landed implementation plans to `history/runtime/` | verify corresponding runtime contract is active and implementation is landed |
| `docs/capabilities/medical-display/` | continue through `medical_display_portfolio_consolidation.md` | preserve active display platform and audit contracts |
| `docs/references/` positioning docs | merge superseded positioning docs into fewer reference entries | avoid losing historical naming rationale |
| `docs/history/superpowers/` | keep as historical archive only | do not track new local process drafts |

## Archive Rule

1. Active truth stays in root/core, runtime, policies, and active program docs.
2. Historical closeout, dated recurring intake snapshot, activation package, old roadmap, and process draft move to `history/`; the recurring lane owner remains in `status` / `references`.
3. Before moving a file, search inbound links with `rg` and update links or leave the file in place.
4. Code and tests must not treat `docs/**` files as machine-readable authority, quality truth, runtime truth, policy truth, or regression oracle. Business/runtime surfaces should use stable ids such as `program:*`, `policy:*`, `runtime:*`, `core:*`, or durable JSON/schema surfaces.
5. Narrow exceptions are allowed only for docs tooling: classifying changed `docs/` paths as documentation-only, generating a tracked docs asset, or rendering a human-readable link. These exceptions must not inspect Markdown prose as behavior truth.
6. Do not let code or behavior tests keep historical docs in active locations. Retire machine-readable docs path dependencies first, unless the code is explicitly docs tooling.
7. Do not use tests to lock Markdown wording, headings, or prose. Docs consolidation verification is `git diff --check`, link/path spot-checks, and human review.
