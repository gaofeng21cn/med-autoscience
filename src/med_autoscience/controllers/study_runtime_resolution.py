from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.profiles import WorkspaceProfile

__all__ = [
    "_execution_payload",
    "_load_yaml_dict",
    "_resolve_study",
]


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


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
    explicit_backend_id = runtime_backend_contract.explicit_runtime_backend_id(normalized_execution)
    if explicit_backend_id is None and str(normalized_execution.get("auto_entry") or "").strip() == "on_managed_research_intent":
        profile_backend_id = str(profile.managed_runtime_backend_id or "").strip()
        legacy_backend_id = runtime_backend_contract.runtime_backend_id_from_execution(normalized_execution)
        engine_text = str(normalized_execution.get("engine") or "").strip()
        should_apply_profile_backend = (
            legacy_backend_id == "med_deepscientist"
            or (legacy_backend_id is None and not engine_text)
        )
        if profile_backend_id and should_apply_profile_backend:
            normalized_execution["runtime_backend_id"] = profile_backend_id
            normalized_execution["runtime_backend"] = profile_backend_id
            normalized_execution["runtime_engine_id"] = runtime_backend_contract.engine_id_for_backend_id(profile_backend_id)
            research_backend_id, research_engine_id = runtime_backend_contract.controlled_research_backend_metadata_for_backend_id(
                profile_backend_id
            )
            normalized_execution.setdefault("research_backend_id", research_backend_id)
            normalized_execution.setdefault("research_backend", research_backend_id)
            normalized_execution.setdefault("research_engine_id", research_engine_id)
    else:
        resolved_backend_id = runtime_backend_contract.runtime_backend_id_from_execution(normalized_execution)
        if resolved_backend_id is not None:
            research_backend_id, research_engine_id = runtime_backend_contract.controlled_research_backend_metadata_for_backend_id(
                resolved_backend_id
            )
            normalized_execution.setdefault("research_backend_id", research_backend_id)
            normalized_execution.setdefault("research_backend", research_backend_id)
            normalized_execution.setdefault("research_engine_id", research_engine_id)
    return normalized_execution
