from __future__ import annotations

import importlib
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ready_recommendation_payload() -> dict[str, object]:
    return {
        "figure_id": "F3C",
        "figure_ticket_open": True,
        "storyboard_ready": True,
        "source_artifacts_ready": True,
        "paper_role_allowed": True,
        "non_evidence_figure": True,
        "editable_svg_required": True,
    }


def full_input_contract() -> dict[str, object]:
    return {
        "figure_request": {
            "figure_id": "F3C",
            "figure_type": "method_overview",
            "paper_role": "main_text",
            "title": "Locked multimodal workflow and fusion design",
            "question_answered": "How the locked multimodal workflow is organized",
            "caption_takeaway": "The figure summarizes the locked multimodal workflow without introducing synthetic results.",
        },
        "source_contract": {
            "storyboard_path": "paper/figure_storyboard.md",
            "source_artifacts": [
                "artifacts/runs/run-main-001.json",
                "paper/notes/method.md",
            ],
            "reference_style_paths": ["paper/figures/style_refs/reference.png"],
        },
        "output_contract": {
            "required_formats": ["svg", "pdf", "png"],
            "editable_svg_required": True,
            "caption_safe": True,
        },
        "editing_scope": {
            "allowed": ["layout_refinement", "icon_replacement", "label_cleanup"],
            "forbidden": ["metric_number_editing", "claim_change", "result_plot_generation"],
        },
        "optional_context": {
            "reference_paper": "arxiv:2503.18102",
        },
    }


def provision_payload() -> dict[str, object]:
    payload = full_input_contract()
    payload["user_confirmation"] = {
        "confirmed": True,
        "confirmed_by": "human",
        "confirmed_at": "2026-03-30T08:00:00+00:00",
    }
    return payload


def populate_source_inputs(quest_root: Path) -> None:
    write_text(quest_root / "paper" / "figure_storyboard.md", "# storyboard\n")
    write_text(quest_root / "artifacts" / "runs" / "run-main-001.json", "{}\n")
    write_text(quest_root / "paper" / "notes" / "method.md", "# method\n")
    write_text(quest_root / "paper" / "figures" / "style_refs" / "reference.png", "png")


def populate_handoff(sidecar_root: Path) -> None:
    handoff_root = sidecar_root / "handoff"
    write_text(handoff_root / "final_figure.svg", "<svg></svg>\n")
    write_text(handoff_root / "final_figure.pdf", "%PDF-1.4\n")
    write_text(handoff_root / "preview.png", "png")
    write_text(
        handoff_root / "caption.md",
        "The locked multimodal workflow is summarized without synthetic results.\n",
    )
    write_text(
        handoff_root / "source_trace.json",
        json.dumps(
            {
                "source_artifacts": [
                    {"path": "paper/figure_storyboard.md", "role": "storyboard"},
                    {"path": "artifacts/runs/run-main-001.json", "role": "data_trace"},
                    {"path": "paper/notes/method.md", "role": "method_text"},
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        handoff_root / "figure_catalog_entry.json",
        json.dumps(
            {
                "figure_id": "F3C",
                "title": "Locked multimodal workflow and fusion design",
                "caption": "The locked multimodal workflow is summarized without synthetic results.",
                "paper_role": "main_text",
                "export_files": ["final_figure.svg", "final_figure.pdf", "preview.png"],
                "source_artifacts": ["artifacts/runs/run-main-001.json"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        handoff_root / "sidecar_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "sidecar_id": "autofigure_edit",
                "provider": "autofigure_edit",
                "status": "result_ready",
                "input_contract_hash": "placeholder",
                "figure_id": "F3C",
                "artifacts_generated": [
                    "final_figure.svg",
                    "final_figure.pdf",
                    "preview.png",
                    "caption.md",
                    "source_trace.json",
                    "figure_catalog_entry.json",
                    "sidecar_manifest.json",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )


def test_recommend_autofigure_edit_sidecar_returns_recommended_when_figure_route_is_ready(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autofigure_edit_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    result = module.recommend_autofigure_edit_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )

    assert result["status"] == "recommended"
    assert result["instance_id"] == "F3C"
    recommendation = load_json(quest_root / "sidecars" / "autofigure_edit" / "F3C" / "recommendation.json")
    assert recommendation["status"] == "awaiting_user_confirmation"


def test_provision_autofigure_edit_sidecar_writes_frozen_contract_and_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autofigure_edit_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    module.recommend_autofigure_edit_sidecar(quest_root=quest_root, payload=ready_recommendation_payload())

    result = module.provision_autofigure_edit_sidecar(
        quest_root=quest_root,
        payload=provision_payload(),
    )

    sidecar_root = quest_root / "sidecars" / "autofigure_edit" / "F3C"
    state = load_json(sidecar_root / "sidecar_state.json")
    contract = load_json(sidecar_root / "input_contract.json")

    assert result["status"] == "contract_frozen"
    assert result["sidecar_root"] == str(sidecar_root)
    assert contract["figure_request"]["figure_id"] == "F3C"
    assert state["provider"] == "autofigure_edit"
    assert state["instance_id"] == "F3C"


def test_import_autofigure_edit_sidecar_result_copies_imported_figure_audit_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autofigure_edit_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    populate_source_inputs(quest_root)
    module.recommend_autofigure_edit_sidecar(quest_root=quest_root, payload=ready_recommendation_payload())
    provision = module.provision_autofigure_edit_sidecar(quest_root=quest_root, payload=provision_payload())
    sidecar_root = Path(provision["sidecar_root"])
    populate_handoff(sidecar_root)

    handoff_manifest = load_json(sidecar_root / "handoff" / "sidecar_manifest.json")
    handoff_manifest["input_contract_hash"] = provision["input_contract_hash"]
    write_text(
        sidecar_root / "handoff" / "sidecar_manifest.json",
        json.dumps(handoff_manifest, ensure_ascii=False, indent=2) + "\n",
    )

    result = module.import_autofigure_edit_sidecar_result(
        quest_root=quest_root,
        figure_id="F3C",
    )

    artifact_root = quest_root / "artifacts" / "figures" / "autofigure_edit" / "F3C"
    imported_manifest = load_json(artifact_root / "sidecar_manifest.json")
    figure_catalog_entry = load_json(artifact_root / "figure_catalog_entry.json")

    assert result["status"] == "imported"
    assert imported_manifest["provider"] == "autofigure_edit"
    assert imported_manifest["figure_catalog_entry"]["figure_id"] == "F3C"
    assert figure_catalog_entry["export_paths"] == [
        "artifacts/figures/autofigure_edit/F3C/final_figure.svg",
        "artifacts/figures/autofigure_edit/F3C/final_figure.pdf",
        "artifacts/figures/autofigure_edit/F3C/preview.png",
    ]


def test_resolve_autofigure_edit_sidecar_artifacts_reads_imported_surface_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autofigure_edit_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    populate_source_inputs(quest_root)
    module.recommend_autofigure_edit_sidecar(quest_root=quest_root, payload=ready_recommendation_payload())
    provision = module.provision_autofigure_edit_sidecar(quest_root=quest_root, payload=provision_payload())
    sidecar_root = Path(provision["sidecar_root"])
    populate_handoff(sidecar_root)

    handoff_manifest = load_json(sidecar_root / "handoff" / "sidecar_manifest.json")
    handoff_manifest["input_contract_hash"] = provision["input_contract_hash"]
    write_text(
        sidecar_root / "handoff" / "sidecar_manifest.json",
        json.dumps(handoff_manifest, ensure_ascii=False, indent=2) + "\n",
    )
    module.import_autofigure_edit_sidecar_result(quest_root=quest_root, figure_id="F3C")
    write_text(sidecar_root / "handoff" / "final_figure.svg", "<svg>stale</svg>\n")

    resolved = module.resolve_autofigure_edit_sidecar_artifacts(quest_root=quest_root, figure_id="F3C")

    assert resolved["status"] == "imported"
    assert resolved["artifacts"]["final_figure.svg"].endswith("/artifacts/figures/autofigure_edit/F3C/final_figure.svg")
