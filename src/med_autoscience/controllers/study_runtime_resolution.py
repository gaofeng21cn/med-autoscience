from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience import opl_runtime_contract
from med_autoscience.profiles import WorkspaceProfile

__all__ = [
    "_execution_payload",
    "_load_yaml_dict",
    "_resolve_study",
]

_LEGACY_MDS_ENGINE_IDS = {"med-deepscientist", "med_deepscientist"}
_MAS_NATIVE_ENGINE_IDS = {"med-autoscience", "med_autoscience"}


def _router_module():
    return import_module("med_autoscience.controllers.domain_status_projection")


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    router = _router_module()
    if not path.exists():
        raise FileNotFoundError(f"missing required YAML file: {path}")
    payload = router.yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _resolve_study(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> tuple[str, Path, dict[str, Any]]:
    router = _router_module()
    if study_id is None and study_root is None:
        raise ValueError("study_id or study_root is required")
    if study_root is not None:
        resolved_study_root = Path(study_root).expanduser().resolve()
    else:
        resolved_study_root = (profile.studies_root / str(study_id)).resolve()
    study_payload = router._load_yaml_dict(resolved_study_root / "study.yaml")
    resolved_study_id = str(study_payload.get("study_id") or study_id or resolved_study_root.name).strip()
    if not resolved_study_id:
        raise ValueError(f"could not resolve study_id from {resolved_study_root / 'study.yaml'}")
    if study_id is not None and str(study_id).strip() != resolved_study_id:
        raise ValueError(f"study_id mismatch: expected {study_id}, got {resolved_study_id}")
    return resolved_study_id, resolved_study_root, study_payload


def _execution_payload(
    study_payload: dict[str, Any],
    *,
    profile: WorkspaceProfile | None = None,
) -> dict[str, Any]:
    execution = study_payload.get("execution")
    if not isinstance(execution, dict):
        execution_payload: dict[str, Any] = {}
    else:
        execution_payload = dict(execution)
    if profile is None:
        return execution_payload

    normalized_execution = dict(execution_payload)
    explicit_runtime_ref = opl_runtime_contract.explicit_opl_runtime_ref(normalized_execution)
    if explicit_runtime_ref is None and str(normalized_execution.get("auto_entry") or "").strip() == "on_managed_research_intent":
        profile_runtime_ref = str(profile.opl_runtime_ref or "").strip()
        legacy_runtime_ref = normalized_execution.get("runtime_backend_id") or normalized_execution.get("runtime_backend")
        legacy_runtime_ref = str(legacy_runtime_ref or "").strip() or None
        engine_text = str(normalized_execution.get("engine") or "").strip()
        should_apply_profile_runtime = legacy_runtime_ref == "med_deepscientist" or (
            legacy_runtime_ref is None
            and (
                not engine_text
                or engine_text in _LEGACY_MDS_ENGINE_IDS
                or engine_text in _MAS_NATIVE_ENGINE_IDS
            )
        )
        if profile_runtime_ref and should_apply_profile_runtime:
            normalized_execution["opl_runtime_ref"] = profile_runtime_ref
            normalized_execution["runtime_ref"] = profile_runtime_ref
            normalized_execution["runtime_engine_id"] = opl_runtime_contract.engine_id_for_runtime_ref(profile_runtime_ref)
            research_backend_id, research_engine_id = opl_runtime_contract.controlled_research_backend_metadata_for_runtime_ref(
                profile_runtime_ref
            )
            normalized_execution.setdefault("research_backend_id", research_backend_id)
            normalized_execution.setdefault("research_backend", research_backend_id)
            normalized_execution.setdefault("research_engine_id", research_engine_id)
    else:
        resolved_runtime_ref = opl_runtime_contract.explicit_opl_runtime_ref(normalized_execution)
        if resolved_runtime_ref is not None:
            research_backend_id, research_engine_id = opl_runtime_contract.controlled_research_backend_metadata_for_runtime_ref(
                resolved_runtime_ref
            )
            normalized_execution.setdefault("research_backend_id", research_backend_id)
            normalized_execution.setdefault("research_backend", research_backend_id)
            normalized_execution.setdefault("research_engine_id", research_engine_id)
    return normalized_execution
