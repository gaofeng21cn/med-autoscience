"""Candidate-admission request normalization and cross-record binding."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import normalize_generation_manifest
from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_keys,
    mapping,
    optional_text,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from .._record_validation import (
    typed_ref_list as _typed_ref_list,
)
from .adjudicator import (
    _normalize_adjudicator_context,
    _normalize_adjudicator_receipt,
    _validate_adjudicator_receipt,
)
from .candidate import (
    _normalize_candidate,
    _normalize_mission,
    _validate_manifest_membership,
)
from .currentness import (
    _normalize_currentness_receipt,
    _validate_currentness_receipt_ref,
)
from .policy import _HARD_GATE_KINDS, REQUEST_KIND, SCHEMA_VERSION


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "adjudicator_context",
            "mission",
            "generation_manifest",
            "generation_manifest_ref",
            "currentness_receipt",
            "candidate",
            "adjudicator_receipt",
            "hard_gate",
        },
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if payload.get("schema_version") != SCHEMA_VERSION or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("schema_version must be integer 2")

    context = _normalize_adjudicator_context(payload.get("adjudicator_context"))
    manifest = normalize_generation_manifest(payload.get("generation_manifest"))
    if manifest["manifest_scope"] != "analysis_generation":
        raise RequestShapeError(
            "candidate admission requires an analysis_generation manifest"
        )
    if manifest["independent_review_receipts"]:
        raise RequestShapeError(
            "candidate admission manifest cannot carry downstream review receipts"
        )
    manifest_ref = _exact_ref(
        payload.get("generation_manifest_ref"),
        "generation_manifest_ref",
        "mas_generation_manifest",
    )
    if (
        manifest_ref["sha256"] != manifest["generation_manifest_sha256"]
        or manifest_ref["size_bytes"] != manifest["generation_manifest_size_bytes"]
    ):
        raise RequestShapeError(
            "generation_manifest_ref size/hash does not match canonical manifest"
        )
    candidate = _normalize_candidate(payload.get("candidate"))
    _validate_manifest_membership(manifest, candidate)
    currentness = _normalize_currentness_receipt(payload.get("currentness_receipt"))
    adjudicator = _normalize_adjudicator_receipt(payload.get("adjudicator_receipt"))

    normalized = {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "adjudicator_context": context,
        "mission": _normalize_mission(payload.get("mission"), "mission"),
        "generation_manifest": manifest,
        "generation_manifest_ref": manifest_ref,
        "currentness_receipt": currentness,
        "candidate": candidate,
        "adjudicator_receipt": adjudicator,
        "hard_gate": _normalize_hard_gate(payload.get("hard_gate")),
    }
    _validate_currentness_receipt_ref(normalized)
    _validate_adjudicator_receipt(normalized)
    return normalized


def _normalize_hard_gate(value: Any) -> dict[str, Any]:
    field = "hard_gate"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"kind", "reason_code", "evidence_refs", "next_owner", "resume_condition"},
        field,
    )
    kind = enum_text(
        payload.get("kind"),
        "hard_gate.kind",
        {"none", "human_decision", *_HARD_GATE_KINDS},
    )
    normalized = {
        "kind": kind,
        "reason_code": optional_text(
            payload.get("reason_code"), "hard_gate.reason_code"
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"), "hard_gate.evidence_refs", "mas_gate_evidence"
        ),
        "next_owner": optional_text(payload.get("next_owner"), "hard_gate.next_owner"),
        "resume_condition": optional_text(
            payload.get("resume_condition"), "hard_gate.resume_condition"
        ),
    }
    if kind == "none":
        if any(
            (
                normalized["reason_code"] is not None,
                bool(normalized["evidence_refs"]),
                normalized["next_owner"] is not None,
                normalized["resume_condition"] is not None,
            )
        ):
            raise RequestShapeError("hard_gate.kind none requires an empty gate record")
        return normalized
    missing = [
        name
        for name in ("reason_code", "next_owner", "resume_condition")
        if normalized[name] is None
    ]
    if not normalized["evidence_refs"]:
        missing.append("evidence_refs")
    if missing:
        raise RequestShapeError("hard gate missing: " + ", ".join(missing))
    return normalized
