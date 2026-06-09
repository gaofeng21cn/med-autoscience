from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_does_not_auto_recover_package_ready_handoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "memory" / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    calls: list[tuple[str, str]] = []

    def parked_status() -> dict[str, object]:
        return {
            **make_progress_projection_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_parked_on_unchanged_finalize_state",
            ),
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "execution": {
                "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            },
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        }

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: calls.append(("status", Path(study_root).name)) or parked_status(),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == [("status", "001-risk")]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []

def test_watch_runtime_holds_auto_recovery_when_flapping_circuit_breaker_is_active(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": "2026-04-26T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "status": "handoff_required",
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_runtime_read_model_retired": True,
            "mas_materializes_runtime_supervision": False,
            "health_status": "recovering",
            "runtime_stability_status": "flapping",
            "flapping_episode_count": 2,
            "flapping_circuit_breaker": True,
            "runtime_reason": "quest_marked_running_but_no_live_session",
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
            },
        },
    )
    no_live_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: calls.append(("status", Path(study_root).name)) or no_live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == [("status", "001-risk")]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_recovery_holds"] == [
        {
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "hold_reason": "flapping_circuit_breaker_active",
            "recommended_probe": "refresh_runtime_liveness_before_resume",
            "flapping_episode_count": 2,
            "recovery_probe": {
                "probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::2",
                "status": "hold_active",
                "recommended_action": "hold",
                "reason": "flapping_circuit_breaker_active",
                "next_probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::3",
                "liveness": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
                "current_status": {
                    "quest_status": "running",
                    "decision": "resume",
                    "reason": "quest_marked_running_but_no_live_session",
                    "runtime_stability_status": "flapping",
                    "flapping_circuit_breaker": True,
                    "flapping_episode_count": 2,
                },
            },
        }
    ]
    assert not (study_root / "artifacts" / "runtime" / "recovery_probe" / "latest.json").exists()

def test_watch_runtime_does_not_hold_recovery_for_plain_opl_runtime_handoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": "2026-06-01T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "status": "handoff_required",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_runtime_read_model_retired": True,
            "mas_materializes_runtime_supervision": False,
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "reason": "mas_runtime_supervision_retired",
            },
        },
    )
    no_live_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: no_live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.domain_status_projection,
        "request_opl_stage_attempt",
        lambda **kwargs: calls.append(kwargs)
        or {
            **no_live_status,
            "status": "opl_stage_attempt_requested",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
        raising=False,
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_recovery_holds"] == []
    assert result["managed_study_auto_recoveries"] == []
    action = result["managed_study_actions"][0]
    assert action["study_id"] == "001-risk"
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["resume_postcondition"]["status"] == "opl_stage_attempt_admission_required"
    assert action["resume_postcondition"]["typed_blocker"]["owner"] == "one-person-lab"
    assert not (study_root / "artifacts" / "runtime" / "recovery_probe" / "latest.json").exists()

def test_domain_health_diagnostic_apply_can_request_opl_owner_route_reconcile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_ids = ("001-risk", "002-risk")
    for study_id in study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
    calls: list[dict[str, object]] = []
    materialize_calls: list[dict[str, object]] = []
    dispatch_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "portable_owner_route_reconcile",
            "apply_safe_actions": kwargs["apply_safe_actions"],
            "study_count": len(kwargs["study_ids"]),
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                }
                for study_id in kwargs["study_ids"]
            ],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: materialize_calls.append(kwargs)
        or {
            "surface": "domain_action_request_materializer",
            "materialized_count": 1,
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: dispatch_calls.append(kwargs)
        or {
            "surface": "domain_owner_action_dispatch",
            "executed_count": 1,
            "codex_dispatch_count": 1,
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert len(calls) == 2
    assert calls[0]["profile"] == profile
    assert calls[0]["study_ids"] == study_ids
    assert calls[0]["apply_safe_actions"] is True
    assert calls[0]["developer_supervisor_mode"] == "developer_apply_safe"
    assert calls[1]["profile"] == profile
    assert calls[1]["study_ids"] == study_ids
    assert calls[1]["apply_safe_actions"] is True
    assert calls[1]["developer_supervisor_mode"] == "developer_apply_safe"
    assert calls[1]["persist_surfaces"] is True
    assert calls[1]["retain_unscanned_studies"] is True
    assert result["opl_owner_route_reconcile_request"] == {
        "surface": "portable_owner_route_reconcile",
        "apply_safe_actions": True,
        "study_count": 2,
        "studies": [
            {
                "study_id": "001-risk",
                "running_provider_attempt": False,
                "active_run_id": None,
                "active_stage_attempt_id": None,
            },
            {
                "study_id": "002-risk",
                "running_provider_attempt": False,
                "active_run_id": None,
                "active_stage_attempt_id": None,
            },
        ],
    }
    assert len(materialize_calls) == 1
    assert materialize_calls[0]["profile"] == profile
    assert materialize_calls[0]["study_ids"] == study_ids
    assert materialize_calls[0]["mode"] == "developer_apply_safe"
    assert materialize_calls[0]["apply"] is True
    assert len(dispatch_calls) == 1
    assert dispatch_calls[0]["profile"] == profile
    assert dispatch_calls[0]["study_ids"] == study_ids
    assert dispatch_calls[0]["action_types"] == ()
    assert dispatch_calls[0]["mode"] == "developer_apply_safe"
    assert dispatch_calls[0]["apply"] is True
    supervisor_tick = result["developer_supervisor_same_tick"]
    assert supervisor_tick["surface"] == "developer_supervisor_same_tick"
    assert supervisor_tick["schema_version"] == 1
    assert supervisor_tick["mode"] == "developer_apply_safe"
    assert supervisor_tick["study_ids"] == ["001-risk", "002-risk"]
    assert supervisor_tick["pass_count"] == 1
    assert supervisor_tick["stop_reason"] == "provider_handoff_written_admission_pending"
    assert supervisor_tick["actions"] == [
        "owner-route-reconcile",
        "domain-action-request-materialize",
        "domain-owner-action-dispatch",
    ]
    assert supervisor_tick["owner_route_reconcile"] == result["opl_owner_route_reconcile_request"]
    assert supervisor_tick["materialize"] == {
        "surface": "domain_action_request_materializer",
        "materialized_count": 1,
    }
    assert supervisor_tick["dispatch"] == {
        "surface": "domain_owner_action_dispatch",
        "executed_count": 1,
        "codex_dispatch_count": 1,
    }
    assert supervisor_tick["iterations"][0]["progress_first_delta"]["codex_dispatch_count"] == 1
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_provider_admission"] is True
    assert diagnostic["next_forced_delta"]["required_delta_kind"] == "opl_provider_attempt_admission"
    assert diagnostic["forbidden_next_actions"] == [
        "repeat_receipt_reconcile_without_owner_delta",
        "repeat_read_model_reconcile_without_owner_delta",
        "start_new_provider_attempt_for_same_source_without_owner_delta",
    ]
    assert supervisor_tick["owner_boundaries"] == {
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
    }


def test_domain_health_diagnostic_owner_route_same_tick_honors_explicit_study_scope(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    all_study_ids = ("001-risk", "002-risk", "003-risk", "004-risk")
    focused_study_ids = ("002-risk", "003-risk")
    for study_id in all_study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []
    materialize_calls: list[dict[str, object]] = []
    dispatch_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        return {
            "surface": "portable_owner_route_reconcile",
            "apply_safe_actions": kwargs["apply_safe_actions"],
            "study_ids": list(kwargs["study_ids"]),
            "study_count": len(kwargs["study_ids"]),
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: materialize_calls.append(kwargs)
        or {
            "surface": "domain_action_request_materializer",
            "materialized_count": len(kwargs["study_ids"]),
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: dispatch_calls.append(kwargs)
        or {
            "surface": "domain_owner_action_dispatch",
            "executed_count": len(kwargs["study_ids"]),
            "codex_dispatch_count": 1,
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=focused_study_ids,
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert scan_calls[0]["study_ids"] == focused_study_ids
    assert materialize_calls[0]["study_ids"] == focused_study_ids
    assert dispatch_calls[0]["study_ids"] == focused_study_ids
    touched_studies = set(scan_calls[0]["study_ids"])
    touched_studies.update(materialize_calls[0]["study_ids"])
    touched_studies.update(dispatch_calls[0]["study_ids"])
    assert touched_studies == set(focused_study_ids)
    assert "001-risk" not in touched_studies
    assert "004-risk" not in touched_studies
    supervisor_tick = result["developer_supervisor_same_tick"]
    assert supervisor_tick["study_ids"] == list(focused_study_ids)
    assert result["opl_owner_route_reconcile_request"]["study_ids"] == list(focused_study_ids)


def test_domain_health_diagnostic_focused_scope_limits_runtime_scan_and_managed_status(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    all_study_ids = ("001-risk", "002-risk", "003-risk", "004-risk")
    focused_study_ids = ("002-risk", "003-risk")
    for study_id in all_study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
        quest_root = profile.runtime_root / study_id
        dump_json(quest_root / ".ds" / "runtime_state.json", {"quest_id": study_id, "status": "running"})

    status_reads: list[str] = []
    quest_scans: list[str] = []
    scan_calls: list[dict[str, object]] = []
    materialize_calls: list[dict[str, object]] = []
    dispatch_calls: list[dict[str, object]] = []

    def fake_progress_projection(*, profile, study_root, **kwargs):
        status_reads.append(Path(study_root).name)
        study_id = Path(study_root).name
        return {
            **make_progress_projection_payload(
                study_id=study_id,
                decision="blocked",
                reason="focused_scope_probe",
            ),
            "study_root": str(study_root),
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "running",
        }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", fake_progress_projection)
    monkeypatch.setattr(
        module.quest_state,
        "iter_active_quests",
        lambda runtime_root: [Path(runtime_root) / study_id for study_id in all_study_ids],
    )
    monkeypatch.setattr(
        module,
        "run_domain_health_diagnostic_for_quest",
        lambda *, quest_root, controller_runners, apply: quest_scans.append(Path(quest_root).name)
        or {
            "schema_version": 1,
            "scanned_at": "2026-06-02T00:00:00+00:00",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "controllers": {},
        },
    )
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: scan_calls.append(kwargs)
        or {
            "surface": "portable_owner_route_reconcile",
            "study_ids": list(kwargs["study_ids"]),
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: materialize_calls.append(kwargs)
        or {"surface": "domain_action_request_materializer", "request_task_count": 0},
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: dispatch_calls.append(kwargs)
        or {"surface": "domain_owner_action_dispatch", "execution_count": 0},
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=focused_study_ids,
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert set(status_reads) == set(focused_study_ids)
    assert quest_scans == list(focused_study_ids)
    assert result["scanned_quests"] == list(focused_study_ids)
    assert scan_calls[0]["study_ids"] == focused_study_ids
    assert materialize_calls[0]["study_ids"] == focused_study_ids
    assert dispatch_calls[0]["study_ids"] == focused_study_ids
    assert "001-risk" not in status_reads
    assert "004-risk" not in status_reads
    assert "004-risk" not in quest_scans


def test_domain_health_diagnostic_same_tick_pumps_receipt_followthrough_before_next_heartbeat(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "001-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []
    materialize_calls: list[dict[str, object]] = []
    dispatch_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        pass_index = len(scan_calls)
        action_type = "run_gate_clearing_batch" if pass_index == 1 else "run_quality_repair_batch"
        admitted = pass_index == 3
        return {
            "surface": "portable_owner_route_reconcile",
            "apply_safe_actions": kwargs["apply_safe_actions"],
            "study_count": len(kwargs["study_ids"]),
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": action_type,
                    "action_id": f"action-{pass_index}",
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": admitted,
                    "active_run_id": "opl-stage-attempt://sat_followthrough" if admitted else None,
                    "active_stage_attempt_id": "sat_followthrough" if admitted else None,
                }
            ],
        }

    def fake_materialize(**kwargs) -> dict[str, object]:
        materialize_calls.append(kwargs)
        return {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
        }

    def fake_dispatch(**kwargs) -> dict[str, object]:
        dispatch_calls.append(kwargs)
        if len(dispatch_calls) == 1:
            return {
                "surface": "domain_owner_action_dispatch",
                "execution_count": 1,
                "executed_count": 1,
                "blocked_count": 0,
                "codex_dispatch_count": 0,
                "executions": [{"execution_status": "executed"}],
            }
        return {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 1,
            "blocked_count": 0,
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        fake_materialize,
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch,
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    supervisor_tick = result["developer_supervisor_same_tick"]
    assert len(scan_calls) == 3
    assert len(materialize_calls) == 3
    assert len(dispatch_calls) == 2
    assert supervisor_tick["pass_count"] == 2
    assert supervisor_tick["stop_reason"] == "provider_attempt_started"
    assert scan_calls[2]["persist_surfaces"] is True
    assert supervisor_tick["iterations"][0]["progress_first_delta"]["dispatch_executed_count"] == 1
    assert supervisor_tick["iterations"][0]["progress_first_delta"]["codex_dispatch_count"] == 0
    assert supervisor_tick["iterations"][1]["progress_first_delta"]["codex_dispatch_count"] == 1
    assert supervisor_tick["iterations"][1]["post_admission_materialize"]["default_executor_dispatch_count"] == 1
    assert supervisor_tick["owner_route_reconcile"]["action_queue"][0]["action_type"] == "run_quality_repair_batch"


def test_domain_health_diagnostic_same_tick_stops_on_repeat_suppression(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "001-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [{"study_id": study_id, "action_type": "run_quality_repair_batch"}],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 0,
            "blocked_count": 0,
            "repeat_suppressed_count": 1,
            "codex_dispatch_count": 0,
            "executions": [
                {
                    "execution_status": "repeat_suppressed",
                    "blocked_reason": "progress_first_owner_redrive_budget_exhausted",
                    "repeat_suppressed": True,
                }
            ],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=3)

    assert supervisor_tick["pass_count"] == 1
    assert supervisor_tick["stop_reason"] == "repeat_suppressed_owner_delta_required"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_next_owner_delta"] is True
    assert diagnostic["next_forced_delta"]["reason"] == "repeat_suppressed_owner_delta_required"
    assert diagnostic["next_forced_delta"]["required_delta_kind"] == (
        "deliverable_progress_delta_or_domain_owner_receipt_or_typed_blocker"
    )
    assert diagnostic["forbidden_next_actions"] == [
        "repeat_receipt_reconcile_without_owner_delta",
        "repeat_read_model_reconcile_without_owner_delta",
        "start_new_provider_attempt_for_same_source_without_owner_delta",
    ]


def test_domain_health_diagnostic_same_tick_reports_max_pass_exhaustion_as_owner_delta_required(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "001-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [{"study_id": study_id, "action_type": "run_gate_clearing_batch"}],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 1,
            "blocked_count": 0,
            "repeat_suppressed_count": 0,
            "codex_dispatch_count": 0,
            "executions": [{"execution_status": "executed"}],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=2)

    assert supervisor_tick["pass_count"] == 2
    assert supervisor_tick["stop_reason"] == "max_passes_exhausted_owner_delta_required"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_next_owner_delta"] is True
    assert diagnostic["next_forced_delta"]["reason"] == "max_passes_exhausted_owner_delta_required"
    assert diagnostic["last_iteration_delta"]["dispatch_executed_count"] == 1


def test_domain_health_diagnostic_does_not_request_opl_owner_route_reconcile_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: pytest.fail("runtime watch must not request owner-route reconcile unless explicitly enabled"),
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: pytest.fail("runtime watch must not materialize domain actions unless owner-route reconcile is explicitly enabled"),
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: pytest.fail("runtime watch must not dispatch domain actions unless owner-route reconcile is explicitly enabled"),
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert "opl_owner_route_reconcile_request" not in result
    assert "developer_supervisor_same_tick" not in result

def test_hard_auto_recovery_ignores_stale_continuation_run_id() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup")

    assert module._should_hard_auto_recover_managed_study(
        {
            **make_progress_projection_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "quest_status": "running",
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-stale",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:previous",
            },
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
        }
    )

def test_flapping_recovery_probe_clears_hold_when_current_status_is_live(
    tmp_path: Path,
) -> None:
    policy = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_recovery_policy")
    study_root = tmp_path / "studies" / "001-risk"
    dump_json(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": "2026-04-26T00:01:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "status": "handoff_required",
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_runtime_read_model_retired": True,
            "mas_materializes_runtime_supervision": False,
            "health_status": "recovering",
            "runtime_stability_status": "flapping",
            "flapping_episode_count": 2,
            "flapping_circuit_breaker": True,
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
            },
        },
    )

    hold = policy.hold_for_flapping_circuit_breaker(
        study_root=study_root,
        status_payload={
            **make_progress_projection_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-recovered",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-recovered",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    )

    assert hold is not None
    assert hold["recovery_probe"] == {
        "probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::2",
        "status": "clear_hold",
        "recommended_action": "ready_to_resume",
        "reason": "runtime_liveness_confirmed_live",
        "next_probe_id": None,
        "liveness": {
            "status": "live",
            "active_run_id": "run-recovered",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
        "current_status": {
            "quest_status": "running",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_stability_status": "live",
            "flapping_circuit_breaker": False,
            "flapping_episode_count": 2,
        },
    }
