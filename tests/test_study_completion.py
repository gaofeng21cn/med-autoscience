from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_study_completion_contract_returns_none_when_absent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.study_completion")
    study_root = tmp_path / "study"
    write_text(study_root / "study.yaml", "study_id: 001-risk\n")

    assert module.resolve_study_completion_contract(study_root=study_root) is None


def test_resolve_study_completion_contract_reports_missing_evidence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.study_completion")
    study_root = tmp_path / "study"
    write_text(
        study_root / "study.yaml",
        "\n".join(
            [
                "study_id: 001-risk",
                "study_completion:",
                "  status: completed",
                "  summary: Study is done.",
                "  user_approval_text: 同意",
                "  evidence_paths:",
                "    - manuscript/final/submission_manifest.json",
                "    - notes/revision_status.md",
                "",
            ]
        ),
    )
    write_text(study_root / "manuscript" / "final" / "submission_manifest.json", "{}\n")

    contract = module.resolve_study_completion_contract(study_root=study_root)

    assert contract is not None
    assert contract.ready is False
    assert contract.missing_evidence_paths == ("notes/revision_status.md",)


def test_resolve_study_completion_contract_rejects_unsupported_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.study_completion")
    study_root = tmp_path / "study"
    write_text(
        study_root / "study.yaml",
        "\n".join(
            [
                "study_id: 001-risk",
                "study_completion:",
                "  status: archived",
                "  summary: Study is done.",
                "  user_approval_text: 同意",
                "  evidence_paths:",
                "    - manuscript/final/submission_manifest.json",
                "",
            ]
        ),
    )

    try:
        module.resolve_study_completion_contract(study_root=study_root)
    except ValueError as exc:
        assert "study_completion.status" in str(exc)
    else:
        raise AssertionError("expected ValueError for unsupported study_completion.status")
