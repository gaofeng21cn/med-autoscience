from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterable

from med_autoscience.profiles import WorkspaceProfile

SCHEMA_VERSION = 1
TASK_INTAKE_RELATIVE_ROOT = Path("artifacts") / "controller" / "task_intake"
STARTUP_BRIEF_BLOCK_BEGIN = "<!-- MAS_TASK_INTAKE:BEGIN -->"
STARTUP_BRIEF_BLOCK_END = "<!-- MAS_TASK_INTAKE:END -->"


def task_intake_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / TASK_INTAKE_RELATIVE_ROOT


def latest_task_intake_json_path(*, study_root: Path) -> Path:
    return task_intake_root(study_root=study_root) / "latest.json"


def latest_task_intake_markdown_path(*, study_root: Path) -> Path:
    return task_intake_root(study_root=study_root) / "latest.md"


def timestamped_task_intake_json_path(*, study_root: Path, slug: str) -> Path:
    return task_intake_root(study_root=study_root) / f"{slug}.json"


def timestamped_task_intake_markdown_path(*, study_root: Path, slug: str) -> Path:
    return task_intake_root(study_root=study_root) / f"{slug}.md"


def read_latest_task_intake(*, study_root: Path) -> dict[str, Any] | None:
    latest_path = latest_task_intake_json_path(study_root=study_root)
    if not latest_path.exists():
        return None
    payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"task intake payload must be a JSON object: {latest_path}")
    return payload


def render_task_intake_markdown(
    payload: dict[str, Any],
    *,
    entry_mode_label: Callable[[object], str],
    render_stop_loss_lines: Callable[[dict[str, Any]], list[str]],
    render_manual_hold_lines: Callable[[dict[str, Any]], list[str]],
    build_reviewer_revision_intake: Callable[[dict[str, Any]], dict[str, Any] | None],
    render_manuscript_fast_lane_lines: Callable[[dict[str, Any]], list[str]],
) -> str:
    lines = [
        "# Study Task Intake",
        "",
        f"- 当前 study: `{payload['study_id']}`",
        f"- 写入时间: `{payload['emitted_at']}`",
        f"- 当前入口模式: {entry_mode_label(payload.get('entry_mode'))}",
        f"- 当前投稿目标: `{payload.get('journal_target') or 'none'}`",
        "",
        "## 当前任务意图",
        "",
        str(payload.get("task_intent") or "").strip() or "未提供",
        "",
        "## 约束",
        "",
    ]
    constraints = list(payload.get("constraints") or [])
    if constraints:
        lines.extend(f"- {item}" for item in constraints)
    else:
        lines.append("- None")
    lines.extend(["", "## 证据边界", ""])
    evidence_boundary = list(payload.get("evidence_boundary") or [])
    if evidence_boundary:
        lines.extend(f"- {item}" for item in evidence_boundary)
    else:
        lines.append("- None")
    lines.extend(["", "## 可信输入", ""])
    trusted_inputs = list(payload.get("trusted_inputs") or [])
    if trusted_inputs:
        lines.extend(f"- {item}" for item in trusted_inputs)
    else:
        lines.append("- None")
    lines.extend(["", "## 参考文献", ""])
    reference_papers = list(payload.get("reference_papers") or [])
    if reference_papers:
        lines.extend(f"- {item}" for item in reference_papers)
    else:
        lines.append("- None")
    lines.extend(["", "## 首轮交付", ""])
    first_cycle_outputs = list(payload.get("first_cycle_outputs") or [])
    if first_cycle_outputs:
        lines.extend(f"- {item}" for item in first_cycle_outputs)
    else:
        lines.append("- None")
    revision_intake = build_reviewer_revision_intake(payload)
    lines.extend(render_stop_loss_lines(payload))
    lines.extend(render_manual_hold_lines(payload))
    if revision_intake is not None:
        lines.extend(["", "## Revision Intake Checklist", ""])
        for item in revision_intake["checklist_items"]:
            lines.append(f"- [{item['status']}] {item['label']}: {item['requirement']}")
        lines.extend(
            [
                "",
                "## Revision Handoff Constraint",
                "",
                "- 明确用户、导师或审稿稿件反馈会重新激活同一 study；旧 stopped/submission-ready/finalize 状态不能作为前台直接修改 `manuscript/current_package/` 的许可。",
                "- 先通过 MAS-owned launch/resume 接管 canonical paper surface，再重新生成 `manuscript/current_package/`。",
                "- 紧急 foreground overlay 只能作为 unreconciled handoff 标注，不能作为完成态或 MAS 已修订完成的证据。",
            ]
        )
    lines.extend(render_manuscript_fast_lane_lines(payload))
    lines.append("")
    return "\n".join(lines)


def render_task_intake_runtime_context(
    payload: dict[str, Any],
    *,
    normalized_strings: Callable[[Iterable[object]], list[str]],
    non_empty_text: Callable[[object], str | None],
    build_reviewer_revision_intake: Callable[[dict[str, Any]], dict[str, Any] | None],
    render_manual_hold_lines: Callable[[dict[str, Any]], list[str]],
    render_stop_loss_lines: Callable[[dict[str, Any]], list[str]],
    render_manuscript_fast_lane_lines: Callable[[dict[str, Any]], list[str]],
) -> str:
    lines = [
        f"Task intent: {payload.get('task_intent') or '未提供'}",
        f"Entry mode: {payload.get('entry_mode') or 'full_research'}",
    ]
    journal_target = non_empty_text(payload.get("journal_target"))
    if journal_target is not None:
        lines.append(f"Journal target: {journal_target}")
    constraints = normalized_strings(payload.get("constraints") or [])
    if constraints:
        lines.append("Constraints:")
        lines.extend(f"- {item}" for item in constraints)
    evidence_boundary = normalized_strings(payload.get("evidence_boundary") or [])
    if evidence_boundary:
        lines.append("Evidence boundary:")
        lines.extend(f"- {item}" for item in evidence_boundary)
    trusted_inputs = normalized_strings(payload.get("trusted_inputs") or [])
    if trusted_inputs:
        lines.append("Trusted inputs:")
        lines.extend(f"- {item}" for item in trusted_inputs)
    first_cycle_outputs = normalized_strings(payload.get("first_cycle_outputs") or [])
    if first_cycle_outputs:
        lines.append("First-cycle outputs:")
        lines.extend(f"- {item}" for item in first_cycle_outputs)
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        checklist = ", ".join(item["id"] for item in revision_intake["checklist_items"])
        lines.extend(
            [
                "Revision intake: reviewer_revision",
                f"Revision checklist: {checklist}",
                "Reviewer/user manuscript feedback reactivates the same study line.",
                "A stopped milestone state is not foreground current_package edit permission.",
                "OPL hydrates/resumes the provider attempt from MAS owner refs before MAS domain handlers edit canonical paper sources.",
                "Regenerate manuscript/current_package from canonical authority after revision.",
            ]
        )
    lines.extend(render_manual_hold_lines(payload))
    lines.extend(render_stop_loss_lines(payload))
    lines.extend(render_manuscript_fast_lane_lines(payload))
    return "\n".join(lines)


def render_startup_brief_task_block(
    payload: dict[str, Any],
    *,
    render_markdown: Callable[[dict[str, Any]], str],
) -> str:
    body = render_markdown(payload).strip()
    return f"{STARTUP_BRIEF_BLOCK_BEGIN}\n{body}\n{STARTUP_BRIEF_BLOCK_END}"


def upsert_startup_brief_task_block(
    *,
    existing_text: str,
    payload: dict[str, Any],
    render_markdown: Callable[[dict[str, Any]], str],
) -> str:
    existing = str(existing_text or "").strip()
    replacement = render_startup_brief_task_block(payload, render_markdown=render_markdown)
    if STARTUP_BRIEF_BLOCK_BEGIN in existing and STARTUP_BRIEF_BLOCK_END in existing:
        prefix, rest = existing.split(STARTUP_BRIEF_BLOCK_BEGIN, 1)
        _, suffix = rest.split(STARTUP_BRIEF_BLOCK_END, 1)
        rebuilt = prefix.rstrip()
        if rebuilt:
            rebuilt += "\n\n"
        rebuilt += replacement
        suffix = suffix.strip()
        if suffix:
            rebuilt += f"\n\n{suffix}"
        return rebuilt.strip() + "\n"
    if not existing:
        existing = "# Startup brief"
    return f"{existing.rstrip()}\n\n{replacement}\n"


def write_task_intake(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    entry_mode: str,
    task_intent: str,
    emitted_at: str,
    slug: str,
    non_empty_text: Callable[[object], str | None],
    normalized_strings: Callable[[Iterable[object]], list[str]],
    render_markdown: Callable[[dict[str, Any]], str],
    build_stop_loss_intake: Callable[[dict[str, Any]], dict[str, Any] | None],
    build_manual_hold_intake: Callable[[dict[str, Any]], dict[str, Any] | None],
    build_reviewer_revision_intake: Callable[[dict[str, Any]], dict[str, Any] | None],
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
    task_intake_kind: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": f"study-task::{study_id}::{slug}",
        "emitted_at": emitted_at,
        "study_id": study_id,
        "study_root": str(resolved_study_root),
        "entry_mode": non_empty_text(entry_mode) or "full_research",
        "task_intake_kind": non_empty_text(task_intake_kind),
        "task_intent": non_empty_text(task_intent) or "",
        "journal_target": non_empty_text(journal_target),
        "constraints": normalized_strings(constraints),
        "evidence_boundary": normalized_strings(evidence_boundary),
        "trusted_inputs": normalized_strings(trusted_inputs),
        "reference_papers": normalized_strings(reference_papers),
        "first_cycle_outputs": normalized_strings(first_cycle_outputs),
        "workspace_locator": {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "studies_root": str(profile.studies_root),
            "runtime_root": str(profile.runtime_root),
        },
        "domain_authority_handoff_contract": {
            "opl_runtime_ref": profile.opl_runtime_ref,
            "runtime_owner": "one-person-lab",
            "runtime_root": str(profile.runtime_root),
            "hermes_agent_repo_root": str(profile.hermes_agent_repo_root) if profile.hermes_agent_repo_root else None,
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "return_surface_contract": {
            "opl_runtime_owner_handoff_path": str(
                resolved_study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
            ),
            "domain_health_diagnostic_path": str(
                resolved_study_root / "artifacts" / "domain_health_diagnostic" / "latest.json"
            ),
            "publication_eval_path": str(
                resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
            ),
            "controller_decision_path": str(
                resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
            ),
        },
    }
    stop_loss_intake = build_stop_loss_intake(payload)
    if stop_loss_intake is not None:
        payload["stop_loss_intake"] = stop_loss_intake
    manual_hold_intake = build_manual_hold_intake(payload)
    if manual_hold_intake is not None:
        payload["manual_hold_intake"] = manual_hold_intake
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        payload["revision_intake"] = revision_intake
    latest_json_path = latest_task_intake_json_path(study_root=resolved_study_root)
    latest_markdown_path = latest_task_intake_markdown_path(study_root=resolved_study_root)
    timestamped_json_path = timestamped_task_intake_json_path(study_root=resolved_study_root, slug=slug)
    timestamped_markdown_path = timestamped_task_intake_markdown_path(study_root=resolved_study_root, slug=slug)
    markdown = render_markdown(payload)
    for path, content in (
        (timestamped_json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        (latest_json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        (timestamped_markdown_path, markdown + "\n"),
        (latest_markdown_path, markdown + "\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {
        **payload,
        "artifact_refs": {
            "latest_json": str(latest_json_path),
            "latest_markdown": str(latest_markdown_path),
            "timestamped_json": str(timestamped_json_path),
            "timestamped_markdown": str(timestamped_markdown_path),
        },
    }


__all__ = [
    "SCHEMA_VERSION",
    "STARTUP_BRIEF_BLOCK_BEGIN",
    "STARTUP_BRIEF_BLOCK_END",
    "TASK_INTAKE_RELATIVE_ROOT",
    "latest_task_intake_json_path",
    "latest_task_intake_markdown_path",
    "read_latest_task_intake",
    "render_startup_brief_task_block",
    "render_task_intake_markdown",
    "render_task_intake_runtime_context",
    "task_intake_root",
    "timestamped_task_intake_json_path",
    "timestamped_task_intake_markdown_path",
    "upsert_startup_brief_task_block",
    "write_task_intake",
]
