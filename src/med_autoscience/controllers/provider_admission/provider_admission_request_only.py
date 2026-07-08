from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.provider_admission.provider_admission_current_control_actions import (
    OWNER_CALLABLE_ADAPTERS,
    PAPER_PROGRESS_TRANSITION_REQUESTS,
)
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)
from med_autoscience.controllers.provider_admission.provider_admission_identity import (
    matches_current_action_without_fingerprint as _matches_current_action_without_fingerprint,
)


def first_present_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
        for item in _text_items(value):
            return item
    return None


def request_only_transition_stage_packet_ref(
    *,
    action: Mapping[str, Any],
    current_action_identity: Mapping[str, Any],
    study_id: str,
    work_unit_id: str,
) -> str:
    return (
        _non_empty_text(action.get("stage_packet_ref"))
        or _non_empty_text(current_action_identity.get("stage_packet_ref"))
        or f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
    )


def request_only_transition_dispatch_path(
    action: Mapping[str, Any],
    *,
    study_root: Path,
    action_type: str,
) -> Path | None:
    refs = _mapping(action.get("refs"))
    for ref in (
        _non_empty_text(action.get("dispatch_path")),
        _non_empty_text(action.get("transition_request_ref")),
        _non_empty_text(refs.get("transition_request_ref")),
        _non_empty_text(refs.get("dispatch_path")),
        _non_empty_text(refs.get("immutable_dispatch_path")),
    ):
        if ref is None:
            continue
        path = _resolve_dispatch_ref(ref, study_root=study_root)
        if path.exists():
            return path
    root = Path(study_root).expanduser().resolve()
    for relative_root in (
        OWNER_CALLABLE_ADAPTERS,
        PAPER_PROGRESS_TRANSITION_REQUESTS,
    ):
        candidate = root / relative_root / f"{action_type}.json"
        if candidate.exists():
            return candidate
    return None


def request_only_transition_stage_packet_refs(
    *,
    action: Mapping[str, Any],
    current_action_identity: Mapping[str, Any],
    stage_packet_ref: str,
) -> list[str]:
    refs: list[str] = []
    for ref in (
        stage_packet_ref,
        *_text_items(action.get("stage_packet_refs")),
        *_text_items(current_action_identity.get("stage_packet_refs")),
    ):
        if ref is not None and ref not in refs:
            refs.append(ref)
    return refs


def current_identity_fingerprint_for_action(
    *,
    action_type: str,
    work_unit_id: str,
    current_action_identity: Mapping[str, Any],
) -> str | None:
    if not _matches_current_action_without_fingerprint(
        action_type=action_type,
        work_unit_id=work_unit_id,
        current_action_identity=current_action_identity,
    ):
        return None
    return _non_empty_text(current_action_identity.get("work_unit_fingerprint"))


def _resolve_dispatch_ref(ref: str, *, study_root: Path) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    root = Path(study_root).expanduser().resolve()
    study_id = root.name
    if len(path.parts) >= 2 and path.parts[:2] == ("studies", study_id):
        return (root.parent.parent / path).resolve()
    return (root / path).resolve()


__all__ = [
    "current_identity_fingerprint_for_action",
    "first_present_text",
    "request_only_transition_dispatch_path",
    "request_only_transition_stage_packet_ref",
    "request_only_transition_stage_packet_refs",
]
