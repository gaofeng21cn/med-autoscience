from __future__ import annotations

from . import shared_base as _shared_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared_base)


def write_prediction_study(profile, study_id: str = "001-risk", **kwargs: object) -> Path:
    return write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        **kwargs,
    )


def running_progress_payload(
    study_root: Path,
    quest_root: Path,
    *,
    study_id: str = "001-risk",
    quest_id: str = "quest-001",
    **overrides: object,
) -> dict[str, object]:
    payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {"quest_id": quest_id, "auto_resume": True},
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
    }
    payload.update(overrides)
    return payload


def _runtime_state_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
