from __future__ import annotations

import json
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
    assert payload["style_version"] == "medical_journal_prose_style_v2"
    assert payload["source_set_id"] == "general_medical_journal_style_source_set_v1"
    assert payload["style_digest"].startswith("sha256:")
    assert payload["style_currentness"] == {
        "status": "current",
        "currentness_policy_id": "medical_journal_style_currentness_v1",
        "style_version": "medical_journal_prose_style_v2",
        "current_style_version": "medical_journal_prose_style_v2",
        "style_digest": payload["style_digest"],
        "current_style_digest": payload["style_digest"],
    }
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


def test_style_corpus_reader_rejects_stale_digest(tmp_path: Path) -> None:
    from med_autoscience.medical_journal_style_corpus import (
        materialize_medical_journal_style_corpus,
        read_medical_journal_style_corpus,
    )

    study_root = tmp_path / "study"
    materialize_medical_journal_style_corpus(study_root=study_root)
    path = study_root / "paper" / "medical_journal_style_corpus.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["principles"]["results"].append("Tampered prose rule.")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="style_digest"):
        read_medical_journal_style_corpus(study_root=study_root)


def test_ensure_current_style_corpus_upgrades_legacy_surface(tmp_path: Path) -> None:
    from med_autoscience.medical_journal_style_corpus import ensure_current_medical_journal_style_corpus

    study_root = tmp_path / "study"
    path = study_root / "paper" / "medical_journal_style_corpus.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "surface": "medical_journal_style_corpus",
                "corpus_id": "general_medical_journal_style_corpus_v1",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = ensure_current_medical_journal_style_corpus(study_root=study_root)

    assert payload["style_version"] == "medical_journal_prose_style_v2"
    assert payload["style_currentness"]["status"] == "current"
