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

`Med Auto Science` sits inside `Research Foundry` as the active medical `Research Ops` surface, while `OPL` continues to provide the top-level gateway and federation layer.

Its current role is:

- the first mature medical implementation on the `Research Foundry` line
- the active medical carrier for `Research Ops`
- it owns medical `Research Ops` contracts and delivery expectations
- the domain gateway that organizes medical studies, evidence packages, and submission delivery
- the medical `Research Ops` `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`
- the harness-based runtime surface above a repo-side outer-runtime seam, with `MedDeepScientist` serving as the controlled research backend

The public chain is:

`User / Agent -> OPL Gateway (optional) -> Unified Harness Engineering Substrate -> Research Foundry -> Med Auto Science -> repo-side outer-runtime seam -> Controlled MedDeepScientist research backend`

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

The old `Codex-default host-agent runtime` is now kept only as a migration-era comparison surface and regression oracle; it is no longer the long-term product direction.
The formal-entry matrix remains fixed as: default formal entry `CLI`, supported protocol layer `MCP`, internal control surface `controller`.
That matrix describes how agents enter the runtime, while the public product remains agent-operated and domain-governed.
The current repo-tracked product mainline is still `Auto-only`; any future `Human-in-the-loop` product should reuse the same substrate as a compatible sibling or upper-layer product.
The long-line target runtime topology is:

- `Med Auto Science` stays the only research entry, research gateway, and study/workspace authority owner
- upstream `Hermes-Agent` is the outer runtime substrate owner
- `MedDeepScientist` is the controlled research backend

The current repo-side seam is frozen behind a single `runtime backend interface` contract. Today, this repository has **not** landed a true upstream `Hermes-Agent` integration yet: the controller, outer loop, transport, and durable surface can already carry the future outer-runtime boundary, but real long-running execution still goes through the controlled `MedDeepScientist` backend.

## Entry Modes And Product Boundary

Today, the stable repo-verified surfaces are still `operator entry` and `agent entry`.
That means:

- `operator entry`: workspace preparation, debugging, inspection, and manual governance done by a human operator
- `agent entry`: `CLI` plus `MCP`, called by `Codex` or another host-agent
- `product entry`: not landed yet as a mature direct user-facing entry

The target domain-facing shape is:

`User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`

Inside the broader `OPL` family, the compatible top-level route is:

`User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

That handoff should keep one shared minimum envelope:

- `target_domain_id`
- `task_intent`
- `entry_mode`
- `workspace_locator`
- `runtime_session_contract`
- `return_surface_contract`

`Med Auto Science` then adds research payload such as `study_id`, `journal_target`, and `evidence_boundary`.

This is still a target architecture note, not a claim that the product entry has already landed.
Because the external runtime gate is still open, the current truthful user path remains agent-operated rather than a mature standalone product entry.

### What `Hermes` Means Today

- In this repository, `Hermes` currently names the repo-side outer-runtime seam for the mainline, not a landed upstream `Hermes-Agent` runtime.
- The repo can now use `runtime_backend_id = hermes` honestly because `med_autoscience.runtime_transport.hermes` is no longer a pure alias: it is a repo-side real adapter that binds each managed runtime root to explicit external `Hermes-Agent` runtime evidence, fail-closes on `inspect_hermes_runtime_contract(...)`, and only then delegates actual quest control to the controlled `MedDeepScientist` transport through the backend contract.
- This still gives the outer loop real leverage: `runtime_watch` can detect dropouts, `ensure_study_runtime` can request recovery, `runtime_supervision/latest.json` can escalate repeated failures, and `study_progress` can project physician-friendly updates from durable surfaces.
- On `2026-04-12`, a real proof was captured on study `002-dm-china-us-mortality-attribution`: `ensure-study-runtime` brought a waiting quest back into a live managed run, `watch --apply --ensure-study-runtimes` plus a short `watch --loop` refreshed both `runtime_watch/latest.json` and `runtime_supervision/latest.json`, and `study-progress` returned to a human-readable progress surface with live monitoring links.
- That still does **not** mean upstream Hermes fully owns execution yet: the research engine is still the controlled `MedDeepScientist` backend, standalone host replacement continues through that gate, and full upstream ownership plus external-gate clearance on other hosts and studies still need to be proven honestly.

## Current Repo-Side Status

The priority order is now frozen and partially completed:

That means:

- `P0 runtime native truth` is complete in `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a`
- `P1 workspace canonical literature / knowledge truth` is complete in `Med Auto Science`
- `P2 controlled cutover -> physical monorepo migration` remains active, but what is currently landed is a repo-side real adapter and contract cleanup, not true upstream `Hermes-Agent` ownership proof

The repository now carries the native-runtime transport contract, the workspace canonical literature / reference-context contract, a repo-side outer-runtime seam, and the `MedDeepScientist` deconstruction map. The external runtime gate now sits as a concrete external blocker inside `P2`, and it still prevents any honest claim that upstream `Hermes-Agent` already owns the runtime substrate.

## Execution Handle And Durable Surfaces

- `study_id` is the durable aggregate-root identity for a medical study.
- `quest_id` is the formal managed runtime handle for the controlled research backend quest bound to that study.
- `active_run_id` is the live daemon run handle inside the current quest when execution is active; it must not replace `study_id` or `quest_id`.
- `program_id` is the control-plane and report-routing pointer for the active `research-foundry-medical-mainline`.
- Current canonical durable status, audit, and decision surfaces are `study_runtime_status`, `runtime_watch`, `artifacts/publication_eval/latest.json`, `artifacts/reports/escalation/runtime_escalation_record.json`, `artifacts/controller_decisions/latest.json`, and `artifacts/runtime/last_launch_report.json`.
- `runtime_binding.yaml` now records both outer-substrate metadata (`runtime_backend_id`, `runtime_engine_id`) and controlled research backend metadata (`research_backend_id`, `research_engine_id`).
- Repo-tracked runtime truth and local operator handoff surfaces stay separate: the former owns the product/runtime contract, while the latter carries machine-local resume and continuation state.

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

For current real-study continuation, keep one boundary explicit: `P0` and `P1` are already in the repo, but `P2` still requires controlled cutover validation, parity checks, and the remaining external runtime / workspace gates documented under `docs/program/`.

Typical three-step start:

1. Create or choose a disease-level workspace and place your raw data, data dictionaries, endpoint definitions, inclusion and exclusion rules, and reference papers there.
2. Ask your agent to first clean and register the data into machine-readable, auditable research assets.
3. Ask your agent to run `Med Auto Science` as the medical `Research Ops` gateway and keep the study aligned with your target journal, endpoint priorities, subgroup requirements, and publication standard.

You can give your agent an instruction like this:

> Read the data and documentation in this study workspace first. Step 1: clean and register them into machine-readable, auditable research assets, and make variable definitions, endpoints, and usable scope explicit. Step 2: use Med Auto Science (`https://github.com/gaofeng21cn/med-autoscience`) as the medical `Research Ops` `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`. Run the study through the controlled MedDeepScientist surface, and produce a publication-grade evidence chain with figures, tables, manuscript surfaces, and submission materials. Carry my journal targets, endpoint priorities, subgroup rules, and other constraints into the runtime contract. Prioritize deciding whether this study should continue; if the direction is weak, stop, reframe, or add a proper sidecar.

### How Users Start And Watch Progress Today

For the current agent-operated path, four commands plus one optional host-service entry define the real user-facing loop:

- Start or resume a managed study: `uv run python -m med_autoscience.cli ensure-study-runtime --profile <profile> --study-id <study_id>`
- Inspect the full structured state and monitoring entry: `uv run python -m med_autoscience.cli study-runtime-status --profile <profile> --study-id <study_id>`
- Read the human-facing progress summary: `uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>`
- Refresh the MAS supervisor heartbeat: `uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> --profile <profile> --ensure-study-runtimes --apply`
- Keep the MAS supervisor loop online as a user service: `ops/medautoscience/bin/install-watch-runtime-service`

If a workspace was initialized from an older scaffold, re-run `init-workspace` once before installing the service. The controller now upgrades the service-critical managed entry scripts in place without requiring `--force`.

When `study-runtime-status` reports `autonomous_runtime_notice.required = true` or `execution_owner_guard.supervisor_only = true`, the study is already in a live managed runtime. At that point the user-visible surface is:

- `browser_url`, `quest_session_api_url`, and `active_run_id` as the monitoring entry
- `study-progress` for the plain-language phase, blockers, and next action
- the host service behind `install-watch-runtime-service` keeping the supervisor heartbeat fresh, plus a supervisor-only foreground agent instead of direct writes into runtime-owned surfaces

## Documentation

- [Docs index](docs/README.md)
- [Lightweight product entry and OPL handoff](docs/references/lightweight_product_entry_and_opl_handoff.md) (Chinese only)

Detailed operator docs stay repo-tracked, but they are not part of the default bilingual public surface unless they ship with synchronized English and Chinese mirrors.

## Technical Validation

Use the repository `uv` environment for development and verification:

```bash
uv sync --frozen --group dev
make test-full
uv run python -m build --sdist --wheel
```

Layered local test entrypoints:

- `make test-fast`: default developer slice, excluding meta-only and display-heavy suites
- `make test-meta`: repo-tracked docs, workflow, packaging, and contract-surface checks
- `make test-display`: display materialization and golden-regression suites
- `make test-full`: full clean-clone baseline

If you primarily operate through Codex, use the built-in plugin entry:

- [Codex plugin integration](docs/references/codex_plugin.md)
- [Codex plugin release guide](docs/references/codex_plugin_release.md)
