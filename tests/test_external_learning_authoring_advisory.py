from __future__ import annotations

import importlib


def test_paperspine_manuscript_advisory_returns_refs_only_four_ref_families() -> None:
    module = importlib.import_module("med_autoscience.external_learning_authoring_advisory")

    advisory = module.build_paperspine_manuscript_advisory(
        {
            "action_type": "run_quality_repair_batch",
            "refs": {
                "motivation_spine_refs": ["ref:motivation-spine"],
                "writing_rationale_matrix_refs": ["ref:writing-rationale"],
                "evidence_blueprint_refs": ["ref:evidence-blueprint"],
                "latex_safe_audit_refs": ["ref:latex-safe-audit"],
            },
        }
    )

    assert advisory["surface_kind"] == "mas_paperspine_manuscript_advisory"
    assert advisory["refs_only"] is True
    assert advisory["body_included"] is False
    assert advisory["advisory_only"] is True
    assert advisory["motivation_spine_refs"] == ["ref:motivation-spine"]
    assert advisory["writing_rationale_matrix_refs"] == ["ref:writing-rationale"]
    assert advisory["evidence_blueprint_refs"] == ["ref:evidence-blueprint"]
    assert advisory["latex_safe_audit_refs"] == ["ref:latex-safe-audit"]
    assert advisory["status"] == "advisory_ready"
    assert advisory["advisory_gap"] is False
    assert advisory["missing_ref_families"] == []


def test_paperspine_manuscript_advisory_cannot_authorize_publication_quality_or_artifacts() -> None:
    module = importlib.import_module("med_autoscience.external_learning_authoring_advisory")

    advisory = module.build_paperspine_manuscript_advisory(
        {
            "refs": {
                "motivation_spine_refs": ["ref:motivation-spine"],
                "writing_rationale_matrix_refs": ["ref:writing-rationale"],
                "evidence_blueprint_refs": ["ref:evidence-blueprint"],
                "latex_safe_audit_refs": ["ref:latex-safe-audit"],
            },
        }
    )

    assert advisory["allowed_writes"] == []
    assert "artifacts/publication_eval/latest.json" in advisory["forbidden_writes"]
    assert "artifacts/controller_decisions/latest.json" in advisory["forbidden_writes"]
    assert "paper/**" in advisory["forbidden_writes"]
    assert "manuscript/current_package/**" in advisory["forbidden_writes"]
    assert advisory["can_block_current_owner_action"] is False

    boundary = advisory["authority_boundary"]
    assert boundary["can_write_publication_eval"] is False
    assert boundary["can_write_controller_decisions"] is False
    assert boundary["can_write_paper_or_package"] is False
    assert boundary["can_authorize_publication_quality"] is False
    assert boundary["can_authorize_submission_readiness"] is False
    assert boundary["can_authorize_artifact_authority"] is False
    assert boundary["can_close_stage"] is False


def test_paperspine_manuscript_advisory_missing_inputs_fail_open_as_advisory_gap() -> None:
    module = importlib.import_module("med_autoscience.external_learning_authoring_advisory")

    advisory = module.build_paperspine_manuscript_advisory(
        {"refs": {"motivation_spine_refs": ["ref:motivation-spine"]}}
    )

    assert advisory["status"] == "fail_open_advisory_gap"
    assert advisory["advisory_gap"] is True
    assert advisory["can_block_current_owner_action"] is False
    assert advisory["motivation_spine_refs"] == ["ref:motivation-spine"]
    assert advisory["writing_rationale_matrix_refs"] == []
    assert advisory["evidence_blueprint_refs"] == []
    assert advisory["latex_safe_audit_refs"] == []
    assert advisory["missing_ref_families"] == [
        "writing_rationale_matrix_refs",
        "evidence_blueprint_refs",
        "latex_safe_audit_refs",
    ]


def test_paperorchestra_authoring_advisory_returns_refs_only_four_ref_families() -> None:
    module = importlib.import_module("med_autoscience.external_learning_authoring_advisory")

    advisory = module.build_paperorchestra_authoring_advisory(
        {
            "action_type": "run_quality_repair_batch",
            "refs": {
                "authoring_dag_refs": ["ref:authoring-dag"],
                "outline_plot_refs": ["ref:outline-plot"],
                "literature_section_refs": ["ref:literature-section"],
                "autorater_refs": ["ref:autorater"],
            },
        }
    )

    assert advisory["surface_kind"] == "mas_paperorchestra_authoring_advisory"
    assert advisory["framework_id"] == "paperorchestra"
    assert advisory["refs_only"] is True
    assert advisory["body_included"] is False
    assert advisory["advisory_only"] is True
    assert advisory["authoring_dag_refs"] == ["ref:authoring-dag"]
    assert advisory["outline_plot_refs"] == ["ref:outline-plot"]
    assert advisory["literature_section_refs"] == ["ref:literature-section"]
    assert advisory["autorater_refs"] == ["ref:autorater"]
    assert advisory["status"] == "advisory_ready"
    assert advisory["advisory_gap"] is False
    assert advisory["missing_ref_families"] == []
    assert advisory["allowed_writes"] == []
    assert advisory["can_block_current_owner_action"] is False
    assert advisory["authority_boundary"]["can_authorize_publication_quality"] is False


def test_external_learning_closure_marks_authoring_workers_as_refs_only_landed() -> None:
    closure_module = importlib.import_module("med_autoscience.external_learning_adoption_closure")

    closure = closure_module.build_external_learning_adoption_closure()
    frameworks = {item["framework_id"]: item for item in closure["frameworks"]}
    paperspine = frameworks["paperspine"]
    paperorchestra = frameworks["paperorchestra"]

    assert paperspine["closure_status"] == "sidecar_or_worker_landed"
    assert paperspine["owner_surface"] == "paperspine_manuscript_authoring_sidecar_advisory"
    assert "build_paperspine_manuscript_advisory" in paperspine["worker_or_executor_landing"]
    assert paperspine["friction_policy"]["can_block_current_owner_action"] is False
    assert paperspine["authority_boundary"]["can_authorize_publication_quality"] is False
    assert paperorchestra["closure_status"] == "sidecar_or_worker_landed"
    assert paperorchestra["owner_surface"] == "paperorchestra_authoring_sidecar_advisory"
    assert "build_paperorchestra_authoring_advisory" in paperorchestra["worker_or_executor_landing"]
    assert paperorchestra["friction_policy"]["can_block_current_owner_action"] is False
    assert paperorchestra["authority_boundary"]["can_authorize_publication_quality"] is False
