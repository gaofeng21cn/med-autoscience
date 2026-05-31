# MedAutoScience Agent Entry (Codex)

Use this stage route contract to select entry mode and route actions without changing canonical definitions.

Compatible agents: Codex, Claude Code, OpenClaw
Runtime modes: lightweight, managed

## Mode Contract
- full_research: runtime=managed, scope=none
  preconditions: workspace/profile available
  managed_entry_actions: doctor | bootstrap | overlay-status | request-opl-stage-attempt
  lightweight_routes: (none)
  managed_routes: scout | idea | write | finalize
  startup_boundary_gated_routes: baseline | experiment | analysis-campaign
  governance_routes: decision
  auxiliary_routes: journal-resolution
  upgrade_triggers: (none)
- literature_scout: runtime=lightweight, scope=early evidence framing
  preconditions: workspace/profile available
  managed_entry_actions: doctor | bootstrap | overlay-status | request-opl-stage-attempt
  lightweight_routes: scout
  managed_routes: scout | idea | write | finalize
  startup_boundary_gated_routes: baseline | experiment | analysis-campaign
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: hypothesis viability confirmed
- idea_exploration: runtime=lightweight, scope=route selection and study framing
  preconditions: workspace/profile available
  managed_entry_actions: doctor | bootstrap | overlay-status | request-opl-stage-attempt
  lightweight_routes: idea | decision
  managed_routes: scout | idea | write | finalize
  startup_boundary_gated_routes: baseline | experiment | analysis-campaign
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: experiment execution approved
- project_optimization: runtime=lightweight, scope=pathway adjustment and stop-loss
  preconditions: workspace/profile available
  managed_entry_actions: doctor | bootstrap | overlay-status | request-opl-stage-attempt
  lightweight_routes: decision
  managed_routes: scout | write | finalize
  startup_boundary_gated_routes: baseline | experiment | analysis-campaign
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: major direction change approved
- writing_delivery: runtime=lightweight, scope=manuscript and delivery packaging
  preconditions: workspace/profile available
  managed_entry_actions: doctor | bootstrap | overlay-status | request-opl-stage-attempt
  lightweight_routes: write
  managed_routes: write | finalize
  startup_boundary_gated_routes: (none)
  governance_routes: decision
  auxiliary_routes: journal-resolution
  upgrade_triggers: submission bundle or final delivery requested
- manuscript_fast_lane: runtime=lightweight, scope=controller-visible canonical manuscript text/structure revision from existing evidence only
  preconditions: workspace/profile available | latest task intake explicitly limits work to canonical paper text/structure or evidence repackaging from existing results | study is in manual_finishing or bundle-stage-ready state, or foreground takeover has been explicitly allowed | runtime is inactive, paused, stopped, or supervisor-only takeover rules allow foreground work
  managed_entry_actions: doctor | bootstrap | overlay-status | study-progress
  lightweight_routes: write | finalize
  managed_routes: write | finalize
  startup_boundary_gated_routes: (none)
  governance_routes: decision
  auxiliary_routes: journal-resolution
  upgrade_triggers: new analysis, new result claim, new table/figure computation, live runtime ownership, or claim-boundary change is needed

## Route Contracts
- scout: Scout
  key_question: Is this direction worth entering the current study line?
  goal: Freeze a question-worthy study direction, evidence target, and immediate route recommendation.
  enter_conditions: workspace/profile available | study question or dataset context is readable | current line still needs direction framing or evidence scoping
  hard_success_gate: question framing names the study target, population, and evidence boundary | Literature Scout OS records search strategy with MeSH, query, date, anchor papers, guideline, and journal-neighbor evidence anchors | route recommendation names the next formal route with reasons | blockers and assumptions are explicit enough for controller review
  durable_outputs_minimum: scout note or equivalent route artifact with evidence boundary and next-step recommendation | Literature Scout OS artifact with search strategy, MeSH/query/date, anchor papers, guideline, and journal-neighbor refs | explicit open questions list tied to the study line | route recommendation linked to the active study charter boundary
  human_gate_boundary: primary question, target population, or evidence boundary needs reset | recommended next route would widen the active study charter boundary
  next_routes: baseline | write | decision
  route_back_triggers: evidence target stays ambiguous after scouting | study question changes materially during later routes | downstream review surfaces missing direction rationale
  knowledge_input_obligations: stage_knowledge_packet_ref | portfolio_memory.topic_landscape | portfolio_memory.dataset_question_map | portfolio_memory.venue_intelligence | workspace_literature.coverage | literature_provider_runtime.readiness
  memory_closeout_obligations: stage_memory_closeout_packet | clinical_question_framing | literature_gap | anchor_paper_role | route_recommendation
- idea: Idea
  key_question: Which study line is strongest enough to justify the next route?
  goal: Choose the strongest study line and freeze why it deserves managed execution.
  enter_conditions: scout output or equivalent direction framing exists | candidate study directions can be compared on the same problem boundary | active route still needs a chosen line before baseline work
  hard_success_gate: one primary line is selected with explicit tradeoffs | Study Line Selection Scorecard compares novelty, clinical relevance, data fit, analysis plasticity, external validation, journal fit, cost-risk, and stop threshold | execution recommendation names whether to proceed to baseline or return to decision | chosen line matches the active study charter scope
  durable_outputs_minimum: line-selection note with rationale and discarded alternatives | Study Line Selection Scorecard with novelty, clinical relevance, data fit, analysis plasticity, external validation, journal fit, cost-risk, and stop threshold dimensions | explicit next-route recommendation with boundary assumptions | claim sketch or study objective aligned to the chosen line
  human_gate_boundary: chosen line changes the locked study direction or main claim family | execution recommendation needs a new managed-study commitment beyond the active charter
  next_routes: baseline | decision
  route_back_triggers: baseline readiness is still missing | chosen line conflicts with later evidence review | controller requests a different route bias
  knowledge_input_obligations: stage_knowledge_packet_ref | portfolio_memory.study_recall_index | study_reference_context | prior_candidate_or_failed_lines | journal_neighbor_refs
  memory_closeout_obligations: stage_memory_closeout_packet | selected_line | rejected_alternatives | selection_rationale | stop_rule | memory_reuse_note
- baseline: Baseline
  key_question: Does the current claim have reproducible baseline support?
  goal: Establish the baseline, comparator, and readiness proof for the active study line.
  enter_conditions: chosen study line exists | data source, cohort boundary, or reference baseline is available | startup boundary can justify managed baseline work
  hard_success_gate: baseline or comparator setup is reproducible and scoped to the active claim | baseline readout reveals whether the line is strong enough to continue | unresolved blockers are small enough for analysis-campaign or decision
  durable_outputs_minimum: baseline artifact set or equivalent reproducible baseline record | baseline summary tied to the active claim or study objective | explicit continue or reroute recommendation
  human_gate_boundary: comparator, cohort, or endpoint redefinition changes the active claim boundary | baseline readout points to a stop decision or a direction reset
  next_routes: analysis-campaign | write | decision
  route_back_triggers: baseline result cannot support the active claim | comparator or cohort definition changes materially | reviewer-first scan finds missing baseline proof
  knowledge_input_obligations: stage_knowledge_packet_ref | data_source_contract | cohort_definition_and_inclusion_exclusion | endpoint_definition_and_measurement_window | comparator_definition_and_reference_baseline | startup_run_context | prior_result_lineage | failed_comparator_history
  memory_closeout_obligations: stage_memory_closeout_packet | baseline_cohort_endpoint_comparator_snapshot | baseline_effect_size_or_feasibility_readout | failed_comparator_lesson | continue_reroute_or_stop_recommendation
- experiment: Experiment
  key_question: Does the primary result answer the current study question?
  goal: Run a primary managed experiment when the study line needs fresh main-result execution.
  enter_conditions: startup boundary allows compute-stage work | baseline or equivalent readiness proof exists | study line has a concrete experiment target and stop condition
  hard_success_gate: primary experiment result is recorded with reproducible run context | result answers the intended study question for the current line | next step is clear between analysis-campaign, write, and decision
  durable_outputs_minimum: primary result artifact set with run context | experiment summary tied to the active claim boundary | explicit next-route recommendation after result inspection
  human_gate_boundary: primary experiment target changes the locked study boundary or main claim family | result interpretation would authorize a new externally visible claim
  next_routes: analysis-campaign | write | decision
  route_back_triggers: run outcome invalidates the current study line | result quality or reproducibility gaps block downstream review | controller boundary changes before interpretation stabilizes
  knowledge_input_obligations: stage_knowledge_packet_ref | approved_experiment_protocol | data_contract_and_cohort_lock | endpoint_and_comparator_lock | statistical_analysis_plan | startup_run_context | prior_result_lineage | failed_comparator_history
  memory_closeout_obligations: stage_memory_closeout_packet | primary_result_with_run_context | result_lineage_update | endpoint_or_comparator_deviation | negative_or_failed_comparator_lesson
- analysis-campaign: Analysis Campaign
  key_question: Have the bounded evidence gaps been closed?
  goal: Close the bounded evidence gaps that still block claim acceptance or reviewer pressure.
  enter_conditions: baseline or primary result artifact exists | bounded analysis question is explicit | study charter still allows the requested follow-up analyses
  hard_success_gate: each targeted gap has a resolved outcome or explicit stop decision | Bounded Analysis Candidate Board records explore, exploit, fusion, debug, and stop candidates with target claim, expected evidence gain, cost/risk, clinical interpretability, and decision reason | added analyses stay within the bounded scope of the active line | resulting evidence package can support writing or a decision review
  durable_outputs_minimum: analysis campaign summary with question-to-result traceability | Bounded Analysis Candidate Board covering explore, exploit, fusion, debug, and stop options plus target claim, expected evidence gain, cost/risk, clinical interpretability, and decision reason | added result artifacts or evidence refs for every resolved gap | explicit record of remaining gaps that still require route-back | reviewer/Codex revision handoff when the bounded analysis is triggered by a user manuscript-change request
  human_gate_boundary: requested follow-up analysis adds a new primary claim or leaves bounded analysis scope | campaign needs another gate window beyond the predeclared analysis budget boundary
  next_routes: write | finalize | decision
  route_back_triggers: new gaps expand beyond bounded analysis scope | claim support weakens after follow-up analysis | reviewer-first scan requests a different baseline or study line
  knowledge_input_obligations: stage_knowledge_packet_ref | failed_path_history | evidence_ledger | citation_gaps | bounded_frontier | reviewer_concerns
  memory_closeout_obligations: stage_memory_closeout_packet | slice_ledger | negative_or_weak_result_interpretation | route_impact | failed_path_lesson
- write: Write
  key_question: Does the manuscript narrative faithfully carry the current evidence?
  goal: Convert the current evidence line into a manuscript-facing narrative that can withstand review.
  enter_conditions: active claim and supporting evidence package are readable | required route artifacts are linked or referenced | reviewer-first pressure can be applied against the current draft | user manuscript-change requests from Codex have been converted into a study revision intake with OPL runtime control boundary checked
  hard_success_gate: manuscript line states claims that match cited evidence | first-draft quality scan has checked underused data-asset dimensions before calling the draft ready | open gaps, caveats, and next actions are explicit in the writing surface | draft is ready for finalize or route-back with named reasons | explicit user/reviewer manuscript feedback after a stopped or submission-ready milestone has been handled as same-line revision reactivation, not as direct `current_package` editing
  durable_outputs_minimum: manuscript draft or section update tied to current claim scope | claim-evidence map or equivalent traceability surface | reviewer-first pass note with explicit concerns | first-draft quality note covering field-verified multicenter/geography, subgroup/association, guideline, and real-world constraint axes | revision handoff stating data source, scripts, changed tables/figures, claim guardrails, OPL provider attempt hydration/resume refs, and whether `current_package` was regenerated from controller-authorized `paper/`
  human_gate_boundary: manuscript claims expand beyond the current evidence package or locked study objective | draft is ready for external circulation or submission-facing release
  next_routes: finalize | decision
  route_back_triggers: any active claim lacks supporting evidence | reviewer-first scan finds unresolved logic, novelty, or rigor gaps | first-draft quality scan finds verified asset dimensions that can support a stronger bounded analysis or manuscript framing | manuscript narrative changes the claim boundary | foreground edits only touched `manuscript/current_package/` before OPL provider attempt hydration/resume and MAS owner authorization, or have not been reconciled into the canonical paper source
  knowledge_input_obligations: stage_knowledge_packet_ref | claim_evidence_map | reporting_guideline_pack | journal_neighbor_refs | display_to_claim_map
  memory_closeout_obligations: stage_memory_closeout_packet | writing_experience_lesson | claim_wording_boundary_decision | reporting_guideline_gap | display_to_claim_repair_request | journal_neighbor_positioning_lesson
- review: Review
  key_question: What should the strict AI reviewer send back before the line can advance?
  goal: Convert reviewer pressure, citation gaps, and evidence concerns into route-safe repair or decision work.
  enter_conditions: manuscript or manuscript-facing draft exists | claim-evidence map or evidence package is readable | study reference context and reviewer findings are available or explicitly missing
  hard_success_gate: reviewer action matrix maps each concern to evidence, citation, text, analysis, route decision, or human gate work | unsupported claims are downgraded or routed back before finalize | citation and reference gaps have repair requests or explicit blockers | reusable critique lessons are separated from study-specific truth
  durable_outputs_minimum: reviewer action matrix tied to publication eval or review ledger refs | evidence or citation repair request when literature grounding is insufficient | reusable critique lesson when the finding should change future stage defaults | explicit next route or human gate recommendation
  human_gate_boundary: reviewer conclusion would change study boundary, external release, or submission authorization | citation or evidence gap cannot be repaired inside the current charter
  next_routes: analysis-campaign | write | finalize | decision
  route_back_triggers: active claim lacks direct evidence support | novelty, rigor, or citation gap cannot be closed in writing | AI reviewer requests a different baseline, analysis-campaign, or route decision
  knowledge_input_obligations: stage_knowledge_packet_ref | manuscript | claim_evidence_map | display_to_claim_map | study_reference_context | citation_ledger_refs | ai_reviewer_calibration_memory | prior_reviewer_findings
  memory_closeout_obligations: stage_memory_closeout_packet | reviewer_action_matrix | evidence_or_citation_repair_request | reusable_critique_lesson
- finalize: Finalize
  key_question: Is the submission package ready for final audit?
  goal: Assemble the submission-facing package and verify that the line is ready for final judgment.
  enter_conditions: manuscript-facing draft exists | claim-evidence mapping is current | remaining risks are reviewable as a bounded package
  hard_success_gate: final package is internally consistent across claim, evidence, and limitations | required review artifacts are complete enough for final audit | route recommendation is explicit between submit-ready and route-back | no unreconciled foreground `current_package` revision overlay remains
  durable_outputs_minimum: final package checklist or equivalent delivery record | updated limitations, caveats, and readiness statement | final review summary with explicit go or reroute recommendation
  human_gate_boundary: submission-ready judgment or external delivery authorization is required | final package changes the claim, limitation, or outlet boundary materially
  next_routes: decision | write
  route_back_triggers: final audit finds missing proof or inconsistent claims | submission bundle surfaces unresolved reviewer-level concerns | package assembly changes the meaning of any active claim
  knowledge_input_obligations: stage_knowledge_packet_ref | publication_eval_latest | controller_decision_latest | package_freshness_proof | declarations_and_ethics_checklist | human_gate_status
  memory_closeout_obligations: stage_memory_closeout_packet | package_readiness_decision | package_freshness_or_staleness_lesson | declaration_or_ethics_blocker | human_gate_request_or_clearance
- decision: Decision
  key_question: Should the current study line continue, route back, stop, or enter a human gate?
  goal: Record the official go, stop, reroute, or human-gate judgment for the active study line.
  enter_conditions: route recommendation or blocking condition is explicit | current evidence package and risks are reviewable | controller-owned judgment point has been reached
  hard_success_gate: decision names the chosen route or terminal judgment | Stop-loss Memo is written when the line should stop, route back, or enter a human gate | rationale cites the current evidence and unresolved risks | downstream owner and next action are unambiguous
  durable_outputs_minimum: controller-facing decision record or equivalent durable judgment | Stop-loss Memo with attempted paths, failure reason, evidence gain ceiling, alternative routes, and human gate question when stop or route redesign is recommended | cited evidence refs and route recommendation | explicit next owner or escalation target
  human_gate_boundary: official go, stop, reroute, or direction-reset judgment is required | decision changes the study boundary or authorizes external release
  next_routes: scout | baseline | analysis-campaign | write | finalize
  route_back_triggers: new evidence invalidates the recorded judgment | human gate changes the study boundary | downstream route reports unmet assumptions from the decision record
  knowledge_input_obligations: stage_knowledge_packet_ref | publication_route_memory_refs | controller_decision_inputs | failed_path_history | stop_loss_context
  memory_closeout_obligations: stage_memory_closeout_packet | stop_or_pivot_lesson | route_impact | rejected_alternatives
- journal-resolution: Journal Resolution
  key_question: Which outlet or packaging path best preserves the current claim boundary?
  goal: Resolve journal-facing packaging choices before final delivery or submission prep.
  enter_conditions: writing line exists | target journal list or delivery target is known | packaging choices affect the current manuscript bundle
  hard_success_gate: target outlet or packaging rule is chosen with reasons | manuscript bundle requirements are reflected in the active draft plan | remaining journal-facing gaps are explicit
  durable_outputs_minimum: journal choice note or outlet-resolution record | packaging requirement checklist tied to the draft | explicit next route after journal alignment
  human_gate_boundary: outlet choice changes the claim framing, delivery plan, or submission commitments | journal selection requires external release or submission authorization
  next_routes: write | finalize | decision
  route_back_triggers: journal requirements expose missing evidence or structure gaps | target outlet changes the claim framing materially | packaging constraints require a different delivery plan
  knowledge_input_obligations: stage_knowledge_packet_ref | official_author_guideline | outlet_profile | exporter_profile_constraints | blocked_profile_evidence
  memory_closeout_obligations: stage_memory_closeout_packet | selected_outlet_or_profile_rationale | exporter_constraint_lesson | blocked_profile_decision | reporting_guideline_delta

## Late-Stage Progress Sprint Contract
- sprint_id: publishability_repair_sprint
- objective: Produce one reviewable late-stage paper/package delta before quality gate replay.
- covered_work_units: current_manuscript_prose_currentness_and_gate_replay_write_closeout
- covered_routes: write | review | finalize
- attempt_scope: consume current effective AI reviewer eval when its manuscript, evidence, and analysis refs are current | refresh durable prose currentness against canonical manuscript refs | replay publication gate against the effective eval and current manuscript/package refs | materialize candidate package/display freshness proof with not_submission_ready or gate_pending semantics | close the attempt with typed closeout refs that classify paper progress separately from platform repair
- control_plane_outputs: progress_delta | single_next_owner_blocker | human_gate | stop_loss
- forbidden_control_plane_outputs: record_only_reviewer_loop | stale_fingerprint_execution_block | provider_completed_without_typed_closeout | platform_repair_counted_as_paper_progress
- quality_gate_policy: reviewer and publication gate quality still decide readiness after sprint delta exists | candidate package/display freshness proof must not claim submission readiness | publication_eval/latest.json materialization lag cannot alone force a new reviewer-record route when an effective current archive is available
- authority_boundary: no direct paper body, memory body, artifact body, publication_eval/latest.json, controller_decisions/latest.json, or current_package write outside MAS owner callable | OPL/provider completion is not paper closure without owner receipt, typed blocker, human gate, stop-loss, or progress_delta refs

## Evidence And Review Contract
- minimum_proof_package: active study charter boundary, current route recommendation, and cited evidence refs must be readable together | every route must leave a durable artifact or durable reference path for the next route | writing and finalize routes must carry a current claim-evidence traceability surface
- reviewer_first_checks: apply reviewer-first pressure before treating any draft or package as ready | state the strongest concern first and tie it to the affected claim or evidence gap | test whether the current draft underuses verified timepoint, stakeholder, center/geography, guideline, subgroup, or adoption-constraint dimensions | record whether the concern routes back to scout, baseline, analysis-campaign, or write
- claim_evidence_consistency_requirements: every active claim must map to concrete evidence already present in the current proof package | caveats, limitations, and unsupported edges must stay visible in the same package | a route may only promote forward when claim wording and cited evidence stay aligned
- route_back_policy: route back immediately when a claim loses direct evidence support | route back immediately when reviewer-first checks expose a material gap in rigor, novelty, or relevance | route back to analysis-campaign when a too-light descriptive draft leaves verified data dimensions unused within the locked claim boundary | route back to the narrowest earlier route that can close the gap while keeping the study boundary honest

## Medical Handoff And Evidence Gate
- structured medical handoff: every route-to-route or agent-to-agent transfer must carry `from_route`, `to_route`, `study_id`, `quest_id`, `active_claim_boundary`, `changed_artifact_refs`, `evidence_refs`, `review_refs`, `acceptance_criteria`, `next_owner`, and `human_gate_reason` | the handoff must state the active claim boundary, changed artifacts, durable evidence/review surfaces, acceptance criteria, next owner, and human gate reason before another route can treat the work as closed | every terminal handoff must name the minimum forward delta, changed stage/paper/artifact surface, next owner, next work unit, and next forced target surface; a bare next owner is not a complete Progress-First closeout | a no-op closeout is valid only when it consumes a duplicate, failed-path, stale-currentness, or forbidden-surface ref and emits a typed blocker, human gate, stop-loss, or forced next target surface; repeated no-op for the same work unit without new consumed evidence is an anti-stall violation
- durable evidence refs: `evidence_refs` must point to durable MAS surfaces such as `evidence_ledger`, `review_ledger`, `publication_eval/latest.json`, `controller_decisions/latest.json`, and manuscript/package refs | chat summaries, memory, terminal prose, or screenshot-style QA cannot stand in for evidence authority
- medical QA feedback loop: `PASS`, `FAIL`, and `NEEDS_REVIEW` outcomes must bind each finding to a specific claim/evidence/rigor/submission hygiene gap | a `FAIL` must route back to the narrowest route that can close the gap without widening the active claim boundary
- AI reviewer gate: only AI reviewer-backed `publication_eval/latest.json` can drive reviewer-first ready or finalize-ready state | mechanical projection can only require `review_required` or `projection_only`; it cannot authorize publication-quality readiness
- no claim-only ready: generic persona library approval, non-medical QA gate output, NEXUS role approval, chat/memory summaries, terminal prose, and screenshot-style QA must not be promoted to MAS owner authority or medical paper quality authority

## Medical Route Quality Loop
- bounded medical repair loop: every reviewer, QA, gate-repair, or route-back loop must record `attempt_count`, `verdict`, `finding_refs`, `fix_refs`, `acceptance_criteria`, `next_route`, and `escalation_ref` | `PASS`, `FAIL`, and `NEEDS_REVIEW` are the only stable route QA verdicts; a `FAIL` may retry only within an explicit retry budget | exhausted retry budget must write `controller_decisions/latest.json` or `runtime_escalation_record.json` before any human gate or route redesign is requested
- default needs review gate: manuscript, bundle, or submission readiness defaults to `NEEDS_REVIEW` until durable evidence refs, review refs, and AI reviewer-backed `publication_eval/latest.json` close the active criteria | zero-issue, ready, production-ready, or done claims are invalid without linked evidence/review refs and an owner decision surface
- phase gate handoff: every route or phase gate handoff must carry preconditions, input refs, output refs, evidence refs, acceptance criteria, gate result, decision owner, carry-forward risks, and next route | no phase, route, write, finalize, or submission-facing advance may proceed when the gate result is missing, stale, or claim-only
- analysis-campaign statistical discipline: analysis-campaign planning must state the active hypothesis, endpoint, cohort/data quality constraints, statistical method, subgroup or multiplicity guardrails, and acceptance/failure criteria before running new analysis | sample-size, power, precision, or feasibility rationale must be explicit when the study design or dataset makes formal power calculation impossible | product A/B testing vocabulary, growth metrics, or generic experiment success labels must not become medical evidence authority
- incident postmortem feedback loop: repeated runtime recovery, publication gate, stale package, or evidence-review failures must produce an incident-style record with timeline, impact, root cause, prevention action, owner, and follow-up status | incident learning can update runbooks, telemetry, taxonomy, or controller specificity; it must not relax evidence gates, publication gates, or AI reviewer requirements

## Upgrade Rule
If `upgrade_triggers` is non-empty and any trigger is satisfied, upgrade from lightweight to managed before continuing.

## Startup Boundary Rule
Read MAS domain refs and request OPL provider hydration before any managed compute decision. Do not enter `startup_boundary_gated_routes` unless the MAS controller projection reports `startup_boundary_gate.allow_compute_stage = true`; otherwise stay within `managed_routes`, `governance_routes`, and any writing-only delivery route.

## OPL Runtime Control Rule
If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode, notify the user, report `browser_url`, `quest_session_api_url`, and `active_run_id` when present, and do not write OPL runtime-owned study surfaces.
Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.

## No Ad-hoc Execution Rule
When operating MAS-covered work, agents must use controller-authorized `CLI`, `MCP`, `product-entry`, or OPL-dispatched MAS domain handler surfaces before writing research outputs or advancing a study route.
If a required capability is not exposed through those MAS contracts, stop and close the contract gap in the repo-tracked controller/callable surface before continuing; do not bypass MAS with ad-hoc scripts, direct artifact edits, prompt-only research chains, or generic document/PDF/Office tooling.

## Revision Intake Rule
Treat reviewer feedback, manuscript revision, mentor feedback, 审稿意见, 导师反馈, 论文修改, and Introduction/Methods/Results/Figure/Table feedback as `reviewer_revision` study task intake.
Explicit user/reviewer manuscript feedback after a stopped, submission-ready, or finalize milestone reactivates the same study line; it is not permission to foreground-edit `manuscript/current_package`.
After writing the durable task intake, OPL must hydrate or resume the provider attempt from MAS owner refs before MAS domain handlers edit canonical paper sources and regenerate `current_package` from that authority.
