# Med Autoscience Repository Agent Contract

This root `AGENTS.md` is the repository-native contract for direct sessions that enter from the project root, including Codex App and plain Codex sessions.

Codex is the only active workflow entry in this repository. Historical OMX materials are retained only as legacy references and must not be treated as startup/run requirements.

## Scope

Apply this file to the repository root and all descendants unless a deeper `AGENTS.md` overrides it for a narrower subtree.

## Project Truth

The authoritative project truth contract lives at `contracts/project-truth/AGENTS.md`.
Read that file first whenever repository-specific goals, architecture priorities, mutation rules, or domain constraints matter.

## Working Agreements

- Keep diffs small, reviewable, and reversible.
- Prefer deletion over addition when simplification preserves behavior.
- Reuse existing patterns and utilities before introducing new abstractions.
- Do not add new dependencies without explicit justification.
- Run the relevant tests, type checks, and validation commands before claiming completion.
- Final reports should include what changed and any remaining risks or known gaps.

## Worktree Discipline

- Heavy or long-running implementation work must run in an isolated worktree created from current `main`.
- Keep the shared root checkout on `main` for light reads, planning, review, absorb-to-`main`, push, and cleanup; do not let it become the long-running owner checkout.
- Allow at most one active long-running mainline per worktree. If multiple long-running lanes are needed, create multiple worktrees.
- Before starting a new long-running lane, ensure the owner worktree is clean and free of stale local runtime state.
- After the lane stops, either absorb the verified commits back to `main` or explicitly abandon the lane, then remove its worktree/branch and clear related tmux/session state.
- Do not rely on session-only isolation to prevent hook interference; use physical worktree isolation.

## Test Surface Governance

- `make test-fast` is the default developer slice and must exclude both `meta` and `display_heavy` suites.
- `make test-meta` and `make test-display` are explicit, marker-driven lanes; do not replace them with filename heuristics or fold them back into the default smoke path.
- `make test-full` is the clean-clone baseline and release gate; repo-tracked docs, workflows, and operator instructions should reference it when they mean the full suite.
- When changing test commands or marker allocation, update `Makefile`, `pyproject.toml`, `README*`, CI/release workflows, and command-surface tests together.

## Local State

- `.codex/` and legacy `.omx/` are local tooling state and must remain untracked.
- `.omx/` is legacy historical state only; do not use it as an active workflow entry.
