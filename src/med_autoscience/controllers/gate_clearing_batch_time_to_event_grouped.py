from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from med_autoscience.display_source_contract import INPUT_FILENAME_BY_SCHEMA_ID


def time_to_event_risk_group_surface_present(
    *,
    paper_root: Path,
    read_json: Callable[[Path], dict[str, Any]],
) -> bool:
    payload_path = Path(paper_root) / INPUT_FILENAME_BY_SCHEMA_ID["time_to_event_grouped_inputs_v1"]
    registry_payload = read_json(Path(paper_root) / "display_registry.json")
    payload = read_json(payload_path)
    displays = payload.get("displays")
    registry_items = registry_payload.get("displays")
    if not isinstance(displays, list) or not isinstance(registry_items, list):
        return False
    risk_summary_display_ids = {
        str(item.get("display_id") or "").strip()
        for item in registry_items
        if isinstance(item, dict)
        and str(item.get("requirement_key") or "").strip() == "time_to_event_risk_group_summary"
        and str(item.get("display_id") or "").strip()
    }
    if not risk_summary_display_ids:
        return False
    return any(
        isinstance(display, dict)
        and str(display.get("display_id") or "").strip() in risk_summary_display_ids
        for display in displays
    )
