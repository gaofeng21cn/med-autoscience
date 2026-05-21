from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_guarded_apply_proof,
)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _assert_body_free_canary_packet(packet: dict[str, object], *, owner: str) -> None:
    assert set(packet) == {
        "ref",
        "role",
        "freshness",
        "owner",
        "receipt_id",
        "no_forbidden_write_proof",
    }
    assert packet["owner"] == owner
    assert packet["ref"]
    assert packet["receipt_id"]
    proof = packet["no_forbidden_write_proof"]
    assert isinstance(proof, dict)
    assert proof["write_permitted"] is False
    assert proof["forbidden_writes_performed"] is False
    assert "artifact_body" not in packet
    assert "memory_body" not in packet
    assert "current_package" not in packet


def test_owner_receipt_canary_closeout_materializes_body_free_packets(tmp_path: Path) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    _write_json(
        dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {
            "surface": "paper_repair_owner_receipt",
            "accepted": True,
            "execution_status": "executed",
            "canonical_artifact_delta_refs": [{"path": str(dm002 / "paper" / "manuscript.md")}],
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "progress_delta_candidate": True,
        },
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=tmp_path / "Yang",
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )["paper_line_provider_canary_closeout"]

    packet_roles = {packet["role"] for packet in payload["body_free_evidence_packets"]}
    assert {
        "owner_receipt_ref",
        "progress_delta_ref",
        "artifact_movement_ref",
        "no_forbidden_write_proof_ref",
    } <= packet_roles
    for packet in payload["body_free_evidence_packets"]:
        _assert_body_free_canary_packet(packet, owner="MedAutoScience")


def test_stable_blocker_canary_closeout_materializes_body_free_packets(tmp_path: Path) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    _write_json(
        dm002 / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=tmp_path / "Yang",
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )["paper_line_provider_canary_closeout"]

    assert {
        packet["role"] for packet in payload["body_free_evidence_packets"]
    } == {"stable_typed_blocker_ref", "no_forbidden_write_proof_ref"}
    for packet in payload["body_free_evidence_packets"]:
        _assert_body_free_canary_packet(packet, owner="MedAutoScience")
