from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

_PROGRESS_FIRST_STATUS_KEYS = (
    "current_stage",
    "current_stage_summary",
    "current_stage_label",
    "status_summary",
    "paper_stage",
    "paper_stage_summary",
    "current_blockers",
    "latest_events",
    "next_system_action",
    "next_step",
    "needs_user_decision",
    "needs_physician_decision",
    "progress_freshness",
    "paper_progress_delta",
    "platform_repair_delta",
    "intervention_lane",
    "operator_verdict",
    "operator_status_card",
    "quality_closure_truth",
    "quality_execution_lane",
    "quality_review_loop",
    "supervision",
    "continuation_state",
    "study_macro_state",
    "ai_repair_lifecycle",
    "progress_first_monitoring_summary",
)

_USER_VISIBLE_STATUS_KEYS = (
    "state",
    "writer_state",
    "user_next",
    "reason",
    "conflict_reason",
    "package_delivered",
    "actual_write_active",
    "meaningful_artifact_delta",
    "next_owner",
    "why_not_progressing",
    "user_action_required",
    "state_label",
    "state_summary",
    "current_stage",
    "current_stage_label",
    "current_stage_summary",
    "status_summary",
    "paper_stage",
    "paper_stage_summary",
    "current_blockers",
    "next_system_action",
    "next_step",
    "needs_user_decision",
    "needs_physician_decision",
)


def handle_study_read_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    load_profile: Callable[[str], Any],
    serialize_study_runtime_result: Callable[[Any], dict[str, Any]],
    study_progress: Any,
    domain_status_projection: Any,
    study_state_matrix: Any,
    study_truth_kernel: Any,
    runtime_health_kernel: Any,
) -> int | None:
    if args.command == "study-progress":
        _require_one_study_ref(args, parser)
        profile = load_profile(args.profile)
        result = study_progress.read_study_progress(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
        if args.format == "json":
            payload = serialize_study_runtime_result(result)
            print(json.dumps(_progress_first_status_payload(payload), ensure_ascii=False, indent=2))
        else:
            print(study_progress.render_study_progress_markdown(result), end="")
        return 0

    if args.command == "study-state-matrix":
        profile = load_profile(args.profile)
        result = study_state_matrix.build_study_state_matrix(
            profile=profile,
            domain_status_projection=domain_status_projection,
            study_ids=tuple(args.studies or ()),
            entry_mode=args.entry_mode,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(study_state_matrix.render_study_state_matrix_markdown(result), end="")
        return 0

    if args.command == "reconcile-study-truth":
        _require_one_study_ref(args, parser)
        profile = load_profile(args.profile)
        status_payload = _read_status_payload(
            args=args,
            profile=profile,
            domain_status_projection=domain_status_projection,
            serialize_study_runtime_result=serialize_study_runtime_result,
        )
        resolved_study_id, resolved_study_root, _ = _resolved_study_refs(
            args=args,
            status_payload=status_payload,
            parser=parser,
            command_label="reconcile-truth",
            require_quest=False,
        )
        result = study_truth_kernel.reconcile_truth_snapshot_from_status_payload(
            study_root=Path(resolved_study_root),
            study_id=resolved_study_id,
            status_payload=status_payload,
            recorded_at=_recorded_at(status_payload),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "reconcile-runtime-health":
        _require_one_study_ref(args, parser)
        profile = load_profile(args.profile)
        status_payload = _read_status_payload(
            args=args,
            profile=profile,
            domain_status_projection=domain_status_projection,
            serialize_study_runtime_result=serialize_study_runtime_result,
        )
        resolved_study_id, resolved_study_root, resolved_quest_id = _resolved_study_refs(
            args=args,
            status_payload=status_payload,
            parser=parser,
            command_label="reconcile-runtime-health",
            require_quest=True,
        )
        result = runtime_health_kernel.reconcile_runtime_health_snapshot_from_status_payload(
            study_root=Path(resolved_study_root),
            study_id=resolved_study_id,
            quest_id=resolved_quest_id,
            status_payload=status_payload,
            recorded_at=_recorded_at(status_payload),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    return None


def _require_one_study_ref(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if bool(args.study_id) == bool(args.study_root):
        parser.error("Specify exactly one of --study-id or --study-root")


def _read_status_payload(
    *,
    args: argparse.Namespace,
    profile: Any,
    domain_status_projection: Any,
    serialize_study_runtime_result: Callable[[Any], dict[str, Any]],
) -> dict[str, Any]:
    status = domain_status_projection.progress_projection(
        profile=profile,
        study_id=args.study_id,
        study_root=Path(args.study_root) if args.study_root else None,
        entry_mode=args.entry_mode,
        sync_runtime_summary=False,
    )
    return serialize_study_runtime_result(status)


def _progress_first_status_payload(
    payload: dict[str, Any],
    *,
    preserve_runtime_reason: bool = False,
) -> dict[str, Any]:
    progress_projection = payload.get("progress_projection")
    source_payload = progress_projection if isinstance(progress_projection, dict) else payload
    user_visible = source_payload.get("user_visible_projection")
    if not isinstance(progress_projection, dict) and not _is_current_user_visible_projection(user_visible):
        return payload
    updated = dict(payload)
    for key in _PROGRESS_FIRST_STATUS_KEYS:
        if key in source_payload:
            updated[key] = source_payload[key]
    if _is_current_user_visible_projection(user_visible):
        updated["user_visible_projection"] = dict(user_visible)
        for key in _USER_VISIBLE_STATUS_KEYS:
            if preserve_runtime_reason and key == "reason":
                continue
            if key in user_visible:
                updated[key] = user_visible[key]
    updated["progress_first_projection"] = {
        "surface_kind": "cli_progress_projection_progress_first_view",
        "source": (
            "progress_projection.user_visible_projection"
            if isinstance(progress_projection, dict)
            else "user_visible_projection"
        ),
        "runtime_decision_field": "decision",
        "runtime_reason_field": "reason",
    }
    return updated


def _is_current_user_visible_projection(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("schema_version") != 2:
        return False
    return all(key in value for key in ("writer_state", "user_next", "reason", "state_label", "state_summary"))


def _resolved_study_refs(
    *,
    args: argparse.Namespace,
    status_payload: dict[str, Any],
    parser: argparse.ArgumentParser,
    command_label: str,
    require_quest: bool,
) -> tuple[str, str, str]:
    resolved_study_id = str(status_payload.get("study_id") or args.study_id or "").strip()
    resolved_study_root = str(status_payload.get("study_root") or args.study_root or "").strip()
    resolved_quest_id = str(status_payload.get("quest_id") or resolved_study_id or "").strip()
    if not resolved_study_id:
        parser.error(f"Unable to resolve study_id for {command_label}")
    if not resolved_study_root:
        parser.error(f"Unable to resolve study_root for {command_label}")
    if require_quest and not resolved_quest_id:
        parser.error(f"Unable to resolve quest_id for {command_label}")
    return resolved_study_id, resolved_study_root, resolved_quest_id


def _recorded_at(status_payload: dict[str, Any]) -> str:
    return str(status_payload.get("generated_at") or status_payload.get("recorded_at") or datetime.now(timezone.utc).isoformat())


__all__ = ["handle_study_read_command"]
