from __future__ import annotations

from pathlib import Path as _Path

_PARTS = (
    "state_and_study_items.py",
    "cockpit_payload.py",
    "cockpit_markdown.py",
    "launch_surface.py",
)
for _part in _PARTS:
    _chunk_path = _Path(__file__).with_name("workspace_surfaces_parts") / _part
    exec(compile(_chunk_path.read_text(encoding="utf-8"), str(_chunk_path), "exec"), globals())

del _Path, _PARTS, _part, _chunk_path

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
