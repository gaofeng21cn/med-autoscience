from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_delivery_manifest_records_style_and_quality_authority_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    from med_autoscience.medical_journal_style_corpus import (
        materialize_medical_journal_style_corpus,
        read_medical_journal_style_corpus,
    )
    from med_autoscience.medical_prose_review import stable_medical_prose_review_path
    from med_autoscience.medical_prose_review_request import stable_medical_prose_review_request_path

    paper_root, study_root = make_delivery_workspace(tmp_path)
    materialize_medical_journal_style_corpus(study_root=study_root)
    style_corpus = read_medical_journal_style_corpus(study_root=study_root)
    request_digest = "sha256:" + ("a" * 64)
    style_currentness = {
        "status": "current",
        "style_corpus_ref": str(study_root / "paper" / "medical_journal_style_corpus.json"),
        "corpus_id": style_corpus["corpus_id"],
        "style_version": style_corpus["style_version"],
        "source_set_id": style_corpus["source_set_id"],
        "style_digest": style_corpus["style_digest"],
    }
    dump_json(
        stable_medical_prose_review_request_path(study_root=study_root),
        {
            "schema_version": 1,
            "surface": "medical_prose_review_request",
            "review_owner": "ai_reviewer",
            "request_digest": request_digest,
            "request_currentness": {"status": "current"},
            "style_currentness": style_currentness,
        },
    )
    dump_json(
        stable_medical_prose_review_path(study_root=study_root),
        {
            "schema_version": 1,
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_digest": request_digest,
            },
            "style_currentness": style_currentness,
            "medical_journal_prose_quality": {
                "overall_style_verdict": "clear",
                "summary": "AI reviewer cleared the prose style.",
            },
        },
    )
    dump_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "surface": "publication_eval",
            "provenance": {"owner": "ai_reviewer"},
            "verdict": {"overall_verdict": "promising"},
        },
    )

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert manifest["publication_refs"]["medical_journal_style_corpus"].endswith(
        "paper/medical_journal_style_corpus.json"
    )
    assert manifest["quality_authority_refs"]["derived_delivery_surface_can_authorize_quality"] is False
    assert manifest["quality_authority_refs"]["medical_prose_review"]["request_digest"] == request_digest
    assert manifest["style_authority_refs"]["currentness_status"] == "current"
    assert manifest["style_authority_refs"]["style_corpus"]["style_version"] == "medical_journal_prose_style_v3"
    assert manifest["style_authority_refs"]["medical_prose_review"]["style_digest"] == style_corpus["style_digest"]
