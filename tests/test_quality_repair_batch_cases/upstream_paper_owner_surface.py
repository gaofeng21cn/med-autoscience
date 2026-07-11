from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.test_paper_owner_surface import (
    _analysis_claim_evidence_repair_route_context,
    _write_blocked_publication_eval,
    _write_json,
    _write_quality_summary,
)


def _study(tmp_path: Path):
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="descriptive",
        manuscript_family="observational",
    )
    return profile, study_root, "quest-001"


def test_quality_repair_batch_routes_to_producer_and_materializes_owner_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile, study_root, quest_id = _study(tmp_path)
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nBounded cohort claim.\n", encoding="utf-8")
    for relative_path in ("claim_evidence_map.json", "evidence_ledger.json"):
        _write_json(paper_root / relative_path, {"schema_version": 1, "claims": []})
    _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: SimpleNamespace(paper_root=paper_root),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
            "blocking_artifact_refs": [],
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::blocked",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "selected_publication_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            "gate_replay": {"status": "blocked", "blockers": ["claim_evidence_consistency_failed"]},
            "unit_results": [],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=_analysis_claim_evidence_repair_route_context(),
    )

    upstream = result["gate_clearing_batch"]["unit_results"][0]
    assert upstream["unit_id"] == "analysis_claim_evidence_repair"
    assert upstream["status"] == "updated"
    changed = {Path(path) for path in upstream["result"]["changed_artifact_refs"]}
    assert {
        paper_root / "claim_evidence_map.json",
        paper_root / "evidence_ledger.json",
        paper_root / "review" / "review_ledger.json",
    } <= changed
    for relative_path in ("claim_evidence_map.json", "evidence_ledger.json"):
        payload = json.loads((paper_root / relative_path).read_text(encoding="utf-8"))
        assert payload["controller_repair_receipts"][-1]["work_unit_id"] == (
            "analysis_claim_evidence_repair"
        )
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert upstream["result"]["ai_reviewer_recheck_request_ref"] == str(request_path)
    assert request["request_owner"] == "ai_reviewer"
    assert request["source_surface"] == "quality_repair_batch"


def test_canonical_paper_owner_surface_rejects_untrusted_projection(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_paper_owner_surface")
    profile, study_root, quest_id = _study(tmp_path)
    projected_root = profile.runtime_root / quest_id / "paper"
    (projected_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (projected_root / "draft.md").write_text("# Projected draft\n", encoding="utf-8")
    _write_json(projected_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(projected_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(projected_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(projected_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})

    result = module.prepare_canonical_paper_owner_surface_for_upstream_repair(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        gate_state=SimpleNamespace(paper_root=None),
        authority_route_gate={"action": "paper_write"},
    )

    assert result["status"] == "blocked_missing_authorized_canonical_inputs"
    assert set(result["blocked_canonical_source_surfaces"]) == {
        "paper/medical_manuscript_blueprint.json",
        "paper/medical_prose_review.json",
    }
    assert not (study_root / "paper" / "medical_manuscript_blueprint.json").exists()
    assert not (study_root / "paper" / "medical_prose_review.json").exists()
