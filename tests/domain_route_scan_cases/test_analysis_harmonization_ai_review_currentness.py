from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.domain_route_scan_parts.analysis_harmonization_ai_review import (
    publication_eval_covers_currentness_refs,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_publication_eval_ref_paths_do_not_cover_newer_required_ref_versions(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    analysis_path = (
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    )
    evidence_path = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        analysis_path,
        {
            "surface": "analysis_harmonization_owner_result",
            "generated_at": "2026-05-21T16:33:14+00:00",
        },
    )
    _write_json(
        evidence_path,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "generated_at": "2026-05-21T16:33:14+00:00",
        },
    )
    publication_eval_payload = {
        "emitted_at": "2026-05-20T18:32:14+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(analysis_path), str(evidence_path)],
        },
    }

    assert (
        publication_eval_covers_currentness_refs(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            required_refs=[str(analysis_path), str(evidence_path)],
        )
        is False
    )


def test_publication_eval_covers_required_ref_versions_when_eval_is_newer(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    analysis_path = (
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    )
    evidence_path = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        analysis_path,
        {
            "surface": "analysis_harmonization_owner_result",
            "generated_at": "2026-05-21T16:33:14+00:00",
        },
    )
    _write_json(
        evidence_path,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "generated_at": "2026-05-21T16:33:14+00:00",
        },
    )
    publication_eval_payload = {
        "emitted_at": "2026-05-21T17:00:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(analysis_path), str(evidence_path)],
        },
    }

    assert (
        publication_eval_covers_currentness_refs(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            required_refs=[str(analysis_path), str(evidence_path)],
        )
        is True
    )
