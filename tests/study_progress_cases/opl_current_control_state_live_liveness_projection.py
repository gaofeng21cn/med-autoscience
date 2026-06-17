from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_projection_uses_opl_current_control_state_as_live_liveness_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-24T22:50:48+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live-001",
                    "active_stage_attempt_id": "sat-live-001",
                    "active_workflow_id": "wf-live-001",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-24T22:52:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-001"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-001"
    assert runtime_liveness["active_workflow_id"] == "wf-live-001"
    assert runtime_liveness["provider_completion_is_domain_completion"] is False
    assert runtime_liveness["authority"] == "observability_only"
    assert "domain_ready" not in runtime_liveness
    assert "publication_ready" not in runtime_liveness
    assert "artifact_ready" not in runtime_liveness
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-001"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-001"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_anchor"] == "decision"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-001"


def test_progress_projection_uses_opl_live_attempt_when_runtime_state_waiting_for_user(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 3,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-29T09:31:45+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "waiting_for_user",
                    "active_run_id": "opl-stage-attempt://sat-live-waiting",
                    "active_stage_attempt_id": "sat-live-waiting",
                    "active_workflow_id": "wf-live-waiting",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-29T09:32:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-waiting"
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-waiting"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-waiting"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_anchor"] == "decision"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-waiting"


def test_progress_projection_uses_live_opl_queue_attempt_when_handoff_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-26T20:11:03+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "stale",
                    },
                }
            ],
        },
    )

    monkeypatch.setattr(
        decision_module.opl_provider_attempts,
        "live_provider_attempt_for_study",
        lambda **_: {
            "surface_kind": "opl_current_control_state_provider_attempt",
            "source": "opl_family_runtime_queue_inspect",
            "active_run_id": "opl-stage-attempt://sat-live-queue",
            "active_stage_attempt_id": "sat-live-queue",
            "active_workflow_id": "wf-live-queue",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-26T20:16:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["provider_attempt_source"] == "opl_family_runtime_queue_inspect"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-queue"
    assert runtime_liveness["active_workflow_id"] == "wf-live-queue"
    assert runtime_liveness["handoff_path"] == str(handoff_path)
    assert runtime_liveness["handoff_generated_at"] == "2026-05-26T20:11:03+00:00"
    assert runtime_liveness["provider_completion_is_domain_completion"] is False
    assert "domain_ready" not in runtime_liveness
    assert "publication_ready" not in runtime_liveness
    assert "artifact_ready" not in runtime_liveness
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-queue"


def test_progress_projection_uses_live_opl_attempt_when_fresh_handoff_is_non_running_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-06T10:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "blocked",
                        "runtime_liveness_status": "none",
                        "blocked_reason": "provider_admission_current_control_state_required",
                    },
                    "blocked_reason": "provider_admission_current_control_state_required",
                    "next_owner": "one-person-lab",
                }
            ],
        },
    )
    monkeypatch.setattr(
        decision_module.opl_provider_attempts,
        "live_provider_attempt_for_study",
        lambda **_: {
            "surface_kind": "opl_current_control_state_provider_attempt",
            "source": "opl_family_runtime_attempt_inspect",
            "active_run_id": "opl-stage-attempt://sat-live-supersedes-blocker",
            "active_stage_attempt_id": "sat-live-supersedes-blocker",
            "active_workflow_id": "wf-live-supersedes-blocker",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-06-06T10:01:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["provider_attempt_source"] == "opl_family_runtime_attempt_inspect"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-supersedes-blocker"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-supersedes-blocker"
    assert runtime_liveness["action_type"] == "run_quality_repair_batch"
    assert runtime_liveness["work_unit_id"] == "medical_prose_write_repair"
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-supersedes-blocker"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-supersedes-blocker"


def test_progress_projection_uses_live_opl_attempt_when_quest_state_is_paused(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "paused",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "quest_paused",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-05T03:00:00+00:00",
            "authority": "observability_only",
            "studies": [],
        },
    )

    monkeypatch.setattr(
        decision_module.opl_provider_attempts,
        "live_provider_attempt_for_study",
        lambda **_: {
            "surface_kind": "opl_current_control_state_provider_attempt",
            "source": "opl_family_runtime_attempt_inspect",
            "active_run_id": "opl-stage-attempt://sat-live-paused",
            "active_stage_attempt_id": "sat-live-paused",
            "active_workflow_id": "wf-live-paused",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-06-05T03:01:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["provider_attempt_source"] == "opl_family_runtime_attempt_inspect"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-paused"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-paused"
    assert runtime_liveness["active_workflow_id"] == "wf-live-paused"
    assert runtime_liveness["snapshot"] == {"status": "paused"}
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-paused"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-paused"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_anchor"] == "decision"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-paused"


def test_progress_projection_treats_terminal_opl_success_handoff_as_settled_not_unhealthy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    profile.runtime_root.mkdir(parents=True)
    medautosci_config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    medautosci_config.parent.mkdir(parents=True, exist_ok=True)
    medautosci_config.write_text("MEDAUTOSCI_PROFILE=diabetes\n", encoding="utf-8")
    controlled_backend = profile.workspace_root / "ops" / "mas"
    (controlled_backend / "bin").mkdir(parents=True, exist_ok=True)
    (controlled_backend / "config.env").write_text("MEDAUTOSCI_PROFILE=diabetes\n", encoding="utf-8")
    behavior_gate = controlled_backend / "behavior_equivalence_gate.yaml"
    behavior_gate.parent.mkdir(parents=True, exist_ok=True)
    behavior_gate.write_text(
        "\n".join(
            [
                "schema_version: v1",
                "phase_25_ready: true",
                "critical_overrides: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="route_back_same_line",
        requires_human_confirmation=False,
        action_type="run_quality_repair_batch",
        reason="Route the current paper blocker to the owner work unit.",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-28T08:43:37+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                    "active_workflow_id": None,
                    "running_provider_attempt": False,
                    "handoff_generated_at": "2026-05-28T08:43:37+00:00",
                    "task_id": "frt-terminal-success",
                    "task_kind": "domain_route/reconcile-apply",
                    "current_attempt_state": "succeeded",
                    "reconciliation_status": "succeeded",
                    "terminal_provider_transport_observation_superseded": True,
                    "superseded_terminal_observation_reason": "temporal_workflow_not_started_or_not_found",
                    "superseded_by_task_status": "succeeded",
                    "next_work_unit": {
                        "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                        "lane": "analysis-campaign",
                        "summary": (
                            "Add uncertainty intervals, grouped calibration evidence, "
                            "and reproducibility details."
                        ),
                    },
                    "runtime_health": {
                        "health_status": "settled",
                        "runtime_liveness_status": "none",
                        "summary": (
                            "OPL queue transport is terminal succeeded and no provider attempt is live."
                        ),
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(decision_module.opl_provider_attempts, "live_provider_attempt_for_study", lambda **_: None)
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-28T08:45:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "none"
    assert runtime_liveness["source"] == "opl_current_control_state_terminal_transport_settled"
    assert runtime_liveness["active_run_id"] is None
    assert runtime_liveness["running_provider_attempt"] is False
    assert runtime_liveness["reconciliation_status"] == "succeeded"
    assert runtime_liveness["current_attempt_state"] == "succeeded"
    assert runtime_liveness["terminal_provider_transport_observation_superseded"] is True
    assert runtime_liveness["provider_completion_is_domain_completion"] is False
    assert result.get("active_run_id") is None
    assert "execution_owner_guard" not in result
    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "continue_supervising_runtime"
    assert result["runtime_health_snapshot"]["worker_liveness_state"]["state"] == "not_live"
    assert "runtime_recovery_retry_budget_exhausted" not in result["runtime_health_snapshot"]["blocking_reasons"]
