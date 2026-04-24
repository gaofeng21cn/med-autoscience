from __future__ import annotations

from . import chunk_01 as chunk_01
from . import chunk_02 as chunk_02
from . import chunk_03 as chunk_03
from . import chunk_04 as chunk_04

chunk_01.__dict__.update({
    "_task_intake_scoped_quality_agenda": chunk_02._task_intake_scoped_quality_agenda,
    "_quality_revision_plan_id": chunk_02._quality_revision_plan_id,
    "_quality_review_loop_id": chunk_02._quality_review_loop_id,
    "_top_quality_revision_dimension": chunk_02._top_quality_revision_dimension,
    "_quality_revision_action_type": chunk_02._quality_revision_action_type,
    "_quality_revision_route_target": chunk_02._quality_revision_route_target,
    "_default_quality_revision_action": chunk_02._default_quality_revision_action,
    "_quality_revision_done_criteria": chunk_02._quality_revision_done_criteria,
    "_quality_revision_item_priority": chunk_02._quality_revision_item_priority,
    "_quality_revision_item": chunk_02._quality_revision_item,
    "_quality_revision_plan_from_summary_payload": chunk_02._quality_revision_plan_from_summary_payload,
    "_quality_revision_candidates": chunk_02._quality_revision_candidates,
    "_quality_revision_plan": chunk_02._quality_revision_plan,
    "_normalized_weight_contract": chunk_02._normalized_weight_contract,
    "_normalized_text_list": chunk_02._normalized_text_list,
    "_normalized_quality_revision_item": chunk_02._normalized_quality_revision_item,
    "_normalized_quality_revision_plan": chunk_02._normalized_quality_revision_plan,
    "_quality_review_loop_phase": chunk_02._quality_review_loop_phase,
    "_quality_review_loop_blocking_issues": chunk_02._quality_review_loop_blocking_issues,
    "_quality_review_loop_summary": chunk_02._quality_review_loop_summary,
    "_quality_review_loop_recommended_next_action": chunk_02._quality_review_loop_recommended_next_action,
    "_quality_review_loop_from_summary_payload": chunk_02._quality_review_loop_from_summary_payload,
    "_quality_execution_lane_from_summary_payload": chunk_03._quality_execution_lane_from_summary_payload,
    "_normalized_quality_execution_lane_payload": chunk_03._normalized_quality_execution_lane_payload,
    "_same_line_route_surface_from_summary_payload": chunk_03._same_line_route_surface_from_summary_payload,
    "_normalized_same_line_route_surface_payload": chunk_03._normalized_same_line_route_surface_payload,
    "_normalized_same_line_route_truth_payload": chunk_03._normalized_same_line_route_truth_payload,
    "_normalized_quality_review_loop": chunk_03._normalized_quality_review_loop,
    "_quality_review_agenda": chunk_03._quality_review_agenda,
    "_fallback_refs": chunk_03._fallback_refs,
    "_coerce_quality_basis_item": chunk_03._coerce_quality_basis_item,
    "_publication_gate_quality_basis": chunk_03._publication_gate_quality_basis,
    "_quality_closure_basis": chunk_03._quality_closure_basis,
    "_quality_closure_truth": chunk_03._quality_closure_truth,
    "_quality_execution_lane": chunk_03._quality_execution_lane,
    "_load_review_ledger_context": chunk_03._load_review_ledger_context,
    "_study_quality_truth_from_summary_payload": chunk_03._study_quality_truth_from_summary_payload,
    "build_same_line_route_truth": chunk_03.build_same_line_route_truth,
    "_build_evaluation_summary_payload": chunk_04._build_evaluation_summary_payload,
    "_normalized_promotion_gate": chunk_04._normalized_promotion_gate,
    "_normalized_evaluation_summary": chunk_04._normalized_evaluation_summary,
    "read_promotion_gate": chunk_04.read_promotion_gate,
    "read_evaluation_summary": chunk_04.read_evaluation_summary,
    "materialize_evaluation_summary_artifacts": chunk_04.materialize_evaluation_summary_artifacts,
})
chunk_02.__dict__.update({
    "_quality_execution_lane_from_summary_payload": chunk_03._quality_execution_lane_from_summary_payload,
    "_normalized_quality_execution_lane_payload": chunk_03._normalized_quality_execution_lane_payload,
    "_same_line_route_surface_from_summary_payload": chunk_03._same_line_route_surface_from_summary_payload,
    "_normalized_same_line_route_surface_payload": chunk_03._normalized_same_line_route_surface_payload,
    "_normalized_same_line_route_truth_payload": chunk_03._normalized_same_line_route_truth_payload,
    "_normalized_quality_review_loop": chunk_03._normalized_quality_review_loop,
    "_quality_review_agenda": chunk_03._quality_review_agenda,
    "_fallback_refs": chunk_03._fallback_refs,
    "_coerce_quality_basis_item": chunk_03._coerce_quality_basis_item,
    "_publication_gate_quality_basis": chunk_03._publication_gate_quality_basis,
    "_quality_closure_basis": chunk_03._quality_closure_basis,
    "_quality_closure_truth": chunk_03._quality_closure_truth,
    "_quality_execution_lane": chunk_03._quality_execution_lane,
    "_load_review_ledger_context": chunk_03._load_review_ledger_context,
    "_study_quality_truth_from_summary_payload": chunk_03._study_quality_truth_from_summary_payload,
    "build_same_line_route_truth": chunk_03.build_same_line_route_truth,
    "_build_evaluation_summary_payload": chunk_04._build_evaluation_summary_payload,
    "_normalized_promotion_gate": chunk_04._normalized_promotion_gate,
    "_normalized_evaluation_summary": chunk_04._normalized_evaluation_summary,
    "read_promotion_gate": chunk_04.read_promotion_gate,
    "read_evaluation_summary": chunk_04.read_evaluation_summary,
    "materialize_evaluation_summary_artifacts": chunk_04.materialize_evaluation_summary_artifacts,
})
chunk_03.__dict__.update({
    "_build_evaluation_summary_payload": chunk_04._build_evaluation_summary_payload,
    "_normalized_promotion_gate": chunk_04._normalized_promotion_gate,
    "_normalized_evaluation_summary": chunk_04._normalized_evaluation_summary,
    "read_promotion_gate": chunk_04.read_promotion_gate,
    "read_evaluation_summary": chunk_04.read_evaluation_summary,
    "materialize_evaluation_summary_artifacts": chunk_04.materialize_evaluation_summary_artifacts,
})

__all__ = chunk_01.__all__

STABLE_EVALUATION_SUMMARY_RELATIVE_PATH = chunk_01.STABLE_EVALUATION_SUMMARY_RELATIVE_PATH
STABLE_PROMOTION_GATE_RELATIVE_PATH = chunk_01.STABLE_PROMOTION_GATE_RELATIVE_PATH
_GAP_SEVERITIES = chunk_01._GAP_SEVERITIES
_GAP_SEVERITY_RANK = chunk_01._GAP_SEVERITY_RANK
_GAP_SEVERITY_LABELS = chunk_01._GAP_SEVERITY_LABELS
_ACTION_PRIORITY_RANK = chunk_01._ACTION_PRIORITY_RANK
_ROUTE_REPAIR_ACTION_TYPES = chunk_01._ROUTE_REPAIR_ACTION_TYPES
_QUALITY_DIMENSION_STATUSES = chunk_01._QUALITY_DIMENSION_STATUSES
_QUALITY_CLOSURE_STATES = chunk_01._QUALITY_CLOSURE_STATES
_QUALITY_CLOSURE_BASIS_KEYS = chunk_01._QUALITY_CLOSURE_BASIS_KEYS
_QUALITY_REVIEW_STATUS_RANK = chunk_01._QUALITY_REVIEW_STATUS_RANK
_QUALITY_ASSESSMENT_REVIEW_ORDER = chunk_01._QUALITY_ASSESSMENT_REVIEW_ORDER
_QUALITY_EXECUTION_LANE_LABELS = chunk_01._QUALITY_EXECUTION_LANE_LABELS
_SAME_LINE_ROUTE_STATES = chunk_01._SAME_LINE_ROUTE_STATES
_SAME_LINE_ROUTE_STATE_LABELS = chunk_01._SAME_LINE_ROUTE_STATE_LABELS
_SAME_LINE_ROUTE_MODES = chunk_01._SAME_LINE_ROUTE_MODES
_SAME_LINE_ROUTE_TARGET_LABELS = chunk_01._SAME_LINE_ROUTE_TARGET_LABELS
_PUBLICATION_CRITIQUE_WEIGHT_CONTRACT = chunk_01._PUBLICATION_CRITIQUE_WEIGHT_CONTRACT
_PUBLICATION_CRITIQUE_ACTION_CONTRACT = chunk_01._PUBLICATION_CRITIQUE_ACTION_CONTRACT
_QUALITY_REVISION_PLAN_STATUSES = chunk_01._QUALITY_REVISION_PLAN_STATUSES
_QUALITY_REVISION_ITEM_PRIORITIES = chunk_01._QUALITY_REVISION_ITEM_PRIORITIES
_QUALITY_REVISION_PRIORITY_BY_STATUS = chunk_01._QUALITY_REVISION_PRIORITY_BY_STATUS
_QUALITY_REVISION_DIMENSIONS = chunk_01._QUALITY_REVISION_DIMENSIONS
_QUALITY_REVISION_ACTION_BY_DIMENSION = chunk_01._QUALITY_REVISION_ACTION_BY_DIMENSION
_QUALITY_REVISION_DEFAULT_ACTIONS = chunk_01._QUALITY_REVISION_DEFAULT_ACTIONS
_QUALITY_REVISION_DEFAULT_DONE_CRITERIA = chunk_01._QUALITY_REVISION_DEFAULT_DONE_CRITERIA
_QUALITY_REVIEW_LOOP_PHASES = chunk_01._QUALITY_REVIEW_LOOP_PHASES
_QUALITY_REVIEW_LOOP_PHASE_LABELS = chunk_01._QUALITY_REVIEW_LOOP_PHASE_LABELS
_QUALITY_REVIEW_LOOP_NEXT_PHASES = chunk_01._QUALITY_REVIEW_LOOP_NEXT_PHASES
_QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS = chunk_01._QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS
_TASK_INTAKE_REPORTING_SCOPE_HINTS = chunk_01._TASK_INTAKE_REPORTING_SCOPE_HINTS
_TASK_INTAKE_NO_CLAIM_REOPEN_HINTS = chunk_01._TASK_INTAKE_NO_CLAIM_REOPEN_HINTS
_TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS = chunk_01._TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS
_TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS = chunk_01._TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS
_TASK_INTAKE_STATUS_RECHECK_HINTS = chunk_01._TASK_INTAKE_STATUS_RECHECK_HINTS
_TASK_INTAKE_DISPLAY_REGISTRY_HINTS = chunk_01._TASK_INTAKE_DISPLAY_REGISTRY_HINTS
_TASK_INTAKE_SHELL_INPUT_HINTS = chunk_01._TASK_INTAKE_SHELL_INPUT_HINTS
stable_evaluation_summary_path = chunk_01.stable_evaluation_summary_path
stable_promotion_gate_path = chunk_01.stable_promotion_gate_path
_resolve_stable_ref = chunk_01._resolve_stable_ref
resolve_evaluation_summary_ref = chunk_01.resolve_evaluation_summary_ref
resolve_promotion_gate_ref = chunk_01.resolve_promotion_gate_ref
_required_text = chunk_01._required_text
_required_bool = chunk_01._required_bool
_optional_text = chunk_01._optional_text
_required_choice = chunk_01._required_choice
_required_mapping = chunk_01._required_mapping
_required_string_list = chunk_01._required_string_list
_optional_string_list = chunk_01._optional_string_list
_same_line_route_target_label = chunk_01._same_line_route_target_label
_read_json_object = chunk_01._read_json_object
_normalize_runtime_escalation_ref = chunk_01._normalize_runtime_escalation_ref
_normalize_gate_report = chunk_01._normalize_gate_report
_build_promotion_gate_payload = chunk_01._build_promotion_gate_payload
_gap_counts = chunk_01._gap_counts
_recommended_action_types = chunk_01._recommended_action_types
_route_repair_plan = chunk_01._route_repair_plan
_highest_priority_gap = chunk_01._highest_priority_gap
_highest_priority_action = chunk_01._highest_priority_action
_agenda_field = chunk_01._agenda_field
_agenda_summary = chunk_01._agenda_summary
_quality_review_agenda_from_summary_payload = chunk_01._quality_review_agenda_from_summary_payload
_reviewer_agenda_from_quality_assessment = chunk_01._reviewer_agenda_from_quality_assessment
_normalized_quality_review_agenda = chunk_01._normalized_quality_review_agenda
_unique_non_empty_texts = chunk_01._unique_non_empty_texts
_task_intake_scope_texts = chunk_01._task_intake_scope_texts
_task_intake_contains_hint = chunk_01._task_intake_contains_hint
_format_revision_scope_targets = chunk_01._format_revision_scope_targets
annotations = chunk_01.annotations
json = chunk_01.json
Path = chunk_01.Path
Any = chunk_01.Any
DEFAULT_PUBLICATION_CRITIQUE_POLICY = chunk_01.DEFAULT_PUBLICATION_CRITIQUE_POLICY
build_publication_critique_weight_contract = chunk_01.build_publication_critique_weight_contract
build_revision_action_contract = chunk_01.build_revision_action_contract
read_publication_eval_latest = chunk_01.read_publication_eval_latest
stable_publication_eval_latest_path = chunk_01.stable_publication_eval_latest_path
derive_quality_closure_truth = chunk_01.derive_quality_closure_truth
derive_quality_execution_lane = chunk_01.derive_quality_execution_lane
build_study_quality_truth = chunk_01.build_study_quality_truth
read_study_charter = chunk_01.read_study_charter
resolve_study_charter_ref = chunk_01.resolve_study_charter_ref
read_latest_task_intake = chunk_01.read_latest_task_intake
summarize_task_intake = chunk_01.summarize_task_intake
_task_intake_scoped_quality_agenda = chunk_02._task_intake_scoped_quality_agenda
_quality_revision_plan_id = chunk_02._quality_revision_plan_id
_quality_review_loop_id = chunk_02._quality_review_loop_id
_top_quality_revision_dimension = chunk_02._top_quality_revision_dimension
_quality_revision_action_type = chunk_02._quality_revision_action_type
_quality_revision_route_target = chunk_02._quality_revision_route_target
_default_quality_revision_action = chunk_02._default_quality_revision_action
_quality_revision_done_criteria = chunk_02._quality_revision_done_criteria
_quality_revision_item_priority = chunk_02._quality_revision_item_priority
_quality_revision_item = chunk_02._quality_revision_item
_quality_revision_plan_from_summary_payload = chunk_02._quality_revision_plan_from_summary_payload
_quality_revision_candidates = chunk_02._quality_revision_candidates
_quality_revision_plan = chunk_02._quality_revision_plan
_normalized_weight_contract = chunk_02._normalized_weight_contract
_normalized_text_list = chunk_02._normalized_text_list
_normalized_quality_revision_item = chunk_02._normalized_quality_revision_item
_normalized_quality_revision_plan = chunk_02._normalized_quality_revision_plan
_quality_review_loop_phase = chunk_02._quality_review_loop_phase
_quality_review_loop_blocking_issues = chunk_02._quality_review_loop_blocking_issues
_quality_review_loop_summary = chunk_02._quality_review_loop_summary
_quality_review_loop_recommended_next_action = chunk_02._quality_review_loop_recommended_next_action
_quality_review_loop_from_summary_payload = chunk_02._quality_review_loop_from_summary_payload
_quality_execution_lane_from_summary_payload = chunk_03._quality_execution_lane_from_summary_payload
_normalized_quality_execution_lane_payload = chunk_03._normalized_quality_execution_lane_payload
_same_line_route_surface_from_summary_payload = chunk_03._same_line_route_surface_from_summary_payload
_normalized_same_line_route_surface_payload = chunk_03._normalized_same_line_route_surface_payload
_normalized_same_line_route_truth_payload = chunk_03._normalized_same_line_route_truth_payload
_normalized_quality_review_loop = chunk_03._normalized_quality_review_loop
_quality_review_agenda = chunk_03._quality_review_agenda
_fallback_refs = chunk_03._fallback_refs
_coerce_quality_basis_item = chunk_03._coerce_quality_basis_item
_publication_gate_quality_basis = chunk_03._publication_gate_quality_basis
_quality_closure_basis = chunk_03._quality_closure_basis
_quality_closure_truth = chunk_03._quality_closure_truth
_quality_execution_lane = chunk_03._quality_execution_lane
_load_review_ledger_context = chunk_03._load_review_ledger_context
_study_quality_truth_from_summary_payload = chunk_03._study_quality_truth_from_summary_payload
build_same_line_route_truth = chunk_03.build_same_line_route_truth
_build_evaluation_summary_payload = chunk_04._build_evaluation_summary_payload
_normalized_promotion_gate = chunk_04._normalized_promotion_gate
_normalized_evaluation_summary = chunk_04._normalized_evaluation_summary
read_promotion_gate = chunk_04.read_promotion_gate
read_evaluation_summary = chunk_04.read_evaluation_summary
materialize_evaluation_summary_artifacts = chunk_04.materialize_evaluation_summary_artifacts

__all__ = [
    "STABLE_EVALUATION_SUMMARY_RELATIVE_PATH",
    "STABLE_PROMOTION_GATE_RELATIVE_PATH",
    "build_same_line_route_truth",
    "materialize_evaluation_summary_artifacts",
    "read_evaluation_summary",
    "read_promotion_gate",
    "resolve_evaluation_summary_ref",
    "resolve_promotion_gate_ref",
    "stable_evaluation_summary_path",
    "stable_promotion_gate_path",
]
