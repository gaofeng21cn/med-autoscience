from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from . import control_plane_fixtures as fixtures


@pytest.mark.parametrize("case", fixtures.fact_cases(), ids=lambda case: case.case_id)
def test_opl_runtime_refs_regression_cases(case: fixtures.ControlPlaneFactCase) -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")

    facts = module.resolve_opl_runtime_refs(
        case.payload,
        supervisor_tick_audit=case.supervisor_tick_audit,
    )

    for field_name, expected_value in case.expected.items():
        assert getattr(facts, field_name) == expected_value


def test_supervisor_lightweight_path_preserves_liveness() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.runtime_liveness_projection")
    payload = fixtures.supervisor_lightweight_payload()

    assert module.live_managed_runtime_present(
        status=payload,
        autonomous_runtime_notice=payload["autonomous_runtime_notice"],
        execution_owner_guard=payload["execution_owner_guard"],
        continuation_state=payload["continuation_state"],
    ) is True
    assert module.runtime_recovery_pending_from_status(
        status=payload,
        supervisor_tick_audit={"status": "stale"},
        live_managed_runtime=True,
    ) is False


def test_opl_runtime_refs_invalidates_stale_active_run_when_liveness_has_no_worker() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")

    facts = module.resolve_opl_runtime_refs(
        {
            "quest_status": "running",
            "active_run_id": "run-stale-launch",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": "run-stale-launch",
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": "run-stale-launch",
                    "worker_running": False,
                },
            },
            "autonomous_runtime_notice": {"active_run_id": "run-stale-launch"},
            "execution_owner_guard": {"active_run_id": "run-stale-launch"},
        }
    )

    assert facts.active_run_id is None
    assert facts.active_run_id_source == "invalidated_no_live_worker"
    assert facts.strict_live is False
    assert facts.recovery_pending is True


def test_same_fingerprint_repeated_turn_stays_stable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup")
    study_root = tmp_path / "studies" / "001-risk"
    status_payload = fixtures.same_fingerprint_status_payload()

    first = module._build_outer_loop_wakeup_audit(
        study_root=study_root,
        status_payload=status_payload,
    )
    latest_path = Path(first["latest_path"])
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(first, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    second = module._build_outer_loop_wakeup_audit(
        study_root=study_root,
        status_payload=status_payload,
    )

    assert first["input_fingerprint"] == second["input_fingerprint"]
    assert second["previous_input_fingerprint"] == first["input_fingerprint"]
    assert second["dispatch_cause"] == "input_unchanged"
    assert second["watched_inputs"]["status"]["active_run_id"] == "run-live-fingerprint"
    assert second["watched_inputs"]["status"]["runtime_liveness_status"] == "live"


def test_package_handoff_parked_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.auto_runtime_parking")

    projection = module.build_auto_runtime_parked_projection(fixtures.package_handoff_parked_status())

    assert projection["parked"] is True
    assert projection["parked_state"] == "package_ready_handoff"
    assert projection["parked_owner"] == "user"
    assert projection["resource_release_expected"] is True
    assert projection["auto_execution_complete"] is True
    assert "legacy_current_stage" not in projection


def test_external_upstream_parked_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.auto_runtime_parking")

    projection = module.build_auto_runtime_parked_projection(fixtures.external_upstream_parked_status())

    assert projection["parked"] is True
    assert projection["parked_state"] == "external_upstream_pending"
    assert projection["parked_owner"] == "external_provider"
    assert projection["resource_release_expected"] is True
    assert projection["awaiting_explicit_wakeup"] is True
    assert projection["auto_execution_complete"] is False


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
    legacy_reconcile = workspace_root / "runtime" / "artifacts" / "supervision" / "reconcile" / "latest.json"
    legacy_reconcile.parent.mkdir(parents=True, exist_ok=True)
    legacy_reconcile.write_text(
        json.dumps(
            {
                "surface": "runtime_supervisor_reconcile_receipt",
                "generated_at": "2026-05-24T00:00:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    projection = module.build_outer_supervision_slo_projection(
        profile=profile,
        generated_at="2026-05-24T00:01:00+00:00",
    )

    assert projection["state"] == "missing"
    assert projection["latest_reconcile_domain_routes_at"] is None
    assert projection["refs"]["current_reconcile_source"] == "legacy_reconcile_path_ignored"
