from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.control_plane_facts import resolve_control_plane_facts

def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def normalize_activity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    return resolve_control_plane_facts(status_payload).to_runtime_worker_activity()
