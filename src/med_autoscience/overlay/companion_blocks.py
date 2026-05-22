from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


COMPANION_TEMPLATE_MAP = {
    "decision": ("medical-research-stage-packet.block.md",),
    "finalize": ("medical-research-stage-packet.block.md",),
    "idea": ("medical-research-stage-packet.block.md",),
    "write": ("medical-research-stage-packet.block.md",),
}


def companion_template_names(skill_id: str) -> tuple[str, ...]:
    return COMPANION_TEMPLATE_MAP.get(skill_id, ())


def companion_file_statuses(*, skill_id: str, target_root: Path, template_root: Path) -> list[dict[str, Any]]:
    statuses = []
    for template_name in companion_template_names(skill_id):
        expected_text = _load_template_text(template_root=template_root, template_name=template_name)
        companion_path = target_root / template_name
        current_text = companion_path.read_text(encoding="utf-8") if companion_path.exists() else None
        expected_fingerprint = _fingerprint(expected_text)
        current_fingerprint = _fingerprint(current_text) if current_text is not None else None
        if current_text is None:
            status = "missing"
        elif current_fingerprint == expected_fingerprint:
            status = "ready"
        else:
            status = "drifted"
        statuses.append(
            {
                "template_name": template_name,
                "path": str(companion_path),
                "status": status,
                "current_fingerprint": current_fingerprint,
                "expected_fingerprint": expected_fingerprint,
            }
        )
    return statuses


def companion_files_ready(*, skill_id: str, target_root: Path, template_root: Path) -> bool:
    return all(
        item["status"] == "ready"
        for item in companion_file_statuses(skill_id=skill_id, target_root=target_root, template_root=template_root)
    )


def write_companion_files(*, skill_id: str, target_root: Path, template_root: Path) -> list[dict[str, Any]]:
    written = []
    for template_name in companion_template_names(skill_id):
        companion_path = target_root / template_name
        companion_text = _load_template_text(template_root=template_root, template_name=template_name)
        companion_path.write_text(companion_text, encoding="utf-8")
        written.append(
            {
                "template_name": template_name,
                "path": str(companion_path),
                "fingerprint": _fingerprint(companion_text),
            }
        )
    return written


def _load_template_text(*, template_root: Path, template_name: str) -> str:
    return (template_root / template_name).read_text(encoding="utf-8")


def _fingerprint(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
