<p align="center">
  <img src="assets/branding/medautoscience-logo.png" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>A medical research Foundry Agent and OPL-compatible package built on OPL Framework, with a direct MAS app skill for turning data, study questions, and evidence into manuscript-ready work</strong></p>
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
  <img src="assets/branding/medautoscience-overview.png" alt="Med Auto Science overview" width="100%" />
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

- `Med Auto Science` is publicly positioned as a medical research `Foundry Agent`: an independent domain agent for turning disease data, study questions, evidence, and manuscript work into one governed research line.
- MAS is also an `OPL-compatible package built on OPL Framework`. OPL can discover MAS stage descriptors, action metadata, handoff contracts, receipts, and projections; MAS remains the medical research owner.
- MAS now keeps its canonical OPL Agent semantic pack under repo-root `agent/` and declares those required files through repo-root `contracts/*.json`. OPL compiles that pack into the generated CLI / MCP / Skill / product-entry / tool descriptors; the existing MAS CLI, MCP, product-entry, sidecar, and controller surfaces remain domain action targets and authority functions, so direct operation does not lose capability.
- MAS keeps the direct app skill path as a first-class entry. Direct MAS activation and OPL-hosted handoff return to the same MAS-owned stage, controller, durable truth, review, and artifact surfaces; when a task is started in the hosted path, persistent wakeup, retry, resume, and attempt scheduling are enabled by default through OPL/Temporal rather than a Codex App outer driver.
- MAS owns medical research truth, quality verdicts, runtime-facing owner receipts, artifact authority, and publication authority. OPL Framework owns the generic runtime platform; framework metadata does not replace MAS owner surfaces.
- AI-first quality gates require separation of labor: an execution agent such as Codex CLI may produce the stage work, but reviewer/auditor judgment must be invoked as an independent agent task with its own context, task record, and receipt. A single agent cannot execute and then review itself to close MAS quality gates.
- This positioning adds no MAS-owned daemon, scheduler, or attempt loop. Hermes-Agent, MedDeepScientist/MDS, and the retired MAS local scheduler remain explicit optional/provenance/tombstone surfaces, not default public targets.
- Manuscript quality is governed by MAS study charters, evidence ledgers, review ledgers, AI reviewer workflow, publication gates, and controller records. Status panels, script checks, and historical MDS coverage provide supporting evidence.
- Clinical framing, claim acceptance, and final submission decisions stay with researchers and PIs.
- Journal submission and external system interaction stay under human supervision.

<details>
  <summary><strong>Technical boundary for operators</strong></summary>

- `Med Auto Science` is a medical research domain agent and Foundry Agent. It can be called directly by Codex, and it can also be discovered and hosted as an OPL-compatible package under `OPL Framework`.
- MAS owns the medical work itself: study intake, workspace context, evidence progression, progress explanation, manuscript quality judgment, runtime-facing owner receipts/projections, artifact authority, and manuscript-facing delivery.
- `OPL Framework` is the upper stage-led framework. It owns the generic runtime platform: stage attempts, queues, wakeups, recovery, approvals, receipts, state-machine execution, and cross-domain projection. MAS keeps medical conclusions, manuscript quality, domain transition semantics, artifact authority, and submission-facing judgment.
- In the OPL framework, a `Stage` is a large task step such as scouting, analysis, writing, reviewer repair, or delivery. An Agent executor is the minimum execution unit inside a stage; `Codex CLI` is the current first-class executor.
- MAS has completed monolith closeout. `MedDeepScientist` / `DeepScientist` remains available as provenance, explicit archive import, backend audit, upstream learning, and parity reference.
- Long-running OPL-hosted production execution is Temporal-backed. Temporal is the required production provider for OPL durable stage attempts, signal/query, retry/dead-letter, and workflow history. `Hermes-Agent` is not the target session/wakeup substrate, but it remains available as an explicit Agent executor adapter / proof lane that promises connectivity and auditability, not behavior or quality equivalence with `Codex CLI`.

</details>

## How To Read This Repository

1. Potential users and medical experts should start here, then continue to the [Docs Guide](./docs/README.md).
2. Technical readers and planners should read [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md).
3. Developers and maintainers should continue from the [Docs Guide](./docs/README.md) into `docs/active/`, `docs/runtime/`, `docs/delivery/`, `docs/references/`, and `docs/policies/`.

## Agent And Operator Quick Start

<details>
  <summary><strong>Start here if you are handing this repo to Codex or another agent</strong></summary>

- Read the [Docs Guide](./docs/README.md) first. It maps the current product boundary, operator entry surfaces, and the technical reading order.
- If you need to bootstrap or take over a disease workspace, read [Bootstrap](./bootstrap/README.md) next. It explains the workspace-first model and the `init-workspace -> doctor -> show-profile -> bootstrap` path.
- Treat [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md) as the repo-tracked human-readable truth set before changing runtime or docs.
- The current operator entry surfaces are `CLI`, `MCP`, `product-entry`, and `controller`. Current execution maps live under `docs/active/`, while product-entry and runtime contracts live under `docs/product/` and `docs/runtime/`, so an agent can start there instead of reverse-engineering the codebase. The repo-root `agent/` pack is the generated-interface semantic source for OPL; the local CLI, MCP tools, product-entry surfaces, controller-authorized workspace commands/scripts, durable surfaces, and repo-tracked contracts remain the MAS-owned action targets and authority surfaces behind those generated descriptors.
- MAS can be invoked directly through its Codex app skill or through OPL. Both routes use the same MAS-owned stage, controller, durable truth, and artifact surfaces; OPL/Temporal is the default hosted autonomous runtime for durable scheduling, wakeup, retry, resume, and projection.
- New disease workspaces are no-root-Git / no-quest-Git by default. OPL owns runtime lifecycle, provider attempts, wakeup, retry, and resume state; MAS only exposes domain refs, restore/provenance locators, artifact authority, owner receipts, typed blockers, and human gates.
- When an external agent needs the repo-tracked MAS skill surface directly, use `medautosci product skill-catalog --profile <profile> --format json`; it returns the single MAS app skill, the underlying command contracts, and body-free owner-route / artifact / authority refs for OPL or direct Codex execution.
- For OPL Full online handoff, `medautosci sidecar export --profile <profile> --format json` exposes body-free owner-route refs and `medautosci sidecar dispatch --task <task.json> --format json` records MAS owner-route dispatch receipts. OPL owns stage graph hydration, queue, attempt ledger, retry/dead-letter, and provider readiness; MAS owner surfaces only return receipts, typed blockers, human gates, or domain refs.

</details>

## Further Reading

- [Docs Guide](./docs/README.md)
- [Project](./docs/project.md)
- [Status](./docs/status.md)
- [Architecture](./docs/architecture.md)
- [Invariants](./docs/invariants.md)
- [Decisions](./docs/decisions.md)
