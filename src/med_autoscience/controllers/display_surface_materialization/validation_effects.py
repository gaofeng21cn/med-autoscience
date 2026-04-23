from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, get_template_short_id, math

def _validate_forest_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` rows[{index}] must be an object")
        estimate = _require_numeric_value(
            item.get("estimate"),
            label=f"{path.name} display `{expected_display_id}` rows[{index}].estimate",
        )
        lower = _require_numeric_value(
            item.get("lower"),
            label=f"{path.name} display `{expected_display_id}` rows[{index}].lower",
        )
        upper = _require_numeric_value(
            item.get("upper"),
            label=f"{path.name} display `{expected_display_id}` rows[{index}].upper",
        )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` rows[{index}] must satisfy lower <= estimate <= upper"
            )
        normalized_rows.append(
            {
                "label": _require_non_empty_string(
                    item.get("label"),
                    label=f"{path.name} display `{expected_display_id}` rows[{index}].label",
                ),
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "reference_value": _require_numeric_value(
            payload.get("reference_value", 1.0),
            label=f"{path.name} display `{expected_display_id}` reference_value",
        ),
        "rows": normalized_rows,
    }

def _validate_compact_effect_estimate_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")

    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) < 2 or len(panels_payload) > 4:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain between 2 and 4 entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    expected_row_order: tuple[tuple[str, str], ...] | None = None
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        rows_payload = panel_payload.get("rows")
        if not isinstance(rows_payload, list) or not rows_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] must contain a non-empty rows list"
            )

        normalized_rows: list[dict[str, Any]] = []
        seen_row_ids: set[str] = set()
        seen_row_labels: set[str] = set()
        row_order: list[tuple[str, str]] = []
        for row_index, row_payload in enumerate(rows_payload):
            if not isinstance(row_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}] must be an object"
                )
            row_id = _require_non_empty_string(
                row_payload.get("row_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_id"
                ),
            )
            if row_id in seen_row_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_id must be unique within the panel"
                )
            seen_row_ids.add(row_id)
            row_label = _require_non_empty_string(
                row_payload.get("row_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_label"
                ),
            )
            if row_label in seen_row_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_label must be unique within the panel"
                )
            seen_row_labels.add(row_label)
            estimate = _require_numeric_value(
                row_payload.get("estimate"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].estimate"
                ),
            )
            lower = _require_numeric_value(
                row_payload.get("lower"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].lower"
                ),
            )
            upper = _require_numeric_value(
                row_payload.get("upper"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].upper"
                ),
            )
            if not all(math.isfinite(value) for value in (estimate, lower, upper)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}] values must be finite"
                )
            if not (lower <= estimate <= upper):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}] must satisfy lower <= estimate <= upper"
                )
            normalized_row = {
                "row_id": row_id,
                "row_label": row_label,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
            if row_payload.get("support_n") is not None:
                normalized_row["support_n"] = _require_non_negative_int(
                    row_payload.get("support_n"),
                    label=(
                        f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].support_n"
                    ),
                    allow_zero=False,
                )
            normalized_rows.append(normalized_row)
            row_order.append((row_id, row_label))

        if expected_row_order is None:
            expected_row_order = tuple(row_order)
        elif tuple(row_order) != expected_row_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` rows must appear in the same row_id and row_label order across panels"
            )

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "rows": normalized_rows,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "reference_value": reference_value,
        "panels": normalized_panels,
    }

def _validate_coefficient_path_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    path_panel_title = _require_non_empty_string(
        payload.get("path_panel_title"),
        label=f"{path.name} display `{expected_display_id}` path_panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")
    step_legend_title = _require_non_empty_string(
        payload.get("step_legend_title"),
        label=f"{path.name} display `{expected_display_id}` step_legend_title",
    )
    summary_panel_title = _require_non_empty_string(
        payload.get("summary_panel_title"),
        label=f"{path.name} display `{expected_display_id}` summary_panel_title",
    )

    steps_payload = payload.get("steps")
    if not isinstance(steps_payload, list) or not steps_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty steps list")
    if len(steps_payload) < 2 or len(steps_payload) > 5:
        raise ValueError(f"{path.name} display `{expected_display_id}` steps must contain between 2 and 5 entries")
    normalized_steps: list[dict[str, Any]] = []
    declared_step_ids: list[str] = []
    seen_step_ids: set[str] = set()
    previous_step_order: int | None = None
    for index, item in enumerate(steps_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` steps[{index}] must be an object")
        step_id = _require_non_empty_string(
            item.get("step_id"),
            label=f"{path.name} display `{expected_display_id}` steps[{index}].step_id",
        )
        if step_id in seen_step_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` steps[{index}].step_id must be unique")
        seen_step_ids.add(step_id)
        step_order = _require_non_negative_int(
            item.get("step_order"),
            label=f"{path.name} display `{expected_display_id}` steps[{index}].step_order",
            allow_zero=False,
        )
        if previous_step_order is not None and step_order <= previous_step_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` steps must have strictly increasing step_order"
            )
        previous_step_order = step_order
        declared_step_ids.append(step_id)
        normalized_steps.append(
            {
                "step_id": step_id,
                "step_label": _require_non_empty_string(
                    item.get("step_label"),
                    label=f"{path.name} display `{expected_display_id}` steps[{index}].step_label",
                ),
                "step_order": step_order,
            }
        )

    coefficient_rows_payload = payload.get("coefficient_rows")
    if not isinstance(coefficient_rows_payload, list) or not coefficient_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty coefficient_rows list")
    normalized_rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    seen_row_labels: set[str] = set()
    declared_step_id_set = set(declared_step_ids)
    for row_index, row_payload in enumerate(coefficient_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}] must be an object")
        row_id = _require_non_empty_string(
            row_payload.get("row_id"),
            label=f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_id",
        )
        if row_id in seen_row_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_id must be unique"
            )
        seen_row_ids.add(row_id)
        row_label = _require_non_empty_string(
            row_payload.get("row_label"),
            label=f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_label",
        )
        if row_label in seen_row_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_label must be unique"
            )
        seen_row_labels.add(row_label)

        points_payload = row_payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points must be a non-empty list"
            )
        normalized_points: list[dict[str, Any]] = []
        seen_point_step_ids: set[str] = set()
        for point_index, point_payload in enumerate(points_payload):
            if not isinstance(point_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}] must be an object"
                )
            step_id = _require_non_empty_string(
                point_payload.get("step_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].step_id"
                ),
            )
            if step_id not in declared_step_id_set:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}].step_id must match a declared step"
                )
            if step_id in seen_point_step_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}].step_id must be unique within the row"
                )
            seen_point_step_ids.add(step_id)
            estimate = _require_numeric_value(
                point_payload.get("estimate"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].estimate"
                ),
            )
            lower = _require_numeric_value(
                point_payload.get("lower"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].lower"
                ),
            )
            upper = _require_numeric_value(
                point_payload.get("upper"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].upper"
                ),
            )
            if not all(math.isfinite(value) for value in (estimate, lower, upper)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}] values must be finite"
                )
            if not (lower <= estimate <= upper):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}] must satisfy lower <= estimate <= upper"
                )
            normalized_point: dict[str, Any] = {
                "step_id": step_id,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
            if point_payload.get("support_n") is not None:
                normalized_point["support_n"] = _require_non_negative_int(
                    point_payload.get("support_n"),
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"coefficient_rows[{row_index}].points[{point_index}].support_n"
                    ),
                    allow_zero=False,
                )
            normalized_points.append(normalized_point)

        if seen_point_step_ids != declared_step_id_set:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}] points must cover every declared step_id exactly once within each coefficient row"
            )

        normalized_points.sort(key=lambda item: declared_step_ids.index(str(item["step_id"])))
        normalized_rows.append(
            {
                "row_id": row_id,
                "row_label": row_label,
                "points": normalized_points,
            }
        )

    summary_cards_payload = payload.get("summary_cards")
    if not isinstance(summary_cards_payload, list) or not summary_cards_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty summary_cards list")
    if len(summary_cards_payload) < 2 or len(summary_cards_payload) > 4:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` summary_cards must contain between 2 and 4 entries"
        )
    normalized_summary_cards: list[dict[str, Any]] = []
    seen_card_ids: set[str] = set()
    for card_index, card_payload in enumerate(summary_cards_payload):
        if not isinstance(card_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` summary_cards[{card_index}] must be an object"
            )
        card_id = _require_non_empty_string(
            card_payload.get("card_id"),
            label=f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].card_id",
        )
        if card_id in seen_card_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].card_id must be unique"
            )
        seen_card_ids.add(card_id)
        normalized_card = {
            "card_id": card_id,
            "label": _require_non_empty_string(
                card_payload.get("label"),
                label=f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].label",
            ),
            "value": _require_non_empty_string(
                card_payload.get("value"),
                label=f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].value",
            ),
        }
        detail_text = str(card_payload.get("detail") or "").strip()
        if detail_text:
            normalized_card["detail"] = detail_text
        normalized_summary_cards.append(normalized_card)

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "path_panel_title": path_panel_title,
        "x_label": x_label,
        "reference_value": reference_value,
        "step_legend_title": step_legend_title,
        "steps": normalized_steps,
        "coefficient_rows": normalized_rows,
        "summary_panel_title": summary_panel_title,
        "summary_cards": normalized_summary_cards,
    }

def _validate_broader_heterogeneity_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    matrix_panel_title = _require_non_empty_string(
        payload.get("matrix_panel_title"),
        label=f"{path.name} display `{expected_display_id}` matrix_panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")
    slice_legend_title = _require_non_empty_string(
        payload.get("slice_legend_title"),
        label=f"{path.name} display `{expected_display_id}` slice_legend_title",
    )
    summary_panel_title = _require_non_empty_string(
        payload.get("summary_panel_title"),
        label=f"{path.name} display `{expected_display_id}` summary_panel_title",
    )

    slices_payload = payload.get("slices")
    if not isinstance(slices_payload, list) or not slices_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty slices list")
    if len(slices_payload) < 2 or len(slices_payload) > 5:
        raise ValueError(f"{path.name} display `{expected_display_id}` slices must contain between 2 and 5 entries")
    supported_slice_kinds = {"cohort", "subgroup", "adjustment", "sensitivity"}
    normalized_slices: list[dict[str, Any]] = []
    declared_slice_ids: list[str] = []
    seen_slice_ids: set[str] = set()
    seen_slice_labels: set[str] = set()
    previous_slice_order: int | None = None
    for index, item in enumerate(slices_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` slices[{index}] must be an object")
        slice_id = _require_non_empty_string(
            item.get("slice_id"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_id",
        )
        if slice_id in seen_slice_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` slices[{index}].slice_id must be unique")
        seen_slice_ids.add(slice_id)
        slice_label = _require_non_empty_string(
            item.get("slice_label"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_label",
        )
        if slice_label in seen_slice_labels:
            raise ValueError(f"{path.name} display `{expected_display_id}` slices[{index}].slice_label must be unique")
        seen_slice_labels.add(slice_label)
        slice_order = _require_non_negative_int(
            item.get("slice_order"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_order",
            allow_zero=False,
        )
        if previous_slice_order is not None and slice_order <= previous_slice_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` slices must have strictly increasing slice_order"
            )
        previous_slice_order = slice_order
        slice_kind = _require_non_empty_string(
            item.get("slice_kind"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_kind",
        )
        if slice_kind not in supported_slice_kinds:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` slices[{index}].slice_kind must be one of {sorted(supported_slice_kinds)}"
            )
        declared_slice_ids.append(slice_id)
        normalized_slices.append(
            {
                "slice_id": slice_id,
                "slice_label": slice_label,
                "slice_kind": slice_kind,
                "slice_order": slice_order,
            }
        )

    effect_rows_payload = payload.get("effect_rows")
    if not isinstance(effect_rows_payload, list) or not effect_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty effect_rows list")
    supported_verdicts = {"stable", "attenuated", "context_dependent", "unstable"}
    declared_slice_id_set = set(declared_slice_ids)
    normalized_effect_rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    seen_row_labels: set[str] = set()
    for row_index, row_payload in enumerate(effect_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` effect_rows[{row_index}] must be an object")
        row_id = _require_non_empty_string(
            row_payload.get("row_id"),
            label=f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_id",
        )
        if row_id in seen_row_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_id must be unique")
        seen_row_ids.add(row_id)
        row_label = _require_non_empty_string(
            row_payload.get("row_label"),
            label=f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_label",
        )
        if row_label in seen_row_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_label must be unique"
            )
        seen_row_labels.add(row_label)
        verdict = _require_non_empty_string(
            row_payload.get("verdict"),
            label=f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].verdict",
        )
        if verdict not in supported_verdicts:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].verdict must be one of {sorted(supported_verdicts)}"
            )
        detail_text = str(row_payload.get("detail") or "").strip()
        if row_payload.get("detail") is not None and not detail_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].detail must be non-empty when present"
            )

        slice_estimates_payload = row_payload.get("slice_estimates")
        if not isinstance(slice_estimates_payload, list) or not slice_estimates_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates must be a non-empty list"
            )
        normalized_slice_estimates: list[dict[str, Any]] = []
        seen_row_slice_ids: set[str] = set()
        for estimate_index, estimate_payload in enumerate(slice_estimates_payload):
            if not isinstance(estimate_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}] must be an object"
                )
            slice_id = _require_non_empty_string(
                estimate_payload.get("slice_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id"
                ),
            )
            if slice_id not in declared_slice_id_set:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id must match a declared slice"
                )
            if slice_id in seen_row_slice_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id must be unique within the row"
                )
            seen_row_slice_ids.add(slice_id)
            estimate = _require_numeric_value(
                estimate_payload.get("estimate"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].estimate"
                ),
            )
            lower = _require_numeric_value(
                estimate_payload.get("lower"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].lower"
                ),
            )
            upper = _require_numeric_value(
                estimate_payload.get("upper"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].upper"
                ),
            )
            if not all(math.isfinite(value) for value in (estimate, lower, upper)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}] values must be finite"
                )
            if not (lower <= estimate <= upper):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}] must satisfy lower <= estimate <= upper"
                )
            normalized_estimate: dict[str, Any] = {
                "slice_id": slice_id,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
            if estimate_payload.get("support_n") is not None:
                normalized_estimate["support_n"] = _require_non_negative_int(
                    estimate_payload.get("support_n"),
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"effect_rows[{row_index}].slice_estimates[{estimate_index}].support_n"
                    ),
                    allow_zero=False,
                )
            normalized_slice_estimates.append(normalized_estimate)
        if seen_row_slice_ids != declared_slice_id_set:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}] slice_estimates must cover every declared slice_id exactly once"
            )
        normalized_slice_estimates.sort(key=lambda item: declared_slice_ids.index(str(item["slice_id"])))
        normalized_row = {
            "row_id": row_id,
            "row_label": row_label,
            "verdict": verdict,
            "slice_estimates": normalized_slice_estimates,
        }
        if detail_text:
            normalized_row["detail"] = detail_text
        normalized_effect_rows.append(normalized_row)

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "matrix_panel_title": matrix_panel_title,
        "x_label": x_label,
        "reference_value": reference_value,
        "slice_legend_title": slice_legend_title,
        "slices": normalized_slices,
        "effect_rows": normalized_effect_rows,
        "summary_panel_title": summary_panel_title,
    }

def _validate_interaction_effect_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    estimate_panel_title = _require_non_empty_string(
        payload.get("estimate_panel_title"),
        label=f"{path.name} display `{expected_display_id}` estimate_panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")
    summary_panel_title = _require_non_empty_string(
        payload.get("summary_panel_title"),
        label=f"{path.name} display `{expected_display_id}` summary_panel_title",
    )

    modifiers_payload = payload.get("modifiers")
    if not isinstance(modifiers_payload, list) or not modifiers_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty modifiers list")
    if len(modifiers_payload) < 2 or len(modifiers_payload) > 6:
        raise ValueError(f"{path.name} display `{expected_display_id}` modifiers must contain between 2 and 6 entries")

    supported_verdicts = {"credible", "suggestive", "uncertain"}
    normalized_modifiers: list[dict[str, Any]] = []
    seen_modifier_ids: set[str] = set()
    seen_modifier_labels: set[str] = set()
    for modifier_index, modifier_payload in enumerate(modifiers_payload):
        if not isinstance(modifier_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}] must be an object")
        modifier_id = _require_non_empty_string(
            modifier_payload.get("modifier_id"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].modifier_id",
        )
        if modifier_id in seen_modifier_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].modifier_id must be unique"
            )
        seen_modifier_ids.add(modifier_id)
        modifier_label = _require_non_empty_string(
            modifier_payload.get("modifier_label"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].modifier_label",
        )
        if modifier_label in seen_modifier_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].modifier_label must be unique"
            )
        seen_modifier_labels.add(modifier_label)
        interaction_estimate = _require_numeric_value(
            modifier_payload.get("interaction_estimate"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].interaction_estimate",
        )
        lower = _require_numeric_value(
            modifier_payload.get("lower"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].lower",
        )
        upper = _require_numeric_value(
            modifier_payload.get("upper"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].upper",
        )
        if not all(math.isfinite(value) for value in (interaction_estimate, lower, upper)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}] values must be finite"
            )
        if not (lower <= interaction_estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}] must satisfy lower <= interaction_estimate <= upper"
            )
        support_n = _require_non_negative_int(
            modifier_payload.get("support_n"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].support_n",
            allow_zero=False,
        )
        favored_group_label = _require_non_empty_string(
            modifier_payload.get("favored_group_label"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].favored_group_label",
        )
        interaction_p_value = _require_numeric_value(
            modifier_payload.get("interaction_p_value"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].interaction_p_value",
        )
        if not math.isfinite(interaction_p_value) or interaction_p_value < 0.0 or interaction_p_value > 1.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].interaction_p_value must be between 0.0 and 1.0"
            )
        verdict = _require_non_empty_string(
            modifier_payload.get("verdict"),
            label=f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].verdict",
        )
        if verdict not in supported_verdicts:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` modifiers[{modifier_index}].verdict must be one of credible, suggestive, uncertain"
            )
        normalized_modifiers.append(
            {
                "modifier_id": modifier_id,
                "modifier_label": modifier_label,
                "interaction_estimate": interaction_estimate,
                "lower": lower,
                "upper": upper,
                "support_n": support_n,
                "favored_group_label": favored_group_label,
                "interaction_p_value": interaction_p_value,
                "verdict": verdict,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "estimate_panel_title": estimate_panel_title,
        "x_label": x_label,
        "reference_value": reference_value,
        "summary_panel_title": summary_panel_title,
        "modifiers": normalized_modifiers,
    }


__all__ = [
    "_validate_forest_display_payload",
    "_validate_compact_effect_estimate_panel_display_payload",
    "_validate_coefficient_path_panel_display_payload",
    "_validate_broader_heterogeneity_summary_panel_display_payload",
    "_validate_interaction_effect_summary_panel_display_payload",
]
