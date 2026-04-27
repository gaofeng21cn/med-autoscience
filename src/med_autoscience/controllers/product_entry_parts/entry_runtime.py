from __future__ import annotations

import hashlib
import json

from . import shared as _shared
from . import program_surfaces as _program_surfaces
from . import workspace_surfaces as _workspace_surfaces
from . import manifest_surfaces as _manifest_surfaces
from med_autoscience.study_task_intake import task_intake_overrides_auto_manual_finish

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_program_surfaces)
_module_reexport(_workspace_surfaces)
_module_reexport(_manifest_surfaces)

def build_product_entry(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    direct_entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    selected_direct_entry_mode = _require_direct_entry_mode(direct_entry_mode)
    execution = _execution_payload(study_payload, profile=profile)
    latest_task_payload = read_latest_task_intake(study_root=resolved_study_root)
    if latest_task_payload is None:
        raise ValueError("build-product-entry 需要已有 durable study task intake；请先运行 submit-study-task。")

    task_intent = _non_empty_text(latest_task_payload.get("task_intent"))
    if task_intent is None:
        raise ValueError("latest durable study task intake 缺少 task_intent。")

    managed_entry_mode = (
        _non_empty_text(latest_task_payload.get("entry_mode"))
        or _non_empty_text(execution.get("default_entry_mode"))
        or "full_research"
    )
    runtime_contract = dict(latest_task_payload.get("runtime_session_contract") or {})
    return_contract = dict(latest_task_payload.get("return_surface_contract") or {})
    mainline_snapshot = _mainline_snapshot()
    single_project_boundary = dict(mainline_snapshot.get("single_project_boundary") or {})
    capability_owner_boundary = dict(mainline_snapshot.get("capability_owner_boundary") or {})
    commands = {
        "workspace_cockpit": f"{_command_prefix(profile_ref)} workspace-cockpit --profile {_profile_arg(profile_ref)}",
        "submit_study_task": (
            f"{_command_prefix(profile_ref)} submit-study-task --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)} --task-intent '<task_intent>'"
        ),
        "launch_study": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "study_progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "study_runtime_status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
    }
    commands["workspace_cockpit"] = _json_surface_command(commands["workspace_cockpit"])
    commands["study_progress"] = _json_surface_command(commands["study_progress"])

    payload = {
        "schema_version": SCHEMA_VERSION,
        "entry_kind": PRODUCT_ENTRY_KIND,
        "target_domain_id": TARGET_DOMAIN_ID,
        "task_intent": task_intent,
        "entry_mode": selected_direct_entry_mode,
        "workspace_locator": {
            "workspace_surface_kind": "med_autoscience_study_workspace",
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "study_id": resolved_study_id,
            "study_root": str(resolved_study_root),
        },
        "runtime_session_contract": {
            "runtime_owner": "upstream_hermes_agent",
            "domain_owner": TARGET_DOMAIN_ID,
            "executor_owner": "med_deepscientist",
            "runtime_substrate": "external_hermes_agent_target",
            "managed_entry_mode": managed_entry_mode,
            "managed_runtime_backend_id": runtime_contract.get("managed_runtime_backend_id") or profile.managed_runtime_backend_id,
            "runtime_root": runtime_contract.get("runtime_root") or str(profile.runtime_root),
            "hermes_agent_repo_root": runtime_contract.get("hermes_agent_repo_root"),
            "hermes_home_root": runtime_contract.get("hermes_home_root") or str(profile.hermes_home_root),
            "start_entry": "launch-study",
            "resume_entry": "launch-study",
        },
        "managed_runtime_contract": _build_managed_runtime_contract(
            domain_owner=TARGET_DOMAIN_ID,
            executor_owner="med_deepscientist",
            supervision_status_surface="study_progress",
            attention_queue_surface="workspace_cockpit",
            recovery_contract_surface="study_runtime_status",
        ),
        "return_surface_contract": {
            "entry_adapter": SERVICE_SAFE_ENTRY_ADAPTER,
            "default_formal_entry": "CLI",
            "supported_entry_modes": list(SUPPORTED_DIRECT_ENTRY_MODES),
            "single_project_boundary": single_project_boundary,
            "capability_owner_boundary": capability_owner_boundary,
            "study_progress_projection_contract": {
                "surface_kind": "study_progress_projection_contract",
                "command": commands["study_progress"],
                "needs_physician_decision_field": "needs_physician_decision",
                "intervention_lane_field": "intervention_lane",
                "operator_status_card_field": "operator_status_card",
                "autonomy_contract_field": "autonomy_contract",
                "restore_point_field": "autonomy_contract.restore_point",
                "human_gate_required_field": "autonomy_contract.restore_point.human_gate_required",
                "recovery_contract_field": "recovery_contract",
                "continuation_state_field": "continuation_state",
                "family_checkpoint_lineage_field": "family_checkpoint_lineage",
                "autonomy_soak_status_field": "autonomy_soak_status",
                "quality_closure_truth_field": "quality_closure_truth",
                "quality_execution_lane_field": "quality_execution_lane",
                "same_line_route_truth_field": "same_line_route_truth",
                "same_line_route_surface_field": "same_line_route_surface",
                "quality_repair_batch_followthrough_field": "quality_repair_batch_followthrough",
                "quality_review_followthrough_field": "quality_review_followthrough",
                "gate_clearing_batch_followthrough_field": "gate_clearing_batch_followthrough",
                "research_runtime_control_projection_field": "research_runtime_control_projection",
                "artifact_pickup_field": "research_runtime_control_projection.artifact_pickup_surface",
                "artifact_pickup_refs_field": "research_runtime_control_projection.artifact_pickup_surface.pickup_refs",
                "runtime_human_gate_field": "research_runtime_control_projection.research_gate_surface",
            },
            "research_runtime_control_projection_contract": _build_research_runtime_control_projection(
                resume_command=commands["launch_study"],
                check_progress_command=commands["study_progress"],
                check_runtime_status_command=commands["study_runtime_status"],
                surface_kind="research_runtime_control_projection_contract",
            ),
            "domain_entry_contract": _build_domain_entry_contract(),
            "gateway_interaction_contract": _build_gateway_interaction_contract(),
            "cockpit_command": commands["workspace_cockpit"],
            "submit_task_command": commands["submit_study_task"],
            "launch_command": commands["launch_study"],
            "progress_command": commands["study_progress"],
            "runtime_status_command": commands["study_runtime_status"],
            "runtime_supervision_path": return_contract.get("runtime_supervision_path"),
            "publication_eval_path": return_contract.get("publication_eval_path"),
            "controller_decision_path": return_contract.get("controller_decision_path"),
        },
        "domain_payload": {
            "study_id": resolved_study_id,
            "journal_target": latest_task_payload.get("journal_target"),
            "evidence_boundary": list(latest_task_payload.get("evidence_boundary") or []),
            "trusted_inputs": list(latest_task_payload.get("trusted_inputs") or []),
            "reference_papers": list(latest_task_payload.get("reference_papers") or []),
            "first_cycle_outputs": list(latest_task_payload.get("first_cycle_outputs") or []),
        },
        "source_task_intake": {
            "task_id": latest_task_payload.get("task_id"),
            "emitted_at": latest_task_payload.get("emitted_at"),
        },
        "commands": commands,
    }
    _validate_domain_entry_contract_shape(
        payload["return_surface_contract"]["domain_entry_contract"],
        context="build_product_entry.return_surface_contract.domain_entry_contract",
    )
    _validate_gateway_interaction_contract_shape(
        payload["return_surface_contract"]["gateway_interaction_contract"],
        context="build_product_entry.return_surface_contract.gateway_interaction_contract",
    )
    return payload


def render_build_product_entry_markdown(payload: dict[str, Any]) -> str:
    commands = dict(payload.get("commands") or {})
    return_surface_contract = dict(payload.get("return_surface_contract") or {})
    capability_owner_boundary = dict(return_surface_contract.get("capability_owner_boundary") or {})
    proof_boundary = dict(capability_owner_boundary.get("proof_and_absorb_boundary") or {})
    domain_payload = dict(payload.get("domain_payload") or {})
    lines = [
        "# Build Product Entry",
        "",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- 当前入口模式: {_direct_entry_mode_label(payload.get('entry_mode'))}",
        f"- 当前任务意图: {payload.get('task_intent')}",
        f"- 当前 study: `{domain_payload.get('study_id') or 'unknown'}`",
        f"- 当前投稿目标: {domain_payload.get('journal_target') or 'none'}",
        "",
        "## Commands",
        "",
    ]
    for name, command in commands.items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(
        [
            "",
            "## Return Surface",
            "",
            f"- 单项目边界摘要: `{((return_surface_contract.get('single_project_boundary') or {}).get('summary') or 'none')}`",
            f"- 能力 owner: `{capability_owner_boundary.get('owner') or 'none'}`",
            f"- physical absorb: `{proof_boundary.get('physical_absorb_status') or 'none'}`",
            f"- 进度真相命令: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('command') or 'none')}`",
            f"- 自治 proof 字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('autonomy_soak_status_field') or 'none')}`",
            f"- 质量执行线字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('quality_execution_lane_field') or 'none')}`",
            f"- 同线路由真相字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('same_line_route_truth_field') or 'none')}`",
            f"- quality-repair 跟进字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('quality_repair_batch_followthrough_field') or 'none')}`",
            f"- 质量复评跟进字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('quality_review_followthrough_field') or 'none')}`",
            f"- gate-clearing 跟进字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('gate_clearing_batch_followthrough_field') or 'none')}`",
            f"- runtime control projection 字段: `{((return_surface_contract.get('study_progress_projection_contract') or {}).get('research_runtime_control_projection_field') or 'none')}`",
            f"- 运行监管路径: `{return_surface_contract.get('runtime_supervision_path') or 'none'}`",
            f"- 发表评估路径: `{return_surface_contract.get('publication_eval_path') or 'none'}`",
            f"- 控制器决策路径: `{return_surface_contract.get('controller_decision_path') or 'none'}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_live_task_intake_runtime_message(payload: dict[str, Any]) -> str:
    return (
        "MAS managed task update. Prioritize this latest study task over stale background plans.\n\n"
        f"{render_task_intake_runtime_context(payload)}\n\n"
        "After absorbing this task, report the concrete next action through artifact.interact(...)."
    )


def _task_intake_delivery_fingerprint(payload: Mapping[str, Any]) -> str:
    canonical_payload = {
        "study_id": _non_empty_text(payload.get("study_id")),
        "entry_mode": _non_empty_text(payload.get("entry_mode")) or "full_research",
        "task_intent": _non_empty_text(payload.get("task_intent")) or "",
        "journal_target": _non_empty_text(payload.get("journal_target")),
        "constraints": list(_normalized_strings(payload.get("constraints") or [])),
        "evidence_boundary": list(_normalized_strings(payload.get("evidence_boundary") or [])),
        "trusted_inputs": list(_normalized_strings(payload.get("trusted_inputs") or [])),
        "reference_papers": list(_normalized_strings(payload.get("reference_papers") or [])),
        "first_cycle_outputs": list(_normalized_strings(payload.get("first_cycle_outputs") or [])),
        "revision_intake_kind": _non_empty_text(dict(payload.get("revision_intake") or {}).get("kind"))
        if isinstance(payload.get("revision_intake"), Mapping)
        else None,
    }
    encoded = json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return f"study-task-intake:{hashlib.sha256(encoded).hexdigest()}"


def _runtime_message_id(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    nested_message = payload.get("message")
    if isinstance(nested_message, Mapping):
        message_id = _non_empty_text(nested_message.get("id")) or _non_empty_text(nested_message.get("message_id"))
        if message_id is not None:
            return message_id
    return _non_empty_text(payload.get("message_id")) or _non_empty_text(payload.get("id"))


def _task_intake_delivery_for_current_run(
    *,
    runtime_state: Mapping[str, Any],
    fingerprint: str,
) -> Mapping[str, Any] | None:
    delivery = runtime_state.get("last_task_intake_delivery")
    if not isinstance(delivery, Mapping):
        return None
    if delivery.get("fingerprint") != fingerprint:
        return None
    current_active_run_id = _non_empty_text(runtime_state.get("active_run_id"))
    delivered_active_run_id = _non_empty_text(delivery.get("active_run_id"))
    if current_active_run_id is not None and delivered_active_run_id != current_active_run_id:
        return None
    return delivery


def _write_task_intake_delivery_record(
    *,
    quest_root: Path,
    runtime_state: Mapping[str, Any],
    fingerprint: str,
    delivery_mode: str,
    message_id: str | None,
    source: str,
) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    latest_runtime_state = quest_state.load_runtime_state(quest_root)
    merged_state = dict(latest_runtime_state or runtime_state)
    merged_state["last_task_intake_delivery"] = {
        "fingerprint": fingerprint,
        "active_run_id": _non_empty_text(merged_state.get("active_run_id")),
        "delivery_mode": delivery_mode,
        "message_id": message_id,
        "source": source,
    }
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(json.dumps(merged_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _study_reactivation_command(
    *,
    profile_ref: str | Path | None,
    study_id: str,
    stopped_relaunch: bool,
) -> str:
    command = (
        f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
        f"{_study_selector(study_id=study_id)}"
    )
    if stopped_relaunch:
        command = f"{command} --allow-stopped-relaunch"
    return _json_surface_command(command)


def _apply_revision_reactivation_guidance(
    *,
    result: dict[str, Any],
    payload: dict[str, Any],
    profile_ref: str | Path | None,
    study_id: str,
) -> None:
    result["requires_study_reactivation"] = False
    result["next_required_action"] = None
    result["recommended_next_command"] = None
    result["current_package_edit_policy"] = None
    if not task_intake_overrides_auto_manual_finish(payload):
        return
    quest_status = str(result.get("quest_status") or "").strip().lower()
    stopped_relaunch = quest_status == "stopped"
    result["requires_study_reactivation"] = True
    result["next_required_action"] = (
        "launch_study_with_stopped_relaunch" if stopped_relaunch else "launch_study_or_resume"
    )
    result["recommended_next_command"] = _study_reactivation_command(
        profile_ref=profile_ref,
        study_id=study_id,
        stopped_relaunch=stopped_relaunch,
    )
    result["current_package_edit_policy"] = {
        "surface_kind": "human_facing_projection",
        "direct_current_package_edit_allowed": False,
        "reason": (
            "reviewer_revision_reactivates_same_study_line; "
            "manuscript/current_package must be regenerated from controller-authorized paper authority"
        ),
    }
    result["reason"] = (
        "stopped_revision_requires_study_reactivation"
        if stopped_relaunch
        else "non_live_revision_requires_study_reactivation"
    )


def _enqueue_task_intake_for_live_runtime(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str,
    execution: Mapping[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    layout = build_workspace_runtime_layout_for_profile(profile)
    managed_quest_id = _non_empty_text((execution or {}).get("quest_id")) or study_id
    quest_root = layout.quest_root(managed_quest_id)
    runtime_message = _build_live_task_intake_runtime_message(payload)
    result: dict[str, Any] = {
        "quest_root": str(quest_root),
        "quest_id": managed_quest_id,
        "quest_status": None,
        "intervention_enqueued": False,
        "message_id": None,
        "reason": None,
        "delivery_mode": None,
        "runtime_backend_id": None,
        "backend_submit_error": None,
        "requires_study_reactivation": False,
        "next_required_action": None,
        "recommended_next_command": None,
        "current_package_edit_policy": None,
    }
    if not (quest_root / "quest.yaml").exists():
        result["reason"] = "quest_not_found"
        _apply_revision_reactivation_guidance(
            result=result,
            payload=payload,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        return result

    runtime_state = quest_state.load_runtime_state(quest_root)
    quest_status = str(runtime_state.get("status") or "").strip().lower()
    result["quest_status"] = quest_status or None
    if quest_status not in _LIVE_TASK_INTAKE_RUNTIME_STATUSES:
        result["reason"] = "quest_not_live"
        _apply_revision_reactivation_guidance(
            result=result,
            payload=payload,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        return result

    runtime_state["quest_id"] = managed_quest_id
    fingerprint = _task_intake_delivery_fingerprint(payload)
    existing_delivery = _task_intake_delivery_for_current_run(
        runtime_state=runtime_state,
        fingerprint=fingerprint,
    )
    if existing_delivery is not None:
        result["intervention_enqueued"] = True
        result["delivery_mode"] = _non_empty_text(existing_delivery.get("delivery_mode"))
        result["message_id"] = _non_empty_text(existing_delivery.get("message_id"))
        result["reason"] = "live_runtime_task_context_already_delivered"
        result["idempotent_replay"] = True
        return result

    backend = runtime_backend_contract.resolve_managed_runtime_backend(execution)
    if backend is not None:
        result["runtime_backend_id"] = backend.BACKEND_ID
        try:
            response = backend.chat_quest(
                runtime_root=layout.runtime_root,
                quest_id=managed_quest_id,
                text=runtime_message,
                source="codex-study-task-intake",
            )
        except Exception as exc:
            result["backend_submit_error"] = str(exc)
        else:
            result["intervention_enqueued"] = True
            result["delivery_mode"] = "managed_runtime_chat"
            result["message_id"] = _runtime_message_id(response)
            result["reason"] = "live_runtime_task_context_submitted"
            result["idempotent_replay"] = False
            _write_task_intake_delivery_record(
                quest_root=quest_root,
                runtime_state=runtime_state,
                fingerprint=fingerprint,
                delivery_mode="managed_runtime_chat",
                message_id=result["message_id"],
                source="codex-study-task-intake",
            )
            return result

    record = user_message.enqueue_user_message(
        quest_root=quest_root,
        runtime_state=runtime_state,
        message=runtime_message,
        source="codex-study-task-intake",
        dedupe_key=fingerprint,
    )
    result["intervention_enqueued"] = True
    result["delivery_mode"] = "durable_queue_fallback"
    result["message_id"] = record.get("message_id")
    result["reason"] = "live_runtime_task_context_enqueued_fallback"
    result["idempotent_replay"] = False
    _write_task_intake_delivery_record(
        quest_root=quest_root,
        runtime_state=runtime_state,
        fingerprint=fingerprint,
        delivery_mode="durable_queue_fallback",
        message_id=_non_empty_text(record.get("message_id")),
        source="codex-study-task-intake",
    )
    return result


def submit_study_task(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    task_intent: str,
    entry_mode: str | None = None,
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    execution = _execution_payload(study_payload, profile=profile)
    selected_entry_mode = _non_empty_text(entry_mode) or _non_empty_text(execution.get("default_entry_mode")) or "full_research"
    payload = write_task_intake(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        entry_mode=selected_entry_mode,
        task_intent=task_intent,
        journal_target=journal_target,
        constraints=_normalized_strings(constraints),
        evidence_boundary=_normalized_strings(evidence_boundary),
        trusted_inputs=_normalized_strings(trusted_inputs),
        reference_papers=_normalized_strings(reference_papers),
        first_cycle_outputs=_normalized_strings(first_cycle_outputs),
    )
    layout = build_workspace_runtime_layout_for_profile(profile)
    startup_brief_path = layout.startup_brief_path(resolved_study_id)
    startup_brief_payload = study_payload.get("startup_brief")
    if isinstance(startup_brief_payload, str) and startup_brief_payload.strip():
        candidate = Path(startup_brief_payload).expanduser()
        startup_brief_path = (
            candidate.resolve()
            if candidate.is_absolute()
            else (resolved_study_root / candidate).resolve()
        )
    existing_text = startup_brief_path.read_text(encoding="utf-8") if startup_brief_path.exists() else ""
    updated_text = upsert_startup_brief_task_block(existing_text=existing_text, payload=payload)
    startup_brief_path.parent.mkdir(parents=True, exist_ok=True)
    startup_brief_path.write_text(updated_text, encoding="utf-8")
    latest_payload = read_latest_task_intake(study_root=resolved_study_root) or payload
    runtime_intervention = _enqueue_task_intake_for_live_runtime(
        profile=profile,
        profile_ref=profile_ref,
        study_id=resolved_study_id,
        execution=execution,
        payload=latest_payload,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "task_id": latest_payload.get("task_id"),
        "entry_mode": latest_payload.get("entry_mode"),
        "task_intent": latest_payload.get("task_intent"),
        "journal_target": latest_payload.get("journal_target"),
        "constraints": list(latest_payload.get("constraints") or []),
        "evidence_boundary": list(latest_payload.get("evidence_boundary") or []),
        "trusted_inputs": list(latest_payload.get("trusted_inputs") or []),
        "reference_papers": list(latest_payload.get("reference_papers") or []),
        "first_cycle_outputs": list(latest_payload.get("first_cycle_outputs") or []),
        "revision_intake": latest_payload.get("revision_intake"),
        "startup_brief_path": str(startup_brief_path),
        "artifacts": dict(payload.get("artifact_refs") or {}),
        "runtime_intervention": runtime_intervention,
    }


def render_submit_study_task_markdown(payload: dict[str, Any]) -> str:
    lines = render_task_intake_markdown(
        {
            "study_id": payload.get("study_id"),
            "emitted_at": _utc_now(),
            "entry_mode": payload.get("entry_mode"),
            "journal_target": payload.get("journal_target"),
            "task_intent": payload.get("task_intent"),
            "constraints": payload.get("constraints") or [],
            "evidence_boundary": payload.get("evidence_boundary") or [],
            "trusted_inputs": payload.get("trusted_inputs") or [],
            "reference_papers": payload.get("reference_papers") or [],
            "first_cycle_outputs": payload.get("first_cycle_outputs") or [],
        }
    ).rstrip("\n")
    lines += (
        "\n\n## Synced Surfaces\n\n"
        f"- startup_brief_path: `{payload.get('startup_brief_path')}`\n"
        f"- latest_json: `{((payload.get('artifacts') or {}).get('latest_json') or 'none')}`\n"
        f"- latest_markdown: `{((payload.get('artifacts') or {}).get('latest_markdown') or 'none')}`\n"
    )
    runtime_intervention = dict(payload.get("runtime_intervention") or {})
    if runtime_intervention.get("requires_study_reactivation") is True:
        lines += (
            "\n## Runtime Reactivation\n\n"
            "- 当前 runtime 不在可接收 live intervention 状态；本次 revision 已写入 durable intake，但还必须重新激活同一 study。\n"
            f"- 推荐命令: `{runtime_intervention.get('recommended_next_command') or 'none'}`\n"
            "- 在 MAS/MDS 接管 canonical paper surface 前，不要把直接改 `manuscript/current_package/` 当作完成态。\n"
        )
    return lines
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
