from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import literature_intelligence_os
from med_autoscience.controllers import literature_provider_runtime

from .shared import list_items, mapping, read_json, read_yaml, text


def payload_from_ready_literature_provider_runtime(
    *,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    path = (Path(study_root).expanduser().resolve() / literature_provider_runtime.ARTIFACT_RELATIVE_PATH).resolve()
    provider_runtime = read_json(path)
    if text(provider_runtime.get("surface")) != literature_provider_runtime.SURFACE:
        return {}
    if text(provider_runtime.get("status")) != "ready":
        return {}
    nested = mapping(provider_runtime.get("literature_intelligence_payload"))
    if not nested:
        return {}
    source_refs = [
        str(path),
        *[text(item) for item in list_items(provider_runtime.get("source_refs")) if text(item)],
        *[text(item) for item in list_items(nested.get("source_refs")) if text(item)],
    ]
    payload = {
        **nested,
        "surface": literature_intelligence_os.SURFACE,
        "schema_version": literature_intelligence_os.SCHEMA_VERSION,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "study_id": text(nested.get("study_id")) or text(provider_runtime.get("study_id")) or _study_id_from_root(study_root),
        "status": "ready",
        "missing_reason": "",
        "payload_source": source,
        "source_basis": "ready_literature_provider_runtime",
        "source_refs": list(dict.fromkeys(ref for ref in source_refs if ref)),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    if literature_intelligence_os._missing_reason(payload):
        return {}
    return payload


def _study_id_from_root(study_root: Path) -> str:
    study = read_yaml(Path(study_root).expanduser().resolve() / "study.yaml")
    return text(study.get("study_id")) or Path(study_root).name


__all__ = ["payload_from_ready_literature_provider_runtime"]
