from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")



_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def _validate_cohort_flow_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{path.name} must contain a non-empty steps list")
    normalized_steps: list[dict[str, Any]] = []
    step_ids: set[str] = set()
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{path.name} steps[{index}] must be an object")
        step_id = str(step.get("step_id") or "").strip()
        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()
        if not step_id or not label:
            raise ValueError(f"{path.name} steps[{index}] must include step_id and label")
        if step_id in step_ids:
            raise ValueError(f"{path.name} steps[{index}].step_id must be unique")
        step_ids.add(step_id)
        raw_n = step.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} steps[{index}].n must be an integer")
        raw_columns = step.get("columns")
        if raw_columns is not None and not isinstance(raw_columns, int):
            raise ValueError(f"{path.name} steps[{index}].columns must be an integer when provided")
        role = str(step.get("role") or "").strip()
        role_label = str(step.get("role_label") or _COHORT_FLOW_STEP_ROLE_LABELS.get(role, "")).strip()
        normalized_steps.append(
            {
                "step_id": step_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
                "columns": raw_columns,
                "role": role,
                "role_label": role_label,
            }
        )

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
        endpoint_id = str(endpoint.get("endpoint_id") or "").strip()
        label = str(endpoint.get("label") or "").strip()
        detail = str(endpoint.get("detail") or "").strip()
        if not endpoint_id or not label:
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must include endpoint_id and label")
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
        block_id = str(block.get("panel_id") or block.get("block_id") or "").strip()
        raw_block_type = str(block.get("layout_role") or block.get("block_type") or "").strip()
        block_type = _COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES.get(raw_block_type, raw_block_type)
        style_role = str(block.get("style_role") or "secondary").strip().lower()
        title = str(block.get("title") or "").strip()
        items = block.get("lines")
        if items is None:
            items = block.get("items")
        if not block_id or not block_type or not title:
            raise ValueError(f"{path.name} design_panels[{index}] must include panel_id/block_id, layout_role/block_type, and title")
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

    layout_mode = str(payload.get("layout_mode") or "two_panel_flow").strip().lower()
    if layout_mode not in _COHORT_FLOW_LAYOUT_MODES:
        allowed_modes = ", ".join(sorted(_COHORT_FLOW_LAYOUT_MODES))
        raise ValueError(f"{path.name} layout_mode must be one of: {allowed_modes}")
    comparison_summary_payload = payload.get("comparison_summary") or {}
    if comparison_summary_payload and not isinstance(comparison_summary_payload, dict):
        raise ValueError(f"{path.name} comparison_summary must be an object when provided")

    return {
        "display_id": str(payload.get("display_id") or "").strip(),
        "title": str(payload.get("title") or "").strip(),
        "caption": str(payload.get("caption") or "").strip(),
        "steps": normalized_steps,
        "exclusions": normalized_exclusions,
        "endpoint_inventory": normalized_endpoint_inventory,
        "design_panels": normalized_design_panels,
        "layout_mode": layout_mode,
        "comparison_summary": {
            "title": str(comparison_summary_payload.get("title") or "").strip(),
            "body": str(
                comparison_summary_payload.get("body") or comparison_summary_payload.get("text") or ""
            ).strip(),
        },
    }

