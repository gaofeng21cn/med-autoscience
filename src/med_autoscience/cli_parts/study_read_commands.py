from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable


def handle_study_read_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    load_profile: Callable[[str], Any],
    serialize_study_runtime_result: Callable[[Any], dict[str, Any]],
    study_progress: Any,
    study_runtime_router: Any,
    study_state_matrix: Any,
    study_truth_kernel: Any,
    runtime_health_kernel: Any,
) -> int | None:
    if args.command == "progress-projection":
        _require_one_study_ref(args, parser)
        profile = load_profile(args.profile)
        result = study_runtime_router.progress_projection(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
        )
        print(json.dumps(serialize_study_runtime_result(result), ensure_ascii=False, indent=2))
        return 0

    if args.command == "study-progress":
        _require_one_study_ref(args, parser)
        profile = load_profile(args.profile)
        result = study_progress.read_study_progress(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(study_progress.render_study_progress_markdown(result), end="")
        return 0

    if args.command == "study-state-matrix":
        profile = load_profile(args.profile)
        result = study_state_matrix.build_study_state_matrix(
            profile=profile,
            study_runtime_router=study_runtime_router,
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
            study_runtime_router=study_runtime_router,
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
            study_runtime_router=study_runtime_router,
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
    study_runtime_router: Any,
    serialize_study_runtime_result: Callable[[Any], dict[str, Any]],
) -> dict[str, Any]:
    status = study_runtime_router.progress_projection(
        profile=profile,
        study_id=args.study_id,
        study_root=Path(args.study_root) if args.study_root else None,
        entry_mode=args.entry_mode,
    )
    return serialize_study_runtime_result(status)


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
