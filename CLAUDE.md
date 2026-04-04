# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (dev group includes pytest, build, python-docx)
uv sync --frozen --group dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_cli.py

# Run a single test by name
uv run pytest tests/test_cli.py::test_init_workspace

# Build the package
uv run python -m build --sdist --wheel

# Run CLI commands (development)
uv run python -m med_autoscience.cli <command>
# or after install: medautosci <command>

# Key CLI entry points
medautosci doctor --profile <profile.toml>
medautosci init-workspace --workspace-root /path --workspace-name my-disease
medautosci bootstrap --profile <profile.toml>
medautosci watch --runtime-root /path --apply
```

## Architecture

MedAutoScience is a medical research overlay platform — the governance and orchestration layer that sits above `MedDeepScientist` (a separate runtime repo: `med-deepscientist`). Its role is **not** to run analyses directly, but to control research quality gates, workspace state, and submission delivery.

### Capability chain

All platform behavior flows through a single chain:

```
policy → controller → overlay → adapter
```

- **`policies/`** — declarative rules (research route bias, study archetypes, publication gates, data asset gates). Policies are the source of truth for what is allowed.
- **`controllers/`** — orchestrate policy checks, read/write workspace state, and return structured JSON results. Every CLI command maps to a controller call.
- **`overlay/`** — installs Codex/agent skill overlays into disease workspaces, bridging `MedAutoScience` governance rules into the agent's runtime context.
- **`adapters/`** — thin I/O boundaries to external systems (literature: PubMed, PMC, DOI; ARIS sidecar; ToolUniverse; report store).

### Key modules

| Module | Purpose |
|--------|---------|
| `cli.py` | All CLI commands; each subcommand maps to one controller function |
| `profiles.py` | `WorkspaceProfile` dataclass (frozen); loaded from `.toml` profile files |
| `runtime_protocol/` | Schema contracts for quest state, study runtime state, paper artifacts, topology |
| `runtime_transport/` | Transport layer that drives `MedDeepScientist` runtime (HTTP/process) |
| `display_registry.py`, `display_template_catalog.py` | Medical figure/table template system (8 categories, 40+ types) |
| `publication_display_contract.py`, `display_schema_contract.py` | Contracts for publication-quality display surfaces |
| `mcp_server.py` | MCP server entrypoint (`medautosci-mcp`) |
| `agent_entry/` | Agent entry mode contracts; synced to `templates/` via `sync-agent-entry-assets` |

### Workspace hierarchy

A disease workspace (not this repo) is structured as:

```
workspace/
  datasets/                 # Shared data assets across all studies
  portfolio/data_assets/    # Data version registry and impact records
  studies/<study-id>/       # One study = one research line = one paper target
    quest/                  # MedDeepScientist runtime state for this study
    paper/                  # Paper bundle and submission package
  portfolio/                # Portfolio memory across studies
```

This repo (the platform itself) is installed once and pointed at disease workspaces via profile files.

### Profile files

A profile (`.toml`) is the binding between this platform and a disease workspace. Key fields: `workspace_root`, `runtime_root`, `studies_root`, `med_deepscientist_repo_root`, `enable_medical_overlay`, `medical_overlay_scope`, `research_route_bias_policy`, `preferred_study_archetypes`. See `profiles/workspace.profile.template.toml` for the template.

## Commit convention (Lore protocol)

Commits use a structured format with git trailers. The first line is **why**, not what (the diff shows what):

```
<intent line: why the change was made>

<body: narrative context — constraints, approach rationale>

Constraint: <external constraint that shaped the decision>
Rejected: <alternative considered> | <reason>
Confidence: <low|medium|high>
Scope-risk: <narrow|moderate|broad>
Directive: <forward-looking warning for future modifiers>
Tested: <what was verified>
Not-tested: <known gaps>
```

Trailers are optional but `Rejected:` and `Directive:` are particularly valuable.

## Worktree and branch rules

- `main` is the stable shared branch. Small, safe changes go directly to `main`.
- Any substantial refactor, multi-file migration, or experimental feature must use an isolated worktree under `.worktree/` (gitignored). Do not leave the shared checkout on a feature branch long-term.
- `.omx/` and `.codex/` are local runtime state directories and must remain untracked.

## Agent contract layers

When operating as an agent in this repo, consult contracts in priority order:

1. `AGENTS.md` (root) — OMX/Codex execution and orchestration contract
2. `contracts/dev-hosts/` — host-specific adapter rules (OMX CLI vs Codex App)
3. `contracts/project-truth/AGENTS.md` — authoritative project identity, architecture priorities, domain constraints
4. `.omx/local/AGENTS.local.md` — machine-local overlay (untracked, optional)

## Key design constraints

- **Read state before mutating.** Controllers should check existing state before writing.
- **No direct registry editing.** Data asset mutations go through the `apply-data-asset-update` controller, not direct edits to `registry.json`.
- **No new dependencies** without an explicit request.
- **Upstream intake is periodic**, not automatic. Don't treat a new `MedDeepScientist` commit as an immediate task.
- **`MedAutoScience` is the entry point.** Don't expose `MedDeepScientist` internals directly to users or agents.
