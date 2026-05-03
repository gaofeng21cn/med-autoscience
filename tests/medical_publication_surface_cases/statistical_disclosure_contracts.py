from .shared import *


def test_build_report_blocks_missing_statistical_reviewer_audit(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_statistical_reviewer_audit=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "statistical_reviewer_audit_missing_or_incomplete" in report["blockers"]
    assert report["statistical_reviewer_audit_present"] is False
    assert report["statistical_reviewer_audit_reason_code"] == "missing_statistical_reviewer_audit"


def test_build_report_blocks_unresolved_statistical_review_domain(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    audit_path = _paper_root_from_quest(quest_root) / "review" / "statistical_reviewer_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["sections"]["sample_size_or_precision"]["status"] = "open"
    audit["sections"]["sample_size_or_precision"]["assessment"] = "Precision support remains unresolved."
    dump_json(audit_path, audit)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "statistical_reviewer_audit_missing_or_incomplete" in report["blockers"]
    assert report["statistical_reviewer_audit_reason_code"] == "sample_size_or_precision_not_passed"
    assert any(hit["phrase"] == "sample_size_or_precision_not_passed" for hit in report["top_hits"])


def test_build_report_blocks_missing_structured_disclosure_audit(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_disclosure_audit=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "structured_disclosure_audit_missing_or_incomplete" in report["blockers"]
    assert report["structured_disclosure_audit_present"] is False
    assert any(hit["pattern_id"] == "structured_disclosure_audit" for hit in report["top_hits"])


def test_build_report_requires_disclosure_data_asset_evidence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    audit_path = _paper_root_from_quest(quest_root) / "review" / "structured_disclosure_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["data_asset_evidence"].pop("privacy_evidence")
    dump_json(audit_path, audit)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "structured_disclosure_audit_missing_or_incomplete" in report["blockers"]
    assert any(
        hit["pattern_id"] == "structured_disclosure_audit" and "privacy_evidence" in hit["excerpt"]
        for hit in report["top_hits"]
    )


def test_build_report_carries_statistical_and_disclosure_audits_when_clear(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["statistical_reviewer_audit_valid"] is True
    assert report["structured_disclosure_audit_valid"] is True
