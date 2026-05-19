from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_runtime_workspace_monolith_migrate_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_run_workspace_monolith_migration(*, profile_path: Path, apply: bool) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["apply"] = apply
        return {"surface_kind": "workspace_monolith_migration", "mode": "apply"}

    monkeypatch.setattr(
        cli.workspace_monolith_migration,
        "run_workspace_monolith_migration",
        fake_run_workspace_monolith_migration,
    )

    exit_code = cli.main(
        [
            "runtime",
            "workspace-monolith-migrate",
            "--profile",
            str(profile_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "apply": True}
    assert json.loads(captured.out)["mode"] == "apply"


def test_workspace_legacy_physical_cleanup_audit_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_build_workspace_legacy_physical_cleanup_audit(*, profile_path: Path) -> dict[str, object]:
        called["profile_path"] = profile_path
        return {"surface_kind": "workspace_legacy_physical_cleanup_audit", "mode": "audit_only"}

    monkeypatch.setattr(
        cli.workspace_legacy_physical_cleanup,
        "build_workspace_legacy_physical_cleanup_audit",
        fake_build_workspace_legacy_physical_cleanup_audit,
    )

    exit_code = cli.main(
        [
            "workspace-legacy-physical-cleanup-audit",
            "--profile",
            str(profile_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"profile_path": profile_path}
    assert json.loads(captured.out)["mode"] == "audit_only"


def test_workspace_legacy_physical_cleanup_apply_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_apply_workspace_legacy_physical_cleanup(*, profile_path: Path, apply: bool) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["apply"] = apply
        return {"surface_kind": "workspace_legacy_physical_cleanup_apply", "mode": "apply"}

    monkeypatch.setattr(
        cli.workspace_legacy_physical_cleanup,
        "apply_workspace_legacy_physical_cleanup",
        fake_apply_workspace_legacy_physical_cleanup,
    )

    exit_code = cli.main(
        [
            "workspace-legacy-physical-cleanup-apply",
            "--profile",
            str(profile_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "apply": True}
    assert json.loads(captured.out)["mode"] == "apply"


def test_publication_clean_authority_migration_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_run_paper_authority_clean_migration(
        *,
        profile_path: Path,
        study_ids: tuple[str, ...],
        apply: bool,
    ) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["study_ids"] = study_ids
        called["apply"] = apply
        return {"surface_kind": "paper_authority_clean_migration", "mode": "apply"}

    monkeypatch.setattr(
        cli.paper_authority_migration,
        "run_paper_authority_clean_migration",
        fake_run_paper_authority_clean_migration,
    )

    exit_code = cli.main(
        [
            "publication",
            "clean-authority-migration",
            "--profile",
            str(profile_path),
            "--studies",
            "002-dm-china-us-mortality-attribution",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "profile_path": profile_path,
        "study_ids": ("002-dm-china-us-mortality-attribution",),
        "apply": True,
    }
    assert json.loads(captured.out)["surface_kind"] == "paper_authority_clean_migration"


def test_runtime_study_config_clean_migration_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_run_study_config_clean_migration(
        *,
        profile_path: Path,
        study_ids: tuple[str, ...],
        apply: bool,
    ) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["study_ids"] = study_ids
        called["apply"] = apply
        return {"surface_kind": "study_config_clean_migration", "mode": "apply"}

    monkeypatch.setattr(
        cli.study_config_migration,
        "run_study_config_clean_migration",
        fake_run_study_config_clean_migration,
    )

    exit_code = cli.main(
        [
            "runtime",
            "study-config-clean-migration",
            "--profile",
            str(profile_path),
            "--studies",
            "001-dm-cvd-mortality-risk",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "profile_path": profile_path,
        "study_ids": ("001-dm-cvd-mortality-risk",),
        "apply": True,
    }
    assert json.loads(captured.out)["surface_kind"] == "study_config_clean_migration"


def test_agent_lab_medical_manuscript_quality_suite_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    called: dict[str, object] = {}

    def fake_materialize_medical_manuscript_quality_agent_lab_suite(
        *,
        study_root: Path,
        reviewer_feedback_ref: str | None = None,
    ) -> dict[str, object]:
        called["study_root"] = study_root
        called["reviewer_feedback_ref"] = reviewer_feedback_ref
        return {
            "surface_kind": "mas_agent_lab_medical_manuscript_quality_suite",
            "status": "materialized",
        }

    monkeypatch.setattr(
        cli.agent_lab_medical_manuscript_quality,
        "materialize_medical_manuscript_quality_agent_lab_suite",
        fake_materialize_medical_manuscript_quality_agent_lab_suite,
    )

    exit_code = cli.main(
        [
            "agent-lab-medical-manuscript-quality-suite",
            "--study-root",
            str(study_root),
            "--reviewer-feedback-ref",
            "task-intake:gpt-5.5-review",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "study_root": study_root,
        "reviewer_feedback_ref": "task-intake:gpt-5.5-review",
    }
    assert json.loads(captured.out)["surface_kind"] == "mas_agent_lab_medical_manuscript_quality_suite"


def test_agent_lab_medical_manuscript_quality_suite_dry_run_exposes_mechanism_inputs(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must re-evaluate manuscript quality.",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "research_wiki" / "latest.json",
        {
            "paper_refs": [{"ref": "paper-ref:dm002-current-draft"}],
            "claim_refs": [{"claim_ref": "claim-ref:hdl-unit-contamination"}],
            "experiment_refs": [{"experiment_ref": "experiment-ref:external-validation-replay"}],
            "failed_ideas": [{"id": "failed-idea:mechanical-completeness-gate"}],
            "negative_results": [{"ref": "negative-result:uncalibrated-risk-collapse"}],
            "rationale_refs": ["rationale-ref:ai-reviewer-quality-route-back"],
            "failed_routes": [{"ref": "failed-route:internal-quality-language"}],
        },
    )
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {
            "review_refs": ["review-ref:hdl-harmonization"],
            "mechanism_patch_refs": ["mechanism-patch-ref:reviewer-route-hardening"],
        },
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "evidence_refs": ["evidence-ref:raw-cox-transport-output"],
            "raw_evidence_refs": ["raw-evidence-ref:cox-transport-jsonl"],
        },
    )
    _write_json(
        study_root / "artifacts" / "raw_evidence" / "latest.json",
        {
            "raw_evidence_refs": ["raw-evidence-ref:cox-transport-jsonl"],
            "source_refs": ["source-ref:transport-model-provenance"],
        },
    )
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "claims": [{"claim_ref": "claim-ref:external-validation-performance"}],
            "evidence_refs": ["evidence-ref:cox-transport-validation"],
            "display_refs": ["display-ref:table-2-performance"],
        },
    )
    _write_json(
        study_root / "artifacts" / "analysis_queue" / "latest.json",
        {
            "queue_ref": "analysis-queue:dm002/reviewer-repair",
            "state": "active",
            "retry_policy": "retry-policy:mas/analysis-campaign/manual-owner-retry",
            "budget": {"budget_ref": "analysis-budget:dm002/reviewer-repair"},
            "items": [
                {
                    "ref": "analysis-queue:hdl-harmonization",
                    "state": "blocked",
                    "retry_count": "2",
                    "budget_cost": 5,
                    "source_refs": ["paper-ref:dm002-current-draft"],
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        {
            "queue_ref": "analysis-campaign-queue:dm002/reviewer-repair",
            "state": "recoverable",
            "items": [
                {
                    "ref": "analysis-campaign-item:dm002/provenance-recovery",
                    "state": "blocked",
                    "source_refs": ["raw-evidence-ref:cox-transport-jsonl"],
                }
            ],
        },
    )
    events_path = study_root / ".ds" / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text(
        '{"event_ref":"runtime-event:dm002/controller-route","event_type":"controller_route_selected"}\n',
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"runtime_event_refs": ["runtime-event:dm002/controller-decision-recorded"]},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "provider_state.json",
        {
            "provider_refs": ["provider-ref:temporal-production"],
            "fallback_refs": ["provider-fallback-ref:local-diagnostic-only"],
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "executor_context.json",
        {
            "executor_refs": ["executor-ref:codex_cli"],
            "context_isolation_refs": ["context-isolation-ref:reviewer-no-shared-context"],
        },
    )
    _write_json(
        study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "source_kind": "publication_gate_report",
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["source_provenance_recovery_required"],
            "evidence_refs": ["evidence-ref:raw-cox-transport-output"],
            "review_refs": ["review-ref:hdl-harmonization"],
        },
    )
    _write_json(
        study_root / "artifacts" / "submission_targets" / "latest.json",
        {"target_venue_refs": ["venue-route-ref:target-journal"]},
    )
    (study_root / "paper" / "citation_audit.json").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "paper" / "citation_audit.json").write_text("{}\n", encoding="utf-8")
    (study_root / "paper" / "anonymity_check.json").write_text("{}\n", encoding="utf-8")
    (study_root / "talk").mkdir(parents=True, exist_ok=True)
    (study_root / "talk" / "slides.pptx").write_text("pptx placeholder", encoding="utf-8")
    (study_root / "artifacts" / "overleaf").mkdir(parents=True, exist_ok=True)
    (study_root / "artifacts" / "overleaf" / "status.json").write_text("{}\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "agent-lab-medical-manuscript-quality-suite",
            "--study-root",
            str(study_root),
            "--dry-run",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    task = output["suite"]["tasks"][0]
    mechanism_inputs = task["mechanism_evolution_inputs"]

    assert exit_code == 0
    assert mechanism_inputs["surface_kind"] == "mas_agent_lab_mechanism_evolution_inputs"
    assert mechanism_inputs["target_opl_surface"] == "opl_agent_lab_evolution_result"
    assert any("research_wiki/latest.json" in ref for ref in mechanism_inputs["research_wiki_refs"])
    assert any("analysis_queue/latest.json" in ref for ref in mechanism_inputs["analysis_queue_manifest_refs"])
    graph = mechanism_inputs["research_memory_graph"]
    assert graph["paper_refs"] == ["paper-ref:dm002-current-draft"]
    assert graph["claim_refs"] == ["claim-ref:hdl-unit-contamination"]
    assert graph["experiment_refs"] == ["experiment-ref:external-validation-replay"]
    assert graph["failed_idea_refs"] == ["failed-idea:mechanical-completeness-gate"]
    assert graph["negative_result_refs"] == ["negative-result:uncalibrated-risk-collapse"]
    assert graph["reusable_rationale_refs"] == ["rationale-ref:ai-reviewer-quality-route-back"]
    assert graph["failed_route_refs"] == ["failed-route:internal-quality-language"]
    assert graph["body_included"] is False
    queue = mechanism_inputs["analysis_queue_manifest"]
    assert queue["queue_ref"] == "analysis-queue:dm002/reviewer-repair"
    assert queue["state"] == "active"
    assert queue["retry_policy"] == {"policy_ref": "retry-policy:mas/analysis-campaign/manual-owner-retry"}
    assert queue["budget"] == {"budget_ref": "analysis-budget:dm002/reviewer-repair"}
    assert {
        "ref": "analysis-queue:hdl-harmonization",
        "state": "blocked",
        "retry_count": 2,
        "budget_cost": 5,
        "source_refs": ["paper-ref:dm002-current-draft"],
    } in queue["items"]
    assert {
        "ref": "analysis-campaign-item:dm002/provenance-recovery",
        "state": "blocked",
        "retry_count": 0,
        "budget_cost": 0,
        "source_refs": ["raw-evidence-ref:cox-transport-jsonl"],
    } in queue["items"]
    assert queue["body_included"] is False
    runtime_events = mechanism_inputs["runtime_event_ledger"]
    assert runtime_events["body_included"] is False
    assert runtime_events["event_count"] == 1
    assert runtime_events["controller_event_refs"] == ["runtime-event:dm002/controller-decision-recorded"]
    provider = mechanism_inputs["provider_switch_hygiene"]
    assert provider["body_included"] is False
    assert provider["executor_refs"] == ["executor-ref:codex_cli"]
    assert provider["provider_refs"] == ["provider-ref:temporal-production"]
    assert provider["context_isolation_refs"] == ["context-isolation-ref:reviewer-no-shared-context"]
    assert provider["fallback_refs"] == ["provider-fallback-ref:local-diagnostic-only"]
    claim_map = mechanism_inputs["claim_assurance_map"]
    assert claim_map["body_included"] is False
    assert claim_map["claim_body_included"] is False
    assert claim_map["can_authorize_claim"] is False
    assert claim_map["claim_refs"] == [
        "claim-ref:external-validation-performance",
        "claim-ref:hdl-unit-contamination",
    ]
    assert claim_map["evidence_refs"] == ["evidence-ref:cox-transport-validation"]
    assert claim_map["reviewer_refs"] == ["review-ref:hdl-harmonization"]
    assert claim_map["display_refs"] == ["display-ref:table-2-performance"]
    assurance = mechanism_inputs["assurance_contract"]
    assert assurance["surface_kind"] == "mas_agent_lab_assurance_contract"
    assert assurance["body_included"] is False
    assert "raw-evidence-ref:cox-transport-jsonl" in assurance["raw_evidence_item_refs"]
    assert "evidence-ref:raw-cox-transport-output" in assurance["evidence_item_refs"]
    assert "review-ref:hdl-harmonization" in assurance["review_item_refs"]
    review_gate = mechanism_inputs["adversarial_review_gate"]
    assert review_gate["surface_kind"] == "mas_agent_lab_adversarial_review_gate"
    assert review_gate["independent_ai_reviewer_required"] is True
    assert review_gate["executor_context_reuse_allowed"] is False
    recovery = mechanism_inputs["experiment_queue_recovery"]
    assert recovery["surface_kind"] == "mas_agent_lab_experiment_queue_recovery"
    assert "analysis-campaign-item:dm002/provenance-recovery" in recovery["queue_item_refs"]
    aftercare = mechanism_inputs["publication_aftercare_plan"]
    assert aftercare["surface_kind"] == "mas_publication_aftercare_plan"
    assert aftercare["body_included"] is False
    assert aftercare["can_push_submission"] is False
    assert "publication-aftercare-plan:mas/002-dm-china-us-mortality-attribution" in aftercare[
        "publication_aftercare_plan_refs"
    ]
    assert "venue-route-ref:target-journal" in aftercare["venue_route_refs"]
    assert "runtime-event:dm002/controller-decision-recorded" in mechanism_inputs["evidence_delta_refs"]
    assert "provider-fallback-ref:local-diagnostic-only" in mechanism_inputs["evidence_delta_refs"]
    assert "claim-ref:external-validation-performance" in mechanism_inputs["evidence_delta_refs"]
    assert "raw-evidence-ref:cox-transport-jsonl" in mechanism_inputs["evidence_delta_refs"]
    assert "analysis-campaign-item:dm002/provenance-recovery" in mechanism_inputs["evidence_delta_refs"]
    assert mechanism_inputs["authority_boundary"]["can_write_domain_truth"] is False


def test_publication_aftercare_plan_command_exposes_refs_only_runtime_progression(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    controller = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    quest_root = tmp_path / "quest"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"review_refs": ["review-ref:ai"]})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:grounded"]})
    _write_json(study_root / "paper" / "citation_audit.json", {"citation_refs": ["citation-ref:audit"]})
    _write_json(study_root / "paper" / "anonymity_check.json", {"anonymity_refs": ["anonymity-ref:audit"]})
    _write_json(study_root / "artifacts" / "submission_targets" / "latest.json", {"target_venue_refs": ["venue-ref:journal"]})
    _write_json(study_root / "artifacts" / "overleaf" / "status.json", {"project_refs": ["overleaf-project-ref:paper"]})
    _write_json(
        study_root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        {
            "queue_ref": "analysis-campaign-queue:aftercare",
            "items": [{"ref": "analysis-item:aftercare", "source_refs": ["source-ref:aftercare"]}],
        },
    )
    (study_root / "paper" / "draft.md").write_text("# Draft\n", encoding="utf-8")
    (study_root / "talk").mkdir(parents=True, exist_ok=True)
    (study_root / "talk" / "slides.pptx").write_text("pptx placeholder", encoding="utf-8")
    for name in (
        "input_contract.json",
        "algorithm_scout_report.md",
        "innovation_hypotheses.md",
        "final_method_proposal.md",
        "experiment_plan.md",
        "experiment_results_summary.md",
        "review_loop_summary.md",
        "claim_to_evidence_map.md",
    ):
        path = quest_root / "artifacts" / "algorithm_research" / "aris" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n" if name.endswith(".json") else "ref\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "publication-aftercare-plan",
            "--study-root",
            str(study_root),
            "--quest-root",
            str(quest_root),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    pending_tasks = controller.build_publication_aftercare_pending_tasks(
        profile_name="local",
        profile_ref=tmp_path / "profile.local.toml",
        study_id=output["study_id"],
        projection=output,
    )

    assert exit_code == 0
    assert output["surface_kind"] == "mas_publication_aftercare_plan"
    assert output["refs_only"] is True
    assert output["body_included"] is False
    assert output["authority_boundary"]["can_submit_to_venue"] is False
    assert output["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert output["analysis_queue_entry"]["eligible_for_runtime_dispatch"] is True
    assert output["reviewer_refresh_entry"]["eligible_for_runtime_dispatch"] is True
    assert {task["task_kind"] for task in pending_tasks} == {
        "publication_aftercare/analysis-queue-progress",
        "publication_aftercare/reviewer-refresh",
    }
    assert all(task["requires_approval"] is False for task in pending_tasks)
