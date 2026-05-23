from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _message_digest(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def build_pending_user_message_handoff(
    *,
    quest_root: Path,
    runtime_state: Mapping[str, Any] | None,
    message: str,
    source: str,
    evidence_refs: Iterable[str] | None = None,
    dedupe_key: str | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    state = runtime_state if isinstance(runtime_state, Mapping) else {}
    quest_id = _text(state.get("quest_id")) or resolved_quest_root.name
    digest = _message_digest(message)
    handoff_id = _text(dedupe_key) or f"pending-user-message::{quest_id}::{digest[:16]}"
    return {
        "surface_kind": "mas_opl_pending_user_message_handoff",
        "handoff_id": handoff_id,
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "source": source,
        "status": "owner_route_required",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "message_delivery_owner": "one-person-lab",
        "hydration_owner": "one-person-lab",
        "mas_runtime_queue_retired": True,
        "message_body_included": False,
        "message_digest": digest,
        "evidence_refs": _string_items(evidence_refs),
        "dedupe_key": _text(dedupe_key),
        "runtime_state_mutated": False,
        "user_message_queue_mutated": False,
        "interaction_journal_mutated": False,
        "required_handoff": "Hydrate this MAS controller intervention through OPL current_control_state.",
        "typed_blocker": {
            "blocker_type": "opl_pending_user_message_handoff_required",
            "owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "reason": "mas_user_message_queue_retired",
        },
    }


__all__ = ["build_pending_user_message_handoff"]
