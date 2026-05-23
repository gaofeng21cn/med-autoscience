from __future__ import annotations

from importlib import import_module
from pathlib import Path

from med_autoscience import opl_runtime_contract
from med_autoscience.study_completion import StudyCompletionState, resolve_study_completion_state


def _router_module():
    return import_module("med_autoscience.controllers.domain_status_projection")


def _study_completion_state(*, study_root: Path) -> StudyCompletionState:
    return _router_module().resolve_study_completion_state(study_root=study_root)


def _sync_study_completion(
    *,
    runtime_root: Path,
    quest_id: str,
    completion_state: StudyCompletionState,
    source: str,
) -> dict[str, object]:
    contract = completion_state.contract
    summary = contract.summary.strip() if contract is not None else ""
    if contract is not None and contract.requires_program_human_confirmation:
        raise ValueError("study completion sync requires MAS outer-loop human confirmation before runtime closure")
    if not summary:
        raise ValueError("study completion sync requires summary")
    return {
        "completion": {
            **opl_runtime_contract.provider_admission_required_blocker(
                operation="artifact_complete_quest",
                quest_id=quest_id,
            ),
            "runtime_root": str(Path(runtime_root).expanduser().resolve()),
            "summary_digest_required": True,
            "domain_completion_summary_present": True,
        },
        "source": source,
    }
