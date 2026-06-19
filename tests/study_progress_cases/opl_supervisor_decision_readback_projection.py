from __future__ import annotations

import importlib
import json
from pathlib import Path

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _supervisor_decision_readback(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    fingerprint: str,
    decision_kind: str = "stop_with_stable_typed_blocker",
) -> dict[str, object]:
    obligation_id = (
        f"paper-recovery::{study_id}::{action_type}::{work_unit_id}::{fingerprint}"
    )
    return {
        "surface_kind": "opl_paper_autonomy_supervisor_decision_readback",
        "obligation_id": obligation_id,
        "decision_id": f"{obligation_id}|{decision_kind}|stage-run-003",
        "decision_kind": decision_kind,
        "status": "decision_ready_for_identity_bound_transition",
        "domain_truth_owner": "med-autoscience",
        "substrate_owner": "one-person-lab",
        "current_identity": {
            "stage_run_id": "stage-run-003",
            "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
            "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
            "work_unit_fingerprint": fingerprint,
            "stage_packet_ref": "stage-packet:003",
            "provider_attempt_ref": "provider-attempt:003",
        },
        "typed_blocker_ref": "typed-blocker:003",
        "evidence_refs": ["typed-blocker:003", "stage-run-003"],
        "authority_boundary": {
            "read_model_can_execute": False,
            "observability_can_close_owner_answer": False,
            "opl_can_write_mas_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_domain_typed_blocker": False,
            "provider_completion_is_domain_ready": False,
        },
    }


def _write_supervisor_decision_ledger(
    state_root: Path,
    *,
    readback: dict[str, object],
    recorded_at: str = "2026-06-19T00:00:00.000Z",
) -> Path:
    current_identity = dict(readback["current_identity"])
    ledger_path = (
        state_root
        / "family-runtime"
        / "paper-autonomy"
        / "supervisor"
        / "supervisor-decisions.jsonl"
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "surface_kind": "opl_paper_autonomy_supervisor_decision_ledger_entry",
        "entry_kind": "supervisor_decision_appended",
        "obligation_id": readback["obligation_id"],
        "current_identity": current_identity,
        "decision": readback,
        "decision_id": readback["decision_id"],
        "decision_kind": readback["decision_kind"],
        "reason": None,
        "recorded_at": recorded_at,
        "projection": {
            "append_only_jsonl_compatible": True,
            "payload_refs_only": True,
            "identity_bound": True,
            "current_latest_by_identity": True,
        },
        "authority_boundary": {
            "opl_can_write_mas_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_domain_typed_blocker": False,
            "provider_completion_is_domain_ready": False,
        },
    }
    ledger_path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")
    return ledger_path


def test_study_progress_consumes_opl_supervisor_decision_readback_ledger(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    opl_state_root = tmp_path / "opl-state"
    monkeypatch.setenv("OPL_STATE_DIR", str(opl_state_root))
    readback = _supervisor_decision_readback(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    ledger_path = _write_supervisor_decision_ledger(opl_state_root, readback=readback)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "blocked",
            "decision": "domain_blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {},
            "authority_snapshot": {},
            "progress_projection": {
                "schema_version": 1,
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "paper_recovery_state": {
                    "surface_kind": "paper_recovery_state",
                    "phase": "domain_blocked",
                    "supervisor_decision": {
                        "surface_kind": "paper_progress_policy_result_projection",
                        "decision": "opl_supervisor_decision_readback_required",
                        "requires_opl_supervisor_decision_engine_readback": True,
                    },
                },
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    decision = result["paper_recovery_state"]["supervisor_decision"]
    assert decision["decision"] == "stop_with_stable_typed_blocker"
    assert decision["opl_supervisor_decision_engine_readback_consumed"] is True
    assert decision["opl_supervisor_decision_readback_ref"] == readback["decision_id"]
    assert result["paper_autonomy_supervisor_decision"] == decision
    assert result["opl_paper_autonomy_supervisor_decision_readback"] == readback
    assert result["refs"]["opl_paper_autonomy_supervisor_decision_ledger_path"] == str(
        ledger_path
    )
    assert result["refs"]["opl_paper_autonomy_supervisor_decision_readback_ref"] == (
        readback["decision_id"]
    )
    assert result["provider_admission_pending_count"] == 0


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
