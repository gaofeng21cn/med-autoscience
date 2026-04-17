from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "STABLE_STUDY_CHARTER_RELATIVE_PATH",
    "materialize_study_charter",
    "read_study_charter",
    "resolve_study_charter_ref",
    "stable_study_charter_path",
]


STABLE_STUDY_CHARTER_RELATIVE_PATH = Path("artifacts/controller/study_charter.json")


def stable_study_charter_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_STUDY_CHARTER_RELATIVE_PATH).resolve()


def _non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def resolve_study_charter_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_study_charter_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("study charter reader only accepts the stable controller artifact")
    return stable_path


def read_study_charter(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    charter_path = resolve_study_charter_ref(study_root=study_root, ref=ref)
    payload = json.loads(charter_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"study charter payload must be a JSON object: {charter_path}")
    return payload


def materialize_study_charter(
    *,
    study_root: Path,
    study_id: str,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
    required_first_anchor: str | None = None,
) -> dict[str, str]:
    charter_path = stable_study_charter_path(study_root=study_root)
    title = _non_empty_string(study_payload.get("title")) or study_id
    publication_objective = (
        _non_empty_string(study_payload.get("primary_question"))
        or _non_empty_string(study_payload.get("paper_framing_summary"))
        or title
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "charter_id": f"charter::{study_id}::v1",
        "study_id": study_id,
        "title": title,
        "publication_objective": publication_objective,
        "paper_framing_summary": _non_empty_string(study_payload.get("paper_framing_summary")),
        "minimum_sci_ready_evidence_package": _string_list(
            study_payload.get("minimum_sci_ready_evidence_package")
        ),
        "scientific_followup_questions": _string_list(study_payload.get("scientific_followup_questions")),
        "explanation_targets": _string_list(study_payload.get("explanation_targets")),
        "manuscript_conclusion_redlines": _string_list(study_payload.get("manuscript_conclusion_redlines")),
        "autonomy_envelope": {
            "decision_policy": _non_empty_string(execution.get("decision_policy")) or "autonomous",
            "launch_profile": _non_empty_string(execution.get("launch_profile")) or "continue_existing_state",
            "required_first_anchor": _non_empty_string(required_first_anchor),
        },
    }
    charter_path.parent.mkdir(parents=True, exist_ok=True)
    charter_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "charter_id": str(payload["charter_id"]),
        "artifact_path": str(charter_path),
    }
