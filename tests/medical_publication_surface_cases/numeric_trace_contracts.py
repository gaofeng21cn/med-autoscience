from .shared import *


def test_build_report_projects_numeric_trace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["numeric_trace_present"] is True
    assert report["numeric_trace_valid"] is True


def test_validate_claim_evidence_map_accepts_optional_numeric_trace_refs() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_claim_evidence_map(
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The cohort included 312 eligible patients.",
                    "status": "supported",
                    "paper_role": "main_text",
                    "display_bindings": ["T1"],
                    "sections": ["results"],
                    "evidence_items": [
                        {
                            "item_id": "EV1",
                            "support_level": "direct",
                            "source_paths": ["paper/tables/T1_baseline.csv"],
                            "numeric_trace_refs": ["NT1"],
                        }
                    ],
                }
            ]
        }
    )

    assert errors == []


@pytest.mark.parametrize("numeric_trace_refs", [[], ["NT1", ""], "NT1"])
def test_validate_claim_evidence_map_rejects_invalid_numeric_trace_refs(numeric_trace_refs: object) -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_claim_evidence_map(
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The cohort included 312 eligible patients.",
                    "status": "supported",
                    "paper_role": "main_text",
                    "display_bindings": ["T1"],
                    "sections": ["results"],
                    "evidence_items": [
                        {
                            "item_id": "EV1",
                            "support_level": "direct",
                            "source_paths": ["paper/tables/T1_baseline.csv"],
                            "numeric_trace_refs": numeric_trace_refs,
                        }
                    ],
                }
            ]
        }
    )

    assert errors == [
        "claims[0].evidence_items[0].numeric_trace_refs must contain at least one non-empty string"
    ]


def test_build_report_blocks_missing_numeric_trace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    numeric_trace_path = _paper_root_from_quest(quest_root) / "numeric_trace.json"
    numeric_trace_path.unlink(missing_ok=True)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "numeric_trace_missing_or_incomplete" in report["blockers"]
    assert report["numeric_trace_path"] == str(numeric_trace_path)
    assert report["numeric_trace_present"] is False
    assert report["numeric_trace_valid"] is False


def test_validate_numeric_trace_rejects_missing_mechanical_trace_fields() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_numeric_trace(
        {
            "traces": [
                {
                    "trace_id": "NT1",
                    "claim_id": "C1",
                    "source_paths": ["artifacts/results/main_result.json"],
                }
            ]
        }
    )

    assert errors == [
        "missing traces[0] fields: reported_value, statistic_kind, source_field, "
        "rounding_rule, manuscript_refs, verification_status, evidence_refs"
    ]
