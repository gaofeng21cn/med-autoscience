# Medical paper readiness request packet persistence closeout 2026-06-07

Owner: `MedAutoScience`
Purpose: `medical_paper_readiness_request_packet_persistence_closeout`
State: `history_provenance`
Machine boundary: Human-readable closeout. Current request packet shape, default-executor dispatch identity, readiness surface selection, owner dispatch behavior, study truth, owner receipts, typed blockers and live paper-line truth remain owned by source, tests, contracts, runtime/controller artifacts, owner receipts and typed blockers.

## Scope

This lane records commit `43ffb625` (`Persist medical readiness request packets`). It made default-executor dispatch for `complete_medical_paper_readiness_surface` persist a canonical owner-visible request packet at `artifacts/supervision/requests/medical_paper_readiness/latest.json`, and tightened stale payload handling when the current readiness surface changes.

It changed MAS source and focused tests. This closeout only adds repo-local evidence. It does not write live study workspaces, paper/package artifacts, `publication_eval/latest.json`, `current_package`, owner receipts, quality verdicts, OPL provider state or DM002 / DM003 live owner closeout evidence.

## SSOT

- `src/med_autoscience/controllers/owner_route_handoff_parts/default_executor_dispatch_tasks.py` owns default-executor task generation, persisted dispatch identity and canonical medical-paper-readiness request packet persistence.
- `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/action_execution/medical_paper_readiness.py` owns owner dispatch surface arbitration and request/ref payload consumption.
- `tests/test_cli_cases/owner_route_handoff_command_cases/default_executor_dispatch_currentness_cases.py` owns regression coverage that readiness surface changes persist request packet identity, `surface_key` and payload authoring target.
- `tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py` owns regression coverage that stale request payloads cannot override the current readiness surface.

## Classification

| Surface | Classification | Outcome |
| --- | --- | --- |
| Missing canonical request packet for default-executor readiness dispatch | `conflicts_with_ssot` | Closed by persisting `artifacts/supervision/requests/medical_paper_readiness/latest.json` with request-only authority and current readiness identity. |
| Stale inline/request payload from a previous readiness surface | `stale_or_superseded` | Dropped when the dispatch's declared/current surface changes, and owner dispatch no longer consumes mismatched request payloads for the current surface. |
| Existing operator payload authoring target | `more_specific_detail` | Retained as request packet detail, but normalized to current `surface_key` and stripped of stale operator payloads. |
| Medical readiness source identity and dedupe | `covered_by_ssot` | Default-executor source identity remains bound to the current readiness surface and now also carries a persisted request packet. |
| DM002 / DM003 live owner closeout | `out_of_scope` | Still requires a real owner run to produce StageRun/source/idempotency matched owner receipt, quality gate receipt, typed blocker, human gate or route-back evidence. |

## Changes

- Persisted canonical medical-paper-readiness request packets from default-executor dispatch.
- Added stale readiness payload dropping when a dispatch's prior declared surface differs from the current readiness surface.
- Normalized `payload_authoring_target.surface_key` and `operator_payload_contract.surface_key` to the current readiness surface.
- Mapped `literature_intelligence_os` to `literature_scout` when deriving payload surface identity.
- Adjusted owner dispatch precedence so current readiness surface identity is not displaced by stale request payloads.

## Verification

Fresh commands run from `/Users/gaofeng/workspace/med-autoscience`:

```bash
rtk ./scripts/run-pytest-clean.sh -q tests/test_cli_cases/owner_route_handoff_command.py -k 'readiness_surface_key_changes_default_executor_source_identity'
rtk ./scripts/run-pytest-clean.sh -q -o 'python_files=*.py' tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py -k 'stale_request_payload_for_current_readiness_surface'
rtk ./scripts/run-pytest-clean.sh -q -o 'python_files=*.py' tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py -k 'target_journal_writing_layer_from_existing or stale_request_payload_for_current_readiness_surface'
rtk git diff --check
rtk /Users/gaofeng/.local/bin/opl-doc-doctor doctor . --format json
```

Results:

- Default-executor focused test passed with `1 passed, 94 deselected`.
- Stale request payload focused test passed with `1 passed, 17 deselected`.
- Adjacent direct case run passed with `2 passed, 16 deselected`.
- MAS `git diff --check` passed.
- MAS doctor returned `finding_count=0`.

Note: the first direct attempt against the `_cases.py` files collected no tests because those files are support case modules rather than default pytest entry files. The valid focused entry is either the importing aggregate test file or direct collection with `-o 'python_files=*.py'`.

## Remaining Scope

This closes request-packet persistence and stale-payload arbitration for the medical-paper-readiness owner surface. It does not close DM002 / DM003 live paper-line owner execution, paper readiness, publication readiness, package freshness, quality/submission verdicts, production readiness, physical compensation-chain retirement, or broader MAS docs portfolio cleanup.
