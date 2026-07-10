from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def paper_mission_domain_handler_dispatch_receipt(
    *,
    task: dict[str, Any],
    task_path: Path,
    load_profile: Callable[[str | Path], Any],
    build_readback: Callable[..., dict[str, Any]],
    start_or_resume_task_kind: str,
    forbidden_authority_writes: tuple[str, ...],
    dispatch_execution_policy: Callable[[dict[str, Any]], str],
    recommended_domain_invocation: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    profile_ref = (
        payload.get("profile") or payload.get("profile_path") or payload.get("profile_ref")
    )
    if not profile_ref:
        return _dispatch_error(
            task=task,
            task_path=task_path,
            reason="missing_profile_ref",
            start_or_resume_task_kind=start_or_resume_task_kind,
        )
    study_id = str(payload.get("study_id") or "").strip()
    if not study_id:
        return _dispatch_error(
            task=task,
            task_path=task_path,
            reason="missing_study_id",
            start_or_resume_task_kind=start_or_resume_task_kind,
        )
    profile = load_profile(Path(str(profile_ref)))
    requested_command = _optional_text(payload.get("paper_mission_command"))
    dry_run = payload.get("dry_run") is True
    dispatch_command = _domain_handler_paper_mission_command(
        task=task,
        requested_command=requested_command,
        dry_run=dry_run,
        start_or_resume_task_kind=start_or_resume_task_kind,
    )
    readback = build_readback(
        profile=profile,
        profile_ref=Path(str(profile_ref)),
        study_id=study_id,
        paper_mission_command=dispatch_command,
        objective=_optional_text(payload.get("objective")),
        mission_id=_optional_text(payload.get("mission_id")),
        candidate=_optional_text(payload.get("candidate")),
        run_id=(
            _optional_text(payload.get("run_id"))
            or _default_domain_handler_drive_run_id(
                task=task,
                study_id=study_id,
                start_or_resume_task_kind=start_or_resume_task_kind,
            )
        ),
        submit_opl_runtime=(
            bool(payload.get("submit_opl_runtime"))
            if "submit_opl_runtime" in payload
            else None
        ),
        opl_bin=_optional_text(payload.get("opl_bin")),
        one_shot_migration=bool(payload.get("one_shot_migration", False)),
        study_progress_payload=_optional_text(payload.get("study_progress_payload")),
        runtime_readback_payload=_optional_text(payload.get("runtime_readback_payload")),
        output_root=_optional_text(payload.get("output_root")),
        dry_run=dry_run,
        source="domain-handler-dispatch",
    )
    return {
        "surface_kind": "mas_family_domain_handler_dispatch_receipt",
        "version": "mas-family-domain-handler.v1",
        "accepted": True,
        "task_id": str(task.get("task_id") or "unknown_task"),
        "task_kind": start_or_resume_task_kind,
        "source_task_ref": str(task_path),
        "forbidden_domain_truth_write": False,
        "dispatch": {
            "action_type": start_or_resume_task_kind,
            "action_intent": start_or_resume_task_kind,
            "study_id": study_id,
            "execution_policy": dispatch_execution_policy(readback),
            "recommended_domain_invocation": recommended_domain_invocation(
                profile_ref=profile_ref,
                study_id=study_id,
                readback=readback,
            ),
            "result": readback,
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority": False,
            "writes_runtime": False,
            "forbidden_authority_writes": list(forbidden_authority_writes),
        },
        "forbidden_write_guard_proof": {
            "result": "accepted_no_forbidden_writes",
            "task_kind": start_or_resume_task_kind,
            "requested_writes": [],
        },
    }


def _domain_handler_paper_mission_command(
    *,
    task: Mapping[str, Any],
    requested_command: str | None,
    dry_run: bool,
    start_or_resume_task_kind: str,
) -> str:
    if dry_run:
        return requested_command or "start"
    if _optional_text(task.get("task_kind")) == start_or_resume_task_kind:
        if requested_command in {None, "start", "resume"}:
            return "drive"
    return requested_command or "inspect"


def _default_domain_handler_drive_run_id(
    *,
    task: Mapping[str, Any],
    study_id: str,
    start_or_resume_task_kind: str,
) -> str | None:
    if _optional_text(task.get("task_kind")) != start_or_resume_task_kind:
        return None
    task_id = _optional_text(task.get("task_id")) or "paper-mission-start-or-resume"
    return f"domain-handler-dispatch-{_slug(study_id)}-{_slug(task_id)}"


def _dispatch_error(
    *,
    task: dict[str, Any],
    task_path: Path,
    reason: str,
    start_or_resume_task_kind: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_family_domain_handler_dispatch_receipt",
        "version": "mas-family-domain-handler.v1",
        "accepted": False,
        "task_id": str(task.get("task_id") or "unknown_task"),
        "task_kind": str(task.get("task_kind") or start_or_resume_task_kind),
        "source_task_ref": str(task_path),
        "reason": reason,
        "forbidden_domain_truth_write": False,
    }


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug[:64] or "paper-mission"


__all__ = ["paper_mission_domain_handler_dispatch_receipt"]
