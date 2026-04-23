<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>An independent medical research domain agent and workspace for turning data, study questions, and evidence into manuscript-ready work</strong></p>
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

- `Med Auto Science` is an independent medical research domain agent that can be called directly by Codex, OPL, or other general-purpose agents.
- It supports `direct entry` and `OPL handoff` as two equivalent entry routes with the same study semantics, authority boundary, and durable truth surfaces.
- Its stable product capability surface is the local CLI, workspace commands/scripts, durable surfaces, and repo-tracked contracts that `Codex` or `OPL` skill activation can call directly.
- It owns study intake, workspace context, evidence progression, progress reporting, and manuscript-facing delivery.
- `OPL` stays at family-level session/runtime/projection orchestration and shared modules/contracts/indexes; it does not redefine MAS as an internal module.
- Clinical framing, claim acceptance, and submission decisions stay with researchers and PIs.
- Journal submission and external system interaction stay under human supervision.

## How To Read This Repository

1. Potential users and medical experts should start here, then continue to the [Docs Guide](./docs/README.md).
2. Technical readers and planners should read [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md).
3. Developers and maintainers should continue from the [Docs Guide](./docs/README.md) into `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, and `docs/policies/`.

## Agent And Operator Quick Start

<details>
  <summary><strong>Start here if you are handing this repo to Codex or another agent</strong></summary>

- Read the [Docs Guide](./docs/README.md) first. It maps the current product boundary, operator entry surfaces, and the technical reading order.
- If you need to bootstrap or take over a disease workspace, read [Bootstrap](./bootstrap/README.md) next. It explains the workspace-first model and the `init-workspace -> doctor -> show-profile -> bootstrap` path.
- Treat [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md) as the repo-tracked truth set before changing runtime or docs.
- The current operator entry surfaces are `CLI`, `MCP`, and `controller`. Product-entry and runtime contracts live under `docs/runtime/` and `docs/program/`, so an agent can start there instead of reverse-engineering the codebase; the stable callable surface remains the local CLI, workspace commands/scripts, durable surfaces, and repo-tracked contracts.
- When an external agent needs the repo-tracked MAS skill surface directly, use `medautosci product skill-catalog --profile <profile> --format json`.

</details>

## Further Reading

- [Docs Guide](./docs/README.md)
- [Project](./docs/project.md)
- [Status](./docs/status.md)
- [Architecture](./docs/architecture.md)
- [Invariants](./docs/invariants.md)
- [Decisions](./docs/decisions.md)
