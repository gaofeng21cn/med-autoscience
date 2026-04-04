---
name: med-autoscience
description: Use when Claude Code should operate MedAutoScience through its stable runtime, controller, overlay, and workspace contracts — instead of writing ad-hoc scripts or directly editing workspace state files.
---

# MedAutoScience Skill for Claude Code

Thin entry layer for Claude Code to operate `MedAutoScience` through its stable CLI, controller, and workspace contracts.

## What this skill is

- The Claude Code analogue of the Codex plugin skill
- Sits on top of the existing Python package, CLI, controllers, overlay installer, and workspace profiles
- Does not replace `medautosci` CLI, controller contracts, or any non-Claude-Code integration

## Core rules

Prefer the established `MedAutoScience` runtime contract over ad-hoc edits:

- If no workspace exists yet, call MCP tool `init_workspace` or run `medautosci init-workspace`
- Read current state before any mutation
- Data asset changes go through `apply-data-asset-update` with a structured payload — never edit `registry.json` directly
- Keep `MedAutoScience` as the entry point; do not expose `MedDeepScientist` internals directly

If `medautosci` is not on `PATH`, use the module entry:

```bash
uv run python -m med_autoscience.cli <command>
```

## Key CLI commands

```bash
medautosci init-workspace --workspace-root /path --workspace-name <name>
medautosci doctor --profile <profile.toml>
medautosci show-profile --profile <profile.toml>
medautosci bootstrap --profile <profile.toml>
medautosci watch --runtime-root <runtime-root> [--apply]
medautosci overlay-status --profile <profile.toml>
medautosci install-medical-overlay --profile <profile.toml>
medautosci med-deepscientist-upgrade-check --profile <profile.toml> --refresh
medautosci data-assets-status --workspace-root /path
medautosci publication-gate --quest-root /path [--apply]
medautosci figure-loop-guard --quest-root /path [--apply]
medautosci export-submission-minimal --paper-root /path
```

## MCP server

The `medautosci-mcp` server exposes the same controller surface over MCP. Configure it in `.claude/settings.json` or `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "med-autoscience": {
      "type": "stdio",
      "command": "medautosci-mcp"
    }
  }
}
```

`medautosci-mcp` must be on `PATH` (installed via `uv tool install` or `pip install`).

## Typical tasks

- Validate a workspace profile and report what is missing
- Bootstrap a new disease workspace and install the medical overlay
- Check overlay drift and reapply if needed
- Run `runtime watch` and summarize blockers
- Drive data asset updates and submission delivery through auditable controller commands
- Audit the publication gate and figure-loop-guard status before submission

## Files to read first

- `bootstrap/README.md` — workspace setup and runtime prerequisites
- `controllers/README.md` — controller surface and available commands
- `CLAUDE.md` — repo architecture, commit convention, and worktree rules
