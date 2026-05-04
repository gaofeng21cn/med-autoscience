from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.delivery_visibility_projection import (
    build_study_delivery_inspection_projection,
    render_delivery_inspection_markdown_lines,
)
from med_autoscience.profiles import WorkspaceProfile


def read_delivery_inspection_projection(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
) -> dict[str, Any] | None:
    return build_study_delivery_inspection_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )


def attach_delivery_inspection_projection(
    payload: dict[str, Any],
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
) -> dict[str, Any]:
    delivery_inspection = read_delivery_inspection_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    if delivery_inspection is None:
        return payload
    updated = dict(payload)
    updated["delivery_inspection"] = delivery_inspection
    return updated


def append_delivery_inspection_markdown(
    lines: list[str],
    delivery_inspection: dict[str, Any],
) -> None:
    lines.extend(
        render_delivery_inspection_markdown_lines(
            delivery_inspection,
            heading="## Delivery Inspection",
        )
    )
