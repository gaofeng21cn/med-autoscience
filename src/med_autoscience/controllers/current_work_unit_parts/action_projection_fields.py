from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def action_type(action: Mapping[str, Any]) -> str | None:
    return _text(action.get("action_type")) or _first_text(_text_items(action.get("allowed_actions")))


def work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return (
            _text(value.get("unit_id"))
            or _text(value.get("work_unit_id"))
            or _text(value.get("id"))
            or _text(value.get("ref"))
        )
    return _text(value)


def work_unit_fingerprint(
    action: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )


def action_fingerprint(
    action: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return (
        _text(action.get("action_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(action.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )


def input_refs(action: Mapping[str, Any], source_refs: Sequence[str]) -> list[str]:
    refs = list(source_refs)
    for key in (
        "source_ref",
        "latest_owner_answer_ref",
        "dispatch_path",
        "request_ref",
        "stage_packet_ref",
    ):
        if ref := _text(action.get(key)):
            refs.append(ref)
    refs.extend(_text_items(action.get("input_refs")))
    refs.extend(_text_items(action.get("source_refs")))
    return list(dict.fromkeys(refs))


def required_output_contract(action: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(action.get("required_output_contract"))
    if explicit:
        return explicit
    contract = {
        "owner_receipt_required": action.get("owner_receipt_required") is not False,
        "typed_blocker_accepted": True,
        "accepted_terminal_results": ["owner_receipt", "typed_blocker"],
        "required_delta_kind": _text(action.get("required_delta_kind")),
        "target_surface": _mapping(action.get("target_surface")) or None,
        "required_output_surface": _text(action.get("required_output_surface")),
    }
    return {key: value for key, value in contract.items() if value not in (None, "", [], {})}


def acceptance_refs(action: Mapping[str, Any]) -> list[str]:
    refs = _text_items(action.get("acceptance_refs"))
    refs.extend(_text_items(action.get("closeout_refs")))
    for key in ("owner_receipt_ref", "typed_blocker_ref", "source_ref"):
        if ref := _text(action.get(key)):
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _first_text(items: Sequence[str]) -> str | None:
    return items[0] if items else None


__all__ = [
    "acceptance_refs",
    "action_fingerprint",
    "action_type",
    "input_refs",
    "required_output_contract",
    "work_unit_fingerprint",
    "work_unit_id",
]
