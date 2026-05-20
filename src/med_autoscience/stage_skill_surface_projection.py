from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience import stage_quality_contract


SURFACE_KIND = "stage_skill_surface_projection"
VERSION = "stage-skill-surface-projection.v1"
CONTRACT_REF = "med_autoscience.stage_skill_surface_projection.build_stage_skill_surface_projection"
REPO_PATH = "src/med_autoscience/stage_skill_surface_projection.py"
DEFAULT_STAGE_CARD_REF = "/product_entry_manifest/family_stage_control_plane/stages"
CODEX_CLI_LAUNCH_PACKET_KIND = "mas_codex_cli_stage_launch_packet"
CODEX_CLI_LAUNCH_PACKET_VERSION = "mas-codex-cli-stage-launch-packet.v1"
CODEX_CLI_EXECUTOR_REQUIREMENTS = "Codex CLI default"
VALID_CODEX_STAGE_OUTCOMES = (
    "owner_receipt",
    "typed_blocker",
    "route_back_request",
    "human_gate_request",
    "no_op_with_currentness_proof",
)
FORBIDDEN_CODEX_STAGE_AUTHORITY = (
    "domain_truth",
    "quality_verdict",
    "publication_readiness",
    "submission_readiness",
    "artifact_authority",
    "source_readiness_verdict",
    "memory_writeback_acceptance",
    "script_exit_code_as_publication_quality_verdict",
    "function_return_value_as_ai_reviewer_quality_decision",
    "test_pass_as_artifact_mutation_authorization",
    "queue_completion_as_publication_route_memory_accept_reject",
    "file_presence_as_source_readiness_verdict",
    "provider_completion_as_medical_readiness",
)


def build_stage_skill_surface_projection(*, stage_id: str | None = None) -> dict[str, Any]:
    stage_ref = DEFAULT_STAGE_CARD_REF
    if stage_id:
        stage_ref = f"{DEFAULT_STAGE_CARD_REF}/{stage_id}"
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "skill_locator": {
            "ref_kind": "json_pointer",
            "ref": "/skill_catalog/skills/0",
            "role": "mas_domain_skill_descriptor",
        },
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "refresh_policy": stage_quality_contract.REFRESH_POLICY,
            "source_ref": REPO_PATH,
            "stale_if_projection_source_missing": True,
        },
        "quality_pack_refs": list(stage_quality_contract.REQUIRED_STAGE_QUALITY_PACK_IDS),
        "stage_card_ref": {
            "ref_kind": "json_pointer",
            "ref": stage_ref,
            "role": "family_stage_card_descriptor",
        },
        "authority_boundary": {
            "truth_owner": "MedAutoScience",
            "quality_owner": "MedAutoScience",
            "publication_readiness_owner": "MedAutoScience",
            "opl_role": "descriptor_ref_freshness_locator_consumer",
            "allowed_fields": [
                "skill_locator",
                "freshness",
                "quality_pack_refs",
                "stage_card_ref",
                "authority_boundary",
            ],
            "can_write_mas_truth": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "can_close_paper": False,
        },
    }


def build_codex_cli_launch_packet(
    *,
    stage_id: str,
    prompt_ref: Mapping[str, Any],
    skill_refs: list[Mapping[str, Any]],
    knowledge_refs: list[Mapping[str, Any]],
    quality_gate_refs: list[Mapping[str, Any]],
    quality_pack_refs: list[str],
    allowed_action_refs: list[str],
    expected_runtime_event_refs: list[str],
    independent_gate_receipt_required: bool,
) -> dict[str, Any]:
    return {
        "surface_kind": CODEX_CLI_LAUNCH_PACKET_KIND,
        "version": CODEX_CLI_LAUNCH_PACKET_VERSION,
        "stage_id": str(stage_id),
        "executor_requirements": CODEX_CLI_EXECUTOR_REQUIREMENTS,
        "prompt_ref": dict(prompt_ref),
        "skill_refs": [dict(ref) for ref in skill_refs],
        "tool_refs": {
            "allowed_action_refs": list(allowed_action_refs),
            "dispatch_boundary": "mas_guarded_actions_only",
            "default_executor_kind": "codex_cli_default",
            "can_write_mas_truth": False,
            "can_authorize_quality_verdict": False,
        },
        "knowledge_refs": [dict(ref) for ref in knowledge_refs],
        "quality_gate_refs": [dict(ref) for ref in quality_gate_refs],
        "quality_pack_refs": list(quality_pack_refs),
        "expected_receipt_refs": {
            "owner_receipt_contract_ref": "/product_entry_manifest/owner_receipt_contract",
            "stage_status_ref": "/progress_projection",
            "runtime_event_refs": list(expected_runtime_event_refs),
            "valid_outcomes": list(VALID_CODEX_STAGE_OUTCOMES),
            "independent_gate_receipt_required": bool(independent_gate_receipt_required),
        },
        "ai_first_boundary": {
            "contract_role": "boundary_and_evidence_refs_only",
            "script_verdict_authority": False,
            "self_review_closes_quality_gate": False,
            "independent_reviewer_auditor_required_when_gate_closes": True,
            "codex_cli_may_review_only_as_separate_invocation": True,
        },
        "forbidden_authority": list(FORBIDDEN_CODEX_STAGE_AUTHORITY),
    }


__all__ = [
    "CODEX_CLI_EXECUTOR_REQUIREMENTS",
    "CODEX_CLI_LAUNCH_PACKET_KIND",
    "CODEX_CLI_LAUNCH_PACKET_VERSION",
    "CONTRACT_REF",
    "DEFAULT_STAGE_CARD_REF",
    "FORBIDDEN_CODEX_STAGE_AUTHORITY",
    "REPO_PATH",
    "SURFACE_KIND",
    "VALID_CODEX_STAGE_OUTCOMES",
    "VERSION",
    "build_codex_cli_launch_packet",
    "build_stage_skill_surface_projection",
]
