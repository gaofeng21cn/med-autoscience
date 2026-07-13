---
name: med-autoscience
description: Use when Codex should operate the MAS medical-research domain pack through OPL-generated interfaces and MAS-owned authority handlers.
---

# MedAutoScience

Canonical OPL agent id: `mas`
Plugin/package locator: `med-autoscience`
Generated interface owner: `one-person-lab`
Domain handler target: `med_autoscience.domain_entry:MedAutoScienceDomainEntry.dispatch`

Implementation profile: `contracts/pack_compiler_input.json#/implementation_profile`.
The declarative pack is Markdown/JSON; Python is only a domain-helper language
under the source root declared there. Minimal authority functions remain
declared by the pack authority contracts. Python does not authorize a generic
runtime, CLI, product entry, status, MCP, or workbench.

Use this skill for medical-research planning, study progression, evidence review,
display work, manuscript work, publication handoff, or owner-route diagnosis.

## Entry

Read generated interfaces from OPL:

```bash
opl agents interfaces --domain mas --json
opl actions export --domain mas --format cli --json
opl actions inspect --domain mas --action study_progress --json
```

The MAS repository does not provide a private CLI, MCP server, plugin launcher,
tool runtime, product shell, or environment provisioner. OPL-generated surfaces
route structured action payloads to `MedAutoScienceDomainEntry.dispatch`.

The domain handler accepts the action ids declared by
`contracts/action_catalog.json`. Use `domain_handler_export` for refs-only
owner-route readback and `domain_handler_dispatch` for an OPL task ref.

## Environment

Runtime dependencies are declarative in
`contracts/runtime_environment_requirements.json` and are prepared by OPL:

```bash
opl env prepare --domain mas --profile analysis-display --platform <platform> \
  --requirement-profile contracts/runtime_environment_requirements.json \
  --artifact-root <artifact_root> --apply --json
opl env run --domain mas --profile analysis-display \
  --artifact-root <artifact_root> -- <command>
```

A runtime-environment receipt is not medical, artifact, visual-quality,
publication, submission, or owner authority.

## Professional Work And External Skills

The stage goal and MAS professional policy define what good medical work looks
like. Codex may choose tools, order, iteration, and safe parallelism inside those
boundaries. Preserve ordered dependencies that protect scientific validity,
evidence currentness, authority, or irreversible actions; do not turn a tool
catalog or CLI recipe into the research method.

Use the installed `mas-scholar-skills` capability package for ordinary medical
paper work. Acquire a new external Skill only for a named or demonstrated
coverage gap. Before syncing any new external Skill, inspect its identity,
provenance, permissions, data/credential scope, and compatibility. Search and
comparison order is otherwise executor-chosen; an already installed, inspected,
compatible Skill does not need to repeat acquisition. External outputs remain
candidate refs until the MAS owner path accepts them.

## Authority

MAS owns medical study truth, evidence interpretation, publication-quality
judgment, artifact mutation authorization, memory accept/reject, source
readiness, typed medical blockers, and owner receipts.

OPL owns generated CLI/MCP/Skill/product/status/workbench descriptors, runtime
transport, queues, attempts, lifecycle, storage maintenance, environment
materialization, and refs-only indexing. OPL cannot write MAS truth, sign MAS
owner receipts, authorize publication or export, or promote advisory capability
output into evidence.

Executor and reviewer/auditor must be separate invocations with separate task
records and receipts. Provider completion, file presence, tests, read models,
or generated descriptors never close an AI-first quality gate.

Ordinary progression lets Codex read any prior `StageOutcome`, raw/partial
artifact, negative result, failed attempt, or no-output diagnostic as route
context. No envelope, projection, receipt, or transition table is semantic
transition authority. A consumable delta may advance as
`completed_with_quality_debt`; that debt blocks quality, publication, export,
and submission-ready claims. A stage that produces no scientific or manuscript
delta still emits a no-output or failure diagnostic and advances so Codex can
select another declared stage. Negative or null results remain evidence: Codex
may preserve their lineage and route back to hypothesis, cohort/data, endpoint,
analysis design, writing, or another owning stage instead of chasing a positive
result. Retry, review, and repair limits are quality budgets. Stop only for an
unavailable executor, wrong-target identity/currentness, real authority, safety,
credential, irreversible-action, or explicit human-decision gate.
