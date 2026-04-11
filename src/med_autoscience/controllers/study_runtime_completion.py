from __future__ import annotations

from importlib import import_module
from pathlib import Path

from med_autoscience.runtime_backend import ManagedRuntimeBackend
from med_autoscience.study_completion import StudyCompletionState, resolve_study_completion_state


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _study_completion_state(*, study_root: Path) -> StudyCompletionState:
    return _router_module().resolve_study_completion_state(study_root=study_root)


def _sync_study_completion(
    *,
    runtime_root: Path,
    quest_id: str,
    completion_state: StudyCompletionState,
    source: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, object]:
    router = _router_module()
    contract = completion_state.contract
    summary = contract.summary.strip() if contract is not None else ""
    if contract is not None and contract.requires_program_human_confirmation:
        raise ValueError("study completion sync requires MAS outer-loop human confirmation before runtime closure")
    if not summary:
        raise ValueError("study completion sync requires summary")
    backend = runtime_backend or router._default_managed_runtime_backend()
    completion = backend.artifact_complete_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        summary=summary,
    )
    return {
        "completion": completion,
        "source": source,
    }
