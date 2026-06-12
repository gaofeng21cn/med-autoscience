from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts import provider_admission

from .shared import _mapping_copy, _non_empty_text


def provider_admission_projection_fields(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    candidates = provider_admission.current_control_provider_admission_candidates(
        handoff,
        study_root=study_root,
        status_payload=payload,
        current_control_ref=_non_empty_text(_mapping_copy(handoff.get("refs")).get("latest_path"))
        or _non_empty_text(handoff.get("source_path")),
    )
    return {
        "provider_admission_pending_count": len(candidates),
        "provider_admission_candidates": list(candidates),
    }
