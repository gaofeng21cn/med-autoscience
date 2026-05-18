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
    task_id = f"agent-lab-task:mas/{study_id}/high-quality-medical-manuscript"
    scorecard_ref = f"quality-scorecard:mas/{study_id}/high-quality-medical-manuscript"
    promotion_gate_ref = f"promotion-gate:mas/{study_id}/high-quality-medical-manuscript"
    return {
        "suite_id": f"mas-agent-lab-suite:{study_id}:high-quality-medical-manuscript",
        "suite_kind": "agent_lab_external_suite",
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
                    "stage:mas/publication-gate",
                ],
                "oracle_refs": [
                    "oracle:mas/ai-reviewer-publication-eval",
                    "oracle:mas/review-ledger",
                    "oracle:mas/evidence-ledger",
                ],
                "scorer_refs": [
                    "scorer:mas/ai-reviewer-medical-publication-critique-v1",
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


__all__ = [
    "build_medical_manuscript_quality_agent_lab_suite",
    "materialize_medical_manuscript_quality_agent_lab_suite",
    "stable_medical_manuscript_quality_suite_path",
]
