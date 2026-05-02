from __future__ import annotations

from pathlib import Path

import pytest


def test_style_corpus_materializes_reusable_medical_voice_principles(tmp_path: Path) -> None:
    from med_autoscience.medical_journal_style_corpus import (
        materialize_medical_journal_style_corpus,
        read_medical_journal_style_corpus,
    )

    study_root = tmp_path / "study"
    result = materialize_medical_journal_style_corpus(study_root=study_root)
    payload = read_medical_journal_style_corpus(study_root=study_root)

    assert result["artifact_path"] == str(study_root.resolve() / "paper" / "medical_journal_style_corpus.json")
    assert payload["corpus_id"] == "general_medical_journal_style_corpus_v1"
    assert payload["style_profile"]["target_voice"] == "neutral_clinical_original_research"
    source_ids = {item["source_id"] for item in payload["source_refs"]}
    assert {
        "zeiger_biomedical_papers",
        "gopen_swan_reader_expectations",
        "jama_author_instructions",
        "elsevier_medicine_writing",
        "jama_network_open_original_investigations",
    }.issubset(source_ids)
    assert "Make the clinical finding the grammatical subject." in payload["principles"]["results"]
    assert payload["copyright_boundary"]["long_excerpts_allowed"] is False


def test_style_corpus_reader_rejects_non_authority_path(tmp_path: Path) -> None:
    from med_autoscience.medical_journal_style_corpus import resolve_medical_journal_style_corpus_ref

    with pytest.raises(ValueError, match="study paper corpus"):
        resolve_medical_journal_style_corpus_ref(
            study_root=tmp_path / "study",
            ref=tmp_path / "study" / "paper" / "style_notes.json",
        )
