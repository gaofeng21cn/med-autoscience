from __future__ import annotations

from pathlib import Path
from typing import Any


FORBIDDEN_SYSTEM_PROMPT_SNIPPETS = (
    "Publication-grade figure refinement is recommended with AutoFigure-Edit",
)


def runtime_system_prompt_path(*, runtime_root: Path) -> Path:
    return runtime_root / ".codex" / "prompts" / "system.md"


def sanitize_runtime_system_prompt(*, runtime_root: Path) -> dict[str, Any]:
    prompt_path = runtime_system_prompt_path(runtime_root=runtime_root)
    if not prompt_path.exists():
        return {
            "path": str(prompt_path),
            "exists": False,
            "action": "missing",
            "removed_line_count": 0,
        }

    original_text = prompt_path.read_text(encoding="utf-8")
    original_lines = original_text.splitlines()
    kept_lines = [
        line
        for line in original_lines
        if not any(snippet in line for snippet in FORBIDDEN_SYSTEM_PROMPT_SNIPPETS)
    ]
    removed_line_count = len(original_lines) - len(kept_lines)
    if removed_line_count:
        sanitized_text = "\n".join(kept_lines)
        if original_text.endswith("\n"):
            sanitized_text += "\n"
        prompt_path.write_text(sanitized_text, encoding="utf-8")

    return {
        "path": str(prompt_path),
        "exists": True,
        "action": "sanitized" if removed_line_count else "unchanged",
        "removed_line_count": removed_line_count,
    }


def audit_runtime_system_prompt(*, runtime_root: Path) -> dict[str, Any]:
    prompt_path = runtime_system_prompt_path(runtime_root=runtime_root)
    if not prompt_path.exists():
        return {
            "path": str(prompt_path),
            "exists": False,
            "ready": True,
            "violations": [],
        }

    prompt_text = prompt_path.read_text(encoding="utf-8")
    violations = [snippet for snippet in FORBIDDEN_SYSTEM_PROMPT_SNIPPETS if snippet in prompt_text]
    return {
        "path": str(prompt_path),
        "exists": True,
        "ready": not violations,
        "violations": violations,
    }
