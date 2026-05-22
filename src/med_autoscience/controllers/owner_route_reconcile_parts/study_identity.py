from __future__ import annotations

from pathlib import Path

from med_autoscience.profiles import WorkspaceProfile


def resolve_owner_route_reconcile_study_ids(profile: WorkspaceProfile) -> tuple[str, ...]:
    if not profile.studies_root.is_dir():
        return ()
    study_ids: list[str] = []
    for child in sorted(profile.studies_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        if any((child / marker).is_file() for marker in ("study.yaml", "study.yml", "study.toml")):
            study_ids.append(child.name)
    return tuple(study_ids)


def validate_scan_owner_route_reconcile_study_ids(profile: WorkspaceProfile, study_ids: tuple[str, ...]) -> None:
    available_study_ids = set(resolve_owner_route_reconcile_study_ids(profile))
    for study_id in study_ids:
        if study_id in available_study_ids:
            continue
        known = ", ".join(sorted(available_study_ids)) or "<none>"
        raise ValueError(f"Unknown supervisor study_id: {study_id}; known study_ids: {known}")


__all__ = ["resolve_owner_route_reconcile_study_ids", "validate_scan_owner_route_reconcile_study_ids"]
