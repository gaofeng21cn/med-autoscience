from typing import Any


def opl_stage_attempt_readback(
    study_id: str,
    *,
    action_fingerprint: str,
    work_unit_id: str,
    route_identity_key: str | None = None,
    attempt_idempotency_key: str | None = None,
    request_idempotency_key: str | None = None,
    stage_run_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    return {
        "surface_kind": "opl_stage_attempt_readback",
        "status": "running",
        "stage_attempt_ref": f"opl://attempt/{stage_run_id or action_fingerprint}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "identity": {
            "stage_run_id": stage_run_id or f"stage-run::{study_id}::{work_unit_id}",
            "route_identity_key": route_identity_key,
            "attempt_idempotency_key": attempt_idempotency_key,
            "request_idempotency_key": request_idempotency_key,
        },
    }
