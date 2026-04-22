from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
from med_autoscience import display_registry

matplotlib.use("Agg")

from ..shared import (
    _require_non_empty_string,
)


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def _validate_submission_graphical_abstract_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    catalog_id = _require_non_empty_string(payload.get("catalog_id"), label=f"{path.name} catalog_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")
    caption = _require_non_empty_string(payload.get("caption"), label=f"{path.name} caption")

    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} must contain a non-empty panels list")
    normalized_panels: list[dict[str, Any]] = []
    panel_ids: set[str] = set()
    for panel_index, panel in enumerate(panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} panels[{panel_index}].panel_id",
        )
        if panel_id in panel_ids:
            raise ValueError(f"{path.name} panels[{panel_index}].panel_id must be unique")
        panel_ids.add(panel_id)
        rows_payload = panel.get("rows")
        if not isinstance(rows_payload, list) or not rows_payload:
            raise ValueError(f"{path.name} panels[{panel_index}].rows must be a non-empty list")
        normalized_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows_payload):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name} panels[{panel_index}].rows[{row_index}] must be an object")
            cards_payload = row.get("cards")
            if not isinstance(cards_payload, list) or not cards_payload:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}].cards must be a non-empty list"
                )
            if len(cards_payload) > 2:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}] supports at most two cards"
                )
            normalized_cards: list[dict[str, Any]] = []
            card_ids: set[str] = set()
            for card_index, card in enumerate(cards_payload):
                if not isinstance(card, dict):
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}] must be an object"
                    )
                card_id = _require_non_empty_string(
                    card.get("card_id"),
                    label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id",
                )
                if card_id in card_ids:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id must be unique within the row"
                    )
                card_ids.add(card_id)
                accent_role = str(card.get("accent_role") or "neutral").strip().lower()
                if accent_role not in {"neutral", "primary", "secondary", "contrast", "audit"}:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].accent_role "
                        "must be one of neutral, primary, secondary, contrast, audit"
                    )
                normalized_cards.append(
                    {
                        "card_id": card_id,
                        "title": _require_non_empty_string(
                            card.get("title"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].title",
                        ),
                        "value": _require_non_empty_string(
                            card.get("value"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].value",
                        ),
                        "detail": str(card.get("detail") or "").strip(),
                        "accent_role": accent_role,
                    }
                )
            normalized_rows.append({"cards": normalized_cards})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": _require_non_empty_string(
                    panel.get("panel_label"),
                    label=f"{path.name} panels[{panel_index}].panel_label",
                ),
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} panels[{panel_index}].title",
                ),
                "subtitle": _require_non_empty_string(
                    panel.get("subtitle"),
                    label=f"{path.name} panels[{panel_index}].subtitle",
                ),
                "rows": normalized_rows,
            }
        )

    footer_pills_payload = payload.get("footer_pills") or []
    if not isinstance(footer_pills_payload, list):
        raise ValueError(f"{path.name} footer_pills must be a list when provided")
    normalized_footer_pills: list[dict[str, Any]] = []
    pill_ids: set[str] = set()
    for pill_index, pill in enumerate(footer_pills_payload):
        if not isinstance(pill, dict):
            raise ValueError(f"{path.name} footer_pills[{pill_index}] must be an object")
        pill_id = _require_non_empty_string(
            pill.get("pill_id"),
            label=f"{path.name} footer_pills[{pill_index}].pill_id",
        )
        if pill_id in pill_ids:
            raise ValueError(f"{path.name} footer_pills[{pill_index}].pill_id must be unique")
        pill_ids.add(pill_id)
        panel_id = _require_non_empty_string(
            pill.get("panel_id"),
            label=f"{path.name} footer_pills[{pill_index}].panel_id",
        )
        if panel_id not in panel_ids:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].panel_id must reference a declared panel"
            )
        style_role = str(pill.get("style_role") or "secondary").strip().lower()
        if style_role not in {"primary", "secondary", "contrast", "audit", "neutral"}:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].style_role must be one of primary, secondary, contrast, audit, neutral"
            )
        normalized_footer_pills.append(
            {
                "pill_id": pill_id,
                "panel_id": panel_id,
                "label": _require_non_empty_string(
                    pill.get("label"),
                    label=f"{path.name} footer_pills[{pill_index}].label",
                ),
                "style_role": style_role,
            }
        )

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "submission_companion").strip() or "submission_companion",
        "panels": normalized_panels,
        "footer_pills": normalized_footer_pills,
    }


