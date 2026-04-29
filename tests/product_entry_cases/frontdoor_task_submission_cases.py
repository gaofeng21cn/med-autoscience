from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from . import cockpit_status_and_frontdesk_focus as _cockpit_status_and_frontdesk_focus
from . import manifest_launch_and_task_intake as _manifest_launch_and_task_intake
from . import repo_shell_and_handoff_templates as _repo_shell_and_handoff_templates

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_cockpit_status_and_frontdesk_focus)
_module_reexport(_manifest_launch_and_task_intake)
_module_reexport(_repo_shell_and_handoff_templates)

def test_startup_contract_appends_latest_task_intake_context(monkeypatch, tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    startup_module = importlib.import_module("med_autoscience.controllers.study_runtime_startup")
    resolution_module = importlib.import_module("med_autoscience.controllers.study_runtime_resolution")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先发现并修复卡住、无进度、figure 质量坏循环等系统性问题。",
        constraints=("先保 runtime supervision truth",),
    )

    monkeypatch.setattr(
        startup_module.startup_boundary_gate_controller,
        "evaluate_startup_boundary",
        lambda **kwargs: {
            "allow_compute_stage": False,
            "required_first_anchor": "scout",
            "effective_custom_profile": "startup_boundary_blocked",
            "legacy_code_execution_allowed": False,
            "missing_requirements": ["paper_framing"],
        },
    )
    monkeypatch.setattr(
        startup_module.runtime_reentry_gate_controller,
        "evaluate_runtime_reentry",
        lambda **kwargs: {"allow_runtime_entry": True},
    )
    monkeypatch.setattr(
        startup_module.journal_shortlist_controller,
        "resolve_journal_shortlist",
        lambda **kwargs: {"status": "not_started", "shortlist": [], "candidate_count": 0, "uncovered_shortlist_entries": []},
    )
    monkeypatch.setattr(
        startup_module.medical_analysis_contract_controller,
        "resolve_medical_analysis_contract_for_study",
        lambda **kwargs: {"status": "resolved"},
    )
    monkeypatch.setattr(
        startup_module.medical_reporting_contract_controller,
        "resolve_medical_reporting_contract_for_study",
        lambda **kwargs: {"status": "resolved", "reporting_guideline_family": "TRIPOD"},
    )

    payload = startup_module._build_startup_contract(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        study_payload=resolution_module._load_yaml_dict(study_root / "study.yaml"),
        execution={"startup_contract_profile": "paper_required_autonomous", "launch_profile": "continue_existing_state"},
    )

    assert payload["task_intake_ref"]["study_id"] == "001-risk"
    assert "figure 质量坏循环" in payload["custom_brief"]

def test_submit_study_task_enqueues_task_context_for_live_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')

    class FakeBackend:
        BACKEND_ID = "fake"
        ENGINE_ID = "fake-engine"

        def chat_quest(
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            text: str,
            source: str,
            reply_to_interaction_id: str | None = None,
            decision_response: dict[str, object] | None = None,
        ) -> dict[str, object]:
            assert runtime_root == profile.managed_runtime_home
            assert quest_id == "001-risk"
            assert source == "codex-study-task-intake"
            assert reply_to_interaction_id is None
            assert decision_response is None
            assert "优先清理 publication gate 文面阻塞" in text
            assert "不要继续泛化分析" in text
            assert "只使用现有证据" in text
            return {"ok": True, "message": {"id": "msg-formal-001"}}

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: FakeBackend())
    monkeypatch.setattr(
        product_entry.user_message,
        "enqueue_user_message",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("formal live submit should not fall back to queue")),
    )

    result = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先清理 publication gate 文面阻塞。",
        constraints=("不要继续泛化分析",),
        evidence_boundary=("只使用现有证据",),
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    runtime_intervention = result["runtime_intervention"]

    assert runtime_intervention["intervention_enqueued"] is True
    assert runtime_intervention["quest_status"] == "running"
    assert runtime_intervention["message_id"] == "msg-formal-001"
    assert runtime_intervention["reason"] == "live_runtime_task_context_submitted"
    assert queue["pending"] == []
    assert runtime_state["pending_user_message_count"] == 0


def test_submit_study_task_deduplicates_same_live_runtime_task_for_current_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')
    calls: list[str] = []

    class FakeBackend:
        BACKEND_ID = "fake"
        ENGINE_ID = "fake-engine"

        def chat_quest(
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            text: str,
            source: str,
            reply_to_interaction_id: str | None = None,
            decision_response: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append(text)
            return {"ok": True, "message": {"id": "msg-formal-001"}}

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: FakeBackend())

    first = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="根据审稿意见修订 manuscript。",
        constraints=("补齐 Table 1 和 Table 2",),
    )
    second = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="根据审稿意见修订 manuscript。",
        constraints=("补齐 Table 1 和 Table 2",),
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    first_intervention = first["runtime_intervention"]
    second_intervention = second["runtime_intervention"]

    assert len(calls) == 1
    assert first_intervention["delivery_mode"] == "managed_runtime_chat"
    assert first_intervention["message_id"] == "msg-formal-001"
    assert second_intervention["delivery_mode"] == "managed_runtime_chat"
    assert second_intervention["message_id"] == "msg-formal-001"
    assert second_intervention["reason"] == "live_runtime_task_context_already_delivered"
    assert second_intervention["idempotent_replay"] is True
    assert queue["pending"] == []
    assert runtime_state["pending_user_message_count"] == 0


def test_submit_study_task_deduplicates_same_live_runtime_task_across_run_attempts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')
    calls: list[str] = []

    class FakeBackend:
        BACKEND_ID = "fake"
        ENGINE_ID = "fake-engine"

        def chat_quest(
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            text: str,
            source: str,
            reply_to_interaction_id: str | None = None,
            decision_response: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append(text)
            return {"ok": True, "message": {"id": f"msg-formal-{len(calls):03d}"}}

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: FakeBackend())

    first = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="根据审稿意见修订 manuscript。",
        constraints=("补齐 Table 1 和 Table 2",),
    )
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    runtime_state["active_run_id"] = "run-live-002"
    write_text(quest_root / ".ds" / "runtime_state.json", json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n")
    second = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="根据审稿意见修订 manuscript。",
        constraints=("补齐 Table 1 和 Table 2",),
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    first_intervention = first["runtime_intervention"]
    second_intervention = second["runtime_intervention"]

    assert len(calls) == 1
    assert first_intervention["message_id"] == "msg-formal-001"
    assert second_intervention["message_id"] == "msg-formal-001"
    assert second_intervention["reason"] == "live_runtime_task_context_already_delivered"
    assert second_intervention["idempotent_replay"] is True
    assert queue["pending"] == []


def test_submit_study_task_uses_managed_quest_id_for_live_runtime_intervention(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk", quest_id="001-risk-managed")
    short_quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    managed_quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk-managed"
    write_text(managed_quest_root / "quest.yaml", "id: 001-risk-managed\n")
    write_text(
        managed_quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk-managed",
                "status": "running",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(managed_quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')

    class FakeBackend:
        BACKEND_ID = "fake"
        ENGINE_ID = "fake-engine"

        def chat_quest(
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            text: str,
            source: str,
            reply_to_interaction_id: str | None = None,
            decision_response: dict[str, object] | None = None,
        ) -> dict[str, object]:
            assert runtime_root == profile.managed_runtime_home
            assert quest_id == "001-risk-managed"
            assert source == "codex-study-task-intake"
            assert "根据审稿意见修订 manuscript" in text
            return {"ok": True, "message": {"id": "msg-managed-quest"}}

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: FakeBackend())

    result = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="根据审稿意见修订 manuscript。",
    )

    runtime_intervention = result["runtime_intervention"]
    assert not short_quest_root.exists()
    assert runtime_intervention["quest_id"] == "001-risk-managed"
    assert runtime_intervention["quest_root"] == str(managed_quest_root)
    assert runtime_intervention["intervention_enqueued"] is True
    assert runtime_intervention["message_id"] == "msg-managed-quest"
    assert runtime_intervention["reason"] == "live_runtime_task_context_submitted"


def test_submit_study_task_requires_reactivation_for_stopped_reviewer_revision(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "stopped",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    result = product_entry.submit_study_task(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        task_intent="根据用户反馈和审稿意见推进 manuscript revision，修复 Methods、Figure/Table 与投稿包版本不一致。",
        first_cycle_outputs=("revision checklist",),
    )

    runtime_intervention = result["runtime_intervention"]
    assert runtime_intervention["intervention_enqueued"] is False
    assert runtime_intervention["quest_status"] == "stopped"
    assert runtime_intervention["reason"] == "stopped_revision_requires_study_reactivation"
    assert runtime_intervention["requires_study_reactivation"] is True
    assert runtime_intervention["next_required_action"] == "launch_study_with_stopped_relaunch"
    assert "--allow-stopped-relaunch" in runtime_intervention["recommended_next_command"]
    assert str(profile_ref.resolve()) in runtime_intervention["recommended_next_command"]
    assert runtime_intervention["current_package_edit_policy"]["direct_current_package_edit_allowed"] is False


def test_submit_study_task_falls_back_to_durable_queue_when_backend_chat_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: None)

    result = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先比较不同省份的生物制剂使用意向。",
        constraints=("保留多中心分层分析",),
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    runtime_intervention = result["runtime_intervention"]

    assert runtime_intervention["intervention_enqueued"] is True
    assert runtime_intervention["delivery_mode"] == "durable_queue_fallback"
    assert runtime_intervention["reason"] == "live_runtime_task_context_enqueued_fallback"
    assert len(queue["pending"]) == 1
    assert "优先比较不同省份的生物制剂使用意向" in queue["pending"][0]["content"]
    assert "保留多中心分层分析" in queue["pending"][0]["content"]
    assert runtime_state["pending_user_message_count"] == 1
