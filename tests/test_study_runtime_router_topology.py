from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace


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


def test_study_runtime_router_resolve_study_uses_router_yaml_loader_binding(monkeypatch, tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    study_root = tmp_path / "studies" / "study-001"

    monkeypatch.setattr(
        router,
        "_load_yaml_dict",
        lambda path: {"study_id": "study-001", "title": "patched"},
    )

    resolved_study_id, resolved_study_root, study_payload = router._resolve_study(
        profile=SimpleNamespace(studies_root=tmp_path / "studies"),
        study_id="study-001",
        study_root=study_root,
    )

    assert resolved_study_id == "study-001"
    assert resolved_study_root == study_root.resolve()
    assert study_payload["title"] == "patched"


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


def test_study_runtime_router_create_quest_uses_router_transport_binding(monkeypatch, tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        router.med_deepscientist_transport,
        "create_quest",
        lambda **kwargs: (seen.__setitem__("create_kwargs", kwargs) or {"ok": True}),
    )

    payload = {"quest_id": "quest-001"}
    result = router._create_quest(runtime_root=tmp_path / "runtime", payload=payload)

    assert seen["create_kwargs"]["payload"] == payload
    assert result == {"ok": True}


def test_study_runtime_router_build_execution_context_uses_router_completion_binding(monkeypatch) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")

    monkeypatch.setattr(
        router.study_runtime_protocol,
        "resolve_study_runtime_context",
        lambda **kwargs: SimpleNamespace(
            runtime_root=Path("/tmp/runtime"),
            quest_root=Path("/tmp/runtime/quests/study-001"),
            runtime_binding_path=Path("/tmp/study/runtime_binding.yaml"),
            startup_payload_root=Path("/tmp/runtime/startup-payloads/study-001"),
            launch_report_path=Path("/tmp/study/artifacts/runtime/last_launch_report.json"),
        ),
    )
    monkeypatch.setattr(
        router,
        "_study_completion_state",
        lambda *, study_root: {"patched_root": str(study_root)},
    )

    context = router._build_execution_context(
        profile=SimpleNamespace(),
        study_id="study-001",
        study_root=Path("/tmp/study"),
        study_payload={"execution": {"quest_id": "quest-001"}},
        source="test",
    )

    assert context.completion_state == {"patched_root": "/tmp/study"}


def test_study_runtime_router_build_context_create_payload_uses_router_binding(monkeypatch) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    context = SimpleNamespace(
        profile=SimpleNamespace(),
        study_id="study-001",
        study_root=Path("/tmp/study"),
        study_payload={},
        execution={},
    )

    monkeypatch.setattr(
        router,
        "_build_create_payload",
        lambda **kwargs: {"marker": "patched-create-payload"},
    )

    payload = router._build_context_create_payload(context)

    assert payload["marker"] == "patched-create-payload"


def test_study_runtime_router_execute_runtime_decision_uses_router_dispatch_binding(monkeypatch) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    expected = router.StudyRuntimeExecutionOutcome(binding_last_action="resume")
    status = SimpleNamespace(
        decision=router.StudyRuntimeDecision.RESUME,
        should_refresh_startup_hydration_while_blocked=lambda: False,
        quest_exists=True,
    )

    monkeypatch.setattr(
        router,
        "_execute_resume_runtime_decision",
        lambda **kwargs: expected,
    )

    outcome = router._execute_runtime_decision(status=status, context=SimpleNamespace())

    assert outcome is expected


def test_study_runtime_router_ensure_runtime_uses_router_persistence_binding(monkeypatch, tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    study_root = tmp_path / "studies" / "study-001"
    study_payload = {"study_id": "study-001"}
    context = SimpleNamespace(
        study_id="study-001",
        study_root=study_root,
        runtime_binding_path=study_root / "runtime_binding.yaml",
        launch_report_path=study_root / "artifacts" / "runtime" / "last_launch_report.json",
        runtime_root=tmp_path / "runtime",
        startup_payload_root=tmp_path / "runtime" / "startup-payloads" / "study-001",
    )
    outcome = router.StudyRuntimeExecutionOutcome(binding_last_action="noop")
    seen: dict[str, object] = {}
    status = SimpleNamespace(
        quest_id="quest-001",
        to_dict=lambda: {"decision": "noop"},
        record_runtime_artifacts=lambda **kwargs: seen.setdefault("recorded_artifacts", kwargs),
    )

    monkeypatch.setattr(
        router,
        "_resolve_study",
        lambda **kwargs: ("study-001", study_root, study_payload),
    )
    monkeypatch.setattr(router, "_build_execution_context", lambda **kwargs: context)
    monkeypatch.setattr(router, "_status_state", lambda **kwargs: status)
    monkeypatch.setattr(router, "_run_runtime_preflight", lambda **kwargs: None)
    monkeypatch.setattr(router, "_execute_runtime_decision", lambda **kwargs: outcome)
    monkeypatch.setattr(
        router,
        "_persist_runtime_artifacts",
        lambda **kwargs: seen.setdefault("persist_kwargs", kwargs),
    )

    result = router.ensure_study_runtime(profile=SimpleNamespace(), study_id="study-001", source="test-source")

    assert seen["persist_kwargs"]["status"] is status
    assert seen["persist_kwargs"]["context"] is context
    assert seen["persist_kwargs"]["outcome"] is outcome
    assert seen["persist_kwargs"]["force"] is False
    assert seen["persist_kwargs"]["source"] == "test-source"
    assert result == {"decision": "noop"}


def test_study_runtime_router_reexports_split_startup_and_completion_helpers() -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = importlib.import_module("med_autoscience.controllers.study_runtime_transport")
    resolution = importlib.import_module("med_autoscience.controllers.study_runtime_resolution")
    decision = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    startup = importlib.import_module("med_autoscience.controllers.study_runtime_startup")
    completion = importlib.import_module("med_autoscience.controllers.study_runtime_completion")
    execution = importlib.import_module("med_autoscience.controllers.study_runtime_execution")

    assert router._inspect_quest_live_execution is transport._inspect_quest_live_execution
    assert router._create_quest is transport._create_quest
    assert router._resume_quest is transport._resume_quest
    assert router._pause_quest is transport._pause_quest
    assert router._update_quest_startup_context is transport._update_quest_startup_context
    assert router._sync_completion_with_approval is transport._sync_completion_with_approval
    assert router._load_yaml_dict is resolution._load_yaml_dict
    assert router._resolve_study is resolution._resolve_study
    assert router._execution_payload is resolution._execution_payload
    assert router._record_quest_runtime_audits is decision._record_quest_runtime_audits
    assert router._status_state is decision._status_state
    assert router._status_payload is decision._status_payload
    assert router._build_execution_context is execution._build_execution_context
    assert router._build_context_create_payload is execution._build_context_create_payload
    assert router._run_runtime_preflight is execution._run_runtime_preflight
    assert router._execute_create_runtime_decision is execution._execute_create_runtime_decision
    assert router._execute_resume_runtime_decision is execution._execute_resume_runtime_decision
    assert router._execute_blocked_refresh_runtime_decision is execution._execute_blocked_refresh_runtime_decision
    assert router._execute_pause_runtime_decision is execution._execute_pause_runtime_decision
    assert router._execute_completion_runtime_decision is execution._execute_completion_runtime_decision
    assert router._execute_runtime_decision is execution._execute_runtime_decision
    assert router._persist_runtime_artifacts is execution._persist_runtime_artifacts
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


def test_study_runtime_router_sync_existing_startup_context_forwards_requested_baseline_ref(monkeypatch, tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        router,
        "_update_quest_startup_context",
        lambda **kwargs: (
            seen.__setitem__("kwargs", kwargs)
            or router.StudyRuntimeStartupContextSyncResult.from_payload(
                {
                    "ok": True,
                    "quest_id": kwargs["quest_id"],
                    "snapshot": {
                        "quest_id": kwargs["quest_id"],
                        "startup_contract": kwargs["startup_contract"],
                        "requested_baseline_ref": kwargs.get("requested_baseline_ref"),
                    },
                }
            )
        ),
    )

    result = router._sync_existing_quest_startup_context(
        runtime_root=tmp_path / "runtime",
        quest_id="quest-001",
        create_payload={
            "startup_contract": {"schema_version": 4},
        },
        execution={"requested_baseline_ref": {"baseline_id": "demo-baseline"}},
    )

    assert seen["kwargs"]["requested_baseline_ref"] == {"baseline_id": "demo-baseline"}
    assert result.to_dict()["snapshot"]["requested_baseline_ref"] == {"baseline_id": "demo-baseline"}
