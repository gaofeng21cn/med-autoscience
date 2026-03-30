# Codex Plugin Integration

`MedAutoScience` can now be exposed to Codex as a repo-local plugin at `plugins/med-autoscience/`.

For a higher-level release summary in Chinese, see [codex_plugin_release.md](codex_plugin_release.md).

## What the plugin changes

- Adds a Codex-native discovery and installation surface through `.codex-plugin/plugin.json`
- Adds a plugin marketplace entry at `.agents/plugins/marketplace.json`
- Adds a plugin skill that teaches Codex to operate the existing `MedAutoScience` runtime through stable interfaces
- Adds a plugin-local MCP manifest at `plugins/med-autoscience/.mcp.json`

## What the plugin does not change

- It does not replace the Python package
- It does not replace `medautosci`
- It does not replace controller contracts
- It does not remove profile-driven workspace binding
- It does not change the DeepScientist overlay installation model

## Compatibility

This plugin is intentionally additive. Other frameworks should continue to integrate through the existing surfaces:

- Python package: `med_autoscience`
- CLI: `medautosci`
- Controllers under `src/med_autoscience/controllers/`
- Overlay installer under `src/med_autoscience/overlay/installer.py`

As long as those surfaces remain stable, adding the Codex plugin does not reduce compatibility with non-Codex agents or wrappers.

## Recommended usage

1. Keep using `profiles/*.local.toml` to bind a concrete workspace.
2. Use `doctor` or `show-profile` first to verify paths and overlay policy.
3. Use `bootstrap` to initialize overlay and data-asset state.
4. Use controller commands for auditable mutations and status refreshes.

## Installation State

Creating the repo-local plugin files does not automatically enable the plugin globally in Codex.

- Repo-local state: the plugin now exists inside this repository and can be discovered from this repository's marketplace metadata.
- Global state: Codex is only globally configured for a plugin once the corresponding plugin enablement appears in `~/.codex/config.toml`.

At the time this guide was written, the repo contains the plugin files, but that alone is not the same thing as a machine-wide installation.

## Installing On Another Computer

The most reliable path is:

1. Clone this repository.
2. Run:

   ```bash
   bash scripts/install-codex-plugin.sh
   ```

3. Restart Codex so native skill discovery and plugin metadata are reloaded.

If you want the plugin to be home-local instead of repo-local, copy or sync:

- `plugins/med-autoscience/` to `~/plugins/med-autoscience/`
- `.agents/plugins/marketplace.json` into `~/.agents/plugins/marketplace.json`

Then make sure `medautosci-mcp` is still available on `PATH`.

## Scope boundary

The plugin is a thin entry shell. `MedAutoScience` itself remains the research runtime layer.
