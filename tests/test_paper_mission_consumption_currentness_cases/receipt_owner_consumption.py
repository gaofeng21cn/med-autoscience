from __future__ import annotations

import json
import os
from pathlib import Path

from med_autoscience.controllers.paper_mission_receipt_owner_consumption.storage import (
    _write_output_packet,
)
from tests.test_paper_mission_consumption_currentness_cases.shared import (
    _receipt_owner_consumption_payload,
)


def test_receipt_owner_consumption_write_preserves_newer_route_checkpoint(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
    )
    older_checkpoint = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-old"
        / "stage_attempt_closeout_packet.json"
    )
    newer_checkpoint = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-new"
        / "stage_attempt_closeout_packet.json"
    )
    older_checkpoint.parent.mkdir(parents=True)
    newer_checkpoint.parent.mkdir(parents=True)
    older_checkpoint.write_text("{}", encoding="utf-8")
    newer_checkpoint.write_text("{}", encoding="utf-8")
    os.utime(older_checkpoint, (2_000_000_000, 2_000_000_000))
    os.utime(newer_checkpoint, (3_000_000_000, 3_000_000_000))
    newer_payload = _receipt_owner_consumption_payload(
        study_id=study_id,
        checkpoint_ref=(
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-new/stage_attempt_closeout_packet.json"
        ),
    )
    older_payload = _receipt_owner_consumption_payload(
        study_id=study_id,
        checkpoint_ref=(
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-old/stage_attempt_closeout_packet.json"
        ),
    )

    _write_output_packet(
        output_root=output_root,
        study_id=study_id,
        payload=newer_payload,
        writes_authority=True,
    )
    manifest = _write_output_packet(
        output_root=output_root,
        study_id=study_id,
        payload=older_payload,
        writes_authority=True,
    )

    assert manifest["write_skipped_stale_route_checkpoint"] is True
    payload = json.loads(
        (output_root / study_id / "receipt_owner_consumption.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["mas_receipt_consumption"]["route_checkpoint_evidence_ref"].endswith(
        "sat-new/stage_attempt_closeout_packet.json"
    )
