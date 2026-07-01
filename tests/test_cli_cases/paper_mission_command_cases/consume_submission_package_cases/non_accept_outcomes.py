from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


@pytest.mark.parametrize(
    ("requested_outcome", "expected_consume_status", "expected_mission_state"),
    (
        ("route_back", "route_back", "route_back"),
        ("typed_blocker_required", "typed_blocker", "stable_blocker"),
        ("human_gate_required", "human_gate", "waiting_human_decision"),
    ),
)
def test_paper_mission_consume_candidate_maps_non_accept_outcomes(
    tmp_path: Path,
    capsys,
    requested_outcome: str,
    expected_consume_status: str,
    expected_mission_state: str,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(
        tmp_path,
        requested_outcome=requested_outcome,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["authority_consume_readback"]["consume_result"]["status"] == (
        expected_consume_status
    )
    assert payload["paper_mission_run_candidate"]["consume_result"]["status"] == (
        expected_consume_status
    )
    assert payload["paper_mission_run_candidate"]["mission_state"] == expected_mission_state
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)
