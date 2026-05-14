# Docs Guide

**English** | [中文](./README.zh-CN.md)

This directory is the technical reading layer for `Med Auto Science`. The
repository home remains the user-facing entry for clinicians, PIs, and medical
research teams.

## Start Here

| Need | Entry |
| --- | --- |
| Product role and boundary | [Project](./project.md) |
| Current operating truth | [Status](./status.md) |
| Architecture and owner boundaries | [Architecture](./architecture.md) |
| Non-negotiable constraints | [Invariants](./invariants.md) |
| Durable decisions | [Decisions](./decisions.md) |
| Documentation lifecycle rules | [Docs portfolio governance](./docs_portfolio_consolidation.md) |

## OPL Family Layering

The global OPL-family development reference lives at
`/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.zh-CN.md`.
It owns OPL Framework global targets, global gaps, generic primitive
absorption, App/workbench targets, and cross-repo execution order.

This MAS repo only owns the medical-research domain-agent target state, current
gaps, study/publication/artifact authority, the direct MAS app-skill path,
OPL-hosted sidecar/projection/receipt boundaries, and the list of generic
runtime, memory, artifact lifecycle, workbench, and observability primitives
that should move up into OPL. MAG, RCA, MDS, and OPL-owned App/workbench
backlogs are not maintained in MAS docs.

## Directory Map

| Directory | Purpose |
| --- | --- |
| [active](./active/README.md) | Current execution, current plans, current gaps, and active baton; former `program/` material is maintained here. |
| [public](./public/README.md) | MAS public narrative and first user-facing reading layer. |
| [product](./product/README.md) | MAS app skill, direct product entry, and operator/workbench-facing guidance. |
| [runtime](./runtime/README.md) | Runtime contracts, control surfaces, projections, display contracts, and active designs. |
| [delivery](./delivery/README.md) | Manuscript, package, submission/export, and medical-research delivery authority. |
| [source](./source/README.md) | Study workspaces, source readiness, source truth consumption, and external research intake. |
| [policies](./policies/README.md) | Stable internal rules and long-lived operating boundaries. |
| [specs](./specs/README.md) | Current technical spec index; older specs must be classified as active or historical. |
| [references](./references/README.md) | Supporting references, positioning, integration notes, parity material, and verification records. |
| [history](./history/README.md) | Dated snapshots, provenance, retired boards, archived plans, and process drafts. |

This table follows the OPL-family canonical docs taxonomy. The former
`program/` and `capabilities/` directories have been physically retired; use
`active/` for program-baton material and `delivery/medical-display/` for the
medical-display capability family.

## Reading Rule

Read the core docs first, then enter the relevant directory index. Detailed file
lists live in each subtree README so this page stays a short navigation surface.

`README*` and `docs/**` are human-readable documentation. Code, tests, runtime
status, and contracts should depend on schemas, durable JSON, source paths, or
semantic IDs such as `runtime:*`, `program:*`, `policy:*`, and `human_doc:*`,
not Markdown prose wording.
