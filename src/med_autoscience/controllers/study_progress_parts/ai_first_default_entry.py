from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.ai_reviewer_runtime_workflow import (
    build_ai_reviewer_runtime_workflow_state,
)
from med_autoscience.controllers.ai_reviewer_calibration import (
    build_quality_regression_calibration_evidence_contract,
)
from med_autoscience.controllers.authoring_stage_graph import build_authoring_stage_graph
from med_autoscience.controllers.artifact_runtime_proof import build_artifact_runtime_proof
from med_autoscience.controllers.medical_literature_hygiene import (
    build_medical_literature_hygiene_projection,
)
from med_autoscience.controllers.pre_draft_quality_runtime import (
    build_pre_draft_quality_runtime_state,
)
from med_autoscience.controllers.reviewer_refinement_loop import (
    build_reviewer_refinement_loop_read_model,
)
from med_autoscience.controllers.section_authoring_work_units import (
    build_section_authoring_work_units,
)

_PAPER_ORCHESTRA_SURFACE_IDS = (
    "authoring_stage_graph",
    "section_authoring_work_units",
    "medical_literature_hygiene_projection",
    "reviewer_refinement_loop",
    "quality_regression_projection",
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


def _read_json_mapping(path: Path) -> tuple[Mapping[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, "invalid_json"
    if not isinstance(payload, Mapping):
        return {}, "not_json_object"
    return payload, None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _paper_orchestra_parallel_sections(workplan: Mapping[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    raw_sections = workplan.get("sections")
    if not isinstance(raw_sections, list):
        return sections
    for item in raw_sections:
        if not isinstance(item, Mapping):
            continue
        section_id = _text(item.get("section_id"))
        if section_id is None:
            continue
        status = _text(item.get("status")) or "unknown"
        blockers = _blocker_strings(item.get("blockers"))
        parallelizable = bool(item.get("parallelizable")) or status in {"ready", "closed"}
        if not parallelizable or blockers:
            continue
        sections.append(
            {
                "section_id": section_id,
                "section_title": _text(item.get("section_title")) or section_id,
                "status": status,
                "owner": _text(item.get("owner")) or "MAS writing lane",
                "task_refs": _string_list(item.get("task_refs")),
            }
        )
    return sections


def _section_unit_parallel_sections(section_units: Mapping[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for item in section_units.get("units") or []:
        if not isinstance(item, Mapping) or item.get("blockers"):
            continue
        section = _text(item.get("section"))
        if section is None:
            continue
        sections.append(
            {
                "section_id": section,
                "section_title": section.title(),
                "status": "ready",
                "owner": "MAS writing lane",
                "task_refs": _string_list(item.get("required_refs")),
            }
        )
    return sections


def _surface_status_blocked(surface: Mapping[str, Any], *, clear_statuses: set[str]) -> bool:
    status = _text(surface.get("status"))
    return status not in clear_statuses


def _integrated_surface_summary(
    *,
    stage_graph: Mapping[str, Any],
    section_units: Mapping[str, Any],
    literature_hygiene: Mapping[str, Any],
    refinement_loop: Mapping[str, Any],
) -> dict[str, Any]:
    quality_regression_contract = build_quality_regression_calibration_evidence_contract()
    return {
        "authoring_stage_graph": {
            "surface": stage_graph.get("surface"),
            "status": stage_graph.get("status"),
            "blocking_stage_ids": list(stage_graph.get("blocking_stage_ids") or []),
            "authority": dict(stage_graph.get("authority") or {}),
        },
        "section_authoring_work_units": {
            "surface": section_units.get("surface"),
            "status": section_units.get("status"),
            "unit_count": len(list(section_units.get("units") or [])),
            "blockers": list(section_units.get("blockers") or []),
            "authority": dict(section_units.get("authority") or {}),
        },
        "medical_literature_hygiene_projection": {
            "surface": literature_hygiene.get("surface"),
            "status": literature_hygiene.get("status"),
            "blockers": list(literature_hygiene.get("blockers") or []),
            "authority": dict(literature_hygiene.get("authority") or {}),
        },
        "reviewer_refinement_loop": {
            "surface": refinement_loop.get("surface"),
            "accept_status": (dict(refinement_loop.get("accept") or {})).get("status"),
            "revert_required": bool((dict(refinement_loop.get("revert") or {})).get("required")),
            "worklog_count": len(list(refinement_loop.get("worklog") or [])),
            "contract": dict(refinement_loop.get("contract") or {}),
        },
        "quality_regression_projection": {
            "surface": "quality_regression_projection",
            "role": (dict(quality_regression_contract.get("judge_scores") or {})).get("role"),
            "authority": {
                "owner": quality_regression_contract.get("owner"),
                "can_authorize_publication_quality": bool(
                    (dict(quality_regression_contract.get("judge_scores") or {})).get(
                        "can_authorize_publication_quality"
                    )
                ),
                "can_replace_ai_reviewer": bool(
                    (dict(quality_regression_contract.get("judge_scores") or {})).get(
                        "can_replace_ai_reviewer"
                    )
                ),
            },
            "required_refs": list(quality_regression_contract.get("required_refs") or []),
        },
    }


def _read_reviewer_refinement_loop_projection(study_root: Path) -> dict[str, Any]:
    try:
        return build_reviewer_refinement_loop_read_model(study_root=study_root)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return {
            "surface": "reviewer_refinement_loop",
            "schema_version": 1,
            "study_root": str(study_root),
            "snapshot": {
                "source_surface": "publication_eval/latest.json",
                "source_artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                "authority_blockers": ["publication_eval_latest_unreadable"],
            },
            "accept": {
                "accepted": False,
                "status": "blocked",
                "source": "ai_reviewer_backed_publication_eval_latest",
                "blockers": [f"reviewer_refinement_loop_unreadable:{exc.__class__.__name__}"],
                "package_mutation_allowed": False,
            },
            "revert": {
                "required": True,
                "strategy": "same_line_route_back",
                "direct_package_mutation_allowed": False,
                "route_back": None,
            },
            "worklog": [],
            "contract": {
                "read_model_only": True,
                "accept_authority": "AI reviewer-backed artifacts/publication_eval/latest.json",
                "revert_authority": "same-line route-back decision surface",
                "direct_package_mutation_allowed": False,
            },
        }


def _paper_orchestra_integrated_blocking_gates(
    *,
    stage_graph: Mapping[str, Any],
    section_units: Mapping[str, Any],
    literature_hygiene: Mapping[str, Any],
    refinement_loop: Mapping[str, Any],
    pre_draft: Mapping[str, Any],
    ai_reviewer: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> list[dict[str, Any]]:
    gates = _paper_orchestra_blocking_gates(pre_draft=pre_draft, ai_reviewer=ai_reviewer, artifact=artifact)
    for stage_id in stage_graph.get("blocking_stage_ids") or []:
        gates.append(
            {
                "gate_id": f"authoring_stage_graph:{stage_id}",
                "label": f"authoring stage graph: {stage_id}",
                "owner": "MAS authoring DAG",
                "surface": "authoring_stage_graph",
                "blockers": [],
            }
        )
    if _surface_status_blocked(section_units, clear_statuses={"ready"}):
        gates.append(
            {
                "gate_id": "section_authoring_work_units",
                "label": "section authoring work units",
                "owner": "MAS authoring units",
                "surface": "section_authoring_work_units",
                "blockers": list(section_units.get("blockers") or []),
            }
        )
    if _surface_status_blocked(literature_hygiene, clear_statuses={"clear"}):
        gates.append(
            {
                "gate_id": "medical_literature_hygiene_projection",
                "label": "medical literature hygiene",
                "owner": "MAS deterministic quality gates",
                "surface": "medical_literature_hygiene_projection",
                "blockers": list(literature_hygiene.get("blockers") or []),
            }
        )
    accept = dict(refinement_loop.get("accept") or {})
    if accept.get("status") != "accepted":
        gates.append(
            {
                "gate_id": "reviewer_refinement_loop",
                "label": "reviewer refinement loop",
                "owner": "MAS reviewer refinement loop",
                "surface": "reviewer_refinement_loop",
                "blockers": list(accept.get("blockers") or []),
            }
        )
    return gates


def _paper_orchestra_blocking_gates(
    *,
    pre_draft: Mapping[str, Any],
    ai_reviewer: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    if pre_draft.get("draft_ready") is not True:
        gates.append(
            {
                "gate_id": "pre_draft_quality_gate",
                "label": "pre-draft quality gate",
                "owner": "MAS Quality OS",
                "surface": _text(pre_draft.get("surface")) or "pre_draft_quality_runtime_state",
                "blockers": list(pre_draft.get("blockers") or []),
            }
        )
    if ai_reviewer.get("finalize_authorized") is not True or ai_reviewer.get("submission_authorized") is not True:
        gates.append(
            {
                "gate_id": "ai_reviewer_quality_gate",
                "label": "AI reviewer quality gate",
                "owner": "MAS AI reviewer workflow",
                "surface": _text(ai_reviewer.get("surface")) or "ai_reviewer_runtime_workflow_state",
                "blockers": list(ai_reviewer.get("blockers") or []),
            }
        )
    if artifact.get("current_package_from_canonical_source") is not True:
        gates.append(
            {
                "gate_id": "artifact_rebuild_gate",
                "label": "artifact rebuild gate",
                "owner": "MAS Artifact OS",
                "surface": _text(artifact.get("surface")) or "artifact_runtime_proof",
                "blockers": list(artifact.get("blockers") or []),
            }
        )
    return gates


def _paper_orchestra_next_owner(blocking_gates: list[dict[str, Any]]) -> dict[str, str]:
    if blocking_gates:
        first_gate = blocking_gates[0]
        return {
            "owner": str(first_gate["owner"]),
            "surface": str(first_gate["surface"]),
            "action": "close_pre_draft_quality_gate"
            if first_gate["gate_id"] == "pre_draft_quality_gate"
            else f"close_{first_gate['gate_id']}",
        }
    return {
        "owner": "MAS writing lane",
        "surface": "authoring_workplan_projection",
        "action": "continue_parallel_section_writing",
    }


def _build_paper_orchestra_operator_projection(
    *,
    study_root: Path,
    pre_draft: Mapping[str, Any],
    ai_reviewer: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    workplan_path = study_root / "paper" / "authoring_workplan.json"
    workplan, workplan_read_error = _read_json_mapping(workplan_path)
    stage_graph = build_authoring_stage_graph(study_root=study_root)
    section_units = build_section_authoring_work_units(study_root=study_root)
    literature_hygiene = build_medical_literature_hygiene_projection(paper_root=study_root / "paper")
    refinement_loop = _read_reviewer_refinement_loop_projection(study_root)
    parallel_sections = _section_unit_parallel_sections(section_units) or _paper_orchestra_parallel_sections(workplan)
    blocking_gates = _paper_orchestra_integrated_blocking_gates(
        stage_graph=stage_graph,
        section_units=section_units,
        literature_hygiene=literature_hygiene,
        refinement_loop=refinement_loop,
        pre_draft=pre_draft,
        ai_reviewer=ai_reviewer,
        artifact=artifact,
    )
    current_gate = blocking_gates[0] if blocking_gates else None
    current_stage = {
        "stage_id": current_gate["gate_id"] if current_gate is not None else "parallel_section_writing",
        "label": current_gate["label"] if current_gate is not None else "parallel section writing",
        "owner": current_gate["owner"] if current_gate is not None else "MAS writing lane",
        "surface": current_gate["surface"] if current_gate is not None else "authoring_workplan_projection",
    }
    return {
        "surface": "paper_orchestra_operator_projection",
        "schema_version": 1,
        "read_model": "paper_orchestra_operator_projection_read_model",
        "study_root": str(study_root),
        "status": "blocked" if blocking_gates else "ready_for_parallel_writing",
        "current_dag_stage": current_stage,
        "parallel_sections": parallel_sections,
        "parallel_section_count": len(parallel_sections),
        "blocking_gates": blocking_gates,
        "blocking_gate_count": len(blocking_gates),
        "next_owner": _paper_orchestra_next_owner(blocking_gates),
        "source_refs": {
            "authoring_workplan_path": str(workplan_path),
            "authoring_workplan_read_error": workplan_read_error,
        },
        "integrated_surfaces": _integrated_surface_summary(
            stage_graph=stage_graph,
            section_units=section_units,
            literature_hygiene=literature_hygiene,
            refinement_loop=refinement_loop,
        ),
        "pending_integration_surfaces": [
            surface_id
            for surface_id in _PAPER_ORCHESTRA_SURFACE_IDS
            if surface_id
            not in {
                "authoring_stage_graph",
                "section_authoring_work_units",
                "medical_literature_hygiene_projection",
                "reviewer_refinement_loop",
                "quality_regression_projection",
            }
        ],
        "authority": {
            "read_only": True,
            "creates_runtime_truth": False,
            "can_mutate_runtime": False,
            "can_authorize_quality": False,
            "can_authorize_publication_ready": False,
            "can_authorize_submission": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    }


def _pre_draft_state(state: Mapping[str, Any]) -> dict[str, Any]:
    readiness = _mapping(state.get("readiness"))
    route_back = _mapping(state.get("route_back"))
    authoring_workplan_projection = dict(_mapping(state.get("authoring_workplan_projection")))
    authoring_workplan_projection.pop("source_path", None)
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
        "authoring_workplan_projection": authoring_workplan_projection,
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
    paper_orchestra_operator_projection = _build_paper_orchestra_operator_projection(
        study_root=resolved_study_root,
        pre_draft=pre_draft,
        ai_reviewer=ai_reviewer,
        artifact=artifact,
    )
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
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection,
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
