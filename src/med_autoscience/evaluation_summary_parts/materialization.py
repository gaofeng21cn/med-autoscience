from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_publication_critique_weight_contract,
    build_revision_action_contract,
)
from med_autoscience.publication_eval_latest import read_publication_eval_latest, stable_publication_eval_latest_path
from med_autoscience.quality.publication_gate import (
    derive_quality_closure_truth,
    derive_quality_execution_lane,
)
from med_autoscience.quality.study_quality import build_study_quality_truth
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.study_task_intake import read_latest_task_intake, summarize_task_intake

from .refs_and_validation import (
    __all__,
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
)
from .refs_and_validation import (
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
)
from .refs_and_validation import (
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
)
from .refs_and_validation import (
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
)
from .refs_and_validation import (
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
)
from .refs_and_validation import (
    _agenda_field,
    _agenda_summary,
    _quality_review_agenda_from_summary_payload,
    _reviewer_agenda_from_quality_assessment,
    _normalized_quality_review_agenda,
    _unique_non_empty_texts,
    _task_intake_scope_texts,
    _task_intake_contains_hint,
    _format_revision_scope_targets,
)
from .quality_revision_plan import (
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
)
from .quality_revision_plan import (
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
)
from .quality_closure_truth import (
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
)
from .quality_closure_truth import (
    _quality_execution_lane,
    _load_review_ledger_context,
    _study_quality_truth_from_summary_payload,
    build_same_line_route_truth,
)
from .study_quality_projection import normalized_study_quality_assessment_provenance

_OBJECTIVE_PUNCTUATION = ("，", ",", "；", ";", "。", ".", "：", ":", "、", "？", "?", "！", "!")
from .materialization_builders import _build_evaluation_summary_payload, _objective_compare_text
from .materialization_normalizers import _normalized_evaluation_summary, _normalized_promotion_gate


from .materialization_io import (  # noqa: E402
    materialize_evaluation_summary_artifacts,
    read_evaluation_summary,
    read_promotion_gate,
)
