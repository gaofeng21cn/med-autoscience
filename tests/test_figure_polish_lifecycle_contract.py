from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _valid_payload() -> dict:
    return {
        "schema_version": 1,
        "lifecycle_id": "fig-F1-polish-20260610",
        "relationship_refs": {
            "figure_visual_audit_receipt": "paper/figure_visual_audit_receipt.json",
            "display_pack_lock_publication_figure_quality_refs": (
                "paper/build/display_pack_lock.json#/publication_figure_quality_refs"
            ),
        },
        "events": [
            {
                "state": "draft_rendered",
                "figure_id": "F1",
                "artifact_ref": "paper/figures/generated/F1.png",
                "actor": "display_pack_builder",
                "evidence_ref": "paper/build/display_pack_lock.json",
            },
            {
                "state": "deterministic_qc_clear",
                "figure_id": "F1",
                "artifact_ref": "paper/figures/generated/F1.png",
                "actor": "deterministic_qc",
                "evidence_ref": "paper/qc/F1.layout.json",
            },
            {
                "state": "visual_audit_findings",
                "figure_id": "F1",
                "artifact_ref": "paper/figures/generated/F1.png",
                "actor": "vlm_visual_auditor",
                "evidence_ref": "paper/figure_visual_audit_receipt.json",
                "model_ref": "openai:gpt-5-vlm:2026-06-10",
            },
            {
                "state": "revised",
                "figure_id": "F1",
                "artifact_ref": "paper/figures/generated/F1.revised.png",
                "actor": "display_pack_builder",
                "evidence_ref": "paper/display_overrides.json",
            },
            {
                "state": "audit_clear",
                "figure_id": "F1",
                "artifact_ref": "paper/figures/generated/F1.revised.png",
                "actor": "human_reviewer",
                "evidence_ref": "paper/figure_visual_audit_receipt.json",
            },
        ],
    }


def test_load_figure_polish_lifecycle_accepts_valid_unfinished_prefix(tmp_path: Path) -> None:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    path = tmp_path / "figure_polish_lifecycle.json"
    _write_json(path, _valid_payload())

    payload = load_figure_polish_lifecycle(path)

    assert [event["state"] for event in payload["events"]] == [
        "draft_rendered",
        "deterministic_qc_clear",
        "visual_audit_findings",
        "revised",
        "audit_clear",
    ]
    assert payload["relationship_refs"]["figure_visual_audit_receipt"] == "paper/figure_visual_audit_receipt.json"


def test_load_figure_polish_lifecycle_accepts_multi_figure_gate_sequences(tmp_path: Path) -> None:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    payload = _valid_payload()
    second_sequence = [
        {**event, "figure_id": "F2", "artifact_ref": str(event["artifact_ref"]).replace("F1", "F2")}
        for event in _valid_payload()["events"]
    ]
    payload["events"] = [*payload["events"], *second_sequence]
    path = tmp_path / "figure_polish_lifecycle.json"
    _write_json(path, payload)

    loaded = load_figure_polish_lifecycle(path)

    assert [event["figure_id"] for event in loaded["events"][:5]] == ["F1"] * 5
    assert [event["figure_id"] for event in loaded["events"][5:]] == ["F2"] * 5


def test_load_figure_polish_lifecycle_rejects_skipped_hard_gate(tmp_path: Path) -> None:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    payload = _valid_payload()
    payload["events"] = [
        payload["events"][0],
        {
            "state": "visual_audit_findings",
            "figure_id": "F1",
            "artifact_ref": "paper/figures/generated/F1.png",
            "actor": "vlm_visual_auditor",
            "evidence_ref": "paper/figure_visual_audit_receipt.json",
            "model_ref": "openai:gpt-5-vlm:2026-06-10",
        },
    ]
    path = tmp_path / "figure_polish_lifecycle.json"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="state sequence"):
        load_figure_polish_lifecycle(path)


def test_load_figure_polish_lifecycle_requires_audit_clear_before_manifest(tmp_path: Path) -> None:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    payload = _valid_payload()
    payload["events"] = [
        payload["events"][0],
        payload["events"][1],
        payload["events"][2],
        payload["events"][3],
        {
            "state": "publication_manifested",
            "figure_id": "F1",
            "artifact_ref": "paper/figures/generated/F1.revised.png",
            "actor": "display_pack_builder",
            "evidence_ref": "paper/submission_minimal/submission_manifest.json",
        },
    ]
    path = tmp_path / "figure_polish_lifecycle.json"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="audit_clear"):
        load_figure_polish_lifecycle(path)


def test_load_figure_polish_lifecycle_requires_model_or_reviewer_ref_for_ai_vlm_actor(tmp_path: Path) -> None:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    payload = _valid_payload()
    payload["events"][2].pop("model_ref")
    path = tmp_path / "figure_polish_lifecycle.json"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="model_ref or reviewer_ref"):
        load_figure_polish_lifecycle(path)


def test_load_figure_polish_lifecycle_forbids_data_mutation_and_publication_verdict(tmp_path: Path) -> None:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    payload = _valid_payload()
    payload["events"][2]["mutates_data"] = True
    path = tmp_path / "figure_polish_lifecycle.json"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="mutates_data"):
        load_figure_polish_lifecycle(path)

    payload = _valid_payload()
    payload["events"][4]["carries_publication_verdict"] = True
    _write_json(path, payload)

    with pytest.raises(ValueError, match="carries_publication_verdict"):
        load_figure_polish_lifecycle(path)


def test_root_contract_indexes_figure_polish_lifecycle_surface() -> None:
    from med_autoscience.figure_polish_lifecycle_contract import (
        FIGURE_POLISH_LIFECYCLE_BASENAME,
        VALID_LIFECYCLE_STATES,
    )

    contract = json.loads((REPO_ROOT / "contracts" / "figure_polish_lifecycle_contract.json").read_text())

    assert contract["source_module"] == "src/med_autoscience/figure_polish_lifecycle_contract.py"
    assert contract["paper_surface"]["path"] == f"paper/{FIGURE_POLISH_LIFECYCLE_BASENAME}"
    assert contract["paper_surface"]["state_sequence"] == list(VALID_LIFECYCLE_STATES)
    assert contract["relationships"]["figure_visual_audit_receipt"]["surface"] == "figure_visual_audit_receipt"
    assert (
        contract["relationships"]["display_pack_lock_publication_figure_quality_refs"]["field"]
        == "publication_figure_quality_refs"
    )
    assert contract["authority_boundaries"]["ai_vlm_role"] == (
        "quality_loop_and_audit_receipt_only_no_publication_authority"
    )
