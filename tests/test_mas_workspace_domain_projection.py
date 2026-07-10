from __future__ import annotations

import json

from med_autoscience.controllers.current_work_unit.workspace_projection import (
    build_workspace_domain_projection,
)


def test_workspace_domain_projection_exposes_mas_refs_without_operator_aggregation() -> None:
    projection = build_workspace_domain_projection(
        study_progress_payloads=[
            {
                "study_id": "study-001",
                "quest_id": "quest-001",
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "medical_writer",
                    "stage_id": "manuscript_authoring",
                    "action_type": "write_revision",
                    "work_unit_id": "revise-results",
                    "work_unit_fingerprint": "sha256:work-unit",
                    "input_refs": ["mas:paper/results.md"],
                    "acceptance_refs": ["mas:review/latest.json"],
                    "currentness_basis": {"derived_from_event_id": "event-001"},
                },
                "current_owner_delta": {"next_owner": "medical_writer"},
                "publication_eval": {"status": "revision_required"},
                "current_blockers": ["claim_evidence_gap", ""],
                "recommended_command": "must-not-leak",
            }
        ]
    )

    assert projection["surface_kind"] == "opl_domain_projection"
    assert projection["domain_id"] == "medautoscience"
    assert projection["projection_role"] == "registry_driven_domain_current_work_units"
    current = projection["current_work_units"][0]
    assert current["surface_kind"] == "opl_domain_current_work_unit_profile_projection"
    assert current["work_unit_id"] == "revise-results"
    assert current["current_owner"] == "medical_writer"
    assert current["stage_id"] == "manuscript_authoring"
    assert current["source_refs"] == [
        "mas:paper/results.md",
        "mas:review/latest.json",
    ]
    assert current["authority_boundary"]["can_write_current_owner_delta"] is False
    assert current["domain_display"] == {
        "study_id": "study-001",
        "quest_id": "quest-001",
        "current_owner_delta": {"next_owner": "medical_writer"},
        "publication_eval": {"status": "revision_required"},
        "current_blockers": ["claim_evidence_gap"],
    }
    assert projection["domain_display"] == {
        "surface_kind": "mas_workspace_domain_display",
        "opaque_to_opl": True,
        "studies": [
        {
            "study_id": "study-001",
            "quest_id": "quest-001",
            "current_owner_delta": {"next_owner": "medical_writer"},
            "publication_eval": {"status": "revision_required"},
            "current_blockers": ["claim_evidence_gap"],
        }
        ],
    }
    assert projection["opl_hosted_projection"] == {
        "owner": "one-person-lab",
        "operator_projection_ref": (
            "one-person-lab:src/modules/console/runtime-tray-app-operator-drilldown.ts"
        ),
        "current_owner_delta_ref": (
            "one-person-lab:src/modules/ledger/current-owner-delta-parts/projection.ts"
        ),
        "mas_materializes_workspace_cockpit": False,
        "mas_aggregates_operator_attention": False,
        "mas_generates_operator_commands": False,
    }
    rendered = json.dumps(projection, ensure_ascii=False)
    assert "must-not-leak" not in rendered
    assert "attention_queue" not in projection
    assert "commands" not in projection
