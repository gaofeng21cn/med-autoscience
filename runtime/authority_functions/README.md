# MAS Authority Functions

Owner: `med-autoscience`
Purpose: `minimal_authority_function_catalog`
State: `declaration_surface`
Machine boundary: This directory declares MAS-owned authority functions for OPL stage-pack consumption. It is not a generic runner, scheduler, queue, attempt ledger, runtime state root, cache, or artifact body store.

## Retained Authority

MAS retains the medical criteria and authority for owner receipts, typed blockers, research truth, publication quality, source integrity, artifact mutation, route decisions, and memory acceptance. Open-ended judgments are made by the decisive producer/reviewer roles declared in `agent/`; they are not implemented as repository-local validator functions.

## OPL Boundary

OPL generated surfaces may consume body-free refs, manifests, lineage refs, and receipts through these boundaries. They must not write medical research truth, clinical truth, manuscript bodies, figure bodies, owner receipt bodies, typed blocker bodies, runtime state, queues, caches, or generated artifacts from this declaration.

## Function Ref

- `med_autoscience.authority_handlers.paper_mission.evaluate_paper_mission_authority`: pure, registry-bound evaluation of exact OPL-hosted refs. It performs no filesystem, network, process, runtime, package, or lifecycle operation. The callable does not replace independent reviewer/re_reviewer judgment and cannot materialize a Stage transition.
- `src/med_autoscience/authority_handlers/_stage_attempt_review_snapshot.py#finalize_bounded_analysis_producer_snapshot_closeout`: private attempt-local adapter used only by a bounded analysis producer. It reads declared workspace bytes to verify exact statistical member identities, calls the MAS-owned snapshot builder, and returns closeout refs; it does not write OPL runtime state, issue a verdict, or materialize a Stage transition.
