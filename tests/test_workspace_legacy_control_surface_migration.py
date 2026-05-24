from __future__ import annotations

import importlib
import json
from pathlib import Path


def _legacy_token(*parts: str, sep: str = "_") -> str:
    return sep.join(parts)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_profile(path: Path, workspace_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                'name = "legacy-control-fixture"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'managed_runtime_home = "{workspace_root / "runtime"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_workspace_legacy_control_surface_migration_archives_active_private_control_artifacts(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_legacy_control_surface_migration")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "001-risk"
    _write_profile(profile_path, workspace_root)
    _write_json(
        workspace_root / "artifacts" / "supervision" / "reconcile" / "latest.json",
        {
            "surface": _legacy_token("runtime", "supervisor", "reconcile", "receipt"),
            "recommended_command": "uv run python -m med_autoscience.cli runtime-supervisor-reconcile --profile <profile>",
        },
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "install_proof" / "latest.json",
        {
            "surface": "legacy_scheduler_install_proof",
            "installed_command": f"{workspace_root}/ops/medautoscience/bin/watch-runtime",
        },
    )
    _write_text(
        workspace_root / "artifacts" / "supervision" / "scheduler" / "logs" / "launchd.stderr.log",
        "watch-runtime exited after retired private control tick\n",
    )
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "owner_route": {"surface": _legacy_token("runtime", "supervisor", "owner", "route")},
            "prompt_contract": {
                "same_tick_actions": ["runtime supervisor-scan --apply-safe-actions"],
            },
        },
    )
    request_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json"
    )
    _write_json(
        request_path,
        {
            "surface": "supervisor_request_handoff_packet",
            "source_surface": _legacy_token("runtime", "supervisor", "scan"),
        },
    )

    dry_run = migration.run_workspace_legacy_control_surface_migration(
        profile_path=profile_path,
        apply=False,
    )

    assert dry_run["legacy_active_item_count"] == 4
    assert dry_run["request_refresh_item_count"] == 1
    assert "apply_workspace_legacy_control_surface_migration" in dry_run["next_required_actions"]
    assert "run_domain_action_request_materialize_apply_to_refresh_request_packets" in dry_run["next_required_actions"]
    assert dispatch_path.exists()

    applied = migration.run_workspace_legacy_control_surface_migration(
        profile_path=profile_path,
        apply=True,
    )

    assert applied["remaining_legacy_active_item_count"] == 0
    tombstone = json.loads(dispatch_path.read_text(encoding="utf-8"))
    assert tombstone["surface_kind"] == "legacy_control_surface_tombstone"
    assert tombstone["status"] == "migrated_to_provenance"
    assert tombstone["authority_boundary"]["compatibility_alias_created"] is False
    assert tombstone["legacy_token_count"] >= 1
    assert _legacy_token("runtime", "supervisor") not in dispatch_path.read_text(encoding="utf-8")
    assert "runtime supervisor-" not in dispatch_path.read_text(encoding="utf-8")
    assert request_path.exists()
    assert _legacy_token("runtime", "supervisor", "scan") in request_path.read_text(encoding="utf-8")
    latest = workspace_root / "artifacts" / "runtime" / "legacy_control_surface_migration" / "latest.json"
    assert latest.exists()
    archive_refs = [item["archive_ref"] for item in applied["migrated_items"]]
    assert any(ref.endswith("artifacts/supervision/reconcile/latest.json") for ref in archive_refs)
    assert any(ref.endswith("artifacts/supervision/install_proof/latest.json") for ref in archive_refs)
    assert any(ref.endswith("artifacts/supervision/scheduler/logs/launchd.stderr.log") for ref in archive_refs)
    assert any(ref.endswith("default_executor_dispatches/runtime_platform_repair.json") for ref in archive_refs)


def test_workspace_legacy_control_surface_migration_retires_replaced_request_packets(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_legacy_control_surface_migration")
    request_lifecycle = importlib.import_module("med_autoscience.controllers.domain_action_request_lifecycle")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "001-risk"
    _write_profile(profile_path, workspace_root)
    request_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json"
    )
    _write_json(
        request_path,
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "source_surface": _legacy_token("runtime", "supervisor", "scan"),
            "request_lifecycle": {"state": "requested"},
        },
    )
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
        },
    )

    dry_run = migration.run_workspace_legacy_control_surface_migration(
        profile_path=profile_path,
        apply=False,
    )

    assert dry_run["legacy_active_item_count"] == 0
    assert dry_run["request_refresh_item_count"] == 1
    assert dry_run["request_retirement_item_count"] == 1
    assert dry_run["request_retirement_items"][0]["replacement_evidence"]["kind"] == "current_default_executor_dispatch"
    assert "apply_workspace_legacy_control_surface_migration_for_replaced_request_packets" in dry_run[
        "next_required_actions"
    ]

    applied = migration.run_workspace_legacy_control_surface_migration(
        profile_path=profile_path,
        apply=True,
    )

    assert applied["remaining_request_refresh_item_count"] == 0
    tombstone = json.loads(request_path.read_text(encoding="utf-8"))
    assert tombstone["surface_kind"] == "legacy_control_surface_tombstone"
    assert tombstone["active_path_role"] == "domain_action_request_packet"
    assert tombstone["replacement_evidence"]["kind"] == "current_default_executor_dispatch"
    assert _legacy_token("runtime", "supervisor") not in request_path.read_text(encoding="utf-8")
    assert request_lifecycle.read_ai_reviewer_request(
        study_root=workspace_root / "studies" / study_id,
    ) is None


def test_workspace_legacy_control_surface_migration_reports_refresh_after_partial_request_retirement(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_legacy_control_surface_migration")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, workspace_root)
    replaced_study_id = "001-replaced"
    refresh_study_id = "002-refresh"
    _write_json(
        workspace_root
        / "studies"
        / replaced_study_id
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": replaced_study_id,
            "source_surface": _legacy_token("runtime", "supervisor", "scan"),
        },
    )
    _write_json(
        workspace_root
        / "studies"
        / replaced_study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json",
        {
            "surface": "default_executor_dispatch_request",
            "study_id": replaced_study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
        },
    )
    _write_json(
        workspace_root
        / "studies"
        / refresh_study_id
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": refresh_study_id,
            "source_surface": _legacy_token("runtime", "supervisor", "scan"),
        },
    )

    dry_run = migration.run_workspace_legacy_control_surface_migration(
        profile_path=profile_path,
        apply=False,
    )

    assert dry_run["request_refresh_item_count"] == 2
    assert dry_run["request_retirement_item_count"] == 1
    assert "apply_workspace_legacy_control_surface_migration_for_replaced_request_packets" in dry_run[
        "next_required_actions"
    ]
    assert "run_domain_action_request_materialize_apply_to_refresh_request_packets" in dry_run[
        "next_required_actions"
    ]


def test_outer_supervision_slo_ignores_legacy_reconcile_latest_file(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.outer_supervision_slo")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="workspace",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy" / "runtime",
        med_deepscientist_repo_root=workspace_root / "legacy" / "repo",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=False,
        medical_overlay_scope="workspace",
        medical_overlay_skills=(),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=(),
        default_submission_targets=(),
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "reconcile" / "latest.json",
        {
            "surface": _legacy_token("runtime", "supervisor", "reconcile", "receipt"),
            "generated_at": "2026-05-24T00:00:00+00:00",
        },
    )

    projection = module.build_outer_supervision_slo_projection(
        profile=profile,
        generated_at="2026-05-24T00:01:00+00:00",
    )

    assert projection["state"] == "missing"
    assert projection["latest_reconcile_domain_routes_at"] is None
    assert projection["refs"]["current_reconcile_source"] == "legacy_reconcile_path_ignored"
