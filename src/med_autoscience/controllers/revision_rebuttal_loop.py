from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SURFACE = "revision_rebuttal_loop"
SCHEMA_VERSION = 1
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/revision_rebuttal_loop.json")

_COMMENT_REQUIRED_FIELDS = (
    "comment_id",
    "source",
    "concern",
    "severity",
    "requested_change",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in _list(value) if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    return [_text(item) for item in _list(value) if _text(item)]


def _contains_any(value: object, needles: tuple[str, ...]) -> bool:
    text = _text(value).lower()
    return any(needle in text for needle in needles)


def _comment_identifier(comment: Mapping[str, Any], index: int) -> str:
    return _text(comment.get("comment_id")) or f"comment_{index + 1}"


def _comment_blockers(comments: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for index, comment in enumerate(comments):
        comment_id = _comment_identifier(comment, index)
        for field_name in _COMMENT_REQUIRED_FIELDS:
            if not _text(comment.get(field_name)):
                blockers.append(f"reviewer_comment_missing_{field_name}:{comment_id}")
        if not (_text(comment.get("target_section")) or _text(comment.get("target_claim"))):
            blockers.append(f"reviewer_comment_missing_target:{comment_id}")
    return blockers


def _required_surface_refs(
    evidence_ledger_refs: list[str],
    review_ledger_refs: list[str],
) -> list[str]:
    return [*evidence_ledger_refs, *review_ledger_refs]


def _repair_type(comment: Mapping[str, Any]) -> str:
    concern = _text(comment.get("concern"))
    requested_change = _text(comment.get("requested_change"))
    severity = _text(comment.get("severity")).lower()
    combined = f"{concern} {requested_change}"
    if severity == "major" and _contains_any(requested_change, ("additional analysis", "additional analyses")):
        return "analysis_repair"
    if _contains_any(combined, ("overstrong claim", "overstrong causal", "causal wording")):
        return "claim_downgrade"
    if _contains_any(combined, ("human review", "human gate", "ethics", "approval")):
        return "human_gate"
    if _contains_any(combined, ("rebuttal only", "no change", "already addressed")):
        return "rebuttal_only"
    return "prose_revision"


def _action_matrix_item(
    comment: Mapping[str, Any],
    *,
    evidence_ledger_refs: list[str],
    review_ledger_refs: list[str],
) -> dict[str, Any]:
    comment_id = _text(comment.get("comment_id"))
    repair_type = _repair_type(comment)
    ai_reviewer_recheck_required = repair_type == "analysis_repair"
    return {
        "comment_id": comment_id,
        "repair_type": repair_type,
        "required_surface_refs": _required_surface_refs(evidence_ledger_refs, review_ledger_refs),
        "ai_reviewer_recheck_required": ai_reviewer_recheck_required,
        "response_letter_point": (
            f"Response to {comment_id}: route to {repair_type} for the requested change; "
            "cite the repaired surfaces before rebuttal closure."
        ),
    }


def _next_action(*, blockers: list[str], action_matrix: list[dict[str, Any]]) -> dict[str, str]:
    if blockers:
        return {
            "action": "collect_revision_intake",
            "reason": blockers[0],
        }
    if any(item["ai_reviewer_recheck_required"] for item in action_matrix):
        return {
            "action": "repair_recheck_required",
            "reason": "analysis_repair_requires_ai_reviewer_recheck",
        }
    return {
        "action": "draft_rebuttal_and_recheck",
        "reason": "revision_action_matrix_ready",
    }


def _blockers(
    *,
    comments: list[dict[str, Any]],
    evidence_ledger_refs: list[str],
    review_ledger_refs: list[str],
) -> list[str]:
    blockers: list[str] = []
    if not comments:
        blockers.append("missing_reviewer_comments")
    if not evidence_ledger_refs:
        blockers.append("missing_evidence_ledger_refs")
    if not review_ledger_refs:
        blockers.append("missing_review_ledger_refs")
    if comments:
        blockers.extend(_comment_blockers(comments))
    return blockers


def build_revision_rebuttal_loop_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    comments = _mapping_list(payload.get("reviewer_comments"))
    evidence_ledger_refs = _text_list(payload.get("evidence_ledger_refs"))
    review_ledger_refs = _text_list(payload.get("review_ledger_refs"))
    blockers = _blockers(
        comments=comments,
        evidence_ledger_refs=evidence_ledger_refs,
        review_ledger_refs=review_ledger_refs,
    )
    action_matrix = (
        []
        if blockers
        else [
            _action_matrix_item(
                comment,
                evidence_ledger_refs=evidence_ledger_refs,
                review_ledger_refs=review_ledger_refs,
            )
            for comment in comments
        ]
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "reviewer_comment_count": len(comments),
        "action_matrix": action_matrix,
        "next_action": _next_action(blockers=blockers, action_matrix=action_matrix),
        "durable_refs": {
            "evidence_ledger_refs": evidence_ledger_refs,
            "review_ledger_refs": review_ledger_refs,
        },
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def stable_revision_rebuttal_loop_path(study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize_revision_rebuttal_loop(
    study_root: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    artifact_path = stable_revision_rebuttal_loop_path(study_root)
    projection = build_revision_rebuttal_loop_projection(payload)
    _write_json(artifact_path, projection)
    return {
        "surface": SURFACE,
        "status": projection["status"],
        "artifact_path": str(artifact_path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
