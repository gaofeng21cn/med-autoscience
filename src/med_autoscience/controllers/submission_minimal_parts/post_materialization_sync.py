from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Callable

from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.runtime_protocol import resolve_paper_root_context


def _load_controller(module_name: str):
    return import_module(f"med_autoscience.controllers.{module_name}")


class _LazyModuleProxy:
    def __init__(self, loader: Callable[[], Any]) -> None:
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_module", None)

    def _resolve(self):
        module = object.__getattribute__(self, "_module")
        if module is None:
            module = object.__getattribute__(self, "_loader")()
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        setattr(self._resolve(), name, value)


publication_gate = _LazyModuleProxy(lambda: _load_controller("publication_gate"))
study_progress = _LazyModuleProxy(lambda: _load_controller("study_progress"))


def _read_optional_config_env_value(*, path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        current_key, raw_value = line.split("=", 1)
        if current_key.strip() != key:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        normalized = value.strip()
        return normalized or None
    return None


def _resolve_profile_for_study_root(study_root: Path) -> tuple[Path | None, WorkspaceProfile | None]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    workspace_root = resolved_study_root.parent.parent
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    profile_path: Path | None = None
    configured_profile = _read_optional_config_env_value(
        path=config_env_path,
        key="MED_AUTOSCIENCE_PROFILE",
    )
    if configured_profile is not None:
        candidate = Path(configured_profile).expanduser()
        if not candidate.is_absolute():
            candidate = (workspace_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        profile_path = candidate
    if profile_path is None:
        candidates = sorted((workspace_root / "ops" / "medautoscience" / "profiles").glob("*.local.toml"))
        if len(candidates) == 1:
            profile_path = candidates[0].resolve()
    if profile_path is None or not profile_path.exists():
        return None, None
    return profile_path, load_profile(profile_path)


def replay_post_submission_minimal_sync(*, paper_root: Path) -> dict[str, Any] | None:
    try:
        context = resolve_paper_root_context(Path(paper_root).expanduser().resolve())
    except (FileNotFoundError, ValueError):
        return None

    gate_replay = publication_gate.run_controller(
        quest_root=context.quest_root,
        apply=True,
        source="submission-minimal-post-materialization",
        enqueue_intervention=False,
    )
    gate_refresh = {
        "status": str(gate_replay.get("status") or "").strip(),
        "allow_write": bool(gate_replay.get("allow_write")),
        "current_required_action": str(gate_replay.get("current_required_action") or "").strip() or None,
        "report_json": str(gate_replay.get("report_json") or "").strip() or None,
        "journal_package_sync": gate_replay.get("journal_package_sync"),
    }

    profile_path, profile = _resolve_profile_for_study_root(context.study_root)
    if profile is None:
        return {
            "status": "gate_replayed_profile_unresolved",
            "quest_root": str(context.quest_root),
            "study_root": str(context.study_root),
            "gate_replay": gate_refresh,
            "progress_refresh": {
                "status": "skipped_profile_unresolved",
            },
        }

    progress_payload = study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_path,
        study_id=context.study_id,
        study_root=context.study_root,
    )
    refs = dict(progress_payload.get("refs") or {})
    return {
        "status": "synced",
        "quest_root": str(context.quest_root),
        "study_root": str(context.study_root),
        "gate_replay": gate_refresh,
        "progress_refresh": {
            "current_stage": str(progress_payload.get("current_stage") or "").strip() or None,
            "current_stage_summary": str(progress_payload.get("current_stage_summary") or "").strip() or None,
            "next_system_action": str(progress_payload.get("next_system_action") or "").strip() or None,
            "evaluation_summary_path": str(refs.get("evaluation_summary_path") or "").strip() or None,
            "runtime_status_summary_path": str(refs.get("runtime_status_summary_path") or "").strip() or None,
            "publication_eval_path": str(refs.get("publication_eval_path") or "").strip() or None,
        },
    }
