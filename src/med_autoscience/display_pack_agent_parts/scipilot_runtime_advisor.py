from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SCIPILOT_SOURCE_REF = "Haojae/scipilot-figure-skill@43098ddb9e6a6d142218540c114f9ed38922fc42"
PAPER_MISSION_SUBORDINATION = {
    "surface_kind": "mas_paper_mission_subordination",
    "authority_owner": "MedAutoScience",
    "mainline_route": [
        "PaperMission",
        "submission_authority",
        "submission_authority_owner_gate_or_typed_blocker",
    ],
    "control_plane_role": "subordinate_input_or_advisory_only",
    "can_start_parallel_mainline": False,
    "can_bypass_submission_authority": False,
    "can_close_without_owner_gate_or_typed_blocker": False,
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _lower_tokens(*values: object) -> str:
    return " ".join(_text(value) for value in values).lower()


def _profile_counts(profile: Mapping[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    variables = _sequence(profile.get("variables"))
    for item in variables:
        variable = _mapping(item)
        value = _text(variable.get("type") or variable.get("kind") or variable.get("role"))
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts


def _sample_size_summary(profile: Mapping[str, Any]) -> dict[str, Any]:
    groups = _sequence(profile.get("groups") or profile.get("group_sizes"))
    normalized: list[dict[str, Any]] = []
    for item in groups:
        group = _mapping(item)
        n = _number(group.get("n") or group.get("sample_size") or group.get("count"))
        if n is not None:
            normalized.append({"label": _text(group.get("label") or group.get("group")), "n": int(n)})
    if not normalized:
        n = _number(profile.get("n") or profile.get("sample_size") or profile.get("total_n"))
        return {"total_n": int(n) if n is not None else None, "groups": [], "min_group_n": None}
    return {
        "total_n": sum(item["n"] for item in normalized),
        "groups": normalized,
        "min_group_n": min(item["n"] for item in normalized),
    }


def _recommended_plot_family(request: Mapping[str, Any], variable_profile: Mapping[str, Any]) -> str:
    tokens = _lower_tokens(
        request.get("query"),
        request.get("audit_family"),
        request.get("claim_role"),
        request.get("figure_kind"),
        request.get("requested_chart_type") or request.get("chart_type"),
    )
    if any(token in tokens for token in ("roc", "auc", "discrimination")):
        return "discrimination_curve"
    if any(token in tokens for token in ("calibration", "observed expected", "o:e", "oe")):
        return "calibration_curve_or_summary"
    if any(token in tokens for token in ("decision curve", "dca", "clinical utility")):
        return "clinical_utility_curve"
    if any(token in tokens for token in ("survival", "kaplan", "hazard", "time-to-event")):
        return "survival_curve_with_risk_table"
    if any(token in tokens for token in ("forest", "subgroup", "effect")):
        return "effect_estimate_forest"
    if any(token in tokens for token in ("heatmap", "matrix", "omics")):
        return "matrix_heatmap_with_annotation_tracks"
    counts = _profile_counts(variable_profile)
    if counts.get("categorical") and counts.get("continuous"):
        return "distribution_or_interval_plot_by_group"
    if counts.get("continuous", 0) >= 2:
        return "scatter_or_trend_with_uncertainty"
    return "claim_led_medical_figure_family_route"


def _misleading_warning_ids(request: Mapping[str, Any], sample_summary: Mapping[str, Any]) -> list[str]:
    tokens = _lower_tokens(
        request.get("query"),
        request.get("chart_type"),
        request.get("requested_chart_type"),
        request.get("plot_selection_summary"),
    )
    warnings: list[str] = []
    min_group_n = _number(sample_summary.get("min_group_n"))
    raw_points_visible = bool(request.get("raw_points_visible") or request.get("show_raw_points"))
    if min_group_n is not None and min_group_n < 10 and "bar" in tokens and not raw_points_visible:
        warnings.append("small_n_mean_bar_without_points")
    if request.get("dual_y_axis") is True and not _text(request.get("dual_y_axis_rationale")):
        warnings.append("dual_y_axis_without_shared_unit_or_scatter_rationale")
    if any(token in tokens for token in ("pie", "3d", "3-d")):
        warnings.append("pie_or_3d_chart_for_scientific_evidence")
    if "line" in tokens and request.get("categorical_x_axis") is True and not _text(request.get("ordered_scale_rationale")):
        warnings.append("categorical_axis_connected_as_line_without_ordered_scale_rationale")
    if _text(request.get("palette")).lower() in {"rainbow", "jet"}:
        warnings.append("rainbow_or_jet_for_ordered_scientific_data")
    if request.get("error_bars") is True and not _text(request.get("interval_type")):
        warnings.append("error_bar_or_interval_type_missing_from_caption")
    return warnings


def build_figure_advisor_probe(
    *,
    compiled_request: Mapping[str, Any],
    figure_contract: Mapping[str, Any],
) -> dict[str, Any]:
    request = _mapping(compiled_request)
    contract = _mapping(figure_contract)
    variable_profile = _mapping(
        request.get("variable_type_profile")
        or request.get("variable_profile")
        or request.get("data_profile")
    )
    sample_profile = _mapping(
        request.get("group_sample_size_profile")
        or request.get("sample_size_profile")
        or request.get("data_profile")
    )
    sample_summary = _sample_size_summary(sample_profile)
    warning_ids = _misleading_warning_ids(request, sample_summary)
    return {
        "surface_kind": "figure_advisor_probe",
        "source_ref": SCIPILOT_SOURCE_REF,
        "advisory_only": True,
        "blocks_unrelated_progress": False,
        "authority_boundary": {
            "can_mutate_data_or_statistics": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_replace_visual_audit": False,
            "can_replace_owner_receipt": False,
        },
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
        "question_or_claim": _text(
            request.get("figure_question")
            or request.get("query")
            or request.get("claim_role")
            or contract.get("core_conclusion")
        ),
        "input_refs": {
            "plot_selection_ref": _text(request.get("plot_selection_ref")),
            "variable_profile_ref": _text(request.get("variable_profile_ref")),
            "group_sample_size_ref": _text(request.get("group_sample_size_ref")),
            "warning_ref": _text(request.get("graph_warnings_ref") or request.get("figure_warning_ref")),
        },
        "data_profile_summary": {
            "variable_type_counts": _profile_counts(variable_profile),
            "sample_size": sample_summary,
        },
        "recommended_plot_family": _recommended_plot_family(request, variable_profile),
        "misleading_chart_warning_ids": warning_ids,
        "missing_inputs": [
            name
            for name, present in {
                "question_or_claim": bool(
                    _text(request.get("figure_question") or request.get("query") or contract.get("core_conclusion"))
                ),
                "variable_type_profile_or_ref": bool(variable_profile or _text(request.get("variable_profile_ref"))),
                "sample_size_profile_or_ref": bool(sample_profile or _text(request.get("group_sample_size_ref"))),
                "uncertainty_or_statistical_annotation_policy": bool(
                    _text(request.get("uncertainty_policy") or request.get("statistical_annotation_policy"))
                ),
            }.items()
            if not present
        ],
    }


def _format_warnings(formats: Sequence[Any]) -> list[str]:
    normalized = {_text(item).lower().lstrip(".") for item in formats if _text(item)}
    warnings: list[str] = []
    if "jpg" in normalized or "jpeg" in normalized:
        warnings.append("jpeg_export_not_preferred_for_line_art_or_text")
    if not normalized.intersection({"pdf", "svg"}):
        warnings.append("vector_export_missing")
    return warnings


def build_figure_export_lint(
    *,
    compiled_request: Mapping[str, Any],
    receipt_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = _mapping(compiled_request)
    export_profile = _mapping(
        request.get("figure_export_lint")
        or request.get("export_lint")
        or request.get("artifact_export_profile")
    )
    formats = _sequence(export_profile.get("formats") or export_profile.get("export_formats"))
    warnings = _format_warnings(formats)
    dpi = _number(export_profile.get("dpi"))
    width_mm = _number(export_profile.get("width_mm") or export_profile.get("final_width_mm"))
    if dpi is not None and dpi < 300:
        warnings.append("raster_dpi_below_300")
    if width_mm is not None and width_mm < 80:
        warnings.append("final_width_below_single_column_floor")
    if export_profile.get("fonts_embedded") is False:
        warnings.append("font_embedding_missing_or_unverified")
    if export_profile.get("missing_glyphs") or export_profile.get("cjk_text_present") is True:
        warnings.append("cjk_or_missing_glyph_review_required")
    if export_profile.get("unicode_minus_verified") is False or export_profile.get("negative_sign_verified") is False:
        warnings.append("negative_sign_glyph_review_required")
    return {
        "surface_kind": "figure_export_lint",
        "source_ref": SCIPILOT_SOURCE_REF,
        "advisory_only": True,
        "blocks_unrelated_progress": False,
        "receipt_refs": dict(receipt_refs or {}),
        "export_profile_ref": _text(export_profile.get("ref") or request.get("export_lint_ref")),
        "checked_dimensions": {
            "formats": [_text(item).lower().lstrip(".") for item in formats if _text(item)],
            "dpi": int(dpi) if dpi is not None else None,
            "width_mm": width_mm,
            "height_mm": _number(export_profile.get("height_mm") or export_profile.get("final_height_mm")),
        },
        "warning_ids": warnings,
        "authority_boundary": {
            "can_mutate_data_or_statistics": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_replace_visual_audit": False,
            "can_replace_owner_receipt": False,
        },
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
    }
