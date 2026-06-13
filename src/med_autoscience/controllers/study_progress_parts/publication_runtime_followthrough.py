from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)

def _quality_review_followthrough_projection(
    *,
    quality_review_loop: Mapping[str, Any],
    needs_physician_decision: bool,
    interaction_arbitration: Mapping[str, Any],
    runtime_decision: str | None,
    quest_status: str | None,
    current_blockers: list[str],
    next_system_action: str,
) -> dict[str, Any] | None:
    if not quality_review_loop:
        return None
    waiting_auto_re_review = bool(quality_review_loop.get("re_review_ready")) or _non_empty_text(
        quality_review_loop.get("current_phase")
    ) == "re_review_required"
    if not waiting_auto_re_review:
        return {
            "surface_kind": "quality_review_followthrough",
            "state": "not_in_re_review_waiting",
            "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["not_in_re_review_waiting"],
            "waiting_auto_re_review": False,
            "auto_continue_expected": False,
            "summary": "当前质量闭环不在自动复评等待态，系统会按现有修订线继续推进。",
            "blocking_reason": None,
            "next_confirmation_signal": "看下一次质量评审结论是否继续收窄当前修订线。",
            "user_intervention_required_now": False,
        }

    requires_user_input = needs_physician_decision or bool(interaction_arbitration.get("requires_user_input"))
    runtime_active = quest_status in {"running", "active", "waiting_for_user"}
    runtime_recovery_requested = runtime_decision in {"create_and_start", "resume", "relaunch_stopped"}
    runtime_blocks_auto = runtime_decision in {"blocked", "completed", "create_only"}
    auto_continue_expected = (runtime_active or runtime_recovery_requested) and not runtime_blocks_auto and not requires_user_input
    if auto_continue_expected:
        return {
            "surface_kind": "quality_review_followthrough",
            "state": "auto_re_review_pending",
            "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["auto_re_review_pending"],
            "waiting_auto_re_review": True,
            "auto_continue_expected": True,
            "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
            "blocking_reason": None,
            "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            "user_intervention_required_now": False,
        }

    if requires_user_input:
        blocking_reason = "当前需要用户先确认下一步，系统不会直接自动复评。"
    elif runtime_decision == "blocked":
        blocking_reason = "当前运行被控制面阻断，需先解除阻断后才会继续复评。"
    elif quest_status in {"stopped", "failed", "completed"}:
        blocking_reason = "当前运行不在自动推进状态，需要先恢复运行后才会继续复评。"
    else:
        blocking_reason = _non_empty_text(current_blockers[0] if current_blockers else None) or next_system_action
    return {
        "surface_kind": "quality_review_followthrough",
        "state": "auto_re_review_blocked",
        "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["auto_re_review_blocked"],
        "waiting_auto_re_review": True,
        "auto_continue_expected": False,
        "summary": "当前停在等待复评，系统暂时不会自动继续。",
        "blocking_reason": blocking_reason,
        "next_confirmation_signal": "先解除当前卡点，再看 publication_eval/latest.json 是否出现新的复评结论。",
        "user_intervention_required_now": True,
    }


def _apply_quality_review_followthrough_to_operator_status(
    *,
    operator_status_card: Mapping[str, Any],
    followthrough: Mapping[str, Any] | None,
) -> dict[str, Any]:
    card = dict(operator_status_card or {})
    follow = dict(followthrough or {})
    if not card or not follow or not bool(follow.get("waiting_auto_re_review")):
        return card
    if _non_empty_text(card.get("handling_state")) in {"runtime_recovering", "publication_gate_specificity_required"}:
        return card
    card["quality_review_followthrough"] = follow
    card["current_focus"] = _non_empty_text(follow.get("summary")) or card.get("current_focus")
    next_signal = _non_empty_text(follow.get("next_confirmation_signal"))
    if next_signal is not None:
        card["next_confirmation_signal"] = next_signal
    intervention_required = bool(follow.get("user_intervention_required_now"))
    card["user_intervention_required_now"] = intervention_required
    if intervention_required:
        card["user_visible_verdict"] = "当前停在等待复评，系统不会自动继续；你现在需要先处理卡点。"
    else:
        card["user_visible_verdict"] = "当前在等系统自动复评；你现在不用介入，先等待复评回写。"
    return card


def _gate_clearing_batch_followthrough(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
    current_eval_ids: object = None,
) -> dict[str, Any] | None:
    record_path = gate_clearing_batch.stable_gate_clearing_batch_path(study_root=study_root)
    record = _read_json_object(record_path)
    if record is None:
        return None
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    accepted_eval_ids = _gate_clearing_current_eval_ids(
        current_eval_id,
        current_eval_ids,
    )
    source_eval_id = _non_empty_text(record.get("source_eval_id"))
    if source_eval_id is None:
        return None
    if (
        source_eval_id not in accepted_eval_ids
        and not _gate_clearing_actionable_route_back_record(record)
        and not _gate_clearing_record_matches_current_publication_blocker(
            record,
            publication_eval_payload or {},
        )
    ):
        return None
    unit_results = [
        dict(item)
        for item in (record.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    failed_units = [item for item in unit_results if _non_empty_text(item.get("status")) == "failed"]
    gate_replay = dict(record.get("gate_replay") or {})
    gate_replay_status = _non_empty_text(gate_replay.get("status")) or "unknown"
    if failed_units:
        summary = "最近一轮 gate-clearing batch 已执行，但仍有修复单元失败，当前不能继续自动前推。"
        next_confirmation_signal = "先修掉失败 repair unit，再看 publication_eval/latest.json 是否进入新的复评或放行结论。"
        user_intervention_required_now = True
    elif gate_replay_status == "clear":
        summary = "最近一轮 gate-clearing batch 已执行，并已把发表门控回放到放行状态。"
        next_confirmation_signal = "看 publication_eval/latest.json 是否刷新为新的放行结论，并确认当前 study 已进入下一阶段。"
        user_intervention_required_now = False
    else:
        blockers = [
            _non_empty_text(item)
            for item in (gate_replay.get("blockers") or [])
            if _non_empty_text(item) is not None
        ]
        blocker_summary = f"当前仍剩 {len(blockers)} 个 gate blocker。" if blockers else "当前 gate replay 仍未完全收口。"
        summary = f"最近一轮 gate-clearing batch 已执行；{blocker_summary}"
        next_confirmation_signal = "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。"
        user_intervention_required_now = False
    result = {
        "surface_kind": "gate_clearing_batch_followthrough",
        "status": _non_empty_text(record.get("status")) or "executed",
        "summary": summary,
        "gate_replay_status": gate_replay_status,
        "blocking_issue_count": len(gate_replay.get("blockers") or []),
        "gate_replay_blockers": [
            blocker
            for item in (gate_replay.get("blockers") or [])
            if (blocker := _non_empty_text(item)) is not None
        ],
        "failed_unit_count": len(failed_units),
        "next_confirmation_signal": next_confirmation_signal,
        "user_intervention_required_now": user_intervention_required_now,
        "latest_record_path": str(record_path),
    }
    identity = {
        "source_eval_id": source_eval_id,
        "work_unit_id": _non_empty_text(record.get("work_unit_id"))
        or _non_empty_text(record.get("source_work_unit_id"))
        or _non_empty_text(dict(record.get("work_unit_currentness") or {}).get("explicit_publication_work_unit_id"))
        or _non_empty_text(dict(record.get("explicit_publication_work_unit") or {}).get("unit_id")),
        "work_unit_fingerprint": _non_empty_text(record.get("work_unit_fingerprint"))
        or _non_empty_text(record.get("source_work_unit_fingerprint"))
        or _non_empty_text(dict(record.get("work_unit_currentness") or {}).get("explicit_work_unit_fingerprint"))
        or _non_empty_text(dict(record.get("explicit_publication_work_unit") or {}).get("fingerprint")),
        "owner_route_currentness_basis": dict(record.get("owner_route_currentness_basis") or {}) or None,
        "work_unit_currentness": dict(record.get("work_unit_currentness") or {}) or None,
        "explicit_publication_work_unit": dict(record.get("explicit_publication_work_unit") or {}) or None,
        "current_publication_work_unit": dict(record.get("current_publication_work_unit") or {}) or None,
    }
    if any(value for key, value in identity.items() if key != "source_eval_id"):
        for key, value in identity.items():
            if value:
                result[key] = value
    return result


def _gate_clearing_actionable_route_back_record(record: Mapping[str, Any]) -> bool:
    currentness = dict(record.get("work_unit_currentness") or {})
    if _non_empty_text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    current_work_unit = _non_empty_text(
        currentness.get("current_publication_work_unit_id")
    ) or _non_empty_text(dict(record.get("current_publication_work_unit") or {}).get("unit_id"))
    explicit_work_unit = _non_empty_text(
        currentness.get("explicit_publication_work_unit_id")
    ) or _non_empty_text(dict(record.get("explicit_publication_work_unit") or {}).get("unit_id"))
    return current_work_unit is not None and current_work_unit != explicit_work_unit


def _gate_clearing_record_matches_current_publication_blocker(
    record: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    currentness = dict(record.get("work_unit_currentness") or {})
    if _non_empty_text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    current_work_unit = _non_empty_text(
        currentness.get("current_publication_work_unit_id")
    ) or _non_empty_text(dict(record.get("current_publication_work_unit") or {}).get("unit_id"))
    selected_work_unit = _non_empty_text(
        currentness.get("selected_publication_work_unit_id")
    ) or _non_empty_text(dict(record.get("selected_publication_work_unit") or {}).get("unit_id"))
    if current_work_unit is None:
        return False
    record_fingerprints = {
        text
        for value in (
            record.get("work_unit_fingerprint"),
            record.get("source_work_unit_fingerprint"),
            currentness.get("current_work_unit_fingerprint"),
            currentness.get("explicit_work_unit_fingerprint"),
        )
        if (text := _non_empty_text(value)) is not None
    }
    if not record_fingerprints:
        return False
    for action in publication_eval_payload.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint"))
        if action_fingerprint not in record_fingerprints:
            continue
        action_work_unit = _publication_eval_action_work_unit(action)
        if action_work_unit == current_work_unit or (
            selected_work_unit is not None and action_work_unit == selected_work_unit
        ):
            return True
        for work_unit in action.get("blocking_work_units") or []:
            if not isinstance(work_unit, Mapping):
                continue
            if _non_empty_text(work_unit.get("unit_id")) == current_work_unit:
                return True
    return False


def _publication_eval_action_work_unit(action: Mapping[str, Any]) -> str | None:
    next_work_unit = action.get("next_work_unit")
    if isinstance(next_work_unit, Mapping):
        text = _non_empty_text(next_work_unit.get("unit_id"))
        if text is not None:
            return text
    return _non_empty_text(action.get("work_unit_id"))


def _gate_clearing_current_eval_ids(
    publication_eval_id: str | None,
    current_eval_ids: object,
) -> set[str]:
    accepted: set[str] = set()
    if publication_eval_id is not None:
        accepted.add(publication_eval_id)
    if isinstance(current_eval_ids, str):
        text = _non_empty_text(current_eval_ids)
        if text is not None:
            accepted.add(text)
        return accepted
    if isinstance(current_eval_ids, Mapping):
        for key in ("eval_id", "source_eval_id"):
            text = _non_empty_text(current_eval_ids.get(key))
            if text is not None:
                accepted.add(text)
        return accepted
    if isinstance(current_eval_ids, (list, tuple, set, frozenset)):
        for item in current_eval_ids:
            text = _non_empty_text(item)
            if text is not None:
                accepted.add(text)
    return accepted


def _quality_repair_batch_followthrough(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
    recommended_command: str | None,
) -> dict[str, Any] | None:
    record_path = quality_repair_batch.stable_quality_repair_batch_path(study_root=study_root)
    record = _read_json_object(record_path)
    if record is None:
        return None
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    source_eval_id = _non_empty_text(record.get("source_eval_id"))
    if current_eval_id is None or source_eval_id is None or current_eval_id != source_eval_id:
        return None
    gate_batch = dict(record.get("gate_clearing_batch") or {})
    unit_results = [
        dict(item)
        for item in (gate_batch.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    failed_units = [item for item in unit_results if _non_empty_text(item.get("status")) == "failed"]
    gate_replay = dict(gate_batch.get("gate_replay") or {})
    gate_replay_status = _non_empty_text(gate_replay.get("status")) or "unknown"
    if failed_units:
        summary = "最近一轮 quality-repair batch 已执行，但仍有修复单元失败，当前不能继续自动前推。"
        next_confirmation_signal = "先修掉失败 repair unit，再看 publication_eval/latest.json 是否进入新的复评或放行结论。"
        user_intervention_required_now = True
    elif gate_replay_status == "clear":
        summary = "最近一轮 quality-repair batch 已执行，并已把 quality gate replay 到放行状态。"
        next_confirmation_signal = "看 publication_eval/latest.json 是否刷新为新的放行结论，并确认当前 study 已进入下一阶段。"
        user_intervention_required_now = False
    else:
        blockers = [
            _non_empty_text(item)
            for item in (gate_replay.get("blockers") or [])
            if _non_empty_text(item) is not None
        ]
        blocker_summary = f"当前 gate replay 仍剩 {len(blockers)} 个 blocker。" if blockers else "当前 quality gate replay 仍未完全收口。"
        summary = f"最近一轮 quality-repair batch 已执行；{blocker_summary}"
        next_confirmation_signal = "看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。"
        user_intervention_required_now = False
    payload = {
        "surface_kind": "quality_repair_batch_followthrough",
        "status": _non_empty_text(record.get("status")) or "executed",
        "quality_closure_state": _non_empty_text(record.get("quality_closure_state")),
        "quality_execution_lane_id": _non_empty_text(record.get("quality_execution_lane_id")),
        "summary": summary,
        "gate_replay_status": gate_replay_status,
        "blocking_issue_count": len(gate_replay.get("blockers") or []),
        "failed_unit_count": len(failed_units),
        "next_confirmation_signal": next_confirmation_signal,
        "user_intervention_required_now": user_intervention_required_now,
        "latest_record_path": str(record_path),
    }
    if recommended_command is not None:
        payload["recommended_step_id"] = "run_quality_repair_batch"
        payload["recommended_command"] = recommended_command
    return payload

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
