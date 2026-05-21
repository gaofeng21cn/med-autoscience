from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .agent_lab_aris_followup_assurance import build_aris_followup_assurance_surfaces
from .agent_lab_medical_manuscript_quality_parts.quality_boundary import (
    AUTHORITY_BOUNDARY,
    CROSS_STAGE_VULNERABILITY_AUDIT,
    DEVELOPER_PATCH_WORK_ORDER_ID,
    PAPER_STORY_EXCLUSION_POLICY,
    QUALITY_JUDGMENT_BOUNDARY,
    SELF_EVOLUTION_TARGET_REFS,
    SUITE_RELATIVE_PATH,
    SURFACE_KIND,
)
from .agent_lab_medical_manuscript_quality_parts.study_quality_targets import (
    study_quality_target_profile,
)
from .agent_lab_medical_manuscript_quality_parts.patch_loop_closeout import (
    build_refs_only_patch_loop_closeout_bundle,
)
from .agent_lab_submission_assurance import build_submission_assurance_surfaces
from .publication_aftercare import build_publication_aftercare_plan


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
    developer_work_order = _developer_patch_work_order(
        study_id=study_id,
        evidence_refs=blocker_refs or evidence_refs,
    )
    task = {
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
            "developer_patch_work_order": developer_work_order,
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
                "regression-suite:mas/ai-reviewer-output-readiness-currentness",
                "regression-suite:mas/medical-prose-write-repair-story-surface-delta",
                "regression-suite:mas/agent-lab-medical-manuscript-self-evolution",
                "regression-suite:mas/agent-lab-research-wiki-reviewer-analysis-queue",
            ],
            "no_forbidden_write_proof_refs": [
                "no-forbidden-write:mas/agent-lab-medical-manuscript-quality"
            ],
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        },
    }
    task["patch_loop_closeout_bundle"] = build_refs_only_patch_loop_closeout_bundle(
        root=root,
        study_id=study_id,
        suite_id=f"mas-agent-lab-suite:{study_id}:high-quality-medical-manuscript",
        task_id=task_id,
        promotion_gate_ref=promotion_gate_ref,
        developer_work_order=developer_work_order,
        target_editable_surface_refs=list(SELF_EVOLUTION_TARGET_REFS),
        controller_read_model_feedback_refs=mechanism_inputs["controller_read_model_feedback_refs"],
        forbidden_writes=mechanism_inputs["forbidden_writes"],
    )
    return {
        "suite_id": f"mas-agent-lab-suite:{study_id}:high-quality-medical-manuscript",
        "suite_kind": "agent_lab_external_suite",
        "suite_role": "domain_quality_suite_with_meta_evolution_projection",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "tasks": [task],
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
        profile = study_quality_target_profile(study_id=study_id)
        refs.extend(f"rubric-gap:mas/{study_id}/{slug}" for slug in profile["blocker_ref_slugs"])
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
    controller_read_model_feedback_refs = _controller_read_model_feedback_refs(root=root, study_id=study_id)
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
    runtime_event_ledger = _runtime_event_ledger(root=root, study_id=study_id)
    provider_switch_hygiene = _provider_switch_hygiene(root=root, study_id=study_id)
    claim_assurance_map = _claim_assurance_map(root=root, study_id=study_id)
    followup_surfaces = build_aris_followup_assurance_surfaces(
        root=root,
        study_id=study_id,
        publication_eval_path=publication_eval_path,
        task_intake_path=task_intake_path,
        analysis_queue_manifest_refs=analysis_queue_manifest_refs,
        authority_boundary=AUTHORITY_BOUNDARY,
    )
    submission_assurance_surfaces = build_submission_assurance_surfaces(
        root=root,
        study_id=study_id,
        authority_boundary=AUTHORITY_BOUNDARY,
    )
    publication_aftercare_plan = build_publication_aftercare_plan(study_root=root)
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
        "runtime_event_ledger": runtime_event_ledger,
        "provider_switch_hygiene": provider_switch_hygiene,
        "claim_assurance_map": claim_assurance_map,
        "assurance_contract_refs": followup_surfaces["assurance_contract"]["raw_evidence_refs"]
        + followup_surfaces["assurance_contract"]["evidence_ledger_refs"]
        + followup_surfaces["assurance_contract"]["review_ledger_refs"]
        + followup_surfaces["assurance_contract"]["publication_gate_refs"],
        "adversarial_review_gate_refs": followup_surfaces["adversarial_review_gate"]["promotion_gate_inputs"],
        "experiment_queue_recovery_refs": followup_surfaces["experiment_queue_recovery"][
            "experiment_queue_recovery_refs"
        ],
        "publication_aftercare_plan_refs": publication_aftercare_plan["publication_aftercare_plan_refs"],
        "citation_audit_refs": submission_assurance_surfaces["citation_audit"]["citation_audit_refs"],
        "kill_argument_review_refs": submission_assurance_surfaces["kill_argument_review"][
            "counterargument_review_refs"
        ],
        "submission_assurance_gate_refs": submission_assurance_surfaces["submission_assurance_gate"][
            "gate_refs"
        ],
        "effort_assurance_axis_refs": submission_assurance_surfaces["effort_assurance_axes"][
            "axis_input_refs"
        ],
        "assurance_contract": followup_surfaces["assurance_contract"],
        "adversarial_review_gate": followup_surfaces["adversarial_review_gate"],
        "experiment_queue_recovery": followup_surfaces["experiment_queue_recovery"],
        "publication_aftercare_plan": publication_aftercare_plan,
        "citation_audit": submission_assurance_surfaces["citation_audit"],
        "kill_argument_review": submission_assurance_surfaces["kill_argument_review"],
        "submission_assurance_gate": submission_assurance_surfaces["submission_assurance_gate"],
        "effort_assurance_axes": submission_assurance_surfaces["effort_assurance_axes"],
        "controller_read_model_feedback_refs": controller_read_model_feedback_refs,
        "target_editable_surface_refs": list(SELF_EVOLUTION_TARGET_REFS),
        "developer_patch_work_order": _developer_patch_work_order(
            study_id=study_id,
            evidence_refs=_unique_refs(
                [*(blocker_refs or evidence_refs), *controller_read_model_feedback_refs]
            ),
        ),
        "evidence_delta_refs": _unique_refs(
            [
                *evidence_refs,
                *blocker_refs,
                *research_wiki_refs,
                *failed_route_refs,
                *reviewer_direct_evidence_refs,
                *analysis_queue_manifest_refs,
                *controller_read_model_feedback_refs,
                *runtime_event_ledger["event_source_refs"],
                *runtime_event_ledger["supervision_event_refs"],
                *runtime_event_ledger["controller_event_refs"],
                *provider_switch_hygiene["provider_state_refs"],
                *provider_switch_hygiene["executor_context_refs"],
                *provider_switch_hygiene["fallback_refs"],
                *claim_assurance_map["claim_map_refs"],
                *claim_assurance_map["claim_refs"],
                *claim_assurance_map["evidence_refs"],
                *claim_assurance_map["reviewer_refs"],
                *claim_assurance_map["display_refs"],
                *followup_surfaces["evidence_delta_refs"],
                *publication_aftercare_plan["evidence_delta_refs"],
                *submission_assurance_surfaces["evidence_delta_refs"],
            ]
        ),
        "independent_ai_review_receipt_ref": f"ai-reviewer-receipt:mas/{study_id}/mechanism-direct-evidence-review",
        "version_ledger_ref": f"mechanism-version-ledger:mas/{study_id}/medical-manuscript-quality",
        "rollback_ref": "mechanism-rollback-ref:mas/agent-lab-medical-manuscript-quality",
        "quality_judgment_boundary": dict(QUALITY_JUDGMENT_BOUNDARY),
        "cross_stage_vulnerability_audit": dict(CROSS_STAGE_VULNERABILITY_AUDIT),
        "paper_story_exclusion_policy": dict(PAPER_STORY_EXCLUSION_POLICY),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "forbidden_writes": [
            str(publication_eval_path),
            "controller_decisions/latest.json",
            "manuscript/current_package",
            "paper/submission_minimal",
            "publication-route-memory-body",
        ],
    }


def _developer_patch_work_order(*, study_id: str, evidence_refs: list[str]) -> dict[str, Any]:
    profile = study_quality_target_profile(study_id=study_id)
    return {
        "work_order_id": DEVELOPER_PATCH_WORK_ORDER_ID,
        "owner_agent": "opl-meta-agent",
        "role": "developer_direct_repo_patch",
        "target_repo": "med-autoscience",
        "status": "blocked_until_repo_patch",
        "trigger": "agent_lab_blocked_medical_manuscript_quality_suite",
        "target_editable_surface_refs": list(SELF_EVOLUTION_TARGET_REFS),
        "required_patch_scopes": [
            "analysis_harmonization_owner_callable",
            "source_provenance_owner_recovery",
            "source_provenance_terminal_blocker_route_back",
            "methodology_reframe_decision_owner_route",
            "hard_methodology_unit_harmonization_route",
            "domain_route_analysis_harmonization_owner_result_consumption",
            "ai_reviewer_output_readiness_currentness_consumption",
            "ai_native_expert_judgment_first_quality_boundary",
            "cross_stage_vulnerability_audit_routing",
            "internal_error_debug_history_paper_story_exclusion",
            "prediction_model_first_draft_quality_contract",
            "ai_reviewer_high_quality_medical_manuscript_rubric",
            "write_stage_pre_draft_prediction_model_reporting",
            "quality_repair_blocked_evidence_dispatch_rejection",
            "regression_tests_and_docs",
        ],
        "study_quality_target_family": profile["family"],
        "study_quality_targets": profile["targets"],
        "quality_judgment_boundary": dict(QUALITY_JUDGMENT_BOUNDARY),
        "cross_stage_vulnerability_audit": dict(CROSS_STAGE_VULNERABILITY_AUDIT),
        "paper_story_exclusion_policy": dict(PAPER_STORY_EXCLUSION_POLICY),
        "evidence_refs": evidence_refs,
        "forbidden_writes": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "paper/submission_minimal",
            "manuscript/current_package",
            "submission readiness verdict",
        ],
        "can_modify_mas_repo": True,
        "can_write_study_truth": False,
        "can_authorize_quality_verdict": False,
        "can_mutate_paper_package": False,
    }

def _controller_read_model_feedback_refs(*, root: Path, study_id: str) -> list[str]:
    refs = _existing_refs(
        root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        root / "artifacts" / "supervision" / "hourly" / "latest.json",
        root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unit_harmonized_external_validation_rerun.json",
    )
    if refs:
        refs.append(f"mechanism-defect-ref:mas/{study_id}/analysis-harmonization-result-requeued")
    return _unique_refs(refs)


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


def _runtime_event_ledger(*, root: Path, study_id: str) -> dict[str, Any]:
    event_paths = (
        root / ".ds" / "events.jsonl",
        root / "artifacts" / "runtime" / "events.jsonl",
    )
    supervision_paths = (
        root / "artifacts" / "supervision" / "events.jsonl",
        root / "artifacts" / "supervision" / "controller" / "events.jsonl",
        root / "artifacts" / "supervision" / "hourly" / "latest.json",
        root / "artifacts" / "controller" / "events.jsonl",
        root / "artifacts" / "controller" / "controller_events.jsonl",
        root / "artifacts" / "controller" / "runtime_events.jsonl",
    )
    event_source_refs = _existing_refs(*event_paths)
    supervision_event_refs = _existing_refs(*supervision_paths)
    controller_event_refs = _runtime_controller_event_refs(root=root)
    event_types = _jsonl_event_types((*event_paths, *supervision_paths))
    event_count = sum(_jsonl_count(path) for path in (*event_paths, *supervision_paths))
    if not event_source_refs and not supervision_event_refs and not controller_event_refs:
        controller_event_refs = [f"runtime-event-ledger-missing:mas/{study_id}/body-free"]
    return {
        "surface_kind": "mas_runtime_event_ledger",
        "ledger_kind": "body_free_runtime_event_metadata",
        "body_included": False,
        "event_source_refs": event_source_refs,
        "supervision_event_refs": supervision_event_refs,
        "controller_event_refs": controller_event_refs,
        "event_count": event_count,
        "event_type_refs": [f"runtime-event-type:mas/{study_id}/{event_type}" for event_type in event_types],
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _provider_switch_hygiene(*, root: Path, study_id: str) -> dict[str, Any]:
    provider_state_paths = (
        root / ".ds" / "runtime_state.json",
        root / "artifacts" / "runtime" / "provider_state.json",
        root / "artifacts" / "runtime" / "provider_switch.json",
        root / "artifacts" / "runtime" / "provider_switch_hygiene.json",
        root / "artifacts" / "controller" / "provider_state.json",
    )
    executor_context_paths = (
        root / "artifacts" / "runtime" / "executor_context.json",
        root / "artifacts" / "controller" / "executor_context.json",
        root / "artifacts" / "supervision" / "executor_context.json",
    )
    payloads = [_read_json_object(path) for path in (*provider_state_paths, *executor_context_paths)]
    payloads = [payload for payload in payloads if payload]
    provider_state_refs = _existing_refs(*provider_state_paths)
    executor_context_refs = _existing_refs(*executor_context_paths)
    fallback_refs = _refs_for_keys(
        payloads=payloads,
        keys=("fallback_refs", "provider_fallback_refs", "diagnostic_provider_refs", "state_fallback_refs"),
    )
    return {
        "surface_kind": "mas_provider_switch_hygiene",
        "hygiene_kind": "body_free_provider_executor_context_projection",
        "body_included": False,
        "read_only": True,
        "provider_state_refs": provider_state_refs or [f"provider-state-ref:mas/{study_id}/missing"],
        "executor_context_refs": executor_context_refs or [f"executor-context-ref:mas/{study_id}/missing"],
        "executor_refs": _refs_for_keys(payloads=payloads, keys=("executor_refs", "executor_ref"))
        or [f"executor-ref:mas/{study_id}/codex_cli"],
        "provider_refs": _refs_for_keys(payloads=payloads, keys=("provider_refs", "provider_ref"))
        or [f"provider-ref:mas/{study_id}/temporal-or-local-diagnostic"],
        "context_isolation_refs": _refs_for_keys(
            payloads=payloads,
            keys=("context_isolation_refs", "reviewer_context_isolation_refs", "no_shared_context_refs"),
        )
        or [f"context-isolation-ref:mas/{study_id}/reviewer-no-shared-context"],
        "fallback_refs": fallback_refs,
        "can_switch_provider": False,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _claim_assurance_map(*, root: Path, study_id: str) -> dict[str, Any]:
    claim_map_paths = (
        root / "paper" / "claim_evidence_map.json",
        root / "artifacts" / "publication_eval" / "latest.json",
        root / "paper" / "review" / "review_ledger.json",
        root / "artifacts" / "research_wiki" / "latest.json",
        root / "paper" / "research_wiki.json",
    )
    payloads = [_read_json_object(path) for path in claim_map_paths]
    payloads = [payload for payload in payloads if payload]
    claim_refs = _refs_for_keys(payloads=payloads, keys=("claim_refs", "claims", "claim_ref"))
    evidence_refs = _refs_for_keys(
        payloads=payloads,
        keys=("evidence_refs", "evidence", "supporting_evidence_refs", "source_refs"),
    )
    reviewer_refs = _refs_for_keys(
        payloads=payloads,
        keys=("reviewer_refs", "review_refs", "review_items", "reviewer_feedback_refs"),
    )
    display_refs = _refs_for_keys(
        payloads=payloads,
        keys=("display_refs", "display_material_refs", "table_refs", "figure_refs"),
    )
    return {
        "surface_kind": "mas_claim_assurance_map",
        "map_kind": "body_free_claim_evidence_reviewer_display_refs",
        "body_included": False,
        "claim_body_included": False,
        "can_authorize_claim": False,
        "can_authorize_quality_verdict": False,
        "claim_map_refs": _existing_refs(*claim_map_paths),
        "claim_refs": claim_refs or [f"claim-ref:mas/{study_id}/body-free-default"],
        "evidence_refs": evidence_refs,
        "reviewer_refs": reviewer_refs,
        "display_refs": display_refs,
        "claim_count": len(claim_refs),
        "evidence_count": len(evidence_refs),
        "reviewer_ref_count": len(reviewer_refs),
        "display_ref_count": len(display_refs),
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
    return [f"research-memory-ref:mas/{study_id}/{key}/body-free-default"]


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


def _runtime_controller_event_refs(*, root: Path) -> list[str]:
    refs: list[str] = []
    paths = (
        root / "artifacts" / "controller" / "latest.json",
        root / "artifacts" / "controller_decisions" / "latest.json",
        root / "artifacts" / "publication_eval" / "latest.json",
        root / "artifacts" / "supervision" / "hourly" / "latest.json",
    )
    for path in paths:
        payload = _read_json_object(path)
        refs.extend(
            _refs_for_keys(
                payloads=[payload],
                keys=(
                    "runtime_event_refs",
                    "event_refs",
                    "controller_event_refs",
                    "supervision_event_refs",
                    "receipt_refs",
                ),
            )
        )
    return _unique_refs(refs)


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
    if isinstance(values, Mapping):
        ref = _item_ref(values)
        refs = [ref] if ref else []
        for key in ("refs", "items", "events", "claims", "evidence"):
            refs.extend(_refs_from_value(values.get(key)))
        return _unique_refs(refs)
    if not isinstance(values, list):
        ref = _text(values)
        return [ref] if ref and ":" in ref else []
    refs: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            ref = _item_ref(item)
            if ref:
                refs.append(ref)
            for key in ("refs", "source_refs", "evidence_refs", "review_refs", "display_refs"):
                refs.extend(_refs_from_value(item.get(key)))
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
        "event_ref",
        "provider_ref",
        "executor_ref",
        "context_ref",
        "evidence_ref",
        "review_ref",
        "display_ref",
        "table_ref",
        "figure_ref",
    ):
        ref = _text(item.get(key))
        if ref:
            return ref
    return ""


def _refs_for_keys(*, payloads: list[dict[str, Any]], keys: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        for key in keys:
            refs.extend(_refs_from_value(payload.get(key)))
    return _unique_refs(refs)


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


def _jsonl_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def _jsonl_event_types(paths: tuple[Path, ...]) -> list[str]:
    event_types: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, Mapping):
                continue
            event_type = _text(
                payload.get("event_type")
                or payload.get("type")
                or payload.get("kind")
                or payload.get("event_kind")
            )
            if event_type:
                event_types.append(event_type)
    return _unique_refs(event_types)


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
