from __future__ import annotations

from typing import Any

from .refs_json_helpers import refs_from_value, text, unique_refs


def structured_independent_ai_reviewer_evaluation(
    *,
    study_id: str,
    target_agent_id: str,
    publication_eval: dict[str, Any] | None,
    publication_eval_ref: str,
    evidence_refs: list[str],
    feedback_ref: str | None,
    authority_boundary: dict[str, Any],
) -> dict[str, Any]:
    payload = publication_eval or {}
    quality = payload.get("quality_assessment") if isinstance(payload, dict) else {}
    provenance = payload.get("assessment_provenance")
    direct_evidence_refs = unique_refs(
        [
            publication_eval_ref,
            *evidence_refs,
            *(refs_from_value(payload.get("runtime_context_refs")) if payload else []),
            *(refs_from_value(payload.get("delivery_context_refs")) if payload else []),
            *(refs_from_value(payload.get("recommended_actions")) if payload else []),
            *([feedback_ref] if feedback_ref else []),
        ]
    )
    return {
        "surface_kind": "mas_structured_independent_ai_reviewer_evaluation",
        "schema_version": 1,
        "evaluation_ref": (
            f"structured-ai-reviewer-evaluation:mas/{study_id}/publication_eval_latest"
        ),
        "study_id": study_id,
        "target_agent_id": target_agent_id,
        "source_publication_eval_ref": publication_eval_ref,
        "critique": _publication_eval_critique(payload),
        "suggestions": _publication_eval_suggestions(payload),
        "direct_evidence_refs": direct_evidence_refs,
        "provenance": {
            "owner": "med-autoscience",
            "source_kind": "publication_eval_ai_reviewer_projection",
            "source_eval_id": text(payload.get("eval_id")),
            "source_assessment_provenance": dict(provenance)
            if isinstance(provenance, dict)
            else {},
            "projection_role": "oma_structured_reviewer_input",
            "quality_dimensions": sorted(quality.keys()) if isinstance(quality, dict) else [],
            "refs_only": True,
            "candidate_is_authority": False,
            "can_authorize_quality_verdict": False,
            "can_write_study_truth": False,
        },
        "authority_boundary": dict(authority_boundary),
    }


def _publication_eval_critique(publication_eval: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    verdict = publication_eval.get("verdict") if publication_eval else {}
    verdict_summary = (
        text((verdict or {}).get("summary")) if isinstance(verdict, dict) else None
    )
    if verdict_summary is not None:
        result.append(
            {
                "critique_id": "publication_eval_verdict_summary",
                "severity": text((verdict or {}).get("overall_verdict")) or "review",
                "summary": verdict_summary,
                "direct_evidence_refs": ["artifacts/publication_eval/latest.json"],
            }
        )
    quality = publication_eval.get("quality_assessment")
    if isinstance(quality, dict):
        for key, value in quality.items():
            item = value if isinstance(value, dict) else {}
            summary = text(item.get("summary") or item.get("rationale"))
            status = text(item.get("status")) or "review"
            if summary is None:
                continue
            result.append(
                {
                    "critique_id": f"quality_assessment:{key}",
                    "severity": status,
                    "summary": summary,
                    "direct_evidence_refs": ["artifacts/publication_eval/latest.json"],
                }
            )
    gaps = publication_eval.get("gaps")
    if isinstance(gaps, list):
        for index, gap in enumerate(gaps, start=1):
            item = gap if isinstance(gap, dict) else {}
            summary = text(
                item.get("summary")
                or item.get("description")
                or item.get("gap")
                or item.get("reason")
            )
            if summary is None:
                continue
            result.append(
                {
                    "critique_id": text(item.get("gap_id")) or f"gap:{index}",
                    "severity": text(item.get("severity")) or "gap",
                    "summary": summary,
                    "direct_evidence_refs": refs_from_value(item) or [
                        "artifacts/publication_eval/latest.json"
                    ],
                }
            )
    if result:
        return result
    return [
        {
            "critique_id": "publication_eval_structured_review_missing",
            "severity": "blocked",
            "summary": (
                "Publication evaluation exists but lacks structured critique details; "
                "OMA should route this as a reviewer-evidence contract gap."
            ),
            "direct_evidence_refs": ["artifacts/publication_eval/latest.json"],
        }
    ]


def _publication_eval_suggestions(publication_eval: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    actions = publication_eval.get("recommended_actions")
    if isinstance(actions, list):
        for index, action in enumerate(actions, start=1):
            item = action if isinstance(action, dict) else {}
            summary = text(
                item.get("summary")
                or item.get("action")
                or item.get("recommended_action")
                or item.get("description")
            )
            if summary is None:
                continue
            result.append(
                {
                    "suggestion_id": text(item.get("action_id")) or f"action:{index}",
                    "summary": summary,
                    "target_refs": refs_from_value(item) or [
                        "artifacts/publication_eval/latest.json"
                    ],
                }
            )
    if result:
        return result
    return [
        {
            "suggestion_id": "route_to_mas_owner_review_or_write",
            "summary": (
                "Use MAS owner route to convert reviewer critique into an accepted "
                "paper delta, owner receipt, typed blocker, or human gate."
            ),
            "target_refs": ["owner-route:mas/publication-gate"],
        }
    ]
