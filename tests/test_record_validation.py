from __future__ import annotations

import pytest
from pydantic import StrictBool

from med_autoscience.authority_handlers._record_validation import (
    NonEmptyStr,
    NonNegativeInt,
    PositiveInt,
    RequestShapeError,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    boolean,
    enum_field,
    exact_int_field,
    exact_str_field,
    integer,
    text,
    text_list,
    validate_json_schema,
    validate_record_dict,
)


class _SampleRecord(StrictRecordModel):
    kind: exact_str_field("sample_record")
    schema_version: exact_int_field(2)
    name: NonEmptyStr
    count: NonNegativeInt
    generation: PositiveInt
    enabled: StrictBool
    status: enum_field({"ready", "blocked"})
    tags: UniqueNonEmptyStrList


def test_strict_record_model_validates_and_normalizes_exact_payload() -> None:
    normalized = validate_record_dict(
        _SampleRecord,
        {
            "kind": "sample_record",
            "schema_version": 2,
            "name": "  study-alpha  ",
            "count": 0,
            "generation": 1,
            "enabled": True,
            "status": "ready",
            "tags": ["  primary ", "cohort"],
        },
        "sample",
    )
    assert normalized == {
        "kind": "sample_record",
        "schema_version": 2,
        "name": "study-alpha",
        "count": 0,
        "generation": 1,
        "enabled": True,
        "status": "ready",
        "tags": ["primary", "cohort"],
    }


def test_strict_record_model_enforces_closed_keys_and_strict_types() -> None:
    valid = {
        "kind": "sample_record",
        "schema_version": 2,
        "name": "study-alpha",
        "count": 1,
        "generation": 1,
        "enabled": False,
        "status": "blocked",
        "tags": ["a"],
    }

    missing = dict(valid)
    del missing["name"]
    with pytest.raises(RequestShapeError, match="sample missing fields: name"):
        validate_record_dict(_SampleRecord, missing, "sample")

    extra = {**valid, "unexpected": 1}
    with pytest.raises(
        RequestShapeError, match="sample contains unsupported fields: unexpected"
    ):
        validate_record_dict(_SampleRecord, extra, "sample")

    with pytest.raises(
        RequestShapeError, match="sample.count must be a non-negative integer"
    ):
        validate_record_dict(_SampleRecord, {**valid, "count": True}, "sample")

    with pytest.raises(
        RequestShapeError, match="sample.schema_version must be integer 2"
    ):
        validate_record_dict(_SampleRecord, {**valid, "schema_version": True}, "sample")

    with pytest.raises(RequestShapeError, match="sample.enabled must be boolean"):
        validate_record_dict(_SampleRecord, {**valid, "enabled": 1}, "sample")

    with pytest.raises(RequestShapeError, match="sample.tags contains duplicates"):
        validate_record_dict(_SampleRecord, {**valid, "tags": ["x", "x"]}, "sample")


def test_declarative_json_schema_and_primitive_helpers() -> None:
    schema = {
        "type": "object",
        "required": ["study_id", "count"],
        "additionalProperties": False,
        "properties": {
            "study_id": {"type": "string", "minLength": 1},
            "count": {"type": "integer", "minimum": 0},
        },
    }
    assert validate_json_schema({"study_id": "s1", "count": 2}, schema, "payload") == {
        "study_id": "s1",
        "count": 2,
    }
    with pytest.raises(RequestShapeError, match="payload"):
        validate_json_schema({"study_id": "s1", "count": -1}, schema, "payload")

    assert text("  ok  ", "f") == "ok"
    assert integer(0, "n") == 0
    assert boolean(False, "flag") is False
    assert text_list(("a", "b"), "items") == ["a", "b"]
    with pytest.raises(RequestShapeError, match="n must be a non-negative integer"):
        integer(True, "n")
    with pytest.raises(RequestShapeError, match="flag must be boolean"):
        boolean(0, "flag")
