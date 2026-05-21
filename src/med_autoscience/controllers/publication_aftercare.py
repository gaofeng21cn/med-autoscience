from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .domain_dispatch_evidence_payload import build_domain_dispatch_evidence_record_payload


SURFACE_KIND = "mas_publication_aftercare_plan"
ANALYSIS_QUEUE_TASK_KIND = "publication_aftercare/analysis-queue-progress"
REVIEWER_REFRESH_TASK_KIND = "publication_aftercare/reviewer-refresh"
FORBIDDEN_WRITES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/submission_minimal/",
    "manuscript/current_package/",
    "manuscript/current_package.zip",
    "submission_package/",
    "current_package/",
    "current_package.zip",
)
AUTHORITY_BOUNDARY = {
    "surface_owner": "med-autoscience",
    "surface_role": "publication_aftercare_refs_only_owner_route_control",
    "can_submit_to_venue": False,
    "can_push_shared_resource": False,
    "can_modify_current_package": False,
    "can_modify_submission_package": False,
    "can_modify_study_truth": False,
    "can_authorize_publication_readiness": False,
    "can_authorize_quality_verdict": False,
    "can_store_overleaf_token": False,
    "can_bypass_quality_gate": False,
    "can_start_runtime_owner_progression": False,
    "can_emit_owner_route_task_refs": True,
    "allowed_outputs": ["plan", "refs", "task_template", "blockers"],
    "forbidden_writes": list(FORBIDDEN_WRITES),
}
RESUBMISSION_CONSTRAINTS = {
    "text_only": True,
    "no_new_experiments": True,
    "no_bib_edits": True,
    "never_overwrite": True,
    "requires_human_target_confirmation": True,
    "target_whitelist_required": True,
}
RESUBMISSION_HARD_LEDGER = {
    "ledger_kind": "resubmit_route_hard_ledger",
    "text_only": True,
    "no_new_experiment": True,
    "no_bib_edits": True,
    "no_overwrite": True,
    "target_whitelist_required": True,
    "body_included": False,
}
OWNER_ROUTE_TASK_POLICY = {
    "progression_owner": "med-autoscience-runtime-owner-chain",
    "dispatch_boundary": "sidecar_or_cli_receipt_only",
    "dispatch_authority": "forbidden_mas_emits_refs_or_typed_blockers_only",
    "requires_owner_route_or_supervisor_dispatch": True,
    "requires_owner_receipt_or_typed_blocker": True,
    "quality_gate_bypass_allowed": False,
    "direct_publication_eval_write_allowed": False,
    "direct_controller_decision_write_allowed": False,
    "direct_current_package_write_allowed": False,
    "direct_submission_package_write_allowed": False,
    "forbidden_writes": list(FORBIDDEN_WRITES),
}
REVIEWER_REFRESH_POLICY = {
    "independent_reviewer_agent_required": True,
    "separate_invocation_required": True,
    "separate_context_record_required": True,
    "self_review_closes_quality_gate": False,
    "result_authority": "ai_reviewer_workflow_materialized_publication_eval_only",
    "entry_can_authorize_quality_verdict": False,
}
ARIS_HANDOFF_FILES = (
    "input_contract.json",
    "algorithm_scout_report.md",
    "innovation_hypotheses.md",
    "final_method_proposal.md",
    "experiment_plan.md",
    "experiment_results_summary.md",
    "review_loop_summary.md",
    "prior_limitations.md",
    "why_our_method_can_work.md",
    "claim_to_evidence_map.md",
    "sidecar_manifest.json",
)


def build_publication_aftercare_plan(
    *,
    study_root: Path,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve() if quest_root is not None else None
    study_id = root.name
    input_refs = _input_refs(root, quest_root=resolved_quest_root)
    resubmission_plan = _resubmission_plan(root=root, study_id=study_id)
    talk_package_plan = _talk_package_plan(root=root, study_id=study_id)
    overleaf_sync_plan = _overleaf_sync_plan(root=root, study_id=study_id)
    analysis_queue_entry = _analysis_queue_entry(
        root=root,
        quest_root=resolved_quest_root,
        study_id=study_id,
    )
    reviewer_refresh_entry = _reviewer_refresh_entry(
        root=root,
        quest_root=resolved_quest_root,
        study_id=study_id,
    )
    blockers = _unique_refs(
        [
            *resubmission_plan["blockers"],
            *talk_package_plan["blockers"],
            *overleaf_sync_plan["blockers"],
            *analysis_queue_entry["blockers"],
            *reviewer_refresh_entry["blockers"],
        ]
    )
    publication_aftercare_plan_refs = _unique_refs(
        [
            f"publication-aftercare-plan:mas/{study_id}",
            *_existing_refs(root / "artifacts" / "publication_aftercare" / "latest.json"),
        ]
    )
    evidence_delta_refs = _unique_refs(
        [
            *publication_aftercare_plan_refs,
            *input_refs,
            *resubmission_plan["target_venue_refs"],
            *resubmission_plan["review_corpus_refs"],
            *talk_package_plan["paper_refs"],
            *talk_package_plan["slide_deck_refs"],
            *talk_package_plan["talk_script_refs"],
            *talk_package_plan["package_refs"],
            *talk_package_plan["claim_assurance_refs"],
            *talk_package_plan["citation_assurance_refs"],
            *talk_package_plan["kill_argument_refs"],
            *talk_package_plan["anonymity_assurance_refs"],
            *overleaf_sync_plan["project_refs"],
            *overleaf_sync_plan["status_refs"],
            *overleaf_sync_plan["pull_refs"],
            *overleaf_sync_plan["push_refs"],
            *overleaf_sync_plan["check_refs"],
            *analysis_queue_entry["evidence_delta_refs"],
            *reviewer_refresh_entry["evidence_delta_refs"],
        ]
    )
    return {
        "surface_kind": SURFACE_KIND,
        "plan_kind": "body_free_publication_aftercare_refs",
        "study_id": study_id,
        "study_root_ref": str(root),
        "quest_root_ref": str(resolved_quest_root) if resolved_quest_root is not None else None,
        "status": "ready" if not blockers else "blocked",
        "refs_only": True,
        "body_included": False,
        "machine_readable": True,
        "publication_aftercare_plan_refs": publication_aftercare_plan_refs,
        "resubmission_plan_refs": resubmission_plan["review_corpus_refs"],
        "venue_route_refs": resubmission_plan["target_venue_refs"],
        "resubmit_hard_ledger_refs": resubmission_plan["hard_ledger_refs"],
        "target_whitelist_refs": resubmission_plan["target_whitelist_refs"],
        "paper_talk_refs": talk_package_plan["paper_talk_refs"],
        "talk_package_refs": talk_package_plan["package_refs"],
        "slides_polish_refs": talk_package_plan["slide_deck_refs"],
        "overleaf_sync_refs": overleaf_sync_plan["status_refs"] + overleaf_sync_plan["check_refs"],
        "citation_audit_refs": talk_package_plan["citation_assurance_refs"],
        "kill_argument_refs": talk_package_plan["kill_argument_refs"],
        "aftercare_readiness_inputs": {
            "citation_audit_refs": talk_package_plan["citation_assurance_refs"],
            "kill_argument_refs": talk_package_plan["kill_argument_refs"],
            "body_included": False,
        },
        "author_handoff_refs": _author_handoff_refs(root),
        "external_suite_task_refs": analysis_queue_entry["evidence_delta_refs"],
        "input_refs": input_refs,
        "evidence_delta_refs": evidence_delta_refs,
        "resubmission_plan": resubmission_plan,
        "talk_package_plan": talk_package_plan,
        "overleaf_sync_plan": overleaf_sync_plan,
        "analysis_queue_entry": analysis_queue_entry,
        "reviewer_refresh_entry": reviewer_refresh_entry,
        "owner_route_task_policy": dict(OWNER_ROUTE_TASK_POLICY),
        "can_push_submission": False,
        "can_authorize_submission_action": False,
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "blockers": blockers,
    }


def build_publication_aftercare_pending_tasks(
    *,
    profile_name: str,
    profile_ref: str | Path,
    study_id: str,
    projection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    analysis = _mapping(projection.get("analysis_queue_entry"))
    reviewer = _mapping(projection.get("reviewer_refresh_entry"))
    if analysis.get("eligible_for_owner_route_task_ref") is True:
        tasks.append(
            _pending_task(
                profile_name=profile_name,
                profile_ref=profile_ref,
                study_id=study_id,
                task_kind=ANALYSIS_QUEUE_TASK_KIND,
                priority=45,
                reason="analysis_queue_owner_route_ref",
                entry=analysis,
            )
        )
    if reviewer.get("eligible_for_owner_route_task_ref") is True:
        tasks.append(
            _pending_task(
                profile_name=profile_name,
                profile_ref=profile_ref,
                study_id=study_id,
                task_kind=REVIEWER_REFRESH_TASK_KIND,
                priority=44,
                reason="reviewer_refresh_owner_route_ref",
                entry=reviewer,
            )
        )
    return tasks


def _pending_task(
    *,
    profile_name: str,
    profile_ref: str | Path,
    study_id: str,
    task_kind: str,
    priority: int,
    reason: str,
    entry: Mapping[str, Any],
) -> dict[str, Any]:
    source_fingerprint = _text(entry.get("source_fingerprint")) or _fingerprint(
        {"study_id": study_id, "task_kind": task_kind, "refs": entry.get("evidence_delta_refs")}
    )
    dedupe_key = f"mas:{profile_name}:{study_id}:publication-aftercare:{task_kind}:{source_fingerprint}"
    source_refs = _source_refs_from_entry(entry)
    return {
        "domain_id": "medautoscience",
        "task_kind": task_kind,
        "priority": priority,
        "source": "mas-publication-aftercare",
        "requires_approval": False,
        "dedupe_key": dedupe_key,
        "source_fingerprint": source_fingerprint,
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "idempotency_key": dedupe_key,
            "publication_aftercare_reason": reason,
            "authority_boundary": "mas_owner_route_task_ref_only",
        },
        "source_refs": source_refs,
        "domain_dispatch_evidence_record_payload": build_domain_dispatch_evidence_record_payload(
            task_kind=task_kind,
            study_id=study_id,
            reason=reason,
            evidence_refs=source_refs,
            source_fingerprint=source_fingerprint,
        ),
        "dispatch_owner": "med-autoscience",
        "profile_name": profile_name,
    }


def _resubmission_plan(*, root: Path, study_id: str) -> dict[str, Any]:
    target_paths = (
        root / "artifacts" / "submission_targets" / "latest.json",
        root / "artifacts" / "journal_shortlist" / "latest.json",
        root / "artifacts" / "journal_package" / "latest.json",
        root / "artifacts" / "resubmission" / "latest.json",
        root / "artifacts" / "publication_aftercare" / "resubmit_route_hard_ledger.json",
        root / "paper" / "target_journal_writing_layer.json",
        root / "paper" / "resubmission_plan.json",
    )
    review_paths = (
        root / "paper" / "review" / "review_ledger.json",
        root / "artifacts" / "review_corpus" / "latest.json",
        root / "artifacts" / "publication_eval" / "latest.json",
        root / "artifacts" / "ai_reviewer" / "latest.json",
        root / "paper" / "reviewer_response.md",
        root / "paper" / "reviews.md",
    )
    target_venue_value_refs = _json_refs(
        target_paths,
        keys=(
            "target_venue_ref",
            "target_venue_refs",
            "venue_ref",
            "venue_refs",
            "journal_ref",
            "journal_refs",
            "target_journal_ref",
            "target_journal_refs",
            "journal_slug",
            "journal_slugs",
            "publication_profile_ref",
        ),
    )
    target_venue_refs = _unique_refs([*_existing_refs(*target_paths), *target_venue_value_refs])
    target_whitelist_refs = _unique_refs(
        [
            *_json_refs(
                target_paths,
                keys=(
                    "target_whitelist_ref",
                    "target_whitelist_refs",
                    "target_whitelist",
                    "allowed_target_ref",
                    "allowed_target_refs",
                    "allowed_journal_ref",
                    "allowed_journal_refs",
                    "whitelisted_target_refs",
                    "whitelisted_journal_refs",
                ),
            ),
        ]
    )
    hard_ledger_refs = _unique_refs(
        [
            *_existing_refs(root / "artifacts" / "publication_aftercare" / "resubmit_route_hard_ledger.json"),
            *_json_refs(
                target_paths,
                keys=("hard_ledger_ref", "hard_ledger_refs", "resubmit_route_hard_ledger_ref"),
            ),
        ]
    )
    review_corpus_refs = _unique_refs(
        [
            *_existing_refs(*review_paths),
            *_json_refs(
                review_paths,
                keys=(
                    "review_ref",
                    "review_refs",
                    "reviewer_ref",
                    "reviewer_refs",
                    "review_corpus_ref",
                    "review_corpus_refs",
                    "corpus_ref",
                    "corpus_refs",
                    "review_items",
                    "review_ledger_refs",
                ),
            ),
        ]
    )
    blockers: list[str] = []
    if not target_venue_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/target-venue-ref-missing")
    if not target_whitelist_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/target-whitelist-ref-missing")
    target_venue_ref = target_venue_value_refs[0] if target_venue_value_refs else None
    if target_venue_ref and target_whitelist_refs and target_venue_ref not in target_whitelist_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/target-not-whitelisted")
    if not review_corpus_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/review-corpus-ref-missing")
    return {
        "surface_kind": "mas_resubmission_aftercare_plan",
        "status": "ready" if not blockers else "blocked",
        "target_venue_ref": target_venue_ref,
        "target_venue_refs": target_venue_refs,
        "target_whitelist_refs": target_whitelist_refs,
        "hard_ledger_refs": hard_ledger_refs,
        "hard_ledger": {
            **dict(RESUBMISSION_HARD_LEDGER),
            "target_venue_ref": target_venue_ref,
            "target_whitelisted": bool(target_venue_ref and target_venue_ref in target_whitelist_refs),
        },
        "review_corpus_refs": review_corpus_refs,
        "constraints": dict(RESUBMISSION_CONSTRAINTS),
        "assurance_level": "strict_text_only_resubmission_planning",
        "body_included": False,
        "can_submit_to_venue": False,
        "can_write_current_package": False,
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "blockers": blockers,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _talk_package_plan(*, root: Path, study_id: str) -> dict[str, Any]:
    paper_paths = (
        root / "paper" / "draft.md",
        root / "paper" / "manuscript.md",
        root / "paper" / "paper.pdf",
        root / "manuscript" / "current_package",
        root / "artifacts" / "publication_eval" / "latest.json",
    )
    talk_paths = (
        root / "artifacts" / "talk_package" / "latest.json",
        root / "artifacts" / "paper_talk" / "latest.json",
        root / "artifacts" / "slides_polish" / "latest.json",
        root / "talk" / "package_manifest.json",
        root / "talk" / "slides.pptx",
        root / "talk" / "deck.pptx",
        root / "slides" / "deck.pptx",
        root / "talk" / "script.md",
        root / "talk" / "talk_script.md",
    )
    assurance_paths = (
        root / "paper" / "claim_evidence_map.json",
        root / "paper" / "citation_audit.json",
        root / "paper" / "anonymity_check.json",
        root / "artifacts" / "claim_assurance" / "latest.json",
        root / "artifacts" / "citation_audit" / "latest.json",
        root / "artifacts" / "kill_argument" / "latest.json",
        root / "artifacts" / "kill_argument_refs" / "latest.json",
        root / "artifacts" / "anonymity_check" / "latest.json",
        root / "artifacts" / "publication_eval" / "latest.json",
        root / "paper" / "kill_argument_refs.json",
    )
    talk_json_paths = tuple(path for path in talk_paths if path.suffix == ".json")
    assurance_json_paths = tuple(path for path in assurance_paths if path.suffix == ".json")
    paper_refs = _unique_refs(
        [
            *_existing_refs(*paper_paths),
            *_json_refs(
                assurance_json_paths,
                keys=("paper_ref", "paper_refs", "manuscript_ref", "manuscript_refs"),
            ),
        ]
    )
    slide_deck_refs = _unique_refs(
        [
            *_existing_refs(root / "talk" / "slides.pptx", root / "talk" / "deck.pptx", root / "slides" / "deck.pptx"),
            *_existing_refs(root / "artifacts" / "slides_polish" / "latest.json"),
            *_json_refs(talk_json_paths, keys=("slide_ref", "slide_refs", "deck_ref", "deck_refs")),
        ]
    )
    talk_script_refs = _unique_refs(
        [
            *_existing_refs(root / "talk" / "script.md", root / "talk" / "talk_script.md"),
            *_json_refs(talk_json_paths, keys=("talk_script_ref", "talk_script_refs", "script_ref", "script_refs")),
        ]
    )
    package_refs = _unique_refs(
        [
            *_existing_refs(
                root / "artifacts" / "talk_package" / "latest.json",
                root / "artifacts" / "paper_talk" / "latest.json",
                root / "talk" / "package_manifest.json",
            ),
            *_json_refs(talk_json_paths, keys=("package_ref", "package_refs", "talk_package_ref", "talk_package_refs")),
        ]
    )
    paper_talk_refs = _unique_refs(
        [
            *_json_refs(talk_json_paths, keys=("paper_talk_ref", "paper_talk_refs")),
        ]
    )
    claim_assurance_refs = _unique_refs(
        [
            *_existing_refs(root / "paper" / "claim_evidence_map.json", root / "artifacts" / "claim_assurance" / "latest.json"),
            *_json_refs(
                assurance_json_paths,
                keys=("claim_ref", "claim_refs", "claim_assurance_ref", "claim_assurance_refs"),
            ),
        ]
    )
    citation_assurance_refs = _unique_refs(
        [
            *_existing_refs(root / "paper" / "citation_audit.json", root / "artifacts" / "citation_audit" / "latest.json"),
            *_json_refs(
                assurance_json_paths,
                keys=("citation_ref", "citation_refs", "citation_assurance_ref", "citation_assurance_refs"),
            ),
        ]
    )
    kill_argument_refs = _unique_refs(
        [
            *_existing_refs(
                root / "paper" / "kill_argument_refs.json",
                root / "artifacts" / "kill_argument" / "latest.json",
                root / "artifacts" / "kill_argument_refs" / "latest.json",
            ),
            *_json_refs(
                assurance_json_paths,
                keys=("kill_argument_ref", "kill_argument_refs", "weak_argument_ref", "weak_argument_refs"),
            ),
        ]
    )
    anonymity_assurance_refs = _unique_refs(
        [
            *_existing_refs(root / "paper" / "anonymity_check.json", root / "artifacts" / "anonymity_check" / "latest.json"),
            *_json_refs(
                assurance_json_paths,
                keys=("anonymity_ref", "anonymity_refs", "anonymity_assurance_ref", "anonymity_assurance_refs"),
            ),
        ]
    )
    blockers: list[str] = []
    if not paper_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/talk-paper-ref-missing")
    if not (slide_deck_refs or talk_script_refs or package_refs):
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/talk-package-ref-missing")
    if not claim_assurance_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/claim-assurance-ref-missing")
    if not citation_assurance_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/citation-assurance-ref-missing")
    if not kill_argument_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/kill-argument-ref-missing")
    if not anonymity_assurance_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/anonymity-assurance-ref-missing")
    return {
        "surface_kind": "mas_talk_package_aftercare_plan",
        "status": "ready" if not blockers else "blocked",
        "paper_refs": paper_refs,
        "slide_deck_refs": slide_deck_refs,
        "talk_script_refs": talk_script_refs,
        "package_refs": package_refs,
        "paper_talk_refs": paper_talk_refs,
        "claim_assurance_refs": claim_assurance_refs,
        "citation_assurance_refs": citation_assurance_refs,
        "kill_argument_refs": kill_argument_refs,
        "anonymity_assurance_refs": anonymity_assurance_refs,
        "refs_only_maturity": {
            "paper_talk_ready": bool(paper_talk_refs),
            "slides_polish_ready": bool(slide_deck_refs),
            "citation_audit_ready": bool(citation_assurance_refs),
            "kill_argument_refs_ready": bool(kill_argument_refs),
            "body_included": False,
        },
        "content_grounding_policy": {
            "policy_ref": "policy:mas/publication-aftercare/talk-content-grounding",
            "claims_must_resolve_to_claim_assurance_refs": True,
            "citations_must_resolve_to_citation_assurance_refs": True,
            "kill_arguments_must_resolve_to_kill_argument_refs": True,
            "anonymity_must_resolve_to_anonymity_assurance_refs": True,
            "body_included": False,
        },
        "body_included": False,
        "can_generate_or_push_deck": False,
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "blockers": blockers,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _overleaf_sync_plan(*, root: Path, study_id: str) -> dict[str, Any]:
    overleaf_paths = (
        root / "artifacts" / "overleaf" / "latest.json",
        root / "artifacts" / "overleaf" / "status.json",
        root / "artifacts" / "overleaf" / "check.json",
        root / "paper" / "overleaf_sync.json",
        root / ".overleaf" / "status.json",
    )
    project_refs = _json_refs(
        overleaf_paths,
        keys=("project_ref", "project_refs", "overleaf_project_ref", "overleaf_project_refs", "project_id"),
    )
    status_refs = _unique_refs(
        [
            *_existing_refs(
                root / "artifacts" / "overleaf" / "latest.json",
                root / "artifacts" / "overleaf" / "status.json",
                root / ".overleaf" / "status.json",
            ),
            *_json_refs(overleaf_paths, keys=("status_ref", "status_refs", "sync_status_ref", "sync_status_refs")),
        ]
    )
    pull_refs = _json_refs(overleaf_paths, keys=("pull_ref", "pull_refs", "last_pull_ref", "last_pull_refs"))
    push_refs = _json_refs(overleaf_paths, keys=("push_ref", "push_refs", "last_push_ref", "last_push_refs"))
    check_refs = _unique_refs(
        [
            *_existing_refs(root / "artifacts" / "overleaf" / "check.json"),
            *_json_refs(overleaf_paths, keys=("check_ref", "check_refs", "preflight_check_ref", "preflight_check_refs")),
        ]
    )
    token_key_present = any(_contains_token_key(_read_json_object(path)) for path in overleaf_paths)
    blockers: list[str] = []
    if not project_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/overleaf-project-ref-missing")
    if not (status_refs or check_refs):
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/overleaf-status-or-check-ref-missing")
    if token_key_present:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/overleaf-token-key-present")
    return {
        "surface_kind": "mas_overleaf_sync_aftercare_plan",
        "status": "ready" if not blockers else "blocked",
        "project_refs": _unique_refs(project_refs),
        "status_refs": status_refs,
        "pull_refs": _unique_refs(pull_refs),
        "push_refs": _unique_refs(push_refs),
        "check_refs": check_refs,
        "token_policy": {
            "token_never_stored": True,
            "token_sources_allowed": ["operator_runtime_secret_store"],
            "repo_or_study_token_storage_allowed": False,
        },
        "token_storage_status": "blocked_token_key_present" if token_key_present else "clean_no_token_keys_seen",
        "requires_human_confirmation_for_shared_push": True,
        "shared_push_status": "blocked_requires_human_confirmation",
        "refs_only_maturity": {
            "project_ref_ready": bool(project_refs),
            "status_or_check_ref_ready": bool(status_refs or check_refs),
            "pull_ref_seen": bool(pull_refs),
            "push_ref_seen": bool(push_refs),
            "token_storage_clean": not token_key_present,
            "body_included": False,
        },
        "body_included": False,
        "can_pull": False,
        "can_push_shared_resource": False,
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "blockers": blockers,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _analysis_queue_entry(*, root: Path, quest_root: Path | None, study_id: str) -> dict[str, Any]:
    queue_paths = _candidate_paths(
        root,
        quest_root=quest_root,
        relatives=(
            Path("artifacts/analysis_queue/latest.json"),
            Path("artifacts/analysis_campaign/queue_manifest.json"),
            Path("artifacts/analysis_campaign/latest_manifest.json"),
            Path("paper/analysis_queue.json"),
        ),
    )
    aris_paths = _aris_artifact_paths(root=root, quest_root=quest_root)
    research_pipeline_refs = _existing_refs(
        *[
            path
            for path in aris_paths
            if path.name
            in {
                "input_contract.json",
                "algorithm_scout_report.md",
                "innovation_hypotheses.md",
                "final_method_proposal.md",
                "prior_limitations.md",
                "why_our_method_can_work.md",
                "sidecar_manifest.json",
            }
        ]
    )
    auto_review_loop_refs = _unique_refs(
        [
            *_existing_refs(
                *[
                    path
                    for path in aris_paths
                    if path.name in {"review_loop_summary.md", "claim_to_evidence_map.md"}
                ],
                *_candidate_paths(
                    root,
                    quest_root=quest_root,
                    relatives=(
                        Path("paper/review/review_ledger.json"),
                        Path("artifacts/publication_eval/latest.json"),
                        Path("artifacts/publication_eval/medical_prose_review.json"),
                        Path("artifacts/ai_reviewer/latest.json"),
                    ),
                ),
            ),
            *_json_refs(tuple(queue_paths), keys=("review_ref", "review_refs", "reviewer_refs")),
        ]
    )
    experiment_queue_refs = _unique_refs(
        [
            *_existing_refs(
                *queue_paths,
                *[
                    path
                    for path in aris_paths
                    if path.name in {"experiment_plan.md", "experiment_results_summary.md"}
                ],
            ),
            *_json_refs(
                tuple(queue_paths),
                keys=(
                    "queue_ref",
                    "manifest_ref",
                    "item_ref",
                    "item_refs",
                    "experiment_ref",
                    "experiment_refs",
                    "source_refs",
                ),
            ),
        ]
    )
    blockers: list[str] = []
    if not research_pipeline_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/aris-research-pipeline-ref-missing")
    if not auto_review_loop_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/auto-review-loop-ref-missing")
    if not experiment_queue_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/experiment-queue-ref-missing")
    evidence_delta_refs = _unique_refs([*research_pipeline_refs, *auto_review_loop_refs, *experiment_queue_refs])
    source_fingerprint = _fingerprint(
        {
            "study_id": study_id,
            "entry": "analysis_queue",
            "refs": evidence_delta_refs,
            "blockers": blockers,
        }
    )
    return {
        "surface_kind": "mas_publication_aftercare_analysis_queue_entry",
        "entry_kind": "aris_research_pipeline_auto_review_experiment_queue_refs",
        "status": "ready" if not blockers else "blocked",
        "eligible_for_owner_route_task_ref": not blockers,
        "recommended_task_kind": ANALYSIS_QUEUE_TASK_KIND if not blockers else None,
        "recommended_domain_owner": "med-autoscience",
        "source_fingerprint": source_fingerprint,
        "research_pipeline_refs": research_pipeline_refs,
        "auto_review_loop_refs": auto_review_loop_refs,
        "experiment_queue_refs": experiment_queue_refs,
        "evidence_delta_refs": evidence_delta_refs,
        "body_included": False,
        "owner_route_task_policy": dict(OWNER_ROUTE_TASK_POLICY),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "blockers": blockers,
    }


def _reviewer_refresh_entry(*, root: Path, quest_root: Path | None, study_id: str) -> dict[str, Any]:
    refresh_paths = _candidate_paths(
        root,
        quest_root=quest_root,
        relatives=(
            Path("artifacts/publication_eval/latest.json"),
            Path("artifacts/publication_eval/medical_prose_review.json"),
            Path("artifacts/ai_reviewer/latest.json"),
            Path("artifacts/supervision/requests/ai_reviewer/latest.json"),
            Path("paper/review/review_ledger.json"),
            Path("paper/claim_evidence_map.json"),
            Path("paper/manuscript.md"),
            Path("paper/draft.md"),
        ),
    )
    aris_review_refs = _existing_refs(
        *[
            path
            for path in _aris_artifact_paths(root=root, quest_root=quest_root)
            if path.name in {"review_loop_summary.md", "claim_to_evidence_map.md"}
        ]
    )
    publication_eval_refs = _existing_refs(
        *_candidate_paths(
            root,
            quest_root=quest_root,
            relatives=(Path("artifacts/publication_eval/latest.json"),),
        )
    )
    reviewer_input_refs = _unique_refs(
        [
            *_existing_refs(*refresh_paths),
            *aris_review_refs,
            *_json_refs(
                tuple(refresh_paths),
                keys=(
                    "review_ref",
                    "review_refs",
                    "reviewer_ref",
                    "reviewer_refs",
                    "reviewer_feedback_refs",
                    "ai_reviewer_record_ref",
                    "publication_eval_record_ref",
                    "source_refs",
                ),
            ),
        ]
    )
    blockers: list[str] = []
    if not publication_eval_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/publication-eval-ref-missing")
    if not reviewer_input_refs:
        blockers.append(f"blocker:mas/{study_id}/publication-aftercare/reviewer-refresh-input-ref-missing")
    evidence_delta_refs = _unique_refs([*publication_eval_refs, *reviewer_input_refs])
    source_fingerprint = _fingerprint(
        {
            "study_id": study_id,
            "entry": "reviewer_refresh",
            "refs": evidence_delta_refs,
            "blockers": blockers,
        }
    )
    return {
        "surface_kind": "mas_publication_aftercare_reviewer_refresh_entry",
        "entry_kind": "ai_reviewer_refresh_owner_route_refs",
        "status": "ready" if not blockers else "blocked",
        "eligible_for_owner_route_task_ref": not blockers,
        "recommended_task_kind": REVIEWER_REFRESH_TASK_KIND if not blockers else None,
        "recommended_domain_owner": "med-autoscience",
        "source_fingerprint": source_fingerprint,
        "publication_eval_refs": publication_eval_refs,
        "reviewer_input_refs": reviewer_input_refs,
        "evidence_delta_refs": evidence_delta_refs,
        "body_included": False,
        "reviewer_refresh_policy": dict(REVIEWER_REFRESH_POLICY),
        "owner_route_task_policy": dict(OWNER_ROUTE_TASK_POLICY),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "blockers": blockers,
    }


def _input_refs(root: Path, *, quest_root: Path | None = None) -> list[str]:
    return _existing_refs(
        *_candidate_paths(
            root,
            quest_root=quest_root,
            relatives=(
                Path("artifacts/publication_eval/latest.json"),
                Path("paper/review/review_ledger.json"),
                Path("paper/claim_evidence_map.json"),
                Path("artifacts/submission_targets/latest.json"),
                Path("artifacts/journal_shortlist/latest.json"),
                Path("artifacts/talk_package/latest.json"),
                Path("artifacts/paper_talk/latest.json"),
                Path("artifacts/slides_polish/latest.json"),
                Path("artifacts/overleaf/latest.json"),
                Path("artifacts/overleaf/status.json"),
                Path("artifacts/overleaf/check.json"),
                Path("artifacts/analysis_queue/latest.json"),
                Path("artifacts/analysis_campaign/queue_manifest.json"),
                Path("paper/overleaf_sync.json"),
            ),
        ),
        *_aris_artifact_paths(root=root, quest_root=quest_root),
    )


def _author_handoff_refs(root: Path) -> list[str]:
    return _existing_refs(
        root / "artifacts" / "author_handoff" / "latest.json",
        root / "artifacts" / "publication_aftercare" / "author_handoff.json",
        root / "handoff" / "publication_aftercare.md",
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".json":
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _existing_refs(*paths: Path) -> list[str]:
    return _unique_refs([str(path) for path in paths if path.exists()])


def _json_refs(paths: tuple[Path, ...], *, keys: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    key_set = set(keys)
    for path in paths:
        refs.extend(_collect_refs(_read_json_object(path), key_set=key_set))
    return _unique_refs(refs)


def _collect_refs(value: Any, *, key_set: set[str]) -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in key_set:
                refs.extend(_coerce_ref_values(child))
            refs.extend(_collect_refs(child, key_set=key_set))
    elif isinstance(value, list):
        for item in value:
            refs.extend(_collect_refs(item, key_set=key_set))
    return refs


def _coerce_ref_values(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_coerce_ref_values(item))
        return refs
    if isinstance(value, Mapping):
        refs: list[str] = []
        for key in ("ref", "id", "claim_ref", "evidence_ref", "review_ref", "path", "slug"):
            refs.extend(_coerce_ref_values(value.get(key)))
        return refs
    return []


def _contains_token_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if "token" in str(key).lower():
                return True
            if _contains_token_key(child):
                return True
    if isinstance(value, list):
        return any(_contains_token_key(item) for item in value)
    return False


def _candidate_paths(root: Path, *, quest_root: Path | None, relatives: tuple[Path, ...]) -> list[Path]:
    roots = [root]
    if quest_root is not None and quest_root != root:
        roots.append(quest_root)
    return [base / relative for base in roots for relative in relatives]


def _aris_artifact_paths(*, root: Path, quest_root: Path | None) -> list[Path]:
    bases = _candidate_paths(
        root,
        quest_root=quest_root,
        relatives=(
            Path("artifacts/algorithm_research/aris"),
            Path("sidecars/aris/handoff"),
        ),
    )
    return [base / name for base in bases for name in ARIS_HANDOFF_FILES]


def _source_refs_from_entry(entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for role, key in (
        ("aris_research_pipeline", "research_pipeline_refs"),
        ("auto_review_loop", "auto_review_loop_refs"),
        ("experiment_queue", "experiment_queue_refs"),
        ("publication_eval", "publication_eval_refs"),
        ("reviewer_refresh_input", "reviewer_input_refs"),
    ):
        for ref in entry.get(key) or []:
            text = _text(ref)
            if text is None:
                continue
            refs.append({"role": role, "ref": text, "exists": True, "body_included": False})
    return refs


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _fingerprint(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _unique_refs(refs: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for ref in refs:
        text = str(ref).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique
