from __future__ import annotations

from med_autoscience import display_registry


def _short_id(template_id: str) -> str:
    return str(template_id).rsplit("::", 1)[-1]


def _current_evidence_template_ids(*, include_extended_evidence: bool) -> tuple[str, ...]:
    registered_specs = display_registry.list_evidence_figure_specs()
    registered_by_id = {spec.template_id: spec for spec in registered_specs}
    missing_base_owners = [
        template_id
        for template_id in display_registry._EVIDENCE_TEMPLATE_ORDER
        if template_id not in registered_by_id
    ]
    if missing_base_owners:
        raise AssertionError(f"base evidence template owners are missing: {missing_base_owners}")

    base_owner_ids = set(display_registry._EVIDENCE_TEMPLATE_ORDER)
    template_ids = tuple(
        _short_id(spec.template_id)
        for spec in registered_specs
        if spec.template_id in base_owner_ids
    )
    return template_ids if include_extended_evidence else template_ids[:5]


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
