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


def _write_ready_literature_intelligence(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json",
        {
            "surface": "literature_intelligence_os",
            "status": "ready",
            "search_strategy": {
                "query": "diabetes mortality prediction",
                "mesh_terms": ["Diabetes Mellitus"],
                "keywords": ["diabetes mortality", "transportability"],
            },
            "search_date": "2026-06-06",
            "why_worth_doing": "Provider-backed evidence supports the current study framing.",
            "provider_provenance": [
                {
                    "provider_name": "pubmed",
                    "query": "diabetes mortality prediction",
                    "retrieved_at": "2026-06-06T08:00:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/pubmed.json"],
                },
                {
                    "provider_name": "crossref",
                    "query": "diabetes mortality guideline review",
                    "retrieved_at": "2026-06-06T08:01:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/crossref.json"],
                },
                {
                    "provider_name": "semantic_scholar",
                    "query": "diabetes mortality clinical neighbor",
                    "retrieved_at": "2026-06-06T08:02:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/semantic-scholar.json"],
                },
            ],
            "anchor_papers": ["pmid:12345"],
            "guidelines": ["guideline:TRIPOD+AI"],
            "systematic_reviews": ["doi:10.1000/systematic-review"],
            "journal_neighbor_refs": ["semantic_scholar:S2PAPER1"],
            "citation_ledger_refs": [
                "paper/evidence_ledger.json#pmid-12345",
                "paper/evidence_ledger.json#tripod-ai",
                "paper/evidence_ledger.json#systematic-review",
                "paper/evidence_ledger.json#semantic-S2PAPER1",
            ],
            "screening_decisions": [
                {
                    "ref": "pmid:12345",
                    "decision": "include",
                    "reason": "Study anchor.",
                }
            ],
        },
    )


def _write_literature_materialization(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "literature_materialization.json",
        {
            "schema_version": 1,
            "records": [
                {
                    "record_id": "lit-001",
                    "title": "Guidelines on primary healthcare for type 2 diabetes in China, 2025",
                    "doi": "10.1136/fmch-2025-003765",
                    "pubmed": {"pmid": "41469089"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["background", "methods/context"],
                },
                {
                    "record_id": "lit-002",
                    "title": "Precision subclassification of type 2 diabetes: a systematic review",
                    "doi": "10.1038/s43856-023-00360-3",
                    "pubmed": {"pmid": "37798471"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["background", "methods/context"],
                },
            ],
        },
    )


def _write_mortality_literature_materialization(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "literature_materialization.json",
        {
            "schema_version": 1,
            "records": [
                {
                    "record_id": "mortality-anchor",
                    "title": "Development and validation of a predictive risk model for all-cause mortality in type 2 diabetes",
                    "doi": "10.1016/j.diabres.2015.02.015",
                    "pubmed": {"pmid": "25869581"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["background", "methods/context"],
                },
                {
                    "record_id": "mortality-systematic",
                    "title": "Systematic review of diabetes mortality prediction models",
                    "doi": "10.2337/dc08-1047",
                    "pubmed": {"pmid": "18809629"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["systematic review"],
                },
                {
                    "record_id": "mortality-guideline",
                    "title": "Guideline statement for diabetes mortality risk model reporting",
                    "doi": "10.1155/2018/4638327",
                    "pubmed": {"pmid": "30116741"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["guideline"],
                },
                {
                    "record_id": "mortality-neighbor",
                    "title": "Prediction of Five-Year Cardiovascular Disease Risk in People with Type 2 Diabetes Mellitus",
                    "doi": "10.5334/gh.1131",
                    "pubmed": {"pmid": "36051323"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["neighbor"],
                },
            ],
        },
    )


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
    decision = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    assert decision["decision_type"] == "medical_paper_readiness_owner_blocker"
    assert decision["quality_claim_authorized"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_does_not_author_provider_runtime_from_materialization_without_provider_fetch(
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
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    authoring = execution["owner_result"]["operator_payload_authoring"]
    assert authoring["status"] == "blocked"
    assert authoring["blocked_reason"] == "provider_adapter_fetch_failed_pubmed"
    assert not (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").exists()


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
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "quality_gate_receipt_with_stable_typed_blocker"
    assert owner_delta["required_return_shape_satisfied"] is True
    assert owner_delta["owner_receipt_refs"] == []
    assert owner_delta["quality_gate_receipt_refs"][0] == str(
        study_root / "artifacts" / "medical_paper" / "readiness.json"
    )
    assert owner_delta["quality_gate_receipt_refs"][1].startswith(
        "artifacts/medical_paper/actions/results/"
    )
    assert owner_delta["stable_typed_blocker_refs"] == [
        str(study_root / "artifacts" / "controller_decisions" / "latest.json")
    ]
    assert owner_delta["quality_gate_receipt"]["completed_surface_key"] == "literature_provider_runtime"
    assert owner_delta["quality_gate_receipt"]["action_result_ref"] == owner_delta["quality_gate_receipt_refs"][1]
    assert owner_delta["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"
    assert owner_delta["authority_boundary"]["writes_publication_eval"] is False
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["surface"] == "literature_provider_runtime"
    assert provider_surface["status"] == "ready"
