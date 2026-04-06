from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_record import PublicationEvalRecord

__all__ = [
    "STABLE_PUBLICATION_EVAL_LATEST_RELATIVE_PATH",
    "read_publication_eval_latest",
    "resolve_publication_eval_latest_ref",
    "stable_publication_eval_latest_path",
]


STABLE_PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")


def stable_publication_eval_latest_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_PUBLICATION_EVAL_LATEST_RELATIVE_PATH).resolve()


def resolve_publication_eval_latest_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_publication_eval_latest_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("publication eval latest reader only accepts the eval-owned latest artifact")
    return stable_path


def read_publication_eval_latest(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    latest_path = resolve_publication_eval_latest_ref(study_root=study_root, ref=ref)
    payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"publication eval latest payload must be a JSON object: {latest_path}")
    return PublicationEvalRecord.from_payload(payload).to_dict()
