from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_live_runtime_evidence_rollup_is_opl_redirect_and_never_completes() -> None:
    rollup = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement.live_runtime_evidence_rollup"
    )

    readback = rollup.live_runtime_evidence_rollup_readback(
        repo_root=REPO_ROOT,
        live_tail_evidence_records=[{"surface_id": "runtime_health_kernel"}],
        live_runtime_gap_evidence_records=[{"gap_id": "paper-progress"}],
    )

    assert readback["status"] == "redirect_to_opl_runtime_evidence_readback"
    assert readback["replacement_ref"] == "opl:runtime-evidence-readback"
    assert readback["mas_live_work_order_generation"] == "retired"
    assert readback["mas_live_evidence_intake"] == "retired"
    assert readback["supplied_record_count"] == 2
    assert readback["supplied_records_consumed"] is False
    assert readback["completion_claim_allowed"] is False
    assert readback["live_runtime_readiness_claim_allowed"] is False


def test_live_runtime_evidence_rollup_cli_reads_redirect(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(
        [
            "doctor",
            "live-runtime-evidence-rollup",
            "--repo-root",
            str(REPO_ROOT),
            "--format",
            "json",
        ]
    )
    readback = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert readback["contract_validation"]["status"] == "passed"
    assert readback["next_owner"] == "one-person-lab"
    assert readback["completion_claim_allowed"] is False
