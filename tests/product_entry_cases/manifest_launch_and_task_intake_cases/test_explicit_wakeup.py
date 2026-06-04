from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study, write_text

pytestmark = pytest.mark.contract


def _write_ready_workspace_contracts(profile) -> None:
    profile.managed_runtime_quests_root.mkdir(parents=True, exist_ok=True)
    write_text(profile.workspace_root / "ops" / "medautoscience" / "config.env", "MEDAUTOSCI_PROFILE=diabetes\n")
    write_text(profile.workspace_root / "ops" / "mas" / "config.env", "MEDAUTOSCI_PROFILE=diabetes\n")
    (profile.workspace_root / "ops" / "mas" / "bin").mkdir(parents=True, exist_ok=True)
    write_text(
        profile.workspace_root / "ops" / "mas" / "behavior_equivalence_gate.yaml",
        "\n".join(
            [
                "schema_version: v1",
                "phase_25_ready: true",
                "critical_overrides: []",
            ]
        )
        + "\n",
    )


def test_launch_study_explicit_wakeup_records_truth_resume(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    launch_surface = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.launch_surface"
    )
    monitoring_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    truth_kernel = importlib.import_module("med_autoscience.controllers.study_truth_kernel")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    study_root = write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        launch_surface.domain_status_projection,
        "progress_projection",
        lambda **kwargs: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "continuation_state": {
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            },
            "auto_runtime_parked": {"awaiting_explicit_wakeup": True},
        },
    )
    monkeypatch.setattr(
        launch_surface.study_progress,
        "build_study_progress_projection",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "auto_runtime_parked",
            "progress_first_monitoring_summary": monitoring_module.build_progress_first_monitoring_summary(
                {
                    "study_id": "001-risk",
                    "current_stage": "auto_runtime_parked",
                    "runtime_health_snapshot": {
                        "attempt_state": "awaiting_explicit_resume",
                        "failure_reason": "entry_mode_not_managed",
                    },
                    "product_entry_launch_policy": kwargs["status_payload"]["product_entry_launch_policy"],
                }
            ),
        },
    )

    payload = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        explicit_user_wakeup=True,
    )

    events = truth_kernel.read_truth_events(study_root=study_root)
    assert [event["event_type"] for event in events] == ["explicit_resume"]
    assert events[0]["payload"]["current_required_action"] == "resume_same_study_line"
    assert events[0]["payload"]["resume_owner"] == "one-person-lab"
    assert payload["runtime_status"]["product_entry_launch_policy"]["explicit_user_wakeup_recorded"] is True
    assert payload["runtime_status"]["product_entry_launch_policy"]["owner_handoff_hydration_required"] is True
    assert (
        payload["runtime_status"]["product_entry_launch_policy"]["owner_handoff_hydration_action"]
        == "hydrate_opl_owner_route_from_explicit_resume"
    )
    assert payload["runtime_status"]["study_truth_snapshot"]["canonical_next_action"] == "resume_same_study_line"
    assert payload["runtime_status"]["study_truth_snapshot"]["dominant_authority_refs"][0]["event_type"] == "explicit_resume"
    assert (
        payload["progress"]["progress_first_monitoring_summary"]["next_work_unit"]
        == "hydrate_opl_owner_route_from_explicit_resume"
    )
    assert payload["progress"]["progress_first_monitoring_summary"]["next_owner"] == "one-person-lab"


def test_launch_study_explicit_wakeup_releases_paused_runtime_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    launch_surface = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.launch_surface"
    )
    runtime_protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    runtime_models = importlib.import_module("med_autoscience.runtime_protocol.study_runtime_models")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    _write_ready_workspace_contracts(profile)
    monkeypatch.setattr(
        runtime_protocol,
        "validate_startup_contract_resolution",
        lambda **kwargs: runtime_models.StartupContractValidation(
            status=runtime_models.StartupContractValidationStatus.CLEAR,
            blockers=(),
            medical_analysis_contract_status="resolved",
            medical_reporting_contract_status="resolved",
            medical_analysis_reason_code=None,
            medical_reporting_reason_code=None,
        ),
    )
    monkeypatch.setattr(
        launch_surface.domain_status_projection.startup_boundary_gate_controller,
        "evaluate_startup_boundary",
        lambda **kwargs: {
            "status": "ready_for_compute_stage",
            "allow_compute_stage": True,
            "missing_requirements": [],
            "blockers": [],
        },
    )
    monkeypatch.setattr(
        launch_surface.domain_status_projection.runtime_reentry_gate_controller,
        "evaluate_runtime_reentry",
        lambda **kwargs: {
            "status": "not_configured",
            "allow_runtime_entry": True,
            "blockers": [],
            "required_paths": [],
        },
    )
    quest_root = profile.managed_runtime_home / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    runtime_state = {
        "quest_id": "001-risk",
        "status": "paused",
        "active_run_id": None,
        "worker_running": False,
        "worker_pending": False,
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_anchor": "turn_closeout",
        "continuation_reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
        "continuation_updated_at": "2026-06-03T13:17:32Z",
        "manual_hold": {
            "reason": "manual_pause_for_mas_rebuild",
            "recorded_at": "2026-06-03T13:17:32Z",
            "resume_requires_explicit_wakeup": True,
        },
        "human_takeover_contract": {
            "source": "operator-manual-pause",
            "reason": "manual_pause_for_mas_rebuild",
            "recorded_at": "2026-06-03T13:17:32Z",
            "resume_requires_explicit_wakeup": True,
        },
    }
    runtime_state_text = json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n"
    write_text(quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json", runtime_state_text)
    write_text(quest_root / ".ds" / "runtime_state.json", runtime_state_text)

    before = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
    )
    assert before["runtime_status"]["decision"] == "blocked"
    assert before["runtime_status"]["reason"] == "quest_user_paused_requires_explicit_wakeup"

    after = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        explicit_user_wakeup=True,
    )

    assert after["runtime_status"]["product_entry_launch_policy"]["explicit_user_wakeup_recorded"] is True
    assert after["runtime_status"]["reason"] != "quest_user_paused_requires_explicit_wakeup"
    assert after["runtime_status"]["decision"] in {"resume", "blocked"}
    if after["runtime_status"]["decision"] == "blocked":
        assert after["runtime_status"]["reason"] == "quest_waiting_opl_runtime_owner_route"


def test_launch_study_rejects_unsupported_entry_mode_before_runtime_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    launch_surface = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.launch_surface"
    )
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        launch_surface.domain_status_projection,
        "progress_projection",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("unsupported entry mode must fail first")),
    )

    with pytest.raises(ValueError, match="study launch entry mode 不支持: managed"):
        module.launch_study(
            profile=profile,
            profile_ref=profile_ref,
            study_id="001-risk",
            entry_mode="managed",
            explicit_user_wakeup=True,
        )


def test_launch_study_uses_formal_runtime_entry_mode_for_opl_handoff(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    launch_surface = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.launch_surface"
    )
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    called: dict[str, object] = {}

    def fake_progress_projection(**kwargs):
        called["entry_mode"] = kwargs.get("entry_mode")
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
        }

    monkeypatch.setattr(launch_surface.domain_status_projection, "progress_projection", fake_progress_projection)
    monkeypatch.setattr(
        launch_surface.study_progress,
        "build_study_progress_projection",
        lambda **kwargs: {"study_id": "001-risk", "current_stage": "publication_supervision"},
    )

    payload = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        entry_mode="opl-handoff",
    )

    assert called["entry_mode"] is None
    assert payload["runtime_status"]["product_entry_launch_policy"]["entry_mode"] == "opl-handoff"
    assert payload["runtime_status"]["product_entry_launch_policy"]["supported_entry_modes"] == [
        "direct",
        "opl-handoff",
    ]
