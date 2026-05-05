from __future__ import annotations

from pathlib import Path as _Path

_PARTS = (
    "publication_and_submission.py",
    "publication_owner_currentness.py",
    "manual_finish_dominance.py",
    "runtime_events.py",
    "supervisor_state_overrides.py",
    "runtime_health_dominance.py",
    "status_and_decision.py",
)
for _part in _PARTS:
    _chunk_path = _Path(__file__).with_name("study_runtime_decision_parts") / _part
    exec(compile(_chunk_path.read_text(encoding="utf-8"), str(_chunk_path), "exec"), globals())

del _Path, _PARTS, _part, _chunk_path
