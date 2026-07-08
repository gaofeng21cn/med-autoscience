from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


LEDGER_RELATIVE_PATH = (
    Path("family-runtime")
    / "paper-autonomy"
    / "supervisor"
    / "supervisor-decisions.jsonl"
)
LEDGER_ENTRY_SURFACE_KIND = "opl_paper_autonomy_supervisor_decision_ledger_entry"
READBACK_SURFACE_KIND = "opl_paper_autonomy_supervisor_decision_readback"


def attach_opl_supervisor_decision_readback(
    payload: Mapping[str, Any],
    *,
    profile: WorkspaceProfile | None = None,
) -> dict[str, Any]:
    updated = dict(payload)
    study_id = _text(updated.get("study_id"))
    if study_id is None:
        return updated
    ledger_path = _supervisor_decision_ledger_path(profile=profile)
    if ledger_path is None:
        return updated
    readbacks = current_opl_supervisor_decision_readbacks(
        ledger_path=ledger_path,
        study_id=study_id,
    )
    if not readbacks:
        return updated

    merged = _merge_readback_lists(
        updated.get("opl_paper_autonomy_supervisor_decision_readbacks"),
        readbacks,
    )
    updated["opl_paper_autonomy_supervisor_decision_readbacks"] = merged
    matching = _matching_payload_readback(updated, readbacks=readbacks)
    if matching is not None:
        updated["opl_paper_autonomy_supervisor_decision_readback"] = matching

    refs = dict(updated.get("refs")) if isinstance(updated.get("refs"), Mapping) else {}
    refs["opl_paper_autonomy_supervisor_decision_ledger_path"] = str(ledger_path)
    readback_refs = _text_items(item.get("decision_id") for item in readbacks)
    if readback_refs:
        refs["opl_paper_autonomy_supervisor_decision_readback_refs"] = readback_refs
    if matching is not None and (decision_id := _text(matching.get("decision_id"))) is not None:
        refs["opl_paper_autonomy_supervisor_decision_readback_ref"] = decision_id
    updated["refs"] = refs
    return updated


def current_opl_supervisor_decision_readbacks(
    *,
    ledger_path: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    latest_by_identity: dict[str, dict[str, Any]] = {}
    for entry in _read_jsonl_objects(ledger_path):
        if _text(entry.get("surface_kind")) != LEDGER_ENTRY_SURFACE_KIND:
            continue
        if _text(entry.get("entry_kind")) != "supervisor_decision_appended":
            continue
        readback = _mapping(entry.get("decision"))
        if _text(readback.get("surface_kind")) != READBACK_SURFACE_KIND:
            continue
        if not _readback_matches_study(readback, study_id=study_id):
            continue
        identity_key = _identity_key(readback)
        if identity_key is None:
            continue
        latest_by_identity[identity_key] = readback
    return list(latest_by_identity.values())


def _supervisor_decision_ledger_path(
    *,
    profile: WorkspaceProfile | None,
) -> Path | None:
    for state_root in _candidate_state_roots(profile=profile):
        ledger_path = state_root / LEDGER_RELATIVE_PATH
        if ledger_path.exists():
            return ledger_path.resolve()
    return None


def _candidate_state_roots(*, profile: WorkspaceProfile | None) -> list[Path]:
    roots: list[Path] = []
    explicit = _text(os.environ.get("OPL_STATE_DIR"))
    if explicit is not None:
        roots.append(Path(explicit).expanduser())
    if profile is not None:
        roots.append(profile.managed_runtime_home)
    if profile is None or not _profile_uses_temporary_workspace(profile):
        home_dir = Path(_text(os.environ.get("HOME")) or str(Path.home())).expanduser()
        roots.append(home_dir / "Library" / "Application Support" / "OPL" / "state")
    result: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        resolved = root.resolve()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def _profile_uses_temporary_workspace(profile: WorkspaceProfile) -> bool:
    try:
        profile_root = Path(profile.workspace_root).expanduser().resolve()
        profile_root.relative_to(Path(tempfile.gettempdir()).resolve())
        return True
    except ValueError:
        return False


def _read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    result: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            result.append(dict(payload))
    return result


def _readback_matches_study(readback: Mapping[str, Any], *, study_id: str) -> bool:
    current_identity = _mapping(readback.get("current_identity"))
    if _text(readback.get("study_id")) == study_id:
        return True
    if _text(current_identity.get("study_id")) == study_id:
        return True
    obligation_id = _text(readback.get("obligation_id"))
    return bool(obligation_id and f"::{study_id}::" in obligation_id)


def _identity_key(readback: Mapping[str, Any]) -> str | None:
    obligation_id = _text(readback.get("obligation_id"))
    current_identity = _mapping(readback.get("current_identity"))
    route_identity_key = _text(current_identity.get("route_identity_key"))
    attempt_idempotency_key = _text(current_identity.get("attempt_idempotency_key"))
    stage_run_id = _text(current_identity.get("stage_run_id"))
    work_unit_fingerprint = _text(current_identity.get("work_unit_fingerprint"))
    if not all(
        value is not None
        for value in (
            obligation_id,
            route_identity_key,
            attempt_idempotency_key,
            stage_run_id,
            work_unit_fingerprint,
        )
    ):
        return None
    return "::".join(
        (
            obligation_id,
            route_identity_key,
            attempt_idempotency_key,
            stage_run_id,
            work_unit_fingerprint,
        )
    )


def _matching_payload_readback(
    payload: Mapping[str, Any],
    *,
    readbacks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    obligation_id = _payload_obligation_id(payload)
    fingerprint = _payload_work_unit_fingerprint(payload)
    for readback in readbacks:
        if obligation_id is not None and _text(readback.get("obligation_id")) == obligation_id:
            return readback
    if fingerprint is None:
        return readbacks[0] if len(readbacks) == 1 else None
    matching = [
        readback
        for readback in readbacks
        if _text(_mapping(readback.get("current_identity")).get("work_unit_fingerprint"))
        == fingerprint
    ]
    if len(matching) == 1:
        return matching[0]
    return readbacks[0] if len(readbacks) == 1 else None


def _payload_obligation_id(payload: Mapping[str, Any]) -> str | None:
    recovery = _mapping(payload.get("paper_recovery_state"))
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    return _text(obligation.get("recovery_obligation_id")) or _text(
        recovery.get("recovery_obligation_id")
    )


def _payload_work_unit_fingerprint(payload: Mapping[str, Any]) -> str | None:
    for surface in (
        _mapping(payload.get("current_work_unit")),
        _mapping(payload.get("current_executable_owner_action")),
        _mapping(payload.get("current_execution_envelope")),
    ):
        fingerprint = _text(surface.get("work_unit_fingerprint")) or _text(
            surface.get("action_fingerprint")
        )
        if fingerprint is not None:
            return fingerprint
        basis = _mapping(surface.get("owner_route_currentness_basis")) or _mapping(
            surface.get("currentness_basis")
        )
        fingerprint = _text(basis.get("work_unit_fingerprint")) or _text(
            basis.get("source_fingerprint")
        )
        if fingerprint is not None:
            return fingerprint
    return None


def _merge_readback_lists(
    existing: object,
    new_readbacks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in list(existing or []) if isinstance(existing, list | tuple) else []:
        if not isinstance(item, Mapping):
            continue
        readback = dict(item)
        key = _text(readback.get("decision_id")) or _identity_key(readback)
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        merged.append(readback)
    for readback in new_readbacks:
        key = _text(readback.get("decision_id")) or _identity_key(readback)
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        merged.append(dict(readback))
    return merged


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(values: object) -> list[str]:
    result: list[str] = []
    if values is None:
        return result
    if not isinstance(values, list | tuple | set):
        values = list(values) if not isinstance(values, (str, bytes)) else [values]
    for value in values:
        text = _text(value)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "LEDGER_RELATIVE_PATH",
    "attach_opl_supervisor_decision_readback",
    "current_opl_supervisor_decision_readbacks",
]
