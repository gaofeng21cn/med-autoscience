<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>A disease-focused medical research workspace for turning data, study questions, and evidence into manuscript-ready work</strong></p>
<p align="center">Disease Studies · Evidence Organization · Manuscript Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>Who It Serves</strong><br/>
      Clinicians, PIs, and medical research teams working with disease-specific data and preparing studies for manuscript delivery
    </td>
    <td width="33%" valign="top">
      <strong>What It Organizes</strong><br/>
      Study questions, data assets, analysis progress, evidence gaps, and manuscript-facing files inside one governed workspace
    </td>
    <td width="33%" valign="top">
      <strong>How To Start</strong><br/>
      Tell it the disease area, the dataset you have, the question you want to answer, and the paper outcome you want
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="Med Auto Science hero" width="100%" />
</p>

> `Med Auto Science` is for teams already doing real medical research. It keeps topic framing, data preparation, evidence progression, progress reporting, and manuscript-facing delivery on the same line.

## One-Sentence Quick Start

You can start with prompts like:

- "Help me find a paper-worthy question from this colorectal cancer dataset, tell me what evidence is still missing, and propose the next step."
- "I already have preliminary results. Turn them into one manuscript line and tell me what validation to do next."
- "Keep pushing this disease study toward a publishable paper, and keep the progress plus files organized as we go."

## What It Helps With

- Finding a study question worth continuing from a disease-specific dataset, registry, or cohort.
- Turning existing analyses and early results into one manuscript line with clear next evidence steps.
- Keeping long-running work organized when files, figures, notes, and drafts would otherwise drift apart.
- Managing validation, subgroup analysis, calibration, clinical utility analysis, and other supporting evidence in the same workspace.
- Delivering manuscript-facing outputs as files that stay tied to the study they belong to.

## How It Works

- Researchers provide the clinical question, dataset, constraints, and final judgment.
- The AI operator moves the study forward through data preparation, analysis, evidence organization, and progress reporting.
- The workspace keeps tasks, files, progress, and delivery artifacts together so the whole line stays reviewable.

## Current Boundary

- `Med Auto Science` is the medical research workflow inside the broader `OPL` workspace.
- It owns study intake, workspace context, evidence progression, progress reporting, and manuscript-facing delivery.
- Clinical framing, claim acceptance, and submission decisions stay with researchers and PIs.
- Journal submission and external system interaction stay under human supervision.

## How To Read This Repository

1. Potential users and medical experts should start here, then continue to the [Docs Guide](./docs/README.md).
2. Technical readers and planners should read [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md).
3. Developers and maintainers should continue into `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, and `docs/policies/`.

## Technical Notes For Maintainers

The repository home stays user-facing on purpose.
Runtime contracts, durable handles, bridge surfaces, and historical tranche records live in the technical docs:

- [Docs Guide](./docs/README.md)
- [Status](./docs/status.md)
- [Project](./docs/project.md)
- [Runtime contracts](./docs/runtime/)
- [Program records](./docs/program/)

## Development Verification

- `make test-fast`
- `make test-meta`
- `make test-display`
- `make test-full`
- GitHub `macOS CI` intentionally keeps `quick-checks` lightweight; it installs `pandoc` plus `BasicTeX` for submission-facing DOCX/PDF coverage, while the full study runtime analysis bundle plus `graphviz` / `R` stay on the `display-heavy` and `release/full` lanes.

## Codex Plugin Integration

If you primarily operate through Codex, start with the Codex plugin integration guide at `docs/references/codex_plugin.md`.
Keep `docs/references/codex_plugin_release.md` nearby as the Codex plugin release guide.

## Further Reading

- [Docs Guide](./docs/README.md)
- [Project](./docs/project.md)
- [Status](./docs/status.md)
- [Architecture](./docs/architecture.md)
- [Invariants](./docs/invariants.md)
- [Decisions](./docs/decisions.md)
