from __future__ import annotations

from .shared import *

def test_execute_dispatch_authors_study_line_selection_from_study_literature_and_stage_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        quest_id=study_id,
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_phenotype_treatment_gap",
        paper_framing_summary="DPCC primary-care diabetes phenotype treatment gap study.",
    )
    _write_ready_literature_intelligence(study_root)
    literature_module = importlib.import_module("med_autoscience.controllers.literature_provider_runtime")
    literature_module.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=_complete_provider_payload(),
    )
    _write_stage_output_owner_receipt(study_root, "01-study_intake")
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="study_line_selection")
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
    assert execution["owner_result"]["completed_surface_key"] == "study_line_selection"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "study_metadata_literature_and_stage_refs"
    )
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_study_line_selection"
    assert action_result["status"] == "present"
    line_decision = json.loads(
        (study_root / "artifacts" / "medical_paper" / "study_line_decision.json").read_text(encoding="utf-8")
    )
    assert line_decision["surface"] == "study_line_decision_engine"
    assert line_decision["status"] == "selected"
    assert line_decision["selected_line_id"] == study_id
    assert line_decision["quality_claim_authorized"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["study_line_selection"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "archetype_analysis_contract"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_execute_dispatch_materializes_target_journal_writing_layer_from_existing_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_target_journal_writing_layer(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="target_journal_writing_layer")
    binding = _attach_readiness_closeout_binding(dispatch, study_id=study_id)
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
    assert execution["owner_result"]["completed_surface_key"] == "target_journal_writing_layer"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_target_journal_writing_layer"
    assert action_result["surface_key"] == "target_journal_writing_layer"
    assert action_result["status"] == "present"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "quality_gate_receipt_with_stable_typed_blocker"
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    target_layer = json.loads((study_root / "paper" / "target_journal_writing_layer.json").read_text(encoding="utf-8"))
    assert target_layer["surface"] == "target_journal_writing_layer"
    assert target_layer["target_journal_family"] == "general_internal_medicine"
    assert target_layer["quality_claim_authorized"] is False
    assert target_layer["mechanical_projection_can_authorize_quality"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["target_journal_writing_layer"]["status"] == "present"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper" / "submission_minimal" / "current_package").exists()

def test_execute_dispatch_authors_target_journal_layer_from_structured_writing_sources(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_target_journal_source_surfaces(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="target_journal_writing_layer")
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
    assert execution["owner_result"]["completed_surface_key"] == "target_journal_writing_layer"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "structured_writing_context_sources"
    )
    target_layer = json.loads((study_root / "paper" / "target_journal_writing_layer.json").read_text(encoding="utf-8"))
    assert target_layer["surface"] == "target_journal_writing_layer"
    assert target_layer["target_journal_family"] == "general_internal_medicine"
    assert target_layer["claim_to_paragraph_map"][0]["claim_id"] == "primary_mortality_claim"
    assert target_layer["display_to_claim_map"][0]["display_id"] == "T2"
    assert target_layer["quality_claim_authorized"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["target_journal_writing_layer"]["status"] == "present"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper" / "submission_minimal" / "current_package").exists()

def test_execute_dispatch_materializes_real_study_soak_matrix_evidence_from_stage_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_complete_soak_stage_refs(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="real_study_soak_matrix_evidence")
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
    assert execution["owner_result"]["completed_surface_key"] == "real_study_soak_matrix_evidence"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "real_study_soak_matrix_evidence_builder"
    )
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_real_study_soak_matrix_evidence"
    assert action_result["status"] == "present"
    evidence_path = study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["surface"] == "real_study_soak_matrix_evidence"
    assert evidence["overall_status"] == "complete"
    assert evidence["quality_claim_authorized"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["real_study_soak_matrix_evidence"]["status"] == "present"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
