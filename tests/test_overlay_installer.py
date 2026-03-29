from __future__ import annotations

import importlib
import json
from pathlib import Path


SKILL_IDS = ("scout", "idea", "decision", "write", "finalize", "journal-resolution")


def write_skill(root: Path, skill_id: str, body: str) -> Path:
    target_root = root / f"deepscientist-{skill_id}"
    target_root.mkdir(parents=True, exist_ok=True)
    skill_path = target_root / "SKILL.md"
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


def read_manifest(target_root: Path) -> dict:
    return json.loads((target_root / ".med_autoscience_overlay.json").read_text(encoding="utf-8"))


def test_overlay_status_reports_not_installed_for_global_targets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    skills_root = home / ".codex" / "skills"
    for skill_id in SKILL_IDS:
        write_skill(skills_root, skill_id, f"upstream {skill_id}\n")

    result = module.describe_medical_overlay(home=home)

    assert result["scope"] == "global"
    assert result["all_targets_ready"] is False
    assert [item["skill_id"] for item in result["targets"]] == [
        "scout",
        "idea",
        "decision",
        "write",
        "finalize",
        "journal-resolution",
    ]
    assert {item["status"] for item in result["targets"]} == {"not_installed"}


def test_overlay_status_uses_quest_local_skill_targets_when_quest_root_provided(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    skills_root = quest_root / ".codex" / "skills"
    for skill_id in SKILL_IDS:
        write_skill(skills_root, skill_id, f"quest {skill_id}\n")

    result = module.describe_medical_overlay(quest_root=quest_root)

    assert result["scope"] == "quest"
    assert result["quest_root"] == str(quest_root)
    assert [Path(item["target_root"]) for item in result["targets"]] == [
        skills_root / "deepscientist-scout",
        skills_root / "deepscientist-idea",
        skills_root / "deepscientist-decision",
        skills_root / "deepscientist-write",
        skills_root / "deepscientist-finalize",
        skills_root / "deepscientist-journal-resolution",
    ]


def test_install_medical_overlay_writes_skill_and_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    skills_root = home / ".codex" / "skills"
    original = {}
    for skill_id in SKILL_IDS:
        original[skill_id] = f"upstream {skill_id}\n"
        write_skill(skills_root, skill_id, original[skill_id])

    result = module.install_medical_overlay(home=home)
    status = module.describe_medical_overlay(home=home)

    assert result["installed_count"] == 6
    assert {item["action"] for item in result["targets"]} == {"installed"}
    assert status["all_targets_ready"] is True
    assert {item["status"] for item in status["targets"]} == {"overlay_applied"}
    for skill_id in SKILL_IDS:
        target_root = skills_root / f"deepscientist-{skill_id}"
        manifest = read_manifest(target_root)
        assert manifest["skill_id"] == skill_id
        assert manifest["scope"] == "global"
        assert manifest["policy_id"] == "high_plasticity_medical"
        assert manifest["archetype_ids"] == [
            "clinical_classifier",
            "clinical_subtype_reconstruction",
            "external_validation_model_update",
            "gray_zone_triage",
            "llm_agent_clinical_task",
            "mechanistic_sidecar_extension",
        ]
        assert manifest["source_fingerprint_before_overlay"]
        assert manifest["overlay_fingerprint"]
        assert manifest["source_fingerprint_before_overlay"] != manifest["overlay_fingerprint"]
        assert (target_root / "SKILL.md").read_text(encoding="utf-8") == module.load_overlay_skill_text(skill_id)


def test_overlay_status_detects_overwritten_by_upstream(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    skills_root = home / ".codex" / "skills"
    original = {}
    for skill_id in SKILL_IDS:
        original[skill_id] = f"upstream {skill_id}\n"
        write_skill(skills_root, skill_id, original[skill_id])

    module.install_medical_overlay(home=home)
    write_skill(skills_root, "write", original["write"])

    result = module.describe_medical_overlay(home=home)
    by_skill = {item["skill_id"]: item for item in result["targets"]}

    assert by_skill["write"]["status"] == "overwritten_by_upstream"
    assert by_skill["write"]["needs_reapply"] is True
    assert by_skill["finalize"]["status"] == "overlay_applied"


def test_reapply_medical_overlay_restores_expected_skill_text(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    skills_root = home / ".codex" / "skills"
    for skill_id in SKILL_IDS:
        write_skill(skills_root, skill_id, f"upstream {skill_id}\n")

    module.install_medical_overlay(home=home)
    write_skill(skills_root, "finalize", "upstream finalize\n")

    result = module.reapply_medical_overlay(home=home)
    status = module.describe_medical_overlay(home=home)

    assert {item["action"] for item in result["targets"]} == {"reapplied"}
    assert {item["status"] for item in status["targets"]} == {"overlay_applied"}


def test_install_medical_overlay_requires_existing_target_directories(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"

    try:
        module.install_medical_overlay(home=home)
    except FileNotFoundError as exc:
        message = str(exc)
    else:
        message = ""

    assert "deepscientist-scout" in message


def test_install_medical_overlay_can_target_selected_skill_subset(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    skills_root = home / ".codex" / "skills"
    for skill_id in ("scout", "idea", "decision", "write", "finalize"):
        write_skill(skills_root, skill_id, f"upstream {skill_id}\n")

    result = module.install_medical_overlay(home=home, skill_ids=("scout", "decision"))
    status = module.describe_medical_overlay(home=home, skill_ids=("scout", "decision"))

    assert [item["skill_id"] for item in result["targets"]] == ["scout", "decision"]
    assert status["all_targets_ready"] is True
    assert [item["status"] for item in status["targets"]] == ["overlay_applied", "overlay_applied"]


def test_install_medical_overlay_seeds_workspace_targets_from_home_skills(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    global_skills_root = home / ".codex" / "skills"
    quest_root = tmp_path / "workspace"
    for skill_id in SKILL_IDS:
        write_skill(global_skills_root, skill_id, f"upstream {skill_id}\n")

    result = module.install_medical_overlay(
        quest_root=quest_root,
        home=home,
    )

    assert result["installed_count"] == 6
    for skill_id in SKILL_IDS:
        skill_path = quest_root / ".codex" / "skills" / f"deepscientist-{skill_id}" / "SKILL.md"
        assert skill_path.exists(), skill_path
        assert skill_path.read_text(encoding="utf-8") == module.load_overlay_skill_text(skill_id)


def test_load_overlay_skill_text_renders_policy_and_archetypes_for_front_stages() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    scout_text = module.load_overlay_skill_text("scout")
    write_text = module.load_overlay_skill_text("write")

    assert "{{MED_AUTOSCIENCE_ROUTE_BIAS}}" not in scout_text
    assert "{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}" not in scout_text
    assert "## Medical publication route bias" in scout_text
    assert "## Preferred study archetypes" in scout_text
    assert "Clinical subtype reconstruction" in scout_text
    assert "Gray-zone triage / reflex-testing support" in scout_text
    assert "LLM agent for a clinical task" in scout_text
    assert "Mechanistic sidecar extension" in scout_text
    assert "## Preferred study archetypes" not in write_text


def test_load_overlay_skill_text_for_finalize_includes_study_delivery_sync_contract() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    finalize_text = module.load_overlay_skill_text("finalize")

    assert "ops/medautoscience/bin/sync-delivery" in finalize_text
    assert "--stage finalize" in finalize_text
    assert "missing_study_delivery_wrapper" in finalize_text
    assert "final_delivery_sync_failed" in finalize_text


def test_load_overlay_skill_text_for_write_includes_medical_methods_and_results_contracts() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    write_text = module.load_overlay_skill_text("write")

    assert "methods_implementation_manifest.json" in write_text
    assert "results_narrative_map.json" in write_text
    assert "manuscript_safe_reproducibility_supplement.json" in write_text
    assert "endpoint_provenance_note.md" in write_text
    assert "software package and version" in write_text
    assert "center" in write_text
    assert "ethics" in write_text
    assert "inclusion_criteria" in write_text
    assert "exclusion_criteria" in write_text
    assert "variable_definitions" in write_text
    assert "operational_definition" in write_text
    assert "calibration-first" in write_text
    assert "research_question" in write_text
    assert "direct_answer" in write_text
    assert "clinical meaning" in write_text
    assert "submission_targets.resolved.json" in write_text
    assert "journal-resolution/SKILL.md" in write_text


def test_load_overlay_skill_text_for_journal_resolution_requires_official_sources() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    journal_resolution_text = module.load_overlay_skill_text("journal-resolution")

    assert "official author guidelines" in journal_resolution_text
    assert "official template" in journal_resolution_text
    assert "paper/submission_target_resolution.md" in journal_resolution_text
    assert "paper/submission_targets.resolved.json" in journal_resolution_text
    assert "Do not infer" in journal_resolution_text


def test_load_overlay_skill_text_renders_default_submission_targets_when_provided() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    write_text = module.load_overlay_skill_text(
        "write",
        default_submission_targets=(
            {
                "publication_profile": "frontiers_family_harvard",
                "primary": True,
                "story_surface": "general_medical_journal",
            },
        ),
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
    )

    assert "frontiers_family_harvard" in write_text
    assert "general_medical_journal" in write_text
    assert "AMA" in write_text


def test_load_overlay_skill_text_includes_reference_paper_contract_for_scout_idea_write() -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")

    scout_text = module.load_overlay_skill_text("scout")
    idea_text = module.load_overlay_skill_text("idea")
    write_text = module.load_overlay_skill_text("write")
    finalize_text = module.load_overlay_skill_text("finalize")

    assert "Reference paper contract" in scout_text
    assert "startup_contract.reference_papers" in scout_text
    assert "scout: required" in scout_text
    assert "idea: required" in idea_text
    assert "write: advisory" in write_text
    assert "do not back-solve missing analyses" in write_text
    assert "Reference paper contract" not in finalize_text


def test_overlay_status_detects_config_drift_when_archetypes_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    skills_root = home / ".codex" / "skills"
    for skill_id in SKILL_IDS:
        write_skill(skills_root, skill_id, f"upstream {skill_id}\n")

    module.install_medical_overlay(
        home=home,
        archetype_ids=("clinical_classifier",),
    )

    result = module.describe_medical_overlay(
        home=home,
        archetype_ids=(
            "clinical_classifier",
            "clinical_subtype_reconstruction",
            "external_validation_model_update",
            "gray_zone_triage",
            "llm_agent_clinical_task",
            "mechanistic_sidecar_extension",
        ),
    )
    by_skill = {item["skill_id"]: item for item in result["targets"]}

    assert by_skill["scout"]["status"] == "drifted"
    assert by_skill["idea"]["status"] == "drifted"
    assert by_skill["decision"]["status"] == "drifted"
    assert by_skill["write"]["status"] == "overlay_applied"
