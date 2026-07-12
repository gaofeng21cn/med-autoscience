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

Ordinary progression reads canonical `StageOutcome` and
`NextActionEnvelope`; legacy next-action or diagnostic projections are not
transition authority. Stop at a typed blocker, durable human gate, owner receipt,
or explicit route-back when the required authority is unavailable.
