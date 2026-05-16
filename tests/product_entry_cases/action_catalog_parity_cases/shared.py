from __future__ import annotations

import importlib
import json

from ..shared import *  # noqa: F403,F401


def _write_opl_production_proof(path: Path) -> None:
    checks = {
        "external_temporal_server_reachable": True,
        "managed_worker_ready": True,
        "worker_completed_attempt": True,
        "worker_restart_requery": True,
        "signal_history_preserved": True,
        "typed_closeout_required_for_completed": True,
        "missing_closeout_blocks_completion": True,
        "retry_or_dead_letter_boundary_observed": True,
        "domain_truth_boundary_preserved": True,
    }
    path.write_text(
        json.dumps(
            {
                "family_runtime_residency_proof": {
                    "surface_kind": "opl_temporal_production_residency_proof",
                    "provider_kind": "temporal",
                    "closeout_status": "production_residency_proven",
                    "production_residency_proof": {
                        "surface_kind": "opl_temporal_external_production_residency_proof",
                        "provider_kind": "temporal",
                        "closeout_status": "production_residency_proven",
                        "runtime_snapshot": {
                            "address_source": "managed_local_service_state",
                            "lifecycle_status": "ready",
                            "server_reachable": True,
                            "worker_ready": True,
                            "task_queue": "opl-stage-attempts",
                        },
                        "proof_receipt": {
                            "receipt_kind": "temporal_production_residency_proof",
                            "receipt_status": "proven",
                            "completed_workflow_id": "wf-complete",
                            "blocked_workflow_id": "wf-blocked",
                        },
                        "checks": checks,
                    },
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


__all__ = [name for name in globals() if not name.startswith("__")]
