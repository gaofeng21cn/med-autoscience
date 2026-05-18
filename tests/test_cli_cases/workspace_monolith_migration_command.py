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
    assert queue["items"] == [
        {
            "ref": "analysis-queue:hdl-harmonization",
            "state": "blocked",
            "retry_count": 2,
            "budget_cost": 5,
            "source_refs": ["paper-ref:dm002-current-draft"],
        }
    ]
    assert queue["body_included"] is False
    assert mechanism_inputs["authority_boundary"]["can_write_domain_truth"] is False
