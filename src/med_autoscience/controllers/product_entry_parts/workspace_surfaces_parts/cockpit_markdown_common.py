from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.product_entry_parts.shared_labels import _non_empty_text


def readiness_action_card_label(card: Mapping[str, Any]) -> str:
    status = _non_empty_text(card.get("status"))
    action_result = dict(card.get("action_result") or {})
    missing_reason = _non_empty_text(card.get("missing_reason")) or _non_empty_text(
        action_result.get("missing_reason")
    )
    suffix = ""
    if status and missing_reason:
        suffix = f" [{status} / {missing_reason}]"
    elif status:
        suffix = f" [{status}]"
    label = card.get("display_label") or card.get("label") or card.get("title")
    return f"{label}{suffix}: {card.get('summary')}"
