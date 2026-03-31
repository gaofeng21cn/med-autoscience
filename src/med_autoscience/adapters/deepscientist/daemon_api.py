from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import medicaldeepscientist as medicaldeepscientist_transport


DEFAULT_DAEMON_TIMEOUT_SECONDS = medicaldeepscientist_transport.DEFAULT_DAEMON_TIMEOUT_SECONDS


def resolve_daemon_url(*, runtime_root: Path) -> str:
    return medicaldeepscientist_transport.resolve_daemon_url(runtime_root=runtime_root)


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return medicaldeepscientist_transport.create_quest(runtime_root=runtime_root, payload=payload)


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return medicaldeepscientist_transport.resume_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
    )


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return medicaldeepscientist_transport.pause_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
    )
