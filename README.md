<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>The first mature medical implementation of Research Foundry</strong></p>
<p align="center">Clinical Research Progression · Evidence Packaging · Submission Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>Who It Serves</strong><br/>
      Clinical teams and medical researchers building paper-grade studies from disease-specific data
    </td>
    <td width="33%" valign="top">
      <strong>Public Role</strong><br/>
      Medical `Research Ops` gateway and `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`
    </td>
    <td width="33%" valign="top">
      <strong>Position In The Federation</strong><br/>
      <code>One Person Lab -> Research Foundry -> Med Auto Science</code>
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="Med Auto Science hero" width="100%" />
</p>

> Publicly, `Med Auto Science` is the medical `Research Ops` gateway in the `Research Foundry` line. Internally, it is the medical `Research Ops` `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`.

## Product Position

If your goal is to keep turning disease-specific data into publication-ready studies, `Med Auto Science` gives you a governed and auditable research mainline instead of a pile of disconnected scripts.

## Where It Sits

`Med Auto Science` is not the whole of `Research Foundry`, and it is not the top-level `OPL` gateway either.

Its current role is:

- the first mature medical implementation on the `Research Foundry` line
- the active medical carrier for `Research Ops`
- it owns medical `Research Ops` contracts and delivery expectations
- the domain gateway that organizes medical studies, evidence packages, and submission delivery
- the medical `Research Ops` `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`
- the harness-based runtime surface above a controlled `MedDeepScientist` execution surface, while `MedDeepScientist` itself is not the system body

The public chain is:

`User / Agent -> OPL Gateway (optional) -> Unified Harness Engineering Substrate -> Research Foundry -> Med Auto Science -> Controlled MedDeepScientist surface`

## What It Helps You Do

- Organize disease-level workspaces that keep datasets, study portfolios, and delivery artifacts under one auditable surface.
- Progress studies from data cleaning and asset registration into analysis, validation, evidence packaging, and manuscript delivery.
- Keep medical reporting logic aligned with clinical readers rather than defaulting to generic ML-paper structure.
- Export submission-facing artifacts with stricter governance over figures, tables, and publication surfaces.

## Why It Exists

Many automated research systems are good at executing steps but weak at controlling publication quality.

`Med Auto Science` is built around a different priority:

- decide whether a topic is worth continuing before spending the full execution budget
- organize work around clinical meaning, reporting logic, and evidence chains
- preserve human-auditable state instead of hiding decisions inside transient chat context
- keep agents as operators while leaving critical go/stop judgment to humans

## Current Runtime Shape

The default local execution mode is `Codex-default host-agent runtime`.
On this runtime, medical study progression is executed through a controlled `MedDeepScientist` surface.
This means:

- `Med Auto Science` remains the `Domain Harness OS` and contract owner
- `MedDeepScientist` remains an execution surface under control, not the full system identity

## What Stays Stable Over Time

As runtime hosting evolves (including a future managed web runtime on the same substrate), the core domain contracts stay stable:

- human-auditable state and decision trace
- medical domain contracts for data, study progression, and submission delivery
- controlled runtime surface boundaries between domain logic and execution engine

## Publication Display Templates

The publication display surface is now a stable templated publication-facing layer.

The current medical display system is designed to protect the lower bound of paper figures and tables without capping the upper bound of study-specific presentation. It constrains layout, field organization, export boundaries, and quality checks so that low-level problems such as text overlap, annotation overflow, or unreadable composite panels are caught as contract issues rather than left to ad-hoc repair.

The display line now has three explicit layers:

- a top-level roadmap defined by the original `A-H` paper families
- an engineering audit layer that governs schemas, renderers, QC, and materialization contracts
- a concrete inventory layer that records the currently registered templates, shells, and tables

That means:

- the roadmap answers which manuscript-facing evidence families the platform should ultimately cover
- the audit guide answers which templates are already audited end to end
- the generated catalog answers what is concretely implemented in code today

If you want the maintained documentation entry, continue with:

- [Public documentation index](docs/README.md)

The detailed display roadmap, audit, and catalog references remain repo-tracked operator docs and are currently Chinese-only unless they are explicitly promoted with bilingual mirrors.

## Typical Outputs

When a study is worth continuing, the platform is designed to deliver:

- an investable research direction rather than a one-off run record
- auditable data assets and extension paths
- study-scoped result packages inside a disease workspace
- manuscript-facing evidence organization
- submission-ready paper and supplementary delivery surfaces

## Best-Fit Study Shapes

`Med Auto Science` is especially useful when:

- you already have a disease-specific cohort or a stable clinical dataset
- you want multiple studies to reuse the same workspace and data foundation
- the paper needs external validation, subgroup analysis, calibration, decision utility, or mechanistic sidecars
- the final deliverable is not only analysis output but a full manuscript and submission package

## Fast Start Through Your Agent

For most medical users, the fastest path is to give your goal, data, and constraints to your agent, then let it run `Med Auto Science`.

Typical three-step start:

1. Create or choose a disease-level workspace and place your raw data, data dictionaries, endpoint definitions, inclusion and exclusion rules, and reference papers there.
2. Ask your agent to first clean and register the data into machine-readable, auditable research assets.
3. Ask your agent to run `Med Auto Science` as the medical `Research Ops` gateway and keep the study aligned with your target journal, endpoint priorities, subgroup requirements, and publication standard.

You can give your agent an instruction like this:

> Read the data and documentation in this study workspace first. Step 1: clean and register them into machine-readable, auditable research assets, and make variable definitions, endpoints, and usable scope explicit. Step 2: use Med Auto Science (`https://github.com/gaofeng21cn/med-autoscience`) as the medical `Research Ops` `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`. Run the study through the controlled MedDeepScientist surface, and produce a publication-grade evidence chain with figures, tables, manuscript surfaces, and submission materials. Carry my journal targets, endpoint priorities, subgroup rules, and other constraints into the runtime contract. Prioritize deciding whether this study should continue; if the direction is weak, stop, reframe, or add a proper sidecar.

## Documentation

- [Docs index](docs/README.md)

Detailed operator docs stay repo-tracked, but they are not part of the default bilingual public surface unless they ship with synchronized English and Chinese mirrors.

## Technical Validation

Use the repository `uv` environment for development and verification:

```bash
uv sync --frozen --group dev
uv run pytest
uv run python -m build --sdist --wheel
```

If you primarily operate through Codex, use the built-in plugin entry:

- [Codex plugin integration](docs/codex_plugin.md)
- [Codex plugin release guide](docs/codex_plugin_release.md)
