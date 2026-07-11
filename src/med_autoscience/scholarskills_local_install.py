from __future__ import annotations

from pathlib import Path
import shlex
from typing import Any


SCHOLARSKILLS_DOMAIN = "mas-scholar-skills"
SCHOLARSKILLS_SKILL_ID = "mas-scholar-skills"
SCHOLARSKILLS_DEFAULT_SKILL_IDS = (
    "mas-scholar-skills",
    "medical-research-lit",
    "medical-manuscript-writing",
    "medical-manuscript-review",
    "medical-figure-design",
    "medical-figure-style",
    "medical-figure-composer",
    "medical-statistical-review",
    "medical-table-design",
    "medical-submission-prep",
    "medical-data-governance",
)
SCHOLARSKILLS_OPTIONAL_ADVANCED_SKILL_IDS = (
    "medical-structural-biology",
    "medical-protein-design",
    "medical-genomics-foundation-models",
    "medical-single-cell-modeling",
    "medical-indication-dossier",
    "research-pdf-evidence-explorer",
    "scientific-compute-runner",
)
SCHOLARSKILLS_OPTIONAL_ADVANCED_ROUTER_SKILL_IDS = (
    "medical-advanced-biomed-router",
)
SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_ROUTER_SKILL_IDS = (
    "medical-methodology-planner",
    "medical-evidence-integrity-reviewer",
    "medical-publication-routeback-reviewer",
)
SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_SKILL_IDS = (
    "medical-protocol-and-sap-planner",
    "medical-cohort-phenotyping",
    "medical-evidence-synthesis-and-claim-map",
    "medical-reference-integrity-auditor",
    "medical-rebuttal-strategy",
    "medical-display-qc",
    "medical-causal-inference-plan",
    "medical-survival-analysis-plan",
    "medical-risk-model-transportability-reviewer",
    "medical-registry-atlas-story-architect",
    "medical-research-portfolio-memory-curator",
    "medical-display-regression-debugger",
    "medical-data-freeze-and-analysis-readiness-reviewer",
)
SCHOLARSKILLS_RETIRED_OPTIONAL_SKILL_REDIRECTS = {
    "medical-evidence-gap-triage-reviewer": {
        "covered_by": "medical-evidence-integrity-reviewer",
        "mode": "evidence_gap_triage",
    },
    "medical-methodology-routeback-reviewer": {
        "covered_by": "medical-publication-routeback-reviewer",
        "mode": "methodology_routeback",
    },
    "medical-owner-gate-handoff-reviewer": {
        "covered_by": "medical-publication-routeback-reviewer",
        "mode": "owner_gate_handoff",
    },
    "medical-publication-strategy-memory-curator": {
        "covered_by": "medical-research-portfolio-memory-curator",
        "mode": "publication_strategy_memory",
    },
}
SCHOLARSKILLS_OPTIONAL_SKILL_IDS = (
    *SCHOLARSKILLS_OPTIONAL_ADVANCED_ROUTER_SKILL_IDS,
    *SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_ROUTER_SKILL_IDS,
    *SCHOLARSKILLS_OPTIONAL_ADVANCED_SKILL_IDS,
    *SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_SKILL_IDS,
)
SCHOLARSKILLS_SKILL_LOCAL_HELPER_SKILL_IDS = (
    "medical-research-lit",
    "medical-manuscript-writing",
    "medical-manuscript-review",
    "medical-figure-style",
    "medical-figure-composer",
    "medical-statistical-review",
    "medical-table-design",
    "medical-submission-prep",
    "medical-data-governance",
    "medical-protocol-and-sap-planner",
    "medical-cohort-phenotyping",
    "medical-evidence-synthesis-and-claim-map",
    "medical-reference-integrity-auditor",
    "medical-rebuttal-strategy",
    "medical-display-qc",
    "medical-causal-inference-plan",
    "medical-survival-analysis-plan",
    "medical-risk-model-transportability-reviewer",
    "medical-registry-atlas-story-architect",
    "medical-display-regression-debugger",
    "medical-data-freeze-and-analysis-readiness-reviewer",
    "medical-structural-biology",
    "medical-protein-design",
    "medical-genomics-foundation-models",
    "medical-single-cell-modeling",
    "medical-indication-dossier",
    "research-pdf-evidence-explorer",
    "scientific-compute-runner",
)
SCHOLARSKILLS_SOURCE_REPO_REF = "external:mas-scholar-skills"
SCHOLARSKILLS_LOCAL_INSTALL_READBACK_REF = "readback:mas_scholarskills_local_install"
SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_STATUS = "physically_retired"
SCHEMA_VERSION = 1


def build_scholarskills_sync_command(*, scope: str, target: str) -> dict[str, Any]:
    if scope == "workspace":
        target_flag = "--target-workspace"
    elif scope == "quest":
        target_flag = "--target-quest"
    else:
        raise ValueError(f"unsupported ScholarSkills install scope: {scope}")
    argv = [
        "opl",
        "connect",
        "sync-skills",
        "--domain",
        SCHOLARSKILLS_DOMAIN,
        "--scope",
        scope,
        target_flag,
        target,
        "--json",
    ]
    return {
        "argv": argv,
        "command": shlex.join(argv),
        "effect": "install_codex_skill_to_local_workspace_or_quest",
        "writes_authority": False,
    }


def build_scholarskills_local_install_template() -> dict[str, Any]:
    return {
        "surface_kind": "mas_scholarskills_local_install_template",
        "schema_version": SCHEMA_VERSION,
        "domain": SCHOLARSKILLS_DOMAIN,
        "skill_id": SCHOLARSKILLS_SKILL_ID,
        "synced_skill_ids": list(SCHOLARSKILLS_DEFAULT_SKILL_IDS),
        "optional_skill_ids": list(SCHOLARSKILLS_OPTIONAL_SKILL_IDS),
        "optional_skill_policy": _optional_skill_policy(),
        "retired_optional_skill_redirects": _retired_optional_skill_redirects(),
        "skill_local_deterministic_helper_policy": _skill_local_deterministic_helper_policy(),
        "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
        "install_owner": "one-person-lab",
        "workspace": {
            "scope": "workspace",
            "target_skill_path_template": f"<workspace_root>/.codex/skills/{SCHOLARSKILLS_SKILL_ID}",
            "target_skill_path_templates": _target_skill_path_templates(
                "<workspace_root>",
                skill_ids=SCHOLARSKILLS_DEFAULT_SKILL_IDS,
            ),
            "optional_target_skill_path_templates": _target_skill_path_templates(
                "<workspace_root>",
                skill_ids=SCHOLARSKILLS_OPTIONAL_SKILL_IDS,
            ),
            "sync_command_template": build_scholarskills_sync_command(
                scope="workspace",
                target="<workspace_root>",
            ),
        },
        "quest": {
            "scope": "quest",
            "target_skill_path_template": f"<quest_root>/.codex/skills/{SCHOLARSKILLS_SKILL_ID}",
            "target_skill_path_templates": _target_skill_path_templates(
                "<quest_root>",
                skill_ids=SCHOLARSKILLS_DEFAULT_SKILL_IDS,
            ),
            "optional_target_skill_path_templates": _target_skill_path_templates(
                "<quest_root>",
                skill_ids=SCHOLARSKILLS_OPTIONAL_SKILL_IDS,
            ),
            "sync_command_template": build_scholarskills_sync_command(
                scope="quest",
                target="<quest_root>",
            ),
        },
        "mas_program_repo_mirror": _mas_program_repo_mirror(),
        "mas_program_repo_plugin_is_execution_source": False,
        "authority_boundary": _authority_boundary(),
    }


def build_scholarskills_local_install_readback(
    *,
    workspace_root: Path | str,
    quest_root: Path | str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    workspace_skill_path = _target_skill_path(resolved_workspace_root)
    readback: dict[str, Any] = {
        "surface_kind": "mas_scholarskills_local_install_readback",
        "schema_version": SCHEMA_VERSION,
        "domain": SCHOLARSKILLS_DOMAIN,
        "skill_id": SCHOLARSKILLS_SKILL_ID,
        "synced_skill_ids": list(SCHOLARSKILLS_DEFAULT_SKILL_IDS),
        "optional_skill_ids": list(SCHOLARSKILLS_OPTIONAL_SKILL_IDS),
        "optional_skill_policy": _optional_skill_policy(),
        "retired_optional_skill_redirects": _retired_optional_skill_redirects(),
        "skill_local_deterministic_helper_policy": _skill_local_deterministic_helper_policy(),
        "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
        "install_owner": "one-person-lab",
        "status": "command_shape_ready",
        "apply": bool(apply),
        "workspace": {
            "scope": "workspace",
            "target_workspace_root": str(resolved_workspace_root),
            "target_skill_path": str(workspace_skill_path),
            "target_skill_paths": {
                skill_id: str(_target_skill_path(resolved_workspace_root, skill_id=skill_id))
                for skill_id in SCHOLARSKILLS_DEFAULT_SKILL_IDS
            },
            "optional_target_skill_paths": {
                skill_id: str(_target_skill_path(resolved_workspace_root, skill_id=skill_id))
                for skill_id in SCHOLARSKILLS_OPTIONAL_SKILL_IDS
            },
            "sync_command": build_scholarskills_sync_command(
                scope="workspace",
                target=str(resolved_workspace_root),
            ),
        },
        "quest": {
            "scope": "quest",
            "locator_status": "explicit_quest_root_required",
            "sync_command_template": build_scholarskills_sync_command(
                scope="quest",
                target="<quest_root>",
            ),
        },
        "mas_program_repo_mirror": _mas_program_repo_mirror(),
        "mas_program_repo_plugin_is_execution_source": False,
        "authority_boundary": _authority_boundary(),
    }
    if quest_root is not None:
        resolved_quest_root = Path(quest_root).expanduser().resolve()
        readback["quest"].update(
            {
                "target_quest_root": str(resolved_quest_root),
                "target_skill_path": str(_target_skill_path(resolved_quest_root)),
                "target_skill_paths": {
                    skill_id: str(_target_skill_path(resolved_quest_root, skill_id=skill_id))
                    for skill_id in SCHOLARSKILLS_DEFAULT_SKILL_IDS
                },
                "optional_target_skill_paths": {
                    skill_id: str(_target_skill_path(resolved_quest_root, skill_id=skill_id))
                    for skill_id in SCHOLARSKILLS_OPTIONAL_SKILL_IDS
                },
                "sync_command": build_scholarskills_sync_command(
                    scope="quest",
                    target=str(resolved_quest_root),
                ),
            }
        )
    return readback


def build_scholarskills_local_install_readback_for_profile(
    profile: Any,
    *,
    quest_root: Path | str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    return build_scholarskills_local_install_readback(
        workspace_root=Path(profile.workspace_root),
        quest_root=quest_root,
        apply=apply,
    )


def _target_skill_path(root: Path, *, skill_id: str = SCHOLARSKILLS_SKILL_ID) -> Path:
    return root / ".codex" / "skills" / skill_id


def _target_skill_path_templates(root_token: str, *, skill_ids: tuple[str, ...]) -> dict[str, str]:
    return {skill_id: f"{root_token}/.codex/skills/{skill_id}" for skill_id in skill_ids}


def _optional_skill_policy() -> dict[str, Any]:
    return {
        "surface": "optional_advanced_and_medical_method_specialist_skills",
        "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
        "source_contract_refs": [
            "external:mas-scholar-skills/contracts/"
            "scholar-skills-capability-modules.json#/codex_skill_exposure_policy/optional_router_skill_ids",
            "external:mas-scholar-skills/contracts/"
            "scholar-skills-capability-modules.json#/advanced_specialist_pack_policy",
            "external:mas-scholar-skills/contracts/"
            "scholar-skills-capability-modules.json#/medical_method_specialist_pack_policy",
        ],
        "optional_advanced_router_skill_ids": list(SCHOLARSKILLS_OPTIONAL_ADVANCED_ROUTER_SKILL_IDS),
        "optional_medical_method_router_skill_ids": list(
            SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_ROUTER_SKILL_IDS
        ),
        "optional_advanced_skill_ids": list(SCHOLARSKILLS_OPTIONAL_ADVANCED_SKILL_IDS),
        "optional_medical_method_skill_ids": list(SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_SKILL_IDS),
        "materialization_owner": "one-person-lab",
        "sync_path": "opl_connect_source_materialization",
        "refs_only": True,
        "body_included": False,
        "default_core": False,
        "missing_optional_skills_block_mas_ordinary_progress": False,
        "writes_authority": False,
    }


def _retired_optional_skill_redirects() -> dict[str, dict[str, Any]]:
    return {
        skill_id: {
            **redirect,
            "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
            "redirect_only": True,
            "exposed_as_optional_skill": False,
            "body_included": False,
            "writes_authority": False,
        }
        for skill_id, redirect in SCHOLARSKILLS_RETIRED_OPTIONAL_SKILL_REDIRECTS.items()
    }


def _skill_local_deterministic_helper_policy() -> dict[str, Any]:
    return {
        "surface": "skill_local_deterministic_helpers",
        "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
        "source_contract_ref": (
            "external:mas-scholar-skills/contracts/"
            "scholar-skills-capability-modules.json#/professional_skill_quality_upgrade_policy"
        ),
        "helper_file_name": "kernel.py",
        "expected_helper_skill_ids": list(SCHOLARSKILLS_SKILL_LOCAL_HELPER_SKILL_IDS),
        "materialization_owner": "one-person-lab",
        "sync_path": "opl_connect_source_materialization",
        "refs_only": True,
        "helper_body_included": False,
        "default_core": False,
        "missing_helpers_block_mas_ordinary_progress": False,
        "helpers_can_write_authority": False,
    }


def _mas_program_repo_mirror() -> dict[str, Any]:
    return {
        "default_execution_source": False,
        "paper_execution_available": False,
        "physical_status": "retired_absent",
        "must_exist_in_mas_repo": False,
        "role": "tombstone_only",
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "writes_yang_authority": False,
        "writes_runtime_authority": False,
        "writes_study_truth": False,
        "writes_publication_eval": False,
        "writes_controller_decisions": False,
        "writes_owner_receipt": False,
        "writes_typed_blocker": False,
        "writes_human_gate": False,
        "writes_runtime_queue": False,
        "writes_provider_attempt": False,
        "writes_mas_program_repo_plugin": False,
        "owner_gated_refs_consumption": True,
    }


__all__ = [
    "SCHOLARSKILLS_DOMAIN",
    "SCHOLARSKILLS_LOCAL_INSTALL_READBACK_REF",
    "SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_STATUS",
    "SCHOLARSKILLS_DEFAULT_SKILL_IDS",
    "SCHOLARSKILLS_OPTIONAL_ADVANCED_ROUTER_SKILL_IDS",
    "SCHOLARSKILLS_OPTIONAL_ADVANCED_SKILL_IDS",
    "SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_ROUTER_SKILL_IDS",
    "SCHOLARSKILLS_OPTIONAL_MEDICAL_METHOD_SKILL_IDS",
    "SCHOLARSKILLS_OPTIONAL_SKILL_IDS",
    "SCHOLARSKILLS_RETIRED_OPTIONAL_SKILL_REDIRECTS",
    "SCHOLARSKILLS_SKILL_LOCAL_HELPER_SKILL_IDS",
    "SCHOLARSKILLS_SKILL_ID",
    "SCHOLARSKILLS_SOURCE_REPO_REF",
    "build_scholarskills_local_install_readback",
    "build_scholarskills_local_install_readback_for_profile",
    "build_scholarskills_local_install_template",
    "build_scholarskills_sync_command",
]
