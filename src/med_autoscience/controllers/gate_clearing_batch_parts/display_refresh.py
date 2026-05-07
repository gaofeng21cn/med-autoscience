from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import gate_clearing_batch_time_to_event_grouped
from med_autoscience.controllers import gate_clearing_batch_transportability
from med_autoscience.controllers import publication_shell_sync
from med_autoscience.controllers.gate_clearing_batch_parts.io_utils import (
    non_empty_text,
    read_json,
    string_list,
    write_json,
)
from med_autoscience.display_source_contract import INPUT_FILENAME_BY_SCHEMA_ID


def publication_shell_surface_needs_sync(*, study_root: Path, paper_root: Path) -> bool:
    try:
        publication_shell_sync._resolve_cohort_flow_source_payload(
            study_root=study_root,
            paper_root=paper_root,
        )
        publication_shell_sync._resolve_table1_source_path(
            study_root=study_root,
            paper_root=paper_root,
        )
        registry_payload = read_json(Path(paper_root) / "display_registry.json")
        publication_shell_sync._require_binding(
            registry_payload=registry_payload,
            requirement_key="cohort_flow_figure",
        )
        publication_shell_sync._require_binding(
            registry_payload=registry_payload,
            requirement_key="table1_baseline_characteristics",
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return False
    payload = read_json(Path(paper_root) / "baseline_characteristics_schema.json")
    groups = payload.get("groups")
    variables = payload.get("variables")
    if not isinstance(groups, list) or not groups:
        return True
    if not isinstance(variables, list) or not variables:
        return True
    return any(not isinstance(item, dict) for item in variables)


def _registry_display_ids_for_requirement(
    *,
    registry_items: object,
    requirement_key: str,
) -> set[str]:
    if not isinstance(registry_items, list):
        return set()
    display_ids: set[str] = set()
    for item in registry_items:
        if not isinstance(item, dict):
            continue
        if str(item.get("requirement_key") or "").strip() != requirement_key:
            continue
        display_id = str(item.get("display_id") or "").strip()
        if display_id:
            display_ids.add(display_id)
    return display_ids


def _time_to_event_grouped_template_ids(
    *,
    display_surface_materialization_controller: Any,
) -> tuple[str, str]:
    expected_template_id = display_surface_materialization_controller.display_registry.get_evidence_figure_spec(
        "time_to_event_risk_group_summary"
    ).template_id
    legacy_template_id = display_surface_materialization_controller.display_registry.get_evidence_figure_spec(
        "cumulative_incidence_grouped"
    ).template_id
    return expected_template_id, legacy_template_id


def _is_legacy_time_to_event_grouped_normalization_candidate(
    *,
    display: object,
    risk_summary_display_ids: set[str],
    expected_template_id: str,
) -> str | None:
    if not isinstance(display, dict):
        return None
    display_id = str(display.get("display_id") or "").strip()
    if display_id not in risk_summary_display_ids:
        return None
    if str(display.get("template_id") or "").strip() != expected_template_id:
        return None
    if isinstance(display.get("risk_group_summaries"), list) and display.get("risk_group_summaries"):
        return None
    groups = display.get("groups")
    if not isinstance(groups, list) or not groups:
        return None
    return display_id


def _legacy_time_to_event_grouped_normalization_candidate_ids(
    *,
    displays: list[object],
    risk_summary_display_ids: set[str],
    expected_template_id: str,
) -> list[str]:
    candidate_display_ids: list[str] = []
    for display in displays:
        display_id = _is_legacy_time_to_event_grouped_normalization_candidate(
            display=display,
            risk_summary_display_ids=risk_summary_display_ids,
            expected_template_id=expected_template_id,
        )
        if display_id is not None:
            candidate_display_ids.append(display_id)
    return candidate_display_ids


def legacy_time_to_event_grouped_payload_normalization_candidates(
    *,
    paper_root: Path,
    display_surface_materialization_controller: Any,
) -> tuple[Path, list[str], str | None, str | None]:
    payload_path = Path(paper_root) / INPUT_FILENAME_BY_SCHEMA_ID["time_to_event_grouped_inputs_v1"]
    registry_payload = read_json(Path(paper_root) / "display_registry.json")
    payload = read_json(payload_path)
    displays = payload.get("displays")
    registry_items = registry_payload.get("displays")
    if not isinstance(displays, list) or not isinstance(registry_items, list):
        return payload_path, [], None, None

    risk_summary_display_ids = _registry_display_ids_for_requirement(
        registry_items=registry_items,
        requirement_key="time_to_event_risk_group_summary",
    )
    if not risk_summary_display_ids:
        return payload_path, [], None, None

    expected_template_id, legacy_template_id = _time_to_event_grouped_template_ids(
        display_surface_materialization_controller=display_surface_materialization_controller,
    )
    candidate_display_ids = _legacy_time_to_event_grouped_normalization_candidate_ids(
        displays=displays,
        risk_summary_display_ids=risk_summary_display_ids,
        expected_template_id=expected_template_id,
    )

    return payload_path, candidate_display_ids, expected_template_id, legacy_template_id


def normalize_legacy_time_to_event_grouped_payloads(
    *,
    paper_root: Path,
    display_surface_materialization_controller: Any,
) -> dict[str, Any]:
    payload_path, candidate_display_ids, expected_template_id, legacy_template_id = (
        legacy_time_to_event_grouped_payload_normalization_candidates(
            paper_root=paper_root,
            display_surface_materialization_controller=display_surface_materialization_controller,
        )
    )
    if expected_template_id is None or legacy_template_id is None:
        return {
            "status": "current",
            "reason": "time-to-event grouped payload or display registry has no normalization candidates",
            "payload_path": str(payload_path),
        }

    if not candidate_display_ids:
        return {
            "status": "current",
            "payload_path": str(payload_path),
            "checked_display_ids": [],
        }

    payload = read_json(payload_path)
    displays = payload.get("displays")
    if not isinstance(displays, list):
        return {
            "status": "current",
            "reason": "time-to-event grouped payload is not readable",
            "payload_path": str(payload_path),
        }
    updated_display_ids: list[str] = []
    candidate_display_id_set = set(candidate_display_ids)
    for display in displays:
        if not isinstance(display, dict):
            continue
        display_id = str(display.get("display_id") or "").strip()
        if display_id not in candidate_display_id_set:
            continue
        display["legacy_requested_template_id"] = expected_template_id
        display["template_id"] = legacy_template_id
        updated_display_ids.append(display_id)

    write_json(payload_path, payload)
    return {
        "status": "updated",
        "payload_path": str(payload_path),
        "updated_payload_paths": [str(payload_path)],
        "updated_display_ids": updated_display_ids,
        "legacy_requested_template_id": expected_template_id,
        "normalized_template_id": legacy_template_id,
    }


def legacy_time_to_event_grouped_payloads_need_normalization(
    *,
    paper_root: Path,
    display_surface_materialization_controller: Any,
) -> bool:
    _, candidate_display_ids, _, _ = legacy_time_to_event_grouped_payload_normalization_candidates(
        paper_root=paper_root,
        display_surface_materialization_controller=display_surface_materialization_controller,
    )
    return bool(candidate_display_ids)


def time_to_event_risk_group_surface_present(*, paper_root: Path) -> bool:
    return gate_clearing_batch_time_to_event_grouped.time_to_event_risk_group_surface_present(
        paper_root=paper_root,
        read_json=read_json,
    )


def display_registry_item_for_requirement(
    *,
    paper_root: Path,
    requirement_key: str,
) -> dict[str, Any] | None:
    registry_payload = read_json(Path(paper_root) / "display_registry.json")
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        return None
    for item in displays:
        if not isinstance(item, dict):
            continue
        if str(item.get("requirement_key") or "").strip() == requirement_key:
            return item
    return None


def time_to_event_direct_migration_display_inputs_need_refresh(
    *,
    paper_root: Path,
    display_surface_materialization_controller: Any,
) -> bool:
    item = display_registry_item_for_requirement(
        paper_root=paper_root,
        requirement_key="multicenter_generalizability_overview",
    )
    if item is None:
        return False
    display_id = non_empty_text(item.get("display_id"))
    if display_id is None:
        return True
    spec = display_surface_materialization_controller.display_registry.get_evidence_figure_spec(
        "multicenter_generalizability_overview"
    )
    try:
        _, payload = display_surface_materialization_controller._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id=display_id,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        if legacy_direct_migration_feature_shift_payload_present(
            paper_root=paper_root,
            input_schema_id=spec.input_schema_id,
            display_id=display_id,
        ):
            return False
        return True
    source_paths = string_list(payload.get("source_paths"))
    return any("ops/med-the research workflow" in item for item in source_paths)


def legacy_direct_migration_feature_shift_payload_present(
    *,
    paper_root: Path,
    input_schema_id: str,
    display_id: str,
) -> bool:
    return gate_clearing_batch_transportability.legacy_direct_migration_feature_shift_payload_present(
        paper_root=paper_root,
        input_schema_id=input_schema_id,
        display_id=display_id,
        input_filename_by_schema_id=INPUT_FILENAME_BY_SCHEMA_ID,
    )
