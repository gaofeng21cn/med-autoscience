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

## Directory Map

| Directory | Purpose |
| --- | --- |
| [runtime](./runtime/README.md) | Runtime contracts, control surfaces, projections, display contracts, and active designs. |
| [program](./program/README.md) | Small active execution queue and program-level coordination. |
| [capabilities](./capabilities/README.md) | Capability-family documentation such as medical display. |
| [references](./references/README.md) | Supporting references, positioning, integration notes, parity material, and verification records. |
| [policies](./policies/README.md) | Stable internal rules and long-lived operating boundaries. |
| [history](./history/README.md) | Dated snapshots, provenance, retired boards, archived plans, and process drafts. |

## Reading Rule

Read the core docs first, then enter the relevant directory index. Detailed file
lists live in each subtree README so this page stays a short navigation surface.

`README*` and `docs/**` are human-readable documentation. Code, tests, runtime
status, and contracts should depend on schemas, durable JSON, source paths, or
semantic IDs such as `runtime:*`, `program:*`, `policy:*`, and `human_doc:*`,
not Markdown prose wording.
