<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="MedAutoScience Logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">MedAutoScience</h1>

<p align="center"><strong>A medical AI research platform for disease-specific data, study progression, and submission delivery</strong></p>
<p align="center">Clinical Research Progression · Evidence Packaging · Submission Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>Who It Serves</strong><br/>
      Clinical teams and research groups building studies from disease-specific datasets
    </td>
    <td width="33%" valign="top">
      <strong>Public Role</strong><br/>
      Research Ops gateway for agents and medical teams
    </td>
    <td width="33%" valign="top">
      <strong>Position In OPL</strong><br/>
      The <code>Research Ops</code> domain gateway that drives data-to-paper delivery
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="MedAutoScience hero" width="100%" />
</p>

> Publicly, `MedAutoScience` is a `Research Ops Gateway`. Internally, it is powered by an `Agent-first, human-auditable` medical research harness OS.

## One-Sentence Product Position

If your goal is to keep turning disease-specific datasets into publication-ready studies, `MedAutoScience` gives you a governed and auditable research mainline instead of ad-hoc scripts.

## Position In The OPL Federation

In `One Person Lab (OPL)` semantics:

- `MedAutoScience` is the formal `Research Ops` domain gateway.
- It carries a research harness, not a loose script collection.
- It can be routed from the OPL gateway while remaining independently usable.

## Agent Contract Layers

<!-- AGENT-CONTRACT-BASELINE:START -->
- Root `AGENTS.md` is only for Codex/OMX collaboration in this repository's development environment; it is not the standalone project truth contract.
- Project truth contract: `contracts/project-truth/AGENTS.md`.
- OMX project-scope orchestration layer: `.codex/AGENTS.md` (loaded only by OMX / CODEX_HOME sessions).
- Optional machine-private overlay: `.omx/local/AGENTS.local.md` (must stay untracked).
- Local runtime state directories `.omx/` and `.codex/` must remain untracked and out of version control.
<!-- AGENT-CONTRACT-BASELINE:END -->

## What The Platform Focuses On

- Disease-level workspace management for long-running study portfolios.
- Research progression with auditable runtime states.
- Evidence packaging for manuscript and supplement delivery.
- Submission-oriented output synchronization.

## Quick Start Through Your Agent

1. Create or choose a disease-level workspace and put in raw data plus data dictionaries.
2. Ask your agent to clean data into machine-readable and auditable assets.
3. Ask your agent to run `MedAutoScience` as the `Research Ops Gateway / harness`.

## For Technical Operators

Use the repository `uv` environment for development and validation:

```bash
uv sync --frozen --group dev
uv run pytest
uv run python -m build --sdist --wheel
```

If you primarily run `MedAutoScience` through Codex, use the built-in plugin entry.

- Codex Plugin Integration: [docs/codex_plugin.md](docs/codex_plugin.md)
- Codex Plugin Release Guide: [docs/codex_plugin_release.md](docs/codex_plugin_release.md)
- Agent runtime interface: [docs/agent_runtime_interface.md](docs/agent_runtime_interface.md)
- Entry mode contract: [docs/agent_entry_modes.md](docs/agent_entry_modes.md)
- Disease workspace quickstart: [docs/disease_workspace_quickstart.md](docs/disease_workspace_quickstart.md)
- Docs index: [docs/README.md](docs/README.md)

## Release Artifact Base URL

Current release artifacts are published under:

`https://github.com/gaofeng21cn/med-autoscience/releases/download/v0.1.0a4`
