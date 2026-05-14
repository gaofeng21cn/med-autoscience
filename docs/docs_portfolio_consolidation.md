# Documentation Portfolio Governance v2

Status: `active docs governance`
Date: `2026-05-11`
Owner: `MedAutoScience`

## Decision

`docs/` is managed as a lifecycle portfolio. The goal is not to preserve every
file in place; maintainers may rewrite, merge, split, move, archive, or delete
documents when the owner, purpose, state, and machine boundary are clearer after
the change.

The stable root set is:

- `README.md` / `README.zh-CN.md`
- `project.md`
- `status.md`
- `architecture.md`
- `invariants.md`
- `decisions.md`
- `docs_portfolio_consolidation.md`

Everything else belongs to a lifecycle directory.

The OPL-family canonical docs taxonomy for managed framework/domain repos is
`active/public/product/runtime/delivery/source/policies/specs/references/history`.
MAS has physically retired the former `docs/program/` and `docs/capabilities/`
active directories. Current program-baton material lives in `docs/active/`;
medical-display capability material lives under `docs/delivery/medical-display/`.
Those retired directory names may appear only in history/provenance records.

## Lifecycle Signals

Every long-lived document must be classifiable by four signals:

| signal | question |
| --- | --- |
| `owner` | Which MAS owner surface maintains this truth? |
| `purpose` | Is this core explanation, runtime/policy reference, program execution, capability-family material, support reference, or history/provenance? |
| `state` | Is it active, active plan, recurring support, landed snapshot, superseded, retired, or provenance-only? |
| `machine boundary` | Is this human-readable prose only, or is there a durable schema/source/contract ID that machines should use instead? |

If any signal is missing, first add the signal or move the document to the
correct lifecycle layer before expanding it.

## Content-Level Consolidation Rule

Documentation lifecycle decisions are content-level decisions. A file can stay
in place while individual sections move to a current owner doc, a policy, a
reference page, or a history record. A file can also be archived while one
still-current section is merged into the active owner surface first.

Maintainers should review documents in this order:

1. Identify the current factual claims, landed evidence, active work, recurring
   support lanes, and historical narrative inside the document.
2. Merge current factual claims into the relevant core doc or owner doc.
3. Keep active work in `docs/active/` only when it still needs execution order,
   owner gates, or closeout evidence.
4. Move recurring learning/support material to `docs/references/` plus dated
   `docs/history/program/` snapshots.
5. Archive superseded plans, date-stamped calibration notes, and retired boards
   after inbound link review.

Public and core entry docs should lead with current state and owner roles. Use
positive wording such as "MAS owns...", "OPL provides...", and "MDS is retained
as..." before adding boundary constraints. Long lists of retired roles belong
in history/reference material or in contract sections that genuinely need a
guardrail.

## Practice Map

MAS adapts mature documentation practice this way:

| practice | MAS mapping |
| --- | --- |
| Diataxis | Core explanation, runtime/policy reference, program execution, capability-family docs, support references, and history/provenance are separated by reader purpose. |
| GitLab topic types | Each subtree has a focused index; link farms belong in README files, not in active owner documents. |
| Microsoft Learn style | Navigation stays short, scannable, and reader-oriented; public-facing docs remain mirrored in English/Chinese where applicable. |
| Write the Docs docs-as-code | Docs move through Git review and lightweight verification; tests may validate durable contracts and paths, not Markdown wording. |

## Directory Roles

| directory | role | lifecycle rule |
| --- | --- | --- |
| `docs/` root | short technical entry plus core truth | Only root README, core five, and this governance file stay here. |
| `docs/active/` | current execution, gap plans, active baton, and program lifecycle portfolio | Current owner for the former `docs/program/` active material: active README, portfolio entry, the P0 target/acceptance owner, P1/P2 active enablers, and P3/P3a landed foundation owner docs. `human_doc:*` remains a semantic ID, not a physical path promise. |
| `docs/public/` | public MAS narrative after the repository home | Keeps user-facing positioning sparse and subordinate to the repository home. |
| `docs/product/` | direct app skill, product-entry, operator/workbench-facing guidance | Does not own study truth or publication verdicts. |
| `docs/runtime/` | runtime contracts, control, projections, display, active designs | Completed implementation plans move to `docs/history/runtime/`. |
| `docs/delivery/` | manuscript, package, submission/export, delivery authority support, and capability-family docs | Domain authority remains in MAS runtime/artifact surfaces. Medical-display capability docs now live at `docs/delivery/medical-display/`; each family owns its board, contracts, catalogs, plans, provenance, and history links. |
| `docs/source/` | workspace/source intake, source readiness, source truth consumption | Keeps source semantics MAS-owned and only generic shell candidates go up to OPL. |
| `docs/policies/` | stable internal rules | Group by `quality`, `study-workflow`, `runtime-governance`, and `repo-ops`; do not store one-off plans here. |
| `docs/specs/` | active technical specs and spec index | Older specs must be explicitly classified active or history before expansion. |
| `docs/references/` | support references | Group by `mainline`, `integration`, `mds-parity`, `positioning`, `verification`, `workspace`, and `med-deepscientist`. |
| `docs/history/` | dated snapshots, provenance, retired boards, process drafts | History cannot own active backlog, runtime truth, publication truth, or policy authority. |

## Current Subtree Rules

| subtree | owner | rule |
| --- | --- | --- |
| `docs/runtime/contracts/` | Runtime OS / controller owners | Stable contract surfaces. |
| `docs/runtime/control/` | Runtime control owners | Controller, supervisor, orchestration, and runtime action surfaces. |
| `docs/runtime/projections/` | Runtime/Product projection owners | Read models and user-visible projections only. |
| `docs/runtime/display/` | Product projection + Runtime OS | Portal and Live Console display contracts; no runtime authority writes. |
| `docs/runtime/designs/` | Named design owner | Active designs pending contract/test promotion. |
| `docs/references/mds-parity/` | MAS/MDS parity owner | Behavior/capability parity oracle and cleanroom UX reference. |
| `docs/policies/runtime-governance/` | Runtime governance owner | Long-lived runtime and MAS/MDS owner-boundary rules. |
| `docs/delivery/medical-display/` | Medical display owner | Portfolio, board, contracts, catalogs, plans, and provenance are separated in subdirectories. |

## Archive Rule

Archive a document when it is a completed implementation plan, dated intake
snapshot, retired board, superseded roadmap, activation package, or process
draft. The archived file must be reachable through `docs/history/**/README*`
and must point readers back to the current owner surface when needed.

## Monolith And OPL Alignment Rule

After the MAS monolith closeout, documentation updates must classify legacy
runtime material by current lifecycle role before editing prose:

- The OPL-family global development reference is
  `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.zh-CN.md`.
  It owns global framework targets, cross-repo gap ordering, shared primitive
  absorption, App/workbench targets, and same-name docs taxonomy. MAS docs only own
  MAS target state, MAS gaps, MAS authority boundaries, and MAS-to-OPL
  absorption candidates.
- Active MAS docs describe MDS / DeepScientist as historical fixture, explicit
  archive import, backend audit, upstream intake, source provenance, or parity
  reference.
- Active MAS docs describe Hermes as a legacy/optional provider, executor/proof
  lane, or historical migration context unless OPL provider evidence promotes a
  newer role.
- OPL should be described as the stage-led runtime framework with Agent executors as the minimum execution unit:
  it owns stage attempts, queue/wakeup, retry/dead-letter, approval transport,
  receipt/projection, and shared lifecycle/index primitives; MAS owns medical
  truth, quality verdicts, and artifact authority.
- MAS remains the medical paper/research domain agent. `Stage` means a large
  task step, and `Codex CLI` remains the default concrete executor inside MAS
  stages unless a MAS route selects another executor.
- Old WebUI, daemon, external-runtime cutover, and development-plan material
  that is no longer active belongs in `docs/history/**` or `docs/references/**`
  with a pointer back to the current owner surface.

Before moving or deleting a document:

1. Search inbound references with `rg`.
2. Replace active links with the current owner surface or history path.
3. If code/tests depend on prose paths, replace that dependency with a semantic
   ID, schema, source path, or durable JSON surface unless it is docs tooling.
4. Run `git diff --check` and the relevant path/contract tests.

## Program Portfolio Rule

`docs/active/` is read as a target/enabler/foundation map:

| role | current MAS document role |
| --- | --- |
| `content_level_execution_map` | `current_development_lines.md` maps the framework-first execution order, current content lines, downgraded/outdated material, merge/absorb rules, priority, and done signals. |
| `target_acceptance` | `ai_first_paper_autonomy_closure_program.md` defines the paper-autonomy outcome contract and live-soak acceptance criteria. |
| `product_enabler` | `opl_app_mas_runtime_workbench_program.md` turns the target into an OPL App Runtime Workbench experience. |
| `framework_enabler` | `opl_temporal_mas_runtime_retirement_program.md` aligns MAS runtime-adjacent obligations with the OPL stage-led framework with Agent executors as the minimum execution unit. |
| `cross_cutting_stage_form` | `stage_surface_standardization_program.md` keeps stage prompts, skills, tools, knowledge packets, closeout memory, quality packs, and OPL stage descriptors in one maintainable form. |
| `landed_foundation` | `mas_single_project_mds_absorb_program.md` and `runtime_lifecycle_sqlite_migration_program.md` preserve monolith, MDS provenance, runtime lifecycle, restore-proof, and compatibility guard evidence. |

When a program document contains mixed material, split the content role before
editing: current target language stays in the target owner, implementation
dependencies move to P1/P2 or OPL, landed evidence stays as guard/provenance,
recurring support moves to references plus dated history snapshots, and retired
route narratives move to history/tombstones.

When a MAS program item is actually a generic framework primitive, record the
MAS evidence and handoff boundary here, then move the implementation owner to
OPL. Do not keep a parallel MAS plan for provider runtime, generic queue,
memory locator/index, artifact lifecycle, workbench shell, route/review
projection, or observability primitives once the owner is OPL.

## Machine Boundary

Human-readable docs do not own MAS study truth, runtime truth, publication
readiness, controller decisions, or artifact authority. Those live in stable
runtime/controller/schema/generated surfaces. Docs may explain and navigate
those surfaces, but they must not become a second truth source.

Allowed machine uses of docs paths are limited to docs tooling, documentation
classification, generated human links, or explicit semantic references such as
`human_doc:*`, `runtime:*`, `program:*`, and `policy:*`.

## Test Retirement Rule

Tests must not scan README/docs prose to fail on legacy terms, headings, fixed
phrases, narrative links, or Markdown placement. Retire those tests or move the
guard to `src/`, `contracts/`, `profiles/`, generated templates, CLI/MCP/API
payloads, schemas, manifests, or generated artifact structure.

Legacy MDS / DeepScientist tests are only retained when they guard explicit
archive import, source provenance, backend audit, historical fixtures, parity
oracle behavior, restore diagnostics, or forbidden default authority. They must
not preserve an external MDS dependency or old active product semantics.
