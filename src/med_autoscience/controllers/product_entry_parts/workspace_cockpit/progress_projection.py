from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.product_entry_parts.shared_labels import _non_empty_text


USER_VISIBLE_REQUIRED_KEYS = ("writer_state", "user_next", "reason")


def study_progress_user_visible_projection(progress_payload: Mapping[str, Any]) -> dict[str, Any]:
    projection = progress_payload.get("user_visible_projection")
    if not isinstance(projection, Mapping):
        return {}
    if projection.get("schema_version") != 2:
        return {}
    if any(_non_empty_text(projection.get(key)) is None for key in USER_VISIBLE_REQUIRED_KEYS):
        return {}
    return dict(projection)


def user_visible_field(
    *,
    user_visible_projection: Mapping[str, Any],
    key: str,
) -> Any:
    return user_visible_projection.get(key)


def user_visible_list(
    *,
    user_visible_projection: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = user_visible_field(user_visible_projection=user_visible_projection, key=key)
    return list(value or []) if isinstance(value, list) else []
