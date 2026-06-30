# Data Lifecycle CLI Contract

Owner: `MedAutoScience`
Purpose: `Define the minimal MAS read-only data lifecycle command boundary.`
State: `active_runtime_support`
Machine boundary: Human-readable contract support only; executable truth remains in `medautosci data-lifecycle ...` JSON output, controller source, tests, and runtime/owner receipts.

## Boundary

`medautosci data-lifecycle inspect --workspace-root <path> --format json` is a read-only workspace lifecycle projection. It scans only management surfaces needed for operator review:

- `runtime/` and `runtime/archives/`
- `archive/` or `archives/`
- `artifacts/runtime/`
- `studies/<study-id>/artifacts/`
- local tool cache directories such as `.pytest_cache`

The command always skips `data/datasets/` as the current clinical data asset authority plane. Dataset bodies are not generic cleanup residue, runtime cache, or artifact projections.

`medautosci data-lifecycle closeout --workspace-root <path> --dry-run --format json` derives a candidate closeout plan from the same read-only scan. It does not delete files, write receipts, mutate runtime queues, compact SQLite files, or mark runtime/artifact readiness.

## Output Semantics

The JSON surface exposes:

- `management_mode`: owner split for MAS projection, OPL/provider runtime, OPL physical cleanup, and `data/datasets` exclusion.
- `lifecycle_gaps`: missing lifecycle management surfaces, such as a missing restore index for runtime archives.
- `cleanup_candidates`: bounded directory/file candidate refs classified as `runtime`, `archive`, `artifact`, or `cache`, with aggregate `bytes`, `mib` and `file_count`.
- `mutation_policy`: `read_only=true`, `writes_workspace=false`, and `physical_cleanup_performed=false`.

These outputs are operator evidence and owner handoff inputs. They are not publication readiness, paper progress, artifact mutation authority, owner receipt, or physical cleanup authorization.
