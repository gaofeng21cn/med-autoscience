from __future__ import annotations


def owner_token(value: object) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    compact = lowered.replace("/", "_").replace("-", "_")
    if compact in {"mas_controller", "publication_gate"}:
        return compact
    if "publication_gate" in compact or "publication gate" in lowered:
        return "publication_gate"
    if _mas_controller_paper_line_owner(lowered=lowered, compact=compact):
        return "mas_controller"
    return compact


def _mas_controller_paper_line_owner(*, lowered: str, compact: str) -> bool:
    has_mas_controller = (
        "mas_controller" in compact
        or "mas controller" in lowered
        or ("mas" in lowered and "controller" in lowered)
    )
    if not has_mas_controller:
        return False
    return (
        "paper_line" in compact
        or "paper line" in lowered
        or "paper/" in lowered
        or "controller_authorized" in compact
        or "controller-authorized" in lowered
    )


__all__ = ["owner_token"]
