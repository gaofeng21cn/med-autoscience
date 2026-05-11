# Documentation Portfolio Governance v2

Status: `active docs governance`
Date: `2026-05-09`
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
| `docs/runtime/` | runtime contracts, control, projections, display, active designs | Completed implementation plans move to `docs/history/runtime/`. |
| `docs/program/` | active execution queue | Keep small: program README, portfolio queue, MAS absorb program, runtime lifecycle SQLite program. |
| `docs/capabilities/` | capability-family docs | Each family owns its board, contracts, catalogs, plans, provenance, and history links. |
| `docs/references/` | support references | Group by `mainline`, `integration`, `mds-parity`, `positioning`, `verification`, `workspace`, and `med-deepscientist`. |
| `docs/policies/` | stable internal rules | Group by `quality`, `study-workflow`, `runtime-governance`, and `repo-ops`; do not store one-off plans here. |
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
| `docs/capabilities/medical-display/` | Medical display owner | Portfolio, board, contracts, catalogs, plans, and provenance are separated in subdirectories. |

## Archive Rule

Archive a document when it is a completed implementation plan, dated intake
snapshot, retired board, superseded roadmap, activation package, or process
draft. The archived file must be reachable through `docs/history/**/README*`
and must point readers back to the current owner surface when needed.

## Monolith And OPL Alignment Rule

After the MAS monolith closeout, documentation updates must classify legacy
runtime material by current lifecycle role before editing prose:

- Active MAS docs may describe MDS / DeepScientist only as historical fixture,
  explicit archive import, backend audit, upstream intake, source provenance, or
  parity reference.
- Active MAS docs may describe Hermes only as a legacy/optional provider,
  executor/proof lane, or historical migration context unless OPL provider
  evidence promotes a newer role.
- OPL should be described as the Codex-first, stage-led agent runtime framework:
  it owns stage attempts, queue/wakeup, retry/dead-letter, approval transport,
  receipt/projection, and shared lifecycle/index primitives; it does not own MAS
  medical truth.
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

## Machine Boundary

Human-readable docs do not own MAS study truth, runtime truth, publication
readiness, controller decisions, or artifact authority. Those live in stable
runtime/controller/schema/generated surfaces. Docs may explain and navigate
those surfaces, but they must not become a second truth source.

Allowed machine uses of docs paths are limited to docs tooling, documentation
classification, generated human links, or explicit semantic references such as
`human_doc:*`, `runtime:*`, `program:*`, and `policy:*`.
