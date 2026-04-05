from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from med_autoscience import publication_display_contract


StubKind = Literal["cohort_flow", "table_shell", "evidence_inputs"]


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
        status="required_pending_materialization",
    ),
    "time_to_event_discrimination_calibration_panel": RequiredDisplaySurfaceStub(
        filename="time_to_event_discrimination_calibration_inputs.json",
        blocker_key="missing_time_to_event_discrimination_calibration_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_discrimination_calibration_inputs_v1",
        status="required_pending_materialization",
        template_id="time_to_event_discrimination_calibration_panel",
    ),
    "kaplan_meier_grouped": RequiredDisplaySurfaceStub(
        filename="time_to_event_grouped_inputs.json",
        blocker_key="missing_time_to_event_grouped_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_grouped_inputs_v1",
        status="required_pending_materialization",
        template_id="kaplan_meier_grouped",
    ),
    "time_to_event_decision_curve": RequiredDisplaySurfaceStub(
        filename="time_to_event_decision_curve_inputs.json",
        blocker_key="missing_time_to_event_decision_curve_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_decision_curve_inputs_v1",
        status="required_pending_materialization",
        template_id="time_to_event_decision_curve",
    ),
    "multicenter_generalizability_overview": RequiredDisplaySurfaceStub(
        filename="multicenter_generalizability_inputs.json",
        blocker_key="missing_multicenter_generalizability_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="multicenter_generalizability_inputs_v1",
        status="required_pending_materialization",
        template_id="multicenter_generalizability_overview",
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
        elif spec.schema_value == "table2_time_to_event_performance_summary":
            payload["columns"] = []
            payload["rows"] = []
    else:
        display_payload: dict[str, Any] = {
            "display_id": item["display_id"],
            "template_id": spec.template_id,
        }
        if item.get("catalog_id"):
            display_payload["catalog_id"] = item["catalog_id"]
        payload["displays"] = [display_payload]

    if item.get("catalog_id") and spec.stub_kind != "evidence_inputs":
        payload["catalog_id"] = item["catalog_id"]

    return spec.filename, payload


def seed_publication_display_contracts(*, paper_root: Path) -> list[str]:
    return publication_display_contract.seed_publication_display_contracts_if_missing(paper_root=paper_root)
