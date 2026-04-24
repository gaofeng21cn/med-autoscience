from __future__ import annotations

from pathlib import Path as _Path

for _chunk_path in sorted((_Path(__file__).with_name("test_study_runtime_router_cases")).glob("chunk_*.py")):
    exec(compile(_chunk_path.read_text(encoding="utf-8"), str(_chunk_path), "exec"), globals())

del _Path, _chunk_path
