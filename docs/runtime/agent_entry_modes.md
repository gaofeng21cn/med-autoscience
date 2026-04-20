# Agent Entry Modes

Canonical source: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`.

## Compatible Agents
- Codex, Claude Code, OpenClaw

## Runtime Modes
- lightweight, managed

## Mode Contract

### full_research (Full Research)
- default_runtime_mode: managed
- lightweight_scope: none
- preconditions: workspace/profile available
- managed_entry_actions: doctor | bootstrap | overlay-status | ensure-study-runtime
- lightweight_routes: (none)
- managed_routes: scout | idea | write | finalize
- startup_boundary_gated_routes: baseline | experiment | analysis-campaign
- governance_routes: decision
- auxiliary_routes: journal-resolution
- upgrade_triggers: (none)

### literature_scout (Literature Scout)
- default_runtime_mode: lightweight
- lightweight_scope: early evidence framing
- preconditions: workspace/profile available
- managed_entry_actions: doctor | bootstrap | overlay-status | ensure-study-runtime
- lightweight_routes: scout
- managed_routes: scout | idea | write | finalize
- startup_boundary_gated_routes: baseline | experiment | analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: hypothesis viability confirmed

### idea_exploration (Idea Exploration)
- default_runtime_mode: lightweight
- lightweight_scope: route selection and study framing
- preconditions: workspace/profile available
- managed_entry_actions: doctor | bootstrap | overlay-status | ensure-study-runtime
- lightweight_routes: idea | decision
- managed_routes: scout | idea | write | finalize
- startup_boundary_gated_routes: baseline | experiment | analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: experiment execution approved

### project_optimization (Project Optimization)
- default_runtime_mode: lightweight
- lightweight_scope: pathway adjustment and stop-loss
- preconditions: workspace/profile available
- managed_entry_actions: doctor | bootstrap | overlay-status | ensure-study-runtime
- lightweight_routes: decision
- managed_routes: scout | write | finalize
- startup_boundary_gated_routes: baseline | experiment | analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: major direction change approved

### writing_delivery (Writing Delivery)
- default_runtime_mode: lightweight
- lightweight_scope: manuscript and delivery packaging
- preconditions: workspace/profile available
- managed_entry_actions: doctor | bootstrap | overlay-status | ensure-study-runtime
- lightweight_routes: write
- managed_routes: write | finalize
- startup_boundary_gated_routes: (none)
- governance_routes: decision
- auxiliary_routes: journal-resolution
- upgrade_triggers: submission bundle or final delivery requested

## Route Contracts

### scout (Scout)
- goal: Freeze a question-worthy study direction, evidence target, and immediate route recommendation.
- enter_conditions: workspace/profile available | study question or dataset context is readable | current line still needs direction framing or evidence scoping
- hard_success_gate: question framing names the study target, population, and evidence boundary | route recommendation names the next formal route with reasons | blockers and assumptions are explicit enough for controller review
- durable_outputs_minimum: scout note or equivalent route artifact with evidence boundary and next-step recommendation | explicit open questions list tied to the study line | route recommendation linked to the active study charter boundary
- human_gate_boundary: primary question, target population, or evidence boundary needs reset | recommended next route would widen the active study charter boundary
- next_routes: baseline | write | decision
- route_back_triggers: evidence target stays ambiguous after scouting | study question changes materially during later routes | downstream review surfaces missing direction rationale

### idea (Idea)
- goal: Choose the strongest study line and freeze why it deserves managed execution.
- enter_conditions: scout output or equivalent direction framing exists | candidate study directions can be compared on the same problem boundary | active route still needs a chosen line before baseline work
- hard_success_gate: one primary line is selected with explicit tradeoffs | execution recommendation names whether to proceed to baseline or return to decision | chosen line matches the active study charter scope
- durable_outputs_minimum: line-selection note with rationale and discarded alternatives | explicit next-route recommendation with boundary assumptions | claim sketch or study objective aligned to the chosen line
- human_gate_boundary: chosen line changes the locked study direction or main claim family | execution recommendation needs a new managed-study commitment beyond the active charter
- next_routes: baseline | decision
- route_back_triggers: baseline readiness is still missing | chosen line conflicts with later evidence review | controller requests a different route bias

### baseline (Baseline)
- goal: Establish the baseline, comparator, and readiness proof for the active study line.
- enter_conditions: chosen study line exists | data source, cohort boundary, or reference baseline is available | startup boundary can justify managed baseline work
- hard_success_gate: baseline or comparator setup is reproducible and scoped to the active claim | baseline readout reveals whether the line is strong enough to continue | unresolved blockers are small enough for analysis-campaign or decision
- durable_outputs_minimum: baseline artifact set or equivalent reproducible baseline record | baseline summary tied to the active claim or study objective | explicit continue or reroute recommendation
- human_gate_boundary: comparator, cohort, or endpoint redefinition changes the active claim boundary | baseline readout points to a stop decision or a direction reset
- next_routes: analysis-campaign | write | decision
- route_back_triggers: baseline result cannot support the active claim | comparator or cohort definition changes materially | reviewer-first scan finds missing baseline proof

### experiment (Experiment)
- goal: Run a primary managed experiment when the study line needs fresh main-result execution.
- enter_conditions: startup boundary allows compute-stage work | baseline or equivalent readiness proof exists | study line has a concrete experiment target and stop condition
- hard_success_gate: primary experiment result is recorded with reproducible run context | result answers the intended study question for the current line | next step is clear between analysis-campaign, write, and decision
- durable_outputs_minimum: primary result artifact set with run context | experiment summary tied to the active claim boundary | explicit next-route recommendation after result inspection
- human_gate_boundary: primary experiment target changes the locked study boundary or main claim family | result interpretation would authorize a new externally visible claim
- next_routes: analysis-campaign | write | decision
- route_back_triggers: run outcome invalidates the current study line | result quality or reproducibility gaps block downstream review | controller boundary changes before interpretation stabilizes

### analysis-campaign (Analysis Campaign)
- goal: Close the bounded evidence gaps that still block claim acceptance or reviewer pressure.
- enter_conditions: baseline or primary result artifact exists | bounded analysis question is explicit | study charter still allows the requested follow-up analyses
- hard_success_gate: each targeted gap has a resolved outcome or explicit stop decision | added analyses stay within the bounded scope of the active line | resulting evidence package can support writing or a decision review
- durable_outputs_minimum: analysis campaign summary with question-to-result traceability | added result artifacts or evidence refs for every resolved gap | explicit record of remaining gaps that still require route-back
- human_gate_boundary: requested follow-up analysis adds a new primary claim or leaves bounded analysis scope | campaign needs another gate window beyond the predeclared analysis budget boundary
- next_routes: write | finalize | decision
- route_back_triggers: new gaps expand beyond bounded analysis scope | claim support weakens after follow-up analysis | reviewer-first scan requests a different baseline or study line

### write (Write)
- goal: Convert the current evidence line into a manuscript-facing narrative that can withstand review.
- enter_conditions: active claim and supporting evidence package are readable | required route artifacts are linked or referenced | reviewer-first pressure can be applied against the current draft
- hard_success_gate: manuscript line states claims that match cited evidence | open gaps, caveats, and next actions are explicit in the writing surface | draft is ready for finalize or route-back with named reasons
- durable_outputs_minimum: manuscript draft or section update tied to current claim scope | claim-evidence map or equivalent traceability surface | reviewer-first pass note with explicit concerns
- human_gate_boundary: manuscript claims expand beyond the current evidence package or locked study objective | draft is ready for external circulation or submission-facing release
- next_routes: finalize | decision
- route_back_triggers: any active claim lacks supporting evidence | reviewer-first scan finds unresolved logic, novelty, or rigor gaps | manuscript narrative changes the claim boundary

### finalize (Finalize)
- goal: Assemble the submission-facing package and verify that the line is ready for final judgment.
- enter_conditions: manuscript-facing draft exists | claim-evidence mapping is current | remaining risks are reviewable as a bounded package
- hard_success_gate: final package is internally consistent across claim, evidence, and limitations | required review artifacts are complete enough for final audit | route recommendation is explicit between submit-ready and route-back
- durable_outputs_minimum: final package checklist or equivalent delivery record | updated limitations, caveats, and readiness statement | final review summary with explicit go or reroute recommendation
- human_gate_boundary: submission-ready judgment or external delivery authorization is required | final package changes the claim, limitation, or outlet boundary materially
- next_routes: decision | write
- route_back_triggers: final audit finds missing proof or inconsistent claims | submission bundle surfaces unresolved reviewer-level concerns | package assembly changes the meaning of any active claim

### decision (Decision)
- goal: Record the official go, stop, reroute, or human-gate judgment for the active study line.
- enter_conditions: route recommendation or blocking condition is explicit | current evidence package and risks are reviewable | controller-owned judgment point has been reached
- hard_success_gate: decision names the chosen route or terminal judgment | rationale cites the current evidence and unresolved risks | downstream owner and next action are unambiguous
- durable_outputs_minimum: controller-facing decision record or equivalent durable judgment | cited evidence refs and route recommendation | explicit next owner or escalation target
- human_gate_boundary: official go, stop, reroute, or direction-reset judgment is required | decision changes the study boundary or authorizes external release
- next_routes: scout | baseline | analysis-campaign | write | finalize
- route_back_triggers: new evidence invalidates the recorded judgment | human gate changes the study boundary | downstream route reports unmet assumptions from the decision record

### journal-resolution (Journal Resolution)
- goal: Resolve journal-facing packaging choices before final delivery or submission prep.
- enter_conditions: writing line exists | target journal list or delivery target is known | packaging choices affect the current manuscript bundle
- hard_success_gate: target outlet or packaging rule is chosen with reasons | manuscript bundle requirements are reflected in the active draft plan | remaining journal-facing gaps are explicit
- durable_outputs_minimum: journal choice note or outlet-resolution record | packaging requirement checklist tied to the draft | explicit next route after journal alignment
- human_gate_boundary: outlet choice changes the claim framing, delivery plan, or submission commitments | journal selection requires external release or submission authorization
- next_routes: write | finalize | decision
- route_back_triggers: journal requirements expose missing evidence or structure gaps | target outlet changes the claim framing materially | packaging constraints require a different delivery plan

## Evidence And Review Contract
- minimum_proof_package: active study charter boundary, current route recommendation, and cited evidence refs must be readable together | every route must leave a durable artifact or durable reference path for the next route | writing and finalize routes must carry a current claim-evidence traceability surface
- reviewer_first_checks: apply reviewer-first pressure before treating any draft or package as ready | state the strongest concern first and tie it to the affected claim or evidence gap | record whether the concern routes back to scout, baseline, analysis-campaign, or write
- claim_evidence_consistency_requirements: every active claim must map to concrete evidence already present in the current proof package | caveats, limitations, and unsupported edges must stay visible in the same package | a route may only promote forward when claim wording and cited evidence stay aligned
- route_back_policy: route back immediately when a claim loses direct evidence support | route back immediately when reviewer-first checks expose a material gap in rigor, novelty, or relevance | route back to the narrowest earlier route that can close the gap while keeping the study boundary honest

## Upgrade Rules
If `upgrade_triggers` is non-empty and any trigger is satisfied, upgrade from lightweight to managed before continuing.

## Startup Boundary Rule
Run `ensure-study-runtime` before any managed compute decision. Do not enter `startup_boundary_gated_routes` unless that controller reports `startup_boundary_gate.allow_compute_stage = true`; otherwise stay within `managed_routes`, `governance_routes`, and any writing-only delivery route.

## Live Runtime Ownership Rule
If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode, notify the user, and do not write runtime-owned study surfaces.
Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.
