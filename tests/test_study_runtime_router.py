from __future__ import annotations

from dataclasses import replace
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
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
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline", "write", "finalize"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
        default_startup_anchor_policy="scout_first_for_continue_existing_state",
        legacy_code_execution_policy="forbid_without_user_approval",
        startup_boundary_requirements=("paper_framing", "journal_shortlist", "evidence_package"),
    )


def write_study(
    workspace_root: Path,
    study_id: str,
    *,
    study_status: str = "ready",
    quest_id: str | None = None,
    study_archetype: str | None = None,
    preferred_study_archetype: str | None = None,
    paper_framing_summary: str | None = None,
    paper_urls: list[str] | None = None,
    journal_shortlist: list[str] | None = None,
    journal_shortlist_evidence: list[dict[str, object]] | None = None,
    minimum_sci_ready_evidence_package: list[str] | None = None,
    launch_profile: str = "continue_existing_state",
    endpoint_type: str | None = None,
    manuscript_family: str | None = None,
    submission_targets_mode: str | None = None,
    submission_targets: list[dict[str, object]] | None = None,
    study_completion: dict[str, object] | None = None,
    runtime_reentry_required_paths: list[str] | None = None,
    runtime_reentry_execution_root: str | None = None,
    runtime_reentry_first_unit: str | None = None,
    runtime_reentry_require_startup_hydration: bool | None = None,
    runtime_reentry_require_managed_skill_audit: bool | None = None,
) -> Path:
    study_root = workspace_root / "studies" / study_id
    write_text(workspace_root / "ops" / "med-deepscientist" / "startup_briefs" / f"{study_id}.md", "# Startup brief\n")
    lines = [
        f"study_id: {study_id}",
        "title: Diabetes mortality risk paper",
        f"status: {study_status}",
        "primary_question: >",
        "  Build a submission-ready survival-risk study.",
        "brief_file: brief.md",
        "protocol_file: protocol.md",
        f"startup_brief: ../../ops/med-deepscientist/startup_briefs/{study_id}.md",
    ]
    if study_archetype is not None:
        lines.append(f"study_archetype: {study_archetype}")
    if preferred_study_archetype is not None:
        lines.append(f"preferred_study_archetype: {preferred_study_archetype}")
    if paper_framing_summary is not None:
        lines.extend(
            [
                "paper_framing_summary: >",
                f"  {paper_framing_summary}",
            ]
        )
    if endpoint_type is not None:
        lines.append(f"endpoint_type: {endpoint_type}")
    if manuscript_family is not None:
        lines.append(f"manuscript_family: {manuscript_family}")
    if paper_urls:
        lines.append("paper_urls:")
        lines.extend(f"  - {url}" for url in paper_urls)
    if journal_shortlist:
        lines.append("journal_shortlist:")
        lines.extend(f"  - {item}" for item in journal_shortlist)
    if journal_shortlist_evidence is None and journal_shortlist:
        journal_shortlist_evidence = [
            {
                "journal_name": journal_name,
                "selection_band": "primary_fit" if index == 0 else "strong_alternative",
                "fit_summary": f"{journal_name} fits the paper framing.",
                "risk_summary": f"{journal_name} still requires a full evidence package.",
                "official_scope_sources": [f"https://example.org/{index}/scope"],
                "similar_paper_examples": [
                    {
                        "title": f"Example paper {index}",
                        "journal": journal_name,
                        "year": 2024,
                        "source_url": f"https://example.org/{index}/paper",
                        "similarity_rationale": "Same clinical prediction surface.",
                    }
                ],
                "tier_snapshot": {
                    "source": "manual_snapshot",
                    "retrieved_on": "2026-03-30",
                    "quartile": "Q1",
                },
                "confidence": "medium",
            }
            for index, journal_name in enumerate(journal_shortlist)
        ]
    if journal_shortlist_evidence:
        lines.append("journal_shortlist_evidence:")
        lines.extend(
            f"  {line}" if line else line
            for line in yaml.safe_dump(journal_shortlist_evidence, allow_unicode=True, sort_keys=False).splitlines()
        )
    if minimum_sci_ready_evidence_package:
        lines.append("minimum_sci_ready_evidence_package:")
        lines.extend(f"  - {item}" for item in minimum_sci_ready_evidence_package)
    if submission_targets_mode is not None:
        lines.append(f"submission_targets_mode: {submission_targets_mode}")
    if submission_targets:
        lines.append("submission_targets:")
        lines.extend(
            f"  {line}" if line else line
            for line in yaml.safe_dump(submission_targets, allow_unicode=True, sort_keys=False).splitlines()
        )
    if study_completion:
        lines.append("study_completion:")
        lines.extend(
            f"  {line}" if line else line
            for line in yaml.safe_dump(study_completion, allow_unicode=True, sort_keys=False).splitlines()
        )
    lines.extend(
        [
            "execution:",
            "  engine: med-deepscientist",
            "  auto_entry: on_managed_research_intent",
            "  auto_resume: true",
            f"  quest_id: {quest_id or study_id}",
            "  default_entry_mode: full_research",
            "  startup_contract_profile: paper_required_autonomous",
            f"  launch_profile: {launch_profile}",
            "  decision_policy: autonomous",
        ]
    )
    if runtime_reentry_required_paths is not None:
        lines.extend(
            [
                "  runtime_reentry_gate:",
                "    enabled: true",
                f"    execution_root: {runtime_reentry_execution_root or 'analysis/clean_room_execution'}",
                f"    first_runtime_unit: {runtime_reentry_first_unit or '00_entry_validation'}",
                f"    require_startup_hydration: {'true' if runtime_reentry_require_startup_hydration else 'false'}",
                f"    require_managed_skill_audit: {'true' if runtime_reentry_require_managed_skill_audit else 'false'}",
                "    required_paths:",
            ]
        )
        lines.extend(f"      - {path}" for path in runtime_reentry_required_paths)
    lines.extend(
        [
            "",
        ]
    )
    write_text(
        study_root / "study.yaml",
        "\n".join(lines),
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


@pytest.fixture(autouse=True)
def _patch_runtime_sidecars(monkeypatch):
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    monkeypatch.setattr(
        module.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "ensure_medical_overlay",
        lambda **kwargs: {"selected_action": "noop", "post_status": {"all_targets_ready": True}},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "materialize_runtime_medical_overlay",
        lambda **kwargs: {"materialized_surface_count": 1, "surfaces": []},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {"all_roots_ready": True, "surface_count": 1, "surfaces": []},
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_bash_sessions",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "session_count": 1,
            "live_session_count": 1,
            "live_session_ids": ["sess-default"],
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-default",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-default",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-default"],
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: {
            "ok": True,
            "snapshot": {
                "quest_id": quest_id,
                "startup_contract": startup_contract,
                "requested_baseline_ref": requested_baseline_ref,
            },
        },
    )


def test_ensure_study_runtime_creates_and_starts_new_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    created: dict[str, object] = {}
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
    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
            "startup": {"queued": True},
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: resumed.update(
            {"runtime_root": runtime_root, "quest_id": quest_id, "source": source}
        )
        or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert created["runtime_root"] == profile.med_deepscientist_runtime_root
    payload = created["payload"]
    assert payload["quest_id"] == "001-risk"
    assert payload["auto_start"] is False
    assert payload["title"] == "Diabetes mortality risk paper"
    assert payload["startup_contract"]["custom_profile"] == "freeform"
    assert payload["startup_contract"]["scope"] == "full_research"
    assert payload["startup_contract"]["baseline_mode"] == "reuse_existing_only"
    assert payload["startup_contract"]["baseline_execution_policy"] == "reuse_existing_only"
    assert "resolve-journal-shortlist" in payload["startup_contract"]["controller_first_policy_summary"]
    assert payload["startup_contract"]["submission_targets"] == []
    assert payload["startup_contract"]["journal_shortlist"]["status"] == "resolved"
    assert "resolve-submission-targets" in payload["startup_contract"]["controller_first_policy_summary"]
    assert "apply-data-asset-update" in payload["startup_contract"]["controller_first_policy_summary"]
    assert "continue until durable outputs requiring human selection are produced" in payload["startup_contract"]["automation_ready_summary"]
    assert result["startup_boundary_gate"]["allow_compute_stage"] is True
    assert result["startup_boundary_gate"]["required_first_anchor"] == "scout"
    assert result["startup_hydration"]["status"] == "hydrated"
    assert result["startup_hydration_validation"]["status"] == "clear"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
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


def test_ensure_study_runtime_uses_protocol_runtime_root_for_transport_calls(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    seen: dict[str, object] = {}
    protocol_runtime_root = tmp_path / "protocol-runtime"
    protocol_quest_root = protocol_runtime_root / "quests" / "001-risk"

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
        module.study_runtime_protocol,
        "resolve_study_runtime_context",
        lambda *, profile, study_root, study_id, quest_id: SimpleNamespace(
            runtime_root=protocol_runtime_root,
            quest_root=protocol_quest_root,
            runtime_binding_path=study_root / "runtime_binding.yaml",
            startup_payload_root=tmp_path / "protocol-startup-payloads" / study_id,
            launch_report_path=study_root / "artifacts" / "runtime" / "last_launch_report.json",
        ),
    )
    monkeypatch.setattr(
        module.quest_state,
        "inspect_quest_runtime",
        lambda quest_root: module.quest_state.QuestRuntimeSnapshot(
            quest_exists=False,
            quest_status=None,
            bash_session_audit=None,
        ),
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        seen["create_runtime_root"] = runtime_root
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "quests" / "001-risk"),
                "status": "created",
            },
        }

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        seen["resume_runtime_root"] = runtime_root
        return {"ok": True, "status": "running"}

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(module.med_deepscientist_transport, "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert seen["create_runtime_root"] == protocol_runtime_root
    assert seen["resume_runtime_root"] == protocol_runtime_root


def test_ensure_study_runtime_resume_flow_uses_protocol_quest_root_not_status_string(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    protocol_runtime_root = tmp_path / "protocol-runtime"
    protocol_quest_root = protocol_runtime_root / "quests" / "001-risk"
    seen: dict[str, Path] = {}

    monkeypatch.setattr(
        module,
        "_status_state",
        lambda **kwargs: module.StudyRuntimeStatus.from_payload(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "study_root": str(study_root),
                "entry_mode": "full_research",
                "execution": {"quest_id": "001-risk", "auto_resume": True},
                "quest_id": "001-risk",
                "quest_root": str(tmp_path / "wrong-status-quest-root"),
                "quest_exists": True,
                "quest_status": "paused",
                "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
                "runtime_binding_exists": True,
                "runtime_reentry_gate": {},
                "study_completion_contract": {},
                "decision": "resume",
                "reason": "quest_paused",
            }
        ),
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "resolve_study_runtime_context",
        lambda *, profile, study_root, study_id, quest_id: SimpleNamespace(
            runtime_root=protocol_runtime_root,
            quest_root=protocol_quest_root,
            runtime_binding_path=study_root / "runtime_binding.yaml",
            startup_payload_root=tmp_path / "protocol-startup-payloads" / study_id,
            launch_report_path=study_root / "artifacts" / "runtime" / "last_launch_report.json",
        ),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: (
            seen.__setitem__("overlay_quest_root", quest_root) or {"audit": {"all_roots_ready": True}}
        ),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda *, quest_root, hydration_payload: (
                seen.__setitem__("hydration_quest_root", quest_root) or {"status": "hydrated"}
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda *, quest_root: {"status": "clear", "blockers": []}),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert seen["overlay_quest_root"] == protocol_quest_root
    assert seen["hydration_quest_root"] == protocol_quest_root


def test_study_runtime_status_round_trips_through_typed_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
        "decision": "resume",
        "reason": "quest_paused",
        "runtime_overlay": {"audit": {"all_roots_ready": True}},
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    assert status.decision is module.StudyRuntimeDecision.RESUME
    assert status.reason is module.StudyRuntimeReason.QUEST_PAUSED
    assert status.quest_status is module.StudyRuntimeQuestStatus.PAUSED
    assert status.quest_id == "quest-001"
    assert status.quest_root == "/tmp/runtime/quests/quest-001"
    assert status.quest_exists is True
    assert status.to_dict() == payload

    status.set_decision("blocked", "startup_contract_resolution_failed")
    status.update_quest_runtime(
        quest_id="quest-002",
        quest_root="/tmp/runtime/quests/quest-002",
        quest_exists=False,
        quest_status="created",
    )

    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED
    assert status.quest_status is module.StudyRuntimeQuestStatus.CREATED
    assert status.quest_id == "quest-002"
    assert status.quest_root == "/tmp/runtime/quests/quest-002"
    assert status.quest_exists is False
    assert status.to_dict()["decision"] == "blocked"
    assert status.to_dict()["reason"] == "startup_contract_resolution_failed"
    assert status.to_dict()["quest_status"] == "created"
    assert status.to_dict()["quest_id"] == "quest-002"
    assert status.to_dict()["quest_root"] == "/tmp/runtime/quests/quest-002"


def test_study_runtime_status_treats_stopped_quest_as_resumable(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stopped"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_mapping_semantics_follow_serialized_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    assert dict(status) == payload
    assert "decision" not in status
    assert status.get("decision", "fallback") == "fallback"


def test_study_runtime_status_core_key_assignment_uses_typed_normalization() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    status["decision"] = "blocked"
    status["reason"] = "runtime_overlay_not_ready"
    status["quest_root"] = Path("/tmp/runtime/quests/quest-002")
    status["quest_exists"] = False
    status["quest_status"] = None

    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY
    assert status.quest_root == "/tmp/runtime/quests/quest-002"
    assert status.quest_exists is False
    assert status.quest_status is None
    assert status.to_dict()["quest_root"] == "/tmp/runtime/quests/quest-002"

    with pytest.raises(TypeError, match="quest_exists"):
        status["quest_exists"] = "false"


def test_study_runtime_status_rejects_unknown_decision_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    with pytest.raises(ValueError, match="unknown study runtime decision"):
        status.set_decision("unexpected_action", "test_only")


def test_study_runtime_status_rejects_unknown_reason_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    with pytest.raises(ValueError, match="unknown study runtime reason"):
        status.set_decision("blocked", "unexpected_reason")


def test_study_runtime_status_rejects_unknown_quest_status_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    with pytest.raises(ValueError, match="unknown study runtime quest status"):
        status.update_quest_runtime(quest_status="unexpected_status")


def test_study_runtime_status_records_structured_runtime_extras() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    status.record_analysis_bundle({"ready": True})
    status.record_runtime_overlay({"audit": {"all_roots_ready": True}})
    status.record_startup_contract_validation({"status": "clear"})
    status.record_startup_context_sync({"ok": True})
    status.record_startup_hydration({"status": "hydrated"}, {"status": "clear"})
    status.record_completion_sync({"ok": True})
    status.record_bash_session_audit({"status": "live"})
    status.record_runtime_artifacts(
        runtime_binding_path=Path("/tmp/studies/001-risk/runtime_binding.updated.yaml"),
        launch_report_path=Path("/tmp/studies/001-risk/launch_report.json"),
        startup_payload_path=Path("/tmp/runtime/startup_payloads/001-risk.json"),
    )

    payload = status.to_dict()

    assert payload["analysis_bundle"] == {"ready": True}
    assert payload["runtime_overlay"] == {"audit": {"all_roots_ready": True}}
    assert payload["startup_contract_validation"] == {"status": "clear"}
    assert payload["startup_context_sync"] == {"ok": True}
    assert payload["startup_hydration"] == {"status": "hydrated"}
    assert payload["startup_hydration_validation"] == {"status": "clear"}
    assert payload["completion_sync"] == {"ok": True}
    assert payload["bash_session_audit"] == {"status": "live"}
    assert payload["runtime_binding_path"] == "/tmp/studies/001-risk/runtime_binding.updated.yaml"
    assert payload["launch_report_path"] == "/tmp/studies/001-risk/launch_report.json"
    assert payload["startup_payload_path"] == "/tmp/runtime/startup_payloads/001-risk.json"


def test_execute_runtime_decision_returns_terminal_outcome_for_completed_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    resolved_study_id, resolved_study_root, study_payload = module._resolve_study(
        profile=profile,
        study_id="001-risk",
        study_root=None,
    )
    status = module._status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=None,
    )
    status.set_decision("completed", "quest_already_completed")
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action == "completed"
    assert outcome.daemon_result is None
    assert outcome.startup_payload_path is None


def test_execute_runtime_decision_rejects_unknown_decision(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    resolved_study_id, resolved_study_root, study_payload = module._resolve_study(
        profile=profile,
        study_id="001-risk",
        study_root=None,
    )
    status = module._status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=None,
    )
    status.decision = "unexpected_action"
    status.reason = module.StudyRuntimeReason.QUEST_ALREADY_COMPLETED
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    with pytest.raises(ValueError, match="unsupported study runtime decision"):
        module._execute_runtime_decision(status=status, context=context)


def test_ensure_study_runtime_uses_study_runtime_protocol_persistence_helpers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    seen: dict[str, object] = {}

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
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "quests" / "001-risk"),
                "status": "created",
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "write_startup_payload",
        lambda *, startup_payload_root, create_payload, slug: seen.setdefault(
            "startup_payload_calls",
            [],
        ).append(
            {
                "startup_payload_root": startup_payload_root,
                "create_payload": create_payload,
                "slug": slug,
            }
        )
        or (tmp_path / "protocol-startup-payload.json"),
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "persist_runtime_artifacts",
        lambda **kwargs: seen.setdefault("persist_calls", []).append(kwargs)
        or module.study_runtime_protocol.StudyRuntimeArtifacts(
            runtime_binding_path=kwargs["runtime_binding_path"],
            launch_report_path=kwargs["launch_report_path"],
            startup_payload_path=kwargs["startup_payload_path"],
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert isinstance(result, dict)
    assert result["decision"] == "create_and_start"
    assert len(seen["startup_payload_calls"]) == 1
    assert seen["startup_payload_calls"][0]["create_payload"]["quest_id"] == "001-risk"
    assert len(seen["persist_calls"]) == 1
    assert seen["persist_calls"][0]["last_action"] == "create_and_start"
    assert seen["persist_calls"][0]["source"] == "medautosci-test"


def test_study_runtime_status_prefers_study_completion_contract_over_boundary_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_status="completed",
        study_completion={
            "status": "completed",
            "summary": "Study-level finalized delivery is complete.",
            "user_approval_text": "同意",
            "evidence_paths": [
                "notes/revision_status.md",
                "manuscript/final/submission_manifest.json",
            ],
        },
    )
    write_text(study_root / "notes" / "revision_status.md", "# Revision\n")
    write_text(study_root / "manuscript" / "final" / "submission_manifest.json", "{}\n")

    monkeypatch.setattr(
        module.quest_state,
        "inspect_quest_runtime",
        lambda quest_root: module.quest_state.QuestRuntimeSnapshot(
            quest_exists=True,
            quest_status="paused",
            bash_session_audit=None,
        ),
    )
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "sync_completion"
    assert result["reason"] == "study_completion_ready"
    assert result["study_completion_contract"]["status"] == "resolved"
    assert result["study_completion_contract"]["ready"] is True


def test_ensure_study_runtime_syncs_study_completion_into_managed_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_status="completed",
        quest_id="001-risk-managed",
        study_completion={
            "status": "completed",
            "summary": "Study-level finalized delivery is complete.",
            "user_approval_text": "同意",
            "evidence_paths": [
                "notes/revision_status.md",
                "manuscript/final/submission_manifest.json",
            ],
        },
    )
    write_text(study_root / "notes" / "revision_status.md", "# Revision\n")
    write_text(study_root / "manuscript" / "final" / "submission_manifest.json", "{}\n")

    monkeypatch.setattr(
        module.quest_state,
        "inspect_quest_runtime",
        lambda quest_root: module.quest_state.QuestRuntimeSnapshot(
            quest_exists=True,
            quest_status="paused",
            bash_session_audit=None,
        ),
    )
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
        module.med_deepscientist_transport,
        "sync_completion_with_approval",
        lambda *, runtime_root, quest_id, decision_request_payload, approval_text, summary, source: {
            "completion_request": {
                "status": "ok",
                "interaction_id": "decision-001",
                "payload": decision_request_payload,
            },
            "approval_message": {
                "ok": True,
                "message": {
                    "id": "msg-approval",
                    "content": approval_text,
                },
            },
            "completion": {
                "ok": True,
                "status": "completed",
                "snapshot": {"quest_id": quest_id, "status": "completed"},
                "message": summary,
            },
        },
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")
    runtime_binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    launch_report = json.loads((study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8"))

    assert result["decision"] == "completed"
    assert result["reason"] == "study_completion_synced"
    assert result["quest_status"] == "completed"
    assert result["completion_sync"]["completion"]["status"] == "completed"
    assert runtime_binding["last_action"] == "completed"
    assert launch_report["decision"] == "completed"
    assert launch_report["reason"] == "study_completion_synced"


def test_build_study_completion_request_message_accepts_typed_completion_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    completion_module = importlib.import_module("med_autoscience.study_completion")
    study_root = tmp_path / "study"
    completion_state = completion_module.StudyCompletionState(
        status="resolved",
        contract=completion_module.StudyCompletionContract(
            study_root=study_root,
            status="completed",
            summary="Study-level finalized delivery is complete.",
            user_approval_text="同意",
            completed_at="2026-04-03T00:00:00+00:00",
            evidence_paths=(
                "notes/revision_status.md",
                "manuscript/final/submission_manifest.json",
            ),
            missing_evidence_paths=(),
        ),
        errors=(),
    )

    message = module._build_study_completion_request_message(
        study_id="001-risk",
        study_root=study_root,
        completion_state=completion_state,
    )

    assert "Completion summary: Study-level finalized delivery is complete." in message
    assert "- `notes/revision_status.md`" in message
    assert "Please record explicit quest-completion approval" in message


def test_ensure_study_runtime_prefers_runtime_reentry_anchor_when_configured(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_first_unit="00_entry_validation",
    )
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
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
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: created.update({"runtime_root": runtime_root, "payload": payload})
        or {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    contract = created["payload"]["startup_contract"]
    assert result["decision"] == "create_and_start"
    assert result["startup_boundary_gate"]["required_first_anchor"] == "00_entry_validation"
    assert result["startup_boundary_gate"]["effective_custom_profile"] == "continue_existing_state"
    assert contract["required_first_anchor"] == "00_entry_validation"
    assert contract["custom_profile"] == "continue_existing_state"


def test_ensure_study_runtime_creates_quest_before_runtime_overlay_materialization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    call_order: list[str] = []

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
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: call_order.append("prepare")
        or {"authority": {"selected_action": "noop"}, "materialization": {}, "audit": {"all_roots_ready": True}},
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: call_order.append("create")
        or {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert call_order[:2] == ["create", "prepare"]


def test_ensure_study_runtime_includes_medical_runtime_contracts(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    created: dict[str, object] = {}
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        endpoint_type="binary",
    )

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

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")
    startup_contract = created["payload"]["startup_contract"]

    assert startup_contract["schema_version"] == 4
    assert startup_contract["medical_analysis_contract_summary"]["status"] == "resolved"
    assert startup_contract["medical_analysis_contract_summary"]["study_archetype"] == "clinical_classifier"
    assert startup_contract["medical_analysis_contract_summary"]["endpoint_type"] == "binary"
    assert startup_contract["medical_reporting_contract_summary"]["reporting_guideline_family"] == "TRIPOD"
    assert startup_contract["reporting_guideline_family"] == "TRIPOD"


def test_ensure_study_runtime_blocks_before_create_when_reporting_contract_is_unresolved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        **{
            **make_profile(tmp_path).__dict__,
            "default_submission_targets": (
                {
                    "publication_profile": "unsupported_profile",
                    "primary": True,
                    "package_required": True,
                    "story_surface": "general_medical_journal",
                },
            ),
        }
    )
    created: dict[str, object] = {}
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        endpoint_type="binary",
    )

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

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
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

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_contract_resolution_failed"
    assert result["startup_contract_validation"]["blockers"] == [
        "unsupported_medical_analysis_contract",
        "unsupported_medical_reporting_contract",
    ]
    assert "payload" not in created


def test_ensure_study_runtime_hydrates_before_resume(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )

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
    calls: list[tuple[str, object]] = []

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        calls.append(("create", payload["auto_start"]))
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert calls == [
        ("create", False),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_blocks_when_hydration_validation_fails(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    calls: list[tuple[str, object]] = []

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
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: calls.append(("create", payload["auto_start"]))
        or {"ok": True, "snapshot": {"quest_id": "001-risk", "status": "created"}},
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "blocked", "blockers": ["missing_medical_reporting_contract"]}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "hydration_validation_failed"
    assert result["startup_hydration_validation"]["status"] == "blocked"
    assert calls == [
        ("create", False),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
    ]


def test_ensure_study_runtime_blocks_before_create_when_startup_contract_is_unresolved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = replace(make_profile(tmp_path), preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    write_study(
        profile.workspace_root,
        "001-risk",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
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
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: created.setdefault("payload", payload)
        or {"ok": True, "snapshot": {"quest_id": "001-risk", "status": "created"}},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_contract_resolution_failed"
    assert result["startup_contract_validation"]["status"] == "blocked"
    assert result["startup_contract_validation"]["blockers"] == [
        "unsupported_medical_analysis_contract",
        "unsupported_medical_reporting_contract",
    ]
    assert "payload" not in created


def test_ensure_study_runtime_archives_invalid_partial_quest_root_before_create(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    invalid_quest_root = profile.runtime_root / "001-risk"
    write_text(invalid_quest_root / "paper" / "medical_analysis_contract.json", '{"status":"unsupported"}\n')
    created: dict[str, object] = {}

    monkeypatch.setattr(module, "_timestamp_slug", lambda: "20260402T010203Z")
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

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["payload"] = payload
        assert not invalid_quest_root.exists()
        write_text(invalid_quest_root / "quest.yaml", "quest_id: 001-risk\n")
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(invalid_quest_root),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda **kwargs: {"status": "clear", "blockers": []}),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    archived_root = (
        profile.med_deepscientist_runtime_root
        / "recovery"
        / "invalid_partial_quest_roots"
        / "001-risk-20260402T010203Z"
    )
    assert result["partial_quest_recovery"]["status"] == "archived_invalid_partial_quest_root"
    assert result["partial_quest_recovery"]["archived_root"] == str(archived_root)
    assert archived_root.joinpath("paper", "medical_analysis_contract.json").exists()
    assert created["payload"]["quest_id"] == "001-risk"


def test_ensure_study_runtime_refreshes_startup_hydration_for_existing_created_quest_when_resume_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    calls: list[tuple[str, object]] = []

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
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"))
        )
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["startup_hydration_validation"]["status"] == "clear"
    assert calls == [
        ("sync_startup_context", "001-risk", "full_research"),
        ("hydrate", quest_root),
        ("validate", quest_root),
    ]


def test_ensure_study_runtime_uses_protocol_refresh_gate_for_blocked_existing_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    calls: list[str] = []

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
        module.study_runtime_protocol,
        "should_refresh_startup_hydration_while_blocked",
        lambda status: False,
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append("hydrate") or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda **kwargs: calls.append("validate") or {"status": "clear", "blockers": []}),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert calls == []


def test_ensure_study_runtime_resumes_paused_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    calls: list[tuple[str, object]] = []

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
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_resume_rehydrates_when_runtime_reentry_requires_startup_hydration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    calls: list[tuple[str, object]] = []

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
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_blocks_resume_when_runtime_reentry_hydration_validation_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    calls: list[tuple[str, object]] = []

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
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "blocked", "blockers": ["unsupported_medical_analysis_contract"]}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "hydration_validation_failed"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
    ]


def test_ensure_study_runtime_blocks_when_managed_skill_audit_is_required_but_overlay_is_disabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = replace(make_profile(tmp_path), enable_medical_overlay=False)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_managed_skill_audit=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')

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

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "managed_skill_audit_not_available"


def test_ensure_study_runtime_pauses_running_quest_when_required_startup_hydration_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    write_text(quest_root / "paper" / "medical_analysis_contract.json", '{\"status\":\"unsupported\"}\n')
    write_text(quest_root / "paper" / "medical_reporting_contract.json", '{\"status\":\"resolved\"}\n')

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
        module.med_deepscientist_transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "paused"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "runtime_reentry_not_ready_for_running_quest"
    assert "unsupported_medical_analysis_contract" in result["runtime_reentry_gate"]["blockers"]


def test_ensure_study_runtime_noops_when_quest_is_already_running(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-1"],
            },
        },
    )
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"
    assert result["runtime_liveness_audit"]["status"] == "live"
    assert result["bash_session_audit"]["status"] == "live"


def test_ensure_study_runtime_resumes_running_quest_when_daemon_has_no_live_session(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    calls: list[tuple[str, object]] = []

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
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-stale",
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": "run-stale",
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_marked_running_but_no_live_session"
    assert result["runtime_liveness_audit"]["status"] == "none"
    assert result["bash_session_audit"]["status"] == "none"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_blocks_running_quest_when_live_session_audit_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": False,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": False,
                "status": "unknown",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": None,
                "worker_pending": None,
                "stop_requested": None,
                "error": "daemon unavailable",
            },
            "bash_session_audit": {
                "ok": False,
                "status": "unknown",
                "session_count": None,
                "live_session_count": None,
                "live_session_ids": [],
                "error": "daemon unavailable",
            },
            "error": "daemon unavailable | daemon unavailable",
        },
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "running_quest_live_session_audit_failed"
    assert result["runtime_liveness_audit"]["status"] == "unknown"
    assert result["bash_session_audit"]["status"] == "unknown"


def test_ensure_study_runtime_stays_lightweight_for_non_managed_entry_mode(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )

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
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", entry_mode="literature_scout")

    assert result["decision"] == "lightweight"
    assert result["reason"] == "entry_mode_not_managed"


def test_ensure_study_runtime_blocks_when_study_has_unresolved_data_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )

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
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_data_readiness_blocked"


def test_ensure_study_runtime_creates_without_starting_when_startup_boundary_is_incomplete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
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

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    payload = created["payload"]
    contract = payload["startup_contract"]
    assert result["decision"] == "create_only"
    assert result["reason"] == "startup_boundary_not_ready_for_auto_start"
    assert payload["auto_start"] is False
    assert result["startup_boundary_gate"]["allow_compute_stage"] is False
    assert result["startup_boundary_gate"]["required_first_anchor"] == "scout"
    assert result["startup_boundary_gate"]["missing_requirements"] == [
        "paper_framing",
        "journal_shortlist",
        "evidence_package",
    ]
    assert contract["custom_profile"] == "freeform"
    assert contract["scope"] == "full_research"
    assert contract["baseline_mode"] == "stop_if_insufficient"
    assert contract["baseline_execution_policy"] == "skip_unless_blocking"
    assert contract["required_first_anchor"] == "scout"
    assert contract["legacy_code_execution_allowed"] is False
    assert contract["startup_boundary_gate"]["allow_compute_stage"] is False
    assert "resolve-reference-papers" in contract["controller_first_policy_summary"]
    assert "Only when the platform does not already provide a stable controller" in contract["controller_first_policy_summary"]
    assert "when a study boundary is explicit and startup-ready" in contract["automation_ready_summary"]
    assert "Do not enter baseline, experiment, or analysis-campaign" in contract["custom_brief"]
    assert "Do not execute legacy implementation code" in contract["custom_brief"]
    assert "prefer mature MedAutoScience controllers before freeform external execution" in contract["custom_brief"]


def test_ensure_study_runtime_blocks_when_runtime_reentry_gate_is_incomplete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=["analysis/paper_facing_evidence_contract.md"],
        runtime_reentry_first_unit="10_china_primary_endpoint",
    )

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

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "runtime_reentry_not_ready_for_auto_start"
    assert result["runtime_reentry_gate"]["allow_runtime_entry"] is False
    assert "missing_required_path:analysis/paper_facing_evidence_contract.md" in result["runtime_reentry_gate"]["blockers"]


def test_ensure_study_runtime_applies_startup_boundary_to_non_continue_launch_profiles(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        launch_profile="review_audit",
    )
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

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    payload = created["payload"]
    contract = payload["startup_contract"]
    assert result["decision"] == "create_only"
    assert payload["auto_start"] is False
    assert contract["scope"] == "full_research"
    assert contract["baseline_mode"] == "stop_if_insufficient"
    assert contract["baseline_execution_policy"] == "skip_unless_blocking"
    assert contract["required_first_anchor"] == "scout"
    assert contract["startup_boundary_gate"]["status"] == "scout_first_required"


def test_ensure_study_runtime_pauses_running_quest_when_startup_boundary_disallows_compute(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    paused: dict[str, object] = {}

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

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        paused["runtime_root"] = runtime_root
        paused["quest_id"] = quest_id
        paused["source"] = source
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module.med_deepscientist_transport, "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "startup_boundary_not_ready_for_running_quest"
    assert result["quest_status"] == "paused"
    assert paused == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_ensure_study_runtime_blocks_resume_when_startup_boundary_disallows_compute(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')

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

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["startup_boundary_gate"]["allow_compute_stage"] is False


def test_study_runtime_status_requires_evidence_backed_journal_shortlist(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["Heart"],
        journal_shortlist_evidence=[],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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

    result = module.study_runtime_status(
        profile=profile,
        study_root=study_root,
    )

    assert result["startup_boundary_gate"]["allow_compute_stage"] is False
    assert result["startup_boundary_gate"]["journal_shortlist_ready"] is False
    assert result["startup_boundary_gate"]["journal_shortlist_contract_status"] == "absent"


def test_ensure_study_runtime_uses_protocol_hydration_payload_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    seen: dict[str, object] = {}

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
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: {
            "ok": True,
            "snapshot": {"quest_id": "001-risk", "quest_root": str(runtime_root / "001-risk"), "status": "created"},
        },
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "build_hydration_payload",
        lambda *, create_payload: seen.setdefault("hydration_payload", {"sentinel": True}),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda *, quest_root, hydration_payload: seen.setdefault("run_hydration", hydration_payload)
            or {"status": "hydrated"}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda *, quest_root: {"status": "clear", "blockers": []}),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "create_and_start"
    assert seen["hydration_payload"] == {"sentinel": True}
    assert seen["run_hydration"] == {"sentinel": True}


def test_ensure_study_runtime_uses_protocol_startup_contract_validation(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    called: dict[str, object] = {"create_called": False}

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
        module.study_runtime_protocol,
        "validate_startup_contract_resolution",
        lambda *, startup_contract: module.study_runtime_protocol.StartupContractValidation(
            status="blocked",
            blockers=("forced_blocker",),
            medical_analysis_contract_status=None,
            medical_reporting_contract_status=None,
            medical_analysis_reason_code=None,
            medical_reporting_reason_code=None,
        ),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda **kwargs: called.__setitem__("create_called", True) or {},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["startup_contract_validation"]["blockers"] == ["forced_blocker"]
    assert called["create_called"] is False


def test_ensure_study_runtime_resumes_idle_quest_after_startup_boundary_clears(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
    calls: list[tuple[str, object]] = []

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
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"))
        )
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_initialized_waiting_to_start"
    assert result["quest_status"] == "active"
    assert calls == [
        ("sync_startup_context", "001-risk", "full_research"),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_uses_custom_quest_id_for_existing_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="001-risk-reentry",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk-reentry"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk-reentry\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
    calls: list[tuple[str, object]] = []

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
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"])) or {"status": "hydrated"}),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or {"status": "clear", "blockers": []}
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"))
        )
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["quest_id"] == "001-risk-reentry"
    assert result["quest_root"] == str(profile.runtime_root / "001-risk-reentry")
    assert result["quest_status"] == "active"
    assert calls == [
        ("sync_startup_context", "001-risk-reentry", "full_research"),
        ("hydrate", profile.runtime_root / "001-risk-reentry"),
        ("validate", profile.runtime_root / "001-risk-reentry"),
        ("resume", "001-risk-reentry"),
    ]


def test_ensure_study_runtime_blocks_when_analysis_bundle_is_not_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )

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
        module.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "ensure_bundle", "ready": False},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_runtime_analysis_bundle_not_ready"
    assert result["analysis_bundle"]["ready"] is False


def test_ensure_study_runtime_pauses_running_quest_when_runtime_overlay_audit_fails(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    paused: dict[str, object] = {}

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
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {
            "all_roots_ready": False,
            "surface_count": 2,
            "surfaces": [{"surface": "quest"}, {"surface": "worktree"}],
        },
    )

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        paused["runtime_root"] = runtime_root
        paused["quest_id"] = quest_id
        paused["source"] = source
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module.med_deepscientist_transport, "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "runtime_overlay_audit_failed_for_running_quest"
    assert result["quest_status"] == "paused"
    assert paused == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
