from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import current_work_unit as current_work_unit_reducer


def current_executable_owner_action(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_executable_owner_action"))
    if direct:
        return direct
    return _mapping(_mapping(progress.get("progress_first_monitoring_summary")).get("current_executable_owner_action"))


def successor_owner_action_from_terminal_blocker(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    blocker_reason: str | None,
) -> dict[str, Any] | None:
    if blocker_reason == "current_owner_route_missing":
        successor = _successor_owner_action_from_repair_progress_gate_replay(
            progress,
            typed_blocker=typed_blocker,
        )
        if successor is not None:
            return successor
    action = current_executable_owner_action(progress)
    if action and current_work_unit_reducer.action_supersedes_typed_blocker(
        action=action,
        blocker=typed_blocker,
        progress=progress,
    ):
        return successor_owner_action_from_current_action(action)
    if blocker_reason == "publication_gate_replay_blocked":
        return _successor_owner_action_from_gate_followthrough(progress)
    return None


def successor_owner_action_from_current_action(action: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _first_text(action.get("action_type"), *_text_items(action.get("allowed_actions")))
    owner = _first_text(action.get("next_owner"), action.get("owner"), action.get("request_owner"))
    work_unit_id = _first_text(action.get("work_unit_id"), action.get("next_work_unit"))
    fingerprint = _first_text(action.get("work_unit_fingerprint"), action.get("action_fingerprint"))
    source_ref = _first_text(action.get("source_ref"), *_text_items(action.get("acceptance_refs")))
    return {
        key: value
        for key, value in {
            "action_type": action_type,
            "owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_surface": _first_text(action.get("source_surface"), action.get("source")),
            "source_ref": source_ref,
        }.items()
        if value not in (None, "", [], {})
    }


def current_owner_successor_action(
    progress: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    action = _mapping(current_action) or current_executable_owner_action(progress)
    source = _text(action.get("source")) or _text(action.get("source_surface"))
    if source != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return None
    if not _gate_followthrough_has_consumed_repair_progress(progress, action=action):
        return None
    successor = successor_owner_action_from_current_action(action)
    if (
        _text(successor.get("action_type")) is None
        or _text(successor.get("owner")) is None
        or _text(successor.get("work_unit_id")) is None
        or _text(successor.get("work_unit_fingerprint")) is None
    ):
        return None
    return successor


def _gate_followthrough_has_consumed_repair_progress(
    progress: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
) -> bool:
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    if repair.get("accepted_owner_receipt") is not True:
        return False
    if repair.get("gate_replay_done") is not True:
        return False
    action_work_unit = _text(action.get("work_unit_id"))
    repair_work_unit = _text(repair.get("work_unit_id"))
    if action_work_unit is None or repair_work_unit != action_work_unit:
        return False
    action_eval = _text(action.get("source_eval_id"))
    repair_eval = _text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    return bool(
        _text(repair.get("repair_execution_evidence_ref"))
        or _text(repair.get("owner_receipt_ref"))
        or _text_items(repair.get("gate_replay_refs"))
    )


def _successor_owner_action_from_repair_progress_gate_replay(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _text(typed_blocker.get("action_type")) != "run_gate_clearing_batch":
        return None
    if _text(typed_blocker.get("work_unit_id")) != "publication_gate_replay":
        return None
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return None
    if repair.get("paper_delta_observed") is not True:
        return None
    if repair.get("accepted_owner_receipt") is not True:
        return None
    if repair.get("gate_replay_done") is not True:
        return None
    fingerprint = _text(repair.get("source_fingerprint"))
    if fingerprint is None or fingerprint != _text(typed_blocker.get("work_unit_fingerprint")):
        return None
    blocker_eval = _typed_blocker_source_eval_id(typed_blocker)
    repair_eval = _text(repair.get("source_eval_id"))
    if blocker_eval is not None and repair_eval is not None and blocker_eval != repair_eval:
        return None
    source_ref = (
        _text(repair.get("repair_execution_evidence_ref"))
        or _text(repair.get("owner_receipt_ref"))
        or _first_text(*_text_items(repair.get("gate_replay_refs")))
    )
    if source_ref is None:
        return None
    return {
        "action_type": "run_gate_clearing_batch",
        "owner": "gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": fingerprint,
        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "source_ref": source_ref,
    }


def successor_owner_gate_from_terminal_blocker(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    blocker_reason: str | None,
    owner: str,
) -> dict[str, Any] | None:
    if not _terminal_owner_answer_present(typed_blocker):
        return None
    if blocker_reason != "anti_loop_budget_exhausted":
        return None
    obligation = {
        "action_type": _text(typed_blocker.get("action_type")),
        "work_unit_id": _text(typed_blocker.get("work_unit_id")),
        "work_unit_fingerprint": _text(typed_blocker.get("work_unit_fingerprint")),
    }
    closeout = _matching_terminal_closeout(progress, obligation=obligation)
    closeout_from_ref = _matching_terminal_closeout_from_typed_blocker_refs(
        progress,
        typed_blocker=typed_blocker,
        obligation=obligation,
    )
    if _next_forced_delta_from_closeout(closeout_from_ref):
        closeout = closeout_from_ref
    next_forced_delta = _next_forced_delta_from_closeout(closeout) or _next_forced_delta_from_progress(progress)
    required_input = _first_text(
        _mapping(next_forced_delta).get("required_delta_kind"),
        _mapping(next_forced_delta).get("required_delta"),
        _mapping(next_forced_delta).get("reason"),
        _text(typed_blocker.get("required_owner_action")),
    )
    if required_input is None:
        required_input = "successor_work_unit_or_owner_gate_after_terminal_stop_loss"
    return {
        "owner": owner,
        "required_input": required_input,
        "work_unit_id": _text(typed_blocker.get("work_unit_id")),
        "work_unit_fingerprint": _text(typed_blocker.get("work_unit_fingerprint")),
        "source_surface": "terminal_typed_blocker.next_forced_delta",
        "evidence_refs": _dedupe(
            [
                *_text_items(typed_blocker.get("closeout_refs")),
                _text(typed_blocker.get("typed_blocker_ref")),
                _text(typed_blocker.get("latest_owner_answer_ref")),
                *_closeout_refs(closeout or {}),
            ]
        ),
    }


def _successor_owner_action_from_gate_followthrough(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return None
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(followthrough.get("gate_replay_status")) != "blocked":
        return None
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return None
    if currentness.get("lacks_specific_blocker_object") is True:
        return None
    work_unit = (
        _mapping(followthrough.get("current_publication_work_unit"))
        or _mapping(followthrough.get("explicit_publication_work_unit"))
        or _mapping(followthrough.get("selected_publication_work_unit"))
    )
    work_unit_id = _first_text(
        followthrough.get("work_unit_id"),
        currentness.get("current_publication_work_unit_id"),
        currentness.get("explicit_publication_work_unit_id"),
        currentness.get("selected_publication_work_unit_id"),
        work_unit.get("unit_id"),
        work_unit.get("work_unit_id"),
    )
    fingerprint = _first_text(
        followthrough.get("work_unit_fingerprint"),
        currentness.get("current_work_unit_fingerprint"),
        currentness.get("explicit_work_unit_fingerprint"),
    )
    lane = _first_text(work_unit.get("lane"), followthrough.get("lane"))
    if work_unit_id is None or fingerprint is None or lane != "write":
        return None
    return {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": _text(followthrough.get("latest_record_path")),
    }


def _matching_terminal_closeout(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for key in (
        "terminal_closeout_precedence_evidence",
        "terminal_closeout",
        "accepted_closeout_evidence",
    ):
        value = progress.get(key)
        if isinstance(value, list):
            for item in value:
                candidate = _mapping(item)
                if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                    return dict(candidate)
        else:
            candidate = _mapping(value)
            if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                return dict(candidate)
    return None


def _matching_terminal_closeout_from_typed_blocker_refs(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for ref in _terminal_closeout_ref_candidates(typed_blocker):
        closeout = _read_closeout_ref(progress, ref)
        if closeout and _closeout_matches_obligation(closeout, obligation=obligation):
            closeout.setdefault("source_path", _strip_ref_fragment(ref))
            return closeout
    return None


def _closeout_matches_obligation(
    closeout: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if action_type and _text(closeout.get("action_type")) not in {None, action_type}:
        return False
    if work_unit_id and _text(closeout.get("work_unit_id")) not in {None, work_unit_id}:
        return False
    if fingerprint:
        closeout_fingerprints = {
            value
            for value in (
                _text(closeout.get("work_unit_fingerprint")),
                _text(closeout.get("action_fingerprint")),
            )
            if value is not None
        }
        if closeout_fingerprints and fingerprint not in closeout_fingerprints:
            return False
    return bool(
        _text(closeout.get("stage_attempt_id"))
        or _text(closeout.get("active_stage_attempt_id"))
        or _closeout_refs(closeout)
    )


def _closeout_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(closeout.get("closeout_ref")),
        _text(closeout.get("source_path")),
        *_text_items(closeout.get("closeout_refs")),
    ]
    return _dedupe(refs)


def _terminal_owner_answer_present(typed_blocker: Mapping[str, Any]) -> bool:
    return any(
        _text(value) is not None
        for value in (
            typed_blocker.get("latest_owner_answer_ref"),
            typed_blocker.get("typed_blocker_ref"),
            typed_blocker.get("source_ref"),
        )
    )


def _terminal_closeout_ref_candidates(typed_blocker: Mapping[str, Any]) -> list[str]:
    return _dedupe(
        [
            *_text_items(typed_blocker.get("closeout_refs")),
            _text(typed_blocker.get("typed_blocker_ref")),
            _text(typed_blocker.get("latest_owner_answer_ref")),
            _text(typed_blocker.get("source_ref")),
        ]
    )


def _read_closeout_ref(progress: Mapping[str, Any], ref: str) -> dict[str, Any]:
    path_text = _strip_ref_fragment(ref)
    if path_text is None:
        return {}
    for path in _candidate_ref_paths(progress, path_text):
        payload = _read_json_object(path)
        if payload:
            return payload
    return {}


def _candidate_ref_paths(progress: Mapping[str, Any], path_text: str) -> list[Path]:
    ref_path = Path(path_text).expanduser()
    if ref_path.is_absolute():
        return [ref_path]
    candidates: list[Path] = []
    workspace_root = _path(progress.get("workspace_root"))
    study_root = _path(progress.get("study_root"))
    if workspace_root is not None:
        candidates.append(workspace_root / ref_path)
    if study_root is not None:
        candidates.append(study_root / ref_path)
        study_id = _text(progress.get("study_id"))
        if study_id:
            prefix = f"studies/{study_id}/"
            if path_text.startswith(prefix):
                candidates.append(study_root / path_text.removeprefix(prefix))
        if study_root.name and path_text.startswith(f"{study_root.name}/"):
            candidates.append(study_root.parent / ref_path)
    return _dedupe_paths(candidates)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, NotADirectoryError, OSError, json.JSONDecodeError):
        return {}
    return _mapping(payload)


def _strip_ref_fragment(ref: str | None) -> str | None:
    text = _text(ref)
    if text is None:
        return None
    return text.split("#", 1)[0]


def _path(value: object) -> Path | None:
    text = _text(value)
    return Path(text).expanduser() if text is not None else None


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _typed_blocker_source_eval_id(typed_blocker: Mapping[str, Any]) -> str | None:
    return _first_text(
        typed_blocker.get("source_eval_id"),
        _mapping(typed_blocker.get("currentness_basis")).get("source_eval_id"),
        _mapping(typed_blocker.get("owner_route_currentness_basis")).get("source_eval_id"),
    )


def _next_forced_delta_from_closeout(closeout: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(closeout)
    if not payload:
        return {}
    paper_log = _mapping(payload.get("paper_stage_log"))
    return _mapping(payload.get("next_forced_delta")) or _mapping(paper_log.get("next_forced_delta"))


def _next_forced_delta_from_progress(progress: Mapping[str, Any]) -> dict[str, Any]:
    for candidate in (
        progress.get("next_forced_delta"),
        _mapping(progress.get("progress_first_monitoring_summary")).get("next_forced_delta"),
        _mapping(progress.get("progress_first_monitoring_summary")).get("latest_terminal_stage"),
        _mapping(progress.get("progress_first_monitoring_summary")).get("latest_terminal_stage_log"),
    ):
        payload = _mapping(candidate)
        if not payload:
            continue
        next_delta = _mapping(payload.get("next_forced_delta")) or payload
        if next_delta:
            return next_delta
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _dedupe(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = [
    "current_executable_owner_action",
    "current_owner_successor_action",
    "successor_owner_action_from_current_action",
    "successor_owner_action_from_terminal_blocker",
    "successor_owner_gate_from_terminal_blocker",
]
