from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "ai_first_cross_study_completion_projection"
READ_MODEL = "ai_first_cross_study_completion_read_model"
LOW_LEVEL_FIELD_HINTS = ("raw_terminal_log", "full_prompt", "prompt", "secret", "token", "log_path")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text or default


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_governance_only",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "can_mutate_runtime": False,
        "mechanical_projection_is_quality_authority": False,
    }


def _study_id_from_root(study_root: Path) -> str:
    return study_root.name


def _study_roots_from_studies_root(studies_root: str | Path) -> list[Path]:
    root = Path(studies_root).expanduser()
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))


def _collect_redacted_fields(value: object, redacted: set[str]) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if any(hint in str(key) for hint in LOW_LEVEL_FIELD_HINTS):
                redacted.add(str(key))
            _collect_redacted_fields(nested, redacted)
        return
    if isinstance(value, list):
        for item in value:
            _collect_redacted_fields(item, redacted)


def _redacted_fields(*snapshots: Mapping[str, Any]) -> list[str]:
    redacted: set[str] = set()
    for snapshot in snapshots:
        _collect_redacted_fields(snapshot, redacted)
    return sorted(redacted)


def _feedback_state_from_root(study_root: Path) -> Mapping[str, Any]:
    for path in (
        study_root / "artifacts" / "runtime" / "ai_first_feedback_state" / "latest.json",
        study_root / "artifacts" / "runtime" / "ai_first_feedback" / "latest.json",
    ):
        payload = _read_json_object(path)
        if payload is not None:
            return payload
    return {}


def _dispatch_ledger_from_root(study_root: Path) -> Mapping[str, Any]:
    for path in (
        study_root / "artifacts" / "runtime" / "dispatch_ledger" / "latest.json",
        study_root / "artifacts" / "runtime" / "action_dispatch" / "dispatch_ledger.json",
    ):
        payload = _read_json_object(path)
        if payload is not None:
            return payload
    return {}


def _artifact_proof_from_root(study_root: Path) -> Mapping[str, Any]:
    for path in (
        study_root / "artifacts" / "runtime" / "artifact_runtime_proof" / "latest.json",
        study_root / "artifacts" / "artifact_runtime_proof" / "latest.json",
    ):
        payload = _read_json_object(path)
        if payload is not None:
            return payload
    delivery_manifest = _read_json_object(study_root / "manuscript" / "delivery_manifest.json")
    if delivery_manifest is None:
        return {}
    blocking_refs = _list(delivery_manifest.get("blocking_artifact_refs"))
    source_signature = _text(delivery_manifest.get("source_signature"), "")
    authority_signature = _text(delivery_manifest.get("authority_source_signature"), "")
    delivery_signature = _text(delivery_manifest.get("delivery_source_signature"), "")
    current = bool(source_signature) and len({source_signature, authority_signature, delivery_signature}) == 1
    return {
        "surface": "artifact_runtime_proof",
        "rebuild_status": "current" if current and not blocking_refs else "blocked",
        "current_package_from_canonical_source": current and not blocking_refs,
        "blockers": blocking_refs,
    }


def _publication_eval_from_root(study_root: Path) -> Mapping[str, Any]:
    return _read_json_object(study_root / "artifacts" / "publication_eval" / "latest.json") or {}


def _ai_reviewer_authority(
    *,
    progress_snapshot: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
) -> dict[str, Any]:
    default_entry = _mapping(progress_snapshot.get("ai_first_default_entry_state"))
    workflow = _mapping(default_entry.get("ai_reviewer_workflow"))
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    reviewer_trace = _mapping(publication_eval.get("reviewer_operating_system"))
    owner = _text(provenance.get("owner"), _text(workflow.get("authority_owner"), "unknown"))
    trace_complete = _bool(workflow.get("trace_complete"))
    if trace_complete is None:
        trace_complete = (
            owner == "ai_reviewer"
            and provenance.get("ai_reviewer_required") is False
            and bool(reviewer_trace)
        )
    reviewer_backed = owner == "ai_reviewer" and trace_complete is True
    return {
        "owner": owner,
        "reviewer_backed": reviewer_backed,
        "trace_complete": trace_complete,
        "finalize_authorized_observed": _bool(workflow.get("finalize_authorized")),
        "submission_authorized_observed": _bool(workflow.get("submission_authorized")),
        "authority_contract": _authority_contract(),
    }


def _dispatch_state(dispatch_ledger: Mapping[str, Any]) -> dict[str, Any]:
    actions = [item for item in _list(dispatch_ledger.get("actions")) if isinstance(item, Mapping)]
    if not actions:
        actions = [item for item in _list(dispatch_ledger.get("dispatches")) if isinstance(item, Mapping)]
    open_actions = [
        item
        for item in actions
        if _text(item.get("status"), "open") not in {"closed", "complete", "completed", "succeeded"}
    ]
    failed_actions = [
        item
        for item in actions
        if _text(item.get("status"), "open") in {"failed", "blocked", "error"}
    ]
    latest = actions[-1] if actions else {}
    return {
        "surface": _text(dispatch_ledger.get("surface"), "dispatch_ledger"),
        "present": bool(dispatch_ledger),
        "total_action_count": len(actions),
        "open_action_count": len(open_actions),
        "failed_action_count": len(failed_actions),
        "latest_action_id": _text(latest.get("action_id"), ""),
        "latest_status": _text(latest.get("status"), ""),
        "authority_contract": _authority_contract(),
    }


def _artifact_state(artifact_proof: Mapping[str, Any]) -> dict[str, Any]:
    blockers = _list(artifact_proof.get("blockers"))
    current = _bool(artifact_proof.get("current_package_from_canonical_source"))
    rebuild_pending = _bool(artifact_proof.get("rebuild_pending"))
    if rebuild_pending is None:
        rebuild_pending = bool(blockers) or current is not True
    return {
        "surface": _text(artifact_proof.get("surface"), "artifact_runtime_proof"),
        "present": bool(artifact_proof),
        "rebuild_status": _text(artifact_proof.get("rebuild_status"), "unknown"),
        "current_package_from_canonical_source": current,
        "rebuild_pending": rebuild_pending,
        "blocker_count": len(blockers),
        "authority_contract": _authority_contract(),
    }


def _human_review_required(
    *,
    progress_snapshot: Mapping[str, Any],
    feedback_state: Mapping[str, Any],
) -> bool:
    if progress_snapshot.get("needs_user_decision") is True or progress_snapshot.get("needs_physician_decision") is True:
        return True
    default_entry = _mapping(progress_snapshot.get("ai_first_default_entry_state"))
    if default_entry.get("human_review_required") is True:
        return True
    feedback_user = _mapping(feedback_state.get("user_view"))
    return feedback_user.get("human_review_required") is True


def _external_owner_state(progress_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    owner = _text(
        progress_snapshot.get("external_owner")
        or progress_snapshot.get("external_runtime_owner")
        or progress_snapshot.get("parked_owner"),
        "unknown",
    )
    return {
        "owner": owner,
        "present": owner != "unknown",
        "authority_contract": _authority_contract(),
    }


def _feedback_summary(feedback_state: Mapping[str, Any]) -> dict[str, Any]:
    counts = _mapping(feedback_state.get("counts"))
    primary_action = _mapping(feedback_state.get("primary_action"))
    user_view = _mapping(feedback_state.get("user_view"))
    return {
        "surface": _text(feedback_state.get("surface"), "ai_first_feedback_state"),
        "present": bool(feedback_state),
        "status": _text(feedback_state.get("status"), "unknown"),
        "open_feedback_count": _int(counts.get("open_feedback_count")),
        "primary_action_id": _text(primary_action.get("action_id"), ""),
        "next_action": _text(user_view.get("next_action"), _text(primary_action.get("summary"), "")),
        "authority_contract": _authority_contract(),
    }


def _study_completion_status(
    *,
    feedback: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    ai_reviewer: Mapping[str, Any],
    artifact: Mapping[str, Any],
    human_review_required: bool,
) -> str:
    if not feedback.get("present") and not dispatch.get("present") and not artifact.get("present"):
        return "insufficient_observability"
    if (
        _int(feedback.get("open_feedback_count")) > 0
        or _int(dispatch.get("open_action_count")) > 0
        or _int(dispatch.get("failed_action_count")) > 0
        or artifact.get("rebuild_pending") is True
        or ai_reviewer.get("reviewer_backed") is not True
        or human_review_required
    ):
        return "attention_required"
    return "on_track"


def _build_study_item(
    *,
    study_root: Path,
    progress_snapshot: Mapping[str, Any],
    use_study_root_artifact_fallbacks: bool = True,
) -> dict[str, Any]:
    feedback_state = _mapping(progress_snapshot.get("ai_first_feedback_state"))
    if not feedback_state and use_study_root_artifact_fallbacks:
        feedback_state = _feedback_state_from_root(study_root)
    dispatch_ledger = _mapping(progress_snapshot.get("dispatch_ledger"))
    if not dispatch_ledger and use_study_root_artifact_fallbacks:
        dispatch_ledger = _dispatch_ledger_from_root(study_root)
    artifact_proof = (
        _mapping(_mapping(progress_snapshot.get("ai_first_default_entry_state")).get("artifact_proof"))
    )
    if not artifact_proof and use_study_root_artifact_fallbacks:
        artifact_proof = _artifact_proof_from_root(study_root)
    publication_eval = _mapping(progress_snapshot.get("publication_eval"))
    if not publication_eval and use_study_root_artifact_fallbacks:
        publication_eval = _publication_eval_from_root(study_root)
    feedback = _feedback_summary(feedback_state)
    dispatch = _dispatch_state(dispatch_ledger)
    ai_reviewer = _ai_reviewer_authority(
        progress_snapshot=progress_snapshot,
        publication_eval=publication_eval,
    )
    artifact = _artifact_state(artifact_proof)
    external_owner = _external_owner_state(progress_snapshot)
    human_review_required = _human_review_required(
        progress_snapshot=progress_snapshot,
        feedback_state=feedback_state,
    )
    status = _study_completion_status(
        feedback=feedback,
        dispatch=dispatch,
        ai_reviewer=ai_reviewer,
        artifact=artifact,
        human_review_required=human_review_required,
    )
    study_id = _text(progress_snapshot.get("study_id"), _study_id_from_root(study_root))
    next_action = (
        _text(feedback.get("next_action"), "")
        or _text(progress_snapshot.get("next_system_action"), "")
        or ("human_review_required" if human_review_required else "continue_current_route")
    )
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "status": status,
        "user_view": {
            "study_id": study_id,
            "status": status,
            "current_stage": _text(progress_snapshot.get("current_stage"), "unknown"),
            "next_action": next_action,
            "human_review_required": human_review_required,
        },
        "maintainer_view": {
            "feedback": feedback,
            "dispatch": dispatch,
            "ai_reviewer_authority": ai_reviewer,
            "artifact_proof": artifact,
            "human_review": {"required": human_review_required},
            "external_owner": external_owner,
            "redacted_fields": _redacted_fields(
                progress_snapshot,
                feedback_state,
                dispatch_ledger,
                artifact_proof,
            ),
        },
        "authority_contract": _authority_contract(),
    }


def build_ai_first_cross_study_completion_projection(
    *,
    studies_root: str | Path | None = None,
    study_roots: list[str | Path] | None = None,
    progress_snapshots: Mapping[str, Mapping[str, Any]] | None = None,
    use_study_root_artifact_fallbacks: bool = True,
) -> dict[str, Any]:
    roots = [Path(path).expanduser() for path in (study_roots or [])]
    if studies_root is not None:
        roots.extend(path for path in _study_roots_from_studies_root(studies_root) if path not in roots)
    snapshot_by_study = progress_snapshots or {}
    if not roots and snapshot_by_study:
        roots = [Path(study_id) for study_id in sorted(snapshot_by_study)]
    study_items = [
        _build_study_item(
            study_root=root,
            progress_snapshot=_mapping(snapshot_by_study.get(root.name)),
            use_study_root_artifact_fallbacks=use_study_root_artifact_fallbacks,
        )
        for root in sorted(roots)
    ]
    attention = [item for item in study_items if item["status"] == "attention_required"]
    insufficient = [item for item in study_items if item["status"] == "insufficient_observability"]
    human_review_count = sum(1 for item in study_items if item["user_view"]["human_review_required"])
    if attention:
        status = "attention_required"
        primary_next_action = attention[0]["user_view"]["next_action"]
    elif insufficient:
        status = "insufficient_observability"
        primary_next_action = "materialize_ai_first_feedback_dispatch_and_artifact_surfaces"
    else:
        status = "on_track"
        primary_next_action = "continue_current_study_routes"
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "status": status,
        "authority": "observability_governance_only",
        "user_view": {
            "status": status,
            "study_count": len(study_items),
            "attention_required_count": len(attention),
            "human_review_required_count": human_review_count,
            "primary_next_action": primary_next_action,
            "studies": [item["user_view"] for item in study_items],
        },
        "maintainer_view": {
            "study_count": len(study_items),
            "attention_required_count": len(attention),
            "insufficient_observability_count": len(insufficient),
            "human_review_required_count": human_review_count,
            "studies": [item["maintainer_view"] | {"study_id": item["study_id"]} for item in study_items],
        },
        "studies": study_items,
        "authority_contract": _authority_contract(),
    }
