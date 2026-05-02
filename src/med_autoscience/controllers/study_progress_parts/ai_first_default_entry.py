from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.ai_reviewer_runtime_workflow import (
    build_ai_reviewer_runtime_workflow_state,
)
from med_autoscience.controllers.artifact_runtime_proof import build_artifact_runtime_proof
from med_autoscience.controllers.pre_draft_quality_runtime import (
    build_pre_draft_quality_runtime_state,
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _blocker_strings(value: object) -> list[str]:
    blockers: list[str] = []
    if not isinstance(value, list):
        return blockers
    for item in value:
        if isinstance(item, Mapping):
            text = _text(item.get("code")) or _text(item.get("summary")) or _text(item)
        else:
            text = _text(item)
        if text is not None and text not in blockers:
            blockers.append(text)
    return blockers


def _pre_draft_state(state: Mapping[str, Any]) -> dict[str, Any]:
    readiness = _mapping(state.get("readiness"))
    route_back = _mapping(state.get("route_back"))
    status = _text(state.get("status")) or "unknown"
    blockers = _blocker_strings(state.get("blockers"))
    if readiness.get("draft_ready") is True:
        summary = "写作前 AI-first readiness 已闭合，可以进入 first draft。"
    elif status == "review_required":
        summary = "写作前质量授权仍需 AI reviewer 复核。"
    else:
        summary = "写作前 readiness 未闭合，需要先回到 pre-draft 质量准备。"
    return {
        "surface": state.get("surface"),
        "status": status,
        "draft_ready": bool(readiness.get("draft_ready")),
        "summary": summary,
        "route_back_required": bool(route_back.get("required")),
        "route_back_target": route_back.get("target"),
        "route_back_reason": route_back.get("reason"),
        "blockers": blockers,
        "authority": {
            "mechanical_file_presence_can_authorize_ready": False,
            "mechanical_projection_can_authorize_ready": False,
        },
    }


def _ai_reviewer_state(state: Mapping[str, Any]) -> dict[str, Any]:
    finalize = _mapping(state.get("finalize_authorization"))
    submission = _mapping(state.get("submission_authorization"))
    route_back = _mapping(state.get("route_back"))
    quality_authority = _mapping(state.get("quality_authority"))
    blockers = _blocker_strings(state.get("blockers"))
    finalize_authorized = bool(finalize.get("authorized"))
    submission_authorized = bool(submission.get("authorized"))
    if finalize_authorized and submission_authorized:
        summary = "AI reviewer workflow 已授权 finalize/submission。"
    elif quality_authority.get("state") == "projection_only":
        summary = "当前质量判断仍是机械投影，只能进入 AI reviewer review-required。"
    else:
        summary = "AI reviewer workflow 尚未闭合，不能授权 finalize/submission。"
    return {
        "surface": state.get("surface"),
        "authority_state": quality_authority.get("state"),
        "authority_owner": quality_authority.get("owner"),
        "finalize_authorized": finalize_authorized,
        "submission_authorized": submission_authorized,
        "summary": summary,
        "route_back_required": bool(route_back.get("required")),
        "route_back_target": route_back.get("target"),
        "route_back_reason": route_back.get("reason"),
        "blockers": blockers,
        "authority": {
            "mechanical_projection_can_authorize_quality": False,
        },
    }


def _artifact_state(state: Mapping[str, Any]) -> dict[str, Any]:
    rebuild_status = _text(state.get("rebuild_status")) or "unknown"
    current = bool(state.get("current_package_from_canonical_source"))
    blockers = _blocker_strings(state.get("blockers"))
    if current and rebuild_status == "current":
        summary = "artifact rebuild proof 已确认 current package 来自 canonical source。"
    else:
        summary = "artifact rebuild proof 未闭合，current package 只能作为派生产物。"
    return {
        "surface": state.get("surface"),
        "rebuild_status": rebuild_status,
        "current_package_from_canonical_source": current,
        "summary": summary,
        "rebuild_pending": not current,
        "blockers": blockers,
        "authority": {
            "derived_artifact_can_authorize_submission": False,
            "derived_artifact_can_be_quality_authority": False,
            "derived_artifact_can_be_edit_source": False,
        },
    }


def _recommended_next_step(
    *,
    pre_draft: Mapping[str, Any],
    ai_reviewer: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> str:
    if pre_draft.get("draft_ready") is not True:
        return "先补齐 pre-draft readiness，再进入 first draft/write。"
    if ai_reviewer.get("finalize_authorized") is not True or ai_reviewer.get("submission_authorized") is not True:
        return "先回到 AI reviewer workflow，补齐 finalize/submission 质量授权。"
    if artifact.get("current_package_from_canonical_source") is not True:
        return "先从 canonical source 重建 manuscript/submission package。"
    return "继续当前写作、定稿或投稿包收口路径。"


def _route_back_reason(*, pre_draft: Mapping[str, Any], ai_reviewer: Mapping[str, Any], artifact: Mapping[str, Any]) -> str | None:
    return (
        _text(pre_draft.get("route_back_reason"))
        or _text(ai_reviewer.get("route_back_reason"))
        or ("canonical_artifact_rebuild_pending" if artifact.get("rebuild_pending") else None)
    )


def build_ai_first_default_entry_state(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    pre_draft = _pre_draft_state(build_pre_draft_quality_runtime_state(resolved_study_root))
    ai_reviewer = _ai_reviewer_state(build_ai_reviewer_runtime_workflow_state(resolved_study_root))
    artifact = _artifact_state(build_artifact_runtime_proof(resolved_study_root))
    blockers = [
        *[f"pre_draft:{item}" for item in pre_draft["blockers"]],
        *[f"ai_reviewer:{item}" for item in ai_reviewer["blockers"]],
        *[f"artifact:{item}" for item in artifact["blockers"]],
    ]
    route_back_required = (
        bool(pre_draft.get("route_back_required"))
        or bool(ai_reviewer.get("route_back_required"))
        or bool(artifact.get("rebuild_pending"))
    )
    human_review_required = (
        ai_reviewer.get("finalize_authorized") is not True
        or ai_reviewer.get("submission_authorized") is not True
    )
    if not route_back_required and not human_review_required:
        status = "ready_for_current_paper_route"
    elif ai_reviewer.get("authority_state") == "projection_only" or human_review_required:
        status = "review_required"
    else:
        status = "route_back_required"
    return {
        "surface": "ai_first_default_entry_state",
        "schema_version": 1,
        "read_model": "ai_first_default_entry_read_model",
        "study_root": str(resolved_study_root),
        "status": status,
        "summary": _recommended_next_step(
            pre_draft=pre_draft,
            ai_reviewer=ai_reviewer,
            artifact=artifact,
        ),
        "recommended_next_step": _recommended_next_step(
            pre_draft=pre_draft,
            ai_reviewer=ai_reviewer,
            artifact=artifact,
        ),
        "route_back": {
            "required": route_back_required,
            "reason": _route_back_reason(pre_draft=pre_draft, ai_reviewer=ai_reviewer, artifact=artifact),
            "pre_draft_target": pre_draft.get("route_back_target"),
            "ai_reviewer_target": ai_reviewer.get("route_back_target"),
            "artifact_target": "canonical_artifact_rebuild" if artifact.get("rebuild_pending") else None,
        },
        "human_review_required": human_review_required,
        "blockers": blockers,
        "pre_draft": pre_draft,
        "ai_reviewer_workflow": ai_reviewer,
        "artifact_proof": artifact,
        "counts": {
            "pre_draft_blocker_count": len(pre_draft["blockers"]),
            "ai_reviewer_blocker_count": len(ai_reviewer["blockers"]),
            "artifact_blocker_count": len(artifact["blockers"]),
            "total_blocker_count": len(blockers),
            "quality_ready_count": _int(pre_draft.get("draft_ready"))
            + _int(ai_reviewer.get("finalize_authorized"))
            + _int(ai_reviewer.get("submission_authorized"))
            + _int(artifact.get("current_package_from_canonical_source")),
        },
        "authority": {
            "default_entry_can_authorize_quality": False,
            "default_entry_can_mutate_runtime": False,
            "mechanical_projection_can_authorize_quality": False,
            "submission_readiness_requires_ai_reviewer": True,
            "derived_artifact_can_authorize_submission": False,
        },
    }


__all__ = ["build_ai_first_default_entry_state"]
