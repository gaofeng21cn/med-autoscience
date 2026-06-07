from __future__ import annotations

from .shared import *

def test_execute_dispatch_blocks_readiness_surface_completion_without_provider_payload(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _readiness_dispatch(study_id=study_id)
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
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    assert execution["owner_callable_surface"] == "medical_paper_readiness.complete_medical_paper_readiness_surface"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "stable_typed_blocker"
    assert owner_delta["required_return_shape_satisfied"] is True
    assert owner_delta["owner_receipt_refs"] == []
    assert owner_delta["quality_gate_receipt_refs"] == []
    assert owner_delta["stable_typed_blocker_refs"] == [
        str(study_root / "artifacts" / "controller_decisions" / "latest.json")
    ]
    assert owner_delta["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"
    assert owner_delta["body_included"] is False
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert owner_delta["closeout_binding"]["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_delta["closeout_binding"]["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_delta["closeout_binding"]["source_fingerprint"] == binding["source_fingerprint"]
    assert owner_delta["closeout_binding"]["idempotency_key"] == (
        f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience"
    )
    assert owner_delta["stage_run_id"] == binding["stage_run_id"]
    assert owner_delta["source_fingerprint"] == binding["source_fingerprint"]
    assert owner_delta["body_included"] is False
    decision = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    assert decision["decision_type"] == "medical_paper_readiness_owner_blocker"
    assert decision["quality_claim_authorized"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_apply_without_opl_authorization_hands_readiness_action_to_provider(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _readiness_dispatch(study_id=study_id)
    _drop_opl_execution_authorization(dispatch)
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    assert execution["execution_status"] == "handoff_ready"
    assert execution["owner_callable_surface"] == "opl_default_executor.stage_attempt"
    assert execution["blocked_reason"] is None
    assert execution["will_start_llm"] is True
    assert execution["provider_attempt_or_lease_required"] is True
    assert execution["provider_completion_is_domain_completion"] is False
    assert execution["dispatch_path"].endswith(
        "artifacts/supervision/consumer/default_executor_dispatches/complete_medical_paper_readiness_surface.json"
    )
    assert not (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").exists()
    assert not (study_root / "artifacts" / "medical_paper" / "owner_blocker.json").exists()

def test_execute_dispatch_authors_provider_runtime_from_verified_materialization_when_pubmed_fetch_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    pubmed = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    semantic = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(pubmed, "fetch_pubmed_summary", lambda **_: [])
    monkeypatch.setattr(
        semantic,
        "fetch_paper_batch",
        lambda **_: {
            "payload": [
                {
                    "paperId": "S2PAPER1",
                    "title": "Semantic Scholar neighbor",
                    "year": 2025,
                    "venue": "JAMA Internal Medicine",
                    "externalIds": {"DOI": "10.1038/s43856-023-00360-3"},
                    "citationCount": 80,
                }
            ],
            "response_status": "ok",
            "rate_limit_status": {
                "status": "ok",
                "remaining": 10,
                "reset_at": "",
                "backoff": {"policy": "exponential", "retry_after_seconds": 0},
            },
        },
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_literature_materialization(study_root)
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
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    authoring = execution["owner_result"]["operator_payload_authoring"]
    assert authoring["source_basis"] == "verified_literature_materialization"
    assert authoring["quality_claim_authorized"] is False
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["status"] == "ready"
    assert provider_surface["provider_provenance"][0]["provider_name"] == "pubmed"
    assert provider_surface["provider_response_ledger_refs"][0] == (
        "artifacts/medical_paper/provider_responses/"
        "pubmed-verified-literature-materialization-41469089-37798471.json"
    )
    assert provider_surface["literature_intelligence_payload"]["source_basis"] == "verified_literature_materialization"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_execute_dispatch_blocks_when_existing_literature_intelligence_is_not_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_ready_literature_intelligence(study_root)
    literature_path = study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json"
    payload = json.loads(literature_path.read_text(encoding="utf-8"))
    payload["status"] = "draft"
    literature_path.write_text(json.dumps(payload), encoding="utf-8")
    _write_readiness_dispatch(study_root, profile, _readiness_dispatch(study_id=study_id))

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    authoring = execution["owner_result"]["operator_payload_authoring"]
    assert authoring["status"] == "blocked"
    assert authoring["blocked_reason"] == "insufficient_literature_provider_payload_sources"
    assert not (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").exists()

def test_execute_dispatch_authors_provider_payload_from_live_provider_adapters(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    pubmed = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    crossref = importlib.import_module("med_autoscience.adapters.literature.doi")
    semantic = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    records = importlib.import_module("med_autoscience.literature_records")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")

    def _record(*, pmid: str | None, doi: str, title: str):
        return records.LiteratureRecord(
            record_id=f"pmid:{pmid}" if pmid else f"doi:{doi}",
            title=title,
            authors=("Example Author",),
            year=2025,
            journal="Example Journal",
            doi=doi,
            pmid=pmid,
            pmcid=None,
            arxiv_id=None,
            abstract=None,
            full_text_availability="metadata_only",
            source_priority=2,
            citation_payload={"source": "test"},
            local_asset_paths=(),
            relevance_role="candidate",
            claim_support_scope=(),
        )

    monkeypatch.setattr(
        pubmed,
        "fetch_pubmed_summary",
        lambda **_: [
            _record(
                pmid="41469089",
                doi="10.1136/fmch-2025-003765",
                title="Guidelines on primary healthcare for type 2 diabetes in China, 2025",
            ),
            _record(
                pmid="37798471",
                doi="10.1038/s43856-023-00360-3",
                title="Precision subclassification of type 2 diabetes: a systematic review",
            ),
        ],
    )
    monkeypatch.setattr(
        crossref,
        "fetch_crossref_work",
        lambda doi: _record(
            pmid=None,
            doi=doi,
            title=(
                "Guidelines on primary healthcare for type 2 diabetes in China, 2025"
                if doi == "10.1136/fmch-2025-003765"
                else "Precision subclassification of type 2 diabetes: a systematic review"
            ),
        ),
    )
    monkeypatch.setattr(
        semantic,
        "fetch_paper_batch",
        lambda **_: {
            "payload": [
                {
                    "paperId": "S2PAPER1",
                    "title": "Semantic Scholar neighbor",
                    "year": 2025,
                    "venue": "JAMA Internal Medicine",
                    "externalIds": {"DOI": "10.1038/s43856-023-00360-3"},
                    "citationCount": 80,
                }
            ],
            "response_status": "ok",
            "rate_limit_status": {
                "status": "ok",
                "remaining": 10,
                "reset_at": "",
                "backoff": {"policy": "exponential", "retry_after_seconds": 0},
            },
        },
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_literature_materialization(study_root)
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
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["status"] == "ready"
    assert provider_surface["providers"] == ["pubmed", "crossref", "semantic_scholar"]
    assert provider_surface["provider_response_ledger_refs"] == [
        "artifacts/medical_paper/provider_responses/pubmed-esummary-41469089-37798471.json",
        (
            "artifacts/medical_paper/provider_responses/"
            "crossref-works-10-1136-fmch-2025-003765-10-1038-s43856-023-00360-3.json"
        ),
        "artifacts/medical_paper/provider_responses/semantic-scholar-doi-10-1038-s43856-023-00360-3.json",
    ]
    assert (
        study_root / "artifacts" / "medical_paper" / "provider_responses" / "pubmed-esummary-41469089-37798471.json"
    ).is_file()
    assert provider_surface["quality_claim_authorized"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_execute_dispatch_blocks_when_semantic_provider_fetch_raises(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    pubmed = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    crossref = importlib.import_module("med_autoscience.adapters.literature.doi")
    semantic = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    records = importlib.import_module("med_autoscience.literature_records")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")

    def _record(*, pmid: str | None, doi: str, title: str):
        return records.LiteratureRecord(
            record_id=f"pmid:{pmid}" if pmid else f"doi:{doi}",
            title=title,
            authors=("Example Author",),
            year=2025,
            journal="Example Journal",
            doi=doi,
            pmid=pmid,
            pmcid=None,
            arxiv_id=None,
            abstract=None,
            full_text_availability="metadata_only",
            source_priority=2,
            citation_payload={"source": "test"},
            local_asset_paths=(),
            relevance_role="candidate",
            claim_support_scope=(),
        )

    monkeypatch.setattr(
        pubmed,
        "fetch_pubmed_summary",
        lambda **_: [
            _record(
                pmid="41469089",
                doi="10.1136/fmch-2025-003765",
                title="Guidelines on primary healthcare for type 2 diabetes in China, 2025",
            ),
            _record(
                pmid="37798471",
                doi="10.1038/s43856-023-00360-3",
                title="Precision subclassification of type 2 diabetes: a systematic review",
            ),
        ],
    )
    monkeypatch.setattr(
        crossref,
        "fetch_crossref_work",
        lambda doi: _record(
            pmid=None,
            doi=doi,
            title=(
                "Guidelines on primary healthcare for type 2 diabetes in China, 2025"
                if doi == "10.1136/fmch-2025-003765"
                else "Precision subclassification of type 2 diabetes: a systematic review"
            ),
        ),
    )

    def _raise_semantic(**_):
        raise RuntimeError("semantic provider unavailable")

    monkeypatch.setattr(semantic, "fetch_paper_batch", _raise_semantic)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_literature_materialization(study_root)
    _write_readiness_dispatch(study_root, profile, _readiness_dispatch(study_id=study_id))

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    authoring = execution["owner_result"]["operator_payload_authoring"]
    assert authoring["status"] == "blocked"
    assert authoring["blocked_reason"] == "provider_adapter_fetch_failed_semantic_scholar"
    assert not (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").exists()

def test_execute_dispatch_tries_next_semantic_record_when_first_is_rate_limited(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    pubmed = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    crossref = importlib.import_module("med_autoscience.adapters.literature.doi")
    semantic = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    records = importlib.import_module("med_autoscience.literature_records")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")

    def _record(*, pmid: str | None, doi: str, title: str):
        return records.LiteratureRecord(
            record_id=f"pmid:{pmid}" if pmid else f"doi:{doi}",
            title=title,
            authors=("Example Author",),
            year=2025,
            journal="Example Journal",
            doi=doi,
            pmid=pmid,
            pmcid=None,
            arxiv_id=None,
            abstract=None,
            full_text_availability="metadata_only",
            source_priority=2,
            citation_payload={"source": "test"},
            local_asset_paths=(),
            relevance_role="candidate",
            claim_support_scope=(),
        )

    monkeypatch.setattr(
        pubmed,
        "fetch_pubmed_summary",
        lambda **_: [
            _record(
                pmid="41469089",
                doi="10.1136/fmch-2025-003765",
                title="Guidelines on primary healthcare for type 2 diabetes in China, 2025",
            ),
            _record(
                pmid="37798471",
                doi="10.1038/s43856-023-00360-3",
                title="Precision subclassification of type 2 diabetes: a systematic review",
            ),
        ],
    )
    monkeypatch.setattr(
        crossref,
        "fetch_crossref_work",
        lambda doi: _record(
            pmid=None,
            doi=doi,
            title=(
                "Guidelines on primary healthcare for type 2 diabetes in China, 2025"
                if doi == "10.1136/fmch-2025-003765"
                else "Precision subclassification of type 2 diabetes: a systematic review"
            ),
        ),
    )
    semantic_calls: list[list[str]] = []

    def _fetch_semantic(*, paper_ids, **_):
        semantic_calls.append(list(paper_ids))
        if paper_ids == ["DOI:10.1038/s43856-023-00360-3"]:
            return {
                "payload": {"message": "Too Many Requests", "code": "429"},
                "response_status": "rate_limited",
                "rate_limit_status": {
                    "status": "rate_limited",
                    "remaining": None,
                    "reset_at": "",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
            }
        return {
            "payload": [
                {
                    "paperId": "S2GUIDELINE",
                    "title": "Guidelines on primary healthcare for type 2 diabetes in China, 2025",
                    "year": 2025,
                    "venue": "Family Medicine and Community Health",
                    "externalIds": {"DOI": "10.1136/fmch-2025-003765"},
                    "citationCount": 2,
                }
            ],
            "response_status": "ok",
            "rate_limit_status": {
                "status": "ok",
                "remaining": 10,
                "reset_at": "",
                "backoff": {"policy": "exponential", "retry_after_seconds": 0},
            },
        }

    monkeypatch.setattr(semantic, "fetch_paper_batch", _fetch_semantic)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_literature_materialization(study_root)
    _write_readiness_dispatch(study_root, profile, _readiness_dispatch(study_id=study_id))

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert semantic_calls == [
        ["DOI:10.1038/s43856-023-00360-3"],
        ["DOI:10.1136/fmch-2025-003765"],
    ]
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["status"] == "ready"
    assert provider_surface["provider_response_ledger_refs"][2] == (
        "artifacts/medical_paper/provider_responses/"
        "semantic-scholar-doi-10-1136-fmch-2025-003765.json"
    )

def test_execute_dispatch_uses_bounded_pubmed_verified_semantic_candidates(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    pubmed = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    crossref = importlib.import_module("med_autoscience.adapters.literature.doi")
    semantic = importlib.import_module("med_autoscience.adapters.literature.semantic_scholar")
    records = importlib.import_module("med_autoscience.literature_records")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")

    title_by_doi = {
        "10.1016/j.diabres.2015.02.015": (
            "Development and validation of a predictive risk model for all-cause mortality in type 2 diabetes"
        ),
        "10.2337/dc08-1047": "Systematic review of diabetes mortality prediction models",
        "10.1155/2018/4638327": "Guideline statement for diabetes mortality risk model reporting",
        "10.5334/gh.1131": "Prediction of Five-Year Cardiovascular Disease Risk in People with Type 2 Diabetes Mellitus",
    }
    pmid_by_doi = {
        "10.1016/j.diabres.2015.02.015": "25869581",
        "10.2337/dc08-1047": "18809629",
        "10.1155/2018/4638327": "30116741",
        "10.5334/gh.1131": "36051323",
    }

    def _record(*, doi: str, pmid: str | None = None, title: str | None = None):
        return records.LiteratureRecord(
            record_id=f"pmid:{pmid or pmid_by_doi.get(doi, '')}",
            title=title or title_by_doi[doi],
            authors=("Example Author",),
            year=2025,
            journal="Example Journal",
            doi=doi,
            pmid=pmid or pmid_by_doi.get(doi),
            pmcid=None,
            arxiv_id=None,
            abstract=None,
            full_text_availability="metadata_only",
            source_priority=2,
            citation_payload={"source": "test"},
            local_asset_paths=(),
            relevance_role="candidate",
            claim_support_scope=(),
        )

    monkeypatch.setattr(
        pubmed,
        "fetch_pubmed_summary",
        lambda **_: [_record(doi=doi) for doi in title_by_doi],
    )
    monkeypatch.setattr(crossref, "fetch_crossref_work", lambda doi: _record(doi=doi, pmid=None))
    semantic_calls: list[list[str]] = []

    def _fetch_semantic(*, paper_ids, **_):
        semantic_calls.append(list(paper_ids))
        if paper_ids != ["DOI:10.5334/gh.1131"]:
            return {
                "payload": {"message": "Too Many Requests", "code": "429"},
                "response_status": "rate_limited",
                "rate_limit_status": {
                    "status": "rate_limited",
                    "remaining": None,
                    "reset_at": "",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
            }
        return {
            "payload": [
                {
                    "paperId": "S2MORTALITY",
                    "title": title_by_doi["10.5334/gh.1131"],
                    "year": 2022,
                    "venue": "Global Heart",
                    "externalIds": {"DOI": "10.5334/gh.1131"},
                    "citationCount": 2,
                }
            ],
            "response_status": "ok",
            "rate_limit_status": {
                "status": "ok",
                "remaining": 10,
                "reset_at": "",
                "backoff": {"policy": "exponential", "retry_after_seconds": 0},
            },
        }

    monkeypatch.setattr(semantic, "fetch_paper_batch", _fetch_semantic)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_mortality_literature_materialization(study_root)
    _write_readiness_dispatch(study_root, profile, _readiness_dispatch(study_id=study_id))

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert semantic_calls == [
        ["DOI:10.2337/dc08-1047"],
        ["DOI:10.1155/2018/4638327"],
        ["DOI:10.1016/j.diabres.2015.02.015"],
        ["DOI:10.5334/gh.1131"],
    ]
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["status"] == "ready"
    assert provider_surface["provider_response_ledger_refs"][2] == (
        "artifacts/medical_paper/provider_responses/semantic-scholar-doi-10-5334-gh-1131.json"
    )

def test_execute_dispatch_authors_provider_payload_from_existing_literature_evidence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_ready_literature_intelligence(study_root)
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
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["status"] == "ready"
    assert provider_surface["provider_provenance"][0]["provider_name"] == "pubmed"
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_provider_runtime"]["status"] == "present"
    assert by_key["literature_scout"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "study_line_selection"
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

def test_execute_dispatch_materializes_literature_scout_from_existing_intelligence_os(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_literature_intelligence(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="literature_scout")
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
    assert execution["owner_result"]["completed_surface_key"] == "literature_scout"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_literature_scout"
    assert action_result["surface_key"] == "literature_scout"
    assert action_result["status"] == "present"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "quality_gate_receipt_with_stable_typed_blocker"
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    intelligence_os = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json").read_text(
            encoding="utf-8"
        )
    )
    assert intelligence_os["surface"] == "literature_intelligence_os"
    assert intelligence_os["status"] == "ready"
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_scout"]["status"] == "present"
    assert by_key["literature_scout"]["evidence_refs"] == [
        str(study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json")
    ]
    assert not (study_root / "artifacts" / "medical_paper" / "literature_scout.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper" / "submission_minimal" / "current_package").exists()

def test_execute_dispatch_materializes_literature_scout_from_ready_provider_runtime(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_literature_provider_runtime_with_nested_intelligence(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="literature_scout")
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
    assert execution["owner_result"]["completed_surface_key"] == "literature_scout"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "ready_literature_provider_runtime"
    )
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["status"] == "present"
    intelligence_os = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json").read_text(
            encoding="utf-8"
        )
    )
    assert intelligence_os["surface"] == "literature_intelligence_os"
    assert intelligence_os["status"] == "ready"
    assert intelligence_os["quality_claim_authorized"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_scout"]["status"] == "present"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_execute_dispatch_blocks_literature_scout_without_existing_intelligence_os(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="literature_scout")
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
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    assert execution["owner_delta_result"]["result_kind"] == "stable_typed_blocker"
    assert execution["owner_result"]["requested_surface_key"] == "literature_scout"
    assert execution["owner_result"]["operator_payload_authoring"]["blocked_reason"] == (
        "insufficient_literature_scout_payload_sources"
    )
    assert not (study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json").exists()
    assert not (study_root / "artifacts" / "medical_paper" / "literature_scout.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
