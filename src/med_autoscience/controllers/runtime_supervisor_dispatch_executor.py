from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import repeat_suppression
from med_autoscience.runtime_protocol import runtime_lifecycle_store

from . import runtime_dispatch_cost
from . import ai_reviewer_publication_eval_workflow, gate_clearing_batch, publication_gate, quest_hydration, study_runtime_router
from .runtime_supervisor_scan import SUPERVISION_LATEST_RELATIVE_PATH
from .supervisor_action_request_lifecycle import stable_ai_reviewer_request_path
from .runtime_supervisor_consumer import (
    CONSUMER_LATEST_RELATIVE_PATH,
    DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
    FORBIDDEN_SURFACES,
    SUPPORTED_MODE,
)


SCHEMA_VERSION = 1
EXECUTION_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_execution")
EXECUTION_LATEST_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "latest.json"
EXECUTION_HISTORY_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "history.jsonl"
PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
SUPPORTED_ACTION_TYPES = frozenset(
    {
        "runtime_platform_repair",
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "return_to_ai_reviewer_workflow",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _dispatch_dir(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT


def _consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _execution_latest_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / EXECUTION_LATEST_RELATIVE_PATH


def _execution_history_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / EXECUTION_HISTORY_RELATIVE_PATH


def _current_scan_study(profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    latest = _read_json_object(_scan_latest_path(profile))
    if latest is None:
        return None
    for study in latest.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return None


def _publication_eval_latest_path(study_root: Path) -> Path:
    return study_root / PUBLICATION_EVAL_LATEST_RELATIVE_PATH


def _current_consumer_dispatch_files(profile: WorkspaceProfile, study_id: str) -> list[Path]:
    latest = _read_json_object(_consumer_latest_path(profile))
    if latest is None:
        return []
    files: list[Path] = []
    seen: set[Path] = set()
    for dispatch in latest.get("default_executor_dispatches") or []:
        payload = _mapping(dispatch)
        if _text(payload.get("study_id")) != study_id:
            continue
        if _text(payload.get("dispatch_status")) != "ready":
            continue
        refs = _mapping(payload.get("refs"))
        dispatch_path = _text(refs.get("dispatch_path"))
        if dispatch_path is None:
            continue
        path = Path(dispatch_path).expanduser().resolve()
        if path.is_file() and path not in seen:
            files.append(path)
            seen.add(path)
    return files


def _dispatch_files(profile: WorkspaceProfile, study_id: str, action_types: tuple[str, ...]) -> list[Path]:
    current_files = _current_consumer_dispatch_files(profile, study_id)
    if action_types:
        requested = set(action_types)
        return [
            path
            for path in current_files
            if (payload := _read_json_object(path)) is not None and _text(payload.get("action_type")) in requested
        ]
    return current_files


def _resolve_study_ids(profile: WorkspaceProfile, study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    if not profile.studies_root.is_dir():
        return ()
    resolved: list[str] = []
    for dispatch_dir in sorted(
        profile.studies_root.glob(f"*/{DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT.as_posix()}"),
        key=lambda item: item.as_posix(),
    ):
        try:
            study_id = dispatch_dir.relative_to(profile.studies_root).parts[0]
        except (ValueError, IndexError):
            continue
        if any(dispatch_dir.glob("*.json")):
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _contract_guard(dispatch: Mapping[str, Any]) -> tuple[bool, str | None]:
    if _text(dispatch.get("surface")) != "default_executor_dispatch_request":
        return False, "unsupported_dispatch_surface"
    if _text(dispatch.get("dispatch_status")) != "ready":
        return False, "dispatch_not_ready"
    if _text(dispatch.get("executor_kind")) != "codex_cli_default":
        return False, "unsupported_executor_kind"
    if dispatch.get("chat_completion_only_executor_forbidden") is not True:
        return False, "chat_completion_only_guard_missing"
    action_type = _text(dispatch.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return False, "unsupported_action_type"
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if not prompt_contract:
        return False, "prompt_contract_missing"
    for key in ("prompt_budget", "compact_evidence_packet_ref", "do_not_repeat", "repeat_suppression_key"):
        if key not in prompt_contract:
            return False, f"{key}_missing"
    if prompt_contract.get("do_not_repeat") is not True:
        return False, "do_not_repeat_guard_missing"
    for key in (
        "paper_package_mutation_allowed",
        "quality_gate_relaxation_allowed",
        "manual_study_patch_allowed",
        "medical_claim_authoring_allowed",
    ):
        if prompt_contract.get(key) is not False:
            return False, f"{key}_guard_missing"
    forbidden = {
        text
        for item in prompt_contract.get("forbidden_surfaces") or []
        if (text := _text(item)) is not None
    }
    if not set(FORBIDDEN_SURFACES).issubset(forbidden):
        return False, "forbidden_surfaces_incomplete"
    return True, None


def _current_owner_route(profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    latest = _read_json_object(_scan_latest_path(profile))
    if latest is None:
        return None
    for study in latest.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            route = _mapping(payload.get("owner_route"))
            return owner_route_part.ensure_owner_route_v2(route) or None
    return None


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _owner_route_block_reason(*, dispatch: Mapping[str, Any], current_route: Mapping[str, Any] | None) -> str | None:
    if not _dispatch_owner_route(dispatch):
        return "owner_route_missing"
    if current_route is None:
        return "current_owner_route_missing"
    if not owner_route_part.owner_route_matches(dispatch=dispatch, current_route=current_route):
        return "owner_route_stale"
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=current_route):
        return "owner_route_next_owner_mismatch"
    return None


def _quest_root_from_status(profile: WorkspaceProfile, study_id: str) -> Path | None:
    try:
        status = study_runtime_router.study_runtime_status(profile=profile, study_id=study_id, study_root=None, entry_mode=None)
    except Exception:
        return None
    status_payload = dict(status) if isinstance(status, Mapping) else status.to_dict()
    quest_root = _text(status_payload.get("quest_root"))
    return Path(quest_root).expanduser().resolve() if quest_root is not None else None


def _execute_publication_gate_specificity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    quest_root = _quest_root_from_status(profile, study_id)
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.run_controller",
            "quest_root": str(quest_root),
        }
    state = publication_gate.build_gate_state(quest_root)
    report = publication_gate.build_gate_report(state)
    json_path, _ = publication_gate.write_gate_files(quest_root, report)
    report_with_refs = {
        **report,
        "latest_gate_path": str(json_path),
        "main_result_path": str(state.main_result_path) if getattr(state, "main_result_path", None) else None,
        "paper_root": str(state.paper_root) if getattr(state, "paper_root", None) else None,
        "submission_minimal_manifest_path": (
            str(state.submission_minimal_manifest_path)
            if getattr(state, "submission_minimal_manifest_path", None)
            else None
        ),
        "force_publication_gate_specificity_refresh": True,
    }
    materialized = publication_gate._materialize_publication_eval_latest(state=state, report=report_with_refs)
    if materialized is None and getattr(state, "study_root", None) is not None:
        decision_module = publication_gate.import_module("med_autoscience.controllers.study_runtime_decision")
        materialized = decision_module._materialize_publication_eval_from_gate_report(
            study_root=state.study_root,
            study_id=study_id,
            quest_root=quest_root,
            quest_id=quest_root.name,
            publication_gate_report=report_with_refs,
        )
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        "quest_root": str(quest_root),
        "owner_result": {
            "report_json": str(json_path),
            "status": report.get("status"),
            "blockers": list(report.get("blockers") or []),
            "publication_eval": materialized,
        },
    }


def _execute_runtime_platform_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "runtime supervisor-scan --apply-runtime-platform-repair",
        }
    from . import runtime_supervisor_scan

    result = runtime_supervisor_scan.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode=SUPPORTED_MODE,
        persist_surfaces=False,
    )
    study_payload = next(
        (study for study in result.get("studies", []) if isinstance(study, Mapping) and _text(study.get("study_id")) == study_id),
        {},
    )
    apply_result = _mapping(study_payload.get("runtime_platform_repair_apply"))
    executed = _text(apply_result.get("dispatch_status")) == "applied"
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(apply_result.get("reason")) or "runtime_platform_repair_not_applied",
        "owner_callable_surface": "runtime_supervisor_scan.supervisor_scan(apply_runtime_platform_repair=True)",
        "owner_result": apply_result or result,
    }


def _execute_current_package_freshness(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    quest_root = _quest_root_from_status(profile, study_id)
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    study_root = _study_root(profile, study_id)
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "quest_root": str(quest_root),
        }
    try:
        owner_result = gate_clearing_batch.run_gate_clearing_batch(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_root.name,
            source="runtime_supervisor_dispatch_executor",
            control_plane_route_context={
                "controller_route_context": {
                    "control_surface": "gate_clearing_batch",
                    "controller_action_type": "run_gate_clearing_batch",
                    "work_unit_id": "submission_minimal_refresh",
                    "requires_human_confirmation": False,
                }
            },
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "current_package_freshness_workflow_failed",
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "next_owner": "artifact_os",
            "error": str(exc),
            "quest_root": str(quest_root),
        }
    executed = bool(owner_result.get("ok")) if isinstance(owner_result, Mapping) else False
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(_mapping(owner_result).get("status")) or "gate_clearing_batch_not_applied",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(quest_root),
    }


def _execute_artifact_display_materialization(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    paper_root = study_root / "paper"
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    if not reporting_contract_path.exists():
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "medical_reporting_contract_missing",
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
            "next_owner": "artifact_os",
            "required_input_surface": str(reporting_contract_path),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch",
            "paper_root": str(paper_root),
        }
    try:
        stub_result = quest_hydration.materialize_display_contract_stubs(paper_root=paper_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "display_contract_stub_materialization_failed",
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
            "next_owner": "artifact_os",
            "error": str(exc),
            "paper_root": str(paper_root),
        }
    gate_result = _execute_current_package_freshness(profile=profile, study_id=study_id, apply=apply)
    owner_result = _mapping(gate_result.get("owner_result"))
    executed = gate_result.get("execution_status") == "executed"
    return {
        **gate_result,
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else gate_result.get("blocked_reason"),
        "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": {
            "display_contract_stubs": stub_result,
            "gate_clearing_batch": owner_result or gate_result.get("owner_result"),
        },
        "paper_root": str(paper_root),
    }


def _ref_path(packet: Mapping[str, Any], surface: str) -> str | None:
    ref = _mapping(_mapping(_mapping(packet.get("input_contract")).get("required_refs")).get(surface))
    return _text(ref.get("path")) or _text(ref.get("ref")) or _text(ref.get("relative_path"))


def _execute_ai_reviewer_workflow(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    request_path = stable_ai_reviewer_request_path(study_root=study_root)
    request = _read_json_object(request_path)
    if request is None:
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "ai_reviewer_request_missing",
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "next_owner": "ai_reviewer",
            "required_input_surface": str(request_path),
        }
    record = _mapping(_read_json_object(_publication_eval_latest_path(study_root)))
    if not record:
        record = _mapping(request.get("ai_reviewer_record") or request.get("publication_eval_record") or request.get("record"))
    if not record:
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "ai_reviewer_record_missing",
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "next_owner": "ai_reviewer",
            "required_input_surface": str(request_path),
        }
    required_refs = {
        surface: _ref_path(request, surface)
        for surface in (
            "manuscript",
            "evidence_ledger",
            "review_ledger",
            "study_charter",
            "medical_manuscript_blueprint",
            "claim_evidence_map",
            "medical_prose_review",
            "publication_gate_projection",
        )
    }
    missing_refs = [surface for surface, ref in required_refs.items() if ref is None]
    if missing_refs:
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "ai_reviewer_required_refs_missing",
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "next_owner": "ai_reviewer",
            "missing_refs": missing_refs,
            "required_input_surface": str(request_path),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "request_path": str(request_path),
        }
    try:
        owner_result = ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=required_refs["manuscript"],
            evidence_ref=required_refs["evidence_ledger"],
            review_ref=required_refs["review_ledger"],
            charter_ref=required_refs["study_charter"],
            record=record,
            additional_refs={
                surface: ref
                for surface, ref in required_refs.items()
                if surface not in {"manuscript", "evidence_ledger", "review_ledger", "study_charter"}
                and ref is not None
            },
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "ai_reviewer_workflow_failed",
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "next_owner": "ai_reviewer",
            "error": str(exc),
            "request_path": str(request_path),
        }
    controller_decision_refresh = _refresh_controller_decision_after_ai_reviewer_eval(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    if isinstance(owner_result, Mapping):
        owner_result = {
            **dict(owner_result),
            "controller_decision_refresh": controller_decision_refresh,
        }
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        "owner_result": owner_result,
        "request_path": str(request_path),
    }


def _refresh_controller_decision_after_ai_reviewer_eval(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    apply: bool = True,
    source: str = "ai_reviewer_publication_eval_workflow",
) -> dict[str, Any]:
    try:
        status = study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=None,
        )
        status_payload = dict(status) if isinstance(status, Mapping) else status.to_dict()
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "refresh_status": "blocked",
            "blocked_reason": "study_runtime_status_unavailable",
            "error": str(exc),
        }

    from . import study_outer_loop

    try:
        tick_request = study_outer_loop.build_runtime_watch_outer_loop_tick_request(
            study_root=study_root,
            status_payload=status_payload,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "refresh_status": "blocked",
            "blocked_reason": "outer_loop_tick_request_failed",
            "error": str(exc),
        }
    if tick_request is None:
        return {
            "refresh_status": "skipped",
            "skipped_reason": "outer_loop_tick_request_unavailable",
        }
    if not apply:
        return {
            "refresh_status": "dry_run",
            "study_id": study_id,
            "publication_eval_ref": dict(tick_request.get("publication_eval_ref") or {}),
            "decision_type": _text(tick_request.get("decision_type")),
            "work_unit_fingerprint": _text(tick_request.get("work_unit_fingerprint")),
            "next_work_unit": (
                dict(tick_request.get("next_work_unit"))
                if isinstance(tick_request.get("next_work_unit"), Mapping)
                else None
            ),
            "blocking_work_units": list(tick_request.get("blocking_work_units") or []),
        }

    try:
        refresh_result = study_outer_loop.materialize_non_dispatching_outer_loop_decision(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            status_payload=status_payload,
            charter_ref=tick_request["charter_ref"],
            publication_eval_ref=tick_request["publication_eval_ref"],
            decision_type=tick_request["decision_type"],
            route_target=tick_request.get("route_target"),
            route_key_question=tick_request.get("route_key_question"),
            route_rationale=tick_request.get("route_rationale"),
            source_route_key_question=tick_request.get("source_route_key_question"),
            work_unit_fingerprint=tick_request.get("work_unit_fingerprint"),
            next_work_unit=tick_request.get("next_work_unit"),
            blocking_work_units=tick_request.get("blocking_work_units") or [],
            requires_human_confirmation=bool(tick_request.get("requires_human_confirmation")),
            controller_actions=tick_request.get("controller_actions") or [],
            reason=str(tick_request.get("reason") or ""),
            source=source,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "refresh_status": "blocked",
            "blocked_reason": "non_dispatching_controller_decision_materialization_failed",
            "error": str(exc),
        }
    return {
        "refresh_status": "materialized",
        **dict(refresh_result),
    }


def refresh_controller_decisions_for_current_publication_eval(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="controller_decision_refresh",
    )
    developer_mode_payload = developer_mode.to_dict()
    if apply and (
        _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE
        or developer_mode_payload.get("safe_actions_enabled") is not True
    ):
        return {
            "surface": "runtime_supervisor_controller_decision_refresh",
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "workspace_root": str(profile.workspace_root),
            "dry_run": False,
            "requested_mode": mode,
            "effective_mode": developer_mode.mode,
            "developer_supervisor_mode": developer_mode_payload,
            "refresh_count": 0,
            "materialized_count": 0,
            "blocked_count": 1,
            "skipped_count": 0,
            "refreshes": [
                {
                    "refresh_status": "blocked",
                    "blocked_reason": _github_block_reason(developer_mode_payload) or "developer_apply_safe_required",
                }
            ],
        }
    resolved_study_ids = _resolve_study_ids(profile, study_ids)
    refreshes = [
        {
            "study_id": study_id,
            **_refresh_controller_decision_after_ai_reviewer_eval(
                profile=profile,
                study_id=study_id,
                study_root=_study_root(profile, study_id),
                apply=apply,
                source="runtime_supervisor_controller_decision_refresh",
            ),
        }
        for study_id in resolved_study_ids
    ]
    return {
        "surface": "runtime_supervisor_controller_decision_refresh",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "requested_studies": list(resolved_study_ids),
        "refresh_count": len(refreshes),
        "materialized_count": sum(item.get("refresh_status") == "materialized" for item in refreshes),
        "blocked_count": sum(item.get("refresh_status") == "blocked" for item in refreshes),
        "skipped_count": sum(item.get("refresh_status") == "skipped" for item in refreshes),
        "dry_run_count": sum(item.get("refresh_status") == "dry_run" for item in refreshes),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "refreshes": refreshes,
    }


def _execute_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch_path: Path,
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    dispatch = _read_json_object(dispatch_path)
    if dispatch is None:
        return {
            "generated_at": generated_at,
            "study_id": study_id,
            "dispatch_path": str(dispatch_path),
            "execution_status": "blocked",
            "blocked_reason": "dispatch_payload_missing_or_invalid",
        }
    action_type = _text(dispatch.get("action_type")) or "unknown_action"
    action_fingerprint = runtime_dispatch_cost.dispatch_action_fingerprint(
        dispatch=dispatch,
        dispatch_path=dispatch_path,
    )
    guard_ok, guard_reason = _contract_guard(dispatch)
    current_route = _current_owner_route(profile, study_id)
    owner_route_block_reason = _owner_route_block_reason(dispatch=dispatch, current_route=current_route)
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    repeat_guard = repeat_suppression.execution_repeat_suppression(
        dispatch={**dict(dispatch), "owner_route": _dispatch_owner_route(dispatch), "prompt_contract": prompt_contract},
        current_study=_current_scan_study(profile, study_id),
        previous_execution_latest=_read_json_object(_execution_latest_path(profile, study_id)),
    )
    if not guard_ok:
        execution = {
            "execution_status": "blocked",
            "blocked_reason": guard_reason,
            "owner_callable_surface": None,
        }
    elif owner_route_block_reason is not None:
        execution = {
            "execution_status": "blocked",
            "blocked_reason": owner_route_block_reason,
            "owner_callable_surface": None,
            "owner_route_current": False,
            "current_owner_route": current_route,
        }
    elif repeat_guard["repeat_suppressed"]:
        execution = {
            "execution_status": "repeat_suppressed",
            "blocked_reason": repeat_suppression.REPEAT_SUPPRESSED_REASON,
            "owner_callable_surface": None,
            "repeat_suppressed": True,
            "why_not_applied": repeat_suppression.REPEAT_SUPPRESSED_REASON,
        }
    elif apply and (
        _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE
        or developer_mode_payload.get("safe_actions_enabled") is not True
    ):
        execution = {
            "execution_status": "blocked",
            "blocked_reason": _github_block_reason(developer_mode_payload) or "developer_apply_safe_required",
            "owner_callable_surface": None,
        }
    elif action_type == "publication_gate_specificity_required":
        execution = _execute_publication_gate_specificity(profile=profile, study_id=study_id, apply=apply)
    elif action_type == "runtime_platform_repair":
        execution = _execute_runtime_platform_repair(profile=profile, study_id=study_id, apply=apply)
    elif action_type == "current_package_freshness_required":
        execution = _execute_current_package_freshness(profile=profile, study_id=study_id, apply=apply)
    elif action_type == "artifact_display_surface_materialization_required":
        execution = _execute_artifact_display_materialization(profile=profile, study_id=study_id, apply=apply)
    elif action_type == "return_to_ai_reviewer_workflow":
        execution = _execute_ai_reviewer_workflow(profile=profile, study_id=study_id, apply=apply)
    else:
        execution = {
            "execution_status": "blocked",
            "blocked_reason": "unsupported_action_type",
            "owner_callable_surface": None,
        }
    action_cost = runtime_dispatch_cost.executor_action_cost(
        action_type=action_type,
        apply=apply,
        execution=execution,
        action_fingerprint=action_fingerprint,
    )
    return {
        "surface": "default_executor_dispatch_execution",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")),
        "action_type": action_type,
        "action_id": _text(dispatch.get("action_id")),
        "execution_id": f"execution::{study_id}::{action_type}::{generated_at}",
        "next_executable_owner": _text(dispatch.get("next_executable_owner")),
        "required_output_surface": _text(dispatch.get("required_output_surface")),
        "dispatch_path": str(dispatch_path),
        "dispatch_contract_valid": guard_ok,
        "dispatch_contract_blocked_reason": guard_reason,
        "owner_route": _dispatch_owner_route(dispatch) or None,
        "owner_route_current": owner_route_block_reason is None if guard_ok else None,
        "current_owner_route": current_route,
        "prompt_contract": prompt_contract or None,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "repeat_suppression_key": repeat_guard["repeat_suppression_key"],
        "repeat_suppression": repeat_guard,
        "action_fingerprint": action_fingerprint,
        "action_class": action_cost["action_class"],
        "will_start_llm": action_cost["will_start_llm"],
        "action_cost": action_cost,
        "dry_run": not apply,
        "developer_supervisor_mode": dict(developer_mode_payload),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        **execution,
    }


def execute_default_executor_dispatches(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    action_types: Iterable[str] = (),
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="default_executor_dispatch_executor",
    )
    developer_mode_payload = developer_mode.to_dict()
    resolved_study_ids = _resolve_study_ids(profile, study_ids)
    resolved_action_types = tuple(action_type for item in action_types if (action_type := _text(item)) is not None)
    executions: list[dict[str, Any]] = []
    written_files: list[str] = []
    for study_id in resolved_study_ids:
        for dispatch_path in _dispatch_files(profile, study_id, resolved_action_types):
            execution = _execute_dispatch(
                profile=profile,
                study_id=study_id,
                dispatch_path=dispatch_path,
                developer_mode_payload=developer_mode_payload,
                apply=apply,
            )
            executions.append(execution)
        study_executions = [execution for execution in executions if execution["study_id"] == study_id]
        if apply and study_executions:
            latest_path = _execution_latest_path(profile, study_id)
            history_path = _execution_history_path(profile, study_id)
            study_payload = {
                "surface": "default_executor_dispatch_execution_study_latest",
                "schema_version": SCHEMA_VERSION,
                "generated_at": generated_at,
                "study_id": study_id,
                "executions": study_executions,
                "executed_count": sum(item.get("execution_status") == "executed" for item in study_executions),
                "blocked_count": sum(item.get("execution_status") == "blocked" for item in study_executions),
                "codex_dispatch_count": sum(item.get("will_start_llm") is True for item in study_executions),
                "suppressed_dispatch_count": sum(
                    item.get("execution_status") in {"repeat_suppressed", "blocked"} for item in study_executions
                ),
                "dispatch_budget_window": runtime_dispatch_cost.dispatch_budget_window(),
                "dry_run": False,
            }
            _write_json(latest_path, study_payload)
            _append_json_line(
                history_path,
                {
                    "generated_at": generated_at,
                    "study_id": study_id,
                    "execution_statuses": [item.get("execution_status") for item in study_executions],
                    "blocked_reasons": [item.get("blocked_reason") for item in study_executions if item.get("blocked_reason")],
                },
            )
            written_files.append(str(latest_path))
            written_files.append(str(history_path))
            for execution in study_executions:
                quest_root = profile.runtime_root / (_text(execution.get("quest_id")) or study_id)
                execution["runtime_lifecycle_index"] = runtime_lifecycle_store.record_dispatch_receipt(
                    quest_root=quest_root,
                    receipt=execution,
                    receipt_path=latest_path,
                    db_path=runtime_lifecycle_store.workspace_lifecycle_store_path(profile.workspace_root),
                )
            _write_json(latest_path, study_payload)
    payload = {
        "surface": "default_executor_dispatch_executor",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "requested_studies": list(resolved_study_ids),
        "requested_action_types": list(resolved_action_types),
        "execution_count": len(executions),
        "executed_count": sum(item.get("execution_status") == "executed" for item in executions),
        "blocked_count": sum(item.get("execution_status") == "blocked" for item in executions),
        "repeat_suppressed_count": sum(item.get("execution_status") == "repeat_suppressed" for item in executions),
        "dry_run_count": sum(item.get("execution_status") == "dry_run" for item in executions),
        "codex_dispatch_count": sum(item.get("will_start_llm") is True for item in executions),
        "suppressed_dispatch_count": sum(
            item.get("execution_status") in {"repeat_suppressed", "blocked"} for item in executions
        ),
        "dispatch_budget_window": runtime_dispatch_cost.dispatch_budget_window(),
        "action_fingerprints": list(
            dict.fromkeys(item.get("action_fingerprint") for item in executions if item.get("action_fingerprint"))
        ),
        "executions": executions,
        "written_files": written_files,
    }
    return payload


__all__ = [
    "EXECUTION_LATEST_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "SUPPORTED_ACTION_TYPES",
    "execute_default_executor_dispatches",
    "refresh_controller_decisions_for_current_publication_eval",
]
