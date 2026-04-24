from __future__ import annotations

import re

from .shared import Any, Path, _COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES, _format_percent_1dp, _require_non_empty_string, _require_non_negative_int, _require_numeric_list, _require_numeric_value, _require_probability_value, display_registry

def _slugify_legacy_cohort_flow_id(raw_value: object, *, label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(raw_value or "").strip().lower()).strip("_")
    if not normalized:
        raise ValueError(f"{label} must normalize to a non-empty identifier")
    return normalized


def _normalize_cohort_flow_step_id(*, path: Path, step: dict[str, Any], index: int) -> str:
    step_id = str(step.get("step_id") or "").strip()
    if step_id:
        return step_id
    legacy_cohort = str(step.get("cohort") or "").strip()
    if not legacy_cohort:
        raise ValueError(f"{path.name} steps[{index}] must include step_id or legacy cohort, and label")
    return _slugify_legacy_cohort_flow_id(
        legacy_cohort,
        label=f"{path.name} steps[{index}].cohort",
    )


def _normalize_cohort_flow_endpoint_id(*, path: Path, endpoint: dict[str, Any], index: int) -> str:
    endpoint_id = str(endpoint.get("endpoint_id") or "").strip()
    if endpoint_id:
        return endpoint_id
    legacy_endpoint = str(endpoint.get("endpoint") or "").strip()
    if not legacy_endpoint:
        raise ValueError(f"{path.name} endpoint_inventory[{index}] must include endpoint_id or legacy endpoint, and label")
    return _slugify_legacy_cohort_flow_id(
        legacy_endpoint,
        label=f"{path.name} endpoint_inventory[{index}].endpoint",
    )


def _normalize_cohort_flow_design_panel_items(items: object) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            normalized_items.append({"label": item.strip(), "detail": ""})
        elif isinstance(item, dict):
            normalized_items.append(item)
        else:
            normalized_items.append({})
    return normalized_items

def _validate_cohort_flow_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{path.name} must contain a non-empty steps list")
    normalized_steps: list[dict[str, Any]] = []
    step_ids: set[str] = set()
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{path.name} steps[{index}] must be an object")
        step_id = _normalize_cohort_flow_step_id(path=path, step=step, index=index)
        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()
        if not label:
            raise ValueError(f"{path.name} steps[{index}] must include step_id or legacy cohort, and label")
        if step_id in step_ids:
            raise ValueError(f"{path.name} steps[{index}].step_id must be unique")
        step_ids.add(step_id)
        raw_n = step.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} steps[{index}].n must be an integer")
        normalized_steps.append({"step_id": step_id, "label": label, "detail": detail, "n": raw_n})

    exclusions_payload = payload.get("exclusions")
    if exclusions_payload is None:
        exclusions_payload = payload.get("exclusion_branches") or []
    if not isinstance(exclusions_payload, list):
        raise ValueError(f"{path.name} exclusions must be a list when provided")
    normalized_exclusions: list[dict[str, Any]] = []
    exclusion_branch_ids: set[str] = set()
    for index, branch in enumerate(exclusions_payload):
        if not isinstance(branch, dict):
            raise ValueError(f"{path.name} exclusions[{index}] must be an object")
        branch_id = str(branch.get("exclusion_id") or branch.get("branch_id") or "").strip()
        from_step_id = str(branch.get("from_step_id") or "").strip()
        label = str(branch.get("label") or "").strip()
        detail = str(branch.get("detail") or "").strip()
        if not branch_id or not from_step_id or not label:
            raise ValueError(
                f"{path.name} exclusions[{index}] must include exclusion_id/branch_id, from_step_id, and label"
            )
        if branch_id in exclusion_branch_ids:
            raise ValueError(f"{path.name} exclusions[{index}].exclusion_id must be unique")
        if from_step_id not in step_ids:
            raise ValueError(f"{path.name} exclusions[{index}].from_step_id must reference a declared step")
        raw_n = branch.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} exclusions[{index}].n must be an integer")
        exclusion_branch_ids.add(branch_id)
        normalized_exclusions.append(
            {
                "exclusion_id": branch_id,
                "from_step_id": from_step_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
            }
        )

    endpoint_inventory_payload = payload.get("endpoint_inventory") or []
    if not isinstance(endpoint_inventory_payload, list):
        raise ValueError(f"{path.name} endpoint_inventory must be a list when provided")
    normalized_endpoint_inventory: list[dict[str, Any]] = []
    endpoint_ids: set[str] = set()
    for index, endpoint in enumerate(endpoint_inventory_payload):
        if not isinstance(endpoint, dict):
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must be an object")
        endpoint_id = _normalize_cohort_flow_endpoint_id(path=path, endpoint=endpoint, index=index)
        label = str(endpoint.get("label") or endpoint.get("endpoint") or "").strip()
        detail = str(endpoint.get("detail") or endpoint.get("status") or "").strip()
        if not label:
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must include endpoint_id or legacy endpoint, and label")
        if endpoint_id in endpoint_ids:
            raise ValueError(f"{path.name} endpoint_inventory[{index}].endpoint_id must be unique")
        raw_n = endpoint.get("n")
        if raw_n is None:
            raw_n = endpoint.get("event_n")
        if raw_n is not None and not isinstance(raw_n, int):
            raise ValueError(f"{path.name} endpoint_inventory[{index}].n must be an integer when provided")
        endpoint_ids.add(endpoint_id)
        normalized_endpoint_inventory.append(
            {
                "endpoint_id": endpoint_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
            }
        )

    design_panels_payload = payload.get("design_panels")
    if design_panels_payload is None:
        design_panels_payload = payload.get("sidecar_blocks") or []
    if not isinstance(design_panels_payload, list):
        raise ValueError(f"{path.name} design_panels must be a list when provided")
    normalized_design_panels: list[dict[str, Any]] = []
    sidecar_block_ids: set[str] = set()
    for index, block in enumerate(design_panels_payload):
        if not isinstance(block, dict):
            raise ValueError(f"{path.name} design_panels[{index}] must be an object")
        title = str(block.get("title") or block.get("label") or "").strip()
        block_id = str(block.get("panel_id") or block.get("block_id") or "").strip()
        if not block_id and title:
            block_id = _slugify_legacy_cohort_flow_id(title, label=f"{path.name} design_panels[{index}].label")
        raw_block_type = str(block.get("layout_role") or block.get("block_type") or "").strip()
        if not raw_block_type and block.get("items") is not None:
            raw_block_type = "wide_bottom"
        block_type = _COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES.get(raw_block_type, raw_block_type)
        style_role = str(block.get("style_role") or "secondary").strip().lower()
        items = block.get("lines")
        if items is None:
            items = _normalize_cohort_flow_design_panel_items(block.get("items"))
        if not block_id or not block_type or not title:
            raise ValueError(f"{path.name} design_panels[{index}] must include panel_id/block_id or legacy label, layout_role/block_type, and title/label")
        if style_role not in {"primary", "secondary", "context", "audit"}:
            raise ValueError(
                f"{path.name} design_panels[{index}].style_role must be one of primary, secondary, context, audit"
            )
        if block_id in sidecar_block_ids:
            raise ValueError(f"{path.name} design_panels[{index}].panel_id must be unique")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{path.name} design_panels[{index}].lines/items must be a non-empty list")
        normalized_items: list[dict[str, Any]] = []
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"{path.name} design_panels[{index}].lines[{item_index}] must be an object")
            label = str(item.get("label") or "").strip()
            detail = str(item.get("detail") or "").strip()
            if not label:
                raise ValueError(f"{path.name} design_panels[{index}].lines[{item_index}].label must be non-empty")
            normalized_items.append({"label": label, "detail": detail})
        sidecar_block_ids.add(block_id)
        normalized_design_panels.append(
            {
                "panel_id": block_id,
                "layout_role": block_type,
                "style_role": style_role,
                "title": title,
                "lines": normalized_items,
            }
        )

    return {
        "display_id": str(payload.get("display_id") or "").strip(),
        "title": str(payload.get("title") or "").strip(),
        "caption": str(payload.get("caption") or "").strip(),
        "steps": normalized_steps,
        "exclusions": normalized_exclusions,
        "endpoint_inventory": normalized_endpoint_inventory,
        "design_panels": normalized_design_panels,
    }

def _validate_submission_graphical_abstract_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    catalog_id = _require_non_empty_string(payload.get("catalog_id"), label=f"{path.name} catalog_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")
    caption = _require_non_empty_string(payload.get("caption"), label=f"{path.name} caption")

    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} must contain a non-empty panels list")
    normalized_panels: list[dict[str, Any]] = []
    panel_ids: set[str] = set()
    for panel_index, panel in enumerate(panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} panels[{panel_index}].panel_id",
        )
        if panel_id in panel_ids:
            raise ValueError(f"{path.name} panels[{panel_index}].panel_id must be unique")
        panel_ids.add(panel_id)
        rows_payload = panel.get("rows")
        if not isinstance(rows_payload, list) or not rows_payload:
            raise ValueError(f"{path.name} panels[{panel_index}].rows must be a non-empty list")
        normalized_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows_payload):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name} panels[{panel_index}].rows[{row_index}] must be an object")
            cards_payload = row.get("cards")
            if not isinstance(cards_payload, list) or not cards_payload:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}].cards must be a non-empty list"
                )
            if len(cards_payload) > 2:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}] supports at most two cards"
                )
            normalized_cards: list[dict[str, Any]] = []
            card_ids: set[str] = set()
            for card_index, card in enumerate(cards_payload):
                if not isinstance(card, dict):
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}] must be an object"
                    )
                card_id = _require_non_empty_string(
                    card.get("card_id"),
                    label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id",
                )
                if card_id in card_ids:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id must be unique within the row"
                    )
                card_ids.add(card_id)
                accent_role = str(card.get("accent_role") or "neutral").strip().lower()
                if accent_role not in {"neutral", "primary", "secondary", "contrast", "audit"}:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].accent_role "
                        "must be one of neutral, primary, secondary, contrast, audit"
                    )
                normalized_cards.append(
                    {
                        "card_id": card_id,
                        "title": _require_non_empty_string(
                            card.get("title"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].title",
                        ),
                        "value": _require_non_empty_string(
                            card.get("value"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].value",
                        ),
                        "detail": str(card.get("detail") or "").strip(),
                        "accent_role": accent_role,
                    }
                )
            normalized_rows.append({"cards": normalized_cards})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": _require_non_empty_string(
                    panel.get("panel_label"),
                    label=f"{path.name} panels[{panel_index}].panel_label",
                ),
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} panels[{panel_index}].title",
                ),
                "subtitle": _require_non_empty_string(
                    panel.get("subtitle"),
                    label=f"{path.name} panels[{panel_index}].subtitle",
                ),
                "rows": normalized_rows,
            }
        )

    footer_pills_payload = payload.get("footer_pills") or []
    if not isinstance(footer_pills_payload, list):
        raise ValueError(f"{path.name} footer_pills must be a list when provided")
    normalized_footer_pills: list[dict[str, Any]] = []
    pill_ids: set[str] = set()
    for pill_index, pill in enumerate(footer_pills_payload):
        if not isinstance(pill, dict):
            raise ValueError(f"{path.name} footer_pills[{pill_index}] must be an object")
        pill_id = _require_non_empty_string(
            pill.get("pill_id"),
            label=f"{path.name} footer_pills[{pill_index}].pill_id",
        )
        if pill_id in pill_ids:
            raise ValueError(f"{path.name} footer_pills[{pill_index}].pill_id must be unique")
        pill_ids.add(pill_id)
        panel_id = _require_non_empty_string(
            pill.get("panel_id"),
            label=f"{path.name} footer_pills[{pill_index}].panel_id",
        )
        if panel_id not in panel_ids:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].panel_id must reference a declared panel"
            )
        style_role = str(pill.get("style_role") or "secondary").strip().lower()
        if style_role not in {"primary", "secondary", "contrast", "audit", "neutral"}:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].style_role must be one of primary, secondary, contrast, audit, neutral"
            )
        normalized_footer_pills.append(
            {
                "pill_id": pill_id,
                "panel_id": panel_id,
                "label": _require_non_empty_string(
                    pill.get("label"),
                    label=f"{path.name} footer_pills[{pill_index}].label",
                ),
                "style_role": style_role,
            }
        )

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "submission_companion").strip() or "submission_companion",
        "panels": normalized_panels,
        "footer_pills": normalized_footer_pills,
    }

def _validate_baseline_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name} must contain a non-empty groups list")
    group_labels: list[str] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"{path.name} groups[{index}] must be an object")
        label = str(group.get("label") or "").strip()
        if not label:
            raise ValueError(f"{path.name} groups[{index}] must include label")
        group_labels.append(label)

    variables = payload.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError(f"{path.name} must contain a non-empty variables list")
    normalized_rows: list[dict[str, Any]] = []
    for index, variable in enumerate(variables):
        if not isinstance(variable, dict):
            raise ValueError(f"{path.name} variables[{index}] must be an object")
        label = str(variable.get("label") or "").strip()
        values = variable.get("values")
        if not label or not isinstance(values, list) or len(values) != len(group_labels):
            raise ValueError(
                f"{path.name} variables[{index}] must include label and values matching the number of groups"
            )
        normalized_rows.append({"label": label, "values": [str(item).strip() for item in values]})
    return group_labels, normalized_rows

def _validate_column_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    columns = payload.get("columns")
    if not isinstance(columns, list) or not columns:
        raise ValueError(f"{path.name} must contain a non-empty columns list")
    column_labels: list[str] = []
    for index, column in enumerate(columns):
        if not isinstance(column, dict):
            raise ValueError(f"{path.name} columns[{index}] must be an object")
        column_labels.append(
            _require_non_empty_string(column.get("label"), label=f"{path.name} columns[{index}].label")
        )

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        label = _require_non_empty_string(row.get("label"), label=f"{path.name} rows[{index}].label")
        values = row.get("values")
        if not isinstance(values, list) or len(values) != len(column_labels):
            raise ValueError(
                f"{path.name} rows[{index}] must include values matching the number of columns"
            )
        normalized_rows.append({"label": label, "values": [str(item).strip() for item in values]})
    return column_labels, normalized_rows

def _validate_performance_summary_table_generic_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[str, list[str], list[dict[str, Any]]]:
    row_header_label = _require_non_empty_string(
        payload.get("row_header_label"),
        label=f"{path.name} row_header_label",
    )
    column_labels, rows = _validate_column_table_payload(path, payload)
    return row_header_label, column_labels, rows

def _validate_grouped_risk_event_summary_table_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[list[str], list[list[str]]]:
    headers = [
        _require_non_empty_string(payload.get("surface_column_label"), label=f"{path.name} surface_column_label"),
        _require_non_empty_string(payload.get("stratum_column_label"), label=f"{path.name} stratum_column_label"),
        _require_non_empty_string(payload.get("cases_column_label"), label=f"{path.name} cases_column_label"),
        _require_non_empty_string(payload.get("events_column_label"), label=f"{path.name} events_column_label"),
        _require_non_empty_string(payload.get("risk_column_label"), label=f"{path.name} risk_column_label"),
    ]
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[list[str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        surface = _require_non_empty_string(row.get("surface"), label=f"{path.name} rows[{index}].surface")
        stratum = _require_non_empty_string(row.get("stratum"), label=f"{path.name} rows[{index}].stratum")
        cases = _require_non_negative_int(row.get("cases"), label=f"{path.name} rows[{index}].cases", allow_zero=False)
        events = _require_non_negative_int(row.get("events"), label=f"{path.name} rows[{index}].events")
        if events > cases:
            raise ValueError(f"{path.name} rows[{index}].events must not exceed cases")
        risk_display = _require_non_empty_string(
            row.get("risk_display"),
            label=f"{path.name} rows[{index}].risk_display",
        )
        expected_risk_display = _format_percent_1dp(numerator=events, denominator=cases)
        if risk_display != expected_risk_display:
            raise ValueError(
                f"{path.name} rows[{index}].risk_display must equal {expected_risk_display} for {events}/{cases}"
            )
        normalized_rows.append([surface, stratum, str(cases), str(events), risk_display])
    return headers, normalized_rows

def _validate_reference_line_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> dict[str, Any] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    ref_x = _require_numeric_list(payload.get("x"), label=f"{path.name} {label}.x")
    ref_y = _require_numeric_list(payload.get("y"), label=f"{path.name} {label}.y")
    if len(ref_x) != len(ref_y):
        raise ValueError(f"{path.name} {label}.x and .y must have the same length")
    return {
        "x": ref_x,
        "y": ref_y,
        "label": str(payload.get("label") or "").strip(),
    }

def _validate_axis_window_payload(
    *,
    path: Path,
    payload: object,
    label: str,
    require_probability_bounds: bool = False,
) -> dict[str, float] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    reader = _require_probability_value if require_probability_bounds else _require_numeric_value
    xmin = reader(payload.get("xmin"), label=f"{path.name} {label}.xmin")
    xmax = reader(payload.get("xmax"), label=f"{path.name} {label}.xmax")
    ymin = reader(payload.get("ymin"), label=f"{path.name} {label}.ymin")
    ymax = reader(payload.get("ymax"), label=f"{path.name} {label}.ymax")
    if xmin >= xmax:
        raise ValueError(f"{path.name} {label}.xmin must be < .xmax")
    if ymin >= ymax:
        raise ValueError(f"{path.name} {label}.ymin must be < .ymax")
    return {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
    }

def _validate_curve_series_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_series: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        series_label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} {label}[{index}].label",
        )
        x = _require_numeric_list(item.get("x"), label=f"{path.name} {label}[{index}].x")
        y = _require_numeric_list(item.get("y"), label=f"{path.name} {label}[{index}].y")
        if len(x) != len(y):
            raise ValueError(f"{path.name} {label}[{index}].x and .y must have the same length")
        normalized_series.append(
            {
                "label": series_label,
                "x": x,
                "y": y,
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )
    return normalized_series

def _validate_single_curve_series_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    normalized = _validate_curve_series_payload(
        path=path,
        payload=[payload],
        label=label,
    )
    return normalized[0]

def _validate_audit_panel_collection(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_panels: list[dict[str, Any]] = []
    panel_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        panel_id = _require_non_empty_string(item.get("panel_id"), label=f"{path.name} {label}[{index}].panel_id")
        if panel_id in panel_ids:
            raise ValueError(f"{path.name} {label}[{index}].panel_id must be unique")
        rows = item.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{path.name} {label}[{index}].rows must contain a non-empty list")
        normalized_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name} {label}[{index}].rows[{row_index}] must be an object")
            normalized_rows.append(
                {
                    "label": _require_non_empty_string(
                        row.get("label"),
                        label=f"{path.name} {label}[{index}].rows[{row_index}].label",
                    ),
                    "value": _require_numeric_value(
                        row.get("value"),
                        label=f"{path.name} {label}[{index}].rows[{row_index}].value",
                    ),
                }
            )
        panel_ids.add(panel_id)
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": _require_non_empty_string(
                    item.get("panel_label"),
                    label=f"{path.name} {label}[{index}].panel_label",
                ),
                "title": _require_non_empty_string(
                    item.get("title"),
                    label=f"{path.name} {label}[{index}].title",
                ),
                "x_label": _require_non_empty_string(
                    item.get("x_label"),
                    label=f"{path.name} {label}[{index}].x_label",
                ),
                "reference_value": (
                    _require_numeric_value(
                        item.get("reference_value"),
                        label=f"{path.name} {label}[{index}].reference_value",
                    )
                    if item.get("reference_value") is not None
                    else None
                ),
                "rows": normalized_rows,
            }
        )
    return normalized_panels

def _validate_labeled_order_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, str]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_items: list[dict[str, str]] = []
    seen_labels: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        item_label = _require_non_empty_string(item.get("label"), label=f"{path.name} {label}[{index}].label")
        if item_label in seen_labels:
            raise ValueError(f"{path.name} {label}[{index}].label must be unique")
        seen_labels.add(item_label)
        normalized_items.append({"label": item_label})
    return normalized_items

def _validate_panel_order_payload(
    *,
    path: Path,
    payload: object,
    label: str,
    max_panels: int = 2,
) -> list[dict[str, str]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    if len(payload) > max_panels:
        raise ValueError(f"{path.name} {label} must contain at most {max_panels} panels")
    normalized_items: list[dict[str, str]] = []
    seen_panel_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} {label}[{index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} {label}[{index}].panel_id must be unique")
        seen_panel_ids.add(panel_id)
        normalized_items.append(
            {
                "panel_id": panel_id,
                "panel_title": _require_non_empty_string(
                    item.get("panel_title"),
                    label=f"{path.name} {label}[{index}].panel_title",
                ),
            }
        )
    return normalized_items

def _validate_sample_order_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, str]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_items: list[dict[str, str]] = []
    seen_sample_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        sample_id = _require_non_empty_string(
            item.get("sample_id"),
            label=f"{path.name} {label}[{index}].sample_id",
        )
        if sample_id in seen_sample_ids:
            raise ValueError(f"{path.name} {label}[{index}].sample_id must be unique")
        seen_sample_ids.add(sample_id)
        normalized_items.append({"sample_id": sample_id})
    return normalized_items


__all__ = [
    "_validate_cohort_flow_payload",
    "_validate_submission_graphical_abstract_payload",
    "_validate_baseline_table_payload",
    "_validate_column_table_payload",
    "_validate_performance_summary_table_generic_payload",
    "_validate_grouped_risk_event_summary_table_payload",
    "_validate_reference_line_payload",
    "_validate_axis_window_payload",
    "_validate_curve_series_payload",
    "_validate_single_curve_series_payload",
    "_validate_audit_panel_collection",
    "_validate_labeled_order_payload",
    "_validate_panel_order_payload",
    "_validate_sample_order_payload",
]
