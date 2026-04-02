from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
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


def test_resolve_study_runtime_paths_derives_binding_launch_and_runtime_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"

    result = module.resolve_study_runtime_paths(
        profile=profile,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
    )

    assert result["runtime_root"] == profile.workspace_root / "ops" / "med-deepscientist" / "runtime"
    assert result["quest_root"] == profile.workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    assert result["runtime_binding_path"] == study_root / "runtime_binding.yaml"
    assert result["startup_payload_root"] == profile.workspace_root / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk"
    assert result["launch_report_path"] == study_root / "artifacts" / "runtime" / "last_launch_report.json"


def test_resolve_study_runtime_context_derives_typed_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"

    context = module.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
    )

    assert context.runtime_root == profile.workspace_root / "ops" / "med-deepscientist" / "runtime"
    assert context.quest_root == profile.workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    assert context.runtime_binding_path == study_root / "runtime_binding.yaml"
    assert context.startup_payload_root == profile.workspace_root / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk"
    assert context.launch_report_path == study_root / "artifacts" / "runtime" / "last_launch_report.json"


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


def test_write_startup_payload_writes_create_payload_and_returns_written_path(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    startup_payload_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk"

    payload_path = module.write_startup_payload(
        startup_payload_root=startup_payload_root,
        create_payload={"quest_id": "001-risk", "goal": "Launch study 001"},
        slug="20260402T120000Z",
    )

    assert payload_path == startup_payload_root / "20260402T120000Z.json"
    assert json.loads(payload_path.read_text(encoding="utf-8")) == {
        "quest_id": "001-risk",
        "goal": "Launch study 001",
    }


def test_persist_runtime_artifacts_writes_binding_and_launch_report_when_last_action_present(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    runtime_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_binding_path = study_root / "runtime_binding.yaml"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    startup_payload_path = tmp_path / "workspace" / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk" / "20260402T120000Z.json"

    result = module.persist_runtime_artifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        runtime_root=runtime_root,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        last_action="resume",
        status={"decision": "resume", "quest_status": "running"},
        source="test-source",
        force=True,
        startup_payload_path=startup_payload_path,
        daemon_result={"resume": {"ok": True, "status": "running"}},
        recorded_at="2026-04-02T12:00:00+00:00",
    )

    binding = yaml.safe_load(runtime_binding_path.read_text(encoding="utf-8"))
    report = json.loads(launch_report_path.read_text(encoding="utf-8"))
    assert binding["last_action"] == "resume"
    assert binding["quest_id"] == "quest-001"
    assert report["decision"] == "resume"
    assert report["startup_payload_path"] == str(startup_payload_path)
    assert result == {
        "runtime_binding_path": str(runtime_binding_path),
        "launch_report_path": str(launch_report_path),
        "startup_payload_path": str(startup_payload_path),
    }


def test_persist_runtime_artifacts_skips_binding_when_last_action_is_absent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_binding_path = study_root / "runtime_binding.yaml"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"

    result = module.persist_runtime_artifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
        study_id="001-risk",
        study_root=study_root,
        quest_id=None,
        last_action=None,
        status={"decision": "blocked", "quest_exists": False},
        source="test-source",
        force=False,
        startup_payload_path=None,
        daemon_result=None,
        recorded_at="2026-04-02T12:00:00+00:00",
    )

    assert runtime_binding_path.exists() is False
    assert json.loads(launch_report_path.read_text(encoding="utf-8"))["decision"] == "blocked"
    assert result == {
        "runtime_binding_path": str(runtime_binding_path),
        "launch_report_path": str(launch_report_path),
        "startup_payload_path": None,
    }


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


def test_build_hydration_payload_returns_protocol_surface() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    payload = module.build_hydration_payload(
        create_payload={
            "startup_contract": {
                "medical_analysis_contract_summary": {"study_archetype": "clinical_classifier"},
                "medical_reporting_contract_summary": {"reporting_guideline_family": "TRIPOD"},
                "entry_state_summary": " Study root: /tmp/workspace/studies/001-risk ",
            }
        }
    )

    assert payload == {
        "medical_analysis_contract": {"study_archetype": "clinical_classifier"},
        "medical_reporting_contract": {"reporting_guideline_family": "TRIPOD"},
        "entry_state_summary": "Study root: /tmp/workspace/studies/001-risk",
    }


@pytest.mark.parametrize(
    ("create_payload", "message"),
    [
        ({}, "create payload missing startup_contract"),
        ({"startup_contract": {}}, "startup_contract missing medical_analysis_contract_summary"),
        (
            {"startup_contract": {"medical_analysis_contract_summary": {}}},
            "startup_contract missing medical_reporting_contract_summary",
        ),
        (
            {
                "startup_contract": {
                    "medical_analysis_contract_summary": {},
                    "medical_reporting_contract_summary": {},
                    "entry_state_summary": " ",
                }
            },
            "startup_contract missing entry_state_summary",
        ),
    ],
)
def test_build_hydration_payload_rejects_invalid_payload(create_payload: dict[str, object], message: str) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match=message):
        module.build_hydration_payload(create_payload=create_payload)


def test_validate_startup_contract_resolution_returns_clear_for_resolved_contracts() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    result = module.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": {"status": "resolved", "reason_code": "analysis_ok"},
            "medical_reporting_contract_summary": {"status": "resolved", "reason_code": "reporting_ok"},
        }
    )

    assert result == {
        "status": "clear",
        "blockers": [],
        "contract_statuses": {
            "medical_analysis_contract": "resolved",
            "medical_reporting_contract": "resolved",
        },
        "reason_codes": {
            "medical_analysis_contract": "analysis_ok",
            "medical_reporting_contract": "reporting_ok",
        },
    }


def test_validate_startup_contract_resolution_classifies_missing_invalid_and_unsupported() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    result = module.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": {"status": "unsupported", "reason_code": "unsupported_family"},
            "medical_reporting_contract_summary": "invalid-payload",
        }
    )

    assert result == {
        "status": "blocked",
        "blockers": [
            "unsupported_medical_analysis_contract",
            "invalid_medical_reporting_contract",
        ],
        "contract_statuses": {
            "medical_analysis_contract": "unsupported",
            "medical_reporting_contract": None,
        },
        "reason_codes": {
            "medical_analysis_contract": "unsupported_family",
            "medical_reporting_contract": None,
        },
    }


def test_validate_startup_contract_resolution_classifies_unresolved_contracts() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    result = module.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": {"status": "draft", "reason_code": "needs_mapping"},
            "medical_reporting_contract_summary": None,
        }
    )

    assert result == {
        "status": "blocked",
        "blockers": [
            "unresolved_medical_analysis_contract",
            "missing_medical_reporting_contract",
        ],
        "contract_statuses": {
            "medical_analysis_contract": "draft",
            "medical_reporting_contract": None,
        },
        "reason_codes": {
            "medical_analysis_contract": "needs_mapping",
            "medical_reporting_contract": None,
        },
    }


def test_should_refresh_startup_hydration_while_blocked_accepts_allowed_blocked_states() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    assert (
        module.should_refresh_startup_hydration_while_blocked(
            {
                "decision": "blocked",
                "quest_exists": True,
                "quest_status": "created",
                "reason": "startup_boundary_not_ready_for_resume",
            }
        )
        is True
    )


@pytest.mark.parametrize(
    "status",
    [
        {"decision": "resume", "quest_exists": True, "quest_status": "created", "reason": "startup_boundary_not_ready_for_resume"},
        {"decision": "blocked", "quest_exists": False, "quest_status": "created", "reason": "startup_boundary_not_ready_for_resume"},
        {"decision": "blocked", "quest_exists": True, "quest_status": "running", "reason": "startup_boundary_not_ready_for_resume"},
        {"decision": "blocked", "quest_exists": True, "quest_status": "paused", "reason": "other_reason"},
    ],
)
def test_should_refresh_startup_hydration_while_blocked_rejects_other_states(status: dict[str, object]) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    assert module.should_refresh_startup_hydration_while_blocked(status) is False
