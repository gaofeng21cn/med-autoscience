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
        default_startup_anchor_policy="scout_first_for_continue_existing_state",
        legacy_code_execution_policy="forbid_without_user_approval",
        startup_boundary_requirements=("paper_framing", "journal_shortlist", "evidence_package"),
    )


def write_study(
    workspace_root: Path,
    study_id: str,
    *,
    paper_framing_summary: str | None = None,
    paper_urls: list[str] | None = None,
    journal_shortlist: list[str] | None = None,
    journal_shortlist_evidence: list[dict[str, object]] | None = None,
    minimum_sci_ready_evidence_package: list[str] | None = None,
    launch_profile: str = "continue_existing_state",
    runtime_reentry_required_paths: list[str] | None = None,
    runtime_reentry_execution_root: str | None = None,
    runtime_reentry_first_unit: str | None = None,
) -> Path:
    study_root = workspace_root / "studies" / study_id
    write_text(workspace_root / "ops" / "deepscientist" / "startup_briefs" / f"{study_id}.md", "# Startup brief\n")
    lines = [
        f"study_id: {study_id}",
        "title: Diabetes mortality risk paper",
        "status: ready",
        "primary_question: >",
        "  Build a submission-ready survival-risk study.",
        "brief_file: brief.md",
        "protocol_file: protocol.md",
        f"startup_brief: ../../ops/deepscientist/startup_briefs/{study_id}.md",
    ]
    if paper_framing_summary is not None:
        lines.extend(
            [
                "paper_framing_summary: >",
                f"  {paper_framing_summary}",
            ]
        )
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
    lines.extend(
        [
            "execution:",
            "  engine: deepscientist",
            "  auto_entry: on_managed_research_intent",
            "  auto_resume: true",
            f"  quest_id: {study_id}",
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


def test_ensure_study_runtime_creates_and_starts_new_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
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
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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
    write_study(
        profile.workspace_root,
        "001-risk",
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
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_data_readiness_blocked"


def test_ensure_study_runtime_creates_without_starting_when_startup_boundary_is_incomplete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
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

    monkeypatch.setattr(module.daemon_api, "create_quest", fake_create_quest)

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

    monkeypatch.setattr(module.daemon_api, "create_quest", fake_create_quest)

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
    write_study(profile.workspace_root, "001-risk")
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

    monkeypatch.setattr(module.daemon_api, "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "startup_boundary_not_ready_for_running_quest"
    assert result["quest_status"] == "paused"
    assert paused == {
        "runtime_root": profile.deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_ensure_study_runtime_blocks_resume_when_startup_boundary_disallows_compute(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
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


def test_ensure_study_runtime_resumes_idle_quest_after_startup_boundary_clears(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
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

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        resumed["runtime_root"] = runtime_root
        resumed["quest_id"] = quest_id
        resumed["source"] = source
        return {"ok": True, "status": "active"}

    monkeypatch.setattr(module.daemon_api, "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_initialized_waiting_to_start"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
