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
    "medical-statistical-review",
    "medical-table-design",
    "medical-submission-prep",
    "medical-data-governance",
)
SCHOLARSKILLS_SOURCE_REPO_REF = "external:mas-scholar-skills"
SCHOLARSKILLS_LOCAL_INSTALL_READBACK_REF = "readback:mas_scholarskills_local_install"
SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_PATH = "plugins/mas-scholar-skills"
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
        "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
        "install_owner": "one-person-lab",
        "workspace": {
            "scope": "workspace",
            "target_skill_path_template": f"<workspace_root>/.codex/skills/{SCHOLARSKILLS_SKILL_ID}",
            "target_skill_path_templates": {
                skill_id: f"<workspace_root>/.codex/skills/{skill_id}"
                for skill_id in SCHOLARSKILLS_DEFAULT_SKILL_IDS
            },
            "sync_command_template": build_scholarskills_sync_command(
                scope="workspace",
                target="<workspace_root>",
            ),
        },
        "quest": {
            "scope": "quest",
            "target_skill_path_template": f"<quest_root>/.codex/skills/{SCHOLARSKILLS_SKILL_ID}",
            "target_skill_path_templates": {
                skill_id: f"<quest_root>/.codex/skills/{skill_id}"
                for skill_id in SCHOLARSKILLS_DEFAULT_SKILL_IDS
            },
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
    runtime_quests_root: Path | str,
    quest_root: Path | str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_runtime_quests_root = Path(runtime_quests_root).expanduser().resolve()
    workspace_skill_path = _target_skill_path(resolved_workspace_root)
    readback: dict[str, Any] = {
        "surface_kind": "mas_scholarskills_local_install_readback",
        "schema_version": SCHEMA_VERSION,
        "domain": SCHOLARSKILLS_DOMAIN,
        "skill_id": SCHOLARSKILLS_SKILL_ID,
        "synced_skill_ids": list(SCHOLARSKILLS_DEFAULT_SKILL_IDS),
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
            "sync_command": build_scholarskills_sync_command(
                scope="workspace",
                target=str(resolved_workspace_root),
            ),
        },
        "quest": {
            "scope": "quest",
            "runtime_quests_root": str(resolved_runtime_quests_root),
            "target_skill_path_template": str(
                resolved_runtime_quests_root / "<quest_id>" / ".codex" / "skills" / SCHOLARSKILLS_SKILL_ID
            ),
            "target_skill_path_templates": {
                skill_id: str(resolved_runtime_quests_root / "<quest_id>" / ".codex" / "skills" / skill_id)
                for skill_id in SCHOLARSKILLS_DEFAULT_SKILL_IDS
            },
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
        runtime_quests_root=Path(profile.runtime_root),
        quest_root=quest_root,
        apply=apply,
    )


def _target_skill_path(root: Path, *, skill_id: str = SCHOLARSKILLS_SKILL_ID) -> Path:
    return root / ".codex" / "skills" / skill_id


def _mas_program_repo_mirror() -> dict[str, Any]:
    return {
        "path": SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_PATH,
        "role": "dev_review_only_or_retired",
        "default_execution_source": False,
        "paper_execution_available": False,
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
    "SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_PATH",
    "SCHOLARSKILLS_DEFAULT_SKILL_IDS",
    "SCHOLARSKILLS_SKILL_ID",
    "SCHOLARSKILLS_SOURCE_REPO_REF",
    "build_scholarskills_local_install_readback",
    "build_scholarskills_local_install_readback_for_profile",
    "build_scholarskills_local_install_template",
    "build_scholarskills_sync_command",
]
