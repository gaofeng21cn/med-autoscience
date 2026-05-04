from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import literature_intelligence_os
from med_autoscience.controllers.runtime_trajectory_proof import validate_runtime_trajectory_proof


SCHEMA_VERSION = 1
SURFACE = "open_auto_research_projection"
ARTIFACT_RELATIVE_PATH = Path("artifacts/runtime/open_auto_research_projection/latest.json")
RUBRIC_RELATIVE_PATH = Path("artifacts/eval_hygiene/quality_regression_projection/latest.json")
TRAJECTORY_RELATIVE_PATH = Path("artifacts/runtime/action_observation_trajectory/latest.json")
ROUTE_ORCHESTRATOR_RELATIVE_PATH = Path("artifacts/medical_paper/route_decision_orchestrator.json")

AUTHORITY = {
    "read_only": True,
    "can_mutate_runtime": False,
    "can_materialize_artifacts": False,
    "can_authorize_publication_quality": False,
    "can_authorize_submission": False,
    "can_replace_controller_decision": False,
    "can_replace_study_truth": False,
}

ACTION_BY_CAPABILITY = {
    "literature_evidence_graph": {
        "action_id": "run_literature_evidence_graph",
        "surface": "literature_intelligence_os",
    },
    "evaluation_rubric_tree": {
        "action_id": "review_rubric_gaps",
        "surface": "paperbench_style_hierarchical_rubric_tree",
    },
    "runtime_trajectory_proof": {
        "action_id": "inspect_trajectory",
        "surface": "action_observation_trajectory",
    },
    "candidate_path_graph": {
        "action_id": "refine_candidate_path",
        "surface": "candidate_path_graph",
    },
}


def stable_open_auto_research_projection_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def build_open_auto_research_projection(
    *,
    study_root: Path,
    active_run_id: str | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    capabilities = {
        "literature_evidence_graph": _literature_capability(root),
        "evaluation_rubric_tree": _rubric_capability(root),
        "runtime_trajectory_proof": _trajectory_capability(root, active_run_id=active_run_id),
        "candidate_path_graph": _candidate_path_capability(root),
    }
    counts = _counts(capabilities)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(root),
        "status": _overall_status(counts),
        "summary": _summary(counts),
        "counts": counts,
        "capabilities": capabilities,
        "actions": _actions(capabilities),
        "authority": dict(AUTHORITY),
        "refs": {
            "projection_path": str(stable_open_auto_research_projection_path(study_root=root)),
            "literature_evidence_graph_path": str(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=root)),
            "evaluation_rubric_tree_path": str((root / RUBRIC_RELATIVE_PATH).resolve()),
            "runtime_trajectory_proof_path": str((root / TRAJECTORY_RELATIVE_PATH).resolve()),
            "candidate_path_graph_path": str((root / ROUTE_ORCHESTRATOR_RELATIVE_PATH).resolve()),
        },
    }


def materialize_open_auto_research_projection(
    *,
    study_root: Path,
    active_run_id: str | None = None,
) -> dict[str, Any]:
    projection = build_open_auto_research_projection(study_root=study_root, active_run_id=active_run_id)
    path = stable_open_auto_research_projection_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return projection


def build_workspace_open_auto_research_projection(
    *,
    studies: list[Mapping[str, Any]],
) -> dict[str, Any]:
    study_projections = [
        dict(item["open_auto_research_projection"])
        for item in studies
        if isinstance(item.get("open_auto_research_projection"), Mapping)
    ]
    counts = {
        "study_count": len(studies),
        "projection_count": len(study_projections),
        "ready": 0,
        "blocked": 0,
        "needs_review": 0,
    }
    for projection in study_projections:
        projection_counts = projection.get("counts") if isinstance(projection.get("counts"), Mapping) else {}
        counts["ready"] += int(projection_counts.get("ready") or 0)
        counts["blocked"] += int(projection_counts.get("blocked") or 0)
        counts["needs_review"] += int(projection_counts.get("needs_review") or 0)
    return {
        "surface_kind": "workspace_open_auto_research_projection",
        "read_model": "open_auto_research_projection_read_model",
        "authority": "observability_only",
        "status": _workspace_status(counts),
        "summary": _workspace_summary(counts),
        "counts": counts,
        "study_projections": study_projections,
    }


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _literature_capability(study_root: Path) -> dict[str, Any]:
    summary = literature_intelligence_os.build_literature_intelligence_os_summary(study_root=study_root)
    status = _text(summary.get("status")) or "blocked"
    return {
        "status": status,
        "surface": "literature_intelligence_os",
        "summary": (
            f"evidence nodes {dict(summary.get('coverage') or {}).get('evidence_node_count', 0)}; "
            f"contradictions {dict(summary.get('coverage') or {}).get('contradiction_flag_count', 0)}"
            if status == "ready"
            else _text(summary.get("missing_reason")) or "missing_literature_evidence_graph"
        ),
        "artifact_path": summary.get("artifact_path"),
        "coverage": dict(summary.get("coverage") or {}),
        "authority": dict(summary.get("authority") or {}),
    }


def _rubric_capability(study_root: Path) -> dict[str, Any]:
    path = (study_root / RUBRIC_RELATIVE_PATH).resolve()
    payload = _read_json_mapping(path)
    rubric_tree = dict((payload.get("calibration_evidence") or {}).get("rubric_tree") or {})
    if not payload:
        status = "blocked"
        summary = "missing_evaluation_rubric_tree"
    elif not rubric_tree:
        status = "blocked"
        summary = "missing_rubric_tree"
    elif _text(rubric_tree.get("role")) != "calibration_evidence_only":
        status = "needs_review"
        summary = "rubric_role_must_be_calibration_evidence_only"
    elif rubric_tree.get("can_authorize_publication_quality") is not False:
        status = "needs_review"
        summary = "rubric_authority_boundary_needs_review"
    else:
        status = "ready"
        summary = f"rubric nodes {_rubric_node_count(rubric_tree.get('nodes'))}"
    return {
        "status": status,
        "surface": "paperbench_style_hierarchical_rubric_tree",
        "summary": summary,
        "artifact_path": str(path),
        "role": rubric_tree.get("role"),
        "node_count": _rubric_node_count(rubric_tree.get("nodes")),
        "authority": {
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "publication_authority_surface": "artifacts/publication_eval/latest.json",
        },
    }


def _rubric_node_count(value: object) -> int:
    if not isinstance(value, list):
        return 0
    total = 0
    for item in value:
        if not isinstance(item, Mapping):
            continue
        total += 1 + _rubric_node_count(item.get("children"))
    return total


def _trajectory_capability(study_root: Path, *, active_run_id: str | None) -> dict[str, Any]:
    path = (study_root / TRAJECTORY_RELATIVE_PATH).resolve()
    payload = _read_json_mapping(path)
    if not payload:
        return {
            "status": "blocked",
            "surface": "action_observation_trajectory",
            "summary": "missing_action_observation_trajectory",
            "artifact_path": str(path),
            "authority": {"read_model_only": True},
        }
    validation = validate_runtime_trajectory_proof(payload)
    status = "ready" if validation.get("ok") else "needs_review"
    replay_summary = dict(payload.get("replay_summary") or {})
    return {
        "status": status,
        "surface": "action_observation_trajectory",
        "summary": (
            f"steps {len(list(payload.get('steps') or []))}; "
            f"non-replayable {replay_summary.get('non_replayable_step_count', 0)}"
        ),
        "artifact_path": str(path),
        "active_run_id": _text(payload.get("active_run_id")) or active_run_id,
        "replay_summary": replay_summary,
        "validation": validation,
        "authority": dict(payload.get("trajectory_role") or {"read_model_only": True}),
    }


def _candidate_path_capability(study_root: Path) -> dict[str, Any]:
    path = (study_root / ROUTE_ORCHESTRATOR_RELATIVE_PATH).resolve()
    payload = _read_json_mapping(path)
    graph = dict(payload.get("candidate_path_graph") or {})
    if not payload:
        status = "blocked"
        summary = "missing_route_decision_orchestrator_projection"
    elif not graph:
        status = "blocked"
        summary = "missing_candidate_path_graph"
    elif graph.get("decision") == "human_gate":
        status = "needs_review"
        summary = "candidate_path_requires_human_gate"
    else:
        status = "ready"
        summary = f"decision {graph.get('decision')}; candidates {len(list(graph.get('candidates') or []))}"
    return {
        "status": status,
        "surface": "candidate_path_graph",
        "summary": summary,
        "artifact_path": str(path),
        "decision": graph.get("decision"),
        "selected_candidate_id": graph.get("selected_candidate_id"),
        "controller_decision_ref": graph.get("controller_decision_ref") or payload.get("controller_decision_ref"),
        "authority": {
            "read_model_only": True,
            "replaces_controller_decision": False,
            "replaces_study_truth": False,
        },
    }


def _counts(capabilities: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    counts = {"ready": 0, "blocked": 0, "needs_review": 0, "total": len(capabilities)}
    for item in capabilities.values():
        status = _text(item.get("status")) or "blocked"
        if status not in counts:
            status = "blocked"
        counts[status] += 1
    return counts


def _overall_status(counts: Mapping[str, int]) -> str:
    if counts.get("blocked"):
        return "blocked"
    if counts.get("needs_review"):
        return "needs_review"
    return "ready"


def _summary(counts: Mapping[str, int]) -> str:
    return (
        f"{counts.get('ready', 0)} ready; "
        f"{counts.get('needs_review', 0)} needs review; "
        f"{counts.get('blocked', 0)} blocked."
    )


def _actions(capabilities: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    for capability_id, capability in capabilities.items():
        action = dict(ACTION_BY_CAPABILITY[capability_id])
        action["status"] = _text(capability.get("status")) or "blocked"
        actions.append(action)
    return actions


def _workspace_status(counts: Mapping[str, int]) -> str:
    if counts.get("blocked"):
        return "blocked"
    if counts.get("needs_review"):
        return "needs_review"
    if counts.get("projection_count"):
        return "ready"
    return "not_available"


def _workspace_summary(counts: Mapping[str, int]) -> str:
    if not counts.get("projection_count"):
        return "当前还没有可见 Open Auto Research projection。"
    return (
        f"{counts.get('projection_count', 0)} 个 study 已接入 Open Auto Research projection；"
        f"{counts.get('ready', 0)} ready；"
        f"{counts.get('needs_review', 0)} needs review；"
        f"{counts.get('blocked', 0)} blocked。"
    )


__all__ = [
    "build_open_auto_research_projection",
    "build_workspace_open_auto_research_projection",
    "materialize_open_auto_research_projection",
    "stable_open_auto_research_projection_path",
]
