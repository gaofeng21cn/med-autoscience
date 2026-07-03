# MAS Authority Functions

Owner: `med-autoscience`
Purpose: `minimal_authority_function_catalog`
State: `declaration_surface`
Machine boundary: This directory declares MAS-owned authority functions for OPL stage-pack consumption. It is not a generic runner, scheduler, queue, attempt ledger, runtime state root, cache, or artifact body store.

## Retained Authority

MAS retains authority for owner receipts, typed blockers, medical research truth, clinical or cohort truth, publication quality verdicts, source-integrity verdicts, artifact mutation authorization, publication route decisions, and memory accept/reject decisions.

## OPL Boundary

OPL generated surfaces may consume body-free refs, manifests, lineage refs, and receipts through these boundaries. They must not write medical research truth, clinical truth, manuscript bodies, figure bodies, owner receipt bodies, typed blocker bodies, runtime state, queues, caches, or generated artifacts from this declaration.

## Function Refs

- `medical_research_owner_receipt_signer`: MAS-owned closeout authority for stage owner receipts or MAS-owned typed blockers.
- `publication_quality_gate`: MAS-owned publication quality and integrity gate, including citation, calculation, source, figure-code, and manuscript-readiness checks.
- `artifact_mutation_authorizer`: MAS-owned authorization surface for manuscript, figure, table, data-product, and submission-package body mutation.
- `memory_accept_reject_decider`: MAS-owned decision surface for durable medical research memory body acceptance or rejection.
