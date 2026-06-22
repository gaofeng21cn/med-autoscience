from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_GOVERNED_ANSWER_SHAPES = (
    "domain_owner_receipt_ref",
    "quality_gate_receipt_ref",
    "route_back_evidence_ref",
    "typed_blocker_ref",
    "human_gate_ref",
)


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    filename: str
    study_id: str
    packet_kind: str
    owner_surface: str
    owner_identity: Mapping[str, str]
    next_legal_surface: Mapping[str, str]
    stable_blocker_ref: str | None = None


_CANDIDATES: dict[str, CandidateSpec] = {
    "B002-0810": CandidateSpec(
        candidate_id="B002-0810",
        filename="current_main_03c390_b002_post_0808_owner_answer_candidate_0810.md",
        study_id="002-dm-china-us-mortality-attribution",
        packet_kind="package_local_ai_reviewer_mas_owner_answer_candidate",
        owner_surface="MAS publication AI-reviewer governed owner answer",
        owner_identity={
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::"
                "produce_ai_reviewer_publication_eval_record_against_current_inputs"
            ),
        },
        next_legal_surface={
            "kind": "ai_reviewer_owner_answer_or_route_back",
            "accept_path": "accept_metadata_only_payload_target_refresh_after_0808",
            "owner_callable": "publication_ai_reviewer_owner_intake",
        },
    ),
    "B003-0751": CandidateSpec(
        candidate_id="B003-0751",
        filename="current_main_03c390_b003_post_0736_blocker_disposition_packet_0751.md",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        packet_kind="paper_facing_route_back_narrower_blocker_human_gate_packet_not_authority",
        owner_surface="MAS paper recovery / publication gate governed owner answer",
        owner_identity={
            "owner": "med-autoscience",
            "action_type": "publication_gate_replay",
            "work_unit_id": "publication-blockers::0915410f804b3697",
            "work_unit_fingerprint": "owner-gate-decision:d6d895635654560a85573c04",
        },
        next_legal_surface={
            "kind": "publication_gate_owner_answer_or_human_gate",
            "owner_callable": "publication_gate_replay",
            "allowed_dispositions": (
                "preserve_blocker_after_story_surface_acceptance,"
                "narrow_blocker_to_remaining_gate_obstacle,"
                "route_back_specific_story_surface,"
                "human_gate_for_blocker_disposition"
            ),
        },
        stable_blocker_ref="owner-gate-decision:d6d895635654560a85573c04",
    ),
}


def intake_owner_answer_candidate(
    *,
    candidate_id: str,
    candidate_path: Path,
    expected_sha256: str | None,
) -> dict[str, Any]:
    spec = _candidate_spec(candidate_id)
    path = Path(candidate_path).expanduser().resolve()
    payload = path.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    base = _base_payload(spec=spec, path=path, actual_sha=actual_sha)
    if path.name != spec.filename:
        return {
            **base,
            "status": "candidate_filename_mismatch",
            "expected_filename": spec.filename,
            "actual_filename": path.name,
            "blocked_owner": _blocked_owner(spec),
        }
    if expected_sha256 and actual_sha != expected_sha256:
        return {
            **base,
            "status": "candidate_hash_mismatch",
            "expected_sha256": expected_sha256,
            "blocked_owner": _blocked_owner(spec),
        }
    return {
        **base,
        "status": "exact_blocked_owner",
        "blocked_owner": _blocked_owner(spec),
        "reason": (
            "Package-local foreground candidates are not MAS authority. A governed "
            "owner answer must consume the candidate and return an accepted answer "
            "shape before MAS can project it as consumed."
        ),
    }


def _candidate_spec(candidate_id: str) -> CandidateSpec:
    normalized = str(candidate_id or "").strip().upper()
    if normalized not in _CANDIDATES:
        raise ValueError(f"unknown owner answer candidate id: {candidate_id}")
    return _CANDIDATES[normalized]


def _base_payload(*, spec: CandidateSpec, path: Path, actual_sha: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface_kind": "mas_owner_answer_candidate_intake_readback",
        "schema_version": 1,
        "candidate_id": spec.candidate_id,
        "candidate_path": str(path),
        "candidate_filename": path.name,
        "candidate_sha256": actual_sha,
        "candidate_packet_kind": spec.packet_kind,
        "candidate_is_authority": False,
        "governed_answer_consumed": False,
        "study_id": spec.study_id,
        "owner_identity": dict(spec.owner_identity),
        "required_governed_answer_shapes": list(REQUIRED_GOVERNED_ANSWER_SHAPES),
        "next_legal_surface": dict(spec.next_legal_surface),
        "write_plan": _no_write_plan(),
        "forbidden_authority_writes": _forbidden_authority_writes(),
        "authority_boundary": _authority_boundary(),
    }
    if spec.stable_blocker_ref:
        payload["stable_blocker_policy"] = {
            "preserve_or_explicitly_supersede": spec.stable_blocker_ref,
            "provider_redrive_allowed": False,
        }
    return payload


def _blocked_owner(spec: CandidateSpec) -> dict[str, Any]:
    return {
        "owner_surface": spec.owner_surface,
        "study_id": spec.study_id,
        "owner_identity": dict(spec.owner_identity),
        "required_governed_answer_shapes": list(REQUIRED_GOVERNED_ANSWER_SHAPES),
        "missing_authority": "governed_owner_answer_consuming_package_candidate",
    }


def _no_write_plan() -> dict[str, Any]:
    return {
        "mode": "readback_only",
        "written_files": [],
        "can_write_publication_eval_latest": False,
        "can_write_controller_decisions_latest": False,
        "can_write_payload_targets": False,
        "can_write_owner_receipts": False,
        "can_write_typed_blockers": False,
        "can_write_human_gate_authority_records": False,
        "can_write_runtime_queues_or_provider_attempts": False,
        "can_write_canonical_package_or_manuscript": False,
    }


def _forbidden_authority_writes() -> dict[str, bool]:
    return {
        "publication_eval_latest": True,
        "controller_decisions_latest": True,
        "owner_receipts": True,
        "typed_blockers": True,
        "human_gate_authority_records": True,
        "runtime_provider_queues_attempts_admissions_leases": True,
        "payload_target_files": True,
        "canonical_manuscript_package_authority": True,
        "non_dry_run_ai_reviewer_materialization": True,
        "provider_redrive_hydrate_tick_replay_dhd_apply": True,
    }


def _authority_boundary() -> dict[str, bool | str]:
    return {
        "owner": "med-autoscience",
        "surface_role": "package_candidate_intake_readback_only",
        "candidate_markdown_can_satisfy_owner_answer": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_create_human_gate": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
    }


__all__ = ["intake_owner_answer_candidate"]
