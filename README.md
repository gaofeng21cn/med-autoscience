<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>A medical research mainline for turning disease-specific data into paper-grade studies</strong></p>
<p align="center">Clinical Research Progression · Evidence Packaging · Submission Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>Who It Serves</strong><br/>
      Clinical teams and medical researchers who want to keep studies progressing toward real manuscript delivery
    </td>
    <td width="33%" valign="top">
      <strong>What It Helps With</strong><br/>
      Study organization, evidence packaging, progress supervision, and submission-facing research delivery
    </td>
    <td width="33%" valign="top">
      <strong>Public Role</strong><br/>
      The first-level medical domain module and agent under the `OPL` GUI and management shell
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="Med Auto Science hero" width="100%" />
</p>

> `Med Auto Science` is the medical research line in the `Research Foundry` family. It is designed to help teams keep studies governed, auditable, and steadily moving toward publication-facing outputs.

## What It Helps You Do

- Organize disease-specific workspaces so data, studies, evidence, and outputs stay on one auditable line.
- Move a study from intake and analysis toward validation, evidence packaging, and manuscript delivery.
- Keep the research story aligned with clinical meaning instead of defaulting to generic ML-paper structure.
- Make progress, blockers, and supervision visible instead of hiding them inside one long chat or one fragile script chain.

## Best-Fit Study Shapes

- You already have a disease cohort, registry, or stable clinical dataset.
- You expect multiple studies to reuse the same workspace and knowledge base.
- You need validation, subgroup work, calibration, clinical utility analysis, or sidecar evidence before writing.
- Your real goal is a paper-grade deliverable, not just one analysis run.

## Current Public Path

| Path | Status | What it means |
| --- | --- | --- |
| `OPL` managed MAS loop | Active | `OPL` is the top-level GUI and management shell; MAS receives domain-scoped medical research tasks from that shell |
| `Codex` default interaction and execution | Active | The default way to inspect, plan, run, and continue MAS work is through Codex-driven `CLI` / `MCP` / controller surfaces |
| `Hermes-Agent` backup and always-on gateway | Active as a gateway mode | Used for external long-running supervision, recovery, scheduling, and backup operation when continuous runtime visibility is needed |
| Medical display / paper-figure line | Supporting line | Kept separate from the research task loop so figure work stays a downstream capability line |

## How To Read This Repository

1. Potential users and medical experts should start here, then continue to the [Docs Guide](./docs/README.md).
2. Technical readers and planners should read [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md).
3. Developers and maintainers should continue into `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, and `docs/policies/`.

## Plain-Language Boundary

`Med Auto Science` is the medical domain module/agent that sits inside the broader `OPL` operating shell.
It owns the medical research task loop: study intake, workspace context, evidence progression, progress reporting, and human decision points.

```text
User / clinical operator
  -> OPL GUI / management shell
      -> Med Auto Science domain module / agent
          -> Codex default interaction + execution
          -> Hermes-Agent backup / long-running gateway when continuous supervision is needed
```

In plain language:

- `OPL` is the top-level GUI and management shell.
- `Med Auto Science` is the first-level medical domain module and agent under that shell.
- `Codex` is the default interactive and execution surface for MAS work.
- upstream `Hermes-Agent` is the external backup mode and long-running gateway for supervised runtime continuity.
- Lower backend details remain implementation references for maintainers and runtime operators.

## Boundary Guardrails

- Keep user-facing explanations centered on `OPL` shell, MAS domain task flow, Codex execution, and Hermes long-running supervision.
- Keep backend transport, migration, handoff, and runtime-owner details in internal runtime/program references.
- Keep medical display and paper-figure assetization as a supporting capability line.

<details>
  <summary><strong>Internal Runtime Reference Keywords</strong></summary>

The public model above is the recommended reading path.
The compatibility notes below retain older contract vocabulary so maintainers can still trace existing runtime documents and tests.

The current formal-entry matrix remains `CLI`, `MCP`, and `controller` on the `Codex-default host-agent runtime` baseline.
The repo-tracked product mainline remains `Auto-only`.

Current honest tranche map remains:

- `P0 runtime native truth`
- `P1 workspace canonical literature / knowledge truth`
- `P2 controlled cutover -> physical monorepo migration`

Older layered runtime ownership wording is retained here as internal compatibility vocabulary:

- `Med Auto Science` owns research entry, study/workspace authority, and outer-loop governance.
- `MedDeepScientist` remains the controlled research backend for real execution.
- upstream `Hermes-Agent` is still the target outer runtime substrate rather than a fully landed end state in this repo.

The current durable handle story stays explicit:

- `program_id` points to `research-foundry-medical-mainline`.
- `study_id` remains the durable study identity.
- `quest_id` is the managed runtime handle for the controlled research backend quest.
- `active_run_id` is the live daemon run handle inside the active quest.
- The durable surface set stays explicit: `study_runtime_status`, `runtime_watch`, `publication_eval/latest.json`, `runtime_escalation_record.json`, and `controller_decisions/latest.json`.
- `study-progress` continues to project physician-friendly updates without pretending the runtime gate is already solved.

This repo still operates through a repo-side outer-runtime seam, and that seam is not a landed upstream `Hermes-Agent` runtime; standalone host replacement continues through that gate.
The external runtime gate now sits as a concrete external blocker inside `P2`.

Older repo-verified entry wording is retained here for internal traceability:

- `operator entry` and `agent entry`
- `product entry`: not landed yet as a mature direct user-facing entry
- the current lightweight shell still centers on `build-product-entry` as an internal machine bridge

Older target route labels remain documented as compatibility references:

- `User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`
- `User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

The lightweight repo-tracked shell now includes `workspace-cockpit`, `submit-study-task`, `launch-study`, `product-preflight`, `product-start`, `product-frontdesk`, `product-entry-manifest`, and `build-product-entry`.
For the current public model, the practical user loop is `product-frontdesk` -> `workspace-cockpit` -> `submit-study-task` -> `launch-study` -> `study-progress`; `product-entry-manifest` and `build-product-entry` are internal machine-readable bridge surfaces.

The medical display line remains intentionally separate from the runtime mainline, so publication-figure work stays a downstream capability line.
</details>

## Development Verification

- `make test-fast`
- `make test-meta`
- `make test-display`
- `make test-full`
- GitHub `macOS CI` intentionally keeps `quick-checks` lightweight; it only installs `pandoc` for submission-facing DOCX coverage, while the full study runtime analysis bundle plus `graphviz` / `R` stay on the `display-heavy` and `release/full` lanes.

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
