from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
import yaml

from tests.study_runtime_test_helpers import make_profile, write_text


def _profile_with_hermes_binding(tmp_path: Path):
    profile = make_profile(tmp_path)
    return profile.__class__(
        **{
            **profile.__dict__,
            "hermes_agent_repo_root": tmp_path / "_external" / "hermes-agent",
            "hermes_home_root": tmp_path / ".hermes",
            "managed_runtime_backend_id": "hermes",
        }
    )


def test_hermes_transport_requires_explicit_runtime_binding_before_delegating(tmp_path: Path) -> None:
    hermes = importlib.import_module("med_autoscience.runtime_transport.hermes")

    with pytest.raises(RuntimeError, match="hermes runtime adapter binding"):
        hermes.create_quest(
            runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
            payload={"quest_id": "quest-unbound"},
        )


def test_hermes_transport_binds_runtime_root_and_delegates_after_external_runtime_check(
    monkeypatch,
    tmp_path: Path,
) -> None:
    hermes = importlib.import_module("med_autoscience.runtime_transport.hermes")
    stable_transport = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    profile = _profile_with_hermes_binding(tmp_path)
    runtime_root = profile.runtime_root
    seen: dict[str, object] = {}

    binding = hermes.bind_runtime_root_from_profile(runtime_root=runtime_root, profile=profile)

    monkeypatch.setattr(
        hermes,
        "inspect_hermes_runtime_contract",
        lambda **kwargs: (
            seen.__setitem__("contract_kwargs", kwargs)
            or {
                "ready": True,
                "issues": [],
                "repo_root": str(profile.hermes_agent_repo_root),
                "hermes_home_root": str(profile.hermes_home_root),
            }
        ),
    )
    monkeypatch.setattr(
        stable_transport,
        "create_quest",
        lambda **kwargs: (seen.__setitem__("create_kwargs", kwargs) or {"ok": True, "delegated": True}),
    )

    result = hermes.create_quest(
        runtime_root=runtime_root,
        payload={"quest_id": "quest-001"},
    )

    binding_path = runtime_root.parent / hermes.RUNTIME_BINDING_FILENAME
    binding_payload = yaml.safe_load(binding_path.read_text(encoding="utf-8"))

    assert binding["runtime_root"] == str(runtime_root.resolve())
    assert binding_path.is_file()
    assert binding_payload["hermes_agent_repo_root"] == str(profile.hermes_agent_repo_root.resolve())
    assert binding_payload["hermes_home_root"] == str(profile.hermes_home_root.resolve())
    assert seen["contract_kwargs"] == {
        "hermes_agent_repo_root": profile.hermes_agent_repo_root.resolve(),
        "hermes_home_root": profile.hermes_home_root.resolve(),
    }
    assert seen["create_kwargs"] == {
        "runtime_root": runtime_root,
        "payload": {"quest_id": "quest-001"},
    }
    assert result == {"ok": True, "delegated": True}


def test_hermes_transport_fails_closed_when_external_runtime_is_not_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    hermes = importlib.import_module("med_autoscience.runtime_transport.hermes")
    stable_transport = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    profile = _profile_with_hermes_binding(tmp_path)
    runtime_root = profile.runtime_root

    hermes.bind_runtime_root_from_profile(runtime_root=runtime_root, profile=profile)

    monkeypatch.setattr(
        hermes,
        "inspect_hermes_runtime_contract",
        lambda **kwargs: {
            "ready": False,
            "issues": ["external_runtime.gateway_service_not_loaded"],
        },
    )
    monkeypatch.setattr(
        stable_transport,
        "resume_quest",
        lambda **kwargs: pytest.fail("stable transport should not be called when Hermes runtime is not ready"),
    )

    with pytest.raises(RuntimeError, match="external_runtime.gateway_service_not_loaded"):
        hermes.resume_quest(
            runtime_root=runtime_root,
            quest_id="quest-001",
            source="test",
        )


def test_hermes_transport_inspect_live_execution_returns_structured_unknown_when_external_runtime_is_not_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    hermes = importlib.import_module("med_autoscience.runtime_transport.hermes")
    profile = _profile_with_hermes_binding(tmp_path)
    runtime_root = profile.managed_runtime_home
    quest_root = runtime_root / "quests" / "quest-001"

    hermes.bind_runtime_root_from_profile(runtime_root=runtime_root, profile=profile)
    write_text(quest_root / "quest.yaml", "quest_id: quest-001\nstatus: running\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
            }
        )
        + "\n",
    )
    monkeypatch.setattr(
        hermes,
        "inspect_hermes_runtime_contract",
        lambda **kwargs: {
            "ready": False,
            "issues": ["external_runtime.gateway_service_not_loaded"],
        },
    )

    result = hermes.inspect_quest_live_execution(
        runtime_root=runtime_root,
        quest_id="quest-001",
    )

    assert result["ok"] is False
    assert result["status"] == "unknown"
    assert result["source"] == "external_runtime_contract"
    assert result["active_run_id"] == "run-live-001"
    assert result["runtime_audit"]["status"] == "unknown"
    assert "external_runtime.gateway_service_not_loaded" in result["error"]


def test_router_binds_runtime_root_when_selecting_hermes_backend(tmp_path: Path) -> None:
    hermes = importlib.import_module("med_autoscience.runtime_transport.hermes")
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = _profile_with_hermes_binding(tmp_path)

    backend = router._managed_runtime_backend_for_execution(
        {"runtime_backend_id": "hermes", "runtime_engine_id": "hermes"},
        profile=profile,
        runtime_root=profile.runtime_root,
    )

    binding_path = profile.runtime_root.parent / hermes.RUNTIME_BINDING_FILENAME
    binding_payload = yaml.safe_load(binding_path.read_text(encoding="utf-8"))

    assert backend.BACKEND_ID == "hermes"
    assert binding_path.is_file()
    assert binding_payload["runtime_root"] == str(profile.runtime_root.resolve())
