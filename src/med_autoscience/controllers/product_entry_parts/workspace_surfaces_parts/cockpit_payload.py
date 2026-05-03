def _study_item(
    *,
    progress_payload: dict[str, Any],
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    study_id = str(progress_payload.get("study_id") or "").strip()
    commands = {
        "launch": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
    }
    supervision = dict(progress_payload.get("supervision") or {})
    monitoring = {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    intervention_lane = dict(progress_payload.get("intervention_lane") or {})
    operator_verdict = dict(progress_payload.get("operator_verdict") or {})
    operator_status_card = dict(progress_payload.get("operator_status_card") or {})
    auto_runtime_parked = dict(progress_payload.get("auto_runtime_parked") or {})
    recommended_command = _non_empty_text(progress_payload.get("recommended_command"))
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    autonomy_contract = dict(progress_payload.get("autonomy_contract") or {})
    autonomy_soak_status = dict(progress_payload.get("autonomy_soak_status") or {})
    quality_closure_truth = dict(progress_payload.get("quality_closure_truth") or {})
    quality_execution_lane = dict(progress_payload.get("quality_execution_lane") or {})
    same_line_route_truth = _same_line_route_truth_payload(progress_payload)
    same_line_route_surface = dict(progress_payload.get("same_line_route_surface") or {})
    quality_review_loop = dict(progress_payload.get("quality_review_loop") or {})
    quality_repair_followthrough = dict(progress_payload.get("quality_repair_batch_followthrough") or {})
    quality_review_followthrough = dict(progress_payload.get("quality_review_followthrough") or {})
    gate_clearing_followthrough = _normalized_gate_clearing_followthrough(
        progress_payload,
        fallback_command=commands["progress"],
    )
    ai_first_default_entry_state = dict(progress_payload.get("ai_first_default_entry_state") or {})
    ai_first_operations_dashboard = dict(progress_payload.get("ai_first_operations_dashboard") or {})
    ai_first_feedback_state = dict(progress_payload.get("ai_first_feedback_state") or {})
    ai_first_action_dispatch_lifecycle = dict(
        progress_payload.get("ai_first_action_dispatch_lifecycle") or {}
    )
    dispatch_ledger = dict(progress_payload.get("dispatch_ledger") or {})
    publication_eval = dict(progress_payload.get("publication_eval") or {})
    paper_orchestra_operator_projection = dict(progress_payload.get("paper_orchestra_operator_projection") or {})
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    study_truth_snapshot = _truth_snapshot_summary(progress_payload.get("study_truth_snapshot"))
    runtime_health_snapshot = _runtime_health_snapshot_summary(progress_payload.get("runtime_health_snapshot"))
    control_plane_snapshot = _control_plane_snapshot_summary(progress_payload.get("control_plane_snapshot"))
    research_runtime_control_projection = dict(progress_payload.get("research_runtime_control_projection") or {})
    gate_surface = dict(research_runtime_control_projection.get("research_gate_surface") or {})
    if gate_surface.get("approval_gate_field") == "needs_user_decision":
        gate_surface.setdefault("legacy_approval_gate_field", "needs_physician_decision")
        research_runtime_control_projection["research_gate_surface"] = gate_surface
    return {
        "study_id": study_id,
        "truth_epoch": _non_empty_text(progress_payload.get("truth_epoch"))
        or _non_empty_text((study_truth_snapshot or {}).get("truth_epoch")),
        "study_truth_snapshot": study_truth_snapshot,
        "runtime_health_epoch": _non_empty_text(progress_payload.get("runtime_health_epoch"))
        or _non_empty_text((runtime_health_snapshot or {}).get("runtime_health_epoch")),
        "runtime_health_snapshot": runtime_health_snapshot,
        "control_plane_snapshot": control_plane_snapshot,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "operator_status_card": operator_status_card or None,
        "auto_runtime_parked": auto_runtime_parked or None,
        "parked_state": progress_payload.get("parked_state"),
        "parked_owner": progress_payload.get("parked_owner"),
        "external_owner": progress_payload.get("external_owner"),
        "external_runtime_owner": progress_payload.get("external_runtime_owner"),
        "resource_release_expected": progress_payload.get("resource_release_expected"),
        "awaiting_explicit_wakeup": progress_payload.get("awaiting_explicit_wakeup"),
        "auto_execution_complete": progress_payload.get("auto_execution_complete"),
        "reopen_policy": progress_payload.get("reopen_policy"),
        "legacy_current_stage": progress_payload.get("legacy_current_stage"),
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract or None,
        "autonomy_soak_status": autonomy_soak_status or None,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_review_loop": quality_review_loop or None,
        "quality_repair_followthrough": quality_repair_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
        "gate_clearing_followthrough": gate_clearing_followthrough or None,
        "ai_first_default_entry_state": ai_first_default_entry_state or None,
        "ai_first_operations_dashboard": ai_first_operations_dashboard or None,
        "ai_first_feedback_state": ai_first_feedback_state or None,
        "ai_first_action_dispatch_lifecycle": ai_first_action_dispatch_lifecycle or None,
        "dispatch_ledger": dispatch_ledger or None,
        "publication_eval": publication_eval or None,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "research_runtime_control_projection": research_runtime_control_projection or None,
        "recovery_contract": recovery_contract or None,
        "needs_physician_decision": bool(progress_payload.get("needs_physician_decision")),
        "needs_user_decision": bool(progress_payload.get("needs_user_decision")),
        "monitoring": monitoring,
        "task_intake": task_intake or None,
        "progress_freshness": progress_freshness or None,
        "commands": commands,
    }


def _truth_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "truth_epoch",
        "authority_epoch",
        "canonical_next_action",
        "blocking_reasons",
        "dominant_authority_refs",
        "allowed_controller_actions",
        "package_state",
        "writer_epoch",
        "source_signature",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _runtime_health_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "runtime_health_epoch",
        "canonical_runtime_action",
        "attempt_state",
        "retry_budget_remaining",
        "worker_liveness_state",
        "supervisor_state",
        "dominant_runtime_refs",
        "blocking_reasons",
        "allowed_controller_actions",
        "source_signature",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _control_plane_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "control_state",
        "canonical_next_action",
        "canonical_runtime_action",
        "dispatch_gate",
        "route_authorization",
        "blocking_reasons",
        "allowed_controller_actions",
        "authority_refs",
        "quality_gate_relaxation_allowed",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.exists():
        return []
    return [
        study_root
        for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir())
        if (study_root / "study.yaml").exists()
    ]


def _workspace_cockpit_study_snapshot(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
) -> tuple[dict[str, Any], list[str]]:
    progress_payload = study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    item = _study_item(progress_payload=progress_payload, profile_ref=profile_ref)
    alerts = list(item["current_blockers"])
    progress_freshness = dict(item.get("progress_freshness") or {})
    progress_summary = _non_empty_text(progress_freshness.get("summary"))
    if _non_empty_text(progress_freshness.get("status")) in {"stale", "missing"} and progress_summary is not None:
        alerts.append(progress_summary)
    return item, alerts


def read_workspace_cockpit(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    inspect_workspace_supervision = _controller_override("_inspect_workspace_supervision", _inspect_workspace_supervision)
    doctor_report = build_doctor_report_fn(profile)
    workspace_alerts = _workspace_ready_alerts(doctor_report)
    studies: list[dict[str, Any]] = []
    study_roots = _study_roots(profile)
    if study_roots:
        with ThreadPoolExecutor(max_workers=len(study_roots)) as executor:
            futures = [
                executor.submit(
                    _workspace_cockpit_study_snapshot,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_root=study_root,
                )
                for study_root in study_roots
            ]
            for future in futures:
                item, item_alerts = future.result()
                studies.append(item)
                for alert in item_alerts:
                    if alert not in workspace_alerts:
                        workspace_alerts.append(alert)
    service = inspect_workspace_supervision(profile)
    workspace_supervision = _workspace_supervision_summary(studies=studies, service=service)
    if (
        (not bool(service.get("loaded")) or bool(service.get("drift_reasons")))
        and service.get("summary") not in workspace_alerts
    ):
        workspace_alerts.append(str(service.get("summary")))
    baseline_alerts = _workspace_ready_alerts(doctor_report)
    if workspace_alerts and not baseline_alerts:
        workspace_status = "attention_required"
    elif baseline_alerts:
        workspace_status = "blocked"
    else:
        workspace_status = "ready"
    mainline_snapshot = _mainline_snapshot()
    commands = {
        "mainline_status": f"{_command_prefix(profile_ref)} mainline-status",
        "doctor": f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}",
        "bootstrap": f"{_command_prefix(profile_ref)} bootstrap --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
        "service_install": f"{_command_prefix(profile_ref)} runtime-ensure-supervision --profile {_profile_arg(profile_ref)}",
        "service_status": f"{_command_prefix(profile_ref)} runtime-supervision-status --profile {_profile_arg(profile_ref)}",
    }
    attention_queue = _attention_queue(
        workspace_status=workspace_status,
        workspace_supervision=workspace_supervision,
        studies=studies,
        commands=commands,
    )
    ai_first_operations_state = _workspace_ai_first_operations_state(studies=studies)
    ai_first_cross_study_completion_projection = _workspace_ai_first_cross_study_completion_projection(
        study_roots=study_roots,
        studies=studies,
    )
    paper_orchestra_operator_projection = build_workspace_paper_orchestra_operator_projection(studies=studies)
    user_loop = _user_loop(profile=profile, profile_ref=profile_ref)
    operator_brief = _workspace_operator_brief(
        workspace_status=workspace_status,
        workspace_alerts=workspace_alerts,
        attention_queue=attention_queue,
        studies=studies,
        user_loop=user_loop,
        commands=commands,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "workspace_status": workspace_status,
        "mainline_snapshot": mainline_snapshot,
        "workspace_alerts": workspace_alerts,
        "workspace_supervision": workspace_supervision,
        "ai_first_operations_state": ai_first_operations_state,
        "ai_first_cross_study_completion_projection": ai_first_cross_study_completion_projection,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection,
        "attention_queue": attention_queue,
        "operator_brief": operator_brief,
        "user_loop": user_loop,
        "phase2_user_product_loop": phase2_user_product_loop,
        "studies": studies,
        "commands": commands,
    }
