from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import medical_paper_v2_materializers


SCHEMA_VERSION = 1
COMMAND_SURFACE = "medical_paper_v3_guarded_operator_command"
RESULT_SURFACE = "medical_paper_v3_guarded_operator_action_result"
LEDGER_SURFACE = "medical_paper_v3_guarded_operator_action_ledger"
REPLAY_LEDGER_SURFACE = "medical_paper_v5_guarded_operator_replay_ledger"
ACTIONS_ROOT = Path("artifacts/medical_paper/actions")

ACTION_SURFACE_KEYS: dict[str, str] = {
    "materialize_literature_scout": "literature_scout",
    "run_provider_literature_scout": "literature_provider_runtime",
    "materialize_study_line_selection": "study_line_selection",
    "materialize_archetype_analysis_contract": "archetype_analysis_contract",
    "materialize_bounded_analysis_candidate_board": "bounded_analysis_candidate_board",
    "materialize_stop_loss_memo": "stop_loss_memo",
    "materialize_target_journal_writing_layer": "target_journal_writing_layer",
    "materialize_real_study_soak_matrix_evidence": "real_study_soak_matrix_evidence",
    "materialize_route_decision": "route_decision_orchestrator",
    "resolve_statistical_blockers": "statistical_discipline_operations",
    "start_revision_rebuttal_loop": "revision_rebuttal_loop",
    "authorize_manuscript_drafting": "authoring_runtime_authorization",
    "run_real_workspace_soak_monitor": "real_workspace_soak_monitor",
}


def guarded_operator_authority_contract() -> dict[str, Any]:
    return {
        "surface": "medical_paper_v3_operator_authority_contract",
        "schema_version": SCHEMA_VERSION,
        "guard": "existing_product_entry_controller_guard",
        "owner": "MAS_controller_product_entry",
        "execution_boundary": "guarded_operator_action",
        "can_mutate_runtime": False,
        "can_write_runtime_owned_artifacts": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "runtime_write_policy": "supervisor_runtime_guard_required",
    }


def guarded_operator_command(
    *,
    action_id: str,
    surface_key: str | None,
    action_instance_id: str | None = None,
    idempotency_key: str | None = None,
    input_digest: str | None = None,
    operator_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    digest = input_digest
    if digest is None and operator_payload is not None:
        digest = guarded_operator_input_digest(
            action_id=action_id,
            surface_key=surface_key,
            operator_payload=operator_payload,
        )
    if digest is None:
        digest = _pending_input_digest(action_id=action_id, surface_key=surface_key)
    resolved_action_instance_id = _resolved_action_instance_id(
        action_id=action_id,
        surface_key=surface_key,
        action_instance_id=action_instance_id,
    )
    resolved_idempotency_key = _resolved_idempotency_key(
        action_id=action_id,
        surface_key=surface_key,
        action_instance_id=resolved_action_instance_id,
        idempotency_key=idempotency_key,
    )
    return {
        "surface": COMMAND_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "action_id": action_id,
        "action_instance_id": resolved_action_instance_id,
        "idempotency_key": resolved_idempotency_key,
        "input_digest": digest,
        "surface_key": surface_key,
        "entrypoint": "product_entry.dispatch_guarded_medical_paper_operator_action",
        "guard": "existing_product_entry_controller_guard",
        "requires": ["profile_ref", "study_id", "operator_payload"],
        "status": "guarded_pending",
    }


def guarded_pending_action_result(
    *,
    missing_reason: str | None,
    next_action: str,
    action_id: str | None = None,
    surface_key: str | None = None,
    action_instance_id: str | None = None,
    idempotency_key: str | None = None,
    input_digest: str | None = None,
) -> dict[str, Any]:
    resolved_action_instance_id = (
        _resolved_action_instance_id(
            action_id=action_id,
            surface_key=surface_key,
            action_instance_id=action_instance_id,
        )
        if action_id
        else action_instance_id
    )
    digest = input_digest
    if digest is None and action_id:
        digest = _pending_input_digest(action_id=action_id, surface_key=surface_key)
    resolved_idempotency_key = (
        _resolved_idempotency_key(
            action_id=action_id,
            surface_key=surface_key,
            action_instance_id=resolved_action_instance_id,
            idempotency_key=idempotency_key,
        )
        if action_id
        else idempotency_key
    )
    return {
        "status": "guarded_pending",
        "durable_ref": None,
        "missing_reason": missing_reason,
        "next_action": next_action,
        "authority_contract": guarded_operator_authority_contract(),
        "action_instance_id": resolved_action_instance_id,
        "idempotency_key": resolved_idempotency_key,
        "input_digest": digest,
    }


def dispatch_guarded_medical_paper_operator_action(
    *,
    study_root: Path,
    action_id: str,
    surface_key: str | None = None,
    operator_payload: Mapping[str, Any] | None = None,
    action_instance_id: str | None = None,
    idempotency_key: str | None = None,
    apply: bool = True,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    expected_surface_key = ACTION_SURFACE_KEYS.get(action_id)
    if expected_surface_key is None:
        return _blocked_result(
            action_id=action_id,
            surface_key=surface_key,
            missing_reason="unsupported_guarded_operator_action",
            action_instance_id=action_instance_id,
            idempotency_key=idempotency_key,
        )
    if surface_key is not None and surface_key != expected_surface_key:
        return _blocked_result(
            action_id=action_id,
            surface_key=surface_key,
            missing_reason="action_surface_mismatch",
            action_instance_id=action_instance_id,
            idempotency_key=idempotency_key,
        )
    if not operator_payload:
        return _blocked_result(
            action_id=action_id,
            surface_key=expected_surface_key,
            missing_reason="missing_operator_payload",
            action_instance_id=action_instance_id,
            idempotency_key=idempotency_key,
        )
    if not isinstance(operator_payload, Mapping):
        return _blocked_result(
            action_id=action_id,
            surface_key=expected_surface_key,
            missing_reason="operator_payload_must_be_mapping",
            action_instance_id=action_instance_id,
            idempotency_key=idempotency_key,
        )
    try:
        input_digest = guarded_operator_input_digest(
            action_id=action_id,
            surface_key=expected_surface_key,
            operator_payload=operator_payload,
        )
    except TypeError:
        return _blocked_result(
            action_id=action_id,
            surface_key=expected_surface_key,
            missing_reason="operator_payload_not_json_serializable",
            action_instance_id=action_instance_id,
            idempotency_key=idempotency_key,
        )

    resolved_action_instance_id = _resolved_action_instance_id(
        action_id=action_id,
        surface_key=expected_surface_key,
        action_instance_id=action_instance_id,
    )
    resolved_idempotency_key = _resolved_idempotency_key(
        action_id=action_id,
        surface_key=expected_surface_key,
        action_instance_id=resolved_action_instance_id,
        idempotency_key=idempotency_key,
    )
    existing = _read_action_ledger(study_root=resolved_study_root, idempotency_key=resolved_idempotency_key)
    if existing:
        previous_digest = _text(existing.get("input_digest"))
        if previous_digest and previous_digest != input_digest:
            return _blocked_result(
                action_id=action_id,
                surface_key=expected_surface_key,
                missing_reason="input_digest_drift",
                action_instance_id=resolved_action_instance_id,
                idempotency_key=resolved_idempotency_key,
                input_digest=input_digest,
                expected_input_digest=previous_digest,
                observed_input_digest=input_digest,
                duplicate_submit_detected=True,
                reconciliation="input_digest_drift",
            )
        replayed = _replay_previous_result(
            study_root=resolved_study_root,
            idempotency_key=resolved_idempotency_key,
            ledger=existing,
        )
        if replayed:
            return replayed

    materialized = medical_paper_v2_materializers.materialize_medical_paper_v2_surface(
        study_root=resolved_study_root,
        surface_key=expected_surface_key,
        payload=operator_payload,
        apply=apply,
    )
    status = _text(materialized.get("status")) or "blocked"
    missing_reason = _text(materialized.get("missing_reason"))
    durable_ref = _text(materialized.get("artifact_path")) or None
    result_ref = _action_result_relative_path(idempotency_key=resolved_idempotency_key)
    ledger_ref = _action_ledger_relative_path(idempotency_key=resolved_idempotency_key)
    result = {
        "surface": RESULT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "action_id": action_id,
        "action_instance_id": resolved_action_instance_id,
        "idempotency_key": resolved_idempotency_key,
        "input_digest": input_digest,
        "surface_key": expected_surface_key,
        "status": status,
        "durable_ref": durable_ref if status not in {"blocked", "missing"} else durable_ref,
        "replay_ref": str(ledger_ref),
        "missing_reason": missing_reason,
        "next_action": _next_action_for_status(status=status, missing_reason=missing_reason),
        "authority_contract": guarded_operator_authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "duplicate_submit_detected": False,
        "replay": False,
        "dry_run": not apply,
        "reconciliation": "new_result",
        "action_result_ref": str(result_ref),
        "retry_governance": _retry_governance(
            status=status,
            missing_reason=missing_reason,
            duplicate_submit_detected=False,
            reconciliation="new_result",
        ),
        "materializer_result": materialized,
    }
    if apply:
        _write_action_result_and_ledger(
            study_root=resolved_study_root,
            idempotency_key=resolved_idempotency_key,
            result=result,
        )
    return result


def _blocked_result(
    *,
    action_id: str,
    surface_key: str | None,
    missing_reason: str,
    action_instance_id: str | None = None,
    idempotency_key: str | None = None,
    input_digest: str | None = None,
    expected_input_digest: str | None = None,
    observed_input_digest: str | None = None,
    duplicate_submit_detected: bool = False,
    reconciliation: str = "blocked",
) -> dict[str, Any]:
    resolved_action_instance_id = _resolved_action_instance_id(
        action_id=action_id,
        surface_key=surface_key,
        action_instance_id=action_instance_id,
    )
    resolved_idempotency_key = _resolved_idempotency_key(
        action_id=action_id,
        surface_key=surface_key,
        action_instance_id=resolved_action_instance_id,
        idempotency_key=idempotency_key,
    )
    result: dict[str, Any] = {
        "surface": RESULT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "action_id": action_id,
        "action_instance_id": resolved_action_instance_id,
        "idempotency_key": resolved_idempotency_key,
        "input_digest": input_digest,
        "surface_key": surface_key,
        "status": "blocked",
        "durable_ref": None,
        "replay_ref": (
            str(_action_ledger_relative_path(idempotency_key=resolved_idempotency_key))
            if resolved_idempotency_key
            else None
        ),
        "missing_reason": missing_reason,
        "next_action": "补齐 operator payload 后再通过 product-entry/controller guard 调用。",
        "authority_contract": guarded_operator_authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "duplicate_submit_detected": duplicate_submit_detected,
        "replay": False,
        "reconciliation": reconciliation,
        "blocked_retry_reason": missing_reason,
        "retry_governance": _retry_governance(
            status="blocked",
            missing_reason=missing_reason,
            duplicate_submit_detected=duplicate_submit_detected,
            reconciliation=reconciliation,
        ),
    }
    if expected_input_digest is not None:
        result["expected_input_digest"] = expected_input_digest
    if observed_input_digest is not None:
        result["observed_input_digest"] = observed_input_digest
    return result


def _next_action_for_status(*, status: str, missing_reason: str | None) -> str:
    if status == "ready":
        return "guarded operator action 已物化 durable surface，继续读取 readiness/progress 投影。"
    if status == "partial":
        return missing_reason or "继续补齐 partial surface 缺口。"
    return missing_reason or "operator action blocked；补齐输入后重试。"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def guarded_operator_input_digest(
    *,
    action_id: str,
    surface_key: str | None,
    operator_payload: Mapping[str, Any],
) -> str:
    return _stable_digest(
        {
            "action_id": action_id,
            "surface_key": surface_key,
            "operator_payload": dict(operator_payload),
        }
    )


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def _resolved_action_instance_id(
    *,
    action_id: str,
    surface_key: str | None,
    action_instance_id: str | None,
) -> str:
    text = _text(action_instance_id)
    if text:
        return text
    encoded = json.dumps(
        {"action_id": action_id, "surface_key": surface_key},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"guarded-operator-action::{action_id}::{surface_key or 'unknown'}::{digest}"


def _resolved_idempotency_key(
    *,
    action_id: str | None,
    surface_key: str | None,
    action_instance_id: str | None,
    idempotency_key: str | None,
) -> str | None:
    text = _text(idempotency_key)
    if text:
        return text
    if not action_id:
        return None
    return _stable_digest(
        {
            "action_id": action_id,
            "surface_key": surface_key,
            "action_instance_id": action_instance_id,
        }
    ).replace("sha256:", "guarded-operator-action::sha256:", 1)


def _pending_input_digest(*, action_id: str, surface_key: str | None) -> str:
    return _stable_digest(
        {
            "action_id": action_id,
            "surface_key": surface_key,
            "operator_payload": None,
        }
    )


def _action_path_key(*, idempotency_key: str) -> str:
    return hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()


def _action_result_relative_path(*, idempotency_key: str) -> Path:
    return ACTIONS_ROOT / "results" / f"{_action_path_key(idempotency_key=idempotency_key)}.json"


def _action_ledger_relative_path(*, idempotency_key: str) -> Path:
    return ACTIONS_ROOT / "ledger" / f"{_action_path_key(idempotency_key=idempotency_key)}.json"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _read_action_ledger(*, study_root: Path, idempotency_key: str) -> Mapping[str, Any]:
    return _read_json(study_root / _action_ledger_relative_path(idempotency_key=idempotency_key))


def _write_action_result_and_ledger(
    *,
    study_root: Path,
    idempotency_key: str,
    result: Mapping[str, Any],
) -> None:
    result_ref = _action_result_relative_path(idempotency_key=idempotency_key)
    ledger_ref = _action_ledger_relative_path(idempotency_key=idempotency_key)
    _write_json(study_root / result_ref, result)
    _write_json(
        study_root / ledger_ref,
        _replay_ledger_payload(
            idempotency_key=idempotency_key,
            result_ref=result_ref,
            result=result,
            event_kind="new_result",
            reconciliation="new_result",
        ),
    )


def _replay_previous_result(
    *,
    study_root: Path,
    idempotency_key: str,
    ledger: Mapping[str, Any],
) -> dict[str, Any] | None:
    result_ref = _action_result_relative_path(idempotency_key=idempotency_key)
    result_path = study_root / result_ref
    stored_result = _read_json(result_path)
    if stored_result:
        return _replayed_result(result=stored_result, reconciliation="result_replayed")
    ledger_result = ledger.get("result") if isinstance(ledger.get("result"), Mapping) else {}
    if not ledger_result:
        return None
    result = _replayed_result(result=ledger_result, reconciliation="result_recreated_from_ledger")
    _write_json(result_path, result)
    return result


def _replayed_result(*, result: Mapping[str, Any], reconciliation: str) -> dict[str, Any]:
    replayed = dict(result)
    replayed["duplicate_submit_detected"] = True
    replayed["replay"] = True
    replayed["reconciliation"] = reconciliation
    replayed["authority_contract"] = guarded_operator_authority_contract()
    replayed["quality_claim_authorized"] = False
    replayed["mechanical_projection_can_authorize_quality"] = False
    idempotency_key = _text(replayed.get("idempotency_key"))
    if idempotency_key:
        replayed["replay_ref"] = str(_action_ledger_relative_path(idempotency_key=idempotency_key))
    replayed["retry_governance"] = _retry_governance(
        status=_text(replayed.get("status")) or "unknown",
        missing_reason=_text(replayed.get("missing_reason")),
        duplicate_submit_detected=True,
        reconciliation=reconciliation,
    )
    return replayed


def _retry_governance(
    *,
    status: str,
    missing_reason: str | None,
    duplicate_submit_detected: bool,
    reconciliation: str,
) -> dict[str, Any]:
    blocked = status == "blocked"
    return {
        "surface": "medical_paper_v5_operator_retry_governance",
        "retryable": not blocked,
        "blocked_retry_reason": missing_reason if blocked else "",
        "duplicate_submit_detected": duplicate_submit_detected,
        "reconciliation": reconciliation,
        "authority_contract_snapshot": guarded_operator_authority_contract(),
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _replay_ledger_payload(
    *,
    idempotency_key: str,
    result_ref: Path,
    result: Mapping[str, Any],
    event_kind: str,
    reconciliation: str,
) -> dict[str, Any]:
    input_digest = _text(result.get("input_digest"))
    return {
        "surface": REPLAY_LEDGER_SURFACE,
        "legacy_surface": LEDGER_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "action_id": result.get("action_id"),
        "action_instance_id": result.get("action_instance_id"),
        "surface_key": result.get("surface_key"),
        "idempotency_key": idempotency_key,
        "input_digest": input_digest,
        "input_digest_history": [input_digest] if input_digest else [],
        "durable_ref": result.get("durable_ref"),
        "action_result_ref": str(result_ref),
        "replay_ref": str(_action_ledger_relative_path(idempotency_key=idempotency_key)),
        "action_timeline": [
            {
                "event": event_kind,
                "status": result.get("status"),
                "input_digest": input_digest,
                "reconciliation": reconciliation,
                "durable_ref": result.get("durable_ref"),
                "blocked_retry_reason": result.get("missing_reason") if result.get("status") == "blocked" else "",
            }
        ],
        "retry_governance": dict(result.get("retry_governance") or {}),
        "authority_contract_snapshot": guarded_operator_authority_contract(),
        "result": dict(result),
    }


__all__ = [
    "ACTION_SURFACE_KEYS",
    "COMMAND_SURFACE",
    "REPLAY_LEDGER_SURFACE",
    "RESULT_SURFACE",
    "dispatch_guarded_medical_paper_operator_action",
    "guarded_operator_input_digest",
    "guarded_operator_authority_contract",
    "guarded_operator_command",
    "guarded_pending_action_result",
]
