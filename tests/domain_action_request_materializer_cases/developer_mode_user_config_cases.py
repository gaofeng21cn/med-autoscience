from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def _disable_unrelated_fresh_progress(monkeypatch) -> None:
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    source_fingerprint = f"truth-source::{study_id}::{owner_reason}"
    truth_epoch = f"truth-epoch::{study_id}"
    runtime_health_epoch = f"runtime-health::{study_id}::{owner_reason}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": source_fingerprint,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": source_fingerprint,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": runtime_health_epoch,
                "truth_epoch": truth_epoch,
                "work_unit_fingerprint": source_fingerprint,
                "work_unit_id": owner_reason,
            },
        },
    }


def _unsupported_domain_action(study_id: str, quest_id: str) -> dict[str, object]:
    action_type = "unsupported_supervisor_action"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="external_observer",
        owner_reason=action_type,
        allowed_actions=[action_type],
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "authority": "observability_only",
        "reason": action_type,
        "action_id": f"supervisor-action::{study_id}::{action_type}",
        "owner_route": route,
        "handoff_packet": {
            "packet_type": "external_supervisor_handoff",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": action_type,
            "reason": action_type,
            "authority": "observability_only",
            "recommended_owner": "external_observer",
            "owner_route": route,
        },
    }


def _write_consumer_scan(profile, study_id: str, quest_id: str) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [_unsupported_domain_action(study_id, quest_id)],
        },
    )


def _write_executable_current_work_unit_scan(profile, study_id: str, quest_id: str) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    owner_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="medical_prose_write_repair",
        allowed_actions=["run_quality_repair_batch"],
    )
    owner_route["source_refs"] = {
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "study_truth_epoch": "truth::dm003::2026-06-12T00:00:00Z",
        "runtime_health_epoch": "runtime-health::dm003::2026-06-12T00:00:00Z",
        "owner_route_currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth::dm003::2026-06-12T00:00:00Z",
            "runtime_health_epoch": "runtime-health::dm003::2026-06-12T00:00:00Z",
        },
    }
    owner_route["work_unit_fingerprint"] = "publication-blockers::0915410f804b3697"
    owner_route["source_fingerprint"] = "publication-blockers::0915410f804b3697"
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "owner_route": owner_route,
                        "state": {"state_kind": "executable_owner_action"},
                    },
                    "owner_route": owner_route,
                }
            ],
            "action_queue": [],
        },
    )


def test_materialize_domain_action_requests_allows_user_configured_developer_mode_without_github_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    opl_state_dir = tmp_path / "opl-state"
    monkeypatch.setenv("OPL_STATE_DIR", str(opl_state_dir))
    _write_json(
        opl_state_dir / "developer-supervisor.json",
        {
            "version": "g1",
            "enabled": "on",
            "mode": "developer_apply_safe",
            "auto_enable_github_login": "gaofeng21cn",
            "updated_at": "2026-05-10T00:00:00+00:00",
        },
    )
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    _write_consumer_scan(profile, study_id, "quest-nf")

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["effective_mode"] == "developer_apply_safe"
    assert result["developer_supervisor_mode"]["mode_source"] == "command"
    assert result["developer_supervisor_mode"]["authority_gate"] == {
        "allowed": True,
        "source": "opl_family_user_config",
        "reason": None,
    }
    assert result["github_gate"]["allowed"] is False
    assert result["apply_allowed"] is True
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()


def test_blocked_current_work_unit_dispatch_exposes_supervisor_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_executable_current_work_unit_scan(profile, study_id, study_id)
    owner_route = json.loads(
        (
            profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )["studies"][0]["owner_route"]
    monkeypatch.setattr(
        progress_module,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "owner_route": owner_route,
                "state": {"state_kind": "executable_owner_action"},
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
                "typed_blocker": None,
                "parked_state": None,
            },
            "current_executable_owner_action": {
                "owner": "write",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "owner_route": owner_route,
            },
            "owner_route": owner_route,
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="external_observe",
        apply=True,
    )

    assert result["apply_allowed"] is False
    assert result["blocked_domain_progress_transition_request_count"] == 1
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert dispatch["dispatch_status"] == "blocked"
    assert dispatch["blocked_reason"] == "developer_apply_safe_required"
    assert dispatch["execution_gate"] == {
        "gate_kind": "developer_supervisor",
        "blocked": True,
        "reason": "developer_apply_safe_required",
        "requested_mode": "external_observe",
        "effective_mode": "external_observe",
        "required_mode": "developer_apply_safe",
        "safe_actions_enabled": False,
        "authority_gate": result["developer_supervisor_mode"]["authority_gate"],
        "github_user_gate": result["developer_supervisor_mode"]["github_user_gate"],
        "repo_write_policy": result["developer_supervisor_mode"]["repo_write_policy"],
    }
    assert dispatch["provider_admission_effect"] == "not_admitted_until_execution_gate_clears"


def test_materialize_domain_action_requests_honors_user_config_disabled_over_apply_safe_default(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    opl_state_dir = tmp_path / "opl-state"
    monkeypatch.setenv("OPL_STATE_DIR", str(opl_state_dir))
    _write_json(
        opl_state_dir / "developer-supervisor.json",
        {
            "version": "g1",
            "enabled": "off",
            "mode": "developer_apply_safe",
            "auto_enable_github_login": "gaofeng21cn",
            "updated_at": "2026-05-10T00:00:00+00:00",
        },
    )
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    _write_consumer_scan(profile, study_id, "quest-nf")

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["effective_mode"] == "external_observe"
    assert result["developer_supervisor_mode"]["mode_source"] == "opl_family_user_config_disabled"
    assert result["developer_supervisor_mode"]["authority_gate"] == {
        "allowed": False,
        "source": "opl_family_user_config",
        "reason": "developer_supervisor_disabled_by_user_config",
    }
    assert result["apply_allowed"] is False
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()


def test_materialize_domain_action_requests_uses_profile_github_username_for_pull_request_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    profile = profile.__class__(
        **{
            **profile.__dict__,
            "developer_supervisor_mode": "developer_apply_safe",
            "developer_supervisor_mode_explicit": True,
            "github_username": "someone-else",
            "mas_developer_github_usernames": ("gaofeng21cn",),
        }
    )
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    _write_consumer_scan(profile, study_id, "quest-nf")

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    developer_mode = result["developer_supervisor_mode"]
    assert result["effective_mode"] == "developer_apply_safe"
    assert result["apply_allowed"] is True
    assert developer_mode["github_user_gate"] == {
        "expected_login": "gaofeng21cn",
        "login": "someone-else",
        "allowed": False,
        "source": "profile",
        "reason": "github_user_requires_pull_request_route",
    }
    assert developer_mode["repo_write_policy"] == {
        "route": "pull_request",
        "direct_repo_write_allowed": False,
        "pull_request_required": True,
        "source": "profile",
        "reason": "github_user_requires_pull_request_route",
    }
    assert developer_mode["authority_gate"] == {
        "allowed": True,
        "source": "profile_developer_mode_pull_request",
        "reason": "github_user_requires_pull_request_route",
    }
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()


def test_materialize_domain_action_requests_uses_pull_request_route_for_non_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    _write_consumer_scan(profile, study_id, "quest-nf")

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["effective_mode"] == "developer_apply_safe"
    assert result["apply_allowed"] is True
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert result["developer_supervisor_mode"]["repo_write_policy"]["route"] == "pull_request"
    assert result["developer_supervisor_mode"]["repo_write_policy"]["pull_request_required"] is True
    assert result["domain_progress_transition_request_count"] == 0
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()


def test_materialize_domain_action_requests_blocks_apply_for_non_developer_apply_safe_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    _write_consumer_scan(profile, study_id, "quest-nf")

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="external_observe",
        apply=True,
    )

    assert result["effective_mode"] == "external_observe"
    assert result["apply_allowed"] is False
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert not (profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json").exists()
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()
