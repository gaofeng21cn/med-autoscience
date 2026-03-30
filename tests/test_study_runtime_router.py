from __future__ import annotations

import importlib
import json
from pathlib import Path

import yaml


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    return profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        deepscientist_runtime_root=workspace_root / "ops" / "deepscientist" / "runtime",
        deepscientist_repo_root=tmp_path / "DeepScientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline", "write", "finalize"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )


def write_study(workspace_root: Path, study_id: str) -> Path:
    study_root = workspace_root / "studies" / study_id
    write_text(workspace_root / "ops" / "deepscientist" / "startup_briefs" / f"{study_id}.md", "# Startup brief\n")
    write_text(
        study_root / "study.yaml",
        "\n".join(
            [
                f"study_id: {study_id}",
                "title: Diabetes mortality risk paper",
                "status: ready",
                "primary_question: >",
                "  Build a submission-ready survival-risk study.",
                "brief_file: brief.md",
                "protocol_file: protocol.md",
                f"startup_brief: ../../ops/deepscientist/startup_briefs/{study_id}.md",
                "execution:",
                "  engine: deepscientist",
                "  auto_entry: on_managed_research_intent",
                "  auto_resume: true",
                f"  quest_id: {study_id}",
                "  default_entry_mode: full_research",
                "  startup_contract_profile: paper_required_autonomous",
                "  launch_profile: continue_existing_state",
                "  decision_policy: autonomous",
                "",
            ]
        ),
    )
    write_text(study_root / "brief.md", "# Brief\n")
    write_text(study_root / "protocol.md", "# Protocol\n")
    return study_root


def _clear_readiness_report(workspace_root: Path, study_id: str) -> dict[str, object]:
    return {
        "status": "clear",
        "study_summary": {
            "study_count": 1,
            "review_needed_count": 0,
            "clear_count": 1,
            "review_needed_study_ids": [],
            "clear_study_ids": [study_id],
            "outdated_private_release_study_ids": [],
            "unresolved_contract_study_ids": [],
            "public_extension_study_ids": [],
        },
    }


def test_ensure_study_runtime_creates_and_starts_new_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    created: dict[str, object] = {}

    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.submission_targets_controller,
        "resolve_submission_targets",
        lambda **_: {
            "targets": [
                {
                    "publication_profile": "general_medical_journal",
                    "primary": True,
                    "package_required": True,
                    "resolution_status": "resolved_profile",
                }
            ]
        },
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "running",
            },
            "startup": {"queued": True},
        }

    monkeypatch.setattr(module.daemon_api, "create_quest", fake_create_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert created["runtime_root"] == profile.deepscientist_runtime_root
    payload = created["payload"]
    assert payload["quest_id"] == "001-risk"
    assert payload["auto_start"] is True
    assert payload["title"] == "Diabetes mortality risk paper"
    assert payload["startup_contract"]["custom_profile"] == "continue_existing_state"
    assert payload["startup_contract"]["submission_targets"][0]["publication_profile"] == "general_medical_journal"
    assert Path(result["startup_payload_path"]).is_file()
    assert Path(result["runtime_binding_path"]).is_file()
    assert Path(result["launch_report_path"]).is_file()
    binding = yaml.safe_load(Path(result["runtime_binding_path"]).read_text(encoding="utf-8"))
    assert binding["last_action"] == "create_and_start"
    assert binding["quest_id"] == "001-risk"
    report = json.loads(Path(result["launch_report_path"]).read_text(encoding="utf-8"))
    assert report["decision"] == "create_and_start"
    assert report["study_id"] == "001-risk"
    assert report["study_root"] == str(study_root)


def test_ensure_study_runtime_resumes_paused_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    resumed: dict[str, object] = {}

    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.submission_targets_controller,
        "resolve_submission_targets",
        lambda **_: {"targets": []},
    )

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        resumed["runtime_root"] = runtime_root
        resumed["quest_id"] = quest_id
        resumed["source"] = source
        return {"ok": True, "status": "running"}

    monkeypatch.setattr(module.daemon_api, "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert resumed == {
        "runtime_root": profile.deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_ensure_study_runtime_noops_when_quest_is_already_running(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')

    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.submission_targets_controller,
        "resolve_submission_targets",
        lambda **_: {"targets": []},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"


def test_ensure_study_runtime_stays_lightweight_for_non_managed_entry_mode(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.submission_targets_controller,
        "resolve_submission_targets",
        lambda **_: {"targets": []},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", entry_mode="literature_scout")

    assert result["decision"] == "lightweight"
    assert result["reason"] == "entry_mode_not_managed"


def test_ensure_study_runtime_blocks_when_study_has_unresolved_data_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: {
            "status": "attention_needed",
            "study_summary": {
                "study_count": 1,
                "review_needed_count": 1,
                "clear_count": 0,
                "review_needed_study_ids": ["001-risk"],
                "clear_study_ids": [],
                "outdated_private_release_study_ids": [],
                "unresolved_contract_study_ids": ["001-risk"],
                "public_extension_study_ids": [],
            },
        },
    )
    monkeypatch.setattr(
        module.submission_targets_controller,
        "resolve_submission_targets",
        lambda **_: {"targets": []},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_data_readiness_blocked"
