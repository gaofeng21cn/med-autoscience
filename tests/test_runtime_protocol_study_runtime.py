from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from med_autoscience import study_decision_record as decision_record
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as runtime


def make_profile(tmp_path: Path):
    workspace_root = tmp_path / "workspace"
    return WorkspaceProfile(
        name="pituitary",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "memory" / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )


def test_runtime_protocol_facade_import_does_not_load_controller_modules() -> None:
    script = (
        "import sys\n"
        "import med_autoscience.runtime_protocol\n"
        "loaded = sorted(name for name in sys.modules if name.startswith('med_autoscience.controllers'))\n"
        "if loaded:\n"
        "    raise SystemExit('\\n'.join(loaded))\n"
    )

    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr or result.stdout


def test_runtime_protocol_sources_do_not_import_controller_modules() -> None:
    protocol_root = Path(__file__).resolve().parents[1] / "src" / "med_autoscience" / "runtime_protocol"
    offenders = sorted(
        path.relative_to(protocol_root).as_posix()
        for path in protocol_root.rglob("*.py")
        if "med_autoscience.controllers" in path.read_text(encoding="utf-8")
    )

    assert offenders == []


def test_resolve_study_runtime_context_derives_typed_paths(tmp_path: Path) -> None:
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"

    context = runtime.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
    )

    assert context.runtime_root == profile.workspace_root / "runtime"
    assert context.quest_root == profile.workspace_root / "runtime" / "quests" / "quest-001"
    assert context.runtime_binding_path == study_root / "runtime_binding.yaml"
    assert context.startup_payload_root == profile.workspace_root / "runtime" / "startup_payloads" / "001-risk"
    assert context.launch_report_path == study_root / "artifacts" / "runtime" / "last_launch_report.json"


def test_write_runtime_binding_writes_protocol_schema(tmp_path: Path) -> None:
    runtime_root = tmp_path / "workspace" / "runtime"
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    binding_path = study_root / "runtime_binding.yaml"

    runtime.write_runtime_binding(
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
    assert payload["schema_version"] == 1
    assert payload["runtime_owner"] == "one-person-lab"
    assert payload["domain_owner"] == "med-autoscience"
    assert payload["opl_runtime_ref"] == "opl_hosted_stage_runtime"
    assert payload["runtime_ref"] == "opl_hosted_stage_runtime"
    assert payload["runtime_engine_id"] == "opl-hosted-stage-runtime"
    assert "runtime_backend_id" not in payload
    assert "runtime_backend" not in payload
    assert payload["research_backend_id"] == "mas_domain_intent_adapter"
    assert payload["research_backend"] == "mas_domain_intent_adapter"
    assert payload["research_engine_id"] == "mas-domain-intent-adapter"
    assert payload["study_id"] == "001-risk"
    assert payload["quest_id"] == "quest-001"
    assert payload["runtime_root"] == str(runtime_root / "quests")
    assert payload["runtime_quests_root"] == str(runtime_root / "quests")
    assert payload["historical_fixture_ref"] == {
        "surface_kind": "historical_fixture_ref",
        "runtime_root": str(runtime_root),
        "read_only": True,
    }
    assert payload["last_action"] == "resume"
    assert payload["last_action_at"] == "2026-04-02T12:00:00+00:00"
    assert payload["last_source"] == "test-source"


def test_write_runtime_binding_rejects_retired_mas_runtime_core_backend_metadata(tmp_path: Path) -> None:
    runtime_root = tmp_path / "workspace" / "runtime"
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    binding_path = study_root / "runtime_binding.yaml"

    with pytest.raises(ValueError, match="OPL owns runtime hydration"):
        runtime.write_runtime_binding(
            runtime_binding_path=binding_path,
            runtime_root=runtime_root,
            study_id="001-risk",
            study_root=study_root,
            quest_id="quest-mas-runtime-core-001",
            last_action="resume",
            source="test-source",
            recorded_at="2026-04-11T12:00:00+00:00",
            opl_runtime_ref="mas_runtime_core",
        )


@pytest.mark.parametrize(
    "execution",
    [
        {
            "opl_runtime_ref": "mas_runtime_core",
            "runtime_engine_id": "mas-runtime-core",
            "auto_entry": "on_managed_research_intent",
        },
        {
            "engine": "med-deepscientist",
            "opl_runtime_ref": "hermes",
            "runtime_engine_id": "hermes",
            "research_backend_id": "med_deepscientist",
            "research_engine_id": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
        },
    ],
)
def test_runtime_binding_opl_metadata_rejects_retired_runtime_backends(execution: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="OPL owns runtime hydration"):
        runtime._runtime_binding_opl_metadata({"execution": execution})


def test_write_launch_report_records_runtime_payload(tmp_path: Path) -> None:
    report_path = tmp_path / "workspace" / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"

    runtime.write_launch_report(
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


def test_write_launch_report_persists_autonomous_runtime_notice_payload(tmp_path: Path) -> None:
    report_path = tmp_path / "workspace" / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"

    runtime.write_launch_report(
        launch_report_path=report_path,
        status={
            "decision": "noop",
            "quest_status": "running",
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "quest:001-risk:run-live",
                "notification_reason": "detected_existing_live_managed_runtime",
                "quest_id": "001-risk",
                "quest_status": "running",
                "active_run_id": "run-live",
                "browser_url": "http://127.0.0.1:20999",
                "quest_api_url": "http://127.0.0.1:20999/api/quests/001-risk",
                "quest_session_api_url": "http://127.0.0.1:20999/api/quests/001-risk/session",
                "monitoring_available": True,
                "monitoring_error": None,
                "launch_report_path": str(report_path),
            },
        },
        source="test-source",
        force=False,
        startup_payload_path=None,
        daemon_result=None,
        recorded_at="2026-04-02T12:00:00+00:00",
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    notice = payload["autonomous_runtime_notice"]
    assert notice["required"] is True
    assert notice["notice_key"] == "quest:001-risk:run-live"
    assert notice["notification_reason"] == "detected_existing_live_managed_runtime"
    assert notice["quest_status"] == "running"
    assert notice["active_run_id"] == "run-live"
    assert notice["monitoring_available"] is True
    assert notice["launch_report_path"] == str(report_path)


def test_persist_runtime_artifacts_writes_binding_and_launch_report_when_last_action_present(tmp_path: Path) -> None:
    runtime_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_binding_path = study_root / "runtime_binding.yaml"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    startup_payload_path = tmp_path / "workspace" / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk" / "20260402T120000Z.json"

    result = runtime.persist_runtime_artifacts(
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
    assert result == runtime.StudyRuntimeArtifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        startup_payload_path=startup_payload_path,
    )


def test_persist_runtime_artifacts_skips_binding_when_last_action_is_absent(tmp_path: Path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_binding_path = study_root / "runtime_binding.yaml"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"

    result = runtime.persist_runtime_artifacts(
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
    assert result == runtime.StudyRuntimeArtifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        startup_payload_path=None,
    )


def test_study_runtime_artifacts_from_payload_round_trips_protocol_surface(tmp_path: Path) -> None:
    payload = {
        "runtime_binding_path": str(tmp_path / "workspace" / "studies" / "001-risk" / "runtime_binding.yaml"),
        "launch_report_path": str(
            tmp_path / "workspace" / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
        ),
        "startup_payload_path": str(
            tmp_path / "workspace" / "ops" / "med-deepscientist" / "startup_payloads" / "001-risk" / "payload.json"
        ),
    }

    result = runtime.StudyRuntimeArtifacts.from_payload(payload)

    assert result.to_dict() == payload


def test_study_runtime_artifacts_from_payload_rejects_missing_launch_report_path() -> None:
    with pytest.raises(ValueError, match="study runtime artifacts payload missing launch_report_path"):
        runtime.StudyRuntimeArtifacts.from_payload({"runtime_binding_path": "/tmp/runtime_binding.yaml"})
