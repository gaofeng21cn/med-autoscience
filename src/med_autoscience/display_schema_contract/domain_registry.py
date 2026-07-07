from __future__ import annotations

from med_autoscience import display_registry


def input_schema_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    schema_ids: list[str] = []
    seen: set[str] = set()
    for spec in display_registry.list_evidence_figure_specs():
        if spec.evidence_class != evidence_class:
            continue
        if spec.input_schema_id in seen:
            continue
        seen.add(spec.input_schema_id)
        schema_ids.append(spec.input_schema_id)
    return tuple(schema_ids)


def template_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    return tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.evidence_class == evidence_class
    )


def template_ids_for_input_schema(input_schema_id: str) -> tuple[str, ...]:
    evidence_template_ids = tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.input_schema_id == input_schema_id
    )
    illustration_shell_ids = tuple(
        spec.shell_id
        for spec in display_registry.list_illustration_shell_specs()
        if spec.input_schema_id == input_schema_id
    )
    table_shell_ids = tuple(
        spec.shell_id
        for spec in display_registry.list_table_shell_specs()
        if spec.input_schema_id == input_schema_id
    )
    return evidence_template_ids + illustration_shell_ids + table_shell_ids
