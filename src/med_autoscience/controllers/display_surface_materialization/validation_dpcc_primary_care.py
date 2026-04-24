from __future__ import annotations

from .shared import (
    Any,
    Path,
    _require_non_empty_string,
    _require_non_negative_int,
    _require_probability_value,
)

_DPCC_GAP_RATE_FIELDS: tuple[str, ...] = (
    "severe_glycemia_low_intensity_gap_rate",
    "uncontrolled_glycemia_no_drug_gap_rate",
    "hypertension_no_antihypertensive_gap_rate",
    "dyslipidemia_no_lipid_lowering_gap_rate",
)

_DPCC_GAP_PATIENT_FIELDS: tuple[str, ...] = (
    "severe_glycemia_low_intensity_gap_patients",
    "uncontrolled_glycemia_no_drug_gap_patients",
    "hypertension_no_antihypertensive_gap_patients",
    "dyslipidemia_no_lipid_lowering_gap_patients",
)


def _require_optional_probability_value(value: object, *, label: str) -> float | None:
    if value is None:
        return None
    return _require_probability_value(value, label=label)


def _normalize_common_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    template_id = _require_non_empty_string(
        payload.get("template_id"),
        label=f"{path.name} display `{expected_display_id}` template_id",
    )
    if template_id != expected_template_id:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must declare template_id `{expected_template_id}`"
        )
    display_id = _require_non_empty_string(
        payload.get("display_id"),
        label=f"{path.name} display_id",
    )
    if display_id != expected_display_id:
        raise ValueError(f"{path.name} display_id must equal `{expected_display_id}`")

    normalized: dict[str, Any] = {
        "display_id": display_id,
        "template_id": template_id,
    }
    for key in (
        "title",
        "composition_panel_title",
        "heatmap_panel_title",
        "transition_panel_title",
        "coverage_panel_title",
        "x_label",
        "y_label",
        "annotation",
        "heatmap_scale_label",
    ):
        value = str(payload.get(key) or "").strip()
        if value:
            normalized[key] = value
    render_context = payload.get("render_context")
    if isinstance(render_context, dict):
        normalized["render_context"] = render_context
    return normalized


def _require_object_list(
    value: object,
    *,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{index}] must be an object")
        normalized.append(item)
    return normalized


def _validate_dpcc_phenotype_gap_structure_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized = _normalize_common_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    rows_payload = _require_object_list(
        payload.get("rows"),
        label=f"{path.name} display `{expected_display_id}` rows",
    )
    normalized_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows_payload):
        normalized_row: dict[str, Any] = {
            "phenotype_label": _require_non_empty_string(
                row.get("phenotype_label"),
                label=f"{path.name} rows[{row_index}].phenotype_label",
            ),
            "share_of_index_patients": _require_probability_value(
                row.get("share_of_index_patients"),
                label=f"{path.name} rows[{row_index}].share_of_index_patients",
            ),
        }
        for field in _DPCC_GAP_RATE_FIELDS:
            normalized_row[field] = _require_optional_probability_value(
                row.get(field),
                label=f"{path.name} rows[{row_index}].{field}",
            )
        normalized_rows.append(normalized_row)
    normalized["rows"] = normalized_rows
    return normalized


def _validate_dpcc_transition_site_support_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized = _normalize_common_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    transition_rows = _require_object_list(
        payload.get("transition_rows"),
        label=f"{path.name} display `{expected_display_id}` transition_rows",
    )
    site_fold_rows = _require_object_list(
        payload.get("site_fold_rows"),
        label=f"{path.name} display `{expected_display_id}` site_fold_rows",
    )
    normalized_transition_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(transition_rows):
        normalized_transition_rows.append(
            {
                "source_phenotype_label": _require_non_empty_string(
                    row.get("source_phenotype_label"),
                    label=f"{path.name} transition_rows[{row_index}].source_phenotype_label",
                ),
                "target_phenotype_label": _require_non_empty_string(
                    row.get("target_phenotype_label"),
                    label=f"{path.name} transition_rows[{row_index}].target_phenotype_label",
                ),
                "patient_count": _require_non_negative_int(
                    row.get("patient_count"),
                    label=f"{path.name} transition_rows[{row_index}].patient_count",
                ),
                "share_of_transition_patients": _require_probability_value(
                    row.get("share_of_transition_patients"),
                    label=f"{path.name} transition_rows[{row_index}].share_of_transition_patients",
                ),
            }
        )
    normalized_site_fold_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(site_fold_rows):
        normalized_site_fold_rows.append(
            {
                "fold_id": _require_non_empty_string(
                    row.get("fold_id"),
                    label=f"{path.name} site_fold_rows[{row_index}].fold_id",
                ),
                "index_patients": _require_non_negative_int(
                    row.get("index_patients"),
                    label=f"{path.name} site_fold_rows[{row_index}].index_patients",
                ),
                "share_of_index_patients": _require_probability_value(
                    row.get("share_of_index_patients"),
                    label=f"{path.name} site_fold_rows[{row_index}].share_of_index_patients",
                ),
            }
        )
    normalized["transition_rows"] = normalized_transition_rows
    normalized["site_fold_rows"] = normalized_site_fold_rows
    if payload.get("visit_coverage") is not None:
        normalized["visit_coverage"] = _require_probability_value(
            payload.get("visit_coverage"),
            label=f"{path.name} display `{expected_display_id}` visit_coverage",
        )
    if payload.get("eligible_site_count") is not None:
        normalized["eligible_site_count"] = _require_non_negative_int(
            payload.get("eligible_site_count"),
            label=f"{path.name} display `{expected_display_id}` eligible_site_count",
        )
    return normalized


def _validate_dpcc_treatment_gap_alignment_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized = _normalize_common_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    rows_payload = _require_object_list(
        payload.get("rows"),
        label=f"{path.name} display `{expected_display_id}` rows",
    )
    normalized_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows_payload):
        index_patients = _require_non_negative_int(
            row.get("index_patients"),
            label=f"{path.name} rows[{row_index}].index_patients",
            allow_zero=False,
        )
        normalized_row: dict[str, Any] = {
            "phenotype_label": _require_non_empty_string(
                row.get("phenotype_label"),
                label=f"{path.name} rows[{row_index}].phenotype_label",
            ),
            "index_patients": index_patients,
        }
        for field in _DPCC_GAP_PATIENT_FIELDS:
            patients = _require_non_negative_int(
                row.get(field),
                label=f"{path.name} rows[{row_index}].{field}",
            )
            if patients > index_patients:
                raise ValueError(
                    f"{path.name} rows[{row_index}].{field} must not exceed index_patients"
                )
            normalized_row[field] = patients
        normalized_rows.append(normalized_row)
    normalized["rows"] = normalized_rows
    return normalized


__all__ = [
    "_validate_dpcc_phenotype_gap_structure_display_payload",
    "_validate_dpcc_transition_site_support_display_payload",
    "_validate_dpcc_treatment_gap_alignment_display_payload",
]
