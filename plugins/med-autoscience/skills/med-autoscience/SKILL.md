# MedAutoScience Plugin

Use this plugin when Codex should operate `MedAutoScience` through its stable runtime surface instead of treating the repository as an ad-hoc script collection.

## What this plugin is

- A thin Codex entry layer for `MedAutoScience`
- Additive to the existing Python package, CLI, controllers, overlays, and workspace profiles
- Not a replacement for the `medautosci` CLI, controller contracts, or non-Codex integrations

## Core rule

Prefer the existing `MedAutoScience` runtime contracts:

- `medautosci doctor --profile <profile>`
- `medautosci show-profile --profile <profile>`
- `medautosci bootstrap --profile <profile>`
- `medautosci watch --runtime-root <runtime-root>`
- `medautosci overlay-status --profile <profile>`
- `medautosci install-medical-overlay --profile <profile>`
- `medautosci deepscientist-upgrade-check --profile <profile> --refresh`
- `medautosci-mcp`

When `medautosci` is not on `PATH`, use the module entry:

```bash
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile <profile>
```

## Operating guidance

- Read workspace status before mutations.
- For data assets, go through controller commands and structured payloads. Do not directly hand-edit registry files.
- Preserve `MedAutoScience` as the runtime layer. Do not collapse controller, profile, overlay, and workspace logic into plugin-only files.
- Keep compatibility with other frameworks by leaving existing CLI and controller entrypoints unchanged.
- The plugin-local MCP facade depends on the `medautosci-mcp` command being available on `PATH`.

## First files to read

- `bootstrap/README.md`
- `controllers/README.md`
- `guides/codex_plugin.md`

## Typical tasks

- Audit whether a workspace profile is correctly wired
- Bootstrap a new study workspace for Codex-driven execution
- Check overlay drift or reapply the medical overlay
- Run runtime watch and summarize blockers
- Drive data-asset and submission controllers through auditable commands
