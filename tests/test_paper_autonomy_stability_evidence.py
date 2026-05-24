from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _ready_matrix_payload(study_id: str) -> dict[str, object]:
    return {
        "surface": "real_study_soak_matrix_evidence",
        "study_id": study_id,
        "study_archetype": "observational_real_world",
        "stages": [
            "literature_scout",
            "line_selection",
            "baseline",
            "primary_analysis",
            "bounded_analysis",
            "route_back",
            "stop_loss",
            "revision_reopen",
            "runtime_recovery",
            "finalize_rebuild",
            "final_pre_submission_audit",
        ],
        "contracts": {
            "literature_contract": True,
            "statistical_contract": True,
        },
        "result_strength": "adequate",
        "route_action": "continue",
        "durable_refs": [f"{study_id}/artifacts/publication_eval/latest.json"],
    }


def _write_display_refs(workspace: Path) -> None:
    _write_json(
        workspace / "artifacts" / "runtime" / "progress_portal" / "latest.json",
        {"surface_kind": "mas_progress_portal", "study": {"study_id": "001-active"}},
    )
    (workspace / "ops" / "mas" / "progress").mkdir(parents=True, exist_ok=True)
    (workspace / "ops" / "mas" / "progress" / "index.html").write_text(
        "<!doctype html><title>Med Auto Science</title>\n",
        encoding="utf-8",
    )


def test_paper_autonomy_stability_evidence_is_read_only_and_reports_blockers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_autonomy_stability_evidence")
    workspace = tmp_path / "Yang" / "Fixture"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "fixture.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    status_path = _write_json(
        workspace / "studies" / "001-active" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": "001-active",
            "health_status": "running",
            "active_run_id": "run-123",
            "runtime_reason": "worker_running",
        },
    )
    _write_json(
        workspace
        / "studies"
        / "001-active"
        / "artifacts"
        / "medical_paper"
        / "real_study_soak_matrix_evidence.json",
        _ready_matrix_payload("001-active"),
    )
    before_mtimes = {path: path.stat().st_mtime_ns for path in (profile_path, status_path)}

    def fake_scan(**kwargs):
        assert kwargs["apply_safe_actions"] is False
        assert kwargs["persist_surfaces"] is False
        return {
            "surface": "portable_owner_route_reconcile",
            "studies": [
                {
                    "study_id": "001-active",
                    "stable_blocker": {
                        "kind": "human_gate",
                        "status": "blocked",
                        "reason": "awaiting_user_wakeup",
                        "next_action": "wait_for_human_wakeup",
                    },
                }
            ],
            "action_queue": [],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **_: {"surface": "domain_action_request_materializer", "request_tasks": []},
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **_: {
            "surface": "default_executor_dispatch_executor",
            "execution_count": 0,
            "blocked_count": 0,
            "executions": [],
        },
    )

    payload = module.build_paper_autonomy_stability_evidence(profile_paths=[profile_path])

    assert payload["surface"] == "paper_autonomy_stability_evidence"
    assert payload["read_only_contract"]["can_write_current_package"] is False
    assert payload["summary"]["writes_performed"] is False
    assert payload["summary"]["can_claim_landed"] is False
    profile = payload["profiles"][0]
    assert profile["profile_readable"] is True
    assert profile["owner_route_handoff_observation"]["can_complete"] is True
    assert profile["workspace_migration_dry_run"]["dry_run"] is True
    assert profile["workspace_migration_dry_run"]["writes_performed"] is False
    assert profile["real_workspace_soak_monitor"]["writes_performed"] is False
    assert profile["legacy_mds_diagnostic"]["diagnostic_only"] is True
    assert profile["legacy_mds_diagnostic"]["default_runner_can_launch_runtime"] is False
    assert any(blocker["kind"] == "human_gate" for blocker in payload["blockers"])
    assert any(blocker["kind"] == "runtime_truth" for blocker in payload["blockers"])
    assert "wait_for_human_wakeup" in payload["next_actions"]
    assert not (workspace / "artifacts" / "supervision" / "reconcile" / "latest.json").exists()
    assert {path: path.stat().st_mtime_ns for path in before_mtimes} == before_mtimes


def test_paper_autonomy_stability_evidence_projects_progress_degradation_read_model(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_autonomy_stability_evidence")
    workspace = tmp_path / "Yang" / "Fixture"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "fixture.workspace.toml"
    study_root = workspace / "studies" / "001-active"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    _write_display_refs(workspace)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": "001-active",
            "health_status": "running",
            "active_run_id": "run-123",
            "runtime_reason": "worker_running",
            "publication_supervisor_state": {
                "supervisor_phase": "write",
                "phase_owner": "publication_gate",
                "current_required_action": "continue_write_stage",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "study_macro_state" / "latest.json",
        {
            "surface_kind": "study_macro_state",
            "study_id": "001-active",
            "writer_state": "queued",
            "user_next": "watch",
            "reason": "runtime",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "ai_reviewer_required": True,
            },
            "verdict": {"overall_verdict": "mixed"},
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "request_id": "ai-reviewer::001-active",
            "request_owner": "publication_gate",
            "request_lifecycle": {"state": "assigned", "assigned_to": "ai_reviewer"},
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "real_study_soak_matrix_evidence.json",
        _ready_matrix_payload("001-active"),
    )

    def fake_scan(**kwargs):
        assert kwargs["apply_safe_actions"] is False
        assert kwargs["persist_surfaces"] is False
        suffix = "before" if not fake_scan.seen else "after"
        fake_scan.seen = True
        return {
            "surface": "portable_owner_route_reconcile",
            "studies": [
                {
                    "study_id": "001-active",
                    "owner_route": {
                        "next_owner": f"mas_controller_{suffix}",
                        "idempotency_key": f"route-{suffix}",
                    },
                    "action_queue": [{"study_id": "001-active", "action_type": "unsupported_supervisor_action"}],
                }
            ],
            "action_queue": [{"study_id": "001-active", "action_type": "unsupported_supervisor_action"}],
        }

    fake_scan.seen = False
    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **_: {"surface": "domain_action_request_materializer", "request_tasks": []},
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **_: {
            "surface": "default_executor_dispatch_executor",
            "execution_count": 1,
            "blocked_count": 0,
            "executions": [{"study_id": "001-active", "execution_status": "dry_run"}],
        },
    )

    payload = module.build_paper_autonomy_stability_evidence(profile_paths=[profile_path])

    evidence = payload["paper_progress_degradation_evidence"]
    assert evidence["surface"] == "paper_progress_degradation_evidence"
    assert evidence["read_only_contract"]["can_write_current_package"] is False
    assert evidence["summary"]["writes_performed"] is False
    profile = evidence["profiles"][0]
    assert profile["progress_portal_refs"]["status"] == "readable"
    assert profile["safe_reconcile_dry_run"]["next_action"] == "review_safe_reconcile_dry_run_before_apply"
    study = profile["studies"][0]
    assert study["status_progress_readability"]["status"] == "readable"
    assert study["owner_route_progression"]["status"] == "advanced"
    handoff = study["publication_handoff_clarity"]
    assert handoff["status"] == "clear"
    assert handoff["publication_gate"]["current_required_action"] == "continue_write_stage"
    assert handoff["ai_reviewer"]["source"] == "ai_reviewer_request_lifecycle"
    assert handoff["writer_handoff"]["writer_state"] == "queued"


def test_paper_autonomy_stability_evidence_cli_outputs_json(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_build(*, yang_root, profile_paths, study_ids):
        called["yang_root"] = yang_root
        called["profile_paths"] = profile_paths
        called["study_ids"] = study_ids
        return {
            "surface": "paper_autonomy_stability_evidence",
            "schema_version": 1,
            "profiles": [],
        }

    monkeypatch.setattr(
        cli.paper_autonomy_stability_evidence,
        "build_paper_autonomy_stability_evidence",
        fake_build,
    )

    exit_code = cli.main(
        [
            "runtime",
            "paper-autonomy-stability-evidence",
            "--yang-root",
            str(tmp_path),
            "--profiles",
            "profile.toml",
            "--studies",
            "001",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "yang_root": tmp_path,
        "profile_paths": ("profile.toml",),
        "study_ids": ("001",),
    }
    assert json.loads(captured.out)["surface"] == "paper_autonomy_stability_evidence"


def test_paper_progress_degradation_ignores_migrated_ai_reviewer_request_tombstone(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_degradation_evidence")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-active"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "ai_reviewer_required": True,
            },
            "verdict": {"overall_verdict": "mixed"},
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface_kind": "legacy_control_surface_tombstone",
            "status": "migrated_to_provenance",
            "active_path_role": "domain_action_request_packet",
        },
    )
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "fixture.workspace.toml"
    _write_profile(workspace_root, profile_path)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)

    result = module.build_profile_progress_degradation_evidence(
        profile_path=str(tmp_path / "profile.local.toml"),
        profile=profile,
        studies=[
            {
                "study_id": "001-active",
                "study_root": str(study_root),
                "status_progress_readable": True,
                "readable_surface_count": 1,
                "surface_refs": [{"relative_ref": "artifacts/runtime/runtime_status_summary.json", "readable": True}],
            }
        ],
        reconcile={"study_receipts": []},
        monitor={},
    )

    handoff = result["studies"][0]["publication_handoff_clarity"]
    assert handoff["ai_reviewer"]["status"] == "blocked"
    assert handoff["ai_reviewer"]["source"] == "publication_eval.assessment_provenance"
    assert handoff["ai_reviewer"]["request_state"] == ""
