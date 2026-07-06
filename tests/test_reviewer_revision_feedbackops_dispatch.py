from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_feedbackops_dispatch_consumes_request_and_blocks_on_missing_ai_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        dispatch_reviewer_revision_feedbackops,
    )

    request_path = tmp_path / "feedbackops_dispatch_request.json"
    suite_path = tmp_path / "latest_suite.json"
    suite_path.write_text('{"suite_id":"suite:mas/test"}\n', encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_request",
                "status": "ready_for_opl_feedbackops",
                "study_id": "001-risk",
                "suite_path": str(suite_path),
                "opl_feedback_submit": {
                    "argv": [
                        "--target-agent",
                        "mas",
                        "--delivery-ref",
                        str(suite_path),
                        "--feedback-ref",
                        "task-intake:latest",
                        "--json",
                    ]
                },
                "authority_boundary": {"can_write_owner_receipt": False},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def fake_run(argv, *, text, capture_output, check):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, '{"ok":true}', "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = dispatch_reviewer_revision_feedbackops(request_path=request_path, opl_bin="opl")

    assert result["status"] == "blocked_missing_structured_ai_reviewer_evaluation"
    assert result["writes_study_truth"] is False
    assert result["writes_owner_receipt"] is False
    assert calls == [
        [
            "opl",
            "feedback",
            "submit",
            "--target-agent",
            "mas",
            "--delivery-ref",
            str(suite_path),
            "--feedback-ref",
            "task-intake:latest",
            "--json",
        ],
        ["opl", "feedback", "read", "--json"],
        ["opl", "feedback", "reconcile", "--json"],
        ["opl", "agent-lab", "run", "--suite", str(suite_path), "--json"],
    ]
    readback = json.loads((tmp_path / "feedbackops_execution_readback.json").read_text())
    assert readback["status"] == "blocked_missing_structured_ai_reviewer_evaluation"
    assert readback["feedbackops_read"]["stdout_summary"] == {"top_level_keys": ["ok"]}


def test_feedbackops_execution_readback_reader_compacts_command_outputs(tmp_path: Path) -> None:
    from med_autoscience.reviewer_revision_feedbackops_dispatch import (
        read_reviewer_revision_feedbackops_execution_readback,
    )

    readback_path = (
        tmp_path
        / "artifacts"
        / "agent_lab"
        / "medical_manuscript_quality"
        / "feedbackops_execution_readback.json"
    )
    readback_path.parent.mkdir(parents=True)
    readback_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_readback",
                "schema_version": 1,
                "study_id": "001-risk",
                "status": "blocked_missing_structured_ai_reviewer_evaluation",
                "next_owner": "opl-meta-agent",
                "blocked_reason": "missing structured reviewer evaluation",
                "writes_study_truth": False,
                "writes_owner_receipt": False,
                "writes_typed_blocker": False,
                "feedbackops_read": {
                    "argv": ["opl", "feedback", "read", "--json"],
                    "returncode": 0,
                    "stdout_bytes": 100000,
                    "stdout_json": None,
                    "stdout_summary": {"feedbackops": {"status": "ready"}},
                    "stderr": "",
                },
                "agent_lab_run": {
                    "argv": ["opl", "agent-lab", "run", "--suite", "suite.json", "--json"],
                    "returncode": 0,
                    "stdout_bytes": 200000,
                    "stdout_json": None,
                    "stdout_summary": {"agent_lab": {"status": "blocked"}},
                    "stderr": "",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    compact = read_reviewer_revision_feedbackops_execution_readback(study_root=tmp_path)

    assert compact is not None
    assert compact["status"] == "blocked_missing_structured_ai_reviewer_evaluation"
    assert compact["commands"]["feedbackops_read"]["stdout_summary"] == {"feedbackops": {"status": "ready"}}
    assert compact["commands"]["agent_lab_run"]["stdout_bytes"] == 200000
