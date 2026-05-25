from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience import stage_quality_contract

from .provider_readiness import DOMAIN_OWNER, TARGET_DOMAIN_ID

REPO_ROOT = Path(__file__).resolve().parents[4]
REPO_SOURCE_ANCHORS = {
    "agent": "agent/standard-domain-agent-anchor.json",
    "contracts": "contracts/runtime/standard-domain-agent-anchor.json",
    "runtime": "runtime/artifact_locator/workspace-runtime-artifact-root.locator.json",
    "docs": "docs/runtime/contracts/standard_domain_agent_skeleton.md",
}


def build_domain_agent_skeleton_mapping_surface() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_domain_agent_skeleton_mapping",
        "version": "mas-opl-domain-agent-skeleton-mapping.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "mapping_mode": "repo_source_physical_anchors_landed",
        "repo_tracks_real_workspace_artifacts": False,
        "repo_source_anchor_status": _repo_source_anchor_status(),
        "skeleton": {
            "agent/stages": [
                "agent/stages/stage_route_contract.yaml",
                "med_autoscience.controllers.stage_knowledge_plane.stage_knowledge_plane_contract",
            ],
            "agent/prompts": [
                "MAS app skill command contracts",
                "stage prompt and review/repair prompt surfaces",
            ],
            "agent/skills": [
                "medautosci product skill-catalog --format json",
                "medautosci domain-handler export --format json",
                "medautosci domain-handler dispatch --format json",
            ],
            "agent/knowledge": [
                "artifacts/stage_knowledge/<stage>/latest.json",
                "stage_memory_closeout_packet",
                "memory_write_router_receipt",
                "stage_recall_index",
            ],
            "agent/quality_gates": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "AI reviewer workflow",
                "claim-evidence and submission package gates",
                stage_quality_contract.REPO_PATH,
            ],
            "contracts/runtime/domain-handler": [
                "mas_family_domain_handler_export",
                "mas_family_domain_handler_dispatch_receipt",
                "mas_opl_forbidden_write_guard_proof",
            ],
            "contracts/runtime/projection_builders": [
                "mas_opl_runtime_workbench_projection",
                "progress_portal opl_handoff projection",
                "product-entry manifest provider-ready contract",
            ],
            "contracts/runtime/lifecycle_adapters": [
                "mas_opl_lifecycle_inventory",
                "workspace_runtime_artifact_root_locator",
                "domain_authority_refs_index refs-only replacement for retired lifecycle refs adapter",
            ],
        },
    }

def build_standard_domain_agent_skeleton_surface() -> dict[str, Any]:
    mapping = build_domain_agent_skeleton_mapping_surface()
    return {
        "surface_kind": "standard_domain_agent_skeleton",
        "version": "standard-domain-agent-skeleton.v1",
        "skeleton_id": "mas.standard_domain_agent_skeleton.v1",
        "target_domain_id": DOMAIN_OWNER,
        "mapping_mode": mapping["mapping_mode"],
        "repo_tracks_real_workspace_artifacts": mapping["repo_tracks_real_workspace_artifacts"],
        "repo_source_boundary": {
            "required_dirs": ["agent", "contracts", "runtime", "docs"],
            "forbidden_dirs": ["artifacts"],
        },
        "repo_source_anchor_status": mapping["repo_source_anchor_status"],
        "skeleton": mapping["skeleton"],
        "default_new_surface_slots": {
            "stage": "agent/stages",
            "prompt": "agent/prompts",
            "skill": "agent/skills",
            "knowledge": "agent/knowledge",
            "quality": "agent/quality_gates",
            "projection": "contracts/runtime/projection_builders",
        },
        "workspace_runtime_artifact_root_locator_ref": (
            "/product_entry_manifest/workspace_runtime_artifact_root_locator"
        ),
        "quality_pack_locator": stage_quality_contract.build_stage_quality_pack_locator_projection(),
        "artifact_boundary": {
            "repo_contains_real_artifacts": False,
            "artifact_roots_are_locators": True,
            "workspace_artifact_locator_refs": [
                "/product_entry_manifest/workspace_runtime_artifact_root_locator"
            ],
            "runtime_artifact_locator_refs": [
                "/product_entry_manifest/workspace_runtime_artifact_root_locator"
            ],
        },
        "physical_skeleton_layout_audit": build_physical_skeleton_layout_audit_surface(),
        "authority_boundary": {
            "opl": "framework_transport_and_projection_only",
            "domain_agent": "truth_quality_artifact_owner",
            "forbidden_opl_authority": [
                "domain_truth",
                "quality_verdict",
                "canonical_artifact_blob",
                "publication_or_export_gate",
            ],
        },
    }

def build_physical_skeleton_layout_audit_surface() -> dict[str, Any]:
    slots = [
        _physical_skeleton_slot(
            "agent/stages",
            surface_class="stage",
            default_for_new_surfaces=True,
            repo_paths=[
                "docs/policies/study-workflow/stage_led_research_autonomy.md",
                "agent/stages/stage_route_contract.yaml",
                "src/med_autoscience/controllers/stage_knowledge_plane.py",
            ],
            mapping_explanation=(
                "New stage definitions should land in the standard slot while existing stage policy "
                "and stage knowledge controller paths remain the active repo mapping."
            ),
        ),
        _physical_skeleton_slot(
            "agent/prompts",
            surface_class="prompt",
            default_for_new_surfaces=True,
            repo_paths=[
                "templates/stage_route_contract.yaml",
                "templates/codex/medautoscience-entry.SKILL.md",
                "templates/openclaw/medautoscience-entry.prompt.md",
            ],
            mapping_explanation=(
                "New prompt surfaces should land in the standard prompt slot; existing Codex and "
                "OpenClaw entry templates stay as generated prompt assets."
            ),
        ),
        _physical_skeleton_slot(
            "agent/skills",
            surface_class="skill",
            default_for_new_surfaces=True,
            repo_paths=[
                "src/med_autoscience/cli.py",
                "src/med_autoscience/cli_parts/parser.py",
                "plugins/mas/bin/medautosci-mcp",
            ],
            mapping_explanation=(
                "New skill-callable surfaces should land in the standard skill slot while the "
                "current CLI, parser, and MCP wrapper remain the active callable surfaces."
            ),
        ),
        _physical_skeleton_slot(
            "agent/knowledge",
            surface_class="knowledge",
            default_for_new_surfaces=True,
            repo_paths=[
                "docs/policies/study-workflow/publication_route_memory_policy.md",
                "docs/policies/study-workflow/publication_route_memory_library.md",
                "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
            ],
            mapping_explanation=(
                "New repo-tracked knowledge contracts should land in the standard knowledge slot; "
                "workspace knowledge packets and memory receipts remain locator-only artifacts."
            ),
        ),
        _physical_skeleton_slot(
            "agent/quality_gates",
            surface_class="quality",
            default_for_new_surfaces=True,
            repo_paths=[
                stage_quality_contract.REPO_PATH,
                "src/med_autoscience/controllers/publication_gate.py",
                "src/med_autoscience/controllers/ai_reviewer_publication_eval.py",
                "src/med_autoscience/controllers/paper_repair_executor.py",
            ],
            mapping_explanation=(
                "New quality contracts should land in the standard quality-gate slot while existing "
                "publication gate, AI reviewer, and repair executor paths remain mapped authority surfaces."
            ),
        ),
        _physical_skeleton_slot(
            "contracts/runtime/domain-handler",
            surface_class="runtime_domain_handler",
            default_for_new_surfaces=False,
            repo_paths=[
                "src/med_autoscience/controllers/owner_route_handoff.py",
                "src/med_autoscience/controllers/opl_provider_ready_adapter.py",
            ],
            mapping_explanation=(
                "Runtime domain handler contracts stay mapped to the current MAS adapter surfaces; new domain "
                "stage, prompt, skill, knowledge, quality, and projection surfaces should use their "
                "standard slots before adding domain handler code."
            ),
        ),
        _physical_skeleton_slot(
            "contracts/runtime/projection_builders",
            surface_class="projection",
            default_for_new_surfaces=True,
            repo_paths=[
                "src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py",
                "src/med_autoscience/controllers/real_paper_autonomy_soak_inventory.py",
            ],
            mapping_explanation=(
                "New projection surfaces should land in the standard projection-builder slot; current "
                "product-entry and soak inventory builders remain the active repo mapping."
            ),
        ),
        _physical_skeleton_slot(
            "runtime/artifact_locator",
            surface_class="artifact_locator",
            default_for_new_surfaces=False,
            locator_refs=["/product_entry_manifest/workspace_runtime_artifact_root_locator"],
            status="locator_only_no_artifact_body",
            mapping_explanation=(
                "Runtime artifacts are exposed through locator refs only; repo source must not add "
                "artifact bodies under this slot."
            ),
        ),
        _physical_skeleton_slot(
            "artifacts",
            surface_class="artifact_body",
            default_for_new_surfaces=False,
            locator_refs=["/product_entry_manifest/workspace_runtime_artifact_root_locator"],
            status="forbidden_repo_artifact_body",
            mapping_explanation=(
                "Real workspace artifacts are forbidden in the repo skeleton and remain discoverable "
                "only through workspace runtime artifact locators."
            ),
        ),
    ]
    return {
        "surface_kind": "standard_domain_agent_physical_skeleton_layout_audit",
        "version": "standard-domain-agent-physical-layout-audit.v1",
        "standard_layout_version": "standard-domain-agent-physical-layout.v1",
        "status": "repo_source_physical_anchors_landed",
        "repo_source_root": "repo:med-autoscience",
        "repo_source_anchor_status": _repo_source_anchor_status(),
        "repo_tracks_real_workspace_artifacts": False,
        "artifact_body_included": False,
        "workspace_runtime_artifact_root_locator_ref": "/product_entry_manifest/workspace_runtime_artifact_root_locator",
        "default_placement_policy": {
            "new_repo_source_surfaces_follow_standard_slots": True,
            "preserve_current_locator_boundaries": True,
            "destructive_directory_reorganization_allowed": False,
            "real_workspace_artifacts_remain_locator_only": True,
        },
        "slots": slots,
        "summary": {
            "mapped_slot_count": sum(1 for slot in slots if slot["status"] == "mapped_to_existing_repo_paths"),
            "locator_only_slot_count": sum(1 for slot in slots if slot["locator_refs"] and not slot["repo_paths"]),
            "missing_required_slot_count": sum(1 for slot in slots if slot["status"] == "missing_required_repo_path"),
            "forbidden_repo_artifact_body": any(slot["status"] == "forbidden_repo_artifact_body" for slot in slots),
        },
    }

def _physical_skeleton_slot(
    slot_id: str,
    *,
    surface_class: str,
    default_for_new_surfaces: bool,
    repo_paths: list[str] | None = None,
    locator_refs: list[str] | None = None,
    status: str | None = None,
    mapping_explanation: str,
) -> dict[str, Any]:
    paths = list(repo_paths or [])
    return {
        "slot_id": slot_id,
        "surface_class": surface_class,
        "status": status or ("mapped_to_existing_repo_paths" if paths else "missing_required_repo_path"),
        "repo_paths": paths,
        "locator_refs": list(locator_refs or []),
        "default_for_new_surfaces": default_for_new_surfaces,
        "mapping_explanation": mapping_explanation,
        "artifact_body_included": False,
        "repo_tracks_real_workspace_artifacts": False,
    }


def _repo_source_anchor_status() -> dict[str, Any]:
    anchors = [
        {
            "anchor_id": anchor_id,
            "repo_path": repo_path,
            "exists": (REPO_ROOT / repo_path).exists(),
            "body_included": False,
            "artifact_body_allowed": False,
        }
        for anchor_id, repo_path in REPO_SOURCE_ANCHORS.items()
    ]
    return {
        "surface_kind": "mas_standard_skeleton_repo_source_anchor_status",
        "version": "mas-standard-skeleton-repo-source-anchor-status.v1",
        "status": "landed" if all(anchor["exists"] for anchor in anchors) else "typed_blocker",
        "required_anchor_ids": list(REPO_SOURCE_ANCHORS),
        "anchors": anchors,
        "missing_anchor_ids": [anchor["anchor_id"] for anchor in anchors if anchor["exists"] is not True],
        "workspace_artifacts_locator_only": True,
    }
