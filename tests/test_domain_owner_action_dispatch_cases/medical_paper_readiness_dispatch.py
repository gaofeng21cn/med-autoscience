from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_json as _write_json,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_literature_provider_runtime import _complete_provider_payload


ACTION_TYPE = "complete_medical_paper_readiness_surface"


def _readiness_dispatch(*, study_id: str) -> dict[str, object]:
    dispatch = _dispatch(
        study_id=study_id,
        action_type=ACTION_TYPE,
        owner="MedAutoScience",
        required_output_surface=(
            "artifacts/medical_paper/<surface_key>.json or "
            "typed blocker:medical_paper_readiness_surface_input_required"
        ),
    )
    dispatch["surface_key"] = "literature_provider_runtime"
    dispatch["prompt_contract"]["surface_key"] = "literature_provider_runtime"
    return dispatch


def _write_readiness_dispatch(study_root: Path, profile, dispatch: dict[str, object]) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)


def test_execute_dispatch_blocks_readiness_surface_completion_without_provider_payload(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_readiness_dispatch(study_root, profile, _readiness_dispatch(study_id=study_id))

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    assert execution["owner_callable_surface"] == "medical_paper_readiness.complete_medical_paper_readiness_surface"
    decision = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    assert decision["decision_type"] == "medical_paper_readiness_owner_blocker"
    assert decision["quality_claim_authorized"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_materializes_provider_payload_for_readiness_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch["operator_payload"] = _complete_provider_payload()
    dispatch["prompt_contract"]["operator_payload"] = _complete_provider_payload()
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_callable_surface"] == "medical_paper_readiness.complete_medical_paper_readiness_surface"
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["surface"] == "literature_provider_runtime"
    assert provider_surface["status"] == "ready"
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_provider_runtime"]["status"] == "present"
    assert readiness["quality_claim_authorized"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_materializes_provider_payload_from_readiness_request_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    _write_json(
        study_root / request_ref,
        {
            "surface": "supervisor_request_handoff_packet",
            "action_type": ACTION_TYPE,
            "surface_key": "literature_provider_runtime",
            "operator_payload": _complete_provider_payload(),
            "payload_authoring_target": {
                "surface": "medical_paper_readiness_operator_payload_authoring_target",
                "surface_key": "literature_provider_runtime",
                "operator_payload": _complete_provider_payload(),
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch["operator_payload_ref"] = request_ref
    dispatch["medical_paper_readiness_payload_ref"] = request_ref
    dispatch["prompt_contract"]["operator_payload_ref"] = request_ref
    dispatch["prompt_contract"]["medical_paper_readiness_payload_ref"] = request_ref
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "literature_provider_runtime"
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["surface"] == "literature_provider_runtime"
    assert provider_surface["status"] == "ready"
