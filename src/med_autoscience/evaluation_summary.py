from __future__ import annotations

from .evaluation_summary_parts import (
    STABLE_EVALUATION_SUMMARY_RELATIVE_PATH,
    STABLE_PROMOTION_GATE_RELATIVE_PATH,
    _GAP_SEVERITIES,
    _GAP_SEVERITY_RANK,
    _GAP_SEVERITY_LABELS,
    _ACTION_PRIORITY_RANK,
    _ROUTE_REPAIR_ACTION_TYPES,
    _QUALITY_DIMENSION_STATUSES,
    _QUALITY_CLOSURE_STATES,
    _QUALITY_CLOSURE_BASIS_KEYS,
    _QUALITY_REVIEW_STATUS_RANK,
    _QUALITY_ASSESSMENT_REVIEW_ORDER,
    _QUALITY_EXECUTION_LANE_LABELS,
    _SAME_LINE_ROUTE_STATES,
    _SAME_LINE_ROUTE_STATE_LABELS,
    _SAME_LINE_ROUTE_MODES,
    _SAME_LINE_ROUTE_TARGET_LABELS,
    _PUBLICATION_CRITIQUE_WEIGHT_CONTRACT,
    _PUBLICATION_CRITIQUE_ACTION_CONTRACT,
    _QUALITY_REVISION_PLAN_STATUSES,
    _QUALITY_REVISION_ITEM_PRIORITIES,
    _QUALITY_REVISION_PRIORITY_BY_STATUS,
    _QUALITY_REVISION_DIMENSIONS,
    _QUALITY_REVISION_ACTION_BY_DIMENSION,
    _QUALITY_REVISION_DEFAULT_ACTIONS,
    _QUALITY_REVISION_DEFAULT_DONE_CRITERIA,
    _QUALITY_REVIEW_LOOP_PHASES,
    _QUALITY_REVIEW_LOOP_PHASE_LABELS,
    _QUALITY_REVIEW_LOOP_NEXT_PHASES,
    _QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS,
    _TASK_INTAKE_REPORTING_SCOPE_HINTS,
    _TASK_INTAKE_NO_CLAIM_REOPEN_HINTS,
    _TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS,
    _TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS,
    _TASK_INTAKE_STATUS_RECHECK_HINTS,
    _TASK_INTAKE_DISPLAY_REGISTRY_HINTS,
    _TASK_INTAKE_SHELL_INPUT_HINTS,
    stable_evaluation_summary_path,
    stable_promotion_gate_path,
    _resolve_stable_ref,
    resolve_evaluation_summary_ref,
    resolve_promotion_gate_ref,
    _required_text,
    _required_bool,
    _optional_text,
    _required_choice,
    _required_mapping,
    _required_string_list,
    _optional_string_list,
    _same_line_route_target_label,
    _read_json_object,
    _normalize_runtime_escalation_ref,
    _normalize_gate_report,
    _build_promotion_gate_payload,
    _gap_counts,
    _recommended_action_types,
    _route_repair_plan,
    _highest_priority_gap,
    _highest_priority_action,
    _agenda_field,
    _agenda_summary,
    _quality_review_agenda_from_summary_payload,
    _reviewer_agenda_from_quality_assessment,
    _normalized_quality_review_agenda,
    _unique_non_empty_texts,
    _task_intake_scope_texts,
    _task_intake_contains_hint,
    _format_revision_scope_targets,
    annotations,
    json,
    Path,
    Any,
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_publication_critique_weight_contract,
    build_revision_action_contract,
    read_publication_eval_latest,
    stable_publication_eval_latest_path,
    derive_quality_closure_truth,
    derive_quality_execution_lane,
    build_study_quality_truth,
    read_study_charter,
    resolve_study_charter_ref,
    read_latest_task_intake,
    summarize_task_intake,
    _task_intake_scoped_quality_agenda,
    _quality_revision_plan_id,
    _quality_review_loop_id,
    _top_quality_revision_dimension,
    _quality_revision_action_type,
    _quality_revision_route_target,
    _default_quality_revision_action,
    _quality_revision_done_criteria,
    _quality_revision_item_priority,
    _quality_revision_item,
    _quality_revision_plan_from_summary_payload,
    _quality_revision_candidates,
    _quality_revision_plan,
    _normalized_weight_contract,
    _normalized_text_list,
    _normalized_quality_revision_item,
    _normalized_quality_revision_plan,
    _quality_review_loop_phase,
    _quality_review_loop_blocking_issues,
    _quality_review_loop_summary,
    _quality_review_loop_recommended_next_action,
    _quality_review_loop_from_summary_payload,
    _quality_execution_lane_from_summary_payload,
    _normalized_quality_execution_lane_payload,
    _same_line_route_surface_from_summary_payload,
    _normalized_same_line_route_surface_payload,
    _normalized_same_line_route_truth_payload,
    _normalized_quality_review_loop,
    _quality_review_agenda,
    _fallback_refs,
    _coerce_quality_basis_item,
    _publication_gate_quality_basis,
    _quality_closure_basis,
    _quality_closure_truth,
    _quality_execution_lane,
    _load_review_ledger_context,
    _study_quality_truth_from_summary_payload,
    build_same_line_route_truth,
    _build_evaluation_summary_payload,
    _normalized_promotion_gate,
    _normalized_evaluation_summary,
    read_promotion_gate,
    read_evaluation_summary,
    materialize_evaluation_summary_artifacts,
    __all__,
)
from .evaluation_summary_parts import chunk_01 as chunk_01
from .evaluation_summary_parts import chunk_02 as chunk_02
from .evaluation_summary_parts import chunk_03 as chunk_03
from .evaluation_summary_parts import chunk_04 as chunk_04

import sys
from types import ModuleType
from typing import Any as _Any

_DECLARED_NAMES = ('__all__', 'STABLE_EVALUATION_SUMMARY_RELATIVE_PATH', 'STABLE_PROMOTION_GATE_RELATIVE_PATH', '_GAP_SEVERITIES', '_GAP_SEVERITY_RANK', '_GAP_SEVERITY_LABELS', '_ACTION_PRIORITY_RANK', '_ROUTE_REPAIR_ACTION_TYPES', '_QUALITY_DIMENSION_STATUSES', '_QUALITY_CLOSURE_STATES', '_QUALITY_CLOSURE_BASIS_KEYS', '_QUALITY_REVIEW_STATUS_RANK', '_QUALITY_ASSESSMENT_REVIEW_ORDER', '_QUALITY_EXECUTION_LANE_LABELS', '_SAME_LINE_ROUTE_STATES', '_SAME_LINE_ROUTE_STATE_LABELS', '_SAME_LINE_ROUTE_MODES', '_SAME_LINE_ROUTE_TARGET_LABELS', '_PUBLICATION_CRITIQUE_WEIGHT_CONTRACT', '_PUBLICATION_CRITIQUE_ACTION_CONTRACT', '_QUALITY_REVISION_PLAN_STATUSES', '_QUALITY_REVISION_ITEM_PRIORITIES', '_QUALITY_REVISION_PRIORITY_BY_STATUS', '_QUALITY_REVISION_DIMENSIONS', '_QUALITY_REVISION_ACTION_BY_DIMENSION', '_QUALITY_REVISION_DEFAULT_ACTIONS', '_QUALITY_REVISION_DEFAULT_DONE_CRITERIA', '_QUALITY_REVIEW_LOOP_PHASES', '_QUALITY_REVIEW_LOOP_PHASE_LABELS', '_QUALITY_REVIEW_LOOP_NEXT_PHASES', '_QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS', '_TASK_INTAKE_REPORTING_SCOPE_HINTS', '_TASK_INTAKE_NO_CLAIM_REOPEN_HINTS', '_TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS', '_TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS', '_TASK_INTAKE_STATUS_RECHECK_HINTS', '_TASK_INTAKE_DISPLAY_REGISTRY_HINTS', '_TASK_INTAKE_SHELL_INPUT_HINTS', 'stable_evaluation_summary_path', 'stable_promotion_gate_path', '_resolve_stable_ref', 'resolve_evaluation_summary_ref', 'resolve_promotion_gate_ref', '_required_text', '_required_bool', '_optional_text', '_required_choice', '_required_mapping', '_required_string_list', '_optional_string_list', '_same_line_route_target_label', '_read_json_object', '_normalize_runtime_escalation_ref', '_normalize_gate_report', '_build_promotion_gate_payload', '_gap_counts', '_recommended_action_types', '_route_repair_plan', '_highest_priority_gap', '_highest_priority_action', '_agenda_field', '_agenda_summary', '_quality_review_agenda_from_summary_payload', '_reviewer_agenda_from_quality_assessment', '_normalized_quality_review_agenda', '_unique_non_empty_texts', '_task_intake_scope_texts', '_task_intake_contains_hint', '_format_revision_scope_targets', '_task_intake_scoped_quality_agenda', '_quality_revision_plan_id', '_quality_review_loop_id', '_top_quality_revision_dimension', '_quality_revision_action_type', '_quality_revision_route_target', '_default_quality_revision_action', '_quality_revision_done_criteria', '_quality_revision_item_priority', '_quality_revision_item', '_quality_revision_plan_from_summary_payload', '_quality_revision_candidates', '_quality_revision_plan', '_normalized_weight_contract', '_normalized_text_list', '_normalized_quality_revision_item', '_normalized_quality_revision_plan', '_quality_review_loop_phase', '_quality_review_loop_blocking_issues', '_quality_review_loop_summary', '_quality_review_loop_recommended_next_action', '_quality_review_loop_from_summary_payload', '_quality_execution_lane_from_summary_payload', '_normalized_quality_execution_lane_payload', '_same_line_route_surface_from_summary_payload', '_normalized_same_line_route_surface_payload', '_normalized_same_line_route_truth_payload', '_normalized_quality_review_loop', '_quality_review_agenda', '_fallback_refs', '_coerce_quality_basis_item', '_publication_gate_quality_basis', '_quality_closure_basis', '_quality_closure_truth', '_quality_execution_lane', '_load_review_ledger_context', '_study_quality_truth_from_summary_payload', 'build_same_line_route_truth', '_build_evaluation_summary_payload', '_normalized_promotion_gate', '_normalized_evaluation_summary', 'read_promotion_gate', 'read_evaluation_summary', 'materialize_evaluation_summary_artifacts',)


def _split_chunks() -> tuple[ModuleType, ...]:
    return tuple(
        value
        for name, value in globals().items()
        if name.startswith("chunk_") and isinstance(value, ModuleType)
    )


def _restore_declaring_module() -> None:
    module_name = __name__
    for name in _DECLARED_NAMES:
        value = globals().get(name)
        if isinstance(value, type) or callable(value):
            if getattr(value, "__module__", None) != module_name:
                try:
                    value.__module__ = module_name
                except (AttributeError, TypeError):
                    pass


class _SplitModule(ModuleType):
    def __setattr__(self, name: str, value: _Any) -> None:
        super().__setattr__(name, value)
        for chunk in _split_chunks():
            if hasattr(chunk, name):
                setattr(chunk, name, value)


_restore_declaring_module()
sys.modules[__name__].__class__ = _SplitModule
