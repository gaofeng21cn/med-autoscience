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
    assert result == module.StudyRuntimeArtifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        startup_payload_path=startup_payload_path,
    )


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
    assert result == module.StudyRuntimeArtifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        startup_payload_path=None,
    )


def test_study_runtime_artifacts_from_payload_round_trips_protocol_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    payload = {
        "runtime_binding_path": str(tmp_path / "workspace" / "studies" / "001-risk" / "runtime_binding.yaml"),
        "launch_report_path": str(
            tmp_path / "workspace" / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
        ),
        "startup_payload_path": str(
            tmp_path / "workspace" / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk" / "payload.json"
        ),
    }

    result = module.StudyRuntimeArtifacts.from_payload(payload)

    assert result.to_dict() == payload


def test_study_runtime_artifacts_from_payload_rejects_missing_launch_report_path() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match="study runtime artifacts payload missing launch_report_path"):
        module.StudyRuntimeArtifacts.from_payload({"runtime_binding_path": "/tmp/runtime_binding.yaml"})


def test_study_runtime_protocol_reexports_models_from_study_runtime_models() -> None:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    models = importlib.import_module("med_autoscience.runtime_protocol.study_runtime_models")

    assert protocol.StudyRuntimeContext is models.StudyRuntimeContext
    assert protocol.StudyRuntimeArtifacts is models.StudyRuntimeArtifacts
    assert protocol.StartupContractValidationStatus is models.StartupContractValidationStatus
    assert protocol.StartupHydrationStatus is models.StartupHydrationStatus
    assert protocol.StartupHydrationValidationStatus is models.StartupHydrationValidationStatus
    assert protocol.StartupContractValidation is models.StartupContractValidation
    assert protocol.StartupHydrationReport is models.StartupHydrationReport
    assert protocol.StartupHydrationValidationReport is models.StartupHydrationValidationReport
    assert protocol.StartupContractValidation.__module__ == models.__name__
    assert protocol.StartupHydrationReport.__module__ == models.__name__
    assert protocol.StartupHydrationValidationReport.__module__ == models.__name__


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


def test_write_startup_hydration_report_persists_typed_protocol_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "001-risk"
    report = module.StartupHydrationReport(
        status=module.StartupHydrationStatus.HYDRATED,
        recorded_at="2026-04-03T08:00:00+00:00",
        quest_root=str(quest_root),
        entry_state_summary="Study root: /tmp/workspace/studies/001-risk",
        literature_report={"record_count": 1},
        written_files=(str(quest_root / "paper" / "medical_analysis_contract.json"),),
        report_path=None,
    )

    written = module.write_startup_hydration_report(quest_root=quest_root, report=report)

    expected_path = quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"
    assert written.report_path == str(expected_path)
    payload = json.loads(expected_path.read_text(encoding="utf-8"))
    assert payload == written.to_dict()


def test_write_startup_hydration_validation_report_persists_typed_protocol_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "001-risk"
    report = module.StartupHydrationValidationReport(
        status=module.StartupHydrationValidationStatus.CLEAR,
        recorded_at="2026-04-03T08:05:00+00:00",
        quest_root=str(quest_root),
        blockers=(),
        medical_analysis_contract_status="resolved",
        medical_reporting_contract_status="resolved",
        medical_analysis_contract_path=str(quest_root / "paper" / "medical_analysis_contract.json"),
        medical_reporting_contract_path=str(quest_root / "paper" / "medical_reporting_contract.json"),
        report_path=None,
    )

    written = module.write_startup_hydration_validation_report(quest_root=quest_root, report=report)

    expected_path = quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"
    assert written.report_path == str(expected_path)
    payload = json.loads(expected_path.read_text(encoding="utf-8"))
    assert payload == written.to_dict()


def test_startup_hydration_report_rejects_missing_required_fields() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match="startup hydration payload missing recorded_at"):
        module.StartupHydrationReport.from_payload({"status": "hydrated"})


def test_startup_hydration_validation_report_rejects_missing_required_fields() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match="startup hydration validation payload missing checked_paths"):
        module.StartupHydrationValidationReport.from_payload(
            {
                "status": "clear",
                "recorded_at": "2026-04-03T08:05:00+00:00",
                "quest_root": "/tmp/runtime/quests/001-risk",
                "blockers": [],
                "contract_statuses": {
                    "medical_analysis_contract": "resolved",
                    "medical_reporting_contract": "resolved",
                },
            }
        )


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

    assert result.status is module.StartupContractValidationStatus.CLEAR
    assert result == module.StartupContractValidation(
        status=module.StartupContractValidationStatus.CLEAR,
        blockers=(),
        medical_analysis_contract_status="resolved",
        medical_reporting_contract_status="resolved",
        medical_analysis_reason_code="analysis_ok",
        medical_reporting_reason_code="reporting_ok",
    )


def test_startup_contract_validation_from_payload_reconstructs_protocol_surface() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    result = module.StartupContractValidation.from_payload(
        {
            "status": "blocked",
            "blockers": ["missing_medical_reporting_contract"],
            "contract_statuses": {
                "medical_analysis_contract": "resolved",
                "medical_reporting_contract": None,
            },
            "reason_codes": {
                "medical_analysis_contract": "analysis_ok",
                "medical_reporting_contract": None,
            },
        }
    )

    assert result == module.StartupContractValidation(
        status=module.StartupContractValidationStatus.BLOCKED,
        blockers=("missing_medical_reporting_contract",),
        medical_analysis_contract_status="resolved",
        medical_reporting_contract_status=None,
        medical_analysis_reason_code="analysis_ok",
        medical_reporting_reason_code=None,
    )


def test_startup_contract_validation_from_payload_rejects_missing_protocol_fields() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match="startup contract validation payload missing contract_statuses"):
        module.StartupContractValidation.from_payload(
            {
                "status": "clear",
                "blockers": [],
                "reason_codes": {
                    "medical_analysis_contract": None,
                    "medical_reporting_contract": None,
                },
            }
        )


def test_validate_startup_contract_resolution_classifies_missing_invalid_and_unsupported() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    result = module.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": {"status": "unsupported", "reason_code": "unsupported_family"},
            "medical_reporting_contract_summary": "invalid-payload",
        }
    )

    assert result.status is module.StartupContractValidationStatus.BLOCKED
    assert result == module.StartupContractValidation(
        status=module.StartupContractValidationStatus.BLOCKED,
        blockers=(
            "unsupported_medical_analysis_contract",
            "invalid_medical_reporting_contract",
        ),
        medical_analysis_contract_status="unsupported",
        medical_reporting_contract_status=None,
        medical_analysis_reason_code="unsupported_family",
        medical_reporting_reason_code=None,
    )


def test_validate_startup_contract_resolution_classifies_unresolved_contracts() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    result = module.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": {"status": "draft", "reason_code": "needs_mapping"},
            "medical_reporting_contract_summary": None,
        }
    )

    assert result.status is module.StartupContractValidationStatus.BLOCKED
    assert result == module.StartupContractValidation(
        status=module.StartupContractValidationStatus.BLOCKED,
        blockers=(
            "unresolved_medical_analysis_contract",
            "missing_medical_reporting_contract",
        ),
        medical_analysis_contract_status="draft",
        medical_reporting_contract_status=None,
        medical_analysis_reason_code="needs_mapping",
        medical_reporting_reason_code=None,
    )


def test_startup_contract_validation_from_payload_round_trips_protocol_surface() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    payload = {
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

    result = module.StartupContractValidation.from_payload(payload)

    assert result == module.StartupContractValidation(
        status=module.StartupContractValidationStatus.CLEAR,
        blockers=(),
        medical_analysis_contract_status="resolved",
        medical_reporting_contract_status="resolved",
        medical_analysis_reason_code="analysis_ok",
        medical_reporting_reason_code="reporting_ok",
    )
    assert result.to_dict() == payload


def test_startup_contract_validation_from_payload_rejects_missing_contract_statuses() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match="startup contract validation payload missing contract_statuses"):
        module.StartupContractValidation.from_payload({"status": "clear", "blockers": []})


def test_startup_contract_validation_rejects_unknown_status() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    with pytest.raises(ValueError, match="unknown startup contract validation status"):
        module.StartupContractValidation(
            status="unexpected",
            blockers=(),
            medical_analysis_contract_status=None,
            medical_reporting_contract_status=None,
            medical_analysis_reason_code=None,
            medical_reporting_reason_code=None,
        )


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
