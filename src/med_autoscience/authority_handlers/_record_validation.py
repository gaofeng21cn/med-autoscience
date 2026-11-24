"""Shared declarative validation primitives for zero-I/O MAS authority records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Annotated, Any

from jsonschema import Draft202012Validator
from opl_framework.exact_refs import (
    canonical_json_bytes_v1,
    fingerprint_v1,
    normalize_exact_json_object,
    normalize_exact_ref,
    normalize_exact_ref_list,
    normalize_sha256,
    normalize_typed_ref,
    normalize_typed_ref_list,
)
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainValidator,
    StrictBool,
    StrictInt,
    StrictStr,
    TypeAdapter,
    ValidationError,
)

_FIELD_PLACEHOLDER = "__FIELD__"


class RequestShapeError(ValueError):
    """Raised when a host-injected authority request is not exact and typed."""


class StrictRecordModel(BaseModel):
    """Strict, closed-schema Pydantic v2 base model for MAS authority records."""

    model_config = ConfigDict(extra="forbid", strict=True)


def _strip_non_empty(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise RequestShapeError(f"{_FIELD_PLACEHOLDER} must be a non-empty string")
    return stripped


def _ensure_unique_strings(values: list[str]) -> list[str]:
    if len(values) != len(set(values)):
        raise RequestShapeError(f"{_FIELD_PLACEHOLDER} contains duplicates")
    return values


NonEmptyStr = Annotated[StrictStr, AfterValidator(_strip_non_empty)]
NonNegativeInt = Annotated[StrictInt, Field(ge=0)]
PositiveInt = Annotated[StrictInt, Field(ge=1)]

_NON_EMPTY_STR_ADAPTER = TypeAdapter(NonEmptyStr)
_NON_NEGATIVE_INT_ADAPTER = TypeAdapter(NonNegativeInt)
_STRICT_BOOL_ADAPTER = TypeAdapter(StrictBool)
_UNIQUE_NON_EMPTY_STR_LIST_ADAPTER = TypeAdapter(
    Annotated[list[NonEmptyStr], AfterValidator(_ensure_unique_strings)]
)


def _validate_optional_text_value(value: Any) -> str | None:
    if value is None:
        return None
    return text(value, _FIELD_PLACEHOLDER)


def _validate_sha256_value(value: Any) -> str:
    return sha256(value, _FIELD_PLACEHOLDER)


def _validate_optional_sha256_value(value: Any) -> str | None:
    if value is None:
        return None
    return sha256(value, _FIELD_PLACEHOLDER)


def _validate_unique_str_list_value(value: Any) -> list[str]:
    return text_list(value, _FIELD_PLACEHOLDER)


OptionalNonEmptyStr = Annotated[
    str | None, PlainValidator(_validate_optional_text_value)
]
Sha256Text = Annotated[str, PlainValidator(_validate_sha256_value)]
OptionalSha256Text = Annotated[
    str | None, PlainValidator(_validate_optional_sha256_value)
]
UniqueNonEmptyStrList = Annotated[
    list[str], PlainValidator(_validate_unique_str_list_value)
]


def _join_loc(root_field: str, loc: Sequence[str | int]) -> str:
    path = root_field
    for part in loc:
        if isinstance(part, int):
            path = f"{path}[{part}]"
        elif path:
            path = f"{path}.{part}"
        else:
            path = str(part)
    return path


def _format_validation_error(error: ValidationError, root_field: str) -> str:
    errors = error.errors()
    missing_by_parent: dict[tuple[str | int, ...], list[str]] = {}
    extra_by_parent: dict[tuple[str | int, ...], list[str]] = {}
    for err in errors:
        loc = err.get("loc", ())
        if not loc:
            continue
        parent = tuple(loc[:-1])
        leaf = str(loc[-1])
        if err["type"] == "missing":
            missing_by_parent.setdefault(parent, []).append(leaf)
        elif err["type"] == "extra_forbidden":
            extra_by_parent.setdefault(parent, []).append(leaf)

    if missing_by_parent:
        parent = min(missing_by_parent, key=lambda key: (len(key), str(key)))
        parent_path = _join_loc(root_field, parent)
        return f"{parent_path} missing fields: {', '.join(sorted(missing_by_parent[parent]))}"
    if extra_by_parent:
        parent = min(extra_by_parent, key=lambda key: (len(key), str(key)))
        parent_path = _join_loc(root_field, parent)
        return (
            f"{parent_path} contains unsupported fields: "
            f"{', '.join(sorted(extra_by_parent[parent]))}"
        )

    first = errors[0]
    loc = first.get("loc", ())
    full_path = _join_loc(root_field, loc)
    err_type = first["type"]
    ctx = first.get("ctx") or {}

    if err_type == "value_error":
        raw_error = ctx.get("error")
        message = (
            str(raw_error)
            if raw_error is not None
            else str(first.get("msg", "")).removeprefix("Value error, ")
        )
        if _FIELD_PLACEHOLDER in message:
            return message.replace(_FIELD_PLACEHOLDER, full_path)
        return message

    if err_type == "bool_type":
        return f"{full_path} must be boolean"
    if err_type == "string_type":
        return f"{full_path} must be a non-empty string"
    if err_type == "int_type":
        return f"{full_path} must be a non-negative integer"
    if err_type == "greater_than_equal":
        if ctx.get("ge") == 1:
            return f"{full_path} must be positive"
        return f"{full_path} must be a non-negative integer"
    if err_type == "list_type":
        return f"{full_path} must be an array"
    if err_type in {"dict_type", "model_type"}:
        return f"{full_path} must be an object"
    if err_type == "literal_error":
        expected = ctx.get("expected", "")
        return f"{full_path} must be one of: {expected}"
    return f"{full_path}: {first.get('msg', 'invalid value')}"


def validate_record_model[ModelT: StrictRecordModel](
    model_cls: type[ModelT],
    value: Any,
    field: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> ModelT:
    """Validate one mapping against a strict Pydantic v2 record model."""

    payload = mapping(value, field)
    validation_context = {"root_field": field, **(dict(context) if context else {})}
    try:
        return model_cls.model_validate(payload, context=validation_context)
    except ValidationError as error:
        raise RequestShapeError(_format_validation_error(error, field)) from error


def validate_record_dict(
    model_cls: type[StrictRecordModel],
    value: Any,
    field: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one mapping with a strict Pydantic v2 model and return a plain dict."""

    return validate_record_model(model_cls, value, field, context=context).model_dump()


def validate_json_schema(
    value: Any,
    schema: Mapping[str, Any],
    field: str,
) -> dict[str, Any]:
    """Validate one mapping declaratively with JSON Schema Draft 2020-12."""

    payload = mapping(value, field)
    validator = Draft202012Validator(dict(schema))
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda err: (list(err.absolute_path), err.message),
    )
    if errors:
        first = errors[0]
        err_path = _join_loc(field, list(first.absolute_path))
        raise RequestShapeError(f"{err_path}: {first.message}")
    return payload


def exact_ref_field(expected_kind: str) -> Any:
    """Build a Pydantic field type validated by OPL exact-ref normalization."""

    def _validate(value: Any) -> dict[str, Any]:
        return exact_ref(value, _FIELD_PLACEHOLDER, expected_kind)

    return Annotated[dict[str, Any], PlainValidator(_validate)]


def optional_exact_ref_field(expected_kind: str) -> Any:
    """Build an optional Pydantic field type validated by OPL exact-ref normalization."""

    def _validate(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        return exact_ref(value, _FIELD_PLACEHOLDER, expected_kind)

    return Annotated[dict[str, Any] | None, PlainValidator(_validate)]


def typed_ref_field(expected_kind: str) -> Any:
    """Build a Pydantic field type validated by OPL typed-ref normalization."""

    def _validate(value: Any) -> dict[str, str]:
        return typed_ref(value, _FIELD_PLACEHOLDER, expected_kind)

    return Annotated[dict[str, str], PlainValidator(_validate)]


def optional_typed_ref_field(expected_kind: str) -> Any:
    """Build an optional Pydantic field type validated by OPL typed-ref normalization."""

    def _validate(value: Any) -> dict[str, str] | None:
        return optional_typed_ref(value, _FIELD_PLACEHOLDER, expected_kind)

    return Annotated[dict[str, str] | None, PlainValidator(_validate)]


def exact_ref_list_field(
    expected_kind: str,
    *,
    dedupe_size: bool = True,
) -> Any:
    """Build a Pydantic list field validated by OPL exact-ref list normalization."""

    def _validate(value: Any) -> list[dict[str, Any]]:
        return exact_ref_list(
            value,
            _FIELD_PLACEHOLDER,
            expected_kind,
            dedupe_size=dedupe_size,
        )

    return Annotated[list[dict[str, Any]], PlainValidator(_validate)]


def typed_ref_list_field(expected_kind: str) -> Any:
    """Build a Pydantic list field validated by OPL typed-ref list normalization."""

    def _validate(value: Any) -> list[dict[str, str]]:
        return typed_ref_list(value, _FIELD_PLACEHOLDER, expected_kind)

    return Annotated[list[dict[str, str]], PlainValidator(_validate)]


def enum_field(allowed: Iterable[str]) -> Any:
    """Build a Pydantic string field constrained to an explicit enum set."""

    allowed_set = frozenset(allowed)

    def _validate(value: Any) -> str:
        return enum_text(value, _FIELD_PLACEHOLDER, set(allowed_set))

    return Annotated[str, PlainValidator(_validate)]


def exact_str_field(expected: str, *, message: str | None = None) -> Any:
    """Build a Pydantic field matching one exact string constant."""

    def _validate(value: Any) -> str:
        if value != expected:
            detail = (
                message
                if message is not None
                else f"{_FIELD_PLACEHOLDER} must be {expected}"
            )
            raise RequestShapeError(detail)
        return expected

    return Annotated[str, PlainValidator(_validate)]


def exact_int_field(expected: int, *, message: str | None = None) -> Any:
    """Build a Pydantic field matching one exact integer constant (rejecting bool)."""

    def _validate(value: Any) -> int:
        if value != expected or isinstance(value, bool):
            detail = (
                message
                if message is not None
                else f"{_FIELD_PLACEHOLDER} must be integer {expected}"
            )
            raise RequestShapeError(detail)
        return expected

    return Annotated[int, PlainValidator(_validate)]


def mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RequestShapeError(f"{field} must be an object")
    return dict(value)


def sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RequestShapeError(f"{field} must be an array")
    return list(value)


def exact_keys(payload: Mapping[str, Any], allowed: set[str], field: str) -> None:
    missing = sorted(allowed - set(payload))
    unknown = sorted(set(payload) - allowed)
    if missing:
        raise RequestShapeError(f"{field} missing fields: {', '.join(missing)}")
    if unknown:
        raise RequestShapeError(
            f"{field} contains unsupported fields: {', '.join(unknown)}"
        )


def text(value: Any, field: str) -> str:
    try:
        return _NON_EMPTY_STR_ADAPTER.validate_python(value)
    except ValidationError as error:
        raise RequestShapeError(_format_validation_error(error, field)) from error


def optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return text(value, field)


def text_list(value: Any, field: str) -> list[str]:
    items = sequence(value, field)
    try:
        return _UNIQUE_NON_EMPTY_STR_LIST_ADAPTER.validate_python(items)
    except ValidationError as error:
        raise RequestShapeError(_format_validation_error(error, field)) from error


def enum_text(value: Any, field: str, allowed: set[str]) -> str:
    normalized = text(value, field)
    if normalized not in allowed:
        raise RequestShapeError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return normalized


def integer(value: Any, field: str) -> int:
    try:
        return _NON_NEGATIVE_INT_ADAPTER.validate_python(value)
    except ValidationError as error:
        raise RequestShapeError(_format_validation_error(error, field)) from error


def boolean(value: Any, field: str) -> bool:
    try:
        return _STRICT_BOOL_ADAPTER.validate_python(value)
    except ValidationError as error:
        raise RequestShapeError(_format_validation_error(error, field)) from error


def sha256(value: Any, field: str) -> str:
    return normalize_sha256(value, field, error_type=RequestShapeError)


def optional_sha256(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return sha256(value, field)


def exact_json_object(
    *,
    encoded_value: Any,
    byte_size_value: Any,
    expected_sha256: str,
    supplied_record: Any,
    field: str,
) -> tuple[str, int, dict[str, Any]]:
    return normalize_exact_json_object(
        encoded_value=encoded_value,
        byte_size_value=byte_size_value,
        expected_sha256=expected_sha256,
        supplied_record=supplied_record,
        field=field,
        error_type=RequestShapeError,
    )


def typed_ref(value: Any, field: str, expected_kind: str) -> dict[str, str]:
    return normalize_typed_ref(
        value,
        field,
        expected_kind,
        error_type=RequestShapeError,
    )


def exact_ref(value: Any, field: str, expected_kind: str) -> dict[str, Any]:
    return normalize_exact_ref(
        value,
        field,
        expected_kind,
        error_type=RequestShapeError,
    )


def optional_typed_ref(
    value: Any,
    field: str,
    expected_kind: str,
) -> dict[str, str] | None:
    if value is None:
        return None
    return typed_ref(value, field, expected_kind)


def typed_ref_list(
    value: Any,
    field: str,
    expected_kind: str,
) -> list[dict[str, str]]:
    return normalize_typed_ref_list(
        value,
        field,
        expected_kind,
        error_type=RequestShapeError,
    )


def exact_ref_list(
    value: Any,
    field: str,
    expected_kind: str,
    *,
    dedupe_size: bool = True,
) -> list[dict[str, Any]]:
    return normalize_exact_ref_list(
        value,
        field,
        expected_kind,
        dedupe_size=dedupe_size,
        error_type=RequestShapeError,
    )


def dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes_v1(payload)


def fingerprint(payload: Mapping[str, Any]) -> str:
    return fingerprint_v1(payload)


__all__ = [
    "NonEmptyStr",
    "NonNegativeInt",
    "OptionalNonEmptyStr",
    "OptionalSha256Text",
    "PositiveInt",
    "RequestShapeError",
    "Sha256Text",
    "StrictRecordModel",
    "UniqueNonEmptyStrList",
    "boolean",
    "canonical_json_bytes",
    "dedupe",
    "enum_field",
    "enum_text",
    "exact_int_field",
    "exact_json_object",
    "exact_keys",
    "exact_ref",
    "exact_ref_field",
    "exact_ref_list",
    "exact_ref_list_field",
    "exact_str_field",
    "fingerprint",
    "integer",
    "mapping",
    "optional_exact_ref_field",
    "optional_sha256",
    "optional_text",
    "optional_typed_ref",
    "optional_typed_ref_field",
    "sequence",
    "sha256",
    "text",
    "text_list",
    "typed_ref",
    "typed_ref_field",
    "typed_ref_list",
    "typed_ref_list_field",
    "validate_json_schema",
    "validate_record_dict",
    "validate_record_model",
]
