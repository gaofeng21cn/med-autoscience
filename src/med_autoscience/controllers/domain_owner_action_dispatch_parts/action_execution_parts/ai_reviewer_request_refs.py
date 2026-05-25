from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def required_refs(request: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        surface: _ref_path(request, surface)
        for surface in (
            "manuscript",
            "evidence_ledger",
            "review_ledger",
            "study_charter",
            "medical_manuscript_blueprint",
            "claim_evidence_map",
            "medical_prose_review",
            "publication_gate_projection",
        )
    }


def optional_refs(request: Mapping[str, Any]) -> dict[str, str | None]:
    return {surface: _ref_path(request, surface) for surface in ("reporting_guideline", "calibration_refs")}


def _ref_path(packet: Mapping[str, Any], surface: str) -> str | None:
    ref = _mapping(_mapping(_mapping(packet.get("input_contract")).get("required_refs")).get(surface))
    return _text(ref.get("path")) or _text(ref.get("ref")) or _text(ref.get("relative_path"))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["optional_refs", "required_refs"]
