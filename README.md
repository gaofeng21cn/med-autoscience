<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>An independent medical research domain agent with a single MAS app skill for turning data, study questions, and evidence into manuscript-ready work</strong></p>
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

## Current Position And Boundary

- `Med Auto Science` is a medical research domain agent. It can be called directly by Codex, and it can also run under the `OPL` agent runtime framework.
- MAS owns the medical work itself: study intake, workspace context, evidence progression, progress explanation, manuscript quality judgment, and manuscript-facing delivery.
- `OPL` is the upper runtime framework. It owns stage attempts, queues, wakeups, recovery, approvals, receipts, and cross-domain projection; it does not make MAS medical conclusions or own manuscript quality.
- In the OPL framework, a `Stage` is a large task step such as scouting, analysis, writing, reviewer repair, or delivery. `Codex CLI` is the default smallest execution unit inside a stage.
- MAS has completed monolith closeout. `MedDeepScientist` / `DeepScientist` is no longer a default runtime, diagnostic, progress UI, or quality dependency; it remains only as provenance, explicit archive import, backend audit, upstream learning, and parity reference.
- `Hermes-Agent` is not the default MAS online substrate. Long-running online execution now follows the OPL provider-backed direction, with Temporal as the target production provider; Hermes remains legacy/optional provider, proof lane, or historical compatibility material.
- Manuscript quality cannot be replaced by status panels, script checks, or historical MDS coverage. Scientific quality, medical writing quality, and submission-facing judgment remain constrained by MAS study charters, evidence ledgers, review ledgers, AI reviewer workflow, publication gates, and controller records.
- Clinical framing, claim acceptance, and final submission decisions stay with researchers and PIs.
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
- Treat [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md) as the repo-tracked human-readable truth set before changing runtime or docs.
- The current operator entry surfaces are `CLI`, `MCP`, `product-entry`, and `controller`. Product-entry and runtime contracts live under `docs/runtime/` and `docs/program/`, so an agent can start there instead of reverse-engineering the codebase; the stable callable surface remains the local CLI, MCP tools, product-entry surfaces, controller-authorized workspace commands/scripts, durable surfaces, and repo-tracked contracts.
- MAS can be invoked directly through its Codex app skill or through OPL. Both routes must converge on the same MAS-owned stage, controller, durable truth, and artifact surfaces; OPL framework metadata must not become a second medical research truth source.
- New disease workspaces are no-root-Git / no-quest-Git by default. Runtime lifecycle status is read from file authority, `artifacts/runtime/runtime_lifecycle.sqlite`, `artifacts/runtime/lifecycle_migration`, `runtime/quests` manifests, and `runtime/restore_index`, not from Git history.
- When an external agent needs the repo-tracked MAS skill surface directly, use `medautosci product skill-catalog --profile <profile> --format json`; it returns the single MAS app skill, the underlying command contracts, and a machine-readable `runtime_continuity` envelope projected from existing runtime/session/progress/artifact surfaces.
- For OPL Full online runtime integration, use `medautosci sidecar export --profile <profile> --format json` and `medautosci sidecar dispatch --task <task.json> --format json`. Local CLI/status/manifest reads can still run without the OPL provider and should report degraded online readiness rather than silently claiming Full online readiness.

</details>

## Further Reading

- [Docs Guide](./docs/README.md)
- [Project](./docs/project.md)
- [Status](./docs/status.md)
- [Architecture](./docs/architecture.md)
- [Invariants](./docs/invariants.md)
- [Decisions](./docs/decisions.md)
