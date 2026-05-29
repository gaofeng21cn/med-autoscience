from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.closeout_io import (
    closeout_does_not_claim_domain_completion,
    read_json_object,
    workspace_relative_ref,
)
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    mapping,
    sequence,
    text,
)


def domain_stage_closeout_owner_evidence(
    *,
    profile: Any,
    study_id: str,
    target_identity: Mapping[str, Any],
    dispatch_identity: Mapping[str, Any],
    stage_attempt_id: str,
    action_type: str,
) -> dict[str, Any] | None:
    closeout_result = _find_domain_stage_closeout(
        profile=profile,
        study_id=study_id,
        target_identity=target_identity,
        dispatch_identity=dispatch_identity,
        stage_attempt_id=stage_attempt_id,
        action_type=action_type,
    )
    if closeout_result is None:
        return None
    closeout_ref, closeout = closeout_result
    artifact_delta = mapping(closeout.get("artifact_delta"))
    verification = mapping(closeout.get("verification"))
    return {
        "closeout_ref": closeout_ref,
        "closeout_refs": sequence(closeout.get("closeout_refs")),
        "owner_receipt_refs": [f"{closeout_ref}#write_owner_closeout"],
        "dispatch_ref": text(dispatch_identity.get("dispatch_ref")),
        "owner": text(closeout.get("owner")),
        "owner_callable_surface": text(closeout.get("surface_kind")),
        "request_ref": None,
        "publication_eval_ref": None,
        "route_outcome": text(closeout.get("status")),
        "quality_status": text(mapping(verification.get("hash_and_size")).get("sha256")),
        "claim_evidence_alignment_status": text(
            mapping(verification.get("draft_review_manuscript_cmp")).get("observed_stdout")
        ),
        "artifact_delta_refs": sequence(artifact_delta.get("artifact_refs")),
        "status": text(closeout.get("status")),
        "artifact_delta_status": text(artifact_delta.get("status")),
        "required_output_surface": text(closeout.get("required_output_surface")),
    }


def _find_domain_stage_closeout(
    *,
    profile: Any,
    study_id: str,
    target_identity: Mapping[str, Any],
    dispatch_identity: Mapping[str, Any],
    stage_attempt_id: str,
    action_type: str,
) -> tuple[str, dict[str, Any]] | None:
    dispatch_ref = text(dispatch_identity.get("dispatch_ref"))
    if dispatch_ref is None:
        return None
    review_root = profile.studies_root / study_id / "paper" / "review"
    for path in sorted(review_root.glob(f"domain_stage_closeout_{stage_attempt_id}_*.json"), reverse=True):
        closeout = read_json_object(path)
        if closeout is None:
            continue
        closeout_ref = workspace_relative_ref(path, workspace_root=profile.workspace_root)
        if closeout_ref is None:
            continue
        if _is_matching_domain_stage_write_closeout(
            closeout=closeout,
            target_identity=target_identity,
            study_id=study_id,
            stage_attempt_id=stage_attempt_id,
            action_type=action_type,
            dispatch_ref=dispatch_ref,
            workspace_root=profile.workspace_root,
        ):
            return closeout_ref, closeout
    return None


def _is_matching_domain_stage_write_closeout(
    *,
    closeout: Mapping[str, Any],
    target_identity: Mapping[str, Any],
    study_id: str,
    stage_attempt_id: str,
    action_type: str,
    dispatch_ref: str,
    workspace_root: Any,
) -> bool:
    authority_boundary = mapping(closeout.get("authority_boundary"))
    artifact_delta = mapping(closeout.get("artifact_delta"))
    stage_packet_ref = text(closeout.get("stage_packet_ref"))
    stage_packet_matches = (
        stage_packet_ref == dispatch_ref
        or (
            stage_packet_ref is not None
            and workspace_relative_ref(stage_packet_ref, workspace_root=workspace_root) == dispatch_ref
        )
    )
    return (
        text(closeout.get("surface_kind")) == "domain_stage_closeout_packet"
        and text(closeout.get("stage_attempt_id")) == stage_attempt_id
        and text(closeout.get("stage_id")) == text(target_identity.get("stage_id"))
        and text(closeout.get("study_id")) == study_id
        and text(closeout.get("action_type")) == action_type
        and text(closeout.get("owner")) == "write"
        and text(closeout.get("status")) == "completed_for_write_owner"
        and text(closeout.get("required_output_surface")) == "canonical manuscript story-surface delta"
        and closeout.get("typed_blocker") is None
        and stage_packet_matches
        and text(artifact_delta.get("status")) == "materialized"
        and closeout_does_not_claim_domain_completion(closeout)
        and authority_boundary.get("publication_quality_authorized") is False
        and authority_boundary.get("submission_authorized") is False
        and authority_boundary.get("paper_package_mutation_allowed") is False
        and authority_boundary.get("quality_gate_relaxation_allowed") is False
        and authority_boundary.get("manual_study_patch_allowed") is False
    )
