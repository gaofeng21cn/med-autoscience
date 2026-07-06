from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

FORBIDDEN_MANUSCRIPT_TERMS = (
    "MAS",
    "AI reviewer",
    "verified outputs",
    "accepted records",
    "source gaps",
    "submission readiness",
    "repair note",
    "manuscript repair",
    "quality repair",
    "publication gate",
    "controller",
    "semantic-audit",
    "Revision analyses were implemented",
    "Table 1 is",
    "Table 2 is",
    "Figure 4 supports",
    "Guideline-linked",
)

def _contains_forbidden_manuscript_terms(text: str) -> bool:
    lowered = text.lower()
    for term in FORBIDDEN_MANUSCRIPT_TERMS:
        escaped = re.escape(term.lower())
        if re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", lowered):
            return True
    return False

def _write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else f"{text}\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True

def _write_json_if_changed(path: Path, payload: Mapping[str, Any]) -> bool:
    rendered = json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True

def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}

def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
