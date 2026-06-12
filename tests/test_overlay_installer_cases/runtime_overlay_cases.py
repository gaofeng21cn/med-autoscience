from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_overlay_installer_cases.helpers import (
    FORBIDDEN_AUTOFIGURE_PROMPT,
    OVERLAY_PREFIX,
    read_manifest,
    read_stage_packet_template,
    stage_packet_path,
    write_runtime_skill,
    write_skill,
    write_system_prompt,
)


def test_materialize_runtime_medical_overlay_can_seed_missing_runtime_overlay_from_repo(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    repo_root = tmp_path / "med-deepscientist"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    workspace_root = tmp_path / "workspace"
    write_runtime_skill(repo_root, "write", "runtime write\n")
    write_runtime_skill(repo_root, "journal-resolution", "runtime journal\n")

    result = module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        med_deepscientist_repo_root=repo_root,
        skill_ids=("write",),
    )

    assert result["materialized_surface_count"] == 1
    assert (
        quest_root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-write" / ".med_autoscience_overlay.json"
    ).exists()


def test_materialize_runtime_medical_overlay_ignores_legacy_worktrees(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    repo_root = tmp_path / "med-deepscientist"
    write_runtime_skill(repo_root, "write", "# DeepScientist write\n")

    module.install_medical_overlay(
        quest_root=workspace_root,
        med_deepscientist_repo_root=repo_root,
        skill_ids=("write",),
    )
    write_skill(worktree_root / ".codex" / "skills", "write", "upstream write\n")

    result = module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        med_deepscientist_repo_root=repo_root,
        skill_ids=("write",),
    )

    assert result["materialized_surface_count"] == 1
    assert not (
        worktree_root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-write" / ".med_autoscience_overlay.json"
    ).exists()

    audit = module.audit_runtime_medical_overlay(
        quest_root=quest_root,
        skill_ids=("write",),
    )

    assert audit["all_roots_ready"] is True
    by_surface = {Path(item["runtime_root"]).name: item for item in audit["surfaces"]}
    assert by_surface["q001"]["all_targets_ready"] is True
    assert "paper-run-1" not in by_surface


def test_materialize_runtime_medical_overlay_materializes_required_companion_blocks(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    module.install_medical_overlay(
        quest_root=workspace_root,
        skill_ids=("write",),
    )
    result = module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )

    assert result["materialized_surface_count"] == 1
    assert stage_packet_path(quest_root, "write").read_text(encoding="utf-8") == read_stage_packet_template()


def test_audit_runtime_medical_overlay_reports_missing_companion_block(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    module.install_medical_overlay(
        quest_root=workspace_root,
        skill_ids=("write",),
    )
    module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )
    missing_stage_packet = stage_packet_path(quest_root, "write")
    missing_stage_packet.unlink(missing_ok=False)

    result = module.audit_runtime_medical_overlay(
        quest_root=quest_root,
        skill_ids=("write",),
    )

    assert result["all_roots_ready"] is False
    surface = result["surfaces"][0]
    assert surface["all_targets_ready"] is False
    target = surface["status"]["targets"][0]
    assert target["status"] == "drifted"
    assert target["companion_files"][0]["status"] == "missing"


def test_materialize_runtime_medical_overlay_does_not_mutate_legacy_mds_skills_without_home_global_writes(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    home = tmp_path / "home"
    home_skills_root = home / ".codex" / "skills"
    repo_root = tmp_path / "med-deepscientist"
    write_runtime_skill(repo_root, "write", "# DeepScientist write\n")
    write_runtime_skill(repo_root, "optimize", "# DeepScientist optimize\n")
    (repo_root / "src" / "skills" / "write" / "templates").mkdir(parents=True)
    (repo_root / "src" / "skills" / "write" / "templates" / "journal.md").write_text(
        "venue template\n",
        encoding="utf-8",
    )

    module.install_medical_overlay(
        quest_root=workspace_root,
        med_deepscientist_repo_root=repo_root,
        skill_ids=("write",),
    )
    for skill_id in ("write", "optimize"):
        legacy_skill = workspace_root / ".codex" / "skills" / f"deepscientist-{skill_id}" / "SKILL.md"
        legacy_skill.parent.mkdir(parents=True, exist_ok=True)
        legacy_skill.write_text(f"# DeepScientist {skill_id}\n", encoding="utf-8")
    result = module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        home=home,
        med_deepscientist_repo_root=repo_root,
        skill_ids=("write",),
    )

    assert result["materialized_surface_count"] == 1
    assert "authoritative_legacy_mds_skill_cleanup" not in result
    for root in (workspace_root, quest_root):
        for skill_id in ("write", "journal-resolution"):
            skill_root = root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-{skill_id}"
            assert (skill_root / "SKILL.md").exists()
            assert read_manifest(skill_root)["scope"] == "quest"
    assert sorted(path.name for path in (workspace_root / ".codex" / "skills").glob("deepscientist-*")) == [
        "deepscientist-optimize",
        "deepscientist-write",
    ]
    assert not any((quest_root / ".codex" / "skills").glob("deepscientist-*"))
    assert not home_skills_root.exists()


def test_materialize_runtime_medical_overlay_ignores_stale_legacy_worktree_manifest_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"

    module.install_medical_overlay(
        quest_root=workspace_root,
        skill_ids=("write",),
    )
    module.reapply_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )

    quest_skill_root = quest_root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-write"
    worktree_skill_root = worktree_root / ".codex" / "skills" / f"{OVERLAY_PREFIX}-write"
    worktree_skill_root.mkdir(parents=True, exist_ok=True)
    (worktree_skill_root / "SKILL.md").write_text(
        (quest_skill_root / "SKILL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (worktree_skill_root / ".med_autoscience_overlay.json").write_text(
        (quest_skill_root / ".med_autoscience_overlay.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )

    assert result["materialized_surface_count"] == 1
    manifest = read_manifest(worktree_skill_root)
    assert manifest["quest_root"] == str(quest_root)
    assert manifest["target_root"] == str(quest_skill_root)
    assert manifest["skill_path"] == str(quest_skill_root / "SKILL.md")

    audit = module.audit_runtime_medical_overlay(
        quest_root=quest_root,
        skill_ids=("write",),
    )

    assert audit["all_roots_ready"] is True
    by_surface = {Path(item["runtime_root"]).name: item for item in audit["surfaces"]}
    assert "paper-run-1" not in by_surface


def test_materialize_runtime_medical_overlay_sanitizes_forbidden_system_prompt_text(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"

    module.install_medical_overlay(
        quest_root=workspace_root,
        skill_ids=("write",),
    )
    write_system_prompt(
        quest_root,
        f"before\n- For every main paper figure caption, append this clearly separated final sentence: `{FORBIDDEN_AUTOFIGURE_PROMPT}`\nafter\n",
    )
    write_system_prompt(
        worktree_root,
        f"header\n- For every main paper figure caption, append this clearly separated final sentence: `{FORBIDDEN_AUTOFIGURE_PROMPT}`\nfooter\n",
    )

    result = module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )

    assert result["materialized_surface_count"] == 1
    prompt_text = (quest_root / ".codex" / "prompts" / "system.md").read_text(encoding="utf-8")
    assert FORBIDDEN_AUTOFIGURE_PROMPT not in prompt_text
    assert "before" in prompt_text
    legacy_prompt_text = (worktree_root / ".codex" / "prompts" / "system.md").read_text(encoding="utf-8")
    assert FORBIDDEN_AUTOFIGURE_PROMPT in legacy_prompt_text


def test_audit_runtime_medical_overlay_ignores_drifted_legacy_worktree(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"

    module.install_medical_overlay(
        quest_root=workspace_root,
        skill_ids=("write",),
    )
    module.reapply_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )
    write_skill(worktree_root / ".codex" / "skills", "write", "upstream write\n")

    result = module.audit_runtime_medical_overlay(
        quest_root=quest_root,
        skill_ids=("write",),
    )

    assert result["all_roots_ready"] is True
    by_surface = {Path(item["runtime_root"]).name: item for item in result["surfaces"]}
    assert by_surface["q001"]["all_targets_ready"] is True
    assert "paper-run-1" not in by_surface


def test_audit_runtime_medical_overlay_ignores_polluted_legacy_worktree_system_prompt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    workspace_root = tmp_path / "workspace"
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"

    module.install_medical_overlay(
        quest_root=workspace_root,
        skill_ids=("write",),
    )
    worktree_root.mkdir(parents=True, exist_ok=True)
    module.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=workspace_root,
        skill_ids=("write",),
    )
    write_system_prompt(
        worktree_root,
        f"header\n- For every main paper figure caption, append this clearly separated final sentence: `{FORBIDDEN_AUTOFIGURE_PROMPT}`\nfooter\n",
    )

    result = module.audit_runtime_medical_overlay(
        quest_root=quest_root,
        skill_ids=("write",),
    )

    assert result["all_roots_ready"] is True
    by_surface = {Path(item["runtime_root"]).name: item for item in result["surfaces"]}
    assert by_surface["q001"]["all_targets_ready"] is True
    assert by_surface["q001"]["system_prompt_ready"] is True
    assert "paper-run-1" not in by_surface
