from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


IMMUTABLE_PACKET_DIRNAME = "immutable"


def immutable_dispatch_packet_path(
    *,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
) -> Path:
    action_type = _slug(_text(dispatch.get("action_type")) or dispatch_path.stem)
    fingerprint = _packet_fingerprint(dispatch=dispatch, dispatch_path=dispatch_path)
    return dispatch_path.parent / IMMUTABLE_PACKET_DIRNAME / action_type / f"{fingerprint}.json"


def dispatch_stage_packet_path(dispatch: Mapping[str, Any], *, fallback_dispatch_path: Path) -> Path:
    refs = _mapping(dispatch.get("refs"))
    packet_path = _text(refs.get("immutable_dispatch_path")) or _text(refs.get("stage_packet_path"))
    if packet_path is None:
        return fallback_dispatch_path
    return Path(packet_path)


def dispatch_with_immutable_packet_ref(
    *,
    dispatch: Mapping[str, Any],
    dispatch_path: Path,
) -> dict[str, Any]:
    packet_path = immutable_dispatch_packet_path(dispatch_path=dispatch_path, dispatch=dispatch)
    payload = dict(dispatch)
    refs = {**_mapping(payload.get("refs"))}
    refs["dispatch_path"] = str(dispatch_path)
    refs["immutable_dispatch_path"] = str(packet_path)
    refs["stage_packet_path"] = str(packet_path)
    payload["refs"] = refs
    return payload


def _packet_fingerprint(*, dispatch: Mapping[str, Any], dispatch_path: Path) -> str:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    identity = {
        "dispatch_path": str(dispatch_path),
        "action_type": _text(dispatch.get("action_type")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(owner_route.get("idempotency_key")),
        "work_unit_id": _text(source_refs.get("work_unit_id")) or _text(owner_route.get("work_unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint")),
        "runtime_health_epoch": _text(owner_route.get("runtime_health_epoch"))
        or _text(source_refs.get("runtime_health_epoch")),
        "generated_at": _text(dispatch.get("generated_at")),
    }
    rendered = json.dumps(identity, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:24]


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "dispatch"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "IMMUTABLE_PACKET_DIRNAME",
    "dispatch_stage_packet_path",
    "dispatch_with_immutable_packet_ref",
    "immutable_dispatch_packet_path",
]
