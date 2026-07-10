from __future__ import annotations

_REPRESENTATIVE_EVIDENCE_TEMPLATE_IDS = (
    "roc_curve_binary",
    "pr_curve_binary",
    "calibration_curve_binary",
    "decision_curve_binary",
    "kaplan_meier_grouped",
)


def _current_evidence_template_ids(*, include_extended_evidence: bool) -> tuple[str, ...]:
    if include_extended_evidence:
        return (*_REPRESENTATIVE_EVIDENCE_TEMPLATE_IDS, "generalizability_subgroup_composite_panel")
    return _REPRESENTATIVE_EVIDENCE_TEMPLATE_IDS


def _build_workspace_registry_displays(
    *,
    include_evidence: bool,
    include_extended_evidence: bool,
) -> list[dict[str, str]]:
    displays = [
        {
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
            "shell_path": "paper/figures/Figure1.shell.json",
        },
        {
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "shell_path": "paper/tables/Table1.shell.json",
        },
    ]
    if include_evidence:
        for figure_index, template_id in enumerate(
            _current_evidence_template_ids(include_extended_evidence=include_extended_evidence),
            start=2,
        ):
            displays.append(
                {
                    "display_id": f"Figure{figure_index}",
                    "display_kind": "figure",
                    "requirement_key": template_id,
                    "shell_path": f"paper/figures/Figure{figure_index}.shell.json",
                }
            )
    return displays


def _workspace_template_bindings(include_extended_evidence: bool) -> list[tuple[int, str]]:
    return list(
        enumerate(
            _current_evidence_template_ids(include_extended_evidence=include_extended_evidence),
            start=2,
        )
    )
