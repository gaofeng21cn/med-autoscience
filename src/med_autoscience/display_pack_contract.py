from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


_VALID_TEMPLATE_KINDS = frozenset(("evidence_figure", "illustration_shell", "table_shell"))
_VALID_EXECUTION_MODES = frozenset(("python_plugin", "subprocess"))
_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
_DISPLAY_CLASS_ID_BY_AUDIT_FAMILY = {
    "Prediction Performance": "prediction_performance",
    "Clinical Utility": "clinical_utility",
    "Time-to-Event": "time_to_event",
    "Data Geometry": "data_geometry",
    "Matrix Pattern": "matrix_pattern",
    "Effect Estimate": "effect_estimate",
    "Model Explanation": "model_explanation",
    "Model Audit": "model_audit",
    "Generalizability": "generalizability",
    "Publication Shells and Tables": "publication_shells_and_tables",
}


@dataclass(frozen=True)
class DisplayPackManifest:
    pack_id: str
    version: str
    display_api_version: str
    default_execution_mode: str
    summary: str
    maintainer: str
    license: str
    source: str
    paper_family_coverage: tuple[str, ...]
    recommended_templates: tuple[str, ...]


@dataclass(frozen=True)
class DisplayTemplateManifest:
    template_id: str
    full_template_id: str
    kind: str
    display_name: str
    display_class_id: str
    audit_family: str
    paper_family_ids: tuple[str, ...]
    renderer_family: str
    input_schema_ref: str
    qc_profile_ref: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...]
    execution_mode: str
    entrypoint: str
    paper_proven: bool


def _expect_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _expect_bool(payload: dict[str, object], key: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a bool")
    return value


def _optional_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _expect_str_tuple(payload: dict[str, object], key: str) -> tuple[str, ...]:
    value = payload[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(value)


def _optional_str_tuple(payload: dict[str, object], key: str) -> tuple[str, ...] | None:
    if key not in payload:
        return None
    return _expect_str_tuple(payload, key)


def _expect_semver(payload: dict[str, object], key: str) -> str:
    value = _expect_str(payload, key)
    if not _SEMVER_PATTERN.match(value):
        raise ValueError(f"{key} must use semantic version format")
    return value


def _expect_execution_mode(payload: dict[str, object], key: str) -> str:
    value = _expect_str(payload, key)
    if value not in _VALID_EXECUTION_MODES:
        raise ValueError(f"{key} must be one of {sorted(_VALID_EXECUTION_MODES)!r}")
    return value


def _split_full_template_id(full_template_id: str) -> tuple[str, str]:
    if "::" not in full_template_id:
        raise ValueError("full_template_id must use '<pack_id>::<template_id>'")
    pack_id, template_id = full_template_id.split("::", 1)
    if not pack_id or not template_id:
        raise ValueError("full_template_id must use '<pack_id>::<template_id>'")
    return pack_id, template_id


def load_display_pack_manifest(path: Path) -> DisplayPackManifest:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))

    pack_id = _expect_str(payload, "pack_id")
    if "." not in pack_id:
        raise ValueError("pack_id must be namespaced")

    return DisplayPackManifest(
        pack_id=pack_id,
        version=_expect_semver(payload, "version"),
        display_api_version=_expect_str(payload, "display_api_version"),
        default_execution_mode=_expect_execution_mode(payload, "default_execution_mode"),
        summary=_optional_str(payload, "summary"),
        maintainer=_optional_str(payload, "maintainer"),
        license=_optional_str(payload, "license"),
        source=_optional_str(payload, "source"),
        paper_family_coverage=_optional_str_tuple(payload, "paper_family_coverage") or (),
        recommended_templates=_optional_str_tuple(payload, "recommended_templates") or (),
    )


def load_display_template_manifest(
    path: Path,
    *,
    expected_pack_id: str,
) -> DisplayTemplateManifest:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))

    template_id = _expect_str(payload, "template_id")
    full_template_id = _expect_str(payload, "full_template_id")
    pack_id, short_template_id = _split_full_template_id(full_template_id)
    if pack_id != expected_pack_id:
        raise ValueError(
            f"full_template_id pack namespace mismatch: expected {expected_pack_id!r}, got {pack_id!r}"
        )
    if short_template_id != template_id:
        raise ValueError(
            f"full_template_id template name mismatch: expected {template_id!r}, got {short_template_id!r}"
        )

    kind = _expect_str(payload, "kind")
    if kind not in _VALID_TEMPLATE_KINDS:
        raise ValueError(f"kind must be one of {sorted(_VALID_TEMPLATE_KINDS)!r}")

    audit_family = _expect_str(payload, "audit_family")
    try:
        display_class_id = _DISPLAY_CLASS_ID_BY_AUDIT_FAMILY[audit_family]
    except KeyError as exc:
        raise ValueError(f"audit_family is not recognized: {audit_family!r}") from exc

    allowed_paper_roles = _optional_str_tuple(payload, "allowed_paper_roles")
    if allowed_paper_roles is None:
        if kind == "illustration_shell":
            allowed_paper_roles = ("main_text",)
        else:
            allowed_paper_roles = ("main_text", "supplementary")

    return DisplayTemplateManifest(
        template_id=template_id,
        full_template_id=full_template_id,
        kind=kind,
        display_name=_expect_str(payload, "display_name"),
        display_class_id=display_class_id,
        audit_family=audit_family,
        paper_family_ids=_expect_str_tuple(payload, "paper_family_ids"),
        renderer_family=_expect_str(payload, "renderer_family"),
        input_schema_ref=_expect_str(payload, "input_schema_ref"),
        qc_profile_ref=_expect_str(payload, "qc_profile_ref"),
        required_exports=_expect_str_tuple(payload, "required_exports"),
        allowed_paper_roles=allowed_paper_roles,
        execution_mode=_expect_execution_mode(payload, "execution_mode"),
        entrypoint=_expect_str(payload, "entrypoint"),
        paper_proven=_expect_bool(payload, "paper_proven"),
    )
