from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.family

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")


def _run_opl_agent_lab_longline() -> dict[str, object]:
    opl_bin = Path(os.environ.get("OPL_BIN", str(DEFAULT_OPL_BIN)))
    result = subprocess.run(
        [str(opl_bin), "agent-lab", "longline", "--json"],
        check=True,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def _mas_disposition(summary: dict[str, object]) -> dict[str, object]:
    dispositions = summary["recommended_repo_test_disposition"]
    assert isinstance(dispositions, list)
    for disposition in dispositions:
        assert isinstance(disposition, dict)
        if disposition.get("domain_id") == "med-autoscience":
            return disposition
    raise AssertionError("med-autoscience disposition missing from OPL Agent Lab longline summary")


def test_mas_longline_migration_guard_runs_through_opl_agent_lab() -> None:
    payload = _run_opl_agent_lab_longline()

    suite = payload["agent_lab_longline"]["suite_result"]
    assert suite["status"] == "passed"
    assert "med-autoscience" in {
        domain_summary["domain_id"] for domain_summary in suite["domain_summary"]
    }

    longline_summary = suite["longline_summary"]
    assert longline_summary["ready_to_reduce_domain_longline_tests"] is True

    disposition = _mas_disposition(longline_summary)
    assert set(disposition["move_to_opl_agent_lab"]) == {
        "provider-hosted guarded apply soak orchestration",
        "resume/retry/dead-letter recovery probe",
        "no-forbidden-write cross-domain regression",
    }
    assert set(disposition["keep_in_domain_repo"]) == {
        "publication-quality scorer",
        "owner receipt fixture",
        "paper artifact authority checks",
    }

    authority = longline_summary["authority_boundary"]
    assert authority["can_write_domain_truth"] is False
    assert authority["can_write_memory_body"] is False
    assert authority["can_accept_or_reject_memory_writeback"] is False
    assert authority["can_authorize_quality_verdict"] is False
