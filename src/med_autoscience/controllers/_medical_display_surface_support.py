from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal

from med_autoscience import display_registry, publication_display_contract


StubKind = Literal["cohort_flow", "table_shell", "display_inputs"]


@dataclass(frozen=True)
class RequiredDisplaySurfaceStub:
    filename: str
    blocker_key: str
    stub_kind: StubKind
    schema_key: str
    schema_value: str
    status: str
    template_id: str | None = None


_REQUIRED_DISPLAY_SURFACE_STUBS: dict[str, RequiredDisplaySurfaceStub] = {
    "cohort_flow_figure": RequiredDisplaySurfaceStub(
        filename="cohort_flow.json",
        blocker_key="missing_cohort_flow",
        stub_kind="cohort_flow",
        schema_key="shell_id",
        schema_value="cohort_flow_figure",
        status="required_pending_population_accounting",
    ),
    "table1_baseline_characteristics": RequiredDisplaySurfaceStub(
        filename="baseline_characteristics_schema.json",
        blocker_key="missing_baseline_characteristics_schema",
        stub_kind="table_shell",
        schema_key="table_shell_id",
        schema_value="table1_baseline_characteristics",
        status="required_pending_table_materialization",
    ),
    "table2_time_to_event_performance_summary": RequiredDisplaySurfaceStub(
        filename="time_to_event_performance_summary.json",
        blocker_key="missing_time_to_event_performance_summary",
        stub_kind="table_shell",
        schema_key="table_shell_id",
        schema_value="table2_time_to_event_performance_summary",
        status="required_pending_table_materialization",
    ),
    "phenotype_gap_structure_figure": RequiredDisplaySurfaceStub(
        filename="stratified_mismatch_matrix_inputs.json",
        blocker_key="missing_stratified_mismatch_matrix_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="stratified_mismatch_matrix_inputs_v1",
        status="required_pending_materialization",
        template_id="phenotype_gap_structure_figure",
    ),
    "table2_phenotype_gap_summary": RequiredDisplaySurfaceStub(
        filename="phenotype_gap_summary_schema.json",
        blocker_key="missing_phenotype_gap_summary_schema",
        stub_kind="table_shell",
        schema_key="table_shell_id",
        schema_value="table2_phenotype_gap_summary",
        status="required_pending_materialization",
    ),
    "site_held_out_stability_figure": RequiredDisplaySurfaceStub(
        filename="transition_support_matrix_inputs.json",
        blocker_key="missing_transition_support_matrix_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="transition_support_matrix_inputs_v1",
        status="required_pending_materialization",
        template_id="site_held_out_stability_figure",
    ),
    "table3_transition_site_support_summary": RequiredDisplaySurfaceStub(
        filename="transition_site_support_summary_schema.json",
        blocker_key="missing_transition_site_support_summary_schema",
        stub_kind="table_shell",
        schema_key="table_shell_id",
        schema_value="table3_transition_site_support_summary",
        status="required_pending_materialization",
    ),
    "treatment_gap_alignment_figure": RequiredDisplaySurfaceStub(
        filename="stratified_mismatch_burden_inputs.json",
        blocker_key="missing_stratified_mismatch_burden_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="stratified_mismatch_burden_inputs_v1",
        status="required_pending_materialization",
        template_id="treatment_gap_alignment_figure",
    ),
    "time_dependent_roc_horizon": RequiredDisplaySurfaceStub(
        filename="binary_prediction_curve_inputs.json",
        blocker_key="missing_binary_prediction_curve_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="binary_prediction_curve_inputs_v1",
        status="required_pending_materialization",
        template_id="time_dependent_roc_horizon",
    ),
    "time_to_event_discrimination_calibration_panel": RequiredDisplaySurfaceStub(
        filename="time_to_event_discrimination_calibration_inputs.json",
        blocker_key="missing_time_to_event_discrimination_calibration_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_discrimination_calibration_inputs_v1",
        status="required_pending_materialization",
        template_id="time_to_event_discrimination_calibration_panel",
    ),
    "risk_layering_monotonic_bars": RequiredDisplaySurfaceStub(
        filename="risk_layering_monotonic_inputs.json",
        blocker_key="missing_risk_layering_monotonic_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="risk_layering_monotonic_inputs_v1",
        status="required_pending_materialization",
        template_id="risk_layering_monotonic_bars",
    ),
    "time_to_event_risk_group_summary": RequiredDisplaySurfaceStub(
        filename="time_to_event_grouped_inputs.json",
        blocker_key="missing_time_to_event_grouped_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_grouped_inputs_v1",
        status="required_pending_materialization",
        template_id="time_to_event_risk_group_summary",
    ),
    "time_to_event_decision_curve": RequiredDisplaySurfaceStub(
        filename="time_to_event_decision_curve_inputs.json",
        blocker_key="missing_time_to_event_decision_curve_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_decision_curve_inputs_v1",
        status="required_pending_materialization",
        template_id="time_to_event_decision_curve",
    ),
    "generalizability_subgroup_composite_panel": RequiredDisplaySurfaceStub(
        filename="generalizability_subgroup_composite_inputs.json",
        blocker_key="missing_generalizability_subgroup_composite_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="generalizability_subgroup_composite_inputs_v1",
        status="required_pending_materialization",
        template_id="generalizability_subgroup_composite_panel",
    ),
    "local_architecture_overview_figure": RequiredDisplaySurfaceStub(
        filename="risk_layering_monotonic_inputs.json",
        blocker_key="missing_local_architecture_overview_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="risk_layering_monotonic_inputs_v1",
        status="required_pending_materialization",
        template_id="risk_layering_monotonic_bars",
    ),
    "model_action_exposure_overview": RequiredDisplaySurfaceStub(
        filename="model_action_exposure_inputs.json",
        blocker_key="missing_model_action_exposure_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="model_action_exposure_inputs_v1",
        status="required_pending_materialization",
        template_id="model_action_exposure_overview",
    ),
    "cross_condition_transition_figure": RequiredDisplaySurfaceStub(
        filename="cross_condition_transition_inputs.json",
        blocker_key="missing_cross_condition_transition_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="cross_condition_transition_inputs_v1",
        status="required_pending_materialization",
        template_id="cross_condition_transition_figure",
    ),
    "sensitivity_uncertainty_figure": RequiredDisplaySurfaceStub(
        filename="sensitivity_uncertainty_inputs.json",
        blocker_key="missing_sensitivity_uncertainty_inputs",
        stub_kind="display_inputs",
        schema_key="input_schema_id",
        schema_value="sensitivity_uncertainty_inputs_v1",
        status="required_pending_materialization",
        template_id="sensitivity_uncertainty_figure",
    ),
    "table1_model_action_exposure_matrix": RequiredDisplaySurfaceStub(
        filename="model_action_exposure_matrix_schema.json",
        blocker_key="missing_model_action_exposure_matrix_schema",
        stub_kind="table_shell",
        schema_key="table_shell_id",
        schema_value="table1_model_action_exposure_matrix",
        status="required_pending_materialization",
    ),
    "table2_cross_condition_transition_summary": RequiredDisplaySurfaceStub(
        filename="cross_condition_transition_summary_schema.json",
        blocker_key="missing_cross_condition_transition_summary_schema",
        stub_kind="table_shell",
        schema_key="table_shell_id",
        schema_value="table2_cross_condition_transition_summary",
        status="required_pending_materialization",
    ),
}


def resolve_required_display_surface_stub(requirement_key: str) -> RequiredDisplaySurfaceStub | None:
    return _REQUIRED_DISPLAY_SURFACE_STUBS.get(requirement_key)


def build_required_display_surface_stub_payload(
    *,
    item: dict[str, str],
    reporting_contract_relpath: str,
) -> tuple[str, dict[str, Any]] | None:
    spec = resolve_required_display_surface_stub(item["requirement_key"])
    if spec is None:
        return None

    payload: dict[str, Any] = {
        "schema_version": 1,
        spec.schema_key: spec.schema_value,
        "source_contract_path": reporting_contract_relpath,
        "status": spec.status,
    }

    if spec.stub_kind == "cohort_flow":
        payload["display_id"] = item["display_id"]
        payload["steps"] = []
        payload["exclusion_branches"] = []
        payload["endpoint_inventory"] = []
        payload["sidecar_blocks"] = []
    elif spec.stub_kind == "table_shell":
        payload["display_id"] = item["display_id"]
        if spec.schema_value == "table1_baseline_characteristics":
            payload["group_columns"] = []
            payload["variables"] = []
        else:
            payload["columns"] = []
            payload["rows"] = []
    else:
        if spec.template_id and display_registry.is_evidence_figure_template(spec.template_id):
            canonical_template_id = display_registry.get_evidence_figure_spec(spec.template_id).template_id
        elif spec.template_id and display_registry.is_illustration_shell(spec.template_id):
            canonical_template_id = display_registry.get_illustration_shell_spec(spec.template_id).shell_id
        elif spec.template_id:
            canonical_template_id = spec.template_id
        else:
            raise ValueError(f"unknown required display surface template `{spec.template_id}`")
        display_payload: dict[str, Any] = {
            "display_id": item["display_id"],
            "template_id": canonical_template_id,
        }
        if item.get("catalog_id"):
            display_payload["catalog_id"] = item["catalog_id"]
        payload["displays"] = [display_payload]

    if item.get("catalog_id") and spec.stub_kind != "display_inputs":
        payload["catalog_id"] = item["catalog_id"]

    return spec.filename, payload


def seed_publication_display_contracts(*, paper_root: Path) -> list[str]:
    return publication_display_contract.seed_publication_display_contracts_if_missing(paper_root=paper_root)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists() and _read_json(path) == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def _is_legacy_display_id(*, display_id: str, display_kind: str) -> bool:
    prefix = "Figure" if display_kind == "figure" else "Table" if display_kind == "table" else ""
    return bool(prefix) and display_id.startswith(prefix) and display_id.removeprefix(prefix).isdigit()


def _display_shell_plan(reporting_contract: dict[str, object]) -> list[dict[str, str]]:
    raw_plan = reporting_contract.get("display_shell_plan")
    if not isinstance(raw_plan, list):
        return []
    plan: list[dict[str, str]] = []
    for raw_item in raw_plan:
        if not isinstance(raw_item, dict):
            raise ValueError("medical_reporting_contract.display_shell_plan must contain mappings")
        item = {
            key: str(raw_item.get(key) or "").strip()
            for key in ("display_id", "display_kind", "requirement_key", "catalog_id")
        }
        if not item["display_id"] or not item["display_kind"] or not item["requirement_key"]:
            raise ValueError(
                "medical_reporting_contract.display_shell_plan items must include display_id, display_kind, requirement_key"
            )
        if resolve_required_display_surface_stub(item["requirement_key"]) is None:
            raise ValueError(
                "medical_reporting_contract.display_shell_plan contains unsupported requirement_key: "
                f"{item['requirement_key']}"
            )
        if not item["catalog_id"] and not _is_legacy_display_id(
            display_id=item["display_id"],
            display_kind=item["display_kind"],
        ):
            raise ValueError("medical_reporting_contract.display_shell_plan semantic display_id items must include catalog_id")
        if not item["catalog_id"]:
            item.pop("catalog_id")
        plan.append(item)
    return plan


def _has_substantive_content(payload: dict[str, Any], *, requirement_key: str) -> bool:
    spec = resolve_required_display_surface_stub(requirement_key)
    if spec is None:
        return False
    if spec.stub_kind == "cohort_flow":
        return bool(payload.get("steps"))
    if spec.stub_kind == "table_shell":
        return any(bool(payload.get(key)) for key in ("groups", "variables", "columns", "rows"))
    displays = payload.get("displays")
    return isinstance(displays, list) and any(
        isinstance(item, dict)
        and any(
            value not in (None, "", [], {}) and key not in {"display_id", "template_id", "catalog_id"}
            for key, value in item.items()
        )
        for item in displays
    )


def _merge_stub(path: Path, *, requirement_key: str, stub: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return stub
    current = _read_json(path)
    if not _has_substantive_content(current, requirement_key=requirement_key):
        return stub
    merged = dict(current)
    spec = resolve_required_display_surface_stub(requirement_key)
    for key in ("schema_version", "source_contract_path", "display_id", "catalog_id"):
        if key in stub:
            merged[key] = stub[key]
    if spec is not None:
        merged[spec.schema_key] = stub[spec.schema_key]
    if spec is not None and spec.stub_kind == "display_inputs":
        existing_displays = current.get("displays")
        stub_displays = stub.get("displays")
        if isinstance(existing_displays, list) and len(existing_displays) == 1 and isinstance(existing_displays[0], dict):
            display = dict(existing_displays[0])
            if isinstance(stub_displays, list) and len(stub_displays) == 1 and isinstance(stub_displays[0], dict):
                display.update(stub_displays[0])
            merged["displays"] = [display]
        else:
            merged["displays"] = stub_displays
    return merged


def materialize_display_contract_surface(
    *,
    paper_root: Path,
    reporting_contract: dict[str, object] | None = None,
) -> dict[str, object]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    contract = (
        dict(reporting_contract)
        if isinstance(reporting_contract, dict)
        else _read_json(resolved_paper_root / "medical_reporting_contract.json")
    )
    plan = _display_shell_plan(contract)
    contract_ref = "paper/medical_reporting_contract.json"
    written_files: list[str] = []
    registry_path = resolved_paper_root / "display_registry.json"
    registry = {
        "schema_version": 1,
        "source_contract_path": contract_ref,
        "displays": [
            {
                **item,
                "shell_path": (
                    f"paper/figures/{item['display_id']}.shell.json"
                    if item["display_kind"] == "figure"
                    else f"paper/tables/{item['display_id']}.shell.json"
                ),
            }
            for item in plan
        ],
    }
    if bool(contract.get("display_registry_required", bool(plan))) and _write_json_if_changed(registry_path, registry):
        written_files.append(str(registry_path))

    for item in plan:
        shell_dir = "figures" if item["display_kind"] == "figure" else "tables"
        shell_path = resolved_paper_root / shell_dir / f"{item['display_id']}.shell.json"
        shell = {
            "schema_version": 1,
            "source_contract_path": contract_ref,
            **item,
        }
        if _write_json_if_changed(shell_path, shell):
            written_files.append(str(shell_path))
        built_stub = build_required_display_surface_stub_payload(item=item, reporting_contract_relpath=contract_ref)
        if built_stub is None:
            continue
        filename, stub = built_stub
        stub_path = resolved_paper_root / filename
        if _write_json_if_changed(
            stub_path,
            _merge_stub(stub_path, requirement_key=item["requirement_key"], stub=stub),
        ):
            written_files.append(str(stub_path))

    written_files.extend(seed_publication_display_contracts(paper_root=resolved_paper_root))
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "reporting_contract_path": str(resolved_paper_root / "medical_reporting_contract.json"),
        "display_registry_path": str(registry_path),
        "written_files": written_files,
    }
