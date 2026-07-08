from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import revision_rebuttal_loop


def payload_from_revision_rebuttal_loop_sources(
    *,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    publication_eval_path = root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = _read_json(publication_eval_path)
    if not publication_eval:
        return {}
    evidence_ledger_refs = _evidence_ledger_refs(root)
    review_ledger_refs = _review_ledger_refs(root)
    if not evidence_ledger_refs or not review_ledger_refs:
        return {}
    reviewer_comments = _reviewer_comments(publication_eval)
    if not reviewer_comments:
        return {}
    payload = {
        "reviewer_comments": reviewer_comments,
        "evidence_ledger_refs": evidence_ledger_refs,
        "review_ledger_refs": review_ledger_refs,
        "payload_source": source,
        "source_basis": "publication_eval_review_and_evidence_ledgers",
        "source_refs": [
            str(publication_eval_path),
            *evidence_ledger_refs,
            *review_ledger_refs,
        ],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    projection = revision_rebuttal_loop.build_revision_rebuttal_loop_projection(payload)
    if _text(projection.get("status")) != "ready":
        return {}
    return {
        **dict(projection),
        **payload,
        "surface": revision_rebuttal_loop.SURFACE,
        "schema_version": revision_rebuttal_loop.SCHEMA_VERSION,
        "status": "ready",
    }


def _reviewer_comments(publication_eval: Mapping[str, Any]) -> list[dict[str, Any]]:
    comments = [
        *_comments_from_quality_assessment(publication_eval),
        *_comments_from_gaps(publication_eval),
    ]
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for comment in comments:
        comment_id = _text(comment.get("comment_id"))
        if not comment_id or comment_id in seen:
            continue
        seen.add(comment_id)
        deduped.append(comment)
    return deduped


def _comments_from_quality_assessment(publication_eval: Mapping[str, Any]) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    for dimension, raw in _mapping(publication_eval.get("quality_assessment")).items():
        item = _mapping(raw)
        status = _text(item.get("status"))
        if not status or status == "ready":
            continue
        summary = _text(item.get("summary"))
        if not summary:
            continue
        requested_change = _text(item.get("reviewer_revision_advice")) or summary
        section = _text(dimension)
        if section in {"claim", "evidence", "evidence_strength"} and "analysis" not in requested_change.lower():
            requested_change = f"Add additional analysis or evidence repair before acceptance. {requested_change}"
        comments.append(
            {
                "comment_id": f"quality_dimension:{section}",
                "source": "ai_reviewer",
                "concern": summary,
                "severity": _severity(item.get("severity")),
                "requested_change": requested_change,
                "target_section": section,
                "target_claim": _target_claim(item),
            }
        )
    return comments


def _comments_from_gaps(publication_eval: Mapping[str, Any]) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    for gap in _mapping_list(publication_eval.get("gaps")):
        gap_id = _text(gap.get("gap_id"))
        summary = _text(gap.get("summary"))
        if not gap_id or not summary:
            continue
        gap_type = _text(gap.get("gap_type")) or "paper"
        comments.append(
            {
                "comment_id": f"publication_gap:{gap_id}",
                "source": "ai_reviewer",
                "concern": summary,
                "severity": _severity(gap.get("severity")),
                "requested_change": _text(gap.get("reviewer_revision_advice"))
                or _requested_change_for_gap(gap_type=gap_type, summary=summary),
                "target_section": gap_type,
                "target_claim": _target_claim(gap),
            }
        )
    return comments


def _requested_change_for_gap(*, gap_type: str, summary: str) -> str:
    if gap_type in {"claim", "evidence", "evidence_strength"}:
        return f"Add additional analysis or evidence repair before acceptance. {summary}"
    return f"Repair this reviewer concern before acceptance. {summary}"


def _severity(value: object) -> str:
    severity = _text(value).lower()
    if severity in {"must_fix", "important", "critical"}:
        return "major"
    if severity in {"major", "minor"}:
        return severity
    return "major"


def _target_claim(item: Mapping[str, Any]) -> str | None:
    for key in ("claim_id", "target_claim"):
        if text := _text(item.get(key)):
            return text
    refs = [*_text_list(item.get("evidence_refs")), *_text_list(item.get("artifact_refs"))]
    for ref in refs:
        marker = ref.rsplit("#", 1)[-1].strip()
        if marker and marker.lower().startswith("c"):
            return marker
    return None


def _evidence_ledger_refs(root: Path) -> list[str]:
    candidates = [
        root / "paper" / "evidence_ledger.json",
        root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper" / "evidence_ledger.json",
        root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "manuscript" / "audit" / "evidence_ledger.json",
        root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "manuscript" / "current_package" / "audit" / "evidence_ledger.json",
    ]
    refs = [str(path) for path in candidates if _json_object_exists(path)]
    claim_map = root / "paper" / "claim_evidence_map.json"
    if _json_object_exists(claim_map):
        refs.append(str(claim_map))
    return list(dict.fromkeys(refs))


def _review_ledger_refs(root: Path) -> list[str]:
    candidates = [
        root / "paper" / "review" / "review_ledger.json",
        root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper" / "review" / "review_ledger.json",
        root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "manuscript" / "review" / "review_ledger.json",
        root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "manuscript" / "current_package" / "audit" / "review_ledger.json",
    ]
    return list(dict.fromkeys(str(path) for path in candidates if _json_object_exists(path)))


def _json_object_exists(path: Path) -> bool:
    return bool(_read_json(path))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _text_list(value: object) -> list[str]:
    return [_text(item) for item in value if _text(item)] if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["payload_from_revision_rebuttal_loop_sources"]
