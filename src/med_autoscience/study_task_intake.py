from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.profiles import WorkspaceProfile

SCHEMA_VERSION = 1
TASK_INTAKE_RELATIVE_ROOT = Path("artifacts") / "controller" / "task_intake"
STARTUP_BRIEF_BLOCK_BEGIN = "<!-- MAS_TASK_INTAKE:BEGIN -->"
STARTUP_BRIEF_BLOCK_END = "<!-- MAS_TASK_INTAKE:END -->"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_strings(values: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return normalized


def task_intake_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / TASK_INTAKE_RELATIVE_ROOT


def latest_task_intake_json_path(*, study_root: Path) -> Path:
    return task_intake_root(study_root=study_root) / "latest.json"


def latest_task_intake_markdown_path(*, study_root: Path) -> Path:
    return task_intake_root(study_root=study_root) / "latest.md"


def _timestamped_task_intake_json_path(*, study_root: Path, slug: str) -> Path:
    return task_intake_root(study_root=study_root) / f"{slug}.json"


def _timestamped_task_intake_markdown_path(*, study_root: Path, slug: str) -> Path:
    return task_intake_root(study_root=study_root) / f"{slug}.md"


def read_latest_task_intake(*, study_root: Path) -> dict[str, Any] | None:
    latest_path = latest_task_intake_json_path(study_root=study_root)
    if not latest_path.exists():
        return None
    payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"task intake payload must be a JSON object: {latest_path}")
    return payload


def render_task_intake_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Study Task Intake",
        "",
        f"- study_id: `{payload['study_id']}`",
        f"- emitted_at: `{payload['emitted_at']}`",
        f"- entry_mode: `{payload.get('entry_mode') or 'full_research'}`",
        f"- journal_target: `{payload.get('journal_target') or 'none'}`",
        "",
        "## Task Intent",
        "",
        str(payload.get("task_intent") or "").strip() or "未提供",
        "",
        "## Constraints",
        "",
    ]
    constraints = list(payload.get("constraints") or [])
    if constraints:
        lines.extend(f"- {item}" for item in constraints)
    else:
        lines.append("- None")
    lines.extend(["", "## Evidence Boundary", ""])
    evidence_boundary = list(payload.get("evidence_boundary") or [])
    if evidence_boundary:
        lines.extend(f"- {item}" for item in evidence_boundary)
    else:
        lines.append("- None")
    lines.extend(["", "## Trusted Inputs", ""])
    trusted_inputs = list(payload.get("trusted_inputs") or [])
    if trusted_inputs:
        lines.extend(f"- {item}" for item in trusted_inputs)
    else:
        lines.append("- None")
    lines.extend(["", "## Reference Papers", ""])
    reference_papers = list(payload.get("reference_papers") or [])
    if reference_papers:
        lines.extend(f"- {item}" for item in reference_papers)
    else:
        lines.append("- None")
    lines.extend(["", "## First-Cycle Outputs", ""])
    first_cycle_outputs = list(payload.get("first_cycle_outputs") or [])
    if first_cycle_outputs:
        lines.extend(f"- {item}" for item in first_cycle_outputs)
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_task_intake_runtime_context(payload: dict[str, Any]) -> str:
    lines = [
        f"Task intent: {payload.get('task_intent') or '未提供'}",
        f"Entry mode: {payload.get('entry_mode') or 'full_research'}",
    ]
    journal_target = _non_empty_text(payload.get("journal_target"))
    if journal_target is not None:
        lines.append(f"Journal target: {journal_target}")
    constraints = _normalized_strings(payload.get("constraints") or [])
    if constraints:
        lines.append("Constraints:")
        lines.extend(f"- {item}" for item in constraints)
    evidence_boundary = _normalized_strings(payload.get("evidence_boundary") or [])
    if evidence_boundary:
        lines.append("Evidence boundary:")
        lines.extend(f"- {item}" for item in evidence_boundary)
    trusted_inputs = _normalized_strings(payload.get("trusted_inputs") or [])
    if trusted_inputs:
        lines.append("Trusted inputs:")
        lines.extend(f"- {item}" for item in trusted_inputs)
    first_cycle_outputs = _normalized_strings(payload.get("first_cycle_outputs") or [])
    if first_cycle_outputs:
        lines.append("First-cycle outputs:")
        lines.extend(f"- {item}" for item in first_cycle_outputs)
    return "\n".join(lines)


def render_startup_brief_task_block(payload: dict[str, Any]) -> str:
    body = render_task_intake_markdown(payload).strip()
    return f"{STARTUP_BRIEF_BLOCK_BEGIN}\n{body}\n{STARTUP_BRIEF_BLOCK_END}"


def upsert_startup_brief_task_block(*, existing_text: str, payload: dict[str, Any]) -> str:
    existing = str(existing_text or "").strip()
    replacement = render_startup_brief_task_block(payload)
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
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
) -> dict[str, Any]:
    emitted_at = _utc_now()
    slug = _timestamp_slug()
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": f"study-task::{study_id}::{slug}",
        "emitted_at": emitted_at,
        "study_id": study_id,
        "study_root": str(resolved_study_root),
        "entry_mode": _non_empty_text(entry_mode) or "full_research",
        "task_intent": _non_empty_text(task_intent) or "",
        "journal_target": _non_empty_text(journal_target),
        "constraints": _normalized_strings(constraints),
        "evidence_boundary": _normalized_strings(evidence_boundary),
        "trusted_inputs": _normalized_strings(trusted_inputs),
        "reference_papers": _normalized_strings(reference_papers),
        "first_cycle_outputs": _normalized_strings(first_cycle_outputs),
        "workspace_locator": {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "studies_root": str(profile.studies_root),
            "runtime_root": str(profile.runtime_root),
        },
        "runtime_session_contract": {
            "managed_runtime_backend_id": profile.managed_runtime_backend_id,
            "runtime_root": str(profile.runtime_root),
            "hermes_agent_repo_root": str(profile.hermes_agent_repo_root) if profile.hermes_agent_repo_root else None,
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "return_surface_contract": {
            "runtime_supervision_path": str(
                resolved_study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
            ),
            "publication_eval_path": str(
                resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
            ),
            "controller_decision_path": str(
                resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
            ),
        },
    }
    latest_json_path = latest_task_intake_json_path(study_root=resolved_study_root)
    latest_markdown_path = latest_task_intake_markdown_path(study_root=resolved_study_root)
    timestamped_json_path = _timestamped_task_intake_json_path(study_root=resolved_study_root, slug=slug)
    timestamped_markdown_path = _timestamped_task_intake_markdown_path(study_root=resolved_study_root, slug=slug)
    markdown = render_task_intake_markdown(payload)
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
