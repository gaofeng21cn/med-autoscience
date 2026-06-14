# Paper recovery owner callable materializer closeout

Owner: `MedAutoScience`
Purpose: `process_closeout_provenance`
State: `history_provenance`
Machine boundary: 本文是人读 closeout ledger。当前 truth 继续归 MAS source/tests、PaperRecovery source、domain action materializer / dispatch source、runtime/controller surfaces、owner receipts、typed blockers 和 live workspace artifacts。

## Snapshot

- `RUN_SNAPSHOT_TS=2026-06-14T22:44:32Z`.
- Repo scope: `/Users/gaofeng/workspace/med-autoscience/.worktrees/codex-mas-dm-recovery-materializer`, branch `codex/mas-dm-recovery-materializer`, base `origin/main@7e793c6b9`.
- Six-repo frozen inventory before this write lane found only two relevant dirty external lanes:
  - OPL Brand L5 worktree `/Users/gaofeng/workspace/one-person-lab.worktrees/brand-l5-owner-acceptance`, branch `codex/brand-l5-owner-acceptance`, dirty test-only expectation.
  - MAS worktree `/Users/gaofeng/workspace/med-autoscience/.worktrees/codex-mas-dm-recovery-materializer`, this lane.
- Post-snapshot activity: this lane inspected the MAS dirty write set, fixed the materializer/dispatch behavior, verified it, and prepared it for main absorption. The OPL Brand L5 dirty worktree was not modified or absorbed.

## Candidate Gate

Concrete retirement/materializer theme: `paper_recovery_state owner_action_ready -> default executor dispatch materialization`.

Source of truth:

- Machine truth: `src/med_autoscience/controllers/domain_action_request_materializer_parts/paper_recovery_owner_callable.py`, `src/med_autoscience/controllers/domain_action_request_materializer.py`, `src/med_autoscience/controllers/domain_action_request_materializer_parts/current_action_selection.py`, `src/med_autoscience/controllers/domain_action_request_materializer_parts/current_typed_blocker_transition_barrier.py`, `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/fresh_progress_owner_actions.py`, `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/progress_blocking_selection.py`, focused tests.
- Contract boundary: MAS-owned `paper_recovery_state` may materialize successor owner actions/gates; diagnostic `current_execution_envelope_*` actions are not supported request actions and must not swallow current owner-route queue, consumed transition, or paper-recovery dispatch candidates unless the blocker is the hard OPL execution authorization boundary.
- Human owner docs: this closeout ledger only. No active docs truth was changed.

Value gate:

- Pollution surface: `paper_recovery_state.phase=owner_action_ready` could be observed, but same-tick request/dispatch materialization and dispatch selection were missing or swallowed by unsupported fresh-progress diagnostic barriers.
- Expected mutation: wire paper-recovery owner callable action identity into materialization and dispatch selection; let dry-run diagnostic previews request ready-dispatch shape; keep `current_execution_envelope_*` diagnostic barriers from preempting dispatchable owner-route or consumed-transition actions; preserve hard fail-closed behavior for `opl_execution_authorization_required`.
- Verification: focused paper-recovery materializer/dispatch tests, full materializer case suite, full domain-owner dispatch suite, health diagnostic aggregation suite, and `git diff --check`.

Safety gate:

- Active caller evidence exists in domain health diagnostic preview, domain action request materializer, default executor dispatch materialization, and domain owner action dispatch.
- No live study workspace, paper artifact, `publication_eval/latest.json`, `controller_decisions/latest.json`, owner receipt, typed blocker, human gate, provider attempt, workflow, package metadata, or contract file was written.
- Existing OPL Brand L5 worktree remained blocked: current contract still reports all ten owner-acceptance requirements with blocker refs and no owner-acceptance refs; focused test actual values remained `typed_blocker_followthrough_route_count=47` / `observed_refs_not_l5_claim_route_count=83`, not the dirty expectation `37` / `93`.

## Landed Source And Tests

Changed source:

- `src/med_autoscience/controllers/domain_action_request_materializer.py`
- `src/med_autoscience/controllers/domain_action_request_materializer_parts/current_action_selection.py`
- `src/med_autoscience/controllers/domain_action_request_materializer_parts/current_typed_blocker_transition_barrier.py`
- `src/med_autoscience/controllers/domain_action_request_materializer_parts/paper_recovery_owner_callable.py`
- `src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_dry_run_previews.py`
- `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/fresh_progress_owner_actions.py`
- `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/persisted_dispatches.py`
- `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/progress_blocking_selection.py`

Changed tests:

- `tests/domain_action_request_materializer_cases/test_paper_recovery_owner_callable.py`
- `tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_materialized_dispatch_blockers.py`
- `tests/test_domain_owner_action_dispatch_cases/test_paper_recovery_owner_callable.py`

Behavioral effect:

- Paper recovery successor owner action now carries predecessor study/quest/work-unit/blocker identity from `current_work_unit` / typed blocker when the recovery obligation itself is sparse.
- Dispatch selection can match paper-recovery successor owner action dispatches through owner route/source refs instead of requiring the generic fresh-progress matcher.
- Persisted dispatch selection can select same-tick paper-recovery successor dispatches and suppress stale stage-native residue for that selection path.
- Dry-run health diagnostic preview asks the materializer for ready-dispatch shape without applying writes.
- Unsupported non-hard `current_execution_envelope_*` diagnostics are recorded as ignored diagnostics and no longer swallow dispatchable top-level owner-route actions, consumed domain-transition actions, or paper recovery actions.
- Hard `opl_execution_authorization_required` envelope barrier still fails closed before stale executable queue/materialization.

## Verification

Fresh commands run from this worktree:

- `UV_HTTP_TIMEOUT=120 ./scripts/run-pytest-clean.sh tests/domain_action_request_materializer_cases/test_paper_recovery_owner_callable.py tests/test_domain_owner_action_dispatch_cases/test_paper_recovery_owner_callable.py -q` -> `10 passed`.
- `UV_HTTP_TIMEOUT=120 ./scripts/run-pytest-clean.sh tests/domain_action_request_materializer_cases -q` -> `78 passed`.
- `UV_HTTP_TIMEOUT=120 ./scripts/run-pytest-clean.sh tests/test_domain_owner_action_dispatch.py -q` -> `94 passed`.
- `UV_HTTP_TIMEOUT=120 ./scripts/run-pytest-clean.sh tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases.py -q` -> `89 passed`.
- `./scripts/verify.sh` -> passed; emitted a non-blocking line-budget advisory for `src/med_autoscience/controllers/domain_action_request_materializer.py`.
- `rtk git diff --check -- <changed source/test files>` -> passed.

Diagnostic note:

- Directly running `tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_materialized_dispatch_blockers.py` returned `no tests ran` because this case file is imported through the aggregate `tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases.py` collection surface. The aggregate entry was run and passed.
- A post-commit focused retry of `tests/test_domain_owner_action_dispatch_cases/test_paper_recovery_owner_callable.py` failed during dependency extraction for `pillow==12.1.1` with a UV network timeout before tests executed. The aggregate `tests/test_domain_owner_action_dispatch.py` suite was rerun after the `persisted_dispatches.py` selection patch and passed.

## Stop Evidence

Post-mutation candidate reevaluation:

- `Brand L5 owner acceptance`: blocked. The dirty OPL test expectation remains unsupported by current contract/runtime evidence; absorbing it would create a false readiness claim.
- `MAS source lane`: this lane passed value/safety gates and is ready for commit/push/cleanup.
- New docs lifecycle SSOT lane: not opened in this closeout because no fresh coherent SSOT cluster was validated after the source lane; opening a low-confidence docs sweep would violate this automation's no-token-churning rule.
- New concrete retirement lane: no additional no-active-caller / replacement-owner candidate was validated after this source lane. Next run should start from stale public surfaces around non-hard `current_execution_envelope_*` diagnostics and any remaining paper-recovery handoff aliases.

This closeout does not claim MAS paper progress, publication readiness, domain readiness, owner receipt completion, typed blocker resolution, human gate resolution, provider running proof, current package freshness, or OPL-family campaign completion.
