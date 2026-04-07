from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class DisplayPackManifest:
    pack_id: str
    version: str
    display_api_version: str
    default_execution_mode: str


def _expect_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def load_display_pack_manifest(path: Path) -> DisplayPackManifest:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))

    pack_id = _expect_str(payload, "pack_id")
    if "." not in pack_id:
        raise ValueError("pack_id must be namespaced")

    return DisplayPackManifest(
        pack_id=pack_id,
        version=_expect_str(payload, "version"),
        display_api_version=_expect_str(payload, "display_api_version"),
        default_execution_mode=_expect_str(payload, "default_execution_mode"),
    )
