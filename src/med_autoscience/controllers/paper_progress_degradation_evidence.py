from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import progress_portal
from med_autoscience.profiles import WorkspaceProfile


SURFACE = "paper_progress_degradation_evidence"
SCHEMA_VERSION = 1
READ_MODEL = "paper_progress_degradation_evidence_read_model"

READ_ONLY_CONTRACT = {
    "mode": "read_only_degradation_evidence",
    "writes_real_workspace": False,
    "can_mutate_runtime": False,
    "can_write_current_package": False,
    "can_write_publication_eval": False,
    "can_write_controller_decisions": False,
    "can_write_runtime_sqlite": False,
    "can_write_restore_archive": False,
    "allowed_actions": [
        "read_status_progress_surfaces",
        "read_owner_route_dry_run_projection",
        "read_publication_gate_projection",
        "read_ai_reviewer_handoff_projection",
        "read_writer_handoff_projection",
        "read_progress_portal_refs",
        "summarize_safe_reconcile_dry_run",
    ],
    "prohibited_actions": [
        "runtime_relaunch",
        "safe_reconcile_apply",
        "current_package_write",
        "publication_eval_write",
        "controller_decisions_write",
        "runtime_sqlite_write",
        "restore_archive_write",
    ],
}

STUDY_PROGRESS_REFS: tuple[Path, ...] = (
    Path("artifacts/runtime/runtime_status_summary.json"),
    Path("artifacts/runtime/runtime_supervision/latest.json"),
    Path("artifacts/runtime/study_macro_state/latest.json"),
    Path("artifacts/truth/latest.json"),
    Path("artifacts/controller_decisions/latest.json"),
    Path("artifacts/publication_eval/latest.json"),
    Path("artifacts/runtime/domain_health_diagnostic/latest.json"),
    Path("artifacts/supervision/requests/ai_reviewer/latest.json"),
)


def build_paper_progress_degradation_evidence(
    profile_evidences: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    blockers = [
        dict(blocker)
        for profile in profile_evidences
        for blocker in _sequence(profile.get("blockers"))
        if isinstance(blocker, Mapping)
    ]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "mode": "read_only_degradation_evidence",
        "read_only_contract": dict(READ_ONLY_CONTRACT),
        "profile_count": len(profile_evidences),
        "summary": {
            "profiles_with_blockers": sum(bool(profile.get("blockers")) for profile in profile_evidences),
            "blocker_count": len(blockers),
            "writes_performed": False,
            "can_claim_landed": False,
        },
        "profiles": [dict(profile) for profile in profile_evidences],
        "blockers": blockers,
        "next_actions": _next_actions(blockers),
    }


def build_profile_progress_degradation_evidence(
    *,
    profile_path: str,
    profile: WorkspaceProfile,
    studies: Sequence[Mapping[str, Any]],
    reconcile: Mapping[str, Any],
    monitor: Mapping[str, Any],
) -> dict[str, Any]:
    owner_route_by_study = _owner_route_receipts_by_study(reconcile)
    study_items = [
        _study_degradation_evidence(
            profile_path=profile_path,
            study=study,
            owner_route=owner_route_by_study.get(_text(study.get("study_id")), {}),
        )
        for study in studies
    ]
    portal_refs = _progress_portal_refs(profile.workspace_root)
    safe_reconcile = _safe_reconcile_dry_run_evidence(reconcile)
    monitor_evidence = _monitor_evidence(monitor)
    blockers = [
        dict(blocker)
        for source in [*study_items, portal_refs, safe_reconcile, monitor_evidence]
        for blocker in _sequence(source.get("blockers"))
        if isinstance(blocker, Mapping)
    ]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "mode": "read_only_degradation_evidence",
        "read_only_contract": dict(READ_ONLY_CONTRACT),
        "profile_path": profile_path,
        "workspace_root": str(profile.workspace_root),
        "study_count": len(study_items),
        "studies": study_items,
        "progress_portal_refs": portal_refs,
        "safe_reconcile_dry_run": safe_reconcile,
        "real_workspace_soak_monitor": monitor_evidence,
        "summary": {
            "status_progress_readable_count": sum(
                item["status_progress_readability"]["status"] == "readable" for item in study_items
            ),
            "owner_route_advanced_count": sum(
                item["owner_route_progression"]["status"] == "advanced" for item in study_items
            ),
            "publication_handoff_clear_count": sum(
                item["publication_handoff_clarity"]["status"] == "clear" for item in study_items
            ),
            "progress_portal_refs_readable": portal_refs["status"] == "readable",
            "safe_reconcile_has_next_action": bool(safe_reconcile.get("next_action")),
            "blocker_count": len(blockers),
            "writes_performed": False,
            "can_claim_landed": False,
        },
        "blockers": blockers,
        "next_actions": _next_actions(blockers),
    }


def _study_degradation_evidence(
    *,
    profile_path: str,
    study: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(study.get("study_id"))
    study_root_text = _text(study.get("study_root"))
    study_root = Path(study_root_text).expanduser().resolve() if study_root_text else None
    surface_payloads = _study_surface_payloads(study_root)
    publication_supervisor_state = _publication_supervisor_state(surface_payloads)
    publication_eval = _mapping(surface_payloads.get("artifacts/publication_eval/latest.json"))
    ai_reviewer_request = _mapping(surface_payloads.get("artifacts/supervision/requests/ai_reviewer/latest.json"))
    macro_state = _mapping(surface_payloads.get("artifacts/runtime/study_macro_state/latest.json"))

    status_progress = _status_progress_readability(profile_path=profile_path, study=study)
    owner_route_progression = _owner_route_progression(
        profile_path=profile_path,
        study_id=study_id,
        owner_route=owner_route,
    )
    publication_handoff = _publication_handoff_clarity(
        profile_path=profile_path,
        study_id=study_id,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval=publication_eval,
        ai_reviewer_request=ai_reviewer_request,
        macro_state=macro_state,
    )
    blockers = [
        dict(blocker)
        for source in (status_progress, owner_route_progression, publication_handoff)
        for blocker in _sequence(source.get("blockers"))
        if isinstance(blocker, Mapping)
    ]
    return {
        "study_id": study_id,
        "study_root": study_root_text,
        "status_progress_readability": status_progress,
        "owner_route_progression": owner_route_progression,
        "publication_handoff_clarity": publication_handoff,
        "blockers": blockers,
    }


def _status_progress_readability(
    *,
    profile_path: str,
    study: Mapping[str, Any],
) -> dict[str, Any]:
    readable_refs = [
        _text(surface.get("relative_ref"))
        for surface in _sequence(study.get("surface_refs"))
        if isinstance(surface, Mapping) and surface.get("readable") is True
    ]
    if study.get("status_progress_readable") is True:
        return {
            "status": "readable",
            "readable_surface_count": study.get("readable_surface_count"),
            "readable_refs": [ref for ref in readable_refs if ref],
            "blockers": [],
        }
    blocker = _blocker(
        kind="status_progress_readability",
        reason=_text(study.get("reason")) or "status_progress_surface_unreadable",
        next_action="repair_status_progress_surfaces",
        profile_path=profile_path,
        study_id=_text(study.get("study_id")),
    )
    return {
        "status": "blocked",
        "readable_surface_count": study.get("readable_surface_count"),
        "readable_refs": [ref for ref in readable_refs if ref],
        "blockers": [blocker],
    }


def _owner_route_progression(
    *,
    profile_path: str,
    study_id: str,
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    before = _mapping(owner_route.get("before"))
    after = _mapping(owner_route.get("after"))
    before_route = _mapping(before.get("owner_route"))
    after_route = _mapping(after.get("owner_route"))
    stable_blocker = _mapping(after.get("stable_blocker") or before.get("stable_blocker"))
    if after_route and before_route and after_route != before_route:
        status = "advanced"
        next_action = "review_safe_reconcile_dry_run_before_apply"
    elif after.get("owner_forwarded") is True:
        status = "advanced"
        next_action = "review_forwarded_owner_route"
    elif stable_blocker:
        status = "blocked"
        next_action = _text(stable_blocker.get("next_action")) or "resolve_owner_route_stable_blocker"
    elif before_route or after_route:
        status = "stationary"
        next_action = "inspect_stationary_owner_route"
    else:
        status = "missing"
        next_action = "rerun_scan_domain_routes_or_repair_owner_route_inputs"

    blockers = []
    if status != "advanced":
        blockers.append(
            _blocker(
                kind=_text(stable_blocker.get("kind")) or "owner_route_progression",
                reason=_text(stable_blocker.get("reason")) or status,
                next_action=next_action,
                profile_path=profile_path,
                study_id=study_id,
            )
        )
    return {
        "status": status,
        "next_action": next_action,
        "before": before,
        "after": after,
        "blockers": blockers,
    }


def _publication_handoff_clarity(
    *,
    profile_path: str,
    study_id: str,
    publication_supervisor_state: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    ai_reviewer_request: Mapping[str, Any],
    macro_state: Mapping[str, Any],
) -> dict[str, Any]:
    publication_gate = _publication_gate_clarity(
        profile_path=profile_path,
        study_id=study_id,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval=publication_eval,
    )
    ai_reviewer = _ai_reviewer_clarity(
        profile_path=profile_path,
        study_id=study_id,
        publication_eval=publication_eval,
        ai_reviewer_request=ai_reviewer_request,
    )
    writer_handoff = _writer_handoff_clarity(
        profile_path=profile_path,
        study_id=study_id,
        publication_supervisor_state=publication_supervisor_state,
        macro_state=macro_state,
    )
    blockers = [
        dict(blocker)
        for source in (publication_gate, ai_reviewer, writer_handoff)
        for blocker in _sequence(source.get("blockers"))
        if isinstance(blocker, Mapping)
    ]
    return {
        "status": "clear" if not blockers else "blocked",
        "publication_gate": publication_gate,
        "ai_reviewer": ai_reviewer,
        "writer_handoff": writer_handoff,
        "blockers": blockers,
    }


def _publication_gate_clarity(
    *,
    profile_path: str,
    study_id: str,
    publication_supervisor_state: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
) -> dict[str, Any]:
    supervisor_phase = _text(publication_supervisor_state.get("supervisor_phase"))
    phase_owner = _text(publication_supervisor_state.get("phase_owner"))
    current_required_action = _text(publication_supervisor_state.get("current_required_action"))
    if supervisor_phase and phase_owner and current_required_action:
        return {
            "status": "clear",
            "source": "publication_supervisor_state",
            "supervisor_phase": supervisor_phase,
            "phase_owner": phase_owner,
            "current_required_action": current_required_action,
            "blockers": [],
        }
    eval_verdict = _mapping(publication_eval.get("verdict"))
    reason = "publication_gate_required_action_missing"
    if eval_verdict or publication_eval:
        reason = "publication_gate_supervisor_state_incomplete"
    blocker = _blocker(
        kind="publication_gate_handoff",
        reason=reason,
        next_action="refresh_publication_gate_supervisor_state",
        profile_path=profile_path,
        study_id=study_id,
    )
    return {
        "status": "blocked",
        "source": "publication_eval" if publication_eval else "missing",
        "supervisor_phase": supervisor_phase,
        "phase_owner": phase_owner,
        "current_required_action": current_required_action,
        "blockers": [blocker],
    }


def _ai_reviewer_clarity(
    *,
    profile_path: str,
    study_id: str,
    publication_eval: Mapping[str, Any],
    ai_reviewer_request: Mapping[str, Any],
) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    owner = _text(provenance.get("owner"))
    ai_reviewer_required = provenance.get("ai_reviewer_required")
    request_state = _text(_mapping(ai_reviewer_request.get("request_lifecycle")).get("state"))
    request_owner = _text(ai_reviewer_request.get("request_owner") or ai_reviewer_request.get("assigned_to"))
    if owner == "ai_reviewer" and ai_reviewer_required is False:
        return {
            "status": "clear",
            "source": "publication_eval.assessment_provenance",
            "assessment_owner": owner,
            "ai_reviewer_required": ai_reviewer_required,
            "request_state": request_state,
            "blockers": [],
        }
    if request_state or request_owner:
        return {
            "status": "clear",
            "source": "ai_reviewer_request_lifecycle",
            "assessment_owner": owner,
            "ai_reviewer_required": ai_reviewer_required,
            "request_state": request_state,
            "blockers": [],
        }
    blocker = _blocker(
        kind="ai_reviewer_handoff",
        reason="ai_reviewer_handoff_unclear",
        next_action="materialize_ai_reviewer_request_or_eval",
        profile_path=profile_path,
        study_id=study_id,
    )
    return {
        "status": "blocked",
        "source": "publication_eval.assessment_provenance" if provenance else "missing",
        "assessment_owner": owner,
        "ai_reviewer_required": ai_reviewer_required,
        "request_state": request_state,
        "blockers": [blocker],
    }


def _writer_handoff_clarity(
    *,
    profile_path: str,
    study_id: str,
    publication_supervisor_state: Mapping[str, Any],
    macro_state: Mapping[str, Any],
) -> dict[str, Any]:
    writer_state = _text(macro_state.get("writer_state"))
    current_required_action = _text(publication_supervisor_state.get("current_required_action"))
    supervisor_phase = _text(publication_supervisor_state.get("supervisor_phase"))
    if writer_state:
        return {
            "status": "clear",
            "source": "study_macro_state",
            "writer_state": writer_state,
            "current_required_action": current_required_action,
            "blockers": [],
        }
    if current_required_action and any(token in current_required_action for token in ("write", "bundle", "handoff")):
        return {
            "status": "clear",
            "source": "publication_supervisor_state",
            "writer_state": writer_state,
            "current_required_action": current_required_action,
            "supervisor_phase": supervisor_phase,
            "blockers": [],
        }
    blocker = _blocker(
        kind="writer_handoff",
        reason="writer_handoff_state_missing",
        next_action="materialize_writer_handoff_state",
        profile_path=profile_path,
        study_id=study_id,
    )
    return {
        "status": "blocked",
        "source": "missing",
        "writer_state": writer_state,
        "current_required_action": current_required_action,
        "supervisor_phase": supervisor_phase,
        "blockers": [blocker],
    }


def _progress_portal_refs(workspace_root: Path) -> dict[str, Any]:
    refs = [
        _ref_status(
            label="progress_portal_payload",
            path=workspace_root / progress_portal.PROGRESS_PORTAL_PAYLOAD_REF,
            kind="json",
        ),
        _ref_status(
            label="progress_portal_html",
            path=workspace_root / progress_portal.PROGRESS_PORTAL_HTML_REF,
            kind="text",
        ),
    ]
    unreadable = [ref for ref in refs if ref["readable"] is not True]
    blockers = []
    if unreadable:
        blockers.append(
            {
                "kind": "progress_portal_refs",
                "reason": "progress_portal_refs_unreadable",
                "next_action": "materialize_progress_portal_read_models",
                "missing_or_unreadable_refs": [ref["label"] for ref in unreadable],
            }
        )
    return {
        "status": "readable" if not unreadable else "blocked",
        "refs": refs,
        "blockers": blockers,
    }


def _safe_reconcile_dry_run_evidence(reconcile: Mapping[str, Any]) -> dict[str, Any]:
    next_action = _safe_reconcile_next_action(reconcile)
    status = "blocked" if reconcile.get("can_complete") is not True else "ready"
    blockers = []
    if not next_action:
        blockers.append(
            {
                "kind": "safe_reconcile_dry_run",
                "reason": "safe_reconcile_next_action_missing",
                "next_action": "rerun_safe_reconcile_dry_run",
            }
        )
    if reconcile.get("can_complete") is not True:
        blockers.append(
            {
                "kind": "safe_reconcile_dry_run",
                "reason": _text(reconcile.get("reason")) or "safe_reconcile_dry_run_blocked",
                "next_action": next_action or _text(reconcile.get("next_action")) or "repair_runtime_truth_or_profile_inputs",
            }
        )
    return {
        "status": status,
        "dry_run": reconcile.get("dry_run") is True,
        "writes_performed": False,
        "next_action": next_action,
        "step_receipt_count": len(_sequence(reconcile.get("step_receipts"))),
        "stable_blocker_count": len(_sequence(reconcile.get("stable_blockers"))),
        "blocked_count": reconcile.get("blocked_count"),
        "execution_count": reconcile.get("execution_count"),
        "blockers": blockers,
    }


def _monitor_evidence(monitor: Mapping[str, Any]) -> dict[str, Any]:
    status = _text(monitor.get("status"))
    next_action = _text(monitor.get("next_action"))
    blockers = []
    if status in {"blocked", "partial"} or not next_action:
        blockers.append(
            {
                "kind": "real_workspace_soak_monitor",
                "reason": f"real_workspace_soak_monitor:{status or 'next_action_missing'}",
                "next_action": next_action or "resolve_real_workspace_soak_monitor_gaps",
            }
        )
    return {
        "status": status or "unknown",
        "writes_performed": False,
        "next_action": next_action,
        "blockers": blockers,
    }


def _safe_reconcile_next_action(reconcile: Mapping[str, Any]) -> str:
    explicit = _text(reconcile.get("next_action"))
    if explicit:
        return explicit
    for blocker in _sequence(reconcile.get("stable_blockers")):
        if not isinstance(blocker, Mapping):
            continue
        action = _text(blocker.get("next_action"))
        if action:
            return action
    if reconcile.get("can_complete") is not True:
        return _text(reconcile.get("next_action")) or "repair_runtime_truth_or_profile_inputs"
    if int(reconcile.get("blocked_count") or 0) > 0:
        return "inspect_blocked_safe_reconcile_dispatches"
    if int(reconcile.get("execution_count") or 0) > 0:
        return "review_safe_reconcile_dry_run_before_apply"
    if _sequence(reconcile.get("step_receipts")):
        return "continue_read_only_monitoring"
    return ""


def _owner_route_receipts_by_study(reconcile: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        _text(receipt.get("study_id")): receipt
        for receipt in _sequence(reconcile.get("study_receipts"))
        if isinstance(receipt, Mapping) and _text(receipt.get("study_id"))
    }


def _study_surface_payloads(study_root: Path | None) -> dict[str, Mapping[str, Any]]:
    if study_root is None:
        return {}
    return {ref.as_posix(): _read_json_object(study_root / ref) for ref in STUDY_PROGRESS_REFS}


def _publication_supervisor_state(payloads: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    for payload in payloads.values():
        state = _mapping(payload.get("publication_supervisor_state"))
        if state:
            return state
        controllers = _mapping(payload.get("controllers"))
        publication_gate = _mapping(controllers.get("publication_gate"))
        if publication_gate:
            return publication_gate
    return {}


def _ref_status(*, label: str, path: Path, kind: str) -> dict[str, Any]:
    exists = path.is_file()
    error = ""
    readable = False
    if exists:
        if kind == "json":
            payload = _read_json_object(path)
            readable = bool(payload)
            if not readable:
                error = "json payload is missing or not an object"
        else:
            try:
                readable = bool(path.read_text(encoding="utf-8").strip())
            except OSError as exc:
                error = f"{type(exc).__name__}: {exc}"
    return {
        "label": label,
        "path": str(path),
        "kind": kind,
        "exists": exists,
        "readable": readable,
        "error": error,
    }


def _read_json_object(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _blocker(
    *,
    kind: str,
    reason: str,
    next_action: str,
    profile_path: str,
    study_id: str = "",
) -> dict[str, str]:
    payload = {
        "kind": kind,
        "reason": reason,
        "next_action": next_action,
        "profile_path": profile_path,
    }
    if study_id:
        payload["study_id"] = study_id
    return payload


def _next_actions(blockers: Sequence[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    for blocker in blockers:
        action = _text(blocker.get("next_action"))
        if action and action not in actions:
            actions.append(action)
    return actions


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[Any]:
    return value if isinstance(value, list | tuple) else ()


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "READ_MODEL",
    "READ_ONLY_CONTRACT",
    "SCHEMA_VERSION",
    "SURFACE",
    "build_paper_progress_degradation_evidence",
    "build_profile_progress_degradation_evidence",
]
