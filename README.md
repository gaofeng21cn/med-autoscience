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
      The medical `Research Ops` gateway in `Research Foundry`, with `OPL` remaining the optional top-level federation layer
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
| Agent-assisted research mainline | Active | The current honest way to use the system for real work |
| Lightweight product-entry shell | Early | Launch, task submission, and progress visibility exist, but this is not yet a mature standalone medical front desk |
| Medical display / paper-figure line | Supporting line | Kept separate from the runtime mainline so figure work does not distort research authority |
| Mature direct user-facing medical frontend | Not landed | Still future work behind the runtime gate |

## How To Read This Repository

1. Potential users and medical experts should start here, then continue to the [Docs Guide](./docs/README.md).
2. Technical readers and planners should read [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md).
3. Developers and maintainers should continue into `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, and `docs/policies/`.

## Plain-Language Boundary

`Med Auto Science` is not the same thing as every lower-layer runtime component.
Its role is to stay responsible for medical research entry, study authority, and research-facing truth.

```text
User / Agent
  -> OPL Gateway (optional)
      -> Med Auto Science
          -> Controlled Research Backend
```

In plain language:

- `OPL` is optional and stays above this repository.
- `Med Auto Science` owns the medical research workflow and authority boundary.
- The current research engine still sits below this repository and should not be confused with the public product surface.

## What This Repository Is Not

- It is not a claim that a mature direct medical product frontend has already landed.
- It is not a claim that upstream `Hermes-Agent` fully owns research execution here today.
- It is not a place to mix paper-figure assetization back into the main research runtime storyline.

<details>
  <summary><strong>Technical Notes And Current Runtime Truth</strong></summary>

The current formal-entry matrix remains `CLI`, `MCP`, and `controller` on the `Codex-default host-agent runtime` baseline.
The repo-tracked product mainline remains `Auto-only`.

Current honest tranche map remains:

- `P0 runtime native truth`
- `P1 workspace canonical literature / knowledge truth`
- `P2 controlled cutover -> physical monorepo migration`

Current truthful runtime ownership is still layered:

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

Current repo-verified public entry wording remains:

- `operator entry` and `agent entry`
- `product entry`: not landed yet as a mature direct user-facing entry
- the current lightweight shell still centers on `build-product-entry`

Compatible target routes remain documented as:

- `User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`
- `User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

The lightweight repo-tracked shell now includes `workspace-cockpit`, `submit-study-task`, `launch-study`, `product-preflight`, `product-start`, `product-frontdesk`, `product-entry-manifest`, and `build-product-entry`.
These surfaces improve launch, task intake, and progress visibility, and the manifest/frontdesk now also carry explicit guardrail-recovery guidance, a structured `Phase 3` host-clearance lane, a `Phase 4` backend-deconstruction lane, plus a structured `Phase 5` platform target. They still do not mean a mature standalone medical frontend has landed.

The medical display line remains intentionally separate from the runtime mainline, so publication-figure work does not rewrite research authority or gateway truth.
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
