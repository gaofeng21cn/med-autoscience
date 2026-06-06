from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study


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
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["surface_key"] = "literature_provider_runtime"
    return dispatch


def _write_readiness_dispatch(study_root: Path, profile, dispatch: dict[str, object]) -> Path:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    return dispatch_path


def _readiness_closeout_binding_env(*, study_id: str) -> dict[str, str]:
    source_fingerprint = f"truth-source::{study_id}::{ACTION_TYPE}"
    return {
        "OPL_STAGE_RUN_ID": f"stage-run::{study_id}::domain_owner/default-executor-dispatch",
        "OPL_STAGE_MANIFEST_REF": (
            "artifacts/supervision/consumer/stage_manifests/"
            "domain_owner_default_executor_dispatch.json"
        ),
        "OPL_CURRENT_POINTER_REF": (
            "artifacts/supervision/consumer/current_pointers/"
            "domain_owner_default_executor_dispatch.json"
        ),
        "OPL_PROVIDER_ATTEMPT_REF": f"opl://stage-attempts/{study_id}/{ACTION_TYPE}",
        "OPL_ATTEMPT_LEASE_REF": f"opl://stage-attempts/{study_id}/{ACTION_TYPE}/leases/current",
        "OPL_ATTEMPT_LEASE_STATUS": "active",
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF": (
            f"opl://stage-attempts/{study_id}/{ACTION_TYPE}/execution-authorizations/current"
        ),
        "OPL_SOURCE_FINGERPRINT": source_fingerprint,
        "OPL_IDEMPOTENCY_KEY": f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience",
    }


def test_readiness_owner_delta_carries_closeout_binding_from_provider_env(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    for key, value in _readiness_closeout_binding_env(study_id=study_id).items():
        monkeypatch.setenv(key, value)
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch.pop("closeout_binding", None)
    dispatch.pop("opl_execution_authorization", None)
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract.pop("closeout_binding", None)
    prompt_contract.pop("opl_execution_authorization", None)
    dispatch_path = _write_readiness_dispatch(study_root, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", f"stage-attempt::{study_id}::{ACTION_TYPE}")
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", ACTION_TYPE)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_delta = result["executions"][0]["owner_delta_result"]
    binding = owner_delta["closeout_binding"]
    assert result["blocked_count"] == 1
    assert owner_delta["result_kind"] == "stable_typed_blocker"
    assert binding["stage_run_id"] == f"stage-run::{study_id}::domain_owner/default-executor-dispatch"
    assert binding["stage_manifest_ref"] == (
        "artifacts/supervision/consumer/stage_manifests/"
        "domain_owner_default_executor_dispatch.json"
    )
    assert binding["current_pointer_ref"] == (
        "artifacts/supervision/consumer/current_pointers/"
        "domain_owner_default_executor_dispatch.json"
    )
    assert binding["provider_attempt_ref"] == f"opl://stage-attempts/{study_id}/{ACTION_TYPE}"
    assert binding["attempt_lease_status"] == "active"
    assert binding["trusted_opl_execution_authorization"] is True
    assert owner_delta["idempotency_key"] == f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience"
    assert owner_delta["body_included"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
