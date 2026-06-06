from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from med_autoscience.controllers.stage_artifact_materializer import materialize_stage_artifact_delta


def _remove_opl_execution_authorization(dispatch: dict[str, object]) -> None:
    dispatch.pop("opl_execution_authorization", None)
    prompt_contract = dispatch.get("prompt_contract")
    if isinstance(prompt_contract, dict):
        prompt_contract.pop("opl_execution_authorization", None)


def test_provider_hosted_stage_attempt_identity_authorizes_publication_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(study_root / "study.yaml", {"study_id": study_id})
    materialize_stage_artifact_delta(
        study_id=study_id,
        study_root=study_root,
        workspace_root=profile.workspace_root,
        apply=True,
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
        required_output_surface=(
            "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
            "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ),
    )
    _remove_opl_execution_authorization(dispatch)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "publication_handoff_owner_gate"
        / "provider-hosted.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-provider-hosted-publication")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "opl://stage-attempts/sat-provider-hosted-publication")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat-provider-hosted-publication/leases/frt-provider-hosted-publication/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat-provider-hosted-publication/execution-authorizations/frt-provider-hosted-publication/wf-provider-hosted-publication",
    )
    monkeypatch.setenv("OPL_SOURCE_FINGERPRINT", "mas_default_executor_source_provider_hosted_publication")
    monkeypatch.setenv("OPL_IDEMPOTENCY_KEY", "idem_provider_hosted_publication")
    monkeypatch.setenv("OPL_WORKFLOW_ID", "wf-provider-hosted-publication")
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "publication_handoff_owner_gate")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", "publication_handoff_owner_gate")
    monkeypatch.setenv("OPL_TASK_ID", "frt-provider-hosted-publication")

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_handoff_owner_gate",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    blocker_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_missing"
    assert blocker_path.is_file()
    blocker = json.loads(blocker_path.read_text(encoding="utf-8"))
    assert blocker["closeout_binding"]["provider_attempt_ref"] == (
        "opl://stage-attempts/sat-provider-hosted-publication"
    )
    assert blocker["closeout_binding"]["attempt_lease_ref"] == (
        "opl://stage-attempts/sat-provider-hosted-publication/leases/frt-provider-hosted-publication/active"
    )
    assert blocker["closeout_binding"]["attempt_lease_status"] == "active"
    assert blocker["closeout_binding"]["execution_authorization_decision_ref"] == (
        "opl://stage-attempts/sat-provider-hosted-publication/execution-authorizations/frt-provider-hosted-publication/wf-provider-hosted-publication"
    )
    assert blocker["closeout_binding"]["source_fingerprint"] == (
        "mas_default_executor_source_provider_hosted_publication"
    )
    assert blocker["closeout_binding"]["idempotency_key"] == "idem_provider_hosted_publication"
    assert blocker["closeout_binding"]["trusted_opl_execution_authorization"] is True
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
