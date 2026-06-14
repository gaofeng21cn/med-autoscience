from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.owner_route_handoff_parts import current_dispatch_identity


def matching_provider_admission_identity(
    *,
    candidates: list[Mapping[str, Any]],
    action_type: str,
    work_unit_id: str | None,
    dispatch_path: Path,
    stage_packet_path: Path,
    workspace_root: Path,
) -> dict[str, Any] | None:
    for candidate in candidates:
        if _text(candidate.get("action_type")) != action_type:
            continue
        candidate_work_unit = _text(candidate.get("work_unit_id"))
        if work_unit_id is not None and not current_dispatch_identity.work_unit_ids_equivalent_for_action(
            action_type=action_type,
            left=candidate_work_unit,
            right=work_unit_id,
        ):
            continue
        if not _candidate_dispatch_path_matches(
            candidate_dispatch_path=_text(candidate.get("dispatch_path")),
            dispatch_path=dispatch_path,
            stage_packet_path=stage_packet_path,
            workspace_root=workspace_root,
        ):
            continue
        return dict(candidate)
    return None


def current_provider_admission_supersedes_consumed_receipt(
    *,
    provider_admission_candidates: list[Mapping[str, Any]],
    action_type: str,
    work_unit_id: str | None,
    dispatch_path: Path,
    stage_packet_path: Path,
    workspace_root: Path,
) -> bool:
    identity = matching_provider_admission_identity(
        candidates=provider_admission_candidates,
        action_type=action_type,
        work_unit_id=work_unit_id,
        dispatch_path=dispatch_path,
        stage_packet_path=stage_packet_path,
        workspace_root=workspace_root,
    )
    return (
        bool(identity)
        and _text(identity.get("status")) == "provider_admission_pending"
        and identity.get("provider_attempt_or_lease_required") is True
    )


def provider_admission_payload_fields(
    *,
    provider_admission_identity: Mapping[str, Any] | None,
    owner_route_basis: Mapping[str, Any],
) -> dict[str, Any]:
    identity = _mapping(provider_admission_identity)
    if not identity:
        return {}
    work_unit_id = _text(identity.get("work_unit_id"))
    work_unit_fingerprint = _text(identity.get("work_unit_fingerprint"))
    action_fingerprint = _text(identity.get("action_fingerprint")) or work_unit_fingerprint
    currentness_basis = dict(owner_route_basis)
    identity_basis = _mapping(identity.get("currentness_basis"))
    for key, value in identity_basis.items():
        if value is not None:
            currentness_basis[key] = value
    if work_unit_id is not None and _text(owner_route_basis.get("work_unit_id")) is None:
        currentness_basis["work_unit_id"] = work_unit_id
    if work_unit_fingerprint is not None and _text(owner_route_basis.get("work_unit_fingerprint")) is None:
        currentness_basis["work_unit_fingerprint"] = work_unit_fingerprint
    for key in ("work_unit_id", "work_unit_fingerprint"):
        value = _text(owner_route_basis.get(key))
        if value is not None:
            currentness_basis[key] = value
    fields: dict[str, Any] = {
        "provider_admission_identity": dict(identity),
        "provider_admission_status": _text(identity.get("status")),
        "provider_admission_source": _text(identity.get("source")),
        "provider_admission_execution_ref": _text(identity.get("execution_ref")),
        "provider_attempt_or_lease_required": identity.get("provider_attempt_or_lease_required") is True,
        "owner_callable_surface": _text(identity.get("owner_callable_surface")),
    }
    canonical_work_unit_id = _text(owner_route_basis.get("work_unit_id"))
    canonical_work_unit_fingerprint = _text(owner_route_basis.get("work_unit_fingerprint"))
    if work_unit_id is not None and canonical_work_unit_id is None:
        fields["work_unit_id"] = work_unit_id
    if work_unit_fingerprint is not None and canonical_work_unit_fingerprint is None:
        fields["work_unit_fingerprint"] = work_unit_fingerprint
    provider_matches_canonical_fingerprint = (
        action_fingerprint is not None
        and canonical_work_unit_fingerprint is not None
        and action_fingerprint == canonical_work_unit_fingerprint
    )
    if action_fingerprint is not None and (
        canonical_work_unit_fingerprint is None or provider_matches_canonical_fingerprint
    ):
        fields["action_fingerprint"] = action_fingerprint
        fields["source_fingerprint"] = action_fingerprint
    if currentness_basis:
        fields["owner_route_currentness_basis"] = currentness_basis
    return {key: value for key, value in fields.items() if value is not None}


def _candidate_dispatch_path_matches(
    *,
    candidate_dispatch_path: str | None,
    dispatch_path: Path,
    stage_packet_path: Path,
    workspace_root: Path,
) -> bool:
    candidate = _normalized_path_text(candidate_dispatch_path)
    if candidate is None:
        return False
    expected_paths = {
        _normalized_path_text(str(dispatch_path)),
        _normalized_path_text(str(stage_packet_path)),
        _normalized_path_text(_workspace_relative(dispatch_path, workspace_root=workspace_root)),
        _normalized_path_text(_workspace_relative(stage_packet_path, workspace_root=workspace_root)),
    }
    expected = {path for path in expected_paths if path is not None}
    for path in expected:
        if candidate == path or candidate.endswith(f"/{path}") or path.endswith(f"/{candidate}"):
            return True
    return False


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_path_text(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text.replace("\\", "/")


__all__ = [
    "current_provider_admission_supersedes_consumed_receipt",
    "matching_provider_admission_identity",
    "provider_admission_payload_fields",
]
