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
_CONTEXT_FIELDS_BY_ACTION_LABEL = {
    "ACCEPT_ANALYSIS": ("line_number", "citation_ref", "statistical_result"),
    "ACCEPT_TEXT": ("line_number", "citation_ref"),
    "SOFTEN_CLAIM": ("line_number", "citation_ref"),
    "DISAGREE": ("line_number", "citation_ref"),
    "AUTHOR_INPUT_NEEDED": ("citation_ref", "statistical_result"),
}


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


def _stable_concern_id(comment: Mapping[str, Any]) -> str:
    source = _text(comment.get("source")) or "reviewer"
    comment_id = _text(comment.get("comment_id")) or "unidentified"
    return f"{source}:{comment_id}"


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
    if _contains_any(
        combined,
        ("overstrong claim", "overstrong causal", "causal wording", "too strong", "restrained association"),
    ):
        return "claim_downgrade"
    if _contains_any(combined, ("human review", "human gate", "ethics", "approval")):
        return "human_gate"
    if _contains_any(combined, ("rebuttal only", "no change", "already addressed")):
        return "rebuttal_only"
    return "prose_revision"


def _action_label(comment: Mapping[str, Any], repair_type: str) -> str:
    combined = f"{_text(comment.get('concern'))} {_text(comment.get('requested_change'))}".lower()
    if _contains_any(combined, ("author", "rationale", "available", "unavailable")):
        return "AUTHOR_INPUT_NEEDED"
    if repair_type == "analysis_repair":
        return "ACCEPT_ANALYSIS"
    if repair_type == "claim_downgrade":
        return "SOFTEN_CLAIM"
    if repair_type == "rebuttal_only":
        return "DISAGREE"
    return "ACCEPT_TEXT"


def _missing_context_fields(comment: Mapping[str, Any], action_label: str) -> list[str]:
    required_fields = _CONTEXT_FIELDS_BY_ACTION_LABEL.get(action_label, ())
    return [field_name for field_name in required_fields if not _text(comment.get(field_name))]


def _repair_routes(
    comment: Mapping[str, Any],
    *,
    repair_type: str,
    ledger_refs: list[str],
) -> dict[str, Any]:
    analysis_repair_required = repair_type == "analysis_repair"
    text_repair_required = repair_type in {"claim_downgrade", "prose_revision"}
    recheck_reason = (
        "analysis_repair_requires_ai_reviewer_recheck"
        if analysis_repair_required
        else "text_repair_requires_ai_reviewer_recheck"
        if text_repair_required
        else "rebuttal_closure_requires_ai_reviewer_recheck"
    )
    target_claim = _text(comment.get("target_claim")) or None
    target_section = _text(comment.get("target_section")) or None
    return {
        "analysis_repair": {
            "required": analysis_repair_required,
            "target_claim": target_claim,
            "target_section": target_section,
            "ledger_refs": ledger_refs,
        },
        "text_repair": {
            "required": text_repair_required,
            "target_claim": target_claim,
            "target_section": target_section,
            "ledger_refs": ledger_refs,
        },
        "ai_reviewer_recheck": {
            "required": True,
            "reason": recheck_reason,
        },
    }


def _action_type(repair_type: str) -> str:
    if repair_type == "analysis_repair":
        return "analysis_repair"
    if repair_type in {"claim_downgrade", "prose_revision"}:
        return "text_repair"
    if repair_type == "human_gate":
        return "human_gate"
    return "rebuttal_only"


def _work_units(repair_routes: Mapping[str, Any], ledger_refs: list[str]) -> dict[str, Any]:
    analysis_repair = dict(repair_routes["analysis_repair"])
    text_repair = dict(repair_routes["text_repair"])
    ai_reviewer_recheck = dict(repair_routes["ai_reviewer_recheck"])
    analysis_repair["work_unit_type"] = "analysis_repair"
    text_repair["work_unit_type"] = "text_repair"
    ai_reviewer_recheck["work_unit_type"] = "ai_reviewer_recheck"
    ai_reviewer_recheck["ledger_refs"] = ledger_refs
    return {
        "analysis_repair": analysis_repair,
        "text_repair": text_repair,
        "ai_reviewer_recheck": ai_reviewer_recheck,
    }


def _action_matrix_item(
    comment: Mapping[str, Any],
    *,
    evidence_ledger_refs: list[str],
    review_ledger_refs: list[str],
) -> dict[str, Any]:
    comment_id = _text(comment.get("comment_id"))
    repair_type = _repair_type(comment)
    action_label = _action_label(comment, repair_type)
    missing_context_fields = _missing_context_fields(comment, action_label)
    required_surface_refs = _required_surface_refs(evidence_ledger_refs, review_ledger_refs)
    repair_routes = _repair_routes(
        comment,
        repair_type=repair_type,
        ledger_refs=required_surface_refs,
    )
    ai_reviewer_recheck_required = repair_routes["ai_reviewer_recheck"]["required"]
    action_type = _action_type(repair_type)
    return {
        "comment_id": comment_id,
        "stable_concern_id": _stable_concern_id(comment),
        "repair_type": repair_type,
        "action_type": action_type,
        "action_label": "AUTHOR_INPUT_NEEDED" if missing_context_fields else action_label,
        "missing_context_fields": missing_context_fields,
        "required_surface_refs": required_surface_refs,
        "work_units": _work_units(repair_routes, required_surface_refs),
        "repair_routes": repair_routes,
        "ai_reviewer_recheck_required": ai_reviewer_recheck_required,
        "response_letter_point": (
            f"Response to {comment_id}: route to {action_type} for the requested change; "
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


def _repair_plan(action_matrix: list[dict[str, Any]]) -> dict[str, bool]:
    analysis_repair_required = any(
        item["repair_routes"]["analysis_repair"]["required"] for item in action_matrix
    )
    text_repair_required = any(item["repair_routes"]["text_repair"]["required"] for item in action_matrix)
    ai_reviewer_recheck_required = any(item["ai_reviewer_recheck_required"] for item in action_matrix)
    return {
        "analysis_repair_required": analysis_repair_required,
        "text_repair_required": text_repair_required,
        "ai_reviewer_recheck_required": ai_reviewer_recheck_required,
        "mechanical_projection_can_authorize_quality": False,
    }


def _comment_response_tracker(action_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tracker: list[dict[str, Any]] = []
    for item in action_matrix:
        missing_fields = list(item.get("missing_context_fields") or [])
        tracker.append(
            {
                "stable_concern_id": item["stable_concern_id"],
                "comment_id": item["comment_id"],
                "action_label": item["action_label"],
                "response_status": "author_input_needed" if missing_fields else "planned",
                "response_letter_point": item["response_letter_point"],
                "blocking_missing_fields": missing_fields,
                "read_model_only": True,
            }
        )
    return tracker


def _manuscript_change_checklist(action_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checklist: list[dict[str, Any]] = []
    for item in action_matrix:
        action_label = item["action_label"]
        target_section = item["repair_routes"]["analysis_repair"]["target_section"]
        stable_concern_id = item["stable_concern_id"]
        if action_label == "AUTHOR_INPUT_NEEDED":
            check_item = f"Collect author input for {stable_concern_id} before drafting a rebuttal."
            change_required = False
        else:
            check_item = f"Update {target_section} for {stable_concern_id} before response closure."
            change_required = True
        checklist.append(
            {
                "stable_concern_id": stable_concern_id,
                "comment_id": item["comment_id"],
                "action_label": action_label,
                "target_section": target_section,
                "target_claim": item["repair_routes"]["analysis_repair"]["target_claim"],
                "change_required": change_required,
                "check_item": check_item,
                "read_model_only": True,
            }
        )
    return checklist


def _missing_author_input_list(action_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for item in action_matrix:
        missing_fields = list(item.get("missing_context_fields") or [])
        if item["action_label"] != "AUTHOR_INPUT_NEEDED" and not missing_fields:
            continue
        missing.append(
            {
                "stable_concern_id": item["stable_concern_id"],
                "comment_id": item["comment_id"],
                "source": item["stable_concern_id"].split(":", 1)[0],
                "missing_fields": missing_fields,
                "reason": "rebuttal_context_incomplete",
            }
        )
    return missing


def _response_package_readiness(
    *,
    blockers: list[str],
    action_matrix: list[dict[str, Any]],
) -> dict[str, Any]:
    readiness_blockers = list(blockers)
    for item in action_matrix:
        if item["action_label"] == "AUTHOR_INPUT_NEEDED":
            readiness_blockers.append(f"author_input_needed:{item['stable_concern_id']}")
        for field_name in item.get("missing_context_fields") or []:
            readiness_blockers.append(f"reviewer_comment_missing_{field_name}:{item['comment_id']}")
    return {
        "status": "blocked" if readiness_blockers else "planning_ready",
        "ready": not readiness_blockers,
        "blockers": readiness_blockers,
        "read_model_only": True,
        "publication_readiness_authorized": False,
        "current_package_mutation_allowed": False,
    }


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
    response_package_readiness = _response_package_readiness(
        blockers=blockers,
        action_matrix=action_matrix,
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "reviewer_comment_count": len(comments),
        "action_matrix": action_matrix,
        "comment_to_action_matrix": action_matrix,
        "comment_response_tracker": _comment_response_tracker(action_matrix),
        "manuscript_change_checklist": _manuscript_change_checklist(action_matrix),
        "missing_author_input_list": _missing_author_input_list(action_matrix),
        "response_package_readiness": response_package_readiness,
        "repair_plan": _repair_plan(action_matrix),
        "next_action": _next_action(blockers=blockers, action_matrix=action_matrix),
        "durable_refs": {
            "evidence_ledger_refs": evidence_ledger_refs,
            "review_ledger_refs": review_ledger_refs,
        },
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "publication_readiness_authorized": False,
        "current_package_mutation_allowed": False,
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
