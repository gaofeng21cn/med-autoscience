from __future__ import annotations

from .shared import *

def test_execute_dispatch_materializes_revision_rebuttal_loop_from_review_and_ledger_sources(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_readiness_surfaces_before_revision_rebuttal(study_root)
    _write_revision_rebuttal_loop_sources(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="revision_rebuttal_loop")
    _attach_readiness_closeout_binding(dispatch, study_id=study_id)
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
    assert execution["owner_result"]["completed_surface_key"] == "revision_rebuttal_loop"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "publication_eval_review_and_evidence_ledgers"
    )
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "start_revision_rebuttal_loop"
    assert action_result["status"] == "ready"
    artifact_path = study_root / "artifacts" / "medical_paper" / "revision_rebuttal_loop.json"
    projection = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert projection["surface"] == "revision_rebuttal_loop"
    assert projection["status"] == "ready"
    assert projection["reviewer_comment_count"] >= 1
    assert projection["durable_refs"]["review_ledger_refs"] == [
        str(study_root / "paper" / "review" / "review_ledger.json")
    ]
    assert projection["durable_refs"]["evidence_ledger_refs"] == [
        str(study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper" / "evidence_ledger.json"),
        str(study_root / "paper" / "claim_evidence_map.json"),
    ]
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["revision_rebuttal_loop"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "authoring_runtime_authorization"

def test_execute_dispatch_materializes_authoring_runtime_authorization_from_paper_sources(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_readiness_surfaces_before_revision_rebuttal(study_root)
    _write_revision_rebuttal_loop_sources(study_root)
    _write_revision_rebuttal_loop_surface(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="authoring_runtime_authorization")
    _attach_readiness_closeout_binding(dispatch, study_id=study_id)
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
    assert execution["blocked_reason"] == "publication_eval_not_ai_reviewer_owned"
    assert execution["owner_result"]["completed_surface_key"] == "authoring_runtime_authorization"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "target_journal_layer_publication_eval_and_ledgers"
    )
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "authorize_manuscript_drafting"
    assert action_result["status"] == "blocked"
    artifact_path = study_root / "artifacts" / "medical_paper" / "authoring_runtime_authorization.json"
    projection = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert projection["surface"] == "ai_reviewer_journal_writing_authorization"
    assert projection["full_drafting_authorized"] is False
    assert projection["required_refs"]["evidence_ledger_ref"] == (
        "artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/evidence_ledger.json"
    )
    assert projection["required_refs"]["review_ledger_ref"] == "paper/review/review_ledger.json"
    assert "publication_eval_not_ai_reviewer_owned" in projection["blockers"]
    assert "claim_to_paragraph_map_evidence_ref_outside_ledger:C1" not in projection["blockers"]
    assert "claim_to_paragraph_map_review_ref_outside_ledger:C1" not in projection["blockers"]
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["authoring_runtime_authorization"]["status"] == "blocked"
    assert by_key["authoring_runtime_authorization"]["missing_reason"] == "publication_eval_not_ai_reviewer_owned"
    assert readiness["next_action"]["surface_key"] == "authoring_runtime_authorization"

def test_execute_dispatch_dry_run_projects_authored_revision_rebuttal_loop_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_readiness_surfaces_before_revision_rebuttal(study_root)
    _write_revision_rebuttal_loop_sources(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="revision_rebuttal_loop")
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=False,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "revision_rebuttal_loop"
    assert execution["owner_result"]["operator_payload_authoring"]["status"] == "ready"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["status"] == "ready"
    assert action_result["dry_run"] is True
    assert not (study_root / "artifacts" / "medical_paper" / "revision_rebuttal_loop.json").exists()
