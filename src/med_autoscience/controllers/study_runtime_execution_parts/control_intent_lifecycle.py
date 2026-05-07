from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def lifecycle_for_authorization(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> dict[str, Any]:
    decision_emitted_at = _text(authorization_context.get("decision_emitted_at"))
    if decision_emitted_at is not None:
        return control_intent.lifecycle_state_since(
            study_root=study_root,
            identity=identity,
            recorded_at=decision_emitted_at,
        )
    return control_intent.lifecycle_state(study_root=study_root, identity=identity)
