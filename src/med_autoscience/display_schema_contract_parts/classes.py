from __future__ import annotations

from med_autoscience import display_registry

from .core import DisplaySchemaClass, _input_schema_ids_for_evidence_class, _template_ids_for_evidence_class


def _schema_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    return _input_schema_ids_for_evidence_class(evidence_class)


def _publication_shell_and_table_template_ids() -> tuple[str, ...]:
    return tuple(
        [
            item.template_id
            for item in display_registry.list_evidence_figure_specs()
            if item.evidence_class == "publication_shells_and_tables"
        ]
        + [item.shell_id for item in display_registry.list_illustration_shell_specs()]
        + [item.shell_id for item in display_registry.list_table_shell_specs()]
    )


def _publication_shell_and_table_schema_ids() -> tuple[str, ...]:
    schema_ids: list[str] = []
    seen: set[str] = set()
    for schema_id in (
        [
            item.input_schema_id
            for item in display_registry.list_evidence_figure_specs()
            if item.evidence_class == "publication_shells_and_tables"
        ]
        + [item.input_schema_id for item in display_registry.list_illustration_shell_specs()]
        + [item.input_schema_id for item in display_registry.list_table_shell_specs()]
    ):
        if schema_id in seen:
            continue
        seen.add(schema_id)
        schema_ids.append(schema_id)
    return tuple(schema_ids)

_DISPLAY_SCHEMA_CLASSES: tuple[DisplaySchemaClass, ...] = (
    DisplaySchemaClass(
        class_id="prediction_performance",
        display_name="Prediction Performance",
        template_ids=_template_ids_for_evidence_class("prediction_performance"),
        input_schema_ids=_schema_ids_for_evidence_class("prediction_performance"),
    ),
    DisplaySchemaClass(
        class_id="clinical_utility",
        display_name="Clinical Utility",
        template_ids=_template_ids_for_evidence_class("clinical_utility"),
        input_schema_ids=_schema_ids_for_evidence_class("clinical_utility"),
    ),
    DisplaySchemaClass(
        class_id="time_to_event",
        display_name="Time-to-Event",
        template_ids=_template_ids_for_evidence_class("time_to_event"),
        input_schema_ids=_schema_ids_for_evidence_class("time_to_event"),
    ),
    DisplaySchemaClass(
        class_id="data_geometry",
        display_name="Data Geometry",
        template_ids=_template_ids_for_evidence_class("data_geometry"),
        input_schema_ids=_schema_ids_for_evidence_class("data_geometry"),
    ),
    DisplaySchemaClass(
        class_id="matrix_pattern",
        display_name="Matrix Pattern",
        template_ids=_template_ids_for_evidence_class("matrix_pattern"),
        input_schema_ids=_schema_ids_for_evidence_class("matrix_pattern"),
    ),
    DisplaySchemaClass(
        class_id="effect_estimate",
        display_name="Effect Estimate",
        template_ids=_template_ids_for_evidence_class("effect_estimate"),
        input_schema_ids=_schema_ids_for_evidence_class("effect_estimate"),
    ),
    DisplaySchemaClass(
        class_id="model_explanation",
        display_name="Model Explanation",
        template_ids=_template_ids_for_evidence_class("model_explanation"),
        input_schema_ids=_schema_ids_for_evidence_class("model_explanation"),
    ),
    DisplaySchemaClass(
        class_id="model_audit",
        display_name="Model Audit",
        template_ids=_template_ids_for_evidence_class("model_audit"),
        input_schema_ids=_schema_ids_for_evidence_class("model_audit"),
    ),
    DisplaySchemaClass(
        class_id="generalizability",
        display_name="Generalizability",
        template_ids=_template_ids_for_evidence_class("generalizability"),
        input_schema_ids=_schema_ids_for_evidence_class("generalizability"),
    ),
    DisplaySchemaClass(
        class_id="publication_shells_and_tables",
        display_name="Publication Shells and Tables",
        template_ids=_publication_shell_and_table_template_ids(),
        input_schema_ids=_publication_shell_and_table_schema_ids(),
    ),
)
