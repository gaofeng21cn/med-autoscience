from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience import display_registry
from med_autoscience.display_source_contract import (
    INPUT_FILENAME_BY_SCHEMA_ID,
    TABLE_INPUT_FILENAME_BY_SCHEMA_ID,
)
from med_autoscience.controllers.display_surface_materialization.contract_backed_registry import (
    resolve_contract_backed_figure_registry_fields,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relpath_from_workspace(path: Path, workspace_root: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def _resolve_workspace_path(path_value: object, *, paper_root: Path) -> Path:
    raw_path = str(path_value or "").strip()
    if not raw_path:
        raise ValueError("expected non-empty paper workspace path")
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _contract_path_from_shell_path(shell_path: str) -> str:
    if shell_path.endswith(".shell.json"):
        return f"{shell_path.removesuffix('.shell.json')}.contract.json"
    return str(Path(shell_path).with_suffix(".contract.json"))


def _contract_backed_figure_contract_candidates(
    *,
    paper_root: Path,
    display: dict[str, Any],
    shell_payload: dict[str, Any],
) -> list[Path]:
    candidate_values: list[str] = []
    for value in (shell_payload.get("source_contract_path"), display.get("source_contract_path")):
        normalized = str(value or "").strip()
        if normalized:
            candidate_values.append(normalized)

    shell_path = str(display.get("shell_path") or "").strip()
    if shell_path:
        candidate_values.append(_contract_path_from_shell_path(shell_path))

    display_id = str(shell_payload.get("display_id") or display.get("display_id") or "").strip()
    if display_id:
        candidate_values.append(f"paper/figures/{display_id}.contract.json")

    candidates: list[Path] = []
    seen: set[str] = set()
    for value in candidate_values:
        resolved = _resolve_workspace_path(value, paper_root=paper_root)
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(resolved)
    return candidates


def _load_contract_backed_figure_payloads(
    *,
    paper_root: Path,
    display: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    shell_path = str(display.get("shell_path") or "").strip()
    if not shell_path:
        display_id = str(display.get("display_id") or "").strip()
        raise ValueError(f"contract-backed figure `{display_id}` requires shell_path")
    resolved_shell_path = _resolve_workspace_path(shell_path, paper_root=paper_root)
    if not resolved_shell_path.exists():
        raise ValueError(f"contract-backed figure shell_path does not exist: {shell_path}")
    shell_payload = load_json(resolved_shell_path)

    candidates = _contract_backed_figure_contract_candidates(
        paper_root=paper_root,
        display=display,
        shell_payload=shell_payload,
    )
    for candidate_path in candidates:
        if candidate_path.exists():
            return shell_payload, load_json(candidate_path), candidate_path

    display_id = str(display.get("display_id") or shell_payload.get("display_id") or "").strip()
    candidate_labels = ", ".join(relpath_from_workspace(path, paper_root.parent) for path in candidates) or "none"
    raise ValueError(f"contract-backed figure `{display_id}` source_contract_path does not exist; candidates: {candidate_labels}")


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


def _update_renderer_contracts(
    *,
    path: Path,
    expected_renderer_contracts: dict[str, dict[str, object]],
) -> bool:
    payload = load_json(path)
    figures = payload.get("figures")
    if not isinstance(figures, list):
        raise ValueError(f"{path.name} must contain a figures list")

    remaining_figure_ids = set(expected_renderer_contracts)
    changed = False
    for index, entry in enumerate(figures):
        if not isinstance(entry, dict):
            raise ValueError(f"{path.name} figures[{index}] must be an object")
        figure_id = str(entry.get("figure_id") or "").strip()
        if figure_id not in expected_renderer_contracts:
            continue
        renderer_contract = entry.get("renderer_contract")
        if not isinstance(renderer_contract, dict):
            raise ValueError(f"{path.name} figures[{index}] is missing renderer_contract")
        for field_name, expected_value in expected_renderer_contracts[figure_id].items():
            if renderer_contract.get(field_name) == expected_value:
                continue
            renderer_contract[field_name] = expected_value
            changed = True
        remaining_figure_ids.discard(figure_id)

    if remaining_figure_ids:
        missing_figure_ids = ", ".join(sorted(remaining_figure_ids))
        raise ValueError(f"{path.name} is missing figures for: {missing_figure_ids}")

    if changed:
        dump_json(path, payload)
    return changed


def _renderer_contract_for_evidence_spec(spec) -> dict[str, object]:
    return {
        "figure_semantics": "evidence",
        "renderer_family": spec.renderer_family,
        "template_id": spec.template_id,
        "layout_qc_profile": spec.layout_qc_profile,
        "required_exports": list(spec.required_exports),
        "fallback_on_failure": False,
        "failure_action": "block_and_fix_environment",
    }


def _renderer_contract_for_illustration_spec(spec) -> dict[str, object]:
    return {
        "figure_semantics": "illustration",
        "renderer_family": spec.renderer_family,
        "template_id": spec.shell_id,
        "layout_qc_profile": spec.shell_qc_profile,
        "required_exports": list(spec.required_exports),
        "fallback_on_failure": False,
        "failure_action": "block_and_fix_environment",
    }


def _renderer_contract_for_registry_fields(registry_fields: dict[str, Any]) -> dict[str, object]:
    template_id = str(registry_fields.get("template_id") or "").strip()
    renderer_family = str(registry_fields.get("renderer_family") or "").strip()
    layout_qc_profile = str(registry_fields.get("qc_profile") or "").strip()
    required_exports = registry_fields.get("required_exports")
    if not template_id or not renderer_family or not layout_qc_profile or not isinstance(required_exports, list):
        raise ValueError(f"contract-backed registry fields are incomplete for `{template_id or 'unknown'}`")
    figure_semantics = "illustration" if display_registry.is_illustration_shell(template_id) else "evidence"
    return {
        "figure_semantics": figure_semantics,
        "renderer_family": renderer_family,
        "template_id": template_id,
        "layout_qc_profile": layout_qc_profile,
        "required_exports": list(required_exports),
        "fallback_on_failure": False,
        "failure_action": "block_and_fix_environment",
    }


def _contract_backed_figure_renderer_contract(
    *,
    paper_root: Path,
    display: dict[str, Any],
    catalog_id: str,
) -> tuple[str, dict[str, object]]:
    display_id = str(display.get("display_id") or "").strip()
    shell_payload, contract_payload, _ = _load_contract_backed_figure_payloads(
        paper_root=paper_root,
        display=display,
    )
    figure_id = str(
        contract_payload.get("figure_id")
        or shell_payload.get("catalog_id")
        or catalog_id
        or display_id
        or ""
    ).strip()
    if not display_id or not figure_id:
        raise ValueError("contract-backed figure requires display_id and figure_id/catalog_id")
    registry_fields = resolve_contract_backed_figure_registry_fields(
        paper_root=paper_root,
        item=display,
        shell_payload=shell_payload,
        contract_payload=contract_payload,
        display_id=display_id,
        figure_id=figure_id,
    )
    return figure_id, _renderer_contract_for_registry_fields(registry_fields)


def _resolve_table_requirement_key(
    *,
    paper_root: Path,
    display: dict[str, Any],
    requirement_key: str,
) -> str:
    if display_registry.is_table_shell(requirement_key):
        return requirement_key

    display_id = str(display.get("display_id") or "").strip()
    shell_path = str(display.get("shell_path") or "").strip()
    if not shell_path:
        raise ValueError(f"table display `{display_id}` does not map to a registered table shell")
    resolved_shell_path = _resolve_workspace_path(shell_path, paper_root=paper_root)
    if not resolved_shell_path.exists():
        raise ValueError(f"table display shell_path does not exist: {shell_path}")
    shell_payload = load_json(resolved_shell_path)
    shell_requirement_key = str(shell_payload.get("requirement_key") or "").strip()
    if display_registry.is_table_shell(shell_requirement_key):
        return shell_requirement_key
    raise ValueError(
        f"table display `{display_id}` does not map to a registered table shell; "
        f"registry requirement `{requirement_key}`, shell requirement `{shell_requirement_key or 'missing'}`"
    )


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
    figure_semantics_renderer_contracts: dict[str, dict[str, object]] = {}

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
                figure_semantics_renderer_contracts[catalog_id] = _renderer_contract_for_evidence_spec(spec)
            continue

        if display_kind == "figure" and display_registry.is_illustration_shell(requirement_key):
            spec = display_registry.get_illustration_shell_spec(requirement_key)
            if requirement_key == "cohort_flow_figure":
                cohort_flow_path = resolved_paper_root / "cohort_flow.json"
                if cohort_flow_path.exists():
                    illustration_shell_ids_by_path[cohort_flow_path] = spec.shell_id
            if catalog_id:
                figure_semantics_renderer_contracts[catalog_id] = _renderer_contract_for_illustration_spec(spec)
            continue

        if display_kind == "figure":
            figure_id, renderer_contract = _contract_backed_figure_renderer_contract(
                paper_root=resolved_paper_root,
                display=display,
                catalog_id=catalog_id,
            )
            figure_semantics_renderer_contracts[figure_id] = renderer_contract
            continue

        if display_kind == "table":
            table_requirement_key = _resolve_table_requirement_key(
                paper_root=resolved_paper_root,
                display=display,
                requirement_key=requirement_key,
            )
            spec = display_registry.get_table_shell_spec(table_requirement_key)
            input_filename = TABLE_INPUT_FILENAME_BY_SCHEMA_ID.get(spec.input_schema_id)
            if input_filename is None:
                raise ValueError(
                    f"unsupported table input_schema_id `{spec.input_schema_id}` for `{table_requirement_key}`"
                )
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
    if figure_semantics_path.exists() and figure_semantics_renderer_contracts:
        if _update_renderer_contracts(
            path=figure_semantics_path,
            expected_renderer_contracts=figure_semantics_renderer_contracts,
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
