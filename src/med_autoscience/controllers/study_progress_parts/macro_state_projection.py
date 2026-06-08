from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import opl_runtime_refs, study_macro_state


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
    if direct is not None and not _direct_live_state_is_opl_attempt_routeback(payload, direct):
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


def _direct_live_state_is_opl_attempt_routeback(
    payload: Mapping[str, Any],
    direct: Mapping[str, Any],
) -> bool:
    if _text(direct.get("writer_state")) != "live":
        return False
    if opl_runtime_refs.strict_live(payload):
        return False
    transition = _mapping(payload.get("domain_transition"))
    if _text(transition.get("decision_type")) not in {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }:
        return False
    active_run_id = (
        _text(payload.get("active_run_id"))
        or _text(_mapping(payload.get("supervision")).get("active_run_id"))
        or _text(_mapping(payload.get("continuation_state")).get("active_run_id"))
        or _text(_mapping(payload.get("study_truth_snapshot")).get("active_run_id"))
        or _text(
            _mapping(_mapping(payload.get("study_truth_snapshot")).get("execution_owner")).get(
                "active_run_id"
            )
        )
    )
    return bool(active_run_id and active_run_id.startswith("opl-stage-attempt://"))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
