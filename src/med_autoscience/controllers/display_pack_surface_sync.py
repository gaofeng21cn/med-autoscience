from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience import display_registry
from med_autoscience.display_source_contract import (
    INPUT_FILENAME_BY_SCHEMA_ID,
    TABLE_INPUT_FILENAME_BY_SCHEMA_ID,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relpath_from_workspace(path: Path, workspace_root: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def _update_top_level_identifier(
    *,
    path: Path,
    field_name: str,
    expected_identifier: str,
) -> bool:
    payload = load_json(path)
    current_identifier = str(payload.get(field_name) or "").strip()
    if not current_identifier:
        raise ValueError(f"{path.name} is missing `{field_name}`")
    if current_identifier == expected_identifier:
        return False
    payload[field_name] = expected_identifier
    dump_json(path, payload)
    return True


def _update_display_template_ids(
    *,
    path: Path,
    expected_template_ids: dict[str, str],
) -> bool:
    payload = load_json(path)
    displays = payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError(f"{path.name} must contain a displays list")

    remaining_display_ids = set(expected_template_ids)
    changed = False
    for index, entry in enumerate(displays):
        if not isinstance(entry, dict):
            raise ValueError(f"{path.name} displays[{index}] must be an object")
        display_id = str(entry.get("display_id") or "").strip()
        if display_id not in expected_template_ids:
            continue
        observed_template_id = str(entry.get("template_id") or "").strip()
        if not observed_template_id:
            raise ValueError(f"{path.name} displays[{index}] is missing `template_id`")
        expected_template_id = expected_template_ids[display_id]
        if observed_template_id != expected_template_id:
            entry["template_id"] = expected_template_id
            changed = True
        remaining_display_ids.discard(display_id)

    if remaining_display_ids:
        missing_display_ids = ", ".join(sorted(remaining_display_ids))
        raise ValueError(f"{path.name} is missing displays for: {missing_display_ids}")

    if changed:
        dump_json(path, payload)
    return changed


def _update_renderer_contract_template_ids(
    *,
    path: Path,
    expected_template_ids: dict[str, str],
) -> bool:
    payload = load_json(path)
    figures = payload.get("figures")
    if not isinstance(figures, list):
        raise ValueError(f"{path.name} must contain a figures list")

    remaining_figure_ids = set(expected_template_ids)
    changed = False
    for index, entry in enumerate(figures):
        if not isinstance(entry, dict):
            raise ValueError(f"{path.name} figures[{index}] must be an object")
        figure_id = str(entry.get("figure_id") or "").strip()
        if figure_id not in expected_template_ids:
            continue
        renderer_contract = entry.get("renderer_contract")
        if not isinstance(renderer_contract, dict):
            raise ValueError(f"{path.name} figures[{index}] is missing renderer_contract")
        observed_template_id = str(renderer_contract.get("template_id") or "").strip()
        if not observed_template_id:
            raise ValueError(f"{path.name} figures[{index}].renderer_contract is missing `template_id`")
        expected_template_id = expected_template_ids[figure_id]
        if observed_template_id != expected_template_id:
            renderer_contract["template_id"] = expected_template_id
            changed = True
        remaining_figure_ids.discard(figure_id)

    if remaining_figure_ids:
        missing_figure_ids = ", ".join(sorted(remaining_figure_ids))
        raise ValueError(f"{path.name} is missing figures for: {missing_figure_ids}")

    if changed:
        dump_json(path, payload)
    return changed


def sync_display_pack_surface(*, paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).resolve()
    workspace_root = resolved_paper_root.parent
    registry_payload = load_json(resolved_paper_root / "display_registry.json")
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json must contain a displays list")

    figure_display_templates_by_input_path: dict[Path, dict[str, str]] = {}
    illustration_shell_ids_by_path: dict[Path, str] = {}
    table_shell_ids_by_path: dict[Path, str] = {}
    figure_semantics_template_ids: dict[str, str] = {}

    for index, display in enumerate(displays):
        if not isinstance(display, dict):
            raise ValueError(f"display_registry.json displays[{index}] must be an object")
        display_id = str(display.get("display_id") or "").strip()
        display_kind = str(display.get("display_kind") or "").strip()
        requirement_key = str(display.get("requirement_key") or "").strip()
        catalog_id = str(display.get("catalog_id") or "").strip()
        if not display_id or not display_kind or not requirement_key:
            raise ValueError(f"display_registry.json displays[{index}] must include display_id, display_kind, and requirement_key")

        if display_kind == "figure" and display_registry.is_evidence_figure_template(requirement_key):
            spec = display_registry.get_evidence_figure_spec(requirement_key)
            input_filename = INPUT_FILENAME_BY_SCHEMA_ID.get(spec.input_schema_id)
            if input_filename is None:
                raise ValueError(f"unsupported evidence input_schema_id `{spec.input_schema_id}` for `{requirement_key}`")
            input_path = resolved_paper_root / input_filename
            figure_display_templates_by_input_path.setdefault(input_path, {})[display_id] = spec.template_id
            if catalog_id:
                figure_semantics_template_ids[catalog_id] = spec.template_id
            continue

        if display_kind == "figure" and display_registry.is_illustration_shell(requirement_key):
            spec = display_registry.get_illustration_shell_spec(requirement_key)
            if requirement_key == "cohort_flow_figure":
                cohort_flow_path = resolved_paper_root / "cohort_flow.json"
                if cohort_flow_path.exists():
                    illustration_shell_ids_by_path[cohort_flow_path] = spec.shell_id
            if catalog_id:
                figure_semantics_template_ids[catalog_id] = spec.shell_id
            continue

        if display_kind == "table":
            spec = display_registry.get_table_shell_spec(requirement_key)
            input_filename = TABLE_INPUT_FILENAME_BY_SCHEMA_ID.get(spec.input_schema_id)
            if input_filename is None:
                raise ValueError(f"unsupported table input_schema_id `{spec.input_schema_id}` for `{requirement_key}`")
            table_shell_ids_by_path[resolved_paper_root / input_filename] = spec.shell_id
            continue

        raise ValueError(f"unsupported display registry entry `{display_kind}` / `{requirement_key}`")

    updated_files: list[Path] = []

    for path, expected_template_ids in sorted(figure_display_templates_by_input_path.items()):
        if _update_display_template_ids(path=path, expected_template_ids=expected_template_ids):
            updated_files.append(path)

    for path, expected_shell_id in sorted(illustration_shell_ids_by_path.items()):
        if _update_top_level_identifier(path=path, field_name="shell_id", expected_identifier=expected_shell_id):
            updated_files.append(path)

    for path, expected_shell_id in sorted(table_shell_ids_by_path.items()):
        if _update_top_level_identifier(path=path, field_name="table_shell_id", expected_identifier=expected_shell_id):
            updated_files.append(path)

    figure_semantics_path = resolved_paper_root / "figure_semantics_manifest.json"
    if figure_semantics_path.exists() and figure_semantics_template_ids:
        if _update_renderer_contract_template_ids(
            path=figure_semantics_path,
            expected_template_ids=figure_semantics_template_ids,
        ):
            updated_files.append(figure_semantics_path)

    graphical_abstract_path = resolved_paper_root / "submission_graphical_abstract.json"
    if graphical_abstract_path.exists():
        graphical_abstract_shell_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
        if _update_top_level_identifier(
            path=graphical_abstract_path,
            field_name="shell_id",
            expected_identifier=graphical_abstract_shell_id,
        ):
            updated_files.append(graphical_abstract_path)

    return {
        "status": "synced",
        "paper_root": str(resolved_paper_root),
        "updated_files": [
            relpath_from_workspace(path, workspace_root)
            for path in sorted(set(updated_files))
        ],
    }
