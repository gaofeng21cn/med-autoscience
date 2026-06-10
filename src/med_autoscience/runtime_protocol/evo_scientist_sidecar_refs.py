from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_evo_scientist_sidecar_observation"
LATEST_SURFACE_KIND = "mas_evo_scientist_sidecar_latest_projection"
EXECUTION_SURFACE_KIND = "mas_evo_scientist_runtime_sidecar_execution_surface"
SCHEMA_VERSION = 1
RUNTIME_REF_ROOT = Path("artifacts/runtime/evo_scientist_sidecar")
OBSERVATIONS_DIR = RUNTIME_REF_ROOT / "observations"
LATEST_REF = RUNTIME_REF_ROOT / "latest.json"
CONTRACT_REF = "contracts/evo_scientist_progress_accelerator.json"
PROJECTION_REF = (
    "med_autoscience.evo_scientist_learning_projection."
    "build_evo_scientist_learning_projection"
)
WRITER_REF = (
    "med_autoscience.runtime_protocol.evo_scientist_sidecar_refs."
    "write_evo_scientist_sidecar_observation"
)

_OUTPUT_REF_KEYS = (
    "tool_affordance_ref",
    "observation_memory_ref",
    "failed_path_memory_ref",
    "reviewer_briefing_ref",
    "route_hint_ref",
    "stop_loss_candidate_ref",
)

_FORBIDDEN_WRITE_SURFACES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/evidence/evidence_ledger.json",
    "paper/review/review_ledger.json",
    "paper/",
    "manuscript/",
    "paper/manuscript/current_package",
    "manuscript/current_package",
    "current_package.zip",
    "owner_receipt",
    "typed_blocker",
    "stage/current.json",
    "control/current_owner_delta.json",
)


def build_evo_scientist_sidecar_execution_surface() -> dict[str, Any]:
    return {
        "surface_kind": EXECUTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "implementation_status": "repo_callable_worker_landed",
        "execution_model": "nonblocking_refs_only_sidecar_writer",
        "contract_ref": CONTRACT_REF,
        "projection_ref": PROJECTION_REF,
        "writer_ref": WRITER_REF,
        "automatic_hook": (
            "study_progress materialize_read_model_artifacts after current owner action "
            "and current execution envelope are projected"
        ),
        "cli_entrypoints": [
            "medautosci evo-scientist-sidecar observe --study-root <study> --apply",
            "medautosci evo-scientist-sidecar read-latest --study-root <study>",
        ],
        "runtime_ref_root": str(RUNTIME_REF_ROOT),
        "latest_ref": str(LATEST_REF),
        "observation_ref_glob": str(OBSERVATIONS_DIR / "*.json"),
        "refs_only_state_index_family": "evo_scientist_sidecar_ref",
        "implemented_launch_points": [
            "after_current_owner_delta_materialized",
            "after_executor_turn_or_subagent_completion_via_cli",
            "after_receipt_or_typed_blocker_recorded_via_cli",
        ],
        "implemented_outputs": list(_OUTPUT_REF_KEYS),
        "nonblocking_contract": _nonblocking_contract(),
        "authority_boundary": _authority_boundary(),
        "forbidden_write_surfaces": list(_FORBIDDEN_WRITE_SURFACES),
    }


def observe_current_owner_payload(
    *,
    study_root: Path,
    progress_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    current_action = _mapping(progress_payload.get("current_executable_owner_action"))
    current_work_unit = _mapping(progress_payload.get("current_work_unit"))
    execution_envelope = _mapping(progress_payload.get("current_execution_envelope"))
    stage_kernel_projection = _mapping(progress_payload.get("stage_kernel_projection"))
    current_owner_delta_ref = _text(
        _mapping(stage_kernel_projection.get("refs")).get("current_owner_delta_ref")
    )
    event: dict[str, Any] = {
        "event_kind": "current_owner_delta_materialized",
        "source": "study_progress.materialize_read_model_artifacts",
        "study_id": _text(progress_payload.get("study_id")),
        "quest_id": _text(progress_payload.get("quest_id")),
        "active_run_id": _text(progress_payload.get("active_run_id")),
        "current_owner_delta_ref": current_owner_delta_ref,
        "current_owner_action_ref": _text(current_action.get("source_ref")),
        "owner_policy_ref": _text(execution_envelope.get("owner_policy_ref")),
        "current_executable_owner_action": current_action,
        "current_work_unit": current_work_unit,
        "current_execution_envelope": execution_envelope,
    }
    return write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event=event,
        apply=apply,
    )


def write_evo_scientist_sidecar_observation(
    *,
    study_root: Path,
    event: Mapping[str, Any] | None,
    apply: bool = True,
) -> dict[str, Any]:
    try:
        resolved_study_root = Path(study_root).expanduser().resolve()
        event_payload = _mapping(event)
        observed_at = _utc_now()
        if not resolved_study_root.exists():
            return _skipped_projection(
                study_root=resolved_study_root,
                observed_at=observed_at,
                reason="study_root_missing",
                diagnostic={"study_root": str(resolved_study_root)},
            )
        if not _has_observable_input(event_payload):
            return _skipped_projection(
                study_root=resolved_study_root,
                observed_at=observed_at,
                reason="missing_observable_current_owner_or_ref",
                diagnostic={"event_keys": sorted(str(key) for key in event_payload)},
            )

        event_fingerprint = _event_fingerprint(event_payload)
        event_id = f"evo_sidecar_{event_fingerprint[:16]}"
        observation_rel = OBSERVATIONS_DIR / f"{event_id}.json"
        observation_path = resolved_study_root / observation_rel
        latest_path = resolved_study_root / LATEST_REF
        if apply and observation_path.exists():
            existing = _read_json_object(observation_path)
            if existing.get("surface_kind") == SURFACE_KIND:
                written_refs = _sync_latest_ref_if_needed(
                    latest_path=latest_path,
                    observation=existing,
                    latest_ref=str(LATEST_REF),
                )
                return {
                    **existing,
                    "apply": True,
                    "write_status": (
                        "latest_ref_refreshed" if written_refs else "existing_ref_reused"
                    ),
                    "written_refs": written_refs,
                }
        observation = _build_recorded_observation(
            study_root=resolved_study_root,
            event=event_payload,
            observed_at=observed_at,
            event_id=event_id,
            event_fingerprint=event_fingerprint,
            observation_ref=str(observation_rel),
            latest_ref=str(LATEST_REF),
        )
        if apply:
            _write_json(observation_path, observation)
            _write_json(latest_path, observation)
        return {
            **observation,
            "apply": apply,
            "write_status": "written" if apply else "dry_run_no_write",
            "written_refs": [str(observation_rel), str(LATEST_REF)] if apply else [],
        }
    except Exception as exc:  # pragma: no cover - defensive fail-open boundary.
        return _skipped_projection(
            study_root=Path(study_root).expanduser(),
            observed_at=_utc_now(),
            reason="sidecar_writer_exception",
            diagnostic={"exception_type": type(exc).__name__, "message": str(exc)},
        )


def read_latest_evo_scientist_sidecar_projection(*, study_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    latest_path = resolved_study_root / LATEST_REF
    if not latest_path.exists():
        return {
            "surface_kind": LATEST_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "absent",
            "study_root": str(resolved_study_root),
            "latest_ref": str(LATEST_REF),
            "nonblocking_contract": _nonblocking_contract(),
            "authority_boundary": _authority_boundary(),
        }
    try:
        payload = json.loads(latest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "surface_kind": LATEST_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "unreadable",
            "study_root": str(resolved_study_root),
            "latest_ref": str(LATEST_REF),
            "diagnostic": {"exception_type": type(exc).__name__, "message": str(exc)},
            "nonblocking_contract": _nonblocking_contract(),
            "authority_boundary": _authority_boundary(),
        }
    return {
        "surface_kind": LATEST_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "available",
        "study_root": str(resolved_study_root),
        "latest_ref": str(LATEST_REF),
        "observation": _mapping(payload),
        "nonblocking_contract": _nonblocking_contract(),
        "authority_boundary": _authority_boundary(),
    }


def _build_recorded_observation(
    *,
    study_root: Path,
    event: Mapping[str, Any],
    observed_at: str,
    event_id: str,
    event_fingerprint: str,
    observation_ref: str,
    latest_ref: str,
) -> dict[str, Any]:
    event_kind = _text(event.get("event_kind")) or "current_owner_delta_materialized"
    outputs = {
        "tool_affordance_ref": f"{observation_ref}#tool_affordance",
        "observation_memory_ref": f"{observation_ref}#observation_memory",
        "failed_path_memory_ref": f"{observation_ref}#failed_path_memory",
        "reviewer_briefing_ref": f"{observation_ref}#reviewer_briefing",
        "route_hint_ref": f"{observation_ref}#route_hint",
        "stop_loss_candidate_ref": f"{observation_ref}#stop_loss_candidate",
    }
    current_action = _mapping(event.get("current_executable_owner_action"))
    current_work_unit = _mapping(event.get("current_work_unit"))
    execution_envelope = _mapping(event.get("current_execution_envelope"))
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "recorded",
        "event_id": event_id,
        "event_fingerprint": event_fingerprint,
        "observed_at": observed_at,
        "study_root": str(study_root),
        "sidecar_kind": "evo_scientist_progress_accelerator",
        "event_kind": event_kind,
        "source": _text(event.get("source")) or "unknown",
        "contract_ref": CONTRACT_REF,
        "projection_ref": PROJECTION_REF,
        "writer_ref": WRITER_REF,
        "observation_ref": observation_ref,
        "latest_ref": latest_ref,
        "current_owner_delta_ref": _text(event.get("current_owner_delta_ref")),
        "current_owner_action_ref": _text(event.get("current_owner_action_ref")),
        "owner_policy_ref": _text(event.get("owner_policy_ref")),
        "allowed_tool_manifest_ref": _text(event.get("allowed_tool_manifest_ref")),
        "executor_turn_summary_ref": _text(event.get("executor_turn_summary_ref")),
        "subagent_summary_ref": _text(event.get("subagent_summary_ref")),
        "receipt_or_typed_blocker_ref": _text(event.get("receipt_or_typed_blocker_ref")),
        "prior_failed_path_memory_refs": _text_list(event.get("prior_failed_path_memory_refs")),
        "study_id": _text(event.get("study_id")),
        "quest_id": _text(event.get("quest_id")),
        "active_run_id": _text(event.get("active_run_id")),
        "current_owner_summary": _current_owner_summary(
            current_action=current_action,
            current_work_unit=current_work_unit,
            execution_envelope=execution_envelope,
        ),
        "outputs": outputs,
        "nonblocking_contract": _nonblocking_contract(),
        "authority_boundary": _authority_boundary(),
        "forbidden_write_surfaces": list(_FORBIDDEN_WRITE_SURFACES),
        "payload_role": "refs_only_observation",
        "body_included": False,
        "counts_as_paper_progress": False,
        "counts_as_owner_answer": False,
        "can_close_stage": False,
    }


def _current_owner_summary(
    *,
    current_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    execution_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "next_owner": (
            _text(current_action.get("next_owner"))
            or _text(current_action.get("owner"))
            or _text(execution_envelope.get("next_owner"))
        ),
        "action_type": _text(current_action.get("action_type")),
        "work_unit_id": (
            _text(current_action.get("work_unit_id"))
            or _text(current_work_unit.get("work_unit_id"))
            or _text(current_work_unit.get("id"))
        ),
        "work_unit_fingerprint": (
            _text(current_action.get("work_unit_fingerprint"))
            or _text(current_work_unit.get("work_unit_fingerprint"))
            or _text(execution_envelope.get("work_unit_fingerprint"))
        ),
        "envelope_state_kind": _text(execution_envelope.get("state_kind")),
        "status": _text(current_action.get("status")) or _text(current_work_unit.get("status")),
        "source": _text(current_action.get("source")),
    }


def _skipped_projection(
    *,
    study_root: Path,
    observed_at: str,
    reason: str,
    diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "skipped",
        "observed_at": observed_at,
        "study_root": str(study_root),
        "sidecar_kind": "evo_scientist_progress_accelerator",
        "reason": reason,
        "diagnostic": dict(diagnostic),
        "apply": False,
        "write_status": "skipped_no_write",
        "written_refs": [],
        "nonblocking_contract": _nonblocking_contract(),
        "authority_boundary": _authority_boundary(),
        "forbidden_write_surfaces": list(_FORBIDDEN_WRITE_SURFACES),
        "body_included": False,
        "counts_as_paper_progress": False,
        "counts_as_owner_answer": False,
        "can_close_stage": False,
    }


def _nonblocking_contract() -> dict[str, bool]:
    return {
        "mainline_waits_for_sidecar": False,
        "failure_blocks_current_owner_action": False,
        "timeout_blocks_current_owner_action": False,
        "budget_exhaustion_blocks_current_owner_action": False,
        "sidecar_completion_required_for_dispatch": False,
        "sidecar_completion_required_for_quality_gate": False,
        "sidecar_completion_required_for_artifact_mutation": False,
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_evidence_ledger": False,
        "can_write_review_ledger": False,
        "can_write_memory_body": False,
        "can_write_artifact_body": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_authorize_current_owner_action": False,
        "can_authorize_source_readiness": False,
        "can_authorize_publication_quality": False,
        "can_authorize_artifact_authority": False,
        "can_close_quality_gate": False,
        "can_close_stage": False,
    }


def _has_observable_input(event: Mapping[str, Any]) -> bool:
    return any(
        value
        for value in (
            _text(event.get("current_owner_delta_ref")),
            _text(event.get("current_owner_action_ref")),
            _text(event.get("receipt_or_typed_blocker_ref")),
            _mapping(event.get("current_executable_owner_action")),
            _mapping(event.get("current_work_unit")),
        )
    )


def _event_fingerprint(event: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(event, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(rendered, encoding="utf-8")
    tmp_path.replace(path)


def _sync_latest_ref_if_needed(
    *,
    latest_path: Path,
    observation: Mapping[str, Any],
    latest_ref: str,
) -> list[str]:
    latest = _read_json_object(latest_path)
    if latest.get("event_id") == observation.get("event_id"):
        return []
    _write_json(latest_path, observation)
    return [latest_ref]


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if isinstance(value, Path):
        text = str(value)
    else:
        text = str(value or "")
    stripped = text.strip()
    return stripped or None


def _text_list(value: object) -> list[str]:
    if isinstance(value, (str, Path)):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple)):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "CONTRACT_REF",
    "EXECUTION_SURFACE_KIND",
    "LATEST_REF",
    "LATEST_SURFACE_KIND",
    "OBSERVATIONS_DIR",
    "PROJECTION_REF",
    "RUNTIME_REF_ROOT",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "WRITER_REF",
    "build_evo_scientist_sidecar_execution_surface",
    "observe_current_owner_payload",
    "read_latest_evo_scientist_sidecar_projection",
    "write_evo_scientist_sidecar_observation",
]
