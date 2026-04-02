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


def test_resolve_study_completion_state_serializes_ready_contract(tmp_path: Path) -> None:
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
                '  completed_at: "2026-04-03T00:00:00+00:00"',
                "  evidence_paths:",
                "    - manuscript/final/submission_manifest.json",
                "    - notes/revision_status.md",
                "",
            ]
        ),
    )
    write_text(study_root / "manuscript" / "final" / "submission_manifest.json", "{}\n")
    write_text(study_root / "notes" / "revision_status.md", "# Revision\n")

    state = module.resolve_study_completion_state(study_root=study_root)

    assert state.status == "resolved"
    assert state.ready is True
    assert state.contract is not None
    assert state.to_dict() == {
        "ready": True,
        "status": "resolved",
        "completion_status": "completed",
        "summary": "Study is done.",
        "user_approval_text": "同意",
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": [
            "manuscript/final/submission_manifest.json",
            "notes/revision_status.md",
        ],
        "missing_evidence_paths": [],
        "errors": [],
    }


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


def test_resolve_study_completion_state_wraps_invalid_contract_as_invalid_state(tmp_path: Path) -> None:
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

    state = module.resolve_study_completion_state(study_root=study_root)

    assert state.status == "invalid"
    assert state.ready is False
    assert state.contract is None
    assert len(state.errors) == 1
    assert "study_completion.status" in state.errors[0]
    assert state.to_dict() == {
        "ready": False,
        "status": "invalid",
        "completion_status": None,
        "summary": "",
        "user_approval_text": "",
        "completed_at": None,
        "evidence_paths": [],
        "missing_evidence_paths": [],
        "errors": [state.errors[0]],
    }


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
