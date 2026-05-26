from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers.real_paper_autonomy_soak_inventory_parts import (
    forbidden_write_guard,
    guarded_apply,
    provider_guarded_apply,
)
from med_autoscience.profiles import WorkspaceProfile


def build_soak_projection_for_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    target_studies: Sequence[str] | None = None,
) -> dict[str, Any]:
    targets = _loaded_profile_target_studies(profile=profile, target_studies=target_studies)
    profiles = [
        _profile_soak_projection_from_profile(
            profile=profile,
            profile_ref=profile_ref,
            target_studies=targets,
        )
    ]
    return build_soak_projection_payload(
        profiles=profiles,
        target_studies=targets,
    )


def build_soak_projection_payload(
    *,
    profiles: Sequence[Mapping[str, Any]],
    target_studies: Sequence[str],
) -> dict[str, Any]:
    inventory = _inventory()
    targets = tuple(target_studies)
    target_coverage = inventory._target_coverage(profiles=profiles, target_studies=targets)
    state_counts = inventory._projection_state_counts(profiles)
    return {
        "surface": inventory.SOAK_PROJECTION_SURFACE,
        "schema_version": inventory.SCHEMA_VERSION,
        "mode": "read_only_soak_projection",
        "read_only_contract": dict(inventory.READ_ONLY_CONTRACT, mode="read_only_soak_projection"),
        "profile_count": len(profiles),
        "profiles": profiles,
        "summary": {
            "target_studies": list(targets),
            "accepted_state_counts": state_counts,
            "target_coverage": target_coverage,
            "typed_blocker_count": sum(len(item.get("typed_blockers", [])) for item in target_coverage),
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
        },
    }


def build_soak_closeout_projection_for_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    target_studies: Sequence[str] | None = None,
) -> dict[str, Any]:
    targets = _loaded_profile_target_studies(profile=profile, target_studies=target_studies)
    projection = build_soak_projection_for_profile(
        profile=profile,
        profile_ref=profile_ref,
        target_studies=targets,
    )
    return build_soak_closeout_projection_payload(
        projection=projection,
        target_studies=targets,
    )


def build_soak_closeout_projection_payload(
    *,
    projection: Mapping[str, Any],
    target_studies: Sequence[str],
) -> dict[str, Any]:
    inventory = _inventory()
    targets = tuple(target_studies)
    source_summary = _mapping(projection.get("summary"))
    target_coverage = list(source_summary.get("target_coverage") or [])
    selected = inventory._dedupe_target_studies(projection.get("profiles", []))
    closeouts = inventory._target_closeout_packets(
        selected_studies=selected,
        target_studies=targets,
        target_coverage=target_coverage,
    )
    typed_blocker_study_ids = [
        study_id
        for study_id, closeout in closeouts
        if closeout["domain_ready_verdict"] == "typed_blocker"
    ]
    return {
        "surface": inventory.SOAK_CLOSEOUT_SURFACE,
        "schema_version": inventory.SCHEMA_VERSION,
        "mode": "read_only_closeout_projection",
        "read_only_contract": dict(inventory.READ_ONLY_CONTRACT, mode="read_only_closeout_projection"),
        "target_studies": list(targets),
        "closeout_packets": [closeout for _, closeout in closeouts],
        "summary": {
            "target_study_count": len(targets),
            "resolved_closeout_count": len(closeouts),
            "typed_blocker_count": len(typed_blocker_study_ids),
            "typed_blocker_study_ids": typed_blocker_study_ids,
            "target_coverage": target_coverage,
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
        },
        "authority_boundary": inventory._closeout_authority_boundary(),
        "source_projection_summary": {
            "surface": projection.get("surface"),
            "schema_version": projection.get("schema_version"),
            "mode": projection.get("mode"),
            "profile_count": projection.get("profile_count"),
            "summary": {
                "target_studies": list(source_summary.get("target_studies") or []),
                "accepted_state_counts": dict(_mapping(source_summary.get("accepted_state_counts"))),
                "target_coverage": target_coverage,
                "typed_blocker_count": source_summary.get("typed_blocker_count"),
                "writes_performed": source_summary.get("writes_performed"),
                "real_workspace_mutation_allowed": source_summary.get("real_workspace_mutation_allowed"),
            },
        },
    }


def build_provider_hosted_paper_proof_from_projection(
    *,
    closeout_projection: Mapping[str, Any],
    target_studies: Sequence[str],
) -> dict[str, Any]:
    inventory = _inventory()
    targets = tuple(target_studies)
    closeout_packets = [dict(_mapping(packet)) for packet in closeout_projection.get("closeout_packets", [])]
    memory_refs = _dedupe_text(
        ref
        for packet in closeout_packets
        for ref in packet.get("consumed_memory_refs", [])
    )
    writeback_receipt_refs = _dedupe_text(
        ref
        for packet in closeout_packets
        for ref in packet.get("writeback_receipt_refs", [])
    )
    forbidden_guard = forbidden_write_guard.build_provider_forbidden_write_guard(closeout_packets=closeout_packets)
    return {
        "surface": inventory.PROVIDER_HOSTED_PROOF_SURFACE,
        "schema_version": inventory.SCHEMA_VERSION,
        "mode": "read_only_provider_hosted_paper_proof",
        "provider_hosted_status": "readonly_closeout_packet_ready_guarded_apply_pending",
        "target_studies": list(targets),
        "provider_attempt_projection": {
            "attempt_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "attempt_kind": "opl_provider_hosted_stage_attempt",
            "attempt_receipt_policy": "transport_receipt_only_no_domain_truth_authority",
            "typed_closeout_packet_count": len(closeout_packets),
            "can_advance_paper_progress_without_mas_owner_receipt": False,
            "guarded_apply_performed": False,
        },
        "typed_closeout_packets": closeout_packets,
        "publication_route_memory": {
            "consumed_refs": memory_refs,
            "writeback_receipt_refs": writeback_receipt_refs,
            "body_included": False,
            "writeback_acceptance_owner": "med-autoscience",
            "opl_can_read_memory_body": False,
            "opl_can_accept_or_reject_writeback": False,
        },
        "forbidden_write_guard": forbidden_guard,
        "summary": {
            "target_study_count": closeout_projection["summary"]["target_study_count"],
            "typed_closeout_packet_count": len(closeout_packets),
            "typed_blocker_count": closeout_projection["summary"]["typed_blocker_count"],
            "memory_consumed_ref_count": len(memory_refs),
            "writeback_receipt_ref_count": len(writeback_receipt_refs),
            "forbidden_write_guard_result": forbidden_guard["aggregate_result"],
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
            "guarded_apply_performed": False,
        },
        "authority_boundary": inventory._closeout_authority_boundary()
        | {
            "provider_attempt_owner": "one-person-lab",
            "provider_attempt_is_truth": False,
            "provider_completion_is_publication_quality": False,
        },
        "source_closeout_projection_summary": {
            "surface": closeout_projection.get("surface"),
            "schema_version": closeout_projection.get("schema_version"),
            "mode": closeout_projection.get("mode"),
            "summary": dict(_mapping(closeout_projection.get("summary"))),
        },
    }


def build_guarded_apply_proof_for_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    target_studies: Sequence[str] | None = None,
) -> dict[str, Any]:
    inventory = _inventory()
    targets = _loaded_profile_target_studies(profile=profile, target_studies=target_studies)
    provider_proof = build_provider_hosted_paper_proof_from_projection(
        closeout_projection=build_soak_closeout_projection_for_profile(
            profile=profile,
            profile_ref=profile_ref,
            target_studies=targets,
        ),
        target_studies=targets,
    )
    proof = guarded_apply.build_guarded_apply_proof_from_provider_proof(
        provider_proof=provider_proof,
        schema_version=inventory.SCHEMA_VERSION,
        surface=inventory.GUARDED_APPLY_PROOF_SURFACE,
        target_studies=targets,
    )
    provider_receipt = provider_guarded_apply.build_provider_hosted_guarded_apply_receipt_from_proof(
        proof=proof,
        schema_version=inventory.SCHEMA_VERSION,
        surface=inventory.PROVIDER_HOSTED_GUARDED_APPLY_RECEIPT_SURFACE,
        provider_attempt_id=f"product-entry-manifest:{profile.name}:real-paper-owner-payload-closeout",
        idempotency_key=f"mas:{profile.name}:product-entry-manifest:real-paper-owner-payload-closeout",
        target_studies=targets,
    )
    return {
        **proof,
        "paper_line_provider_canary_closeout": provider_receipt["paper_line_provider_canary_closeout"],
        "source_provider_hosted_guarded_apply_receipt_summary": {
            "surface": provider_receipt.get("surface"),
            "schema_version": provider_receipt.get("schema_version"),
            "status": provider_receipt.get("status"),
            "provider_attempt": dict(_mapping(provider_receipt.get("provider_attempt"))),
            "source_fingerprint": provider_receipt.get("source_fingerprint"),
            "summary": dict(_mapping(provider_receipt.get("summary"))),
        },
    }


def _profile_soak_projection_from_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    target_studies: Sequence[str],
) -> dict[str, Any]:
    inventory = _inventory()
    target_set = {str(study_id).strip() for study_id in target_studies if str(study_id).strip()}
    studies = [
        inventory._study_soak_projection(study_root)
        for study_root in inventory._study_roots(profile)
        if not target_set or inventory._matches_target_study(study_root.name, target_set)
    ]
    return {
        "profile_path": _profile_ref_text(profile=profile, profile_ref=profile_ref),
        "profile_readable": True,
        "profile_error": "",
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "studies": studies,
    }


def _profile_ref_text(*, profile: WorkspaceProfile, profile_ref: str | Path | None) -> str:
    if profile_ref is not None:
        return str(Path(profile_ref).expanduser().resolve())
    return f"loaded_workspace_profile:{profile.name}"


def _loaded_profile_target_studies(
    *,
    profile: WorkspaceProfile,
    target_studies: Sequence[str] | None,
) -> tuple[str, ...]:
    if target_studies is not None:
        return tuple(_text(study_id) for study_id in target_studies if _text(study_id))
    return tuple(study_root.name for study_root in _inventory()._study_roots(profile))


def _inventory():
    from med_autoscience.controllers import real_paper_autonomy_soak_inventory

    return real_paper_autonomy_soak_inventory


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


__all__ = [
    "build_guarded_apply_proof_for_profile",
    "build_provider_hosted_paper_proof_from_projection",
    "build_soak_closeout_projection_for_profile",
    "build_soak_closeout_projection_payload",
    "build_soak_projection_for_profile",
    "build_soak_projection_payload",
]
