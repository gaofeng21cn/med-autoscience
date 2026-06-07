# Gate-clearing batch facade test retirement

Owner: `MedAutoScience`
Purpose: `gate_clearing_batch_facade_test_retirement_provenance`
State: `history_provenance`
Machine boundary: 本文是人读过程记录。当前机器真相归 `src/med_autoscience/controllers/gate_clearing_batch.py`、`src/med_autoscience/controllers/gate_clearing_batch_execution.py`、`src/med_autoscience/controllers/gate_clearing_batch_repair_fingerprints.py`、`tests/test_gate_clearing_batch.py` 和 repo-native verification output。

## Closeout

The gate-clearing batch facade test that pinned top-level re-exports of natural-boundary internal helpers is retired.

## Retired Surface

- Retired test file: `tests/test_gate_clearing_batch_cases/module_boundaries.py`.
- Retired aggregate import: `from .test_gate_clearing_batch_cases.module_boundaries import *` in `tests/test_gate_clearing_batch.py`.

The implementation helpers remain active where they are used by gate-clearing behavior. This closeout removes the compatibility-style test contract that required those helpers to stay asserted through the top-level `gate_clearing_batch.py` facade.

## Current Boundary

Behavioral tests continue to cover gate planning, replay, publication work-unit routing, currentness, freshness, authority redrive, submission sync, direct migration, transport normalization and display materialization failures through `tests/test_gate_clearing_batch.py` and the remaining case modules.

Future tests should assert behavior or import the natural owner module directly instead of adding facade/re-export preservation tests for private helpers.

## Verification

Verification run on `2026-06-07`:

- `scripts/run-pytest-clean.sh --collect-only -q tests/test_gate_clearing_batch.py tests/test_gate_clearing_batch_cases`
- `scripts/run-pytest-clean.sh -q tests/test_gate_clearing_batch.py`
- source/test scan confirming `module_boundaries.py` and its aggregate import are absent
- `git diff --check`

## Out Of Scope

This lane did not change gate-clearing execution behavior, repair planning, dependency logic, fingerprinting semantics, runtime currentness, owner-route reconciliation, medical paper readiness or active controller dispatch surfaces.
