from __future__ import annotations

import importlib
from pathlib import Path


def test_study_runtime_router_build_create_payload_uses_router_startup_contract_binding(monkeypatch) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")

    monkeypatch.setattr(
        router,
        "_build_startup_contract",
        lambda **kwargs: {
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": False},
            "marker": "patched-via-router",
        },
    )

    payload = router._build_create_payload(
        profile=object(),
        study_id="study-001",
        study_root=Path("/tmp/study-001"),
        study_payload={},
        execution={},
    )

    assert payload["startup_contract"]["marker"] == "patched-via-router"


def test_study_runtime_router_completion_state_uses_router_resolver_binding(monkeypatch, tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")

    monkeypatch.setattr(
        router,
        "resolve_study_completion_state",
        lambda *, study_root: {"patched_root": str(study_root)},
    )

    assert router._study_completion_state(study_root=tmp_path) == {"patched_root": str(tmp_path)}


def test_study_runtime_router_sync_completion_uses_router_message_builder_binding(monkeypatch, tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        router,
        "_build_study_completion_request_message",
        lambda **kwargs: "patched completion message",
    )
    monkeypatch.setattr(
        router.med_deepscientist_transport,
        "sync_completion_with_approval",
        lambda **kwargs: seen.setdefault("decision_request_payload", kwargs["decision_request_payload"]) or {"ok": True},
    )

    class _Contract:
        summary = "summary"
        user_approval_text = "approved"

    class _CompletionState:
        contract = _Contract()

    router._sync_study_completion(
        runtime_root=tmp_path / "runtime",
        quest_id="quest-001",
        study_id="study-001",
        study_root=tmp_path / "study",
        completion_state=_CompletionState(),
        source="test",
    )

    assert seen["decision_request_payload"]["message"] == "patched completion message"


def test_study_runtime_router_reexports_split_startup_and_completion_helpers() -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    startup = importlib.import_module("med_autoscience.controllers.study_runtime_startup")
    completion = importlib.import_module("med_autoscience.controllers.study_runtime_completion")

    assert router._record_quest_runtime_audits is decision._record_quest_runtime_audits
    assert router._status_state is decision._status_state
    assert router._status_payload is decision._status_payload
    assert router._prepare_runtime_overlay is startup._prepare_runtime_overlay
    assert router._audit_runtime_overlay is startup._audit_runtime_overlay
    assert router._build_startup_contract is startup._build_startup_contract
    assert router._build_create_payload is startup._build_create_payload
    assert router._runtime_reentry_requires_startup_hydration is startup._runtime_reentry_requires_startup_hydration
    assert router._runtime_reentry_requires_managed_skill_audit is startup._runtime_reentry_requires_managed_skill_audit
    assert router._run_startup_hydration is startup._run_startup_hydration
    assert router._sync_existing_quest_startup_context is startup._sync_existing_quest_startup_context
    assert router._study_completion_state is completion._study_completion_state
    assert router._build_study_completion_request_message is completion._build_study_completion_request_message
    assert router._sync_study_completion is completion._sync_study_completion
