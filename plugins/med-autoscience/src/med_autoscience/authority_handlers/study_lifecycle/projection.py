"""Normalize closed study lifecycle projection inventory inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_json_object,
    exact_keys,
    mapping,
    sequence,
    text_list,
)
from .constants import (
    _OPTIONAL_TARGET_ROLES,
    _REQUIRED_TARGET_ROLES,
    _TARGET_ROLE_ORDER,
)
from .primitives import (
    _digest_text,
    _file_ref,
    _json_fingerprint,
    _relative_path,
)


def _normalize_projection_inventory(value: Any, *, study_id: str) -> dict[str, Any]:
    field = "projection_inventory"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"discovery_complete", "targets", "absent_optional_projection_ids"},
        field,
    )
    if payload.get("discovery_complete") is not True:
        raise RequestShapeError(f"{field}.discovery_complete must be true")
    targets = [
        _normalize_projection_target(item, f"{field}.targets[{index}]", study_id=study_id)
        for index, item in enumerate(sequence(payload.get("targets"), f"{field}.targets"))
    ]
    roles = [item["role"] for item in targets]
    if len(roles) != len(set(roles)):
        raise RequestShapeError(f"{field}.targets contains duplicate roles")
    expected_order = [role for role in _TARGET_ROLE_ORDER if role in set(roles)]
    if roles != expected_order:
        raise RequestShapeError(f"{field}.targets must follow declared projection order")
    missing = sorted(_REQUIRED_TARGET_ROLES - set(roles))
    if missing:
        raise RequestShapeError(f"{field}.targets missing required roles: {', '.join(missing)}")
    absent = text_list(
        payload.get("absent_optional_projection_ids"),
        f"{field}.absent_optional_projection_ids",
    )
    unknown_absent = sorted(set(absent) - _OPTIONAL_TARGET_ROLES)
    if unknown_absent:
        raise RequestShapeError(
            f"{field}.absent_optional_projection_ids contains unsupported roles: {', '.join(unknown_absent)}"
        )
    present_optional = set(roles) & _OPTIONAL_TARGET_ROLES
    if present_optional & set(absent):
        raise RequestShapeError(f"{field} optional role cannot be both present and absent")
    if present_optional | set(absent) != _OPTIONAL_TARGET_ROLES:
        raise RequestShapeError(f"{field} must account for every optional role")
    return {
        "discovery_complete": True,
        "targets": targets,
        "absent_optional_projection_ids": sorted(absent),
        "inventory_fingerprint": _json_fingerprint(
            {"targets": targets, "absent_optional_projection_ids": sorted(absent)}
        ),
    }


def _normalize_projection_target(value: Any, field: str, *, study_id: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "projection_id",
            "root",
            "relative_path",
            "ref",
            "sha256",
            "bytes_base64",
            "byte_size",
            "record",
        },
        field,
    )
    role = enum_text(
        payload.get("projection_id"),
        f"{field}.projection_id",
        _REQUIRED_TARGET_ROLES | _OPTIONAL_TARGET_ROLES,
    )
    root = enum_text(payload.get("root"), f"{field}.root", {"workspace", "work_item"})
    source_relative_path = _relative_path(
        payload.get("relative_path"), f"{field}.relative_path"
    )
    target_relative_path = (
        source_relative_path
        if root == "workspace"
        else f"studies/{study_id}/{source_relative_path}"
    )
    current_sha256 = _digest_text(payload.get("sha256"), f"{field}.sha256")
    current_bytes_base64, current_byte_size, current_payload = (
        exact_json_object(
            encoded_value=payload.get("bytes_base64"),
            byte_size_value=payload.get("byte_size"),
            expected_sha256=current_sha256,
            supplied_record=payload.get("record"),
            field=field,
        )
    )
    return {
        "role": role,
        "root": root,
        "source_relative_path": source_relative_path,
        "relative_path": target_relative_path,
        "current_ref": _file_ref(payload.get("ref"), f"{field}.ref"),
        "current_sha256": current_sha256,
        "current_bytes_base64": current_bytes_base64,
        "current_byte_size": current_byte_size,
        "current_payload": current_payload,
    }


def _validate_target_paths(study_id: str, targets: Mapping[str, Mapping[str, Any]]) -> None:
    for role, target in targets.items():
        if target["relative_path"] != _projection_target_path(role, study_id):
            raise RequestShapeError(f"projection target path does not match role {role}")


def _projection_target_path(role: str, study_id: str) -> str:
    expected = {
        "study_lifecycle_current": f"studies/{study_id}/control/lifecycle.json",
        "workspace_lifecycle_latest": "runtime/artifacts/study_lifecycle_control/latest.json",
        "workspace_index": "workspace_index.json",
        "submission_status": f"studies/{study_id}/submission/STATUS.json",
        "publication_current_package_status": (
            f"studies/{study_id}/publication/current_package/STATUS.json"
        ),
        "stage_index": f"studies/{study_id}/control/stage_index.json",
        "workspace_latest_status": "reports/latest_status.json",
        "workspace_studies_index": "reports/studies_index.json",
    }
    return expected[role]
