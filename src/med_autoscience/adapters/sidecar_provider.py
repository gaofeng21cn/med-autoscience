from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Mapping


SAFE_INSTANCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _normalize_instance_id(instance_id: str | None) -> str | None:
    if instance_id is None:
        return None
    normalized = str(instance_id).strip()
    if not normalized:
        return None
    if not SAFE_INSTANCE_ID.fullmatch(normalized):
        raise ValueError(f"unsafe sidecar instance_id: {instance_id}")
    return normalized


def sidecar_root(quest_root: Path, *, provider_id: str, instance_id: str | None = None) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    root = resolved_quest_root / "sidecars" / str(provider_id).strip()
    normalized_instance_id = _normalize_instance_id(instance_id)
    if normalized_instance_id is not None:
        root = root / normalized_instance_id
    return root


def handoff_root(quest_root: Path, *, provider_id: str, instance_id: str | None = None) -> Path:
    return sidecar_root(quest_root, provider_id=provider_id, instance_id=instance_id) / "handoff"


def artifact_root(quest_root: Path, *, domain_id: str, provider_id: str, instance_id: str | None = None) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    root = resolved_quest_root / "artifacts" / str(domain_id).strip() / str(provider_id).strip()
    normalized_instance_id = _normalize_instance_id(instance_id)
    if normalized_instance_id is not None:
        root = root / normalized_instance_id
    return root


def recommendation_path(quest_root: Path, *, provider_id: str, instance_id: str | None = None) -> Path:
    return sidecar_root(quest_root, provider_id=provider_id, instance_id=instance_id) / "recommendation.json"


def input_contract_path(quest_root: Path, *, provider_id: str, instance_id: str | None = None) -> Path:
    return sidecar_root(quest_root, provider_id=provider_id, instance_id=instance_id) / "input_contract.json"


def state_path(quest_root: Path, *, provider_id: str, instance_id: str | None = None) -> Path:
    return sidecar_root(quest_root, provider_id=provider_id, instance_id=instance_id) / "sidecar_state.json"


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def build_contract_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def copy_file(*, source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
