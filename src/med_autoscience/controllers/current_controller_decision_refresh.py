from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from .domain_owner_action_dispatch_parts import controller_refresh


SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _resolve_study_ids(profile: WorkspaceProfile, study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    if not profile.studies_root.is_dir():
        return ()
    return tuple(
        path.name
        for path in sorted(profile.studies_root.iterdir(), key=lambda item: item.name)
        if path.is_dir()
    )


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def refresh_controller_decisions_for_current_publication_eval(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    return controller_refresh.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=study_ids,
        mode=mode,
        apply=apply,
        generated_at=_utc_now(),
        schema_version=SCHEMA_VERSION,
        resolve_study_ids=_resolve_study_ids,
        study_root=_study_root,
    )


__all__ = [
    "SCHEMA_VERSION",
    "refresh_controller_decisions_for_current_publication_eval",
]
