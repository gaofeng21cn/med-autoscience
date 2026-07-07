from __future__ import annotations

from typing import Any


def render_mcp_progress_stage(compact: dict[str, Any]) -> list[str]:
    current_stage = compact.get("current_stage") or "unknown"
    paper_stage = compact.get("paper_stage") or "unknown"
    state_label = str(compact.get("state_label") or "").strip()
    lines = [
        f"- 用户可见状态: {state_label or current_stage}",
        f"- writer_state: `{compact.get('writer_state') or current_stage}`",
        f"- actual_write_active: `{compact.get('actual_write_active')}`",
        f"- package_delivered: `{compact.get('package_delivered')}`",
        f"- user_next: `{compact.get('user_next') or 'unknown'}`",
        f"- 论文阶段: `{paper_stage}`",
    ]
    stage_summary = str(compact.get("state_summary") or compact.get("current_stage_summary") or "").strip()
    if stage_summary:
        lines.append(f"- 状态摘要: {stage_summary}")
    paper_summary = str(compact.get("paper_stage_summary") or "").strip()
    if paper_summary:
        lines.append(f"- 论文摘要: {paper_summary}")
    return lines
