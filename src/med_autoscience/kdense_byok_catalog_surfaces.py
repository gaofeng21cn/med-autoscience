from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.external_learning_progress_workers import (
    FORBIDDEN_WRITES,
    KDENSE_FRAMEWORK_ID,
    KDENSE_SOURCE_CONTRACT_REF,
)


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_kdense_byok_catalog_surfaces"
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / KDENSE_SOURCE_CONTRACT_REF


def build_kdense_byok_catalog_surfaces(
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = _load_contract()
    kdense = _mapping(_mapping(contract.get("source_evidence")).get("kdense_byok"))
    skills = _mapping(
        _mapping(contract.get("source_evidence")).get("scientific_agent_skills")
    )
    planned_items = _planned_items_by_id(contract)
    direct_candidates = _direct_candidates_by_mode(contract)
    allowlist = _allowlist(contract)
    context = _dispatch_context(dispatch)

    payload = _refs_only_surface(
        surface_kind=SURFACE_KIND,
        surface_id="kdense_byok_catalog_surfaces",
    )
    payload.update(
        {
            "schema_version": SCHEMA_VERSION,
            "framework_id": KDENSE_FRAMEWORK_ID,
            "source_contract_ref": KDENSE_SOURCE_CONTRACT_REF,
            "source_pin": {
                "kdense_byok_repo": kdense.get("repo"),
                "kdense_byok_commit": kdense.get("inspected_head_commit"),
                "kdense_byok_release": kdense.get("latest_release_tag"),
                "scientific_agent_skills_repo": skills.get("repo"),
                "scientific_agent_skills_commit": skills.get(
                    "inspected_head_commit"
                ),
            },
            "current_owner_action": context["current_owner_action"],
            "diagnostic": context["diagnostic"],
            "surfaces": {
                "stagecraft_recipe_catalog": _stagecraft_surface(
                    kdense=kdense,
                    candidate=direct_candidates.get("parse_as_stagecraft_recipe_seed"),
                    planned_item=planned_items.get("workflow_templates_to_stagecraft"),
                    allowlist=allowlist,
                ),
                "atlas_source_ref_catalog": _atlas_surface(
                    kdense=kdense,
                    candidate=direct_candidates.get("parse_as_atlas_source_ref_seed"),
                    planned_item=planned_items.get("database_catalog_to_atlas"),
                ),
                "codex_specialist_roster": _specialist_roster_surface(
                    kdense=kdense,
                    skills=skills,
                    allowlist=allowlist,
                    planned_item=planned_items.get("codex_specialist_roster"),
                ),
                "workspace_artifact_preview": _workspace_preview_surface(
                    kdense=kdense,
                    planned_item=planned_items.get(
                        "artifact_workspace_preview_file_tree"
                    ),
                ),
            },
        }
    )
    return payload


def _stagecraft_surface(
    *,
    kdense: Mapping[str, Any],
    candidate: Mapping[str, Any] | None,
    planned_item: Mapping[str, Any] | None,
    allowlist: list[Mapping[str, Any]],
) -> dict[str, Any]:
    surface = _refs_only_surface(
        surface_kind="stagecraft_recipe_catalog_surface",
        surface_id="stagecraft_recipe_catalog",
    )
    surface.update(
        {
            "template_count": kdense.get("workflow_template_count"),
            "source_ref": _text(_mapping(candidate).get("source_ref")),
            "landing_status": _text(_mapping(planned_item).get("landing_status")),
            "completion_gate": _text(_mapping(planned_item).get("completion_gate")),
            "required_refs": [
                "workflow_template_ref",
                "source_provenance_ref",
                "typed_work_unit_input_ref",
                "stage_policy_ref",
            ],
            "placeholder_schema": {
                "source_fields": [
                    "prompt",
                    "placeholders",
                    "requiresFiles",
                    "suggestedSkills",
                ],
                "required_fields": [
                    "goal",
                    "input_refs",
                    "allowed_writes",
                    "forbidden_authority_flags",
                ],
                "body_included": False,
            },
            "suggested_capability_hints": [
                {
                    "skill_id": _text(item.get("skill_id")),
                    "module_id": _text(item.get("module_id")),
                    "use_when": _text(item.get("use_when")),
                }
                for item in allowlist
            ],
            "execution_authority": False,
        }
    )
    return surface


def _atlas_surface(
    *,
    kdense: Mapping[str, Any],
    candidate: Mapping[str, Any] | None,
    planned_item: Mapping[str, Any] | None,
) -> dict[str, Any]:
    surface = _refs_only_surface(
        surface_kind="atlas_source_ref_catalog_surface",
        surface_id="atlas_source_ref_catalog",
    )
    surface.update(
        {
            "source_ref_count": kdense.get("database_ref_count"),
            "source_ref": _text(_mapping(candidate).get("source_ref")),
            "landing_status": _text(_mapping(planned_item).get("landing_status")),
            "completion_gate": _text(_mapping(planned_item).get("completion_gate")),
            "endpoint_provenance": {
                "required": True,
                "required_fields": [
                    "endpoint",
                    "params",
                    "access_date",
                    "count_reconciliation",
                    "local_filters",
                ],
            },
            "access_date_required": True,
            "source_readiness_authority": False,
        }
    )
    return surface


def _specialist_roster_surface(
    *,
    kdense: Mapping[str, Any],
    skills: Mapping[str, Any],
    allowlist: list[Mapping[str, Any]],
    planned_item: Mapping[str, Any] | None,
) -> dict[str, Any]:
    surface = _refs_only_surface(
        surface_kind="codex_specialist_roster_surface",
        surface_id="codex_specialist_roster",
    )
    surface.update(
        {
            "upstream_specialist_count": kdense.get("scientific_specialist_count"),
            "allowlist_source_count": skills.get("skill_dir_count"),
            "role_descriptor_count": len(allowlist),
            "landing_status": _text(_mapping(planned_item).get("landing_status")),
            "completion_gate": _text(_mapping(planned_item).get("completion_gate")),
            "independent_invocation_required": True,
            "reviewer_receipt_candidate_only": True,
            "role_descriptors": [
                {
                    "role_id": f"codex-specialist:{_text(item.get('skill_id'))}",
                    "skill_id": _text(item.get("skill_id")),
                    "source_ref": _text(item.get("source_ref")),
                    "module_id": _text(item.get("module_id")),
                    "owner_surface": _text(item.get("owner_surface")),
                    "use_when": _text(item.get("use_when")),
                    "completion_gate": _text(item.get("completion_gate")),
                    "independent_invocation_required": True,
                    "reviewer_receipt_candidate_only": True,
                    "body_included": False,
                }
                for item in allowlist
            ],
        }
    )
    return surface


def _workspace_preview_surface(
    *,
    kdense: Mapping[str, Any],
    planned_item: Mapping[str, Any] | None,
) -> dict[str, Any]:
    surface = _refs_only_surface(
        surface_kind="workspace_artifact_preview_surface",
        surface_id="workspace_artifact_preview",
    )
    inspected_refs = [
        ref
        for ref in _list_text(kdense.get("inspected_refs"))
        if ref
        in {
            "web/src/components/file-preview-panel.tsx",
            "web/src/components/latex-editor.tsx",
            "web/src/components/tool-activity.tsx",
        }
    ]
    surface.update(
        {
            "source_refs": inspected_refs,
            "landing_status": _text(_mapping(planned_item).get("landing_status")),
            "completion_gate": _text(_mapping(planned_item).get("completion_gate")),
            "manifest_ref_required": True,
            "checksum_ref_required": True,
            "preview_ref_required": True,
            "manifest_ref_family": "artifact_manifest_ref",
            "checksum_ref_family": "artifact_checksum_ref",
            "preview_ref_family": "artifact_preview_ref",
            "artifact_authority": False,
        }
    )
    return surface


def _refs_only_surface(*, surface_kind: str, surface_id: str) -> dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "surface_id": surface_id,
        "refs_only": True,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "body_included": False,
        "allowed_writes": [],
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "forbidden_authority": {
            "can_write_study_truth": False,
            "can_write_source_truth": False,
            "can_write_paper_body": False,
            "can_write_artifact_body": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_current_package": False,
            "can_sign_owner_receipt": False,
            "can_create_typed_blocker": False,
            "can_create_human_gate": False,
            "can_authorize_source_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_submission_readiness": False,
            "can_authorize_provider_admission": False,
            "can_close_stage": False,
        },
    }


def _load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _planned_items_by_id(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        _text(item.get("item_id")): item
        for item in _list_mapping(contract.get("planned_learning_items"))
        if _text(item.get("item_id"))
    }


def _direct_candidates_by_mode(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        _text(item.get("reuse_mode")): item
        for item in _list_mapping(contract.get("direct_reuse_candidates"))
        if _text(item.get("reuse_mode"))
    }


def _allowlist(contract: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    policy = _mapping(contract.get("external_skill_library_policy"))
    return _list_mapping(policy.get("selected_allowlist"))


def _dispatch_context(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    dispatch_mapping = _mapping(dispatch)
    action_id = _dispatch_text(dispatch_mapping, "action_id")
    return {
        "candidate_dispatch_id": action_id or "unknown_dispatch",
        "current_owner_action": _current_owner_action(dispatch_mapping),
        "diagnostic": (
            {"reason": "missing_or_invalid_dispatch"} if not dispatch_mapping else None
        ),
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, str | None]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    return {
        "action_type": _dispatch_text(dispatch, "action_type"),
        "action_id": _dispatch_text(dispatch, "action_id"),
        "owner": _text(owner_route.get("owner")) or _dispatch_text(dispatch, "owner"),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _dispatch_text(dispatch: Mapping[str, Any], key: str) -> str | None:
    return _text(dispatch.get(key)) or _text(_mapping(dispatch.get("source_action")).get(key))


def _list_mapping(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _list_text(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for text in (_text(item) for item in value) if text]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_kdense_byok_catalog_surfaces",
]
