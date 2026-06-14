# OPL execution authorization owner split closeout

Owner: `MedAutoScience`
Purpose: `process_closeout_provenance`
State: `history_provenance`
Machine boundary: 本文是人读 closeout ledger。当前 truth 继续归 MAS source/tests、`study progress` / `domain-health-diagnostic` read-model、OPL current-owner gate readout、owner receipts / typed blockers 和 live workspace artifacts。

## Snapshot

- `RUN_SNAPSHOT_TS=2026-06-14T00:56:48Z`.
- Repo scope: `/Users/gaofeng/workspace/med-autoscience` started from `main@3edd02c8c`; during this verification window the coherent docs/source-test foldback was already linearly landed through `07c02803c` and `de6502bfc`, with `origin/main` at `de6502bfc` before this ledger commit.
- Frozen dirty write set before absorption: `docs/decisions.md`, `docs/status.md`.
- Post-snapshot activity: the dirty docs were a coherent owner-split foldback from the MAS current-work-unit / paper-recovery commits `3a9a177df`, `3edd02c8c`, `07c02803c`, and `de6502bfc`; this lane verified and recorded that foldback instead of overwriting it.

## Candidate Gate

Semantic theme: `opl_execution_authorization_required owner split`.

SSOT owner:

- Machine truth: `src/med_autoscience/controllers/current_work_unit.py`, `src/med_autoscience/controllers/paper_recovery_state.py`, `src/med_autoscience/controllers/current_work_unit_parts/policy_constants.py`, focused tests, and fresh `study progress` output.
- Human current owner: `docs/decisions.md` for durable decision boundary, `docs/status.md` for compact current status.

Peer docs:

- `docs/runtime/projections/study_progress_projection.md`: `more_specific_detail`; it already defines `study_progress` as controller-owned projection and names the OPL authorization blocker rule.
- `docs/docs_portfolio_consolidation.md`: `out_of_scope`; it only defines docs lifecycle ownership.
- OPL `docs/status.md` and `docs/active/current-state-vs-ideal-gap.md`: `covered_by_ssot` on MAS read-model truth and only keep family-level current-owner gate implications.

Classification:

- `covered_by_ssot`: old wording that made `gate_clearing_batch` look like the canonical current owner for `opl_execution_authorization_required`.
- `more_specific_detail`: embedded typed blocker / PaperRecovery obligation owner remains `gate_clearing_batch` for provenance.
- `conflicts_with_ssot`: none after the foldback.
- `stale_or_superseded`: prior "DHD dry-run says owner=gate_clearing_batch" framing for the canonical owner.
- `history_or_provenance`: this ledger and the old implementation commits.

Safety gate:

- Active caller/read-model evidence supports the docs change; no source, runtime workspace, publication artifact, owner receipt, typed blocker, human gate, provider attempt, or Yang study artifact was written.
- Current MAS dirty source/test worktrees remain unrelated and were not touched.

## Evidence

Read source/tests/docs evidence:

- `git show --stat 3a9a177df` showed source/test landing for routing OPL authorization blockers.
- `git show --stat 3edd02c8c` showed focused test isolation cleanup.
- CodeGraph source read covered `build_paper_recovery_state`, current-work-unit policy constants, typed-blocker owner answer helpers, and OPL authorization focused tests.
- Fresh `study progress` for `003-dpcc-primary-care-phenotype-treatment-gap` using `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml` showed:
  - `current_work_unit.status=typed_blocker`
  - `current_work_unit.owner=one-person-lab`
  - `current_work_unit.state.blocker_type=opl_execution_authorization_required`
  - `current_work_unit.state.typed_blocker.owner=gate_clearing_batch`
  - `current_execution_envelope.state_kind=typed_blocker`
  - `current_execution_envelope.owner=one-person-lab`
  - `paper_recovery_state.current_authority.owner=one-person-lab`
  - `paper_recovery_state.current_authority.obligation.owner=gate_clearing_batch`
  - `next_safe_action.kind=provide_opl_execution_authorization_or_human_gate`
  - `running_provider_attempt=false`, `active_run_id=null`, worker liveness `not_live` / `parked`.
- Fresh DHD dry-run was observe-only with `will_start_llm=false`, `codex_dispatch_count=0`, `provider_admission_pending_count=0`.

## Landed And Recorded Files

Already landed before this ledger commit:

- `docs/decisions.md` in `07c02803c`: rewrote the durable decision so canonical `current_work_unit.owner`, `current_execution_envelope.owner`, and `paper_recovery_state.current_authority.owner` are `one-person-lab` for this blocker, while embedded obligation owner remains `gate_clearing_batch`.
- `docs/status.md` in `07c02803c`: added compact current-state foldback with the same owner split and explicit non-claims.
- Focused test split in `de6502bfc`: kept authorization blocker current-work-unit tests isolated.

Recorded by this ledger commit:

- `docs/history/program/opl_execution_authorization_owner_split_closeout_2026_06_14.md`: this provenance ledger.
- `docs/history/program/README.md`: compact history index row.

No source, tests, contracts, workflows, package metadata, runtime workspace artifact, publication artifact, owner receipt, typed blocker, human gate, or OPL provider attempt was changed in this lane.

## Verification

- `scripts/run-python-clean.sh -m med_autoscience.cli study progress --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml --study-id 003-dpcc-primary-care-phenotype-treatment-gap --format json`
- `scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml --studies 003-dpcc-primary-care-phenotype-treatment-gap --request-opl-stage-attempts --dry-run`
- `scripts/run-pytest-clean.sh -q tests/test_paper_recovery_state.py tests/test_current_work_unit.py tests/test_study_progress_projection_currentness.py` passed: `82 passed`.
- `scripts/run-pytest-clean.sh -q tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/provider_admission_current_control_followthrough_cases.py tests/test_provider_admission_current_control.py tests/test_study_progress_projection_currentness.py` passed: `36 passed`.
- `rtk git diff --check` passed.
- Strict conflict-marker scan passed.
- OPL Doc doctor returned `finding_count=0`, `active_truth_health.status=pass`, `markdown_doc_count=275`.

## Stop Evidence

This lane does not close MAS paper progress, publication readiness, domain readiness, owner receipt, typed blocker, human gate, OPL execution authorization, provider running proof, current package freshness, or production readiness. The next closing work must come from the OPL runtime owner or MAS owner surface with a current pointer consumable owner answer, execution authorization repair receipt, human gate, route-back evidence, owner receipt, stable typed blocker supersession, canonical changed surface, or strict same-identity running proof.
