from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


EXECUTED_STATUSES = frozenset({"executed"})
EXECUTION_REF = Path("artifacts/supervision/consumer/default_executor_execution/latest.json")
CLOSEOUT_ROOT_REFS = (
    Path("artifacts/supervision/consumer/default_executor_execution"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
    Path("paper/review"),
    Path("paper/review/default_executor_closeouts"),
)
CLOSEOUT_SURFACES = frozenset(
    {
        "stage_attempt_closeout_packet",
        "domain_stage_closeout_packet",
    }
)


def default_executor_execution_candidates(*, study_root: Path) -> list[tuple[Mapping[str, Any], str]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    receipt = _read_json_object(resolved_study_root / EXECUTION_REF)
    candidates: list[tuple[Mapping[str, Any], str]] = []
    if receipt is not None:
        candidates.extend((execution, str(EXECUTION_REF)) for execution in reversed(_mapping_list(receipt.get("executions"))))
        candidates.extend(
            (execution, f"{EXECUTION_REF}#execution_ledger")
            for execution in reversed(_mapping_list(receipt.get("execution_ledger")))
        )
    candidates.extend(_stage_closeout_candidates(study_root=resolved_study_root))
    return candidates


def _stage_closeout_candidates(*, study_root: Path) -> list[tuple[Mapping[str, Any], str]]:
    candidates: list[tuple[Mapping[str, Any], str]] = []
    seen: set[str] = set()
    for closeout_root_ref in CLOSEOUT_ROOT_REFS:
        closeout_root = study_root / closeout_root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in sorted(closeout_root.glob("*.json"), reverse=True):
            resolved = str(closeout_path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            closeout = _read_json_object(closeout_path)
            if closeout is None:
                continue
            execution = _execution_from_stage_closeout(
                closeout=closeout,
                study_root=study_root,
                closeout_ref=Path(_study_relative_ref(study_root=study_root, path=closeout_path)),
            )
            if execution is not None:
                candidates.append((execution, str(execution["receipt_ref"])))
    return candidates


def _execution_from_stage_closeout(
    *,
    closeout: Mapping[str, Any],
    study_root: Path,
    closeout_ref: Path,
) -> dict[str, Any] | None:
    if _text(closeout.get("surface_kind")) not in CLOSEOUT_SURFACES:
        return None
    if _text(closeout.get("stage_id")) != "domain_owner/default-executor-dispatch":
        return None
    action_type = _text(closeout.get("action_type"))
    if not action_type:
        return None
    route, route_source = _stage_closeout_owner_route(closeout=closeout, study_root=study_root)
    repair_evidence = _stage_closeout_repair_evidence(closeout)
    owner_receipt = _mapping(closeout.get("owner_receipt"))
    domain_execution = _mapping(closeout.get("domain_execution"))
    return {
        "surface": "default_executor_dispatch_execution",
        "schema_version": 1,
        "study_id": _text(closeout.get("study_id")),
        "quest_id": _text(closeout.get("quest_id")),
        "action_type": action_type,
        "execution_status": _stage_closeout_execution_status(closeout),
        "execution_id": _text(closeout.get("execution_id"))
        or _text(closeout.get("closeout_id"))
        or _text(closeout.get("stage_attempt_id")),
        "idempotency_key": _text(closeout.get("idempotency_key")),
        "current_owner_route": route or None,
        "owner_route": route or None,
        "owner_route_currentness_source": route_source,
        "stage_closeout_surface_kind": _text(closeout.get("surface_kind")),
        "stage_closeout_status": _text(closeout.get("status")),
        "stage_closeout_refs": _text_list(closeout.get("closeout_refs")),
        "stage_closeout_required_ref_field": _text(
            _mapping(closeout.get("required_closeout_packet")).get("required_ref_field")
        )
        or "closeout_refs",
        "stage_attempt_id": _text(closeout.get("stage_attempt_id")),
        "typed_blocker": _mapping(closeout.get("typed_blocker")),
        "owner_result": {
            "status": _text(owner_receipt.get("status")) or _text(closeout.get("route_outcome")) or _text(closeout.get("status")),
            "ok": _stage_closeout_has_story_surface_delta(closeout),
            "blocked_reason": _text(domain_execution.get("blocked_reason"))
            or _text(owner_receipt.get("typed_blocker"))
            or _text(closeout.get("blocked_reason")),
            "blocked_reasons": list(owner_receipt.get("blocked_reasons") or []),
            "dispatcher_result": _mapping(domain_execution.get("dispatcher_result")),
            "repair_execution_evidence": repair_evidence,
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
        },
        "receipt_ref": str(closeout_ref),
    }


def _stage_closeout_execution_status(closeout: Mapping[str, Any]) -> str:
    domain_execution_status = _text(_mapping(closeout.get("domain_execution")).get("execution_status"))
    if domain_execution_status in EXECUTED_STATUSES:
        return domain_execution_status
    if _text(closeout.get("route_outcome")) == "write_repair_delta_recorded" and _stage_closeout_has_story_surface_delta(
        closeout
    ):
        return "executed"
    return domain_execution_status or "executed"


def _stage_closeout_owner_route(*, closeout: Mapping[str, Any], study_root: Path) -> tuple[dict[str, Any], str]:
    basis = _mapping(closeout.get("owner_route_basis")) or _mapping(closeout.get("owner_route_currentness"))
    if not basis:
        basis = {
            "truth_epoch": _text(closeout.get("truth_epoch")),
            "source_eval_id": _text(closeout.get("source_eval_id")),
            "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint")),
            "work_unit_id": _text(closeout.get("work_unit_id")),
            "owner_reason": _text(closeout.get("owner_reason")),
        }
    stage_packet_route = _stage_closeout_stage_packet_owner_route(closeout=closeout, study_root=study_root)
    if stage_packet_route and _stage_closeout_basis_missing_required_currentness(basis):
        return stage_packet_route, "stage_packet_ref_recovered"
    if any(_text(basis.get(key)) for key in ("truth_epoch", "work_unit_fingerprint", "work_unit_id", "owner_reason")):
        action_type = _text(closeout.get("action_type"))
        owner = (
            _text(closeout.get("owner"))
            or _text(_mapping(closeout.get("domain_execution")).get("domain_owner"))
            or _stage_closeout_default_owner(action_type)
        )
        return {
            "truth_epoch": _text(basis.get("truth_epoch")),
            "route_epoch": _text(basis.get("truth_epoch")),
            "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
            "source_eval_id": _text(basis.get("source_eval_id")),
            "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint")),
            "next_owner": "write" if owner in {"quality_repair_batch", "write"} else owner,
            "owner_reason": _text(basis.get("owner_reason")) or _text(closeout.get("blocked_reason")),
            "allowed_actions": [action_type] if action_type else [],
            "source_refs": {
                "owner_route_currentness_basis": {
                    "truth_epoch": _text(basis.get("truth_epoch")),
                    "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
                    "source_eval_id": _text(basis.get("source_eval_id")),
                    "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint")),
                    "work_unit_id": _text(basis.get("work_unit_id")),
                    "owner_reason": _text(basis.get("owner_reason")) or _text(closeout.get("blocked_reason")),
                },
                "study_truth_epoch": _text(basis.get("truth_epoch")),
                "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
                "source_eval_id": _text(basis.get("source_eval_id")),
                "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint")),
                "work_unit_id": _text(basis.get("work_unit_id")),
                "blocked_reason": _text(basis.get("owner_reason")) or _text(closeout.get("blocked_reason")),
            },
        }, "embedded_currentness_basis"
    if stage_packet_route:
        return stage_packet_route, "stage_packet_ref_recovered"
    return {}, "missing"


def _stage_closeout_basis_missing_required_currentness(basis: Mapping[str, Any]) -> bool:
    if not basis:
        return True
    return not (
        _text(basis.get("truth_epoch"))
        and _text(basis.get("work_unit_fingerprint"))
        and _text(basis.get("work_unit_id"))
    )


def _stage_closeout_default_owner(action_type: str | None) -> str | None:
    if action_type == "run_quality_repair_batch":
        return "write"
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "current_package_freshness_required":
        return "artifact_os"
    return None


def _stage_closeout_stage_packet_owner_route(*, closeout: Mapping[str, Any], study_root: Path) -> dict[str, Any]:
    stage_packet_ref = _text(closeout.get("stage_packet_ref"))
    if not stage_packet_ref:
        return {}
    if not _stage_packet_ref_has_immutable_owner_route_identity(stage_packet_ref):
        return {}
    stage_packet = _read_json_object(_resolve_study_workspace_ref(study_root=study_root, ref=stage_packet_ref))
    if stage_packet is None:
        return {}
    if _text(stage_packet.get("action_type")) != _text(closeout.get("action_type")):
        return {}
    if _text(stage_packet.get("study_id")) != _text(closeout.get("study_id")):
        return {}
    return dict(_mapping(stage_packet.get("owner_route")) or _mapping(_mapping(stage_packet.get("prompt_contract")).get("owner_route")))


def _stage_packet_ref_has_immutable_owner_route_identity(stage_packet_ref: str) -> bool:
    parts = Path(stage_packet_ref).parts
    if "default_executor_dispatches" not in parts:
        return False
    dispatch_index = parts.index("default_executor_dispatches")
    return len(parts) > dispatch_index + 1 and parts[dispatch_index + 1] == "immutable"


def _stage_closeout_repair_evidence(closeout: Mapping[str, Any]) -> dict[str, Any]:
    artifact_delta = _mapping(closeout.get("artifact_delta"))
    domain_owner_evidence = _mapping(closeout.get("domain_owner_evidence"))
    changed_refs = _stage_closeout_changed_artifact_refs(artifact_delta.get("changed_artifact_refs"))
    story_delta_present = _stage_closeout_has_story_surface_delta(closeout)
    return {
        "status": (
            _text(domain_owner_evidence.get("repair_execution_status"))
            or _text(artifact_delta.get("status"))
            or _text(closeout.get("route_outcome"))
            or _text(closeout.get("status"))
        ),
        "changed_artifact_refs": changed_refs,
        "manuscript_surface_hygiene": {
            "status": _text(domain_owner_evidence.get("manuscript_surface_hygiene_status"))
            or _text(_mapping(artifact_delta.get("manuscript_surface_hygiene")).get("status")),
            "story_surface_delta_required": _text(closeout.get("action_type")) == "run_quality_repair_batch",
            "story_surface_delta_present": story_delta_present,
            "blockers": _mapping(artifact_delta.get("manuscript_surface_hygiene")).get("blockers") or [],
        },
        "gate_replay_done": domain_owner_evidence.get("gate_replay_done"),
        "ai_reviewer_recheck_required": domain_owner_evidence.get("ai_reviewer_recheck_required"),
        "ai_reviewer_recheck_done": domain_owner_evidence.get("ai_reviewer_recheck_done"),
    }


def _stage_closeout_changed_artifact_refs(value: object) -> list[Mapping[str, Any]]:
    refs: list[Mapping[str, Any]] = []
    for item in value or []:
        if isinstance(item, Mapping):
            refs.append(item)
        elif text := _text(item):
            refs.append({"path": text})
    return refs


def _stage_closeout_has_story_surface_delta(closeout: Mapping[str, Any]) -> bool:
    artifact_delta = _mapping(closeout.get("artifact_delta"))
    domain_owner_evidence = _mapping(closeout.get("domain_owner_evidence"))
    if domain_owner_evidence.get("story_surface_delta_present") is True:
        return True
    if artifact_delta.get("story_surface_delta_present") is True:
        return True
    return bool(_story_surface_changed_refs(_stage_closeout_changed_artifact_refs(artifact_delta.get("changed_artifact_refs"))))


def _story_surface_changed_refs(value: object) -> list[Mapping[str, Any]]:
    return [
        ref
        for ref in _mapping_list(value)
        if _is_story_surface_path(_text(ref.get("path")))
    ]


def _is_story_surface_path(path_text: str) -> bool:
    path = Path(path_text).expanduser()
    parts = path.parts
    return (
        len(parts) >= 2
        and parts[-2:] == ("paper", "draft.md")
        or len(parts) >= 3
        and parts[-3:] == ("paper", "build", "review_manuscript.md")
    )


def _resolve_study_workspace_ref(*, study_root: Path, ref: str) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "studies":
        workspace_root = _workspace_root_from_study_root(study_root)
        if workspace_root is not None:
            return workspace_root / path
    return study_root / path


def _workspace_root_from_study_root(study_root: Path) -> Path | None:
    resolved = study_root.expanduser().resolve()
    if resolved.parent.name == "studies":
        return resolved.parent.parent
    return None


def _study_relative_ref(*, study_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(study_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _read_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["default_executor_execution_candidates"]
