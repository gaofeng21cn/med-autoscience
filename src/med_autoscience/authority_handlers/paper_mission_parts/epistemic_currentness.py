"""Epistemic review currentness evaluation normalizers."""

from __future__ import annotations

from typing import Any

from .._generation_manifest import EPISTEMIC_AUTHORITY_BOUNDARY
from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_keys,
    mapping,
    optional_sha256,
    sequence,
    text,
    text_list,
)
from .constants import _EPISTEMIC_CHANGE_CLASSES, _EPISTEMIC_IGNORED_REASONS

def _normalize_epistemic_currentness(
    value: Any,
    field: str,
    *,
    lane: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "version",
            "scope_id",
            "scope_kind",
            "status",
            "invalidating_changes",
            "ignored_changes",
            "reviewed_dependency_refs",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "opl_epistemic_review_currentness_evaluation":
        raise RequestShapeError(
            f"{field}.surface_kind must be opl_epistemic_review_currentness_evaluation"
        )
    if payload.get("version") != "opl-epistemic-review-currentness-evaluation.v2":
        raise RequestShapeError(
            f"{field}.version must be opl-epistemic-review-currentness-evaluation.v2"
        )
    scope_id = text(payload.get("scope_id"), f"{field}.scope_id")
    if scope_id != f"mas:{lane}":
        raise RequestShapeError(f"{field}.scope_id must be mas:{lane}")
    status = enum_text(
        payload.get("status"), f"{field}.status", {"current", "stale"}
    )
    invalidating = [
        _normalize_epistemic_change(item, f"{field}.invalidating_changes[{index}]")
        for index, item in enumerate(
            sequence(payload.get("invalidating_changes"), f"{field}.invalidating_changes")
        )
    ]
    ignored = [
        _normalize_epistemic_change(
            item,
            f"{field}.ignored_changes[{index}]",
            ignored=True,
        )
        for index, item in enumerate(
            sequence(payload.get("ignored_changes"), f"{field}.ignored_changes")
        )
    ]
    if (status == "current" and invalidating) or (
        status == "stale" and not invalidating
    ):
        raise RequestShapeError(
            f"{field}.status must agree with invalidating_changes"
        )
    dependency_refs = text_list(
        payload.get("reviewed_dependency_refs"),
        f"{field}.reviewed_dependency_refs",
    )
    if not dependency_refs or dependency_refs != sorted(set(dependency_refs)):
        raise RequestShapeError(
            f"{field}.reviewed_dependency_refs must be sorted and unique"
        )
    authority = mapping(payload.get("authority_boundary"), f"{field}.authority_boundary")
    exact_keys(
        authority,
        set(EPISTEMIC_AUTHORITY_BOUNDARY),
        f"{field}.authority_boundary",
    )
    if authority != EPISTEMIC_AUTHORITY_BOUNDARY:
        raise RequestShapeError(
            f"{field}.authority_boundary must preserve the OPL/MAS authority split"
        )
    return {
        "surface_kind": "opl_epistemic_review_currentness_evaluation",
        "version": "opl-epistemic-review-currentness-evaluation.v2",
        "scope_id": scope_id,
        "scope_kind": enum_text(
            payload.get("scope_kind"),
            f"{field}.scope_kind",
            {"content", "reference", "display", "package"},
        ),
        "status": status,
        "invalidating_changes": invalidating,
        "ignored_changes": ignored,
        "reviewed_dependency_refs": dependency_refs,
        "authority_boundary": dict(EPISTEMIC_AUTHORITY_BOUNDARY),
    }


def _normalize_epistemic_change(
    value: Any,
    field: str,
    *,
    ignored: bool = False,
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {
        "node_ref",
        "change_class",
        "semantic_changed",
        "locator_sha256_before",
        "locator_sha256_after",
    }
    if ignored:
        keys.add("reason")
    exact_keys(payload, keys, field)
    if not isinstance(payload.get("semantic_changed"), bool):
        raise RequestShapeError(f"{field}.semantic_changed must be boolean")
    if not ignored and payload["semantic_changed"] is not True:
        raise RequestShapeError(
            f"{field}.semantic_changed must be true for an invalidating change"
        )
    normalized = {
        "node_ref": text(payload.get("node_ref"), f"{field}.node_ref"),
        "change_class": enum_text(
            payload.get("change_class"),
            f"{field}.change_class",
            _EPISTEMIC_CHANGE_CLASSES,
        ),
        "semantic_changed": payload["semantic_changed"],
        "locator_sha256_before": optional_sha256(
            payload.get("locator_sha256_before"),
            f"{field}.locator_sha256_before",
        ),
        "locator_sha256_after": optional_sha256(
            payload.get("locator_sha256_after"),
            f"{field}.locator_sha256_after",
        ),
    }
    if ignored:
        normalized["reason"] = enum_text(
            payload.get("reason"),
            f"{field}.reason",
            _EPISTEMIC_IGNORED_REASONS,
        )
    return normalized

