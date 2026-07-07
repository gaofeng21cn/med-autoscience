from __future__ import annotations

from typing import Any


_DEFAULT_REVIEWER_HASH = "0" * 64


def default_visual_audit_review() -> dict[str, Any]:
    return {
        "audit_mode": "vlm_visual_verification",
        "reviewer": {
            "provider": "mas-display-pack-agent",
            "model": "agent-structured-visual-audit-receipt",
            "prompt_hash": _DEFAULT_REVIEWER_HASH,
        },
        "findings": [],
        "final_status": "clear",
    }
