from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def manifest_declared_support_refs(
    manifest: Mapping[str, Any] | None,
    *,
    stage_folder_ref: str,
) -> list[str]:
    if manifest is None or manifest.get("_invalid_json") is True:
        return []
    refs: list[str] = []
    for field in (
        "required_input_artifact_refs",
        "owner_receipt_refs",
        "typed_blocker_refs",
        "lineage_refs",
        "projection_refs",
    ):
        refs.extend(_text_list(manifest.get(field)))
    return [_stage_folder_ref(stage_folder_ref=stage_folder_ref, ref=ref) for ref in refs]


def contract_ref_set(*, stage_folder_ref: str, refs: list[str]) -> list[str]:
    return sorted({_stage_folder_ref(stage_folder_ref=stage_folder_ref, ref=ref) for ref in refs})


def _stage_folder_ref(*, stage_folder_ref: str, ref: str) -> str:
    if ref.startswith("/") or ref.startswith("artifacts/"):
        return ref
    return f"{stage_folder_ref}/{ref}"


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]
