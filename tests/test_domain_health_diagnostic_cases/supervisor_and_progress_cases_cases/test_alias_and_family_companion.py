from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_domain_health_diagnostic_for_runtime_does_not_auto_recover_submission_metadata_parking(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    parked_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_waiting_for_submission_metadata",
        ),
        "quest_status": "waiting_for_user",
        "execution": {
            "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "continuation_state": {
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "decision",
            "continuation_reason": "paper_bundle_submitted",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: (
            record_projection_call(calls, study_root=Path(study_root), kwargs=kwargs),
            parked_status,
        )[1],
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == [("status", "001-risk"), ("currentness", "001-risk")]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []

def test_watch_quest_dry_run_does_not_write_latest_domain_health_diagnostic_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    latest_json = quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json"
    latest_markdown = quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.md"

    assert result["diagnostic_report_persistence"]["persisted"] is False
    assert "latest_report_json" not in result
    assert "latest_report_markdown" not in result
    assert not latest_json.exists()
    assert not latest_markdown.exists()


def test_watch_quest_report_refresh_writes_latest_domain_health_diagnostic_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
        persist_diagnostic_reports=True,
    )

    latest_json = quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json"
    latest_markdown = quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.md"

    assert result["diagnostic_report_persistence"]["persisted"] is True
    assert result["latest_report_json"] == str(latest_json)
    assert result["latest_report_markdown"] == str(latest_markdown)
    assert latest_json.exists()
    assert latest_markdown.exists()

def test_watch_quest_emits_family_orchestration_companion_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["session"]["quest_id"] == "q001"
    assert result["family_event_envelope"]["session"]["active_run_id"] == "run-1"
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_checkpoint_lineage"]["session"]["active_run_id"] == "run-1"
    assert result["family_human_gates"] == []

def test_watch_runtime_emits_family_orchestration_companion_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q001", status="running")

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=runtime_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["payload"]["scanned_quest_count"] == 1
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_human_gates"] == []

def test_watch_runtime_aggregates_publication_gate_human_confirmation_into_family_gates(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q001", status="running")

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=runtime_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["human_confirmation_required"],
                "current_required_action": "human_confirmation_required",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    quest_report = result["reports"][0]
    quest_gate = quest_report["family_human_gates"][0]
    runtime_gate = result["family_human_gates"][0]

    assert quest_gate["version"] == "family-human-gate.v1"
    assert quest_gate["gate_kind"] == "publication_gate_human_confirmation"
    assert quest_gate["request_surface"]["surface_kind"] == "domain_health_diagnostic"
    assert runtime_gate == quest_gate
    assert result["family_event_envelope"]["human_gate_hint"]["gate_id"] == quest_gate["gate_id"]
    assert result["family_checkpoint_lineage"]["resume_contract"]["human_gate_required"] is True
