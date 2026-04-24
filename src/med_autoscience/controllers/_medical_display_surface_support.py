from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from med_autoscience import display_registry, publication_display_contract


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
    "phenotype_gap_structure_figure": RequiredDisplaySurfaceStub(
        filename="phenotype_gap_structure_inputs.json",
        blocker_key="missing_phenotype_gap_structure_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="phenotype_gap_structure_inputs_v1",
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
        filename="site_held_out_stability_inputs.json",
        blocker_key="missing_site_held_out_stability_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="site_held_out_stability_inputs_v1",
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
        filename="treatment_gap_alignment_inputs.json",
        blocker_key="missing_treatment_gap_alignment_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="treatment_gap_alignment_inputs_v1",
        status="required_pending_materialization",
        template_id="treatment_gap_alignment_figure",
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
    "time_to_event_risk_group_summary": RequiredDisplaySurfaceStub(
        filename="time_to_event_grouped_inputs.json",
        blocker_key="missing_time_to_event_grouped_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="time_to_event_grouped_inputs_v1",
        status="required_pending_materialization",
        template_id="time_to_event_risk_group_summary",
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
    "local_architecture_overview_figure": RequiredDisplaySurfaceStub(
        filename="risk_layering_monotonic_inputs.json",
        blocker_key="missing_local_architecture_overview_inputs",
        stub_kind="evidence_inputs",
        schema_key="input_schema_id",
        schema_value="risk_layering_monotonic_inputs_v1",
        status="required_pending_materialization",
        template_id="risk_layering_monotonic_bars",
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
        canonical_template_id = display_registry.get_evidence_figure_spec(spec.template_id).template_id
        display_payload: dict[str, Any] = {
            "display_id": item["display_id"],
            "template_id": canonical_template_id,
        }
        if item.get("catalog_id"):
            display_payload["catalog_id"] = item["catalog_id"]
        payload["displays"] = [display_payload]

    if item.get("catalog_id") and spec.stub_kind != "evidence_inputs":
        payload["catalog_id"] = item["catalog_id"]

    return spec.filename, payload


def seed_publication_display_contracts(*, paper_root: Path) -> list[str]:
    return publication_display_contract.seed_publication_display_contracts_if_missing(paper_root=paper_root)
