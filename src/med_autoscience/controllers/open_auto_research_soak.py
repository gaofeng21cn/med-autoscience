from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import (
    literature_intelligence_os,
    open_auto_research_projection,
    quality_regression_projection,
    route_decision_orchestrator,
    runtime_trajectory_proof,
    study_runtime_router,
)
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE = "open_auto_research_soak"
ARTIFACT_RELATIVE_PATH = Path("artifacts/runtime/open_auto_research_soak/latest.json")
QUALITY_RELATIVE_PATH = Path("artifacts/eval_hygiene/quality_regression_projection/latest.json")
TRAJECTORY_RELATIVE_PATH = Path("artifacts/runtime/action_observation_trajectory/latest.json")
ROUTE_RELATIVE_PATH = Path("artifacts/medical_paper/route_decision_orchestrator.json")

FORBIDDEN_RELATIVE_PATHS: tuple[Path, ...] = (
    Path("manuscript/current_package"),
    Path("manuscript/current_package.zip"),
    Path("manuscript/submission_minimal"),
    Path("paper/submission_minimal"),
    Path("submission_packages"),
    Path("artifacts/publication_eval/latest.json"),
    Path("artifacts/controller_decisions/latest.json"),
    Path("artifacts/truth/latest.json"),
    Path("artifacts/runtime/study_runtime_status/latest.json"),
    Path("artifacts/runtime/runtime_status_summary.json"),
)

AUTHORITY = {
    "owner": "MAS controller",
    "read_model_only": True,
    "can_authorize_publication_quality": False,
    "can_authorize_submission": False,
    "can_replace_publication_eval_latest": False,
    "can_replace_controller_decision_latest": False,
    "can_replace_study_runtime_status": False,
    "can_replace_study_truth": False,
    "can_replay_runtime": False,
    "controller_write_scope": [
        "artifacts/medical_paper/literature_intelligence_os.json",
        "artifacts/eval_hygiene/quality_regression_projection/latest.json",
        "artifacts/runtime/action_observation_trajectory/latest.json",
        "artifacts/medical_paper/route_decision_orchestrator.json",
        "artifacts/runtime/open_auto_research_soak/latest.json",
    ],
}


def stable_open_auto_research_soak_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def run_open_auto_research_soak(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    allow_controller_writes: bool = False,
    runtime_status_payload: Mapping[str, Any] | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root = _resolve_study_selector(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    generated_at = _utc_now()
    runtime_payload = _runtime_status_payload(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        entry_mode=entry_mode,
        runtime_status_payload=runtime_status_payload,
    )
    active_run_id = _text(runtime_payload.get("active_run_id")) or "runtime-status-unavailable"
    before_hashes = _hash_forbidden_surfaces(resolved_study_root)
    written_paths: list[Path] = []
    materialization_results: dict[str, Any] = {}

    if allow_controller_writes:
        materialization_results = _materialize_open_auto_research_sources(
            study_root=resolved_study_root,
            study_id=resolved_study_id,
            runtime_status_payload=runtime_payload,
            generated_at=generated_at,
            active_run_id=active_run_id,
        )
        written_paths.extend(
            Path(path)
            for item in materialization_results.values()
            if isinstance(item, Mapping)
            if (path := item.get("artifact_path"))
        )

    projection = open_auto_research_projection.build_open_auto_research_projection(
        study_root=resolved_study_root,
        active_run_id=active_run_id,
    )
    remaining_gaps = _remaining_gaps(
        study_root=resolved_study_root,
        runtime_status_payload=runtime_payload,
        projection=projection,
    )
    report_path = stable_open_auto_research_soak_path(study_root=resolved_study_root)
    written_paths_for_guard = list(written_paths)
    if allow_controller_writes:
        written_paths_for_guard.append(report_path)
    after_hashes = _hash_forbidden_surfaces(resolved_study_root)
    guard_results = _authority_guard_results(
        study_root=resolved_study_root,
        before=before_hashes,
        after=after_hashes,
        written_paths=written_paths_for_guard,
    )
    verdict_status = "blocked" if remaining_gaps or projection.get("status") == "blocked" else projection["status"]
    report = {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "generated_at": generated_at,
        "live_runtime_context": _live_runtime_context(runtime_payload),
        "input_refs": _input_refs(resolved_study_root, runtime_payload),
        "before_after_hashes": {
            "before": before_hashes,
            "after": after_hashes,
        },
        "capability_results": {
            "materialization": materialization_results,
            "open_auto_research_projection": projection,
        },
        "entry_projection_results": _entry_projection_results(projection),
        "authority_guard_results": guard_results,
        "verdict": {
            "status": verdict_status,
            "mode": "controller_authorized_soak" if allow_controller_writes else "read_only_audit",
            "open_auto_research_status": projection.get("status"),
            "submission_ready_claimed": False,
        },
        "remaining_gaps": remaining_gaps,
        "authority": dict(AUTHORITY),
    }
    if allow_controller_writes:
        _write_json(report_path, report)
    return report


def render_open_auto_research_soak_markdown(payload: Mapping[str, Any]) -> str:
    verdict = _mapping(payload.get("verdict"))
    projection = _mapping(_mapping(payload.get("capability_results")).get("open_auto_research_projection"))
    counts = _mapping(projection.get("counts"))
    lines = [
        "# Open Auto Research Soak",
        "",
        f"- study_id: `{_text(payload.get('study_id')) or 'unknown'}`",
        f"- verdict: `{_text(verdict.get('status')) or 'unknown'}`",
        f"- mode: `{_text(verdict.get('mode')) or 'unknown'}`",
        f"- open_auto_research: `{_text(projection.get('status')) or 'unknown'}`; "
        f"ready `{counts.get('ready', 0)}`; needs_review `{counts.get('needs_review', 0)}`; "
        f"blocked `{counts.get('blocked', 0)}`",
    ]
    gaps = [item for item in payload.get("remaining_gaps") or [] if _text(item)]
    if gaps:
        lines.append(f"- remaining_gaps: {', '.join(f'`{item}`' for item in gaps)}")
    guard = _mapping(payload.get("authority_guard_results"))
    lines.append(
        f"- authority_guard: forbidden_surface_unchanged "
        f"`{bool(guard.get('forbidden_surface_unchanged'))}`; "
        f"authorized_writes_only `{bool(guard.get('authorized_writes_only'))}`"
    )
    for action in projection.get("actions") or []:
        if not isinstance(action, Mapping):
            continue
        lines.append(
            f"- {action.get('action_id') or 'unknown_action'}: "
            f"`{action.get('status') or 'unknown'}` ({action.get('surface') or 'unknown_surface'})"
        )
    return "\n".join(lines) + "\n"


def _resolve_study_selector(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> tuple[str, Path]:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")
    if study_root is not None:
        root = Path(study_root).expanduser().resolve()
        return root.name, root
    assert study_id is not None
    resolved_study_id = _text(study_id)
    if resolved_study_id is None:
        raise ValueError("study_id must be non-empty")
    return resolved_study_id, (profile.studies_root / resolved_study_id).expanduser().resolve()


def _runtime_status_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    entry_mode: str | None,
    runtime_status_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if runtime_status_payload is not None:
        return dict(runtime_status_payload)
    try:
        result = study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
            sync_runtime_summary=False,
            include_progress_projection=False,
        )
    except Exception as exc:  # pragma: no cover - defensive live status projection
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "status": "blocked",
            "reason": "study_runtime_status_unavailable",
            "error": str(exc),
        }
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        converted = to_dict()
        return dict(converted) if isinstance(converted, Mapping) else {}
    return dict(result) if isinstance(result, Mapping) else {}


def _materialize_open_auto_research_sources(
    *,
    study_root: Path,
    study_id: str,
    runtime_status_payload: Mapping[str, Any],
    generated_at: str,
    active_run_id: str,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    results["literature_evidence_graph"] = _materialize_literature_evidence_graph(
        study_root=study_root,
        study_id=study_id,
        generated_at=generated_at,
    )
    results["evaluation_rubric_tree"] = _materialize_evaluation_rubric_tree(
        study_root=study_root,
        generated_at=generated_at,
    )
    results["runtime_trajectory_proof"] = _materialize_runtime_trajectory_proof(
        study_root=study_root,
        runtime_status_payload=runtime_status_payload,
        active_run_id=active_run_id,
    )
    results["candidate_path_graph"] = _materialize_candidate_path_graph(study_root=study_root)
    return results


def _materialize_literature_evidence_graph(
    *,
    study_root: Path,
    study_id: str,
    generated_at: str,
) -> dict[str, Any]:
    evidence_path, ledger = _read_first_json(
        (
            study_root / "paper" / "evidence_ledger.json",
            study_root / "manuscript" / "evidence_ledger.json",
        )
    )
    evidence_nodes = _evidence_nodes_from_ledger(ledger, evidence_path=evidence_path)
    provenance_refs = _provenance_refs(evidence_nodes)
    source_refs = [ref for node in evidence_nodes if (ref := _text(node.get("source_ref")))]
    guideline_refs = [ref for node in evidence_nodes if (ref := _text(node.get("guideline_ref")))]
    contract_guideline_refs = _reporting_guideline_refs(study_root)
    guideline_refs = _dedupe([*guideline_refs, *contract_guideline_refs])
    anchor_refs = [
        f"pmid:{pmid}" if (pmid := _text(node.get("pmid"))) else f"doi:{doi}"
        for node in evidence_nodes
        if _text(node.get("pmid")) or (doi := _text(node.get("doi")))
    ]
    if not anchor_refs:
        anchor_refs = source_refs[:1]
    fallback_source = str(evidence_path) if evidence_path is not None else "missing:evidence_ledger"
    publication_eval_ref = str(study_root / "artifacts" / "publication_eval" / "latest.json")
    searched_sources = source_refs or [fallback_source]
    payload = {
        "study_id": study_id,
        "search_date": generated_at[:10],
        "search_strategy": {
            "query": "DM002 Open Auto Research soak evidence graph",
            "mesh_terms": ["Diabetes Mellitus", "Mortality", "Risk Assessment"],
            "keywords": ["transportability", "diabetes mortality", "external validation"],
        },
        "searched_sources": searched_sources,
        "provider_provenance": [
            {
                "provider_name": "canonical_evidence_ledger",
                "query": "DM002 Open Auto Research soak evidence graph",
                "retrieved_at": generated_at,
                "response_status": "ok" if evidence_path is not None else "missing",
                "source_refs": searched_sources,
            }
        ],
        "why_worth_doing": (
            "Canonical evidence ledger and publication-eval signals support an Open Auto Research "
            "read-model check for transportability, reporting guidance, and runtime observability."
        ),
        "study_rationale": "The evidence graph checks whether canonical sources support the current diabetes mortality research route.",
        "anchor_papers": anchor_refs,
        "guidelines": guideline_refs,
        "systematic_reviews": [
            source_refs[0] if source_refs else f"{fallback_source}#systematic_review_or_related_source"
        ],
        "journal_neighbor_refs": [publication_eval_ref],
        "high_score_neighbor_refs": [
            {
                "ref": publication_eval_ref,
                "score": 1.0,
                "score_source_ref": f"{stable_open_auto_research_soak_path(study_root=study_root)}#publication-eval-signal",
            }
        ],
        "screening_decisions": [
            {
                "decision": "include" if provenance_refs else "exclude",
                "reason": "canonical evidence ledger provenance present"
                if provenance_refs
                else "canonical evidence ledger lacks PMID/DOI/guideline/source provenance",
            }
        ],
        "citation_ledger_refs": [str(evidence_path)] if evidence_path is not None else [],
        "evidence_nodes": evidence_nodes or [{"node_id": "missing_provenance", "claim": "No provenance-bearing evidence node found."}],
        "perspective_questions": [
            {
                "question_id": "dm002.transportability",
                "question": "Does the evidence support transportable diabetes mortality attribution?",
                "evidence_refs": provenance_refs,
            }
        ],
        "contradiction_flags": [],
        "metadata_quality": {
            "source": "canonical_evidence_ledger",
            "provenance_node_count": len(provenance_refs),
        },
        "citation_grounding": {
            "required": True,
            "provenance_keys": list(literature_intelligence_os.EVIDENCE_NODE_PROVENANCE_KEYS),
            "source_ref": str(evidence_path) if evidence_path is not None else None,
        },
    }
    return literature_intelligence_os.materialize_literature_intelligence_os(
        study_root=study_root,
        payload=payload,
    )


def _reporting_guideline_refs(study_root: Path) -> list[str]:
    refs: list[str] = []
    for relative in (
        Path("paper/medical_story_contract.json"),
        Path("paper/medical_reporting_contract.json"),
    ):
        path = study_root / relative
        payload = _read_json(path)
        guideline = _text(payload.get("reporting_guideline_family"))
        if guideline is not None:
            refs.append(f"guideline:{guideline}")
    return _dedupe(refs)


def _materialize_evaluation_rubric_tree(*, study_root: Path, generated_at: str) -> dict[str, Any]:
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    eval_payload = _read_json(eval_path)
    if not eval_payload:
        return {
            "surface": quality_regression_projection.SURFACE,
            "status": "blocked",
            "missing_reason": "missing_publication_eval",
            "artifact_path": str(study_root / QUALITY_RELATIVE_PATH),
        }
    eval_with_ref = dict(eval_payload)
    eval_with_ref["eval_ref"] = str(eval_path)
    evidence_ref = str(study_root / "paper" / "evidence_ledger.json")
    rubric_nodes = [
        {
            "node_id": "dm002.open_auto_research.root",
            "label": "DM002 Open Auto Research calibration",
            "reviewer_kind": "ai_reviewer",
            "evidence_refs": [str(eval_path), evidence_ref],
            "judge_calibration_refs": [f"{stable_open_auto_research_soak_path(study_root=study_root)}#rubric"],
            "score": None,
            "children": [
                {
                    "node_id": "dm002.open_auto_research.ai_reviewer_required",
                    "label": "AI reviewer provenance requirement",
                    "reviewer_kind": "ai_reviewer",
                    "evidence_refs": [str(eval_path)],
                    "judge_calibration_refs": [f"{stable_open_auto_research_soak_path(study_root=study_root)}#ai_reviewer"],
                    "score": None,
                    "children": [],
                }
            ],
        }
    ]
    projection = quality_regression_projection.build_quality_regression_projection(
        draft_eval=eval_with_ref,
        revision_eval=eval_with_ref,
        final_package_eval=eval_with_ref,
        historical_repair_results=[
            {
                "dimension": "evidence_strength",
                "repair_id": "dm002-publication-gate",
                "result": "review_required",
                "evidence_ref": str(eval_path),
            }
        ],
        calibration_evidence_refs=[str(eval_path), evidence_ref, f"generated_at:{generated_at}"],
        judge_scores=[
            {
                "judge_id": "dm002_oar_soak_calibration",
                "compared_stages": ["draft", "revision", "final"],
                "score": None,
                "calibration_evidence_ref": str(eval_path),
            }
        ],
        rubric_nodes=rubric_nodes,
    )
    path = (study_root / QUALITY_RELATIVE_PATH).resolve()
    _write_json(path, projection)
    return {
        "surface": projection["surface"],
        "status": projection["regression_summary"]["status"],
        "artifact_path": str(path),
        "rubric_role": projection["calibration_evidence"]["rubric_tree"]["role"],
    }


def _materialize_runtime_trajectory_proof(
    *,
    study_root: Path,
    runtime_status_payload: Mapping[str, Any],
    active_run_id: str,
) -> dict[str, Any]:
    reason = _text(runtime_status_payload.get("reason")) or "study_runtime_status"
    steps = [
        {
            "step_id": "step-study-runtime-status",
            "action_type": "read_runtime_status",
            "action_ref": "study_runtime_status",
            "observation_ref": str(runtime_status_payload.get("quest_root") or study_root),
            "artifact_delta_refs": [],
            "side_effect_class": "none",
            "status": "observed",
        },
        {
            "step_id": "step-publication-authority-guard",
            "action_type": "observe_publication_gate",
            "action_ref": reason,
            "observation_ref": "artifacts/publication_eval/latest.json",
            "artifact_delta_refs": [
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "side_effect_class": "artifact_write",
            "status": "blocked",
        },
    ]
    proof = runtime_trajectory_proof.build_runtime_trajectory_proof(
        active_run_id=active_run_id,
        steps=steps,
    )
    path = (study_root / TRAJECTORY_RELATIVE_PATH).resolve()
    _write_json(path, proof)
    return {
        "surface": proof["surface"],
        "status": "ready",
        "artifact_path": str(path),
        "replay_summary": proof["replay_summary"],
    }


def _materialize_candidate_path_graph(*, study_root: Path) -> dict[str, Any]:
    evidence_ref = str(study_root / "paper" / "evidence_ledger.json")
    candidate = {
        "line_id": "dm002-current-line",
        "title": "DM002 diabetes China-US mortality attribution",
        "question": "Can the current DM002 line clear AI-reviewer-backed publishability?",
        "evidence_refs": [evidence_ref],
        "stage_output_refs": [
            "artifacts/stage_knowledge/idea/latest.json",
            "artifacts/stage_knowledge/idea/closeouts/dm002-current-line.json",
        ],
        "evidence_basis": [evidence_ref, str(study_root / "artifacts" / "publication_eval" / "latest.json")],
        "expected_artifact": "artifacts/medical_paper/open_auto_research_candidate_path.json",
        "stop_rule": "stop or human gate if publication authority still requires AI reviewer clearance",
        "decision": "human_gate",
        "dimensions": {
            "novelty": 3,
            "clinical_relevance": 4,
            "data_fit": 4,
            "external_validation": 3,
            "analysis_feasibility": 3,
            "journal_fit": 3,
            "risk_cost": 2,
            "stop_threshold": "publication gate remains blocked",
        },
    }
    projection = route_decision_orchestrator.build_route_decision_orchestration(
        study_root=study_root,
        candidates=[candidate],
        requested_action="open_auto_research_soak_review",
    )
    path = (study_root / ROUTE_RELATIVE_PATH).resolve()
    _write_json(path, projection)
    return {
        "surface": projection["surface"],
        "status": projection["status"],
        "artifact_path": str(path),
        "candidate_path_decision": _mapping(projection.get("candidate_path_graph")).get("decision"),
    }


def _entry_projection_results(projection: Mapping[str, Any]) -> dict[str, Any]:
    counts = dict(_mapping(projection.get("counts")))
    actions = [
        {
            key: item[key]
            for key in ("action_id", "status", "surface")
            if isinstance(item, Mapping) and key in item
        }
        for item in projection.get("actions") or []
        if isinstance(item, Mapping)
    ]
    compact = {
        "open_auto_research_status": projection.get("status"),
        "counts": counts,
        "actions": actions,
        "delivery_journal_usability_guard": dict(
            _mapping(projection.get("delivery_journal_usability_guard"))
        ),
        "authority": dict(_mapping(projection.get("authority"))),
        "refs": dict(_mapping(projection.get("refs"))),
    }
    return {
        "study_progress": dict(compact),
        "product_entry_status": dict(compact),
        "workspace_cockpit": dict(compact),
        "mcp_compact": dict(compact),
    }


def _live_runtime_context(runtime_status_payload: Mapping[str, Any]) -> dict[str, Any]:
    supervisor = _mapping(runtime_status_payload.get("publication_supervisor_state"))
    recovery = _mapping(runtime_status_payload.get("runtime_recovery_lifecycle"))
    reason = _text(runtime_status_payload.get("reason"))
    recovery_state = _text(recovery.get("state"))
    quest_status = _text(runtime_status_payload.get("quest_status"))
    if recovery_state == "recovering" or quest_status == "recovering" or reason == "quest_marked_running_but_no_live_session":
        current_stage = "managed_runtime_recovering"
    elif quest_status in {"active", "running"}:
        current_stage = "managed_runtime_active"
    else:
        current_stage = _text(runtime_status_payload.get("current_stage")) or "runtime_status_observed"
    return {
        "current_stage": current_stage,
        "paper_stage": _text(supervisor.get("supervisor_phase")) or _text(runtime_status_payload.get("paper_stage")) or "unknown",
        "quest_status": quest_status,
        "reason": reason,
        "active_run_id": _text(runtime_status_payload.get("active_run_id")),
        "worker_live_session_present": _worker_live_session_present(runtime_status_payload),
    }


def _remaining_gaps(
    *,
    study_root: Path,
    runtime_status_payload: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> list[str]:
    gaps: list[str] = []
    publication_eval = _read_json(study_root / "artifacts" / "publication_eval" / "latest.json")
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    supervisor = _mapping(runtime_status_payload.get("publication_supervisor_state"))
    recovery = _mapping(runtime_status_payload.get("runtime_recovery_lifecycle"))
    if provenance.get("ai_reviewer_required") is True:
        gaps.append("ai_reviewer_required")
    if _text(supervisor.get("supervisor_phase")) == "publishability_gate_blocked" or _text(
        _mapping(publication_eval.get("verdict")).get("overall_verdict")
    ) == "blocked":
        gaps.append("publication_gate_blocked")
    if (
        _text(recovery.get("state")) == "recovering"
        or _text(runtime_status_payload.get("quest_status")) == "recovering"
        or _text(runtime_status_payload.get("reason")) == "quest_marked_running_but_no_live_session"
    ):
        gaps.append("runtime_recovering")
    if projection.get("status") == "blocked":
        gaps.append("open_auto_research_sources_blocked")
    return _dedupe(gaps)


def _input_refs(study_root: Path, runtime_status_payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = {
        "study_root": str(study_root),
        "publication_eval": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        "controller_decisions": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        "paper_evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "manuscript_evidence_ledger": str(study_root / "manuscript" / "evidence_ledger.json"),
    }
    for key in ("quest_root", "active_run_id"):
        value = _text(runtime_status_payload.get(key))
        if value is not None:
            refs[key] = value
    return refs


def _authority_guard_results(
    *,
    study_root: Path,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    written_paths: Sequence[Path],
) -> dict[str, Any]:
    changed = [
        relative
        for relative, before_item in before.items()
        if before_item != after.get(relative)
    ]
    allowed = {str(Path(item)) for item in AUTHORITY["controller_write_scope"]}
    written_refs = [_relative_ref(study_root=study_root, path=path) for path in written_paths]
    unauthorized = [ref for ref in written_refs if ref not in allowed]
    return {
        "forbidden_surface_unchanged": not changed,
        "authorized_writes_only": not changed and not unauthorized,
        "written_refs": written_refs,
        "forbidden_write_refs": changed,
        "unauthorized_write_refs": unauthorized,
        "forbidden_surface_hashes": {
            "changed": changed,
            "before": dict(before),
            "after": dict(after),
        },
        "authority": {
            "can_authorize_publication_quality": False,
            "can_authorize_submission": False,
            "can_replace_controller_decision": False,
            "can_replace_study_truth": False,
            "can_replay_runtime": False,
        },
    }


def _hash_forbidden_surfaces(study_root: Path) -> dict[str, Any]:
    return {str(relative): _hash_path(study_root / relative) for relative in FORBIDDEN_RELATIVE_PATHS}


def _hash_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "kind": "missing", "sha256": None}
    if path.is_file():
        return {"exists": True, "kind": "file", "sha256": _file_sha(path)}
    if path.is_dir():
        digest = hashlib.sha256()
        file_count = 0
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            file_count += 1
            digest.update(str(child.relative_to(path)).encode("utf-8"))
            digest.update(b"\0")
            digest.update(child.read_bytes())
            digest.update(b"\0")
        return {"exists": True, "kind": "directory", "sha256": digest.hexdigest(), "file_count": file_count}
    return {"exists": True, "kind": "other", "sha256": None}


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_ref(*, study_root: Path, path: Path) -> str:
    resolved = Path(path).expanduser().resolve()
    try:
        return str(resolved.relative_to(study_root))
    except ValueError:
        return str(resolved)


def _read_first_json(paths: Sequence[Path]) -> tuple[Path | None, dict[str, Any]]:
    for path in paths:
        payload = _read_json(path)
        if payload:
            return path, payload
    return None, {}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _evidence_nodes_from_ledger(
    ledger: Mapping[str, Any],
    *,
    evidence_path: Path | None,
) -> list[dict[str, Any]]:
    raw_items = ledger.get("items")
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        raw_items = ledger.get("evidence_items")
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        return []
    nodes: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, Mapping):
            continue
        source_ref = _text(item.get("source_ref"))
        item_id = _text(item.get("item_id")) or _text(item.get("id")) or f"item-{index + 1}"
        if source_ref is None and evidence_path is not None:
            source_ref = f"{evidence_path}#{item_id}"
        node = {
            "node_id": item_id,
            "claim": _text(item.get("claim")) or _text(item.get("summary")) or _text(item.get("title")),
            "pmid": _text(item.get("pmid")),
            "doi": _text(item.get("doi")),
            "guideline_ref": _text(item.get("guideline_ref")),
            "source_ref": source_ref,
        }
        nodes.append({key: value for key, value in node.items() if value is not None})
    return nodes


def _provenance_refs(evidence_nodes: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for node in evidence_nodes:
        if pmid := _text(node.get("pmid")):
            refs.append(f"pmid:{pmid}")
        if doi := _text(node.get("doi")):
            refs.append(f"doi:{doi}")
        if guideline_ref := _text(node.get("guideline_ref")):
            refs.append(guideline_ref)
        if source_ref := _text(node.get("source_ref")):
            refs.append(source_ref)
    return _dedupe(refs)


def _worker_live_session_present(runtime_status_payload: Mapping[str, Any]) -> bool:
    liveness = _mapping(runtime_status_payload.get("runtime_liveness_audit"))
    status = _text(liveness.get("status"))
    if status in {"live", "present", "active"}:
        return True
    if _text(runtime_status_payload.get("reason")) == "quest_marked_running_but_no_live_session":
        return False
    return bool(runtime_status_payload.get("worker_live_session_present"))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = [
    "run_open_auto_research_soak",
    "render_open_auto_research_soak_markdown",
    "stable_open_auto_research_soak_path",
]
