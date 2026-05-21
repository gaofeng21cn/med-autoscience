from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile


def owner_route_handoff_task(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    record = _mapping(study.get("owner_route_handoff"))
    handoff = _mapping(record.get("handoff"))
    if _text(handoff.get("recommended_task_kind")) != "domain_route/reconcile-apply":
        return None
    reason = _text(handoff.get("reason")) or _text(record.get("source")) or "owner_route_handoff"
    study_root = Path(_text(study.get("study_root")) or profile.studies_root / study_id)
    owner_route_handoff_ref = _workspace_relative(
        study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json",
        workspace_root=profile.workspace_root,
    )
    route_transition_contract = _route_transition_contract(handoff=handoff)
    stage_graph_handoff = _stage_graph_handoff()
    return {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/reconcile-apply",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "priority": 55,
        "source": "mas-sidecar-export",
        "requires_approval": False,
        "dedupe_key": f"mas:{profile.name}:{study_id}:owner-route-handoff:{reason}",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "reason": reason,
        "runtime_state_path": _text(handoff.get("runtime_state_path")),
        "owner_route_refs": ["mas_runtime_owner_route_handoff"],
        "opl_runtime_owner_route_handoff": handoff,
        "route_transition_contract": route_transition_contract,
        "stage_graph_handoff": stage_graph_handoff,
        "source_refs": [
            ref
            for ref in (
                _source_ref(
                    study_root=study_root,
                    role="owner_route_handoff",
                    relative_path=Path("artifacts/supervision/owner_route_handoff/latest.json"),
                    workspace_root=profile.workspace_root,
                ),
            )
            if ref["exists"]
        ],
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "continuation_reason": reason,
            "authority_boundary": "mas_owner_reconcile_only",
            "owner_route_handoff_ref": owner_route_handoff_ref,
            "route_transition_contract": route_transition_contract,
            "stage_graph_handoff": stage_graph_handoff,
        },
    }


def _route_transition_contract(*, handoff: Mapping[str, Any]) -> dict[str, Any]:
    authority_boundary = _mapping(handoff.get("authority_boundary"))
    return {
        "surface_kind": "mas_route_transition_contract",
        "version": "mas-route-transition-contract.v1",
        "route_is_stage": False,
        "route_semantics_owner": "med-autoscience",
        "stage_lifecycle_owner": "one-person-lab",
        "runtime_transition_owner": "one-person-lab",
        "queue_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "task_kind": "domain_route/reconcile-apply",
        "allowed_payload_refs": [
            "domain_route_ref",
            "owner_route_ref",
            "source_scope_refs",
            "artifact_scope_refs",
            "workspace_scope_refs",
            "runtime_event_refs",
            "expected_owner_receipt_refs",
            "typed_blocker_refs",
            "human_gate_schema_ref",
            "authority_boundary",
            "no_forbidden_write_ref",
        ],
        "forbidden_payload_refs": [
            "study_truth_body",
            "paper_body",
            "manuscript_body",
            "publication_verdict_body",
            "ai_reviewer_verdict_body",
            "artifact_body",
            "package_body",
            "memory_body",
            "current_package_body",
            "runtime_queue_state",
            "retry_state",
            "dead_letter_state",
            "worker_liveness_truth",
        ],
        "forbidden_writes": [
            ".ds/runtime_state.json",
            ".ds/user_message_queue.json",
            "runtime_queue_state",
            "retry_state",
            "dead_letter_state",
            "worker_liveness_truth",
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
            "manuscript/current_package",
            "manuscript/current_package.zip",
            "current_package_mutation",
        ],
        "authority_boundary": {
            "mas_owner_receipt_required": authority_boundary.get("mas_owner_receipt_required") is True,
            "opl_writes_mas_truth": False,
            "mas_writes_generic_runtime_queue": False,
            "mas_resumes_provider_worker": False,
            "opl_may_hydrate_queue_from_refs": True,
            "opl_may_record_transport_receipt": True,
        },
    }


def _stage_graph_handoff() -> dict[str, Any]:
    return {
        "surface_kind": "mas_stage_graph_handoff",
        "version": "mas-stage-graph-handoff.v1",
        "route_is_stage": False,
        "stage_graph_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "authority_boundary": {
            "mas_declares_route_semantics": True,
            "opl_owns_stage_attempt_graph": True,
            "mas_owns_artifact_authority": True,
            "mas_owner_receipt_required": True,
            "same_invocation_self_review_closure_allowed": False,
        },
        "route_stage_graph_hints": {
            "journal-resolution": {
                "route": "journal-resolution",
                "stage": "finalize_and_publication_handoff",
                "stage_graph_owner": "one-person-lab",
                "stage_graph_nodes": [
                    "journal_requirements_resolution",
                    "format_delta_plan",
                    "artifact_mutation_authorization",
                    "independent_format_review",
                    "submission_package_handoff",
                ],
                "allowed_handoff_refs": [
                    "target_journal_ref",
                    "author_guideline_refs",
                    "format_requirement_refs",
                    "submission_package_boundary_ref",
                    "artifact_authority_receipt_ref",
                    "independent_review_record_ref",
                    "human_gate_schema_ref",
                    "typed_blocker_refs",
                    "owner_receipt_refs",
                ],
                "forbidden_handoff_refs": [
                    "artifact_body",
                    "package_body",
                    "manuscript_body",
                    "current_package_body",
                    "publication_verdict_body",
                    "runtime_queue_state",
                ],
            },
            "finalize": {
                "route": "finalize",
                "stage": "finalize_and_publication_handoff",
                "stage_graph_owner": "one-person-lab",
                "allowed_handoff_refs": [
                    "artifact_authority_receipt_ref",
                    "submission_package_boundary_ref",
                    "owner_receipt_refs",
                    "typed_blocker_refs",
                    "human_gate_schema_ref",
                ],
                "forbidden_handoff_refs": [
                    "artifact_body",
                    "package_body",
                    "current_package_body",
                    "publication_verdict_body",
                    "runtime_queue_state",
                ],
            },
        },
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {
        "ref_kind": "repo_path",
        "role": role,
        "ref": _workspace_relative(path, workspace_root=workspace_root),
        "exists": path.exists(),
    }


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


__all__ = ["owner_route_handoff_task"]
