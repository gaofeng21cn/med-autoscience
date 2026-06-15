from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_progress
from med_autoscience.profiles import WorkspaceProfile, load_profile


SURFACE_KIND = "default_executor_dispatch_residue_cleanup"
SCHEMA_VERSION = "mas.default_executor_dispatch_residue_cleanup.v1"
DISPATCH_ROOT_RELPATH = Path("artifacts") / "supervision" / "consumer" / "default_executor_dispatches"
MIGRATION_ROOT_RELPATH = Path("artifacts") / "migration" / SURFACE_KIND
HISTORY_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "history"
ARCHIVE_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "archive"
RESIDUE_STATUSES = {"ready", "migrated_to_provenance", "superseded", "closed"}
TERMINAL_CURRENT_WORK_UNIT_STATUSES = {
    "owner_receipt_recorded",
    "typed_blocker",
    "blocked_current_work_unit",
    "human_gate",
    "waiting_human",
    "terminal_success",
    "terminal_stop_loss",
}
TERMINAL_RECOVERY_PHASES = {
    "owner_receipt_recorded",
    "domain_blocked",
    "typed_blocker",
    "blocked_current_work_unit",
    "waiting_human",
    "human_gate",
    "terminal_success",
    "terminal_stop_loss",
}
TERMINAL_NEXT_SAFE_ACTIONS = {
    "consume_owner_receipt",
    "resolve_typed_blocker",
    "wait_human_gate",
    "route_back_to_owner",
}

ProgressReader = Callable[..., Mapping[str, Any]]


def run_default_executor_dispatch_residue_cleanup(
    *,
    profile_path: Path,
    study_ids: Iterable[str] | None = None,
    apply: bool,
    progress_reader: ProgressReader | None = None,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    selected_study_ids = _resolve_study_ids(profile=profile, study_ids=study_ids)
    recorded_at = _utc_now()
    reader = progress_reader or _default_progress_reader
    initial_studies = [
        _study_plan(profile=profile, study_id=study_id, recorded_at=recorded_at, progress_reader=reader)
        for study_id in selected_study_ids
    ]
    archived_by_study: dict[str, list[dict[str, Any]]] = {study["study_id"]: [] for study in initial_studies}
    if apply and not _has_blockers(initial_studies):
        for study in initial_studies:
            archived_by_study[str(study["study_id"])] = _apply_study_cleanup(
                study_plan=study,
                recorded_at=recorded_at,
            )
    final_studies = (
        [
            _study_plan(profile=profile, study_id=study_id, recorded_at=recorded_at, progress_reader=reader)
            for study_id in selected_study_ids
        ]
        if apply and not _has_blockers(initial_studies)
        else initial_studies
    )
    studies = [
        {
            **study,
            "archived_mutable_slots": archived_by_study.get(str(study["study_id"]), []),
        }
        for study in final_studies
    ]
    report = _report(
        profile=profile,
        profile_path=resolved_profile_path,
        recorded_at=recorded_at,
        mode="apply" if apply else "dry_run",
        initial_studies=initial_studies,
        studies=studies,
        archived_by_study=archived_by_study,
    )
    if apply and not _has_blockers(initial_studies):
        for study in studies:
            if archived_by_study.get(str(study["study_id"])):
                _write_study_receipt(study=study, report=report, recorded_at=recorded_at)
    return report


def _study_plan(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    recorded_at: str,
    progress_reader: ProgressReader,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    study_root = (profile.studies_root / study_id).expanduser().resolve()
    dispatch_root = study_root / DISPATCH_ROOT_RELPATH
    progress = _read_progress(profile=profile, study_id=study_id, progress_reader=progress_reader)
    currentness = _currentness_gate(progress)
    mutable_slots = _mutable_dispatch_slots(
        workspace_root=workspace_root,
        study_root=study_root,
        dispatch_root=dispatch_root,
        archive_stamp=_history_stamp(recorded_at),
    )
    blockers = list(currentness["blockers"])
    for slot in mutable_slots:
        if slot["status"] not in RESIDUE_STATUSES:
            blockers.append(
                {
                    "reason": "unknown_mutable_dispatch_status",
                    "source_relative_path": slot["source_relative_path"],
                    "status": slot["status"],
                }
            )
    cleanup_allowed = not blockers and currentness["terminal_or_blocked_owner_outcome"] is True
    cleanup_candidates = [
        {
            **slot,
            "cleanup_decision": "archive_mutable_residue",
            "stale_reason": currentness["basis_reason"],
            "currentness_basis": currentness["basis"],
        }
        for slot in mutable_slots
        if cleanup_allowed and slot["status"] in RESIDUE_STATUSES
    ]
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "dispatch_root": str(dispatch_root),
        "dispatch_root_exists": dispatch_root.is_dir(),
        "recorded_at": recorded_at,
        "currentness_gate": currentness,
        "blockers": blockers,
        "ready_mutable_slot_count": sum(1 for slot in mutable_slots if slot["status"] == "ready"),
        "mutable_residue_slot_count": sum(1 for slot in mutable_slots if slot["status"] in RESIDUE_STATUSES),
        "stale_ready_mutable_slot_count": sum(
            1 for slot in cleanup_candidates if slot["status"] == "ready"
        ),
        "cleanup_candidate_count": len(cleanup_candidates),
        "mutable_slots": mutable_slots,
        "cleanup_candidates": cleanup_candidates,
        "immutable_provenance_file_count": _immutable_provenance_file_count(dispatch_root),
        "receipt_path": str(study_root / MIGRATION_ROOT_RELPATH / "latest.json"),
    }


def _mutable_dispatch_slots(
    *,
    workspace_root: Path,
    study_root: Path,
    dispatch_root: Path,
    archive_stamp: str,
) -> list[dict[str, Any]]:
    if not dispatch_root.is_dir():
        return []
    slots: list[dict[str, Any]] = []
    for path in sorted(dispatch_root.glob("*.json")):
        payload = _read_json_object(path)
        status = _text((payload or {}).get("dispatch_status")) or _text((payload or {}).get("status"))
        action_type = _text((payload or {}).get("action_type"))
        owner_route = (payload or {}).get("owner_route")
        owner_route = owner_route if isinstance(owner_route, Mapping) else {}
        source_refs = owner_route.get("source_refs")
        source_refs = source_refs if isinstance(source_refs, Mapping) else {}
        source_sha256 = _sha256_file(path)
        archive_path = _archive_path(study_root=study_root, source=path, archive_stamp=archive_stamp)
        slots.append(
            {
                "source_absolute_path": str(path),
                "source_relative_path": _relative_ref(workspace_root, path),
                "source_study_relative_path": _relative_ref(study_root, path),
                "archive_absolute_path": str(archive_path),
                "archive_relative_path": _relative_ref(workspace_root, archive_path),
                "status": status,
                "action_type": action_type,
                "work_unit_id": _text((payload or {}).get("work_unit_id"))
                or _text(source_refs.get("work_unit_id")),
                "work_unit_fingerprint": _text((payload or {}).get("work_unit_fingerprint"))
                or _text((payload or {}).get("action_fingerprint"))
                or _text(owner_route.get("work_unit_fingerprint"))
                or _text(source_refs.get("work_unit_fingerprint")),
                "source_sha256": source_sha256,
                "payload_surface": _text((payload or {}).get("surface"))
                or _text((payload or {}).get("surface_kind")),
            }
        )
    return slots


def _currentness_gate(progress: Mapping[str, Any]) -> dict[str, Any]:
    current_action = progress.get("current_executable_owner_action")
    if isinstance(current_action, Mapping) and current_action:
        return {
            "pass": False,
            "terminal_or_blocked_owner_outcome": False,
            "basis_reason": "current_executable_owner_action_present",
            "basis": _current_basis(progress),
            "blockers": [{"reason": "current_executable_owner_action_present"}],
        }
    current_work_unit = progress.get("current_work_unit")
    current_work_unit = current_work_unit if isinstance(current_work_unit, Mapping) else {}
    paper_recovery = progress.get("paper_recovery_state")
    paper_recovery = paper_recovery if isinstance(paper_recovery, Mapping) else {}
    next_safe_action = paper_recovery.get("next_safe_action")
    next_safe_action = next_safe_action if isinstance(next_safe_action, Mapping) else {}
    status = _text(current_work_unit.get("status")) or _text(current_work_unit.get("state_kind"))
    state = current_work_unit.get("state")
    state = state if isinstance(state, Mapping) else {}
    status = status or _text(state.get("state_kind"))
    blocker_type = _text(state.get("blocker_type"))
    phase = _text(paper_recovery.get("phase"))
    next_safe_action_kind = _text(next_safe_action.get("kind"))
    terminal = (
        status in TERMINAL_CURRENT_WORK_UNIT_STATUSES
        or phase in TERMINAL_RECOVERY_PHASES
        or next_safe_action_kind in TERMINAL_NEXT_SAFE_ACTIONS
        or bool(blocker_type)
    )
    if not terminal:
        return {
            "pass": False,
            "terminal_or_blocked_owner_outcome": False,
            "basis_reason": "no_terminal_owner_outcome_basis",
            "basis": _current_basis(progress),
            "blockers": [{"reason": "no_terminal_owner_outcome_basis"}],
        }
    return {
        "pass": True,
        "terminal_or_blocked_owner_outcome": True,
        "basis_reason": "current_authority_is_terminal_or_blocked_owner_outcome",
        "basis": _current_basis(progress),
        "blockers": [],
    }


def _current_basis(progress: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = progress.get("current_work_unit")
    current_work_unit = current_work_unit if isinstance(current_work_unit, Mapping) else {}
    paper_recovery = progress.get("paper_recovery_state")
    paper_recovery = paper_recovery if isinstance(paper_recovery, Mapping) else {}
    next_safe_action = paper_recovery.get("next_safe_action")
    next_safe_action = next_safe_action if isinstance(next_safe_action, Mapping) else {}
    state = current_work_unit.get("state")
    state = state if isinstance(state, Mapping) else {}
    return {
        "study_id": _text(progress.get("study_id")),
        "current_stage": _text(progress.get("current_stage")),
        "current_work_unit_status": _text(current_work_unit.get("status"))
        or _text(current_work_unit.get("state_kind"))
        or _text(state.get("state_kind"))
        or _text(state.get("blocker_type")),
        "current_action_type": _text(current_work_unit.get("action_type")),
        "current_work_unit_id": _text(current_work_unit.get("work_unit_id")),
        "current_work_unit_fingerprint": _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint")),
        "paper_recovery_phase": _text(paper_recovery.get("phase")),
        "next_safe_action_kind": _text(next_safe_action.get("kind")),
        "provider_admission_allowed": next_safe_action.get("provider_admission_allowed"),
    }


def _apply_study_cleanup(*, study_plan: Mapping[str, Any], recorded_at: str) -> list[dict[str, Any]]:
    archived: list[dict[str, Any]] = []
    for candidate in study_plan.get("cleanup_candidates") or []:
        source = Path(str(candidate["source_absolute_path"]))
        if not source.exists():
            archived.append({**dict(candidate), "applied": False, "skip_reason": "source_missing"})
            continue
        archive_path = _unique_archive_path(Path(str(candidate["archive_absolute_path"])), source)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        source.rename(archive_path)
        archived.append(
            {
                **dict(candidate),
                "archive_absolute_path": str(archive_path),
                "archive_relative_path": _relative_ref(
                    Path(str(study_plan["study_root"])).parent.parent,
                    archive_path,
                ),
                "applied": True,
                "archived_at": recorded_at,
            }
        )
    return archived


def _report(
    *,
    profile: WorkspaceProfile,
    profile_path: Path,
    recorded_at: str,
    mode: str,
    initial_studies: list[Mapping[str, Any]],
    studies: list[Mapping[str, Any]],
    archived_by_study: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    cleanup_candidate_count = sum(int(study["cleanup_candidate_count"]) for study in studies)
    blocker_count = sum(len(study.get("blockers") or []) for study in studies)
    status = "typed_blocked" if blocker_count else "cleanup_pending" if cleanup_candidate_count else "clean"
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "mode": mode,
        "status": status,
        "recorded_at": recorded_at,
        "profile_path": str(profile_path),
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "authority_boundary": {
            "paper_content_mutation": False,
            "publication_truth_mutation": False,
            "runtime_truth_mutation": False,
            "provider_start": False,
            "dhd_apply": False,
            "default_executor_mutable_residue_mutation": mode == "apply",
            "immutable_dispatch_provenance_mutation": False,
        },
        "selection_policy": {
            "mutable_slot_glob": "artifacts/supervision/consumer/default_executor_dispatches/*.json",
            "immutable_provenance_glob": "artifacts/supervision/consumer/default_executor_dispatches/immutable/**/*.json",
            "immutable_provenance_action": "preserve",
            "current_executable_owner_action_policy": "fail_closed",
            "required_currentness_basis": "terminal_or_blocked_owner_outcome",
        },
        "study_count": len(studies),
        "ready_mutable_slot_count": sum(int(study["ready_mutable_slot_count"]) for study in studies),
        "mutable_residue_slot_count": sum(int(study["mutable_residue_slot_count"]) for study in studies),
        "cleanup_candidate_count": cleanup_candidate_count,
        "initial_cleanup_candidate_count": sum(int(study["cleanup_candidate_count"]) for study in initial_studies),
        "blocker_count": blocker_count,
        "archived_mutable_slot_count": sum(len(items) for items in archived_by_study.values()),
        "studies": studies,
        "post_apply": {
            "remaining_cleanup_candidate_count": cleanup_candidate_count,
            "archived_mutable_slot_count": sum(len(items) for items in archived_by_study.values()),
            "blocked_count": blocker_count,
        }
        if mode == "apply"
        else None,
    }


def _write_study_receipt(*, study: Mapping[str, Any], report: Mapping[str, Any], recorded_at: str) -> None:
    study_root = Path(str(study["study_root"])).expanduser().resolve()
    root = study_root / MIGRATION_ROOT_RELPATH
    history_root = study_root / HISTORY_ROOT_RELPATH
    history_root.mkdir(parents=True, exist_ok=True)
    history_path = history_root / f"{_history_stamp(recorded_at)}.json"
    latest_path = root / "latest.json"
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "status": "applied",
        "recorded_at": recorded_at,
        "study_id": study["study_id"],
        "study_root": study["study_root"],
        "authority_boundary": dict(report["authority_boundary"]),
        "selection_policy": dict(report["selection_policy"]),
        "studies": [dict(study)],
        "latest_path": str(latest_path),
        "history_path": str(history_path),
    }
    history_path.write_text(_json_dumps(receipt), encoding="utf-8")
    latest_path.write_text(_json_dumps(receipt), encoding="utf-8")


def _read_progress(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    progress_reader: ProgressReader,
) -> dict[str, Any]:
    payload = progress_reader(profile=profile, study_id=study_id)
    if not isinstance(payload, Mapping):
        raise ValueError(f"progress_reader returned non-mapping for {study_id}")
    return dict(payload)


def _default_progress_reader(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    return study_progress.read_study_progress(
        profile=profile,
        profile_ref=None,
        study_id=study_id,
        entry_mode=None,
        sync_runtime_summary=False,
        materialize_read_model_artifacts=False,
    )


def _resolve_study_ids(*, profile: WorkspaceProfile, study_ids: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(item for raw in (study_ids or ()) if (item := _text(raw)) is not None)
    if selected:
        available_study_ids = set(_discover_study_ids(profile))
        for study_id in selected:
            if study_id not in available_study_ids:
                known = ", ".join(sorted(available_study_ids)) or "<none>"
                raise ValueError(f"Unknown study dispatch residue study_id: {study_id}; known study_ids: {known}")
        return selected
    return _discover_study_ids(profile)


def _discover_study_ids(profile: WorkspaceProfile) -> tuple[str, ...]:
    studies_root = profile.studies_root.expanduser().resolve()
    if not studies_root.is_dir():
        return ()
    return tuple(
        path.name for path in sorted(studies_root.iterdir()) if path.is_dir() and (path / "study.yaml").exists()
    )


def _immutable_provenance_file_count(dispatch_root: Path) -> int:
    immutable_root = dispatch_root / "immutable"
    if not immutable_root.is_dir():
        return 0
    return sum(1 for path in immutable_root.rglob("*.json") if path.is_file())


def _archive_path(*, study_root: Path, source: Path, archive_stamp: str) -> Path:
    return study_root / ARCHIVE_ROOT_RELPATH / archive_stamp / _relative_ref(study_root, source)


def _unique_archive_path(target: Path, source: Path) -> Path:
    if not target.exists():
        return target
    short_hash = _sha256_file(source).removeprefix("sha256:")[:16]
    return target.with_name(f"{target.stem}-{short_hash}{target.suffix}")


def _has_blockers(studies: Iterable[Mapping[str, Any]]) -> bool:
    return any(study.get("blockers") for study in studies)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _history_stamp(recorded_at: str) -> str:
    return recorded_at.replace("+00:00", "Z").replace("+0000", "Z").replace("-", "").replace(":", "")


def _sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _json_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _relative_ref(root: Path, path: Path) -> str:
    try:
        return path.expanduser().resolve().relative_to(root.expanduser().resolve()).as_posix()
    except ValueError:
        return str(path)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["run_default_executor_dispatch_residue_cleanup"]
