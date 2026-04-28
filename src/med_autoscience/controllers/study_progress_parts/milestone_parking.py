from __future__ import annotations

from typing import Any

from .publication_runtime import _reason_label
from .shared_base import _non_empty_text


def finalize_milestone_parking_active(status: dict[str, Any]) -> bool:
    return (
        _non_empty_text(status.get("decision")) == "blocked"
        and _non_empty_text(status.get("reason")) == "quest_parked_on_unchanged_finalize_state"
    )


def finalize_milestone_parking_summary(status: dict[str, Any]) -> str:
    return _reason_label(status.get("reason")) or (
        "投稿包/人审里程碑已停驻；MAS 保持监督入口，等待显式 resume、外部投稿元数据或人工审阅输入。"
    )
