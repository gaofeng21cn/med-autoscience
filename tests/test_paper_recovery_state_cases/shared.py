from __future__ import annotations

import importlib


def _module():
    return importlib.import_module("med_autoscience.controllers.paper_recovery_state")


def _typed_blocker_work_unit(
    *,
    study_id: str = "002-dm-cvd-mortality-risk",
    owner: str = "one-person-lab",
    action_type: str = "run_gate_clearing_batch",
    work_unit_id: str = "publication_gate_replay",
    blocker_type: str = "stage_packet_not_current_selected_dispatch",
) -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": owner,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "state": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": blocker_type,
                "owner": owner,
                "action_type": action_type,
                "work_unit_id": work_unit_id,
            },
        },
    }


def _executable_work_unit(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    owner: str = "write",
    action_type: str = "run_quality_repair_batch",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
) -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": owner,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }
