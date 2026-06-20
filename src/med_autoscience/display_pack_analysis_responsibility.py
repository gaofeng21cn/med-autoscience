from __future__ import annotations

from collections.abc import Mapping
from typing import Any


COMPUTED_IN_TEMPLATE = "computed_in_template"
VALIDATED_SUMMARY_REQUIRED = "validated_summary_required"
ILLUSTRATION_SHELL = "illustration_shell"
TABLE_SHELL = "table_shell"

VALID_ANALYSIS_RESPONSIBILITIES = frozenset(
    (
        COMPUTED_IN_TEMPLATE,
        VALIDATED_SUMMARY_REQUIRED,
        ILLUSTRATION_SHELL,
        TABLE_SHELL,
    )
)

_MODE_POLICY: dict[str, dict[str, Any]] = {
    COMPUTED_IN_TEMPLATE: {
        "statistical_truth_owner": "template_renderer",
        "raw_input_allowed": True,
        "validated_summary_required": False,
        "route_on_raw_input": "",
        "renderer_may_compute": True,
        "description": (
            "The template contains a bounded analysis workflow and records analysis provenance "
            "from renderer execution."
        ),
    },
    VALIDATED_SUMMARY_REQUIRED: {
        "statistical_truth_owner": "upstream_analysis_pipeline",
        "raw_input_allowed": False,
        "validated_summary_required": True,
        "route_on_raw_input": "materialize_validated_analysis_summary_before_display_render",
        "renderer_may_compute": False,
        "description": (
            "The renderer is a deterministic display surface for locked statistics, curves, "
            "scores, calls, or explanation values computed upstream."
        ),
    },
    ILLUSTRATION_SHELL: {
        "statistical_truth_owner": "not_statistical_evidence",
        "raw_input_allowed": False,
        "validated_summary_required": False,
        "route_on_raw_input": "use_evidence_template_or_analysis_owner_for_statistical_claims",
        "renderer_may_compute": False,
        "description": "Composition shell for cohort, workflow, or graphical-abstract expression.",
    },
    TABLE_SHELL: {
        "statistical_truth_owner": "upstream_analysis_pipeline",
        "raw_input_allowed": False,
        "validated_summary_required": True,
        "route_on_raw_input": "materialize_validated_table_values_before_display_render",
        "renderer_may_compute": False,
        "description": "Table shell for already computed and reviewed table values.",
    },
}

_RAW_REQUEST_STATES = frozenset(
    (
        "raw",
        "raw_data",
        "raw_observations",
        "patient_level",
        "patient_level_records",
        "feature_matrix",
        "raw_feature_matrix",
        "raw_counts",
        "raw_predictions",
        "time_status",
        "time_status_records",
        "labels_and_scores",
    )
)

_VALIDATED_REQUEST_STATES = frozenset(
    (
        "validated",
        "validated_summary",
        "validated_display_payload",
        "validated_statistics",
        "validated_curve_series",
        "validated_table_values",
    )
)

_REQUEST_STATE_KEYS = (
    "analysis_input_state",
    "analysis_input_mode",
    "data_input_state",
    "data_input_mode",
    "display_input_state",
    "source_data_state",
)


def normalize_analysis_responsibility(value: object) -> str:
    text = str(value or "").strip()
    if text not in VALID_ANALYSIS_RESPONSIBILITIES:
        raise ValueError(
            "analysis_responsibility must be one of "
            f"{sorted(VALID_ANALYSIS_RESPONSIBILITIES)!r}"
        )
    return text


def normalize_analysis_input_state(value: object) -> str:
    return str(value or "").strip()


def analysis_responsibility_payload(
    *,
    mode: str,
    input_state: str,
) -> dict[str, Any]:
    normalized_mode = normalize_analysis_responsibility(mode)
    policy = dict(_MODE_POLICY[normalized_mode])
    return {
        "mode": normalized_mode,
        "input_state": normalize_analysis_input_state(input_state),
        **policy,
    }


def request_analysis_input_state(request: Mapping[str, Any]) -> str:
    for key in _REQUEST_STATE_KEYS:
        text = normalize_analysis_input_state(request.get(key))
        if text:
            return text
    return "unspecified"


def request_declares_raw_analysis_input(request: Mapping[str, Any]) -> bool:
    if request.get("raw_data") is True or request.get("raw_input") is True:
        return True
    state = request_analysis_input_state(request).lower()
    return state in _RAW_REQUEST_STATES


def request_declares_validated_summary_input(request: Mapping[str, Any]) -> bool:
    state = request_analysis_input_state(request).lower()
    return state in _VALIDATED_REQUEST_STATES


def analysis_responsibility_allows_request(
    *,
    mode: str,
    request: Mapping[str, Any],
) -> bool:
    normalized_mode = normalize_analysis_responsibility(mode)
    if not request_declares_raw_analysis_input(request):
        return True
    return bool(_MODE_POLICY[normalized_mode]["raw_input_allowed"])


def analysis_boundary_payload(
    *,
    mode: str,
    input_state: str,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    responsibility = analysis_responsibility_payload(mode=mode, input_state=input_state)
    request_state = request_analysis_input_state(request)
    raw_input_declared = request_declares_raw_analysis_input(request)
    validated_summary_declared = request_declares_validated_summary_input(request)
    return {
        **responsibility,
        "request_input_state": request_state,
        "request_declares_raw_input": raw_input_declared,
        "request_declares_validated_summary": validated_summary_declared,
        "compatible_with_request": analysis_responsibility_allows_request(
            mode=mode,
            request=request,
        ),
    }


def analysis_boundary_blocker(
    *,
    template_id: str,
    canonical_family_id: str,
    mode: str,
    input_state: str,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    boundary = analysis_boundary_payload(
        mode=mode,
        input_state=input_state,
        request=request,
    )
    return {
        "blocked_reason": "analysis_summary_required_before_display_render",
        "owner": "MedAutoScience",
        "route_hint": boundary["route_on_raw_input"],
        "template_id": template_id,
        "canonical_family_id": canonical_family_id,
        "analysis_responsibility": boundary,
        "required_input_state": boundary["input_state"],
        "request_input_state": boundary["request_input_state"],
        "authority_boundary": {
            "display_resolver_can_mutate_data_or_statistics": False,
            "display_resolver_can_invent_analysis_results": False,
            "display_resolver_can_authorize_publication_readiness": False,
        },
    }
