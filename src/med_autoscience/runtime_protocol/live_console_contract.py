from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import terminal_attach_gate


def authority() -> dict[str, bool | str]:
    return {
        "kind": "read_only_runtime_projection",
        "writes_authority_surface": False,
        "controller_action_execution_allowed": False,
        "quality_authority_allowed": False,
        "publication_authority_allowed": False,
        "submission_authority_allowed": False,
    }


def controller_action_links(*, study_id: str | None) -> list[dict[str, Any]]:
    suffix = f" --study-id {study_id}" if study_id else ""
    return [
        {
            "action": "inspect_progress",
            "label": "inspect progress",
            "command": f"medautosci study progress{suffix}",
            "direct_execution_allowed": False,
        },
        {
            "action": "request_reconcile",
            "label": "request reconcile through MAS controller",
            "command": f"medautosci runtime supervisor-reconcile{suffix}",
            "direct_execution_allowed": False,
        },
    ]


def terminal_attach_gate_status(
    *,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
) -> dict[str, Any]:
    return terminal_attach_gate.blocked_by_missing_terminal_input_owner(
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
    )


def source_refs(
    *,
    session: Mapping[str, Any],
    runtime_health_path: Path | None,
    runtime_supervision_path: Path | None,
    terminal: Sequence[Mapping[str, Any]],
    logs: Sequence[Mapping[str, Any]],
    artifact_delta: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for ref in session.get("evidence_refs") or []:
        if isinstance(ref, Mapping):
            refs.append(first_text(ref.get("path"), ref.get("source")) or "")
        elif isinstance(ref, str):
            refs.append(ref)
    refs.extend(str(Path(path).expanduser().resolve()) for path in (runtime_health_path, runtime_supervision_path) if path)
    refs.extend(first_source_ref(items) or "" for items in (terminal, logs))
    refs.append(artifact_source_ref(artifact_delta) or "")
    return [ref for ref in refs if ref]


def first_source_ref(value: object) -> str | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                text = first_text(item.get("source_ref"), item.get("path"), item.get("ref"))
                if text:
                    return text
    return None


def artifact_source_ref(value: object) -> str | None:
    payload = value if isinstance(value, Mapping) else {}
    refs = payload.get("refs")
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
        return first_text(*refs)
    return first_text(payload.get("source_ref"), payload.get("path"), payload.get("ref"))


def first_text(*values: object) -> str | None:
    for value in values:
        text = value.strip() if isinstance(value, str) else ""
        if text:
            return text
    return None


__all__ = [
    "artifact_source_ref",
    "authority",
    "controller_action_links",
    "first_source_ref",
    "source_refs",
    "terminal_attach_gate_status",
]
