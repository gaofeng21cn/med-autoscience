from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _paper_recovery_state(study_id: str, quest_id: str) -> dict[str, object]:
    return {
        "phase": "owner_action_ready",
        "current_authority": {
            "owner": "MedAutoScience",
            "obligation": {
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": "legacy-paper-recovery::fingerprint",
                "blocker_type": "medical_paper_readiness_missing",
            },
        },
        "supervisor_decision": {
            "decision": "materialize_recovery_action",
            "decision_id": "supervisor-decision::legacy-paper-recovery",
        },
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "MedAutoScience",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "callable_surface": "medical_paper_readiness.complete_medical_paper_readiness_surface",
            },
        },
    }


def test_paper_recovery_owner_callable_without_next_action_envelope_does_not_materialize_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "paper_recovery_state": _paper_recovery_state(study_id, quest_id),
                    "action_queue": [],
                }
            ],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["domain_progress_transition_requests"] == []
    assert result["domain_progress_transition_request_count"] == 0


def test_fresh_progress_paper_recovery_without_next_action_envelope_does_not_materialize_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {"surface": "opl_current_control_state_handoff", "schema_version": 1, "studies": [], "action_queue": []},
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "paper_recovery_state": _paper_recovery_state(study_id, quest_id),
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["domain_progress_transition_requests"] == []
    assert result["domain_progress_transition_request_count"] == 0
