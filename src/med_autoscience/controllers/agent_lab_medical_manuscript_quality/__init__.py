from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..agent_lab_aris_followup_assurance import build_aris_followup_assurance_surfaces
from .quality_boundary import (
    AUTHORITY_BOUNDARY,
    CROSS_STAGE_VULNERABILITY_AUDIT,
    OWNER_CHAIN_REGRESSION_FAMILY,
    OWNER_CHAIN_REGRESSION_SUITE_REFS,
    PAPER_STORY_EXCLUSION_POLICY,
    QUALITY_JUDGMENT_BOUNDARY,
    SUITE_RELATIVE_PATH,
    SURFACE_KIND,
)
from .developer_work_order import (
    attach_first_draft_quality_route_back_checklist as _attach_first_draft_quality_route_back_checklist,
    developer_patch_work_order as _developer_patch_work_order,
    target_editable_surface_refs as _target_editable_surface_refs,
)
from .first_draft_route_back import (
    first_draft_quality_route_back_checklist as _first_draft_quality_route_back_checklist,
)
from .route_refs import (
    failure_delta_refs as _failure_delta_refs,
    owner_route_refs as _owner_route_refs,
    quality_floor_refs as _quality_floor_refs,
)
from .refs_json_helpers import (
    analysis_queue_items as _analysis_queue_items,
    existing_refs as _existing_refs,
    first_mapping as _first_mapping,
    first_text as _first_text,
    jsonl_count as _jsonl_count,
    jsonl_event_types as _jsonl_event_types,
    quality_dimension as _quality_dimension,
    read_json_object as _read_json_object,
    refs_for_keys as _refs_for_keys,
    refs_from_value as _refs_from_value,
    runtime_controller_event_refs as _runtime_controller_event_refs,
    text as _text,
    unique_refs as _unique_refs,
)
from .study_quality_targets import (
    study_quality_contract_profile,
    study_quality_target_profile,
)
from .structured_reviewer_evaluation import (
    structured_independent_ai_reviewer_evaluation as _structured_independent_ai_reviewer_evaluation,
)
from .patch_loop_closeout import (
    build_refs_only_patch_loop_closeout_bundle,
)
from ..agent_lab_submission_assurance import build_submission_assurance_surfaces
from ..publication_aftercare import build_publication_aftercare_plan


FEEDBACKOPS_ACCEPTED_PROFILE = "target_agent_feedback_external_suite"
HIGH_QUALITY_MEDICAL_MANUSCRIPT_FEEDBACK_PROFILE = "high_quality_medical_manuscript_feedback"
FEEDBACKOPS_TARGET_AGENT_ID = "med-autoscience"
OPL_EXECUTION_AUTHORIZATION_REFS = [
    "one-person-lab:contracts/stage-run-kernel-contract.json#execution_authorization_policy",
    "runtime-ref:trusted_opl_execution_authorization",
]
PAPER_MISSION_SUBORDINATION = {
    "surface_kind": "mas_paper_mission_subordination",
    "authority_owner": "MedAutoScience",
    "mainline_route": [
        "PaperMission",
        "submission_authority",
        "submission_authority_owner_gate_or_typed_blocker",
    ],
    "control_plane_role": "subordinate_input_or_advisory_only",
    "can_start_parallel_mainline": False,
    "can_bypass_submission_authority": False,
    "can_close_without_owner_gate_or_typed_blocker": False,
}
REVIEWER_REVISION_COVERAGE_AUDIT_REQUIREMENT = {
    "surface_kind": "mas_reviewer_revision_coverage_audit_requirement",
    "required_for_closeout": True,
    "minimum_fields": [
        "feedback_item_id",
        "requested_change",
        "revision_action",
        "status",
        "evidence_refs",
        "remaining_gap_or_not_applicable_reason",
        "owner_readback_ref",
    ],
    "accepted_statuses": ["covered", "not_applicable_with_reason", "blocked_with_owner"],
    "closeout_without_audit_allowed": False,
}
REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT = {
    "surface_kind": "mas_reviewer_revision_stage_attempt_readback_requirement",
    "required_for_closeout": True,
    "must_preserve_professional_skill_invocation_refs": True,
    "professional_skill_ref_families": [
        "medical-manuscript-writing",
        "medical-manuscript-review",
        "medical-statistical-review",
        "medical-table-design",
        "medical-figure-design",
        "medical-submission-prep",
    ],
    "required_observability_fields": ["duration", "token_usage", "cost"],
    "missing_reason_fields": [
        "missing_duration_reason",
        "missing_token_usage_reason",
        "missing_cost_reason",
    ],
    "missing_reason_policy": "typed_missing_reason_required; do_not_coerce_to_zero",
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
    structured_reviewer_evaluation = _structured_independent_ai_reviewer_evaluation(
        study_id=study_id,
        target_agent_id=FEEDBACKOPS_TARGET_AGENT_ID,
        publication_eval=publication_eval,
        publication_eval_ref=str(publication_eval_path),
        evidence_refs=evidence_refs,
        feedback_ref=feedback_ref,
        authority_boundary=AUTHORITY_BOUNDARY,
    )
    blocker_refs = _blocker_refs(prose_status=prose_status, feedback_ref=feedback_ref, study_id=study_id)
    mechanism_inputs = _mechanism_evolution_inputs(
        root=root,
        study_id=study_id,
        publication_eval_path=publication_eval_path,
        task_intake_path=task_intake_path,
        feedback_ref=feedback_ref,
        evidence_refs=evidence_refs,
        blocker_refs=blocker_refs,
        structured_reviewer_evaluation=structured_reviewer_evaluation,
    )
    task_id = f"agent-lab-task:mas/{study_id}/high-quality-medical-manuscript"
    scorecard_ref = f"quality-scorecard:mas/{study_id}/high-quality-medical-manuscript"
    promotion_gate_ref = f"promotion-gate:mas/{study_id}/high-quality-medical-manuscript"
    quality_floor_refs = _quality_floor_refs(study_id=study_id)
    owner_route_refs = _owner_route_refs(study_id=study_id)
    quality_contract = study_quality_contract_profile(study_id=study_id)
    target_editable_surface_refs = _target_editable_surface_refs(study_id=study_id)
    failure_delta_refs = _failure_delta_refs(
        study_id=study_id,
        prose_status=prose_status,
        blocker_refs=blocker_refs,
        feedback_ref=feedback_ref,
    )
    first_draft_route_back_checklist = _first_draft_quality_route_back_checklist(
        study_id=study_id,
        evidence_refs=evidence_refs,
        blocker_refs=blocker_refs,
        feedback_ref=feedback_ref,
    )
    self_evolution_trigger = _feedback_self_evolution_trigger(
        root=root,
        study_id=study_id,
        feedback_ref=feedback_ref,
        suite_path=stable_medical_manuscript_quality_suite_path(study_root=root),
    )
    developer_work_order = _attach_first_draft_quality_route_back_checklist(
        _developer_patch_work_order(
            study_id=study_id,
            evidence_refs=blocker_refs or evidence_refs,
        ),
        checklist=first_draft_route_back_checklist,
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
            quality_contract["scorer_ref"],
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
            "stage_attempt_readback_requirement": dict(
                REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT
            ),
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
            "quality_floor_refs": quality_floor_refs,
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        },
        "improvement_candidate": {
            "candidate_ref": f"improvement-candidate:mas/{study_id}/high-quality-medical-manuscript-rubric-gap",
            "candidate_kind": "rubric_gap",
            "target_ref": "rubric-gap-ref:mas/high-quality-medical-manuscript-ai-reviewer",
            "evidence_refs": blocker_refs or evidence_refs,
            "owner_route_ref": owner_route_refs[0],
            "owner_route_refs": owner_route_refs,
            "developer_patch_work_order": developer_work_order,
            "feedback_self_evolution_trigger": self_evolution_trigger,
            "structured_independent_ai_reviewer_evaluation": structured_reviewer_evaluation,
            "target_agent_capability_gap": {
                "status": "candidate_only",
                "target_owner": "med-autoscience",
                "target_editable_surface_refs": target_editable_surface_refs,
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
            "closeout_acceptance_refs": [
                "reviewer_revision_coverage_audit_ref",
                "stage_attempt_readback_ref",
            ],
            "regression_suite_refs": [
                "regression-suite:mas/ai-first-quality-boundary",
                "regression-suite:mas/paper-authority-clean-migration",
                quality_contract["regression_suite_ref"],
                "regression-suite:mas/hard-methodology-unit-harmonization-route",
                "regression-suite:mas/ai-reviewer-output-readiness-currentness",
                "regression-suite:mas/medical-prose-write-repair-story-surface-delta",
                "regression-suite:mas/owner-route-attempt-protocol",
                "regression-suite:mas/agent-lab-medical-manuscript-self-evolution",
                "regression-suite:mas/agent-lab-research-wiki-reviewer-analysis-queue",
                *OWNER_CHAIN_REGRESSION_SUITE_REFS,
            ],
            "no_forbidden_write_proof_refs": [
                "no-forbidden-write:mas/agent-lab-medical-manuscript-quality"
            ],
            "owner_or_human_gate_refs": owner_route_refs,
            "failure_delta_refs": failure_delta_refs,
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        },
        "closeout_acceptance_requirements": {
            "coverage_audit": dict(REVIEWER_REVISION_COVERAGE_AUDIT_REQUIREMENT),
            "stage_attempt_readback": dict(REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT),
            "structured_independent_ai_reviewer_evaluation": {
                "required_for_oma_improvement": True,
                "minimum_fields": [
                    "critique",
                    "suggestions",
                    "direct_evidence_refs",
                    "provenance",
                ],
            },
        },
    }
    task["patch_loop_closeout_bundle"] = build_refs_only_patch_loop_closeout_bundle(
        root=root,
        study_id=study_id,
        suite_id=f"mas-agent-lab-suite:{study_id}:high-quality-medical-manuscript",
        task_id=task_id,
        promotion_gate_ref=promotion_gate_ref,
        developer_work_order=developer_work_order,
        target_editable_surface_refs=target_editable_surface_refs,
        controller_read_model_feedback_refs=mechanism_inputs["controller_read_model_feedback_refs"],
        forbidden_writes=mechanism_inputs["forbidden_writes"],
    )
    return {
        "suite_id": f"mas-agent-lab-suite:{study_id}:high-quality-medical-manuscript",
        "suite_kind": "agent_lab_external_suite",
        "suite_role": "domain_quality_suite_with_meta_evolution_projection",
        "feedback_self_evolution_trigger": self_evolution_trigger,
        "structured_independent_ai_reviewer_evaluation": structured_reviewer_evaluation,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "tasks": [task],
    }


def _feedback_self_evolution_trigger(
    *,
    root: Path,
    study_id: str,
    feedback_ref: str | None,
    suite_path: Path,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_agent_lab_feedback_self_evolution_trigger",
        "schema_version": 1,
        "feedbackops_event_kind": FEEDBACKOPS_ACCEPTED_PROFILE,
        "accepted_feedback_profile": FEEDBACKOPS_ACCEPTED_PROFILE,
        "feedback_profiles": [
            FEEDBACKOPS_ACCEPTED_PROFILE,
            HIGH_QUALITY_MEDICAL_MANUSCRIPT_FEEDBACK_PROFILE,
        ],
        "target_agent_id": FEEDBACKOPS_TARGET_AGENT_ID,
        "idempotency_key": f"feedbackops:mas/{study_id}/high_quality_medical_manuscript/latest_suite",
        "feedback_capture_requires_execution_authorization": False,
        "repo_fix_execution_requires_opl_execution_authorization": True,
        "opl_execution_authorization_refs": list(OPL_EXECUTION_AUTHORIZATION_REFS),
        "refs_only": True,
        "writes_study_truth": False,
        "status": "runnable_after_suite_materialized",
        "study_id": study_id,
        "feedback_ref": feedback_ref,
        "adapter_role": "domain_thin_feedback_adapter",
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
        "oma_evolution_skill_ref": "opl-meta-agent:oma-agent-evolution",
        "contract_itself_triggers_execution": False,
        "external_suite_path": str(suite_path),
        "external_suite_ref": f"agent-lab-suite:mas/{study_id}/high-quality-medical-manuscript",
        "source_feedback_refs": _existing_refs(
            root / "artifacts" / "controller" / "task_intake" / "latest.json",
            root / "paper" / "review" / "review_ledger.json",
            root / "artifacts" / "publication_eval" / "latest.json",
        ),
        "target_route": {
            "domain_owner": "med-autoscience",
            "agent_lab_owner": "one-person-lab",
            "meta_agent_owner": "opl-meta-agent",
            "target_repo": "med-autoscience",
        },
        "owner_chain": [
            "med-autoscience:reviewer_revision_intake",
            "med-autoscience:agent_lab_medical_manuscript_quality_suite",
            "one-person-lab:feedbackops_agent_lab_projection",
            "opl-meta-agent:oma-agent-evolution",
            "med-autoscience:owner_closeout_readback",
        ],
        "target_action_contracts": {
            "opl_agent_lab": "opl agent-lab run --suite <suite_path> --json",
            "oma_improve": "opl-meta-agent.improve-from-external-agent-lab-suite",
            "opl_work_order_execute": "opl work-order execute",
            "mas_readback": "paper_mission_readback_ref",
        },
        "owner_closeout_readback_refs": [
            "paper_mission_readback_ref",
            "submission_authority_owner_gate_readback_ref",
            "target_owner_receipt_or_typed_blocker_ref",
        ],
        "required_status_refs": [
            "agent_lab_suite_result_ref",
            "structured_ai_reviewer_evaluation_ref",
            "developer_patch_work_order_ref",
            "opl_work_order_status_ref",
            "reviewer_revision_coverage_audit_ref",
            "stage_attempt_readback_ref",
            "target_owner_receipt_or_typed_blocker_ref",
        ],
        "closeout_acceptance_requirements": {
            "coverage_audit": dict(REVIEWER_REVISION_COVERAGE_AUDIT_REQUIREMENT),
            "stage_attempt_readback": dict(REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT),
        },
        "opl_app_status_projection": {
            "should_register_stage_run": True,
            "status_surface_kind": "opl_agent_lab_domain_feedback_self_evolution_status",
            "queued_status": "queued_for_agent_lab_external_suite",
            "running_status": "running_oma_or_opl_work_order",
            "terminal_statuses": [
                "completed_with_owner_receipt",
                "completed_with_typed_blocker",
                "blocked_requires_human_or_owner_gate",
            ],
        },
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
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
    if prose_status != "ready" or feedback_ref is not None:
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
    structured_reviewer_evaluation: dict[str, Any],
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
    first_draft_route_back_checklist = _first_draft_quality_route_back_checklist(
        study_id=study_id,
        evidence_refs=evidence_refs,
        blocker_refs=blocker_refs,
        feedback_ref=feedback_ref,
    )
    developer_patch_work_order = _attach_first_draft_quality_route_back_checklist(
        _developer_patch_work_order(
            study_id=study_id,
            evidence_refs=_unique_refs(
                [*(blocker_refs or evidence_refs), *controller_read_model_feedback_refs]
            ),
        ),
        checklist=first_draft_route_back_checklist,
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
        "structured_independent_ai_reviewer_evaluation": structured_reviewer_evaluation,
        "structured_ai_reviewer_evaluation_ref": structured_reviewer_evaluation[
            "evaluation_ref"
        ],
        "analysis_queue_manifest_refs": analysis_queue_manifest_refs,
        "analysis_queue_manifest": analysis_queue_manifest,
        "runtime_event_ledger": runtime_event_ledger,
        "provider_switch_hygiene": provider_switch_hygiene,
        "claim_assurance_map": claim_assurance_map,
        "owner_chain_regression_family": dict(OWNER_CHAIN_REGRESSION_FAMILY),
        "first_draft_quality_route_back_checklist": first_draft_route_back_checklist,
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
        "target_editable_surface_refs": _target_editable_surface_refs(study_id=study_id),
        "developer_patch_work_order": developer_patch_work_order,
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


def _controller_read_model_feedback_refs(*, root: Path, study_id: str) -> list[str]:
    refs = _existing_refs(
        root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
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


__all__ = [
    "build_medical_manuscript_quality_agent_lab_suite",
    "materialize_medical_manuscript_quality_agent_lab_suite",
    "stable_medical_manuscript_quality_suite_path",
]
