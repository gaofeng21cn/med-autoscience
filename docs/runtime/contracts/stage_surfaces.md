# MAS Stage Surfaces

Canonical route source: `agent/stages/stage_route_contract.yaml`.
Markdown is a generated human-reading surface; it is not machine truth.
OPL may only project, dispatch, and read refs.
MAS keeps domain truth, quality verdict, owner receipts, typed blockers, and artifact authority.

## Machine Boundary
- Machine truth owners: canonical route contract | stage knowledge plane contracts | MAS controller/domain-authority refs surfaces | publication_eval/latest.json | controller_decisions/latest.json | evidence/review ledgers | workspace artifact locator refs | OPL current-control-state for runtime control
- OPL allowed: projection | dispatch | read_refs
- OPL forbidden: domain_truth | quality_verdict | artifact_authority | memory_writeback_acceptance
- MAS authority: domain_truth | quality_verdict | artifact_authority | runtime_authority_refs | owner_receipt | typed_blocker

## Stage Cards

## scout

- Display name: Scout
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/scout`
- Key question: Is this direction worth entering the current study line?

### Purpose
- Freeze a question-worthy study direction, evidence target, and immediate route recommendation.

### Entry
- workspace/profile available
- study question or dataset context is readable
- current line still needs direction framing or evidence scoping

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | portfolio_memory.topic_landscape | portfolio_memory.dataset_question_map | portfolio_memory.venue_intelligence | workspace_literature.coverage | literature_provider_runtime.readiness

### Outputs
- scout note or equivalent route artifact with evidence boundary and next-step recommendation
- Literature Scout OS artifact with search strategy, MeSH/query/date, anchor papers, guideline, and journal-neighbor refs
- explicit open questions list tied to the study line
- route recommendation linked to the active study charter boundary

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: question framing names the study target, population, and evidence boundary | Literature Scout OS records search strategy with MeSH, query, date, anchor papers, guideline, and journal-neighbor evidence anchors | route recommendation names the next formal route with reasons | blockers and assumptions are explicit enough for controller review

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | clinical_question_framing | literature_gap | anchor_paper_role | route_recommendation

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/scout/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/scout/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['baseline', 'write', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: evidence target stays ambiguous after scouting | study question changes materially during later routes | downstream review surfaces missing direction rationale
- Human gate: primary question, target population, or evidence boundary needs reset | recommended next route would widen the active study charter boundary
- Next routes: baseline | write | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## idea

- Display name: Idea
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/idea`
- Key question: Which study line is strongest enough to justify the next route?

### Purpose
- Choose the strongest study line and freeze why it deserves managed execution.

### Entry
- scout output or equivalent direction framing exists
- candidate study directions can be compared on the same problem boundary
- active route still needs a chosen line before baseline work

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | portfolio_memory.study_recall_index | study_reference_context | prior_candidate_or_failed_lines | journal_neighbor_refs

### Outputs
- line-selection note with rationale and discarded alternatives
- Study Line Selection Scorecard with novelty, clinical relevance, data fit, analysis plasticity, external validation, journal fit, cost-risk, and stop threshold dimensions
- explicit next-route recommendation with boundary assumptions
- claim sketch or study objective aligned to the chosen line

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: one primary line is selected with explicit tradeoffs | Study Line Selection Scorecard compares novelty, clinical relevance, data fit, analysis plasticity, external validation, journal fit, cost-risk, and stop threshold | execution recommendation names whether to proceed to baseline or return to decision | chosen line matches the active study charter scope

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | selected_line | rejected_alternatives | selection_rationale | stop_rule | memory_reuse_note

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/idea/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/idea/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['baseline', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: baseline readiness is still missing | chosen line conflicts with later evidence review | controller requests a different route bias
- Human gate: chosen line changes the locked study direction or main claim family | execution recommendation needs a new managed-study commitment beyond the active charter
- Next routes: baseline | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## baseline

- Display name: Baseline
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/baseline`
- Key question: Does the current claim have reproducible baseline support?

### Purpose
- Establish the baseline, comparator, and readiness proof for the active study line.

### Entry
- chosen study line exists
- data source, cohort boundary, or reference baseline is available
- startup boundary can justify managed baseline work

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | data_source_contract | cohort_definition_and_inclusion_exclusion | endpoint_definition_and_measurement_window | comparator_definition_and_reference_baseline | startup_run_context | prior_result_lineage | failed_comparator_history

### Outputs
- baseline artifact set or equivalent reproducible baseline record
- baseline summary tied to the active claim or study objective
- explicit continue or reroute recommendation

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: baseline or comparator setup is reproducible and scoped to the active claim | baseline readout reveals whether the line is strong enough to continue | unresolved blockers are small enough for analysis-campaign or decision

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | baseline_cohort_endpoint_comparator_snapshot | baseline_effect_size_or_feasibility_readout | failed_comparator_lesson | continue_reroute_or_stop_recommendation

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/baseline/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/baseline/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['analysis-campaign', 'write', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: baseline result cannot support the active claim | comparator or cohort definition changes materially | reviewer-first scan finds missing baseline proof
- Human gate: comparator, cohort, or endpoint redefinition changes the active claim boundary | baseline readout points to a stop decision or a direction reset
- Next routes: analysis-campaign | write | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## experiment

- Display name: Experiment
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/experiment`
- Key question: Does the primary result answer the current study question?

### Purpose
- Run a primary managed experiment when the study line needs fresh main-result execution.

### Entry
- startup boundary allows compute-stage work
- baseline or equivalent readiness proof exists
- study line has a concrete experiment target and stop condition

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | approved_experiment_protocol | data_contract_and_cohort_lock | endpoint_and_comparator_lock | statistical_analysis_plan | startup_run_context | prior_result_lineage | failed_comparator_history

### Outputs
- primary result artifact set with run context
- experiment summary tied to the active claim boundary
- explicit next-route recommendation after result inspection

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: primary experiment result is recorded with reproducible run context | result answers the intended study question for the current line | next step is clear between analysis-campaign, write, and decision

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | primary_result_with_run_context | result_lineage_update | endpoint_or_comparator_deviation | negative_or_failed_comparator_lesson

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/experiment/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/experiment/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['analysis-campaign', 'write', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: run outcome invalidates the current study line | result quality or reproducibility gaps block downstream review | controller boundary changes before interpretation stabilizes
- Human gate: primary experiment target changes the locked study boundary or main claim family | result interpretation would authorize a new externally visible claim
- Next routes: analysis-campaign | write | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## analysis-campaign

- Display name: Analysis Campaign
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/analysis-campaign`
- Key question: Have the bounded evidence gaps been closed?

### Purpose
- Close the bounded evidence gaps that still block claim acceptance or reviewer pressure.

### Entry
- baseline or primary result artifact exists
- bounded analysis question is explicit
- study charter still allows the requested follow-up analyses

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | failed_path_history | evidence_ledger | citation_gaps | bounded_frontier | reviewer_concerns

### Outputs
- analysis campaign summary with question-to-result traceability
- Bounded Analysis Candidate Board covering explore, exploit, fusion, debug, and stop options plus target claim, expected evidence gain, cost/risk, clinical interpretability, and decision reason
- added result artifacts or evidence refs for every resolved gap
- explicit record of remaining gaps that still require route-back
- reviewer/Codex revision handoff when the bounded analysis is triggered by a user manuscript-change request

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: each targeted gap has a resolved outcome or explicit stop decision | Bounded Analysis Candidate Board records explore, exploit, fusion, debug, and stop candidates with target claim, expected evidence gain, cost/risk, clinical interpretability, and decision reason | added analyses stay within the bounded scope of the active line | resulting evidence package can support writing or a decision review

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | slice_ledger | negative_or_weak_result_interpretation | route_impact | failed_path_lesson

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/analysis-campaign/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/analysis-campaign/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['write', 'finalize', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: new gaps expand beyond bounded analysis scope | claim support weakens after follow-up analysis | reviewer-first scan requests a different baseline or study line
- Human gate: requested follow-up analysis adds a new primary claim or leaves bounded analysis scope | campaign needs another gate window beyond the predeclared analysis budget boundary
- Next routes: write | finalize | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## write

- Display name: Write
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/write`
- Key question: Does the manuscript narrative faithfully carry the current evidence?

### Purpose
- Convert the current evidence line into a manuscript-facing narrative that can withstand review.

### Entry
- active claim and supporting evidence package are readable
- required route artifacts are linked or referenced
- reviewer-first pressure can be applied against the current draft
- user manuscript-change requests from Codex have been converted into a study revision intake with OPL runtime control boundary checked

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | claim_evidence_map | reporting_guideline_pack | journal_neighbor_refs | display_to_claim_map

### Outputs
- manuscript draft or section update tied to current claim scope
- claim-evidence map or equivalent traceability surface
- reviewer-first pass note with explicit concerns
- first-draft quality note covering field-verified multicenter/geography, subgroup/association, guideline, and real-world constraint axes
- revision handoff stating data source, scripts, changed tables/figures, claim guardrails, OPL provider attempt hydration/resume refs, and whether `current_package` was regenerated from controller-authorized `paper/`

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: manuscript line states claims that match cited evidence | first-draft quality scan has checked underused data-asset dimensions before calling the draft ready | open gaps, caveats, and next actions are explicit in the writing surface | draft is ready for finalize or route-back with named reasons | explicit user/reviewer manuscript feedback after a stopped or submission-ready milestone has been handled as same-line revision reactivation, not as direct `current_package` editing

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | writing_experience_lesson | claim_wording_boundary_decision | reporting_guideline_gap | display_to_claim_repair_request | journal_neighbor_positioning_lesson

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/write/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/write/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['finalize', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: any active claim lacks supporting evidence | reviewer-first scan finds unresolved logic, novelty, or rigor gaps | first-draft quality scan finds verified asset dimensions that can support a stronger bounded analysis or manuscript framing | manuscript narrative changes the claim boundary | foreground edits only touched `manuscript/current_package/` before OPL provider attempt hydration/resume and MAS owner authorization, or have not been reconciled into the canonical paper source
- Human gate: manuscript claims expand beyond the current evidence package or locked study objective | draft is ready for external circulation or submission-facing release
- Next routes: finalize | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## review

- Display name: Review
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/review`
- Key question: What should the strict AI reviewer send back before the line can advance?

### Purpose
- Convert reviewer pressure, citation gaps, and evidence concerns into route-safe repair or decision work.

### Entry
- manuscript or manuscript-facing draft exists
- claim-evidence map or evidence package is readable
- study reference context and reviewer findings are available or explicitly missing

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | manuscript | claim_evidence_map | display_to_claim_map | study_reference_context | citation_ledger_refs | ai_reviewer_calibration_memory | prior_reviewer_findings

### Outputs
- reviewer action matrix tied to publication eval or review ledger refs
- evidence or citation repair request when literature grounding is insufficient
- reusable critique lesson when the finding should change future stage defaults
- explicit next route or human gate recommendation

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: reviewer action matrix maps each concern to evidence, citation, text, analysis, route decision, or human gate work | unsupported claims are downgraded or routed back before finalize | citation and reference gaps have repair requests or explicit blockers | reusable critique lessons are separated from study-specific truth

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | reviewer_action_matrix | evidence_or_citation_repair_request | reusable_critique_lesson

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/review/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/review/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['analysis-campaign', 'write', 'finalize', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: active claim lacks direct evidence support | novelty, rigor, or citation gap cannot be closed in writing | AI reviewer requests a different baseline, analysis-campaign, or route decision
- Human gate: reviewer conclusion would change study boundary, external release, or submission authorization | citation or evidence gap cannot be repaired inside the current charter
- Next routes: analysis-campaign | write | finalize | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## finalize

- Display name: Finalize
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/finalize`
- Key question: Is the submission package ready for final audit?

### Purpose
- Assemble the submission-facing package and verify that the line is ready for final judgment.

### Entry
- manuscript-facing draft exists
- claim-evidence mapping is current
- remaining risks are reviewable as a bounded package

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | publication_eval_latest | controller_decision_latest | package_freshness_proof | declarations_and_ethics_checklist | human_gate_status

### Outputs
- final package checklist or equivalent delivery record
- updated limitations, caveats, and readiness statement
- final review summary with explicit go or reroute recommendation

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: final package is internally consistent across claim, evidence, and limitations | required review artifacts are complete enough for final audit | route recommendation is explicit between submit-ready and route-back | no unreconciled foreground `current_package` revision overlay remains

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | package_readiness_decision | package_freshness_or_staleness_lesson | declaration_or_ethics_blocker | human_gate_request_or_clearance

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/finalize/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/finalize/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['decision', 'write'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: final audit finds missing proof or inconsistent claims | submission bundle surfaces unresolved reviewer-level concerns | package assembly changes the meaning of any active claim
- Human gate: submission-ready judgment or external delivery authorization is required | final package changes the claim, limitation, or outlet boundary materially
- Next routes: decision | write

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## decision

- Display name: Decision
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/decision`
- Key question: Should the current study line continue, route back, stop, or enter a human gate?

### Purpose
- Record the official go, stop, reroute, or human-gate judgment for the active study line.

### Entry
- route recommendation or blocking condition is explicit
- current evidence package and risks are reviewable
- controller-owned judgment point has been reached

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | publication_route_memory_refs | controller_decision_inputs | failed_path_history | stop_loss_context

### Outputs
- controller-facing decision record or equivalent durable judgment
- Stop-loss Memo with attempted paths, failure reason, evidence gain ceiling, alternative routes, and human gate question when stop or route redesign is recommended
- cited evidence refs and route recommendation
- explicit next owner or escalation target

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: decision names the chosen route or terminal judgment | Stop-loss Memo is written when the line should stop, route back, or enter a human gate | rationale cites the current evidence and unresolved risks | downstream owner and next action are unambiguous

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | stop_or_pivot_lesson | route_impact | rejected_alternatives

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/decision/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/decision/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['scout', 'baseline', 'analysis-campaign', 'write', 'finalize'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: new evidence invalidates the recorded judgment | human gate changes the study boundary | downstream route reports unmet assumptions from the decision record
- Human gate: official go, stop, reroute, or direction-reset judgment is required | decision changes the study boundary or authorizes external release
- Next routes: scout | baseline | analysis-campaign | write | finalize

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback

## journal-resolution

- Display name: Journal Resolution
- Machine source: `agent/stages/stage_route_contract.yaml#/route_contracts/journal-resolution`
- Key question: Which outlet or packaging path best preserves the current claim boundary?

### Purpose
- Resolve journal-facing packaging choices before final delivery or submission prep.

### Entry
- writing line exists
- target journal list or delivery target is known
- packaging choices affect the current manuscript bundle

### Allowed Tools
- MAS controller-authorized CLI/MCP/product-entry domain handler surfaces
- stage-knowledge-packet
- stage-memory-closeout-route
- owner-route-reconcile
- ai-reviewer-publication-eval
- publication-gate
- Boundary: `controller_authorized_surfaces_only`

### Knowledge
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_knowledge_packet | stage_recall_index | publication_route_memory_pack | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_knowledge_packet_ref | official_author_guideline | outlet_profile | exporter_profile_constraints | blocked_profile_evidence

### Outputs
- journal choice note or outlet-resolution record
- packaging requirement checklist tied to the draft
- explicit next route after journal alignment

### Quality
- Verdict owner: MedAutoScience
- Machine source refs: publication_eval/latest.json | review_ledger | evidence_ledger | controller_decisions/latest.json | agent/stages/stage_route_contract.yaml#/evidence_review_contract
- Route success gate: target outlet or packaging rule is chosen with reasons | manuscript bundle requirements are reflected in the active draft plan | remaining journal-facing gaps are explicit

### Closeout
- Status: declared_in_canonical_route_contract
- Machine source refs: stage_memory_closeout_packet | memory_write_router_receipt | src/med_autoscience/stage_knowledge_contract.py
- Obligations: stage_memory_closeout_packet | selected_outlet_or_profile_rationale | exporter_constraint_lesson | blocked_profile_decision | reporting_guideline_delta

### Deliverable Index
- Input refs: stage_knowledge_packet -> artifacts/stage_knowledge/journal-resolution/latest.json | active_study_charter -> artifacts/controller/study_charter.json | stage_entry_conditions -> enter_conditions
- Output refs: durable_outputs_minimum -> durable_outputs_minimum | stage_memory_closeout_packet -> artifacts/stage_knowledge/journal-resolution/closeouts | memory_write_router_receipt -> artifacts/stage_knowledge/memory_write_router_receipts
- Ledger refs: evidence_ledger -> evidence_ledger | review_ledger -> review_ledger | controller_decision -> controller_decisions/latest.json
- Quality gate ref: owner=MedAutoScience, publication_readiness_authority=False, ref=publication_eval/latest.json, ref_kind=durable_surface, role=ai_reviewer_or_publication_gate_projection
- Package/artifact delta ref: body_included=False, owner=MedAutoScience, ref=package_freshness_proof_or_artifact_delta_proof, ref_kind=durable_surface, role=paper_asset_delta_evidence
- Source map ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_source_map, ref_kind=durable_surface, role=source_map
- Page-block anchor ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_page_block_anchors, ref_kind=durable_surface, role=page_block_anchors
- Figure-near-claim ref: body_included=False, can_write_mas_truth=False, owner=MedAutoScience, ref=stage_review_figure_near_claim_refs, ref_kind=durable_surface, role=figure_near_claim_refs
- Paper presentation note: body_included=False, can_authorize_publication_readiness=False, can_authorize_quality_verdict=False, can_authorize_submission_readiness=False, can_write_mas_truth=False, evidence_spine_required=True, mode=optional_deliverable_note, projection_kind=evidence_spine_presentation
- Next owner: next_routes=['write', 'finalize', 'decision'], owner=MedAutoScience, source_ref=route_contract.next_routes

### One-Page Paper Review
- paper_question: 本阶段要回答的论文问题
- stage_inputs: 本阶段输入
- work_completed: 本阶段完成的工作
- manuscript_or_artifact_delta: 论文资产变化
- claim_trace: 跨阶段 claim 影响
- evidence_and_citation_basis: 证据与引用依据
- quality_judgment: 质量判断
- freshness_signal: stale / freshness 红黄绿
- advance_decision: 是否进入下一阶段
- route_back_or_human_gate: 退回原因或人工决策点

### Route Back / Human Gate
- Route back: journal requirements expose missing evidence or structure gaps | target outlet changes the claim framing materially | packaging constraints require a different delivery plan
- Human gate: outlet choice changes the claim framing, delivery plan, or submission commitments | journal selection requires external release or submission authorization
- Next routes: write | finalize | decision

### OPL Boundary
- May: project | dispatch | read source refs
- Must not: write MAS domain truth | authorize quality verdicts | own canonical artifacts | accept memory writeback
