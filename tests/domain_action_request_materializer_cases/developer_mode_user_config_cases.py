from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
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
    assert (profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json").is_file()
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
