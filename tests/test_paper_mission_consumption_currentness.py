from __future__ import annotations

import os
from pathlib import Path

from med_autoscience.controllers.owner_route_handoff.paper_mission_consumption_route_handoff import (
    _paper_mission_handoff_timestamp_key,
    latest_paper_mission_consumption_route_handoff,
)
from med_autoscience.controllers.paper_mission_currentness import (
    receipt_owner_consumption_superseded_by_consumption,
)
from med_autoscience.paper_mission_consumption_readback import (
    _ledger_timestamp_key,
    latest_paper_mission_consumption_transaction_readback,
)
from tests.test_paper_mission_consumption_currentness_cases.receipt_owner_consumption import *  # noqa: F401,F403
from tests.test_paper_mission_consumption_currentness_cases.shared import (
    _patch_json,
    _write_ledger,
)


def test_consumption_transaction_readback_prefers_newest_mtime_over_run_id(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    old_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tzz_old_takeover_dm002_submit",
        transaction_ref="paper-mission-transaction::dm002::old-takeover",
        fingerprint="fingerprint::dm002::old-takeover",
    )
    fresh_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Taa_fresh_main_drive_dm002",
        transaction_ref="paper-mission-transaction::dm002::fresh-drive",
        fingerprint="fingerprint::dm002::fresh-drive",
    )
    os.utime(old_record, (1_000_000_000, 1_000_000_000))
    os.utime(fresh_record, (2_000_000_000, 2_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(fresh_record)
    assert readback["paper_mission_transaction"]["transaction_id"] == (
        "paper-mission-transaction::dm002::fresh-drive"
    )
    assert readback["opl_runtime_carrier"]["work_unit_fingerprint"] == (
        "fingerprint::dm002::fresh-drive"
    )


def test_consumption_route_handoff_prefers_newest_mtime_over_run_id(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    old_handoff = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tzz_old_takeover_dm002_submit",
        transaction_ref="paper-mission-transaction::dm002::old-takeover",
        fingerprint="fingerprint::dm002::old-takeover",
    ).parent / "opl_route_handoff.json"
    fresh_handoff = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Taa_fresh_main_drive_dm002",
        transaction_ref="paper-mission-transaction::dm002::fresh-drive",
        fingerprint="fingerprint::dm002::fresh-drive",
    ).parent / "opl_route_handoff.json"
    os.utime(old_handoff, (1_000_000_000, 1_000_000_000))
    os.utime(fresh_handoff, (2_000_000_000, 2_000_000_000))

    handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert handoff["source_ref"] == str(fresh_handoff)
    assert handoff["paper_mission_transaction_ref"] == (
        "paper-mission-transaction::dm002::fresh-drive"
    )
    assert handoff["opl_runtime_carrier"]["work_unit_fingerprint"] == (
        "fingerprint::dm002::fresh-drive"
    )


def test_consumption_currentness_prefers_external_delta_over_later_drive_noop(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    external_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260628T034633Z_repair_execution_delta",
        transaction_ref="paper-mission-transaction::dm003::followthrough-02",
        fingerprint="fingerprint::dm003::repair-delta",
        external_delta_ref="/workspace/studies/dm003/artifacts/controller/repair_execution_evidence/latest.json",
    )
    later_noop_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="paper_mission_drive/followthrough-02",
        transaction_ref="paper-mission-transaction::dm003::followthrough-02",
        fingerprint="fingerprint::dm003::repair-delta",
    )
    os.utime(external_record, (2_000_000_000, 2_000_000_000))
    os.utime(external_record.parent / "opl_route_handoff.json", (2_000_000_000, 2_000_000_000))
    os.utime(later_noop_record, (3_000_000_000, 3_000_000_000))
    os.utime(
        later_noop_record.parent / "opl_route_handoff.json",
        (3_000_000_000, 3_000_000_000),
    )

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )
    handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(external_record)
    assert handoff["source_ref"] == str(external_record.parent / "opl_route_handoff.json")


def test_consumption_currentness_prefers_newer_paper_facing_delta_over_old_external_delta(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    external_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260628T080615Z_quality_repair_delta",
        transaction_ref="paper-mission-transaction::dm002::quality-repair",
        fingerprint="fingerprint::dm002::quality-repair",
        external_delta_ref="/workspace/studies/dm002/artifacts/controller/repair_execution_evidence/latest.json",
    )
    low_quality_handoff_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260629T_low_quality_handoff_consume_v3",
        transaction_ref="paper-mission-transaction::dm002::low-quality-handoff",
        fingerprint="fingerprint::dm002::low-quality-handoff",
        paper_facing_delta_ref=(
            "/workspace/ops/medautoscience/paper_mission_candidate_package/"
            "20260629T_low_quality_handoff/dm002/paper_facing_candidate_delta.json"
        ),
    )
    os.utime(external_record, (2_000_000_000, 2_000_000_000))
    os.utime(low_quality_handoff_record, (3_000_000_000, 3_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(low_quality_handoff_record)
    assert readback["candidate_ref"] == str(
        low_quality_handoff_record.parent / "package_manifest.json"
    )


def test_consumption_currentness_prefers_reviewer_revision_over_old_submission_candidate(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    old_submission_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260701T045145Z_manuscript_volume_clinical_figures_submit",
        transaction_ref="paper-mission-transaction::obesity::submission-candidate",
        fingerprint="fingerprint::obesity::submission-candidate",
        paper_facing_delta_ref="/workspace/obesity/submission/paper_facing_delta.json",
    )
    reviewer_revision_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260701T1425Z_external_sci_registry_review",
        transaction_ref="paper-mission-transaction::obesity::reviewer-revision",
        fingerprint="fingerprint::obesity::reviewer-revision",
        milestone_kind="reviewer_revision_candidate",
        relative_candidate_ref=True,
    )
    os.utime(old_submission_record, (2_000_000_000, 2_000_000_000))
    os.utime(reviewer_revision_record, (3_000_000_000, 3_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )
    handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(reviewer_revision_record)
    assert readback["candidate_ref"] == str(
        Path("ops")
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260701T1425Z_external_sci_registry_review"
        / study_id
        / "package_manifest.json"
    )
    assert handoff["source_ref"] == str(
        reviewer_revision_record.parent / "opl_route_handoff.json"
    )


def test_consumption_ledger_timestamp_keys_accept_z_run_ids(tmp_path: Path) -> None:
    z_run_path = (
        tmp_path
        / "paper_mission_consumption_ledger"
        / "20260624Zmain_drive_dm002_fresh"
        / "002-dm-china-us-mortality-attribution"
        / "consume_record.json"
    )

    assert _ledger_timestamp_key(z_run_path) == "20260624Zmain_drive_dm002_fresh"
    assert _paper_mission_handoff_timestamp_key(z_run_path) == (
        "20260624Zmain_drive_dm002_fresh"
    )


def test_consumption_transaction_readback_rejects_cross_identity_packets(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    consume_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tcross_identity_dm002",
        transaction_ref="paper-mission-transaction::dm002::canonical",
        fingerprint="fingerprint::dm002::canonical",
    )
    _patch_json(
        consume_record.parent / "stage_terminal_decision.json",
        {
            "stage_terminal_decision_ref": (
                "paper-mission-transaction::dm002::other#stage_terminal_decision"
            )
        },
    )

    assert (
        latest_paper_mission_consumption_transaction_readback(
            workspace_root=workspace_root,
            study_id=study_id,
        )
        is None
    )


def test_consumption_transaction_readback_keeps_accepted_candidate_when_route_handoff_is_route_back(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    consume_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="paper_mission_drive/followthrough-02",
        transaction_ref="paper-mission-transaction::dm003::followthrough-02",
        fingerprint="fingerprint::dm003::followthrough-02",
    )
    _patch_json(
        consume_record.parent / "stage_terminal_decision.json",
        {"transaction_state": "route_back"},
    )

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(consume_record)
    assert readback["selected_outcome"] == "accepted_candidate"
    assert readback["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert readback["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert readback["opl_route_command"]["command_kind"] == "route_back"
    assert readback["transaction_state"] == "route_back"


def test_route_back_consumption_does_not_supersede_consumed_typed_blocker_receipt(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    receipt_ref = workspace_root / "ops" / "medautoscience" / "receipt.json"
    receipt_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    consume_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="paper_mission_drive",
        transaction_ref="paper-mission-transaction::obesity::submission-candidate",
        fingerprint="fingerprint::obesity::submission-candidate",
    )
    _patch_json(
        consume_record.parent / "stage_terminal_decision.json",
        {"transaction_state": "route_back"},
    )
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(consume_record, (3_000_000_000, 3_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["transaction_state"] == "route_back"
    assert (
        receipt_owner_consumption_superseded_by_consumption(
            receipt_owner_consumption_readback={
                "status": "owner_consumption_applied",
                "source_ref": str(receipt_ref),
                "mas_receipt_consumption": {
                    "status": "owner_consumed_typed_blocker",
                },
                "stage_closure_decision": {
                    "outcome": {"kind": "typed_blocker"}
                },
            },
            consumption_ledger_readback=readback,
        )
        is False
    )


def test_consumption_route_handoff_rejects_cross_identity_carrier(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    handoff_ref = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tcross_carrier_dm002",
        transaction_ref="paper-mission-transaction::dm002::canonical",
        fingerprint="fingerprint::dm002::canonical",
    ).parent / "opl_route_handoff.json"
    _patch_json(
        handoff_ref,
        {
            "opl_runtime_carrier": {
                "paper_mission_transaction_ref": (
                    "paper-mission-transaction::dm002::other"
                ),
                "stage_terminal_decision_ref": (
                    "paper-mission-transaction::dm002::other"
                    "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002::other#opl_route_command"
                ),
                "work_unit_fingerprint": "fingerprint::dm002::other",
            }
        },
    )

    assert (
        latest_paper_mission_consumption_route_handoff(
            workspace_root=workspace_root,
            study_id=study_id,
        )
        is None
    )
