from __future__ import annotations

import importlib
import json
from pathlib import Path

import yaml


def make_profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    return profiles.WorkspaceProfile(
        name="pituitary",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline", "write"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )


def test_resolve_study_runtime_paths_derives_binding_and_launch_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"

    result = module.resolve_study_runtime_paths(
        profile=profile,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
    )

    assert result["quest_root"] == profile.workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    assert result["runtime_binding_path"] == study_root / "runtime_binding.yaml"
    assert result["startup_payload_root"] == profile.workspace_root / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk"
    assert result["launch_report_path"] == study_root / "artifacts" / "runtime" / "last_launch_report.json"


def test_write_runtime_binding_writes_protocol_schema(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    runtime_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    binding_path = study_root / "runtime_binding.yaml"

    module.write_runtime_binding(
        runtime_binding_path=binding_path,
        runtime_root=runtime_root,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        last_action="resume",
        source="test-source",
        recorded_at="2026-04-02T12:00:00+00:00",
    )

    payload = yaml.safe_load(binding_path.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": 1,
        "engine": "med-deepscientist",
        "study_id": "001-risk",
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "runtime_root": str(runtime_root / "quests"),
        "med_deepscientist_runtime_root": str(runtime_root),
        "last_action": "resume",
        "last_action_at": "2026-04-02T12:00:00+00:00",
        "last_source": "test-source",
    }


def test_write_launch_report_records_runtime_payload(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    report_path = tmp_path / "workspace" / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"

    module.write_launch_report(
        launch_report_path=report_path,
        status={"decision": "resume", "quest_status": "running"},
        source="test-source",
        force=True,
        startup_payload_path=tmp_path / "payloads" / "001-risk.json",
        daemon_result={"resume": {"ok": True, "status": "running"}},
        recorded_at="2026-04-02T12:00:00+00:00",
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["decision"] == "resume"
    assert payload["source"] == "test-source"
    assert payload["force"] is True
    assert payload["recorded_at"] == "2026-04-02T12:00:00+00:00"
    assert payload["startup_payload_path"].endswith("/payloads/001-risk.json")
    assert payload["daemon_result"] == {"resume": {"ok": True, "status": "running"}}


def test_archive_invalid_partial_quest_root_moves_broken_quest_into_recovery_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    runtime_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    (quest_root / "artifacts").mkdir(parents=True, exist_ok=True)

    result = module.archive_invalid_partial_quest_root(
        quest_root=quest_root,
        runtime_root=runtime_root,
        slug="20260402T120000Z",
    )

    archived_root = runtime_root / "recovery" / "invalid_partial_quest_roots" / "001-risk-20260402T120000Z"
    assert result == {
        "status": "archived_invalid_partial_quest_root",
        "quest_root": str(quest_root),
        "archived_root": str(archived_root),
        "missing_required_files": ["quest.yaml"],
    }
    assert not quest_root.exists()
    assert archived_root.exists()
