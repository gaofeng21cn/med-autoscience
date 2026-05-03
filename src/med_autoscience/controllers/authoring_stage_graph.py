from __future__ import annotations

import json
from pathlib import Path
from typing import Any


__all__ = ["build_authoring_stage_graph", "build_authoring_stage_graph_read_model"]


_SURFACE = "authoring_stage_graph"
_SCHEMA_VERSION = 1
_CLOSED = "closed"
_AI_REVIEWER_POLICY_ID = "medical_publication_critique_v1"

_SURFACE_PATHS = {
    "authoring_workplan": Path("paper/authoring_workplan.json"),
    "pre_draft_readiness": Path("paper/pre_draft_writing_readiness.json"),
    "medical_manuscript_blueprint": Path("paper/medical_manuscript_blueprint.json"),
    "evidence_ledger": Path("paper/evidence_ledger.json"),
    "review_ledger": Path("paper/review_ledger.json"),
    "publication_eval": Path("artifacts/publication_eval/latest.json"),
}

_STAGES: tuple[tuple[str, str], ...] = (
    ("outline", "Outline"),
    ("display_planning", "Display planning"),
    ("literature_grounding", "Literature grounding"),
    ("section_writing", "Section writing"),
    ("refinement", "Refinement"),
)

_EDGES: tuple[tuple[str, str], ...] = (
    ("outline", "display_planning"),
    ("outline", "literature_grounding"),
    ("display_planning", "section_writing"),
    ("literature_grounding", "section_writing"),
    ("section_writing", "refinement"),
)

_READINESS_BY_STAGE = {
    "outline": ("clinical_question", "section_purpose", "reader_flow_plan"),
    "display_planning": ("display_to_claim_map",),
    "literature_grounding": ("claim_evidence_map",),
    "section_writing": ("section_purpose", "reader_flow_plan"),
    "refinement": ("ai_prose_review_feedback_loop",),
}


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "not_json_object"
    return payload, None


def _text(value: object) -> str:
    return str(value or "").strip()


def _status(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return _text(payload.get("status") or payload.get("readiness_status"))


def _is_closed(payload: dict[str, Any] | None) -> bool:
    return _status(payload) == _CLOSED


def _surface_ref(path: Path, payload: dict[str, Any] | None, read_error: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
    }
    if read_error is not None:
        result["read_error"] = read_error
    if payload is not None:
        payload_status = _status(payload)
        if payload_status:
            result["status"] = payload_status
        eval_id = _text(payload.get("eval_id"))
        if eval_id:
            result["eval_id"] = eval_id
        provenance = payload.get("assessment_provenance")
        if isinstance(provenance, dict):
            result["assessment_owner"] = _text(provenance.get("owner"))
            result["ai_reviewer_required"] = provenance.get("ai_reviewer_required")
    return result


def _readiness_items_by_id(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    items = payload.get("readiness_items")
    if not isinstance(items, list):
        items = payload.get("required_readiness_items")
    if not isinstance(items, list):
        return {}

    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        readiness_id = _text(item.get("readiness_id"))
        if readiness_id:
            result[readiness_id] = item
    return result


def _append_readiness_blockers(
    *,
    stage_id: str,
    readiness: dict[str, Any] | None,
    read_error: str | None,
    blockers: list[str],
) -> None:
    if read_error is not None:
        blockers.append(f"pre_draft_readiness_{read_error}")
        return
    if not isinstance(readiness, dict):
        blockers.append("pre_draft_readiness_missing")
        return
    if not _is_closed(readiness):
        blockers.append("pre_draft_readiness_not_closed")

    items_by_id = _readiness_items_by_id(readiness)
    for readiness_id in _READINESS_BY_STAGE[stage_id]:
        item = items_by_id.get(readiness_id)
        if item is None:
            blockers.append(f"pre_draft_readiness_item_missing:{readiness_id}")
            continue
        if not _is_closed(item):
            blockers.append(f"pre_draft_readiness_item_not_closed:{readiness_id}")


def _append_authoring_workplan_blockers(
    *,
    workplan: dict[str, Any] | None,
    read_error: str | None,
    require_sections: bool,
    blockers: list[str],
) -> None:
    if read_error is not None:
        blockers.append(f"authoring_workplan_{read_error}")
        return
    if not isinstance(workplan, dict):
        blockers.append("authoring_workplan_missing")
        return
    if not _is_closed(workplan):
        blockers.append("authoring_workplan_not_closed")

    authority = workplan.get("authority")
    if not isinstance(authority, dict):
        blockers.append("authoring_workplan_authority_missing")
    else:
        if authority.get("read_model_only") is not True:
            blockers.append("authoring_workplan_not_read_model_only")
        if authority.get("can_authorize_draft_readiness") is not False:
            blockers.append("authoring_workplan_authority_overreach")

    if require_sections:
        _append_closed_items_blockers(
            payload=workplan,
            item_key="sections",
            id_key="section_id",
            blocker_prefix="authoring_workplan",
            blockers=blockers,
        )
    _append_closed_items_blockers(
        payload=workplan,
        item_key="work_units",
        id_key="work_unit_id",
        blocker_prefix="authoring_workplan",
        blockers=blockers,
    )


def _append_closed_items_blockers(
    *,
    payload: dict[str, Any],
    item_key: str,
    id_key: str,
    blocker_prefix: str,
    blockers: list[str],
) -> None:
    items = payload.get(item_key)
    if not isinstance(items, list) or not items:
        blockers.append(f"{blocker_prefix}_{item_key}_missing")
        return
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            blockers.append(f"{blocker_prefix}_{item_key}_invalid:{index}")
            continue
        item_id = _text(item.get(id_key)) or str(index)
        if not _is_closed(item):
            blockers.append(f"{blocker_prefix}_{item_key}_not_closed:{item_id}")


def _append_blueprint_blockers(
    *,
    blueprint: dict[str, Any] | None,
    read_error: str | None,
    blockers: list[str],
) -> None:
    if read_error is not None:
        blockers.append(f"medical_manuscript_blueprint_{read_error}")
        return
    if not isinstance(blueprint, dict):
        blockers.append("medical_manuscript_blueprint_missing")
        return
    blueprint_status = _status(blueprint)
    if blueprint_status and blueprint_status != _CLOSED:
        blockers.append("medical_manuscript_blueprint_not_closed")
    if blueprint.get("canonical_ready") is not True:
        blockers.append("medical_manuscript_blueprint_not_canonical_ready")

    provenance = blueprint.get("authoring_provenance")
    if not isinstance(provenance, dict):
        blockers.append("medical_manuscript_blueprint_authoring_provenance_missing")
        return
    if _text(provenance.get("owner")) not in {"ai_author", "ai_reviewer"}:
        blockers.append("medical_manuscript_blueprint_ai_authority_missing")
    if provenance.get("ai_reviewer_required") is not False:
        blockers.append("medical_manuscript_blueprint_still_requires_ai_reviewer")


def _append_closed_surface_blocker(
    *,
    surface_key: str,
    payload: dict[str, Any] | None,
    read_error: str | None,
    blockers: list[str],
) -> None:
    if read_error is not None:
        blockers.append(f"{surface_key}_{read_error}")
        return
    if not isinstance(payload, dict):
        blockers.append(f"{surface_key}_missing")
        return
    if not _is_closed(payload):
        blockers.append(f"{surface_key}_not_closed")


def _append_publication_eval_blockers(
    *,
    publication_eval: dict[str, Any] | None,
    read_error: str | None,
    blockers: list[str],
) -> None:
    if read_error is not None:
        blockers.append(f"publication_eval_{read_error}")
        return
    if not isinstance(publication_eval, dict):
        blockers.append("publication_eval_missing")
        return

    provenance = publication_eval.get("assessment_provenance")
    if not isinstance(provenance, dict):
        blockers.append("publication_eval_ai_reviewer_provenance_missing")
    else:
        if _text(provenance.get("owner")) != "ai_reviewer":
            blockers.append("publication_eval_not_ai_reviewer_backed")
        if _text(provenance.get("policy_id")) != _AI_REVIEWER_POLICY_ID:
            blockers.append("publication_eval_policy_not_ai_reviewer_critique")
        if provenance.get("ai_reviewer_required") is not False:
            blockers.append("publication_eval_still_requires_ai_reviewer")

    verdict = publication_eval.get("verdict")
    overall = _text(verdict.get("overall_verdict")).lower() if isinstance(verdict, dict) else ""
    if overall in {"blocked", "fail", "failed", "needs_review", "review_required"} or not overall:
        blockers.append("publication_eval_not_clear")
    gaps = publication_eval.get("gaps")
    if isinstance(gaps, list) and gaps:
        blockers.append("publication_eval_has_gaps")


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _build_stage_nodes(
    *,
    payloads: dict[str, dict[str, Any] | None],
    read_errors: dict[str, str | None],
) -> list[dict[str, Any]]:
    stage_blockers: dict[str, list[str]] = {stage_id: [] for stage_id, _label in _STAGES}

    for stage_id in ("outline", "display_planning", "literature_grounding", "section_writing", "refinement"):
        _append_readiness_blockers(
            stage_id=stage_id,
            readiness=payloads["pre_draft_readiness"],
            read_error=read_errors["pre_draft_readiness"],
            blockers=stage_blockers[stage_id],
        )

    _append_authoring_workplan_blockers(
        workplan=payloads["authoring_workplan"],
        read_error=read_errors["authoring_workplan"],
        require_sections=False,
        blockers=stage_blockers["outline"],
    )
    _append_blueprint_blockers(
        blueprint=payloads["medical_manuscript_blueprint"],
        read_error=read_errors["medical_manuscript_blueprint"],
        blockers=stage_blockers["outline"],
    )
    _append_closed_surface_blocker(
        surface_key="evidence_ledger",
        payload=payloads["evidence_ledger"],
        read_error=read_errors["evidence_ledger"],
        blockers=stage_blockers["literature_grounding"],
    )
    _append_authoring_workplan_blockers(
        workplan=payloads["authoring_workplan"],
        read_error=read_errors["authoring_workplan"],
        require_sections=True,
        blockers=stage_blockers["section_writing"],
    )
    _append_closed_surface_blocker(
        surface_key="review_ledger",
        payload=payloads["review_ledger"],
        read_error=read_errors["review_ledger"],
        blockers=stage_blockers["refinement"],
    )
    _append_publication_eval_blockers(
        publication_eval=payloads["publication_eval"],
        read_error=read_errors["publication_eval"],
        blockers=stage_blockers["refinement"],
    )

    return [
        {
            "stage_id": stage_id,
            "label": label,
            "status": "blocked" if (blockers := _unique(stage_blockers[stage_id])) else _CLOSED,
            "blockers": blockers,
            "refs": _stage_refs(stage_id),
        }
        for stage_id, label in _STAGES
    ]


def _stage_refs(stage_id: str) -> list[str]:
    refs = {
        "outline": [
            "paper/authoring_workplan.json",
            "paper/pre_draft_writing_readiness.json",
            "paper/medical_manuscript_blueprint.json",
        ],
        "display_planning": [
            "paper/pre_draft_writing_readiness.json",
        ],
        "literature_grounding": [
            "paper/pre_draft_writing_readiness.json",
            "paper/evidence_ledger.json",
        ],
        "section_writing": [
            "paper/authoring_workplan.json",
            "paper/pre_draft_writing_readiness.json",
        ],
        "refinement": [
            "paper/pre_draft_writing_readiness.json",
            "paper/review_ledger.json",
            "artifacts/publication_eval/latest.json",
        ],
    }
    return list(refs[stage_id])


def build_authoring_stage_graph(study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    payloads: dict[str, dict[str, Any] | None] = {}
    read_errors: dict[str, str | None] = {}
    refs: dict[str, dict[str, Any]] = {}

    for surface_key, relative_path in _SURFACE_PATHS.items():
        path = resolved_study_root / relative_path
        payload, read_error = _read_json(path)
        payloads[surface_key] = payload
        read_errors[surface_key] = read_error
        refs[surface_key] = _surface_ref(path, payload, read_error)

    nodes = _build_stage_nodes(payloads=payloads, read_errors=read_errors)
    blocking_stage_ids = [node["stage_id"] for node in nodes if node["status"] == "blocked"]

    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "status": "blocked" if blocking_stage_ids else "projected",
        "nodes": nodes,
        "stage_nodes": nodes,
        "edges": [
            {"from_stage_id": from_stage_id, "to_stage_id": to_stage_id}
            for from_stage_id, to_stage_id in _EDGES
        ],
        "blocking_stage_ids": blocking_stage_ids,
        "refs": refs,
        "authority": {
            "owner": "MAS",
            "read_model_only": True,
            "can_authorize_draft_readiness": False,
            "can_mutate_runtime": False,
            "runtime_owner": "MAS controller",
            "publication_owner": "MAS",
            "paper_orchestra_runtime_owner": False,
            "paper_orchestra_skill_pack_owner": False,
        },
    }


def build_authoring_stage_graph_read_model(study_root: str | Path) -> dict[str, Any]:
    return build_authoring_stage_graph(study_root=study_root)
