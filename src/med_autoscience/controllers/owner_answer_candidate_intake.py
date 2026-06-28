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
B002_PUBLICATION_EVAL_RECORD_ANSWER_SHAPES = (
    "domain_owner_receipt_ref",
    "quality_gate_receipt_ref",
    "publication_eval_record_ref",
    "route_back_evidence_ref",
    "typed_blocker_ref",
    "human_gate_ref",
)
B003_GOVERNED_ANSWER_SHAPES = tuple(
    shape for shape in REQUIRED_GOVERNED_ANSWER_SHAPES if shape != "publication_eval_record_ref"
)
FORBIDDEN_NON_AUTHORITY_RESPONSE_REF_MARKERS = (
    "paper_mission_candidate_package",
    "paper_mission_consumption_ledger",
    "paper_mission_one_shot_migration",
    "candidate_manifest",
    "mission_candidate_artifact_delta",
    "owner_decision_packet",
    "stage_terminal_decision",
    "op-routes",
    "opl_route_command",
    "opl_route_handoff",
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
    provider_redrive_allowed: bool = False
    accepted_response_kinds: tuple[str, ...] = REQUIRED_GOVERNED_ANSWER_SHAPES


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
    "B002-0910": CandidateSpec(
        candidate_id="B002-0910",
        filename=(
            "current_main_74ee64_b002_0901_payload_metadata_human_gate_"
            "response_candidate_0910.md"
        ),
        study_id="002-dm-china-us-mortality-attribution",
        packet_kind="b002_0901_payload_metadata_human_gate_response_candidate",
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
            "kind": "ai_reviewer_payload_metadata_human_gate_or_route_back",
            "owner_callable": "publication_ai_reviewer_owner_intake",
            "immediate_executor_action_if_accepted": "rerun_same_no_write_guard_only",
            "payload_target_persistence_authorized": "false",
            "non_dry_run_materialization_authorized": "false",
        },
    ),
    "B002-1055": CandidateSpec(
        candidate_id="B002-1055",
        filename="current_main_6efcd4_b002_1045_payload_currentness_governed_answer_target_1055.md",
        study_id="002-dm-china-us-mortality-attribution",
        packet_kind="b002_payload_currentness_governed_answer_target",
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
            "kind": "ai_reviewer_payload_currentness_guard_owner_answer",
            "owner_callable": "publication_ai_reviewer_owner_intake",
            "immediate_executor_action_if_accepted": "rerun_same_no_write_guard_only",
            "payload_target_persistence_authorized": "false",
            "non_dry_run_materialization_authorized": "false",
        },
        accepted_response_kinds=B002_PUBLICATION_EVAL_RECORD_ANSWER_SHAPES,
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
        accepted_response_kinds=B003_GOVERNED_ANSWER_SHAPES,
    ),
    "B003-0915": CandidateSpec(
        candidate_id="B003-0915",
        filename=(
            "current_main_74ee64_b003_0901_preserve_blocker_typed_blocker_"
            "response_candidate_0915.md"
        ),
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        packet_kind="b003_0901_preserve_blocker_typed_blocker_response_candidate",
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
                "preserve_existing_stable_blocker,"
                "route_back_specific_story_surface,"
                "human_gate_for_blocker_disposition"
            ),
            "publication_gate_replay_authorized": "false",
            "provider_redrive_authorized": "false",
        },
        stable_blocker_ref="owner-gate-decision:d6d895635654560a85573c04",
        accepted_response_kinds=B003_GOVERNED_ANSWER_SHAPES,
    ),
    "B003-1105": CandidateSpec(
        candidate_id="B003-1105",
        filename="current_main_6efcd4_b003_1045_write_repair_stable_blocker_governed_answer_target_1105.md",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        packet_kind="b003_write_repair_stable_blocker_governed_answer_target",
        owner_surface="MAS paper recovery / publication gate governed owner answer",
        owner_identity={
            "owner": "med-autoscience",
            "action_type": "publication_gate_replay",
            "work_unit_id": "publication-blockers::0915410f804b3697",
            "work_unit_fingerprint": "owner-gate-decision:d6d895635654560a85573c04",
        },
        next_legal_surface={
            "kind": "publication_gate_write_repair_stable_blocker_owner_answer",
            "owner_callable": "publication_gate_replay",
            "allowed_dispositions": (
                "preserve_existing_stable_blocker,"
                "narrow_blocker_to_write_repair_route_selection_gap,"
                "route_back_missing_write_repair_owner_route,"
                "human_gate_for_blocker_disposition"
            ),
            "publication_gate_replay_authorized": "false",
            "provider_redrive_authorized": "false",
        },
        stable_blocker_ref="owner-gate-decision:d6d895635654560a85573c04",
        accepted_response_kinds=B003_GOVERNED_ANSWER_SHAPES,
    ),
}

SUPPORTED_CANDIDATE_IDS = tuple(_CANDIDATES)


def intake_owner_answer_candidate(
    *,
    candidate_id: str,
    candidate_path: Path,
    expected_sha256: str | None,
    governed_response_kind: str | None = None,
    governed_response_ref: str | None = None,
    governed_response_study_id: str | None = None,
    governed_response_owner_surface: str | None = None,
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
    governed_response = _normalize_governed_response(
        kind=governed_response_kind,
        ref=governed_response_ref,
        study_id=governed_response_study_id,
        owner_surface=governed_response_owner_surface,
    )
    if governed_response is not None:
        validation = _validate_governed_response(spec=spec, governed_response=governed_response)
        if validation is not None:
            return {
                **base,
                **validation,
                "blocked_owner": _blocked_owner(spec),
            }
        return {
            **base,
            "status": "governed_response_consumed",
            "governed_answer_consumed": True,
            "governed_response": {
                **governed_response,
                "candidate_id": spec.candidate_id,
                "consumed_by_surface": "mas_owner_answer_candidate_intake_readback",
            },
            "write_plan": _no_write_plan(),
            "reason": (
                "A governed response ref was provided with an accepted response kind "
                "and matching study/owner surface. The intake surface records a no-write "
                "readback only; it does not materialize authority."
            ),
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


def _normalize_governed_response(
    *,
    kind: str | None,
    ref: str | None,
    study_id: str | None,
    owner_surface: str | None,
) -> dict[str, str] | None:
    values = {
        "kind": (kind or "").strip(),
        "ref": (ref or "").strip(),
        "study_id": (study_id or "").strip(),
        "owner_surface": (owner_surface or "").strip(),
    }
    if not any(values.values()):
        return None
    return values


def _validate_governed_response(
    *,
    spec: CandidateSpec,
    governed_response: Mapping[str, str],
) -> dict[str, Any] | None:
    kind = governed_response.get("kind", "")
    if kind not in spec.accepted_response_kinds:
        return {
            "status": "governed_response_kind_not_accepted",
            "governed_answer_consumed": False,
            "governed_response": dict(governed_response),
            "accepted_response_kinds": list(spec.accepted_response_kinds),
        }
    missing = [
        key
        for key in ("ref", "study_id", "owner_surface")
        if not governed_response.get(key)
    ]
    if missing:
        return {
            "status": "governed_response_incomplete",
            "governed_answer_consumed": False,
            "governed_response": dict(governed_response),
            "missing_fields": missing,
        }
    forbidden_marker = _forbidden_non_authority_response_ref_marker(governed_response.get("ref", ""))
    if forbidden_marker:
        return {
            "status": "governed_response_ref_not_authority_materialized",
            "governed_answer_consumed": False,
            "governed_response": dict(governed_response),
            "forbidden_non_authority_ref_marker": forbidden_marker,
            "required_ref_boundary": "MAS authority owner answer ref",
        }
    if governed_response.get("study_id") != spec.study_id:
        return {
            "status": "governed_response_study_mismatch",
            "governed_answer_consumed": False,
            "governed_response": dict(governed_response),
            "expected_study_id": spec.study_id,
        }
    if governed_response.get("owner_surface") != spec.owner_surface:
        return {
            "status": "governed_response_owner_surface_mismatch",
            "governed_answer_consumed": False,
            "governed_response": dict(governed_response),
            "expected_owner_surface": spec.owner_surface,
        }
    return None


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
        "required_governed_answer_shapes": list(spec.accepted_response_kinds),
        "next_legal_surface": dict(spec.next_legal_surface),
        "governed_owner_response_transport": _governed_owner_response_transport(spec),
        "write_plan": _no_write_plan(),
        "forbidden_authority_writes": _forbidden_authority_writes(),
        "authority_boundary": _authority_boundary(),
    }
    if spec.stable_blocker_ref:
        payload["stable_blocker_policy"] = {
            "preserve_or_explicitly_supersede": spec.stable_blocker_ref,
            "provider_redrive_allowed": spec.provider_redrive_allowed,
        }
    return payload


def _blocked_owner(spec: CandidateSpec) -> dict[str, Any]:
    return {
        "owner_surface": spec.owner_surface,
        "study_id": spec.study_id,
        "owner_identity": dict(spec.owner_identity),
        "required_governed_answer_shapes": list(spec.accepted_response_kinds),
        "governed_owner_response_transport": _governed_owner_response_transport(spec),
        "missing_authority": "governed_owner_answer_consuming_package_candidate",
    }


def _governed_owner_response_transport(spec: CandidateSpec) -> dict[str, Any]:
    owner = spec.owner_identity
    if spec.candidate_id.startswith("B002-"):
        return {
            "status": "available",
            "owner_surface": spec.owner_surface,
            "authoring_surface": "ai_reviewer_record_payload_authoring_target",
            "authoring_target_ref": (
                "artifacts/supervision/requests/ai_reviewer/record_production_payloads/"
                "return_to_ai_reviewer_workflow_payload.json"
            ),
            "owner_authored_field": "record_payload",
            "transport_command": (
                "medautosci publication materialize-ai-reviewer-record "
                "--profile <profile.toml> "
                f"--study-id {spec.study_id} "
                "--payload-file <ai_reviewer_record_payload_authoring_target.json> "
                "--entry-mode owner_consumption_payload_guard "
                "--expected-owner ai_reviewer "
                f"--expected-action-type {owner.get('action_type')} "
                f"--expected-work-unit-id {owner.get('work_unit_id')} "
                f"--expected-work-unit-fingerprint {owner.get('work_unit_fingerprint')} "
                "--build-production-trace"
            ),
            "no_write_readback_command": (
                "medautosci publication materialize-ai-reviewer-record "
                "--profile <profile.toml> "
                f"--study-id {spec.study_id} "
                "--entry-mode owner_consumption_payload_guard "
                "--expected-owner ai_reviewer "
                f"--expected-action-type {owner.get('action_type')} "
                f"--expected-work-unit-id {owner.get('work_unit_id')} "
                f"--expected-work-unit-fingerprint {owner.get('work_unit_fingerprint')} "
                "--build-production-trace --dry-run"
            ),
            "response_kind": "publication_eval_record_ref",
            "response_ref_source": "publication_eval_record_ref",
            "record_only_surface": True,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
            "paper_progress_claim_allowed": False,
        }
    if spec.candidate_id.startswith("B003-"):
        return {
            "status": "available",
            "owner_surface": spec.owner_surface,
            "authoring_surface": "study_owner_gate_decision_record",
            "transport_command": (
                "medautosci study-owner-gate-decision "
                "--profile <profile.toml> "
                f"--study-id {spec.study_id} "
                f"--action-type {owner.get('action_type')} "
                f"--work-unit-id {owner.get('work_unit_id')} "
                f"--work-unit-fingerprint {owner.get('work_unit_fingerprint')} "
                "--blocker-type <current_blocker_type> "
                "--decision <preserve_existing_stable_blocker|narrow_stable_blocker|"
                "route_back_to_publication_owner|explicitly_supersede_stable_blocker> "
                "--reason <owner_reason> "
                f"--supersedes-owner-gate-decision-ref {spec.stable_blocker_ref or '<owner-gate-decision-ref>'} "
                "--dry-run"
            ),
            "response_kind": "human_gate_ref",
            "response_ref_source": "human_gate_ref",
            "preserve_or_explicitly_supersede": spec.stable_blocker_ref,
            "provider_redrive_allowed": False,
            "publication_gate_replay_authorized": False,
            "paper_progress_claim_allowed": False,
        }
    return {
        "status": "not_declared",
        "owner_surface": spec.owner_surface,
        "paper_progress_claim_allowed": False,
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
        "provider_redrive_hydrate_tick_replay_domain_diagnostic_apply": True,
    }


def _authority_boundary() -> dict[str, bool | str]:
    return {
        "owner": "med-autoscience",
        "surface_role": "package_candidate_intake_readback_only",
        "candidate_markdown_can_satisfy_owner_answer": False,
        "candidate_or_ledger_ref_can_satisfy_governed_answer": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_create_human_gate": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
    }


def _forbidden_non_authority_response_ref_marker(ref: str) -> str | None:
    normalized = str(ref or "").strip()
    return next(
        (marker for marker in FORBIDDEN_NON_AUTHORITY_RESPONSE_REF_MARKERS if marker in normalized),
        None,
    )


__all__ = ["SUPPORTED_CANDIDATE_IDS", "intake_owner_answer_candidate"]
