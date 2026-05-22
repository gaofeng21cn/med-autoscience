from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent, paper_repair_execution_evidence
from med_autoscience.controllers.work_unit_evidence_adoption_parts import (
    analysis_repair_adoption,
    completed_lifecycle,
    completed_work_unit_handoff,
    generic_completed_work_unit,
)


_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY = "last_controller_decision_authorization"
_WORK_UNIT_TARGET_CONTEXT_KEYS = (
    "specificity_targets",
    "work_unit_targets",
    "blocking_artifact_refs",
    "blocker_details",
    "gate_blocker_details",
    "gaps",
    "source_path",
)


def _text(value: object) -> str | None:
    return analysis_repair_adoption.text(value)


def _read_json_mapping(path: Path) -> dict[str, Any]:
    return analysis_repair_adoption.read_json_mapping(path)


def _write_json_mapping(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _timestamp_key(value: object) -> str | None:
    return analysis_repair_adoption.timestamp_key(value)


def _controller_work_unit_lifecycle_projection(lifecycle: dict[str, Any] | None) -> dict[str, Any]:
    payload = lifecycle if isinstance(lifecycle, dict) else {}
    return {
        "lifecycle_state": str(payload.get("lifecycle_state") or "new").strip() or "new",
        "latest_event_type": payload.get("latest_event_type"),
        "delivery_blocked": bool(payload.get("delivery_blocked")),
        "block_reason": payload.get("block_reason"),
        "terminal_consumed": bool(payload.get("terminal_consumed")),
    }


def _controller_work_unit_adoption_lifecycle(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
) -> dict[str, Any]:
    decision_emitted_at = _timestamp_key(authorization_context.get("decision_emitted_at"))
    if decision_emitted_at is None:
        return control_intent.lifecycle_state(study_root=study_root, identity=identity)
    lifecycle = control_intent.lifecycle_state_since(
        study_root=study_root,
        identity=identity,
        recorded_at=decision_emitted_at,
    )
    if lifecycle.get("lifecycle_state") != "new":
        return lifecycle
    if evidence_adoption.get("already_recorded") is not True:
        return lifecycle
    full_lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    if full_lifecycle.get("terminal_consumed") is True:
        return full_lifecycle
    return lifecycle


def existing_controller_work_unit_evidence_adoption(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    return completed_work_unit_handoff.existing_adoption_payload(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )


def _mark_controller_work_unit_evidence_adopted(
    *,
    quest_root: Path,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
    lifecycle: dict[str, Any],
) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    runtime_state = _read_json_mapping(runtime_state_path)
    runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY] = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "publication_eval_id": _text(authorization_context.get("publication_eval_id")),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
        "source_route_key_question": str(authorization_context.get("source_route_key_question") or "").strip() or None,
        "work_unit_id": str(authorization_context.get("work_unit_id") or "").strip() or None,
        "work_unit_fingerprint": str(authorization_context.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": dict(authorization_context.get("next_work_unit") or {}),
        "blocking_work_units": list(authorization_context.get("blocking_work_units") or []),
        "control_intent_key": str(authorization_context.get("control_intent_key") or "").strip() or None,
        "control_intent_identity": dict(authorization_context.get("control_intent_identity") or {}),
        "active_run_id": _text(evidence_adoption.get("active_run_id")),
        "delivery_mode": "controller_work_unit_evidence_adoption",
        "message_id": None,
        "source": _text(evidence_adoption.get("source")),
        "evidence_adoption": {
            key: evidence_adoption.get(key)
            for key in (
                "report_ref",
                "created_at",
                "recommended_next_route",
                "status",
                "artifact_kind",
                "already_recorded",
            )
            if key in evidence_adoption
        },
        "controller_work_unit_lifecycle": _controller_work_unit_lifecycle_projection(lifecycle),
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in authorization_context:
            runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY][key] = authorization_context[key]
    _write_json_mapping(runtime_state_path, runtime_state)


def record_controller_work_unit_evidence_adoption(
    *,
    status: Any,
    study_root: Path,
    quest_root: Path | None = None,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
) -> None:
    lifecycle = _controller_work_unit_adoption_lifecycle(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
        evidence_adoption=evidence_adoption,
    )
    relaunch_required = analysis_repair_adoption.result_requires_runtime_relaunch(
        dict(evidence_adoption.get("result") or {})
    )
    next_owner = _text(evidence_adoption.get("next_owner")) or "publication_gate"
    next_work_unit = _text(evidence_adoption.get("next_work_unit"))
    status.extras["controller_work_unit_evidence_adoption"] = evidence_adoption
    status.extras["controller_decision_authorization_deduped"] = {
        "control_intent_key": authorization_context.get("control_intent_key"),
        "source": "controller_work_unit_evidence_adoption",
        "lifecycle": lifecycle,
    }
    status.extras["controller_work_unit_next_route"] = {
        "recommended_next_route": evidence_adoption.get("recommended_next_route"),
        "owner": next_owner,
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": relaunch_required,
    }
    if next_work_unit is not None:
        status.extras["controller_work_unit_next_route"]["next_work_unit"] = next_work_unit
    _rebuild_repair_execution_evidence_for_completed_work_unit(
        study_root=study_root,
        authorization_context=authorization_context,
        evidence_adoption=evidence_adoption,
    )
    completed_lifecycle.mark_owner_handoff_if_completed(
        study_root=study_root,
        authorization_context=authorization_context,
        evidence_adoption=evidence_adoption,
        read_json_mapping=_read_json_mapping,
        write_json_mapping=_write_json_mapping,
    )
    if quest_root is not None:
        _mark_controller_work_unit_evidence_adopted(
            quest_root=quest_root,
            authorization_context=authorization_context,
            evidence_adoption=evidence_adoption,
            lifecycle=lifecycle,
        )


def _rebuild_repair_execution_evidence_for_completed_work_unit(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
) -> None:
    if not generic_completed_work_unit.is_completed_adoption_payload(evidence_adoption):
        return
    changed_artifact_refs = _completed_work_unit_changed_artifact_refs(evidence_adoption)
    if not changed_artifact_refs:
        return
    resolved_study_root = Path(study_root).expanduser().resolve()
    evidence = paper_repair_execution_evidence.build_repair_execution_evidence(
        study_id=str(authorization_context.get("study_id") or ""),
        quest_id=str(authorization_context.get("quest_id") or ""),
        study_root=resolved_study_root,
        repair_work_unit=_completed_work_unit_repair_work_unit(authorization_context),
        review_finding=_completed_work_unit_review_finding(authorization_context),
        source_refs=_completed_work_unit_source_refs(evidence_adoption),
        changed_artifact_refs=changed_artifact_refs,
        revision_log_ref=_existing_ref(resolved_study_root / "paper" / "review" / "review_ledger.json")
        or _existing_ref(resolved_study_root / "paper" / "review_ledger.json"),
        evidence_ledger_ref=_existing_ref(resolved_study_root / "paper" / "evidence_ledger.json"),
        review_ledger_ref=_existing_ref(resolved_study_root / "paper" / "review" / "review_ledger.json")
        or _existing_ref(resolved_study_root / "paper" / "review_ledger.json"),
        gate_replay_target="publication_gate",
        gate_replay_refs=_completed_work_unit_gate_replay_refs(
            study_root=resolved_study_root,
            authorization_context=authorization_context,
        ),
        ai_reviewer_recheck_request_ref=_existing_ref(
            resolved_study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
        ),
    )
    evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
        study_root=resolved_study_root,
        evidence=evidence,
    )
    evidence_adoption["repair_execution_evidence_path"] = str(evidence_path)
    evidence_adoption["repair_execution_evidence_status"] = evidence.get("status")


def _completed_work_unit_changed_artifact_refs(evidence_adoption: dict[str, Any]) -> list[object]:
    refs = evidence_adoption.get("artifact_refs")
    return list(refs) if isinstance(refs, list) else []


def _completed_work_unit_source_refs(evidence_adoption: dict[str, Any]) -> list[object]:
    refs = evidence_adoption.get("source_refs")
    source_refs = list(refs) if isinstance(refs, list) else []
    report_ref = _text(evidence_adoption.get("report_ref"))
    if report_ref is not None:
        source_refs.append(report_ref)
    return source_refs


def _completed_work_unit_gate_replay_refs(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
) -> list[object]:
    refs: list[object] = []
    for key in ("publication_eval_path", "decision_path"):
        ref = _existing_context_ref(study_root=study_root, value=authorization_context.get(key))
        if ref is not None and ref not in refs:
            refs.append(ref)
    return refs


def _completed_work_unit_repair_work_unit(authorization_context: dict[str, Any]) -> dict[str, Any]:
    next_work_unit = authorization_context.get("next_work_unit")
    repair_work_unit = dict(next_work_unit) if isinstance(next_work_unit, dict) else {}
    work_unit_id = _text(authorization_context.get("work_unit_id"))
    if work_unit_id is not None:
        repair_work_unit["unit_id"] = work_unit_id
    if _text(repair_work_unit.get("gate_replay_target")) is None:
        repair_work_unit["gate_replay_target"] = "publication_gate"
    for key in ("work_unit_fingerprint", "route_target", "route_key_question", "source_route_key_question"):
        value = _text(authorization_context.get(key))
        if value is not None:
            repair_work_unit[key] = value
    return repair_work_unit or {"unit_id": "repair_work_unit", "gate_replay_target": "publication_gate"}


def _completed_work_unit_review_finding(authorization_context: dict[str, Any]) -> dict[str, Any]:
    finding: dict[str, Any] = {}
    for source_key, target_key in (
        ("publication_eval_id", "source_eval_id"),
        ("decision_id", "controller_decision_id"),
        ("work_unit_fingerprint", "work_unit_fingerprint"),
    ):
        value = _text(authorization_context.get(source_key))
        if value is not None:
            finding[target_key] = value
    for key in ("route_target", "route_key_question", "source_route_key_question"):
        value = _text(authorization_context.get(key))
        if value is not None:
            finding[key] = value
    return finding


def _existing_ref(path: Path) -> str | None:
    resolved = Path(path).expanduser().resolve()
    return str(resolved) if resolved.exists() else None


def _existing_context_ref(*, study_root: Path, value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = Path(study_root).expanduser().resolve() / path
    return _existing_ref(path)


def _has_prior_delivery_or_duplicate(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> bool:
    return any(
        _text(event.get("event_type")) in {"delivered", "skipped_duplicate"}
        for event in control_intent.events_for_business_key_since(
            study_root=study_root,
            business_key=identity.business_key,
            recorded_at=authorization_context.get("decision_emitted_at"),
        )
    )


def _adopt_analysis_repair_evidence(
    *,
    study_root: Path,
    quest_root: Path,
    authorization_context: dict[str, Any],
    identity: control_intent.ControlIntentIdentity,
    active_run_id: str | None,
    source: str,
    has_delivery_for_current_decision: bool,
) -> dict[str, Any] | None:
    for report_path in analysis_repair_adoption.report_candidates(quest_root, active_run_id=active_run_id):
        if not report_path.exists():
            continue
        report_payload = analysis_repair_adoption.normalize_report_payload(
            _read_json_mapping(report_path),
            authorization_context=authorization_context,
        )
        if not analysis_repair_adoption.report_matches(
            payload=report_payload,
            authorization_context=authorization_context,
        ):
            continue
        if (
            not has_delivery_for_current_decision
            and not analysis_repair_adoption.is_exhausted_handoff(report_payload)
        ):
            continue
        payload = analysis_repair_adoption.adoption_payload(
            report_path=report_path,
            report_payload=report_payload,
            authorization_context=authorization_context,
            active_run_id=active_run_id,
            source=source,
        )
        control_intent.append_event(
            study_root=study_root,
            identity=identity,
            event_type="artifact_written",
            payload=payload,
        )
        handoff_payload = analysis_repair_adoption.owner_handoff_payload(
            report_payload=report_payload,
            report_path=report_path,
            source=source,
        )
        if handoff_payload is not None:
            control_intent.append_event(
                study_root=study_root,
                identity=identity,
                event_type="owner_handoff",
                payload=handoff_payload,
            )
        return payload
    return None


def _adopt_generic_completed_work_unit(
    *,
    study_root: Path,
    quest_root: Path,
    authorization_context: dict[str, Any],
    identity: control_intent.ControlIntentIdentity,
    active_run_id: str | None,
    source: str,
    authorized_run_ids: tuple[str, ...],
) -> dict[str, Any] | None:
    is_gate_recheck = generic_completed_work_unit.authorization_is_publication_gate_recheck(authorization_context)
    for report_path in generic_completed_work_unit.report_candidates(
        quest_root,
        active_run_id=active_run_id,
        delivered_run_ids=authorized_run_ids,
    ):
        report_payload = generic_completed_work_unit.read_json_mapping(report_path)
        if not generic_completed_work_unit.matches_completed_work_unit(
            payload=report_payload,
            authorization_context=authorization_context,
            analysis_repair_authorized=False,
            active_run_id=active_run_id,
            delivered_run_ids=authorized_run_ids,
        ):
            continue
        adopted_active_run_id = _text(report_payload.get("run_id")) or _text(report_payload.get("active_run_id"))
        payload = {
            "active_run_id": adopted_active_run_id or active_run_id,
            "report_ref": str(report_path),
            "created_at": generic_completed_work_unit.report_timestamp(report_payload),
            "work_unit_id": _text(authorization_context.get("work_unit_id")),
            "route_target": _text(authorization_context.get("route_target")),
            "recommended_next_route": (
                "publication_gate_replay_completed"
                if is_gate_recheck
                else generic_completed_work_unit.RECOMMENDED_NEXT_ROUTE
            ),
            "source": source,
            "next_owner": "publication_gate" if is_gate_recheck else generic_completed_work_unit.NEXT_OWNER,
            "result": generic_completed_work_unit.normalized_result(
                report_payload,
                authorization_context=authorization_context,
            ),
        }
        if artifact_kind := _text(report_payload.get("artifact_kind")):
            payload["artifact_kind"] = artifact_kind
        if report_status := _text(report_payload.get("status")):
            payload["status"] = report_status
        artifact_refs = generic_completed_work_unit.artifact_refs(report_payload)
        if artifact_refs:
            payload["artifact_refs"] = artifact_refs
        source_refs = generic_completed_work_unit.source_refs(report_payload)
        if source_refs:
            payload["source_refs"] = source_refs
        control_intent.append_event(
            study_root=study_root,
            identity=identity,
            event_type="artifact_written",
            payload=payload,
        )
        if not is_gate_recheck:
            control_intent.append_event(
                study_root=study_root,
                identity=identity,
                event_type="owner_handoff",
                payload=generic_completed_work_unit.owner_handoff_payload(report_path=report_path, source=source),
            )
        return payload
    return None


def adopt_controller_work_unit_evidence_if_present(
    *,
    study_root: Path,
    quest_root: Path,
    authorization_context: dict[str, Any],
    identity: control_intent.ControlIntentIdentity,
    active_run_id: str | None,
    source: str,
) -> dict[str, Any] | None:
    existing_payload = completed_work_unit_handoff.existing_adoption_payload(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    if existing_payload is not None:
        completed_work_unit_handoff.ensure_existing_completed_handoff(
            study_root=study_root,
            identity=identity,
            evidence_adoption=existing_payload,
            source=source,
        )
        return existing_payload
    has_delivery_for_current_decision = _has_prior_delivery_or_duplicate(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    business_key_events = control_intent.events_for_business_key(
        study_root=study_root,
        business_key=identity.business_key,
    )
    has_delivery_for_same_business_key = generic_completed_work_unit.has_delivery_or_duplicate(business_key_events)
    delivered_run_ids = generic_completed_work_unit.delivered_run_ids_for_business_key(
        events=business_key_events,
        decision_emitted_at=authorization_context.get("decision_emitted_at"),
    )
    relay_run_ids = generic_completed_work_unit.relay_run_ids_for_authorization(
        quest_root=quest_root,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        work_unit_target_context_keys=_WORK_UNIT_TARGET_CONTEXT_KEYS,
    )
    authorized_run_ids = (*delivered_run_ids, *relay_run_ids)
    has_matching_relay_marker = generic_completed_work_unit.has_matching_relay_marker(
        quest_root=quest_root,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        work_unit_target_context_keys=_WORK_UNIT_TARGET_CONTEXT_KEYS,
    )
    if (
        not has_delivery_for_current_decision
        and not has_delivery_for_same_business_key
        and not has_matching_relay_marker
        and not relay_run_ids
    ):
        return None
    if analysis_repair_adoption.authorization_matches(authorization_context):
        return _adopt_analysis_repair_evidence(
            study_root=study_root,
            quest_root=quest_root,
            authorization_context=authorization_context,
            identity=identity,
            active_run_id=active_run_id,
            source=source,
            has_delivery_for_current_decision=has_delivery_for_current_decision,
        )
    return _adopt_generic_completed_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        authorization_context=authorization_context,
        identity=identity,
        active_run_id=active_run_id,
        source=source,
        authorized_run_ids=authorized_run_ids,
    )
