# DM002 Manuscript Quality Self-Evolution Patch Receipt

- Date: 2026-05-18
- Source Agent Lab suite: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/002-dm-china-us-mortality-attribution/artifacts/agent_lab/medical_manuscript_quality/latest_suite.json`
- OPL Agent Lab result: `oals_de7c8002af969568edd93c1b`
- OPL Meta Agent developer work order: `oma_developer_patch_work_order_99fdc0d34111`
- 当前实现要求：`opl-meta-agent` 可作为开发者直接修改 `med-autoscience` 的 stage、skill、prompt、rubric、quality contract、owner callable、tests 和 docs。它不得写 DM002 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal`、`manuscript/current_package` 或 submission readiness verdict。
- Hard methodology 路线要求：HDL/unit harmonization 命中时，MAS 必须退到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。该 callable 必须产出 `artifacts/controller/analysis_harmonization/latest.json`，内容为 unit-harmonized rerun evidence 或 `unit_harmonized_rerun_required` typed blocker；只写 supervisor request 不能算 owner 闭环。
- Traceability matrix source: `/tmp/opl-meta-agent-dm002-quality-v2-traceable/developer-patch-work-order.json`

## Scope

This patch updates MAS capability surfaces only: prediction-model first-draft quality contract, medical manuscript prose/rubric safety patterns, write skill guidance, tests, and repo docs.

## Addressed Gap Tokens

- `medical_journal_prose_quality`
- `hdl`
- `model-reproducibility`
- `baseline-survival`
- `table1-table2`
- `uncertainty-intervals`
- `validation-metrics`
- `nhanes`
- `calibration-risk-collapse`
- `figure-quality`
- `internal-quality-language-purge`

## Authority Boundary

This patch does not write study truth, `publication_eval/latest.json`, `controller_decisions/latest.json`, canonical paper artifacts, `manuscript/current_package`, or any submission readiness verdict. DM002 quality closure remains owned by MAS AI reviewer and publication gate.

## Verification Receipt

- `uv run pytest tests/test_prediction_model_first_draft_quality.py tests/test_medical_reporting_audit.py tests/submission_minimal_cases/source_markdown_and_materialized_refs.py tests/test_publication_critique_policy.py -q`: 41 passed.
- `scripts/verify.sh`: repo hygiene audit passed; 4 passed.
- `make test-meta`: 241 passed, 4113 deselected.
- No DM002 study truth, `publication_eval/latest.json`, `controller_decisions/latest.json`, canonical paper artifacts, `manuscript/current_package`, or submission readiness verdict was modified by this source patch.

## Runtime Consumption Follow-Up

The first self-evolution patch tightened first-draft quality gates but DM002 still parked because the runtime read model consumed a delivered-package handoff before unresolved AI-reviewer quality work, and the AI-reviewer workflow materialized the future-facing limitations plan only inside `reviewer_operating_system` instead of preserving the top-level owner record field required by later dispatch.

Follow-up patch:

- Preserve top-level `future_facing_limitations_plan` in AI-reviewer-owned `publication_eval/latest.json` records so later owner dispatch can consume the current record without false `ai_reviewer_record_incomplete` blockers.
- Prevent delivered-package handoff from preempting blocked, must-fix, or AI-reviewer-underdefined publication evaluations.
- Add regression coverage for clean-migration interim eval consumption and delivered-package/AI-reviewer route precedence.

Additional verification:

- `uv run pytest tests/test_ai_reviewer_publication_eval_workflow.py tests/test_paper_authority_migration.py tests/test_cli_cases/study_state_matrix_ai_reviewer_currentness_cases.py tests/test_runtime_supervisor_dispatch_executor_cases/clean_migration_rematerialization.py tests/test_runtime_supervisor_dispatch_executor_cases/ai_reviewer_workflow_dispatch.py tests/test_cli_cases/study_state_matrix_command.py::test_study_state_matrix_projects_delivered_package_and_unclassified_fail_closed tests/test_study_runtime_interaction_arbitration.py::test_arbitrate_waiting_for_user_respects_delivered_package_oracle_over_blocked_closeout_redrive -q`: 39 passed.
- `scripts/verify.sh`: repo hygiene audit passed; 4 passed.

## Source Provenance Follow-Up

The hard-methodology loop surfaced a second blocker: after HDL/unit contamination is detected, a unit-harmonized external validation cannot be rerun as the same transported model unless the original Cox model provenance is recovered. Inputs, metric summaries, and prose-level method descriptions are insufficient.

Follow-up patch:

- Route `analysis_harmonization_owner` model-provenance blockers to `source_provenance_owner`.
- Add `source_provenance_owner.recover_transport_model_provenance_or_typed_blocker`, which writes only `artifacts/controller/source_provenance/latest.json`.
- Add supervisor scan, consumer, dispatch executor, output-readiness, repeat-suppression, and managed-runtime routing for `recover_transport_model_provenance`.
- Preserve the no-forbidden-write boundary: no paper, manuscript package, publication eval, controller decision, or submission-readiness verdict is written by this owner.

Additional verification:

- `scripts/run-pytest-clean.sh tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/runtime_supervisor_consumer_cases/test_clean_rehydrate_owner_route.py tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py tests/test_owner_callable_registry.py -q`: 11 passed.

## Source Provenance Search Follow-Up

The first source-provenance owner patch correctly routed DM002 away from prose repair, but it only inspected fixed known refs before returning a typed blocker. That preserved authority boundaries, but did not yet give `opl-meta-agent` / Agent Lab a real recovery attempt to evaluate.

Follow-up patch:

- Extend the Agent Lab work order with `source_provenance_owner_recovery` and `mechanism-edit-ref:mas/source-provenance-owner-recovery`.
- Make `source_provenance_owner` search bounded study and runtime roots for candidate model/result/provenance artifacts while excluding supervisor/controller control packets.
- Accept only a `canonical_transport_model_provenance_bundle` with coefficients, feature order/coding, 5-year baseline survival or hazard, penalty/tuning provenance, standardization/scaler state, and original-result artifact ref.
- Keep result summaries, prose descriptions, and substitute refits as non-closing candidates; the owner records them in `provenance_search` but keeps `transport_model_provenance_recovery_required` open.
- If a complete canonical bundle is found, return `status=completed` and route back to `analysis_harmonization_owner` for the unit-harmonized rerun; still do not write paper, manuscript package, publication eval, controller decision, or submission-readiness verdict.

Additional verification:

- `scripts/run-pytest-clean.sh tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py -q`: 4 passed.
- `scripts/run-pytest-clean.sh tests/test_agent_lab_medical_manuscript_quality.py -q`: 4 passed.

## Source Provenance Currentness Follow-Up

The bounded search owner exposed a currentness gap in the scan read model: pre-search source-provenance typed blockers were still treated as complete owner outputs. That prevented upgraded MAS from rerunning the owner on DM002 and writing the newly required `provenance_search` evidence.

Follow-up patch:

- Require accepted source-provenance typed blockers to include `provenance_search.searched=true`.
- Require the blocker to explicitly keep `result_summary_acceptance_allowed=false` and `substitute_refit_allowed=false`.
- Treat pre-search blockers as pending owner output so supervisor scan requeues `recover_transport_model_provenance`.
- Keep post-search typed blockers as terminal owner outputs, avoiding repeated queue churn after the bounded search has been performed.
- Route post-search terminal blockers to `methodology_reframe_required` with `next_owner=decision`, so the controller must choose a new study route instead of repeatedly showing `source_provenance_owner` as the next executable owner.

Additional verification:

- `scripts/run-pytest-clean.sh tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py -q`: 8 passed.

## Methodology Reframe Decision Follow-Up

The source-provenance currentness patch correctly stopped the stale owner loop, but DM002 could still park at `blocked_reason=methodology_reframe_required` because the read model had no executable decision-owner action.

Follow-up patch:

- Add `methodology_reframe_route_decision` to owner-route, scan, consumer, dispatch executor, output-readiness, and terminal-stall handoff surfaces.
- Dispatch writes `artifacts/supervision/requests/decision/latest.json` and a controller decision in `artifacts/controller_decisions/latest.json`.
- The controller decision routes the same study back to `analysis-campaign` for methodology reframe and lists allowed decision options: stop-loss current transported-model claim, provenance-limited harmonization audit, reproducible-model rebuild, or human gate.
- Preserve the no-forbidden-write boundary: no paper, manuscript package, publication eval, or submission-readiness verdict is written by this owner.
- Extend the Agent Lab work order with `methodology_reframe_decision_owner_route` and `mechanism-edit-ref:mas/methodology-reframe-decision-owner-route`.

Additional verification:

- `scripts/run-pytest-clean.sh tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/runtime_supervisor_consumer_cases/test_clean_rehydrate_owner_route.py::test_supervisor_consume_routes_methodology_reframe_to_decision_owner tests/test_runtime_supervisor_dispatch_executor.py::test_execute_dispatch_routes_terminal_source_provenance_blocker_to_decision_owner tests/test_runtime_supervisor_dispatch_executor.py::test_execute_dispatch_hands_terminal_hard_methodology_route_to_analysis_owner tests/test_runtime_supervisor_dispatch_executor.py::test_execute_dispatch_hands_model_provenance_route_to_source_owner -q`: 8 passed.

## Provenance-Limited Runtime Authorization Follow-Up

The decision-owner route exposed one more currentness gap: the controller decision preserved the terminal source-provenance blocker fields, but the runtime prompt guard still recognized only the older unit-harmonization tokens. That allowed a valid `provenance_limited_harmonization_audit` authorization to miss the hard-methodology prompt contract.

Follow-up patch:

- Route terminal source-provenance blockers to `next_work_unit.unit_id=provenance_limited_harmonization_audit` instead of a prose/source-documentation repair unit.
- Preserve `selected_route_option`, `terminal_source_provenance_blocker_consumed`, and `current_transport_claim_must_not_be_used_as_medical_conclusion` through controller authorization compaction.
- Teach the runtime prompt hard-methodology guard to recognize the provenance-limited route and inject a contract forbidding contaminated transported-score reruns, medical conclusions from the current failure estimates, AI-reviewer-only reruns, package refreshes, or prose notes as closure.
- Preserve the no-forbidden-write boundary: this source patch does not write paper, manuscript package, publication eval, controller decision in a study workspace, or submission-readiness verdict.

Additional verification:

- `scripts/run-pytest-clean.sh tests/test_mas_runtime_core_turn_prompt_cases/test_current_controller_decision_authorization.py::test_codex_exec_runner_preserves_hard_methodology_route_fields_from_controller_decision -q`: 1 passed.
- `scripts/run-pytest-clean.sh tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_currentness.py tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/test_mas_runtime_core_turn_prompt_cases/test_current_controller_decision_authorization.py -q`: 21 passed.

## Provenance-Limited Owner Callable Follow-Up

The runtime authorization patch made the prompt contract correct, but the managed worker still blocked with `owner_callable_surface_missing` because `provenance_limited_harmonization_audit` had no executable MAS owner.

Follow-up patch:

- Add `provenance_limited_harmonization_owner.provenance_limited_harmonization_audit_or_typed_blocker`.
- Register `provenance_limited_harmonization_audit` across owner callable registry, owner route, supervisor scan, consumer, dispatch executor, persisted dispatches, managed-runtime authorization, output-readiness, repeat-suppression, and terminal-stall handoff.
- Write only `artifacts/controller/provenance_limited_harmonization/latest.json`.
- Preserve `current_transport_claim_must_not_be_used_as_medical_conclusion=true` and disallow current raw transported-score results as medical transportability conclusions.
- If original transported-model provenance is still unrecovered, type-block to clean reproducible rebuild authorization, stop-loss, or human gate; do not route back to prose/source-documentation repair.
- Preserve stale-decision currentness: if analysis/source owner results are newer than `methodology_reframe_route_decision`, scan requeues the decision instead of executing the provenance-limited audit from stale authority.

Additional verification:

- `scripts/run-pytest-clean.sh tests/test_owner_callable_registry.py tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_currentness.py -q`: 20 passed.
- `scripts/run-pytest-clean.sh tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_currentness.py tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/test_mas_runtime_core_turn_prompt_cases/test_current_controller_decision_authorization.py tests/test_owner_callable_registry.py -q`: 24 passed.
- `make test-meta`: 245 passed, 4160 deselected.
- `scripts/verify.sh`: repo hygiene audit passed; 4 passed.

## Human-Gate Rebuild Authorization Follow-Up

The provenance-limited owner correctly blocked DM002 at clean reproducible rebuild authorization, but the next user-authorized `methodology_rebuild_authorization` task intake was not a runtime-consumable route. Study truth still preferred older waiting/projection state, and the accepted provenance-limited typed blocker could remain satisfied even after the human gate had authorized a clean rebuild.

Follow-up patch:

- Treat `task_intake_kind=methodology_rebuild_authorization` as structured human-gate authorization for same-line methodology rebuild.
- Materialize that intake into study truth with `canonical_next_action=authorize_clean_reproducible_model_rebuild`.
- Invalidate stale `rebuild_reproducible_model_route_required` provenance-limited results when a later rebuild authorization exists.
- Re-execute provenance-limited owner so it consumes the authorization and routes to `analysis_harmonization_owner` with `blocked_reason=unit_harmonized_rerun_required`.
- Add supervisor scan projection from the authorized provenance-limited result to `unit_harmonized_external_validation_rerun`.
- Preserve the no-forbidden-write boundary: no paper, manuscript package, publication eval, controller decision, current package, or submission-readiness verdict is written by this route.

Additional verification:

- `scripts/run-pytest-clean.sh tests/test_study_truth_kernel.py tests/test_provenance_limited_harmonization_owner.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_route_priority.py -q`: 18 passed.

## Source-Provenance Currentness Follow-Up

The human-gate authorization route successfully reached `analysis_harmonization_owner`, but a live DM002 scan exposed another currentness issue: the new analysis owner result handed off to `source_provenance_owner`, while an older source-provenance search blocker and older provenance-limited route result could still be treated as current satisfied outputs. That produced `action_queue=[]` even though the current analysis blocker required model-provenance recovery.

Follow-up patch:

- Invalidate source-provenance satisfied output when a newer `analysis_harmonization/latest.json` requests `transport_model_provenance_recovery_required`.
- Invalidate provenance-limited satisfied output when a newer analysis owner result has taken over the clean rebuild route.
- Requeue `source_provenance_owner.recover_transport_model_provenance_or_typed_blocker` from the fresh analysis owner handoff.
- Preserve fail-closed semantics: current raw transported-score results and stale source search blockers still cannot authorize manuscript claims or publication readiness.

Additional verification:

- `scripts/run-pytest-clean.sh tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_route_priority.py tests/test_provenance_limited_harmonization_owner.py -q`: 11 passed.

## Clean Rebuild Decision Route Follow-Up

The source-provenance currentness patch made the stale-output loop visible, but DM002 could still cycle through the old provenance-limited audit route even after the user had explicitly authorized a clean reproducible-model rebuild. The defect was in the decision owner: `methodology_reframe_route_decision` always selected `provenance_limited_harmonization_audit` instead of consuming the clean rebuild authorization as a route choice.

Follow-up patch:

- Let `decision_owner.methodology_reframe_route_decision` read the structured `methodology_rebuild_authorization` task intake and the terminal source-provenance search blocker.
- When both are current, select `rebuild_reproducible_model_route` and write `next_work_unit.unit_id=unit_harmonized_external_validation_rerun` with `required_owner=analysis_harmonization_owner`.
- Add scan/read-model support so a clean rebuild decision directly queues `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`, without requiring another provenance-limited audit pass.
- Preserve the audit path for un-authorized terminal source-provenance blockers.
- Preserve fail-closed semantics: the clean route authorizes only a unit-harmonized rerun or typed blocker; it does not recover old Cox provenance, prove transportability failure, write paper/package surfaces, relax the quality gate, or declare submission readiness.

Additional verification:

- `scripts/run-pytest-clean.sh tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py::test_execute_dispatch_routes_authorized_terminal_source_blocker_to_clean_rebuild tests/runtime_supervisor_scan_cases/test_methodology_reframe_route_priority.py::test_scan_routes_clean_rebuild_decision_directly_to_analysis_owner tests/runtime_supervisor_scan_cases/test_methodology_reframe_currentness.py::test_clean_rebuild_methodology_decision_exposes_current_controller_runtime_route -q`: 3 passed.
- `scripts/run-pytest-clean.sh tests/test_runtime_supervisor_dispatch_executor_cases/hard_methodology_harmonization.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_route_priority.py tests/runtime_supervisor_scan_cases/test_methodology_reframe_currentness.py tests/runtime_supervisor_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/test_provenance_limited_harmonization_owner.py tests/test_mas_runtime_core_turn_prompt_cases/test_current_controller_decision_authorization.py -q`: 30 passed.

## Downstream Hard-Methodology Authorization Currentness Follow-Up

The clean-rebuild decision route was present, but a live DM002 worker could still start from the older `controller_decisions/latest.json` pointing at `provenance_limited_harmonization_audit` after the provenance-limited owner had already written `next_owner=analysis_harmonization_owner` and `next_work_unit=unit_harmonized_external_validation_rerun`. That made the worker repeat a completed audit rather than continue the downstream hard-methodology owner chain.

Follow-up patch:

- Teach MAS turn authorization to treat a completed provenance-limited owner result as superseding the stale audit controller decision when runtime state already carries a downstream unit-harmonized authorization.
- Prefer `unit_harmonized_validation_uncertainty_and_grouped_calibration` / `unit_harmonized_external_validation_rerun` in the managed worker prompt, while preserving the source-provenance and methodology-reframe paths when the provenance-limited owner result is absent or not current.
- Keep the boundary explicit: this is MAS medical owner-chain currentness and prompt authorization; it does not add an OPL-style generic queue, attempt ledger, provider runner, or session control plane to MAS.

## Route-Scan Rebuild Handoff Currentness Follow-Up

The turn prompt authorization patch fixed worker instructions, but DM002 then exposed the matching read-model defect: `domain-route-scan` still evaluated the older source-provenance terminal blocker before the newer provenance-limited owner result, so the next queued action returned to `methodology_reframe_route_decision` instead of continuing the already-authorized unit-harmonized rerun.

Follow-up patch:

- Treat a current provenance-limited `unit_harmonized_rerun_required` typed handoff to `analysis_harmonization_owner` as superseding the stale methodology-reframe decision route.
- Require that provenance-limited owner result to be newer than consumed source provenance, controller decision, and rebuild task-intake surfaces before it can suppress the older decision action.
- Preserve fail-closed behavior when the provenance-limited result is missing, stale, not a rebuild handoff, or not routed to `analysis_harmonization_owner`.
- Keep the OPL/MAS boundary explicit: the patch changes MAS domain owner-route currentness only; OPL remains the home for generic provider, queue, session, attempt, and Agent Lab control-plane mechanics.

Additional verification:

- `scripts/run-pytest-clean.sh tests/domain_route_scan_cases/test_methodology_reframe_route_priority.py::test_scan_prefers_current_provenance_limited_rebuild_handoff_over_stale_audit_decision -q`: 1 passed.
- `scripts/run-pytest-clean.sh tests/domain_route_scan_cases/test_methodology_reframe_route_priority.py tests/domain_route_scan_cases/test_methodology_reframe_currentness.py tests/domain_route_scan_cases/test_analysis_harmonization_owner_result_consumption.py tests/domain_route_scan_cases/test_hard_methodology_currentness.py -q`: 18 passed.
