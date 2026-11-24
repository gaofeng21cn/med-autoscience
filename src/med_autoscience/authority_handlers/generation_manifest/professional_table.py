"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from typing import Any

from pydantic import StrictBool, model_validator

from .._record_validation import (
    NonEmptyStr,
    NonNegativeInt,
    OptionalNonEmptyStr,
    RequestShapeError,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    enum_field,
    exact_int_field,
    exact_str_field,
    sequence,
    text,
    validate_record_dict,
    validate_record_model,
)


class _TableQualityApplicationModel(StrictRecordModel):
    schema_version: exact_int_field(1)
    policy_ref: exact_str_field(
        "medical-table-design#main-table-information-budget",
        message="__FIELD__ is invalid",
    )
    template_policy: exact_str_field("reference_floor_not_required")
    coverage_status: exact_str_field("all_main_tables_assessed")
    main_tables: Any


class _MainTableQualityAssessmentModel(StrictRecordModel):
    table_id: NonEmptyStr
    role: enum_field({"main_text"})
    reader_question: NonEmptyStr
    row_count: NonNegativeInt
    column_count: NonNegativeInt
    body_word_count: NonNegativeInt
    max_cell_word_count: NonNegativeInt
    footnote_word_count: NonNegativeInt
    supplementary_detail_refs: UniqueNonEmptyStrList
    budget_status: enum_field({"within_default_budget", "documented_exception"})
    exception_reason: OptionalNonEmptyStr
    final_embedding_status: enum_field({"pending", "passed"})
    final_embedding_page_span: NonNegativeInt
    standalone_notes_heading_present: StrictBool

    @model_validator(mode="after")
    def _validate_exception_reason(self) -> _MainTableQualityAssessmentModel:
        if self.budget_status == "documented_exception":
            self.exception_reason = text(
                self.exception_reason, "__FIELD__.exception_reason"
            )
        elif self.exception_reason is not None:
            raise RequestShapeError(
                "__FIELD__.exception_reason is allowed only for documented_exception"
            )
        return self


def _normalize_table_quality_application(
    value: Any,
    field: str,
) -> dict[str, Any]:
    parsed = validate_record_model(_TableQualityApplicationModel, value, field)
    main_tables = [
        _normalize_main_table_quality_assessment(
            item,
            f"{field}.main_tables[{index}]",
        )
        for index, item in enumerate(
            sequence(parsed.main_tables, f"{field}.main_tables")
        )
    ]
    if not main_tables:
        raise RequestShapeError(f"{field}.main_tables must not be empty")
    table_ids = [item["table_id"] for item in main_tables]
    if len(table_ids) != len(set(table_ids)):
        raise RequestShapeError(f"{field}.main_tables contains duplicate table ids")
    return {
        "schema_version": 1,
        "policy_ref": "medical-table-design#main-table-information-budget",
        "template_policy": "reference_floor_not_required",
        "coverage_status": "all_main_tables_assessed",
        "main_tables": sorted(main_tables, key=lambda item: item["table_id"]),
    }


def _normalize_main_table_quality_assessment(
    value: Any,
    field: str,
) -> dict[str, Any]:
    return validate_record_dict(_MainTableQualityAssessmentModel, value, field)
