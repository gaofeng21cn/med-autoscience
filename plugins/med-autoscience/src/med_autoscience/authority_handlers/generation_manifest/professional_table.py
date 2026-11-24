"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)



def _normalize_table_quality_application(
    value: Any,
    field: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "schema_version",
            "policy_ref",
            "template_policy",
            "coverage_status",
            "main_tables",
        },
        field,
    )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("policy_ref") != (
        "medical-table-design#main-table-information-budget"
    ):
        raise RequestShapeError(f"{field}.policy_ref is invalid")
    if payload.get("template_policy") != "reference_floor_not_required":
        raise RequestShapeError(
            f"{field}.template_policy must be reference_floor_not_required"
        )
    if payload.get("coverage_status") != "all_main_tables_assessed":
        raise RequestShapeError(
            f"{field}.coverage_status must be all_main_tables_assessed"
        )
    main_tables = [
        _normalize_main_table_quality_assessment(
            item,
            f"{field}.main_tables[{index}]",
        )
        for index, item in enumerate(sequence(payload.get("main_tables"), f"{field}.main_tables"))
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
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "table_id",
            "role",
            "reader_question",
            "row_count",
            "column_count",
            "body_word_count",
            "max_cell_word_count",
            "footnote_word_count",
            "supplementary_detail_refs",
            "budget_status",
            "exception_reason",
            "final_embedding_status",
            "final_embedding_page_span",
            "standalone_notes_heading_present",
        },
        field,
    )
    budget_status = enum_text(
        payload.get("budget_status"),
        f"{field}.budget_status",
        {"within_default_budget", "documented_exception"},
    )
    exception_reason = payload.get("exception_reason")
    if budget_status == "documented_exception":
        exception_reason = text(exception_reason, f"{field}.exception_reason")
    elif exception_reason is not None:
        raise RequestShapeError(
            f"{field}.exception_reason is allowed only for documented_exception"
        )
    if not isinstance(payload.get("standalone_notes_heading_present"), bool):
        raise RequestShapeError(
            f"{field}.standalone_notes_heading_present must be boolean"
        )
    return {
        "table_id": text(payload.get("table_id"), f"{field}.table_id"),
        "role": enum_text(payload.get("role"), f"{field}.role", {"main_text"}),
        "reader_question": text(
            payload.get("reader_question"), f"{field}.reader_question"
        ),
        "row_count": integer(payload.get("row_count"), f"{field}.row_count"),
        "column_count": integer(
            payload.get("column_count"), f"{field}.column_count"
        ),
        "body_word_count": integer(
            payload.get("body_word_count"), f"{field}.body_word_count"
        ),
        "max_cell_word_count": integer(
            payload.get("max_cell_word_count"), f"{field}.max_cell_word_count"
        ),
        "footnote_word_count": integer(
            payload.get("footnote_word_count"), f"{field}.footnote_word_count"
        ),
        "supplementary_detail_refs": text_list(
            payload.get("supplementary_detail_refs"),
            f"{field}.supplementary_detail_refs",
        ),
        "budget_status": budget_status,
        "exception_reason": exception_reason,
        "final_embedding_status": enum_text(
            payload.get("final_embedding_status"),
            f"{field}.final_embedding_status",
            {"pending", "passed"},
        ),
        "final_embedding_page_span": integer(
            payload.get("final_embedding_page_span"),
            f"{field}.final_embedding_page_span",
        ),
        "standalone_notes_heading_present": payload[
            "standalone_notes_heading_present"
        ],
    }
