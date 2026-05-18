from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SURFACE_KIND = "mas_agent_lab_medical_manuscript_quality_suite"
SUITE_RELATIVE_PATH = Path("artifacts") / "agent_lab" / "medical_manuscript_quality" / "latest_suite.json"
AUTHORITY_BOUNDARY = {
    "opl": "agent_lab_eval_improvement_control_plane_refs_only",
    "mas": "publication_quality_and_artifact_authority",
    "can_write_domain_truth": False,
    "can_write_memory_body": False,
    "can_authorize_domain_ready": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_submission_readiness": False,
    "can_mutate_domain_artifact": False,
    "can_promote_default_agent_without_gate": False,
}
SELF_EVOLUTION_TARGET_REFS = [
    "stage_policy_ref:mas/write/pre_draft_prediction_model_reporting",
    "mechanism-edit-ref:mas/research-wiki-failed-route-memory",
    "mechanism-edit-ref:mas/ai-reviewer-direct-evidence-gate",
    "mechanism-edit-ref:mas/analysis-campaign-queue-routing",
    "mechanism-edit-ref:mas/analysis-harmonization-owner-routing",
    "skill_ref:medical-research-write",
    "rubric_ref:ai_reviewer/high_quality_medical_manuscript",
    "prompt_ref:ai_reviewer_medical_prose_quality_review",
    "quality_contract_ref:prediction_model_first_draft_quality",
    "regression-suite:mas/hard-methodology-unit-harmonization-route",
    "regression_suite_ref:mas/agent_lab_medical_manuscript_self_evolution",
]


def stable_medical_manuscript_quality_suite_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / SUITE_RELATIVE_PATH


def build_medical_manuscript_quality_agent_lab_suite(
    *,
    study_root: Path,
    reviewer_feedback_ref: str | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    study_id = root.name
    publication_eval_path = root / "artifacts" / "publication_eval" / "latest.json"
    task_intake_path = root / "artifacts" / "controller" / "task_intake" / "latest.json"
    publication_eval = _read_json_object(publication_eval_path)
    prose_quality = _quality_dimension(publication_eval, "medical_journal_prose_quality")
    prose_status = _text(prose_quality.get("status")) or "underdefined"
    feedback_ref = _resolve_feedback_ref(task_intake_path=task_intake_path, reviewer_feedback_ref=reviewer_feedback_ref)
    scorecard_passed = prose_status == "ready" and feedback_ref is None
    evidence_refs = _existing_refs(
        publication_eval_path,
        root / "paper" / "draft.md",
        root / "paper" / "manuscript.md",
        root / "paper" / "evidence_ledger.json",
        root / "paper" / "review" / "review_ledger.json",
        root / "paper" / "medical_manuscript_blueprint.json",
        root / "paper" / "claim_evidence_map.json",
        root / "paper" / "target_journal_writing_layer.json",
    )
    if feedback_ref is not None:
        evidence_refs.append(feedback_ref)
    blocker_refs = _blocker_refs(prose_status=prose_status, feedback_ref=feedback_ref, study_id=study_id)
    mechanism_inputs = _mechanism_evolution_inputs(
        root=root,
        study_id=study_id,
        publication_eval_path=publication_eval_path,
        task_intake_path=task_intake_path,
        feedback_ref=feedback_ref,
        evidence_refs=evidence_refs,
        blocker_refs=blocker_refs,
    )
    task_id = f"agent-lab-task:mas/{study_id}/high-quality-medical-manuscript"
    scorecard_ref = f"quality-scorecard:mas/{study_id}/high-quality-medical-manuscript"
    promotion_gate_ref = f"promotion-gate:mas/{study_id}/high-quality-medical-manuscript"
    return {
        "suite_id": f"mas-agent-lab-suite:{study_id}:high-quality-medical-manuscript",
        "suite_kind": "agent_lab_external_suite",
        "suite_role": "domain_quality_suite_with_meta_evolution_projection",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "tasks": [
            {
                "task_id": task_id,
                "domain_id": "med-autoscience",
                "task_family": "high_quality_medical_manuscript_self_evolution",
                "authority_boundary": dict(AUTHORITY_BOUNDARY),
                "environment": {
                    "environment_kind": "local_workspace",
                    "workspace_locator_ref": f"workspace-locator:mas/{study_id}",
                    "sandbox_policy": "refs_only_no_artifact_mutation",
                    "network_policy": "domain_owner_policy",
                    "resource_limits": {"max_stage_attempts": 4},
                },
                "instructions_ref": "instructions:mas/high-quality-medical-manuscript-ai-reviewer",
                "agent_entry_ref": "domain-agent-entry:med-autoscience",
                "stage_refs": [
                    "stage:mas/review",
                    "stage:mas/analysis-campaign",
                    "stage:mas/write",
                    "stage:mas/write/pre_draft_prediction_model_reporting",
                    "stage:mas/figure-polish/high_quality_medical_journal_figures",
                    "stage:mas/publication-gate",
                ],
                "oracle_refs": [
                    "oracle:mas/ai-reviewer-publication-eval",
                    "oracle:mas/review-ledger",
                    "oracle:mas/evidence-ledger",
                ],
                "scorer_refs": [
                    "scorer:mas/ai-reviewer-medical-publication-critique-v1",
                    "scorer:mas/prediction-model-first-draft-quality",
                    scorecard_ref,
                ],
                "recovery_probes": [
                    {
                        "probe_ref": f"recovery-probe:mas/{study_id}/review-route-redrive",
                        "probe_kind": "resume_after_interruption",
                        "expected_status": "passed",
                        "observed_status": "passed",
                        "source_refs": [str(task_intake_path) if task_intake_path.exists() else str(publication_eval_path)],
                    }
                ],
                "trajectory": {
                    "trajectory_ref": f"trajectory:mas/{study_id}/high-quality-medical-manuscript",
                    "run_ref": f"run:mas/{study_id}/high-quality-medical-manuscript-agent-lab-projection",
                    "agent_executor": "codex_cli",
                    "stage_attempt_refs": ["stage-attempt:mas/ai-reviewer-medical-prose-quality-review"],
                    "tool_call_refs": ["tool-call:mas/publication-eval-read", "tool-call:mas/review-ledger-read"],
                    "artifact_refs": evidence_refs,
                    "receipt_refs": [str(publication_eval_path)] if publication_eval_path.exists() else [],
                    "repair_refs": blocker_refs,
                    "trace_refs": ["trace-ref:agent-lab/mas-high-quality-medical-manuscript"],
                    "authority_boundary": dict(AUTHORITY_BOUNDARY),
                },
                "mechanism_evolution_inputs": mechanism_inputs,
                "scorecard": {
                    "scorecard_ref": scorecard_ref,
                    "domain_owned": True,
                    "opl_scorecard_role": "scorecard_ref_projection_only",
                    "passed": scorecard_passed,
                    "metric_refs": [
                        f"metric-ref:mas/{study_id}/medical_journal_prose_quality:{prose_status}",
                        "metric-ref:mas/high-quality-medical-manuscript/reproducibility-results-tables-figures",
                    ],
                    "evidence_refs": evidence_refs,
                    "review_refs": [str(root / "paper" / "review" / "review_ledger.json")],
                    "quality_gate_refs": ["quality-gate:mas/publication-owner"],
                    "authority_boundary": dict(AUTHORITY_BOUNDARY),
                },
                "improvement_candidate": {
                    "candidate_ref": f"improvement-candidate:mas/{study_id}/high-quality-medical-manuscript-rubric-gap",
                    "candidate_kind": "rubric_gap",
                    "target_ref": "rubric-gap-ref:mas/high-quality-medical-manuscript-ai-reviewer",
                    "evidence_refs": blocker_refs or evidence_refs,
                    "target_agent_capability_gap": {
                        "status": "candidate_only",
                        "target_owner": "med-autoscience",
                        "target_editable_surface_refs": list(SELF_EVOLUTION_TARGET_REFS),
                        "cannot_authorize_quality_verdict": True,
                    },
                    "allowed_change_scope": "branch_only",
                    "promotion_gate_ref": promotion_gate_ref,
                    "authority_boundary": dict(AUTHORITY_BOUNDARY),
                },
                "promotion_gate": {
                    "gate_ref": promotion_gate_ref,
                    "gate_status": "passed" if scorecard_passed else "blocked",
                    "required_refs": [scorecard_ref, "owner-receipt:mas/ai-reviewer-publication-eval"],
                    "regression_suite_refs": [
                        "regression-suite:mas/ai-first-quality-boundary",
                        "regression-suite:mas/paper-authority-clean-migration",
                        "regression-suite:mas/prediction-model-first-draft-quality",
                        "regression-suite:mas/hard-methodology-unit-harmonization-route",
                        "regression-suite:mas/agent-lab-medical-manuscript-self-evolution",
                        "regression-suite:mas/agent-lab-research-wiki-reviewer-analysis-queue",
                    ],
                    "no_forbidden_write_proof_refs": [
                        "no-forbidden-write:mas/agent-lab-medical-manuscript-quality"
                    ],
                    "authority_boundary": dict(AUTHORITY_BOUNDARY),
                },
            }
        ],
    }


def materialize_medical_manuscript_quality_agent_lab_suite(
    *,
    study_root: Path,
    reviewer_feedback_ref: str | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    suite = build_medical_manuscript_quality_agent_lab_suite(
        study_root=root,
        reviewer_feedback_ref=reviewer_feedback_ref,
    )
    path = stable_medical_manuscript_quality_suite_path(study_root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface_kind": SURFACE_KIND,
        "status": "materialized",
        "study_id": root.name,
        "suite_path": str(path),
        "suite": suite,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _resolve_feedback_ref(*, task_intake_path: Path, reviewer_feedback_ref: str | None) -> str | None:
    explicit = _text(reviewer_feedback_ref)
    if explicit:
        return explicit
    if task_intake_path.exists():
        return str(task_intake_path)
    return None


def _blocker_refs(*, prose_status: str, feedback_ref: str | None, study_id: str) -> list[str]:
    refs: list[str] = []
    if prose_status != "ready":
        refs.append(f"rubric-gap:mas/{study_id}/medical_journal_prose_quality:{prose_status}")
    if feedback_ref is not None:
        refs.extend(
            [
                f"rubric-gap:mas/{study_id}/hdl-harmonization-and-sensitivity",
                f"rubric-gap:mas/{study_id}/model-reproducibility-and-baseline-survival",
                f"rubric-gap:mas/{study_id}/table1-table2-visible-baseline-performance",
                f"rubric-gap:mas/{study_id}/uncertainty-intervals-and-validation-metrics",
                f"rubric-gap:mas/{study_id}/nhanes-survey-weighting-and-unweighted-framing",
                f"rubric-gap:mas/{study_id}/calibration-risk-collapse-and-figure-quality",
                f"rubric-gap:mas/{study_id}/internal-quality-language-purge",
            ]
        )
    return refs


def _mechanism_evolution_inputs(
    *,
    root: Path,
    study_id: str,
    publication_eval_path: Path,
    task_intake_path: Path,
    feedback_ref: str | None,
    evidence_refs: list[str],
    blocker_refs: list[str],
) -> dict[str, Any]:
    research_wiki_refs = _existing_refs(
        root / "artifacts" / "research_wiki" / "latest.json",
        root / "paper" / "research_wiki.json",
        root / "paper" / "route_memory.json",
    )
    failed_route_refs = _failed_route_refs(root=root, study_id=study_id)
    reviewer_direct_evidence_refs = _existing_refs(
        root / "paper" / "review" / "review_ledger.json",
        root / "artifacts" / "publication_eval" / "latest.json",
        root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        task_intake_path,
    )
    if feedback_ref is not None and feedback_ref not in reviewer_direct_evidence_refs:
        reviewer_direct_evidence_refs.append(feedback_ref)
    analysis_queue_manifest_refs = _existing_refs(
        root / "artifacts" / "analysis_queue" / "latest.json",
        root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        root / "artifacts" / "analysis_campaign" / "latest_manifest.json",
        root / "paper" / "analysis_queue.json",
    )
    research_memory_graph = _research_memory_graph(
        root=root,
        study_id=study_id,
        research_wiki_refs=research_wiki_refs,
        failed_route_refs=failed_route_refs,
    )
    analysis_queue_manifest = _analysis_queue_manifest(
        root=root,
        study_id=study_id,
        manifest_refs=analysis_queue_manifest_refs,
    )
    return {
        "surface_kind": "mas_agent_lab_mechanism_evolution_inputs",
        "target_opl_surface": "opl_agent_lab_evolution_result",
        "target_opl_cli": "opl agent-lab evolve --suite <suite.json> --json",
        "automatic_mechanism_promotion_route": "risk_tiered_auto_promotion_with_independent_ai_review",
        "research_wiki_refs": research_wiki_refs,
        "failed_route_refs": failed_route_refs,
        "research_memory_graph": research_memory_graph,
        "reviewer_direct_evidence_refs": reviewer_direct_evidence_refs,
        "analysis_queue_manifest_refs": analysis_queue_manifest_refs,
        "analysis_queue_manifest": analysis_queue_manifest,
        "target_editable_surface_refs": list(SELF_EVOLUTION_TARGET_REFS),
        "evidence_delta_refs": _unique_refs(
            [
                *evidence_refs,
                *blocker_refs,
                *research_wiki_refs,
                *failed_route_refs,
                *reviewer_direct_evidence_refs,
                *analysis_queue_manifest_refs,
            ]
        ),
        "independent_ai_review_receipt_ref": f"ai-reviewer-receipt:mas/{study_id}/mechanism-direct-evidence-review",
        "version_ledger_ref": f"mechanism-version-ledger:mas/{study_id}/medical-manuscript-quality",
        "rollback_ref": "mechanism-rollback-ref:mas/agent-lab-medical-manuscript-quality",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "forbidden_writes": [
            str(publication_eval_path),
            "controller_decisions/latest.json",
            "manuscript/current_package",
            "paper/submission_minimal",
            "publication-route-memory-body",
        ],
    }


def _research_memory_graph(
    *,
    root: Path,
    study_id: str,
    research_wiki_refs: list[str],
    failed_route_refs: list[str],
) -> dict[str, Any]:
    paths = (
        root / "artifacts" / "research_wiki" / "latest.json",
        root / "paper" / "research_wiki.json",
        root / "paper" / "route_memory.json",
    )
    graph = {
        "surface_kind": "mas_research_memory_graph",
        "graph_kind": "body_free_research_memory_graph",
        "body_included": False,
        "memory_body_authority": "mas_publication_route_memory_owner",
        "manifest_refs": research_wiki_refs,
        "paper_refs": _memory_refs(
            paths=paths,
            key="paper_refs",
            study_id=study_id,
        ),
        "claim_refs": _memory_refs(
            paths=paths,
            key="claim_refs",
            study_id=study_id,
        ),
        "experiment_refs": _memory_refs(
            paths=paths,
            key="experiment_refs",
            study_id=study_id,
        ),
        "failed_idea_refs": _memory_refs(
            paths=paths,
            key="failed_idea_refs",
            aliases=("failed_ideas",),
            study_id=study_id,
        ),
        "negative_result_refs": _memory_refs(
            paths=paths,
            key="negative_result_refs",
            aliases=("negative_results",),
            study_id=study_id,
        ),
        "reusable_rationale_refs": _memory_refs(
            paths=paths,
            key="reusable_rationale_refs",
            aliases=("reusable_rationales", "rationale_refs"),
            study_id=study_id,
        ),
        "failed_route_refs": failed_route_refs,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    return graph


def _analysis_queue_manifest(
    *,
    root: Path,
    study_id: str,
    manifest_refs: list[str],
) -> dict[str, Any]:
    paths = (
        root / "artifacts" / "analysis_queue" / "latest.json",
        root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        root / "artifacts" / "analysis_campaign" / "latest_manifest.json",
        root / "paper" / "analysis_queue.json",
    )
    payloads = [_read_json_object(path) for path in paths]
    payloads = [payload for payload in payloads if payload]
    queue_ref = _first_text(payloads, "queue_ref", "ref", "id", "manifest_ref")
    state = _first_text(payloads, "state", "status", "queue_state")
    retry_policy = _first_mapping(payloads, "retry_policy") or {
        "policy_ref": "retry-policy:mas/analysis-campaign/idempotent-owner-replay",
        "max_retry_count": 0,
        "requires_owner_receipt": True,
        "can_authorize_quality_verdict": False,
    }
    budget = _first_mapping(payloads, "budget") or {
        "budget_ref": f"analysis-budget:mas/{study_id}/medical-manuscript-quality",
        "state": "blocked",
        "body_included": False,
    }
    items = _analysis_queue_items(payloads=payloads, study_id=study_id, manifest_refs=manifest_refs)
    return {
        "surface_kind": "mas_analysis_queue_manifest",
        "manifest_kind": "body_free_analysis_queue_manifest",
        "body_included": False,
        "queue_ref": queue_ref or f"analysis-queue:mas/{study_id}/medical-manuscript-quality",
        "state": state or ("active" if manifest_refs and items else "blocked"),
        "retry_policy": retry_policy,
        "budget": budget,
        "items": items,
        "manifest_refs": manifest_refs,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _failed_route_refs(*, root: Path, study_id: str) -> list[str]:
    paths = (
        root / "artifacts" / "research_wiki" / "latest.json",
        root / "paper" / "research_wiki.json",
        root / "paper" / "route_memory.json",
    )
    refs = _json_refs_for_keys(paths=paths, keys=("failed_route_refs", "failed_routes"))
    if refs:
        return _unique_refs(refs)
    return [f"failed-route:mas/{study_id}/medical-manuscript-quality-gap"]


def _memory_refs(
    *,
    paths: tuple[Path, ...],
    key: str,
    study_id: str,
    aliases: tuple[str, ...] = (),
) -> list[str]:
    refs = _json_refs_for_keys(paths=paths, keys=(key, *aliases))
    if refs:
        return _unique_refs(refs)
    return [f"research-memory-ref:mas/{study_id}/{key}/body-free-fallback"]


def _json_refs_for_keys(*, paths: tuple[Path, ...], keys: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    for path in paths:
        payload = _read_json_object(path)
        for key in keys:
            refs.extend(_refs_from_value(payload.get(key)))
    return refs


def _json_refs(path: Path, key: str) -> list[str]:
    payload = _read_json_object(path)
    return _refs_from_value(payload.get(key))


def _analysis_queue_items(
    *,
    payloads: list[dict[str, Any]],
    study_id: str,
    manifest_refs: list[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for payload in payloads:
        for key in ("items", "queue_items", "analysis_items"):
            values = payload.get(key)
            if not isinstance(values, list):
                continue
            for item in values:
                normalized = _analysis_queue_item(item, default_state=_text(payload.get("state")))
                if normalized:
                    items.append(normalized)
    if items:
        return _unique_items(items)
    return [
        {
            "ref": f"analysis-queue-item:mas/{study_id}/medical-manuscript-quality-blocked",
            "state": "blocked",
            "retry_count": 0,
            "budget_cost": 0,
            "source_refs": manifest_refs
            or [f"analysis-queue-missing:mas/{study_id}/medical-manuscript-quality"],
        }
    ]


def _analysis_queue_item(item: object, *, default_state: str) -> dict[str, Any] | None:
    if isinstance(item, Mapping):
        ref = _item_ref(item)
        if not ref:
            return None
        return {
            "ref": ref,
            "state": _text(item.get("state") or item.get("status")) or default_state or "blocked",
            "retry_count": _int(item.get("retry_count"), default=0),
            "budget_cost": item.get("budget_cost", item.get("cost", 0)),
            "source_refs": _refs_from_value(item.get("source_refs")),
        }
    ref = _text(item)
    if not ref:
        return None
    return {
        "ref": ref,
        "state": default_state or "blocked",
        "retry_count": 0,
        "budget_cost": 0,
        "source_refs": [],
    }


def _refs_from_value(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    refs: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            ref = _item_ref(item)
            if ref:
                refs.append(ref)
        else:
            ref = _text(item)
            if ref:
                refs.append(ref)
    return refs


def _item_ref(item: Mapping[str, Any]) -> str:
    for key in (
        "ref",
        "id",
        "route_ref",
        "paper_ref",
        "claim_ref",
        "experiment_ref",
        "idea_ref",
        "failed_idea_ref",
        "negative_result_ref",
        "rationale_ref",
        "queue_ref",
    ):
        ref = _text(item.get(key))
        if ref:
            return ref
    return ""


def _first_text(payloads: list[dict[str, Any]], *keys: str) -> str:
    for payload in payloads:
        for key in keys:
            value = _text(payload.get(key))
            if value:
                return value
    return ""


def _first_mapping(payloads: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for payload in payloads:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return dict(value)
        text = _text(value)
        if text:
            return {"policy_ref": text} if key == "retry_policy" else {"ref": text}
    return {}


def _unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        ref = _text(item.get("ref"))
        if not ref or ref in seen:
            continue
        seen.add(ref)
        unique.append(item)
    return unique


def _unique_refs(refs: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if not ref or ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    return unique


def _quality_dimension(publication_eval: Mapping[str, Any], dimension: str) -> dict[str, Any]:
    quality = publication_eval.get("quality_assessment")
    if not isinstance(quality, Mapping):
        return {}
    item = quality.get(dimension)
    return dict(item) if isinstance(item, Mapping) else {}


def _existing_refs(*paths: Path) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        ref = str(path)
        if ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return refs


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


__all__ = [
    "build_medical_manuscript_quality_agent_lab_suite",
    "materialize_medical_manuscript_quality_agent_lab_suite",
    "stable_medical_manuscript_quality_suite_path",
]
