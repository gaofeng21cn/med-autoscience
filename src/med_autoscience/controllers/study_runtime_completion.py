from __future__ import annotations

from pathlib import Path

from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience.study_completion import StudyCompletionState, resolve_study_completion_state


def _study_completion_state(*, study_root: Path) -> StudyCompletionState:
    return resolve_study_completion_state(study_root=study_root)


def _build_study_completion_request_message(
    *,
    study_id: str,
    study_root: Path,
    completion_state: StudyCompletionState,
) -> str:
    contract = completion_state.contract
    summary = contract.summary.strip() if contract is not None else ""
    evidence_paths = list(contract.evidence_paths) if contract is not None else []
    lines = [
        f"Managed study `{study_id}` already has an explicit study-level completion contract.",
        f"Study root: `{study_root}`",
        f"Completion summary: {summary}",
    ]
    if evidence_paths:
        lines.append("Evidence paths:")
        lines.extend(f"- `{item}`" for item in evidence_paths[:12])
    lines.append("Please record explicit quest-completion approval so the managed runtime can close this study cleanly.")
    return "\n".join(lines)


def _sync_study_completion(
    *,
    runtime_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    completion_state: StudyCompletionState,
    source: str,
) -> dict[str, object]:
    contract = completion_state.contract
    summary = contract.summary.strip() if contract is not None else ""
    approval_text = contract.user_approval_text.strip() if contract is not None else ""
    if not summary or not approval_text:
        raise ValueError("study completion sync requires summary and user approval text")
    return med_deepscientist_transport.sync_completion_with_approval(
        runtime_root=runtime_root,
        quest_id=quest_id,
        decision_request_payload={
            "kind": "decision_request",
            "message": _build_study_completion_request_message(
                study_id=study_id,
                study_root=study_root,
                completion_state=completion_state,
            ),
            "reply_mode": "blocking",
            "deliver_to_bound_conversations": False,
            "include_recent_inbound_messages": False,
            "reply_schema": {"decision_type": "quest_completion_approval"},
        },
        approval_text=approval_text,
        summary=summary,
        source=source,
    )
