from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable


CURRENTNESS_INPUT_SURFACES = (
    "manuscript",
    "evidence_ledger",
    "claim_evidence_map",
)


def request_record_currentness_input_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
    required_inputs: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    resolved_text_ref: Callable[..., str | None],
) -> list[str]:
    refs: list[str] = []
    for surface, ref in required_inputs(request_packet).items():
        if surface not in CURRENTNESS_INPUT_SURFACES:
            continue
        if not isinstance(ref, Mapping):
            continue
        resolved = resolved_text_ref(
            study_root=study_root,
            value=ref.get("path") or ref.get("relative_path") or ref.get("ref"),
        )
        if resolved:
            refs.append(resolved)
    return list(dict.fromkeys(refs))


__all__ = ["CURRENTNESS_INPUT_SURFACES", "request_record_currentness_input_refs"]
