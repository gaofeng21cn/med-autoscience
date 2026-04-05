# Med Autoscience Repository Agent Contract

This root `AGENTS.md` is the repository-native contract for direct sessions that enter from the project root, including Codex App and plain Codex sessions.

If the repository is launched through OMX project-scope installation, OMX-specific orchestration lives in `.codex/AGENTS.md` and augments this file without replacing it.

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

## Local State

- `.omx/` and `.codex/` are local tooling state and must remain untracked.
- `.omx/local/AGENTS.local.md` is reserved for machine-specific private overlays.

