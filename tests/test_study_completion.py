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
                "    - manuscript/submission_manifest.json",
                "    - notes/revision_status.md",
                "",
            ]
        ),
    )
    write_text(study_root / "manuscript" / "submission_manifest.json", "{}\n")
    write_text(study_root / "notes" / "revision_status.md", "# Revision\n")

    state = module.resolve_study_completion_state(study_root=study_root)

    assert state.status is module.StudyCompletionStateStatus.RESOLVED
    assert state.ready is True
    assert state.contract is not None
    assert state.contract.status is module.StudyCompletionContractStatus.COMPLETED
    assert state.to_dict() == {
        "ready": True,
        "status": "resolved",
        "completion_status": "completed",
        "summary": "Study is done.",
        "user_approval_text": "同意",
        "requires_program_human_confirmation": False,
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": [
            "manuscript/submission_manifest.json",
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
                "    - manuscript/submission_manifest.json",
                "    - notes/revision_status.md",
                "",
            ]
        ),
    )
    write_text(study_root / "manuscript" / "submission_manifest.json", "{}\n")

    contract = module.resolve_study_completion_contract(study_root=study_root)

    assert contract is not None
    assert contract.status is module.StudyCompletionContractStatus.COMPLETED
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
                "    - manuscript/submission_manifest.json",
                "",
            ]
        ),
    )

    state = module.resolve_study_completion_state(study_root=study_root)

    assert state.status is module.StudyCompletionStateStatus.INVALID
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
        "requires_program_human_confirmation": False,
        "completed_at": None,
        "evidence_paths": [],
        "missing_evidence_paths": [],
        "errors": [state.errors[0]],
    }


def test_study_completion_state_rejects_unknown_status() -> None:
    module = importlib.import_module("med_autoscience.study_completion")

    try:
        module.StudyCompletionState(
            status="unexpected",
            contract=None,
            errors=(),
        )
    except ValueError as exc:
        assert "unknown study completion state status" in str(exc)
    else:
        raise AssertionError("expected ValueError for unsupported StudyCompletionState.status")


def test_study_completion_contract_rejects_unknown_status() -> None:
    module = importlib.import_module("med_autoscience.study_completion")

    try:
        module.StudyCompletionContract(
            study_root=Path("/tmp/study"),
            status="unexpected",
            summary="done",
            user_approval_text="同意",
            completed_at=None,
            evidence_paths=("notes/revision_status.md",),
            missing_evidence_paths=(),
        )
    except ValueError as exc:
        assert "unknown study completion contract status" in str(exc)
    else:
        raise AssertionError("expected ValueError for unsupported StudyCompletionContract.status")


def test_study_completion_state_from_payload_round_trips_resolved_contract() -> None:
    module = importlib.import_module("med_autoscience.study_completion")
    payload = {
        "ready": True,
        "status": "resolved",
        "completion_status": "completed",
        "summary": "Study is done.",
        "user_approval_text": "同意",
        "requires_program_human_confirmation": False,
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": [
            "manuscript/submission_manifest.json",
            "notes/revision_status.md",
        ],
        "missing_evidence_paths": [],
        "errors": [],
    }

    state = module.StudyCompletionState.from_payload(
        study_root=Path("/tmp/study"),
        payload=payload,
    )

    assert state.status is module.StudyCompletionStateStatus.RESOLVED
    assert state.ready is True
    assert state.contract is not None
    assert state.contract.status is module.StudyCompletionContractStatus.COMPLETED
    assert state.contract.study_root == Path("/tmp/study")
    assert state.to_dict() == payload


def test_study_completion_state_from_payload_rejects_resolved_payload_without_completion_status() -> None:
    module = importlib.import_module("med_autoscience.study_completion")

    try:
        module.StudyCompletionState.from_payload(
            study_root=Path("/tmp/study"),
            payload={
                "ready": True,
                "status": "resolved",
                "summary": "Study is done.",
                "user_approval_text": "同意",
                "requires_program_human_confirmation": False,
                "completed_at": "2026-04-03T00:00:00+00:00",
                "evidence_paths": ["manuscript/submission_manifest.json"],
                "missing_evidence_paths": [],
                "errors": [],
            },
        )
    except ValueError as exc:
        assert "completion_status" in str(exc)
    else:
        raise AssertionError("expected ValueError when resolved payload omits completion_status")


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
                "    - manuscript/submission_manifest.json",
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


def test_resolve_study_completion_state_accepts_autonomous_completion_contract_without_user_approval_text(
    tmp_path: Path,
) -> None:
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
                "  evidence_paths:",
                "    - manuscript/submission_manifest.json",
                "",
            ]
        ),
    )
    write_text(study_root / "manuscript" / "submission_manifest.json", "{}\n")

    state = module.resolve_study_completion_state(study_root=study_root)

    assert state.ready is True
    assert state.contract is not None
    assert state.contract.user_approval_text is None
    assert state.contract.requires_program_human_confirmation is False
