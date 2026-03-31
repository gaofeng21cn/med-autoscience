from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import user_message
from med_autoscience.runtime_transport import medicaldeepscientist as medicaldeepscientist_transport


def enqueue_user_message(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    message: str,
    source: str = "cli",
) -> dict[str, Any]:
    return user_message.enqueue_user_message(
        quest_root=quest_root,
        runtime_state=runtime_state,
        message=message,
        source=source,
    )


def post_quest_control(*, daemon_url: str, quest_id: str, action: str, source: str) -> dict[str, Any]:
    return medicaldeepscientist_transport.post_quest_control(
        daemon_url=daemon_url,
        quest_id=quest_id,
        action=action,
        source=source,
    )
