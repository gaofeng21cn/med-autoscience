from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import study_macro_state


MACRO_STATE_KEYS = (
    "surface",
    "schema_version",
    "study_id",
    "writer_state",
    "user_next",
    "reason",
    "details",
    "conditions",
    "source_fingerprint",
)


def compact_study_macro_state_projection(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    compact = {key: value[key] for key in MACRO_STATE_KEYS if key in value}
    return compact or None


def compact_study_macro_state_from_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct = compact_study_macro_state_projection(payload.get("study_macro_state"))
    if direct is not None:
        return direct
    study_id = _text(payload.get("study_id")) or _text(_mapping(payload.get("study_truth_snapshot")).get("study_id"))
    if study_id is None:
        return None
    return compact_study_macro_state_projection(
        study_macro_state.derive_study_macro_state(
            study_id=study_id,
            status=payload,
            progress=payload,
        )
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
