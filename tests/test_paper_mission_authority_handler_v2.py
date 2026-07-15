from __future__ import annotations

import ast
from copy import deepcopy
import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDLER_SOURCE = ROOT / "src/med_autoscience/authority_handlers/paper_mission.py"


def _digest(character: str) -> str:
    return f"sha256:{character * 64}"


def _ref(kind: str, name: str, character: str) -> dict[str, str]:
    return {
        "kind": kind,
        "ref": f"{kind}://{name}",
        "sha256": _digest(character),
    }


def _request() -> dict[str, object]:
    return {
        "surface_kind": "mas_paper_mission_authority_request",
        "schema_version": 1,
        "host_context": {
            "action_id": "paper_mission",
            "run_ref": _ref("opl_stage_run", "run-001", "a"),
            "producer_attempt_ref": _ref("opl_stage_attempt", "producer", "b"),
            "output_ref": _ref("opl_action_output", "output-001", "c"),
            "output_state": "consumable",
        },
        "mission": {
            "program_id": "program-dm",
            "study_id": "dm002",
            "mission_id": "paper-mission-dm002",
            "stage_id": "manuscript_authoring",
            "stage_goal_ref": _ref("mas_stage_goal", "manuscript", "d"),
        },
        "medical_evidence": {
            "source_readiness_status": "ready",
            "source_readiness_receipt_ref": _ref(
                "mas_source_readiness_receipt", "source", "e"
            ),
            "claim_evidence_status": "aligned",
            "claim_boundary_ref": _ref("mas_claim_boundary", "claims", "f"),
            "candidate_artifact_refs": [_ref("mas_artifact", "manuscript", "1")],
            "evidence_refs": [_ref("mas_evidence", "ledger", "2")],
            "negative_result_refs": [_ref("mas_negative_result", "negative", "3")],
            "failed_path_refs": [_ref("mas_failed_path", "failed", "4")],
            "artifact_lineage_refs": [
                _ref("mas_artifact_lineage", "lineage", "5")
            ],
            "reproducibility_refs": [
                _ref("mas_reproducibility", "reproducibility", "6")
            ],
        },
        "independent_review": {
            "status": "passed",
            "reviewer_attempt_ref": _ref("opl_stage_attempt", "reviewer", "7"),
            "reviewer_receipt_ref": _ref("mas_reviewer_receipt", "review", "8"),
            "rubric_ref": _ref("mas_quality_rubric", "rubric", "9"),
            "reviewed_output_sha256": _digest("c"),
            "defect_refs": [],
            "quality_debt_codes": [],
        },
        "repair_state": {
            "status": "not_required",
            "attempts_used": 0,
            "max_attempts": 3,
            "repair_attempt_refs": [],
            "latest_repair_output_ref": None,
        },
        "hard_gate": {
            "kind": "none",
            "reason_code": None,
            "evidence_refs": [],
            "next_owner": None,
            "resume_condition": None,
        },
    }


def _evaluate(request: dict[str, object]) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.authority_handlers.paper_mission")
    return module.evaluate_paper_mission_authority(request)


def test_passed_independent_review_returns_deterministic_owner_receipt() -> None:
    request = _request()
    original = deepcopy(request)

    first = _evaluate(request)
    second = _evaluate(request)

    assert request == original
    assert first == second
    assert first["status"] == "owner_receipt"
    assert first["stage_outcome"] == {
        "kind": "completed",
        "stage_transition_allowed": True,
        "selects_next_stage": False,
        "publication_or_submission_ready": False,
    }
    assert first["owner_receipt"]["owner"] == "MedAutoScience"
    assert first["owner_receipt"]["authorizes_stage_domain_completion"] is True
    assert first["owner_receipt"]["authorizes_publication_or_submission"] is False
    assert first["authority_boundary"]["performs_filesystem_io"] is False
    assert first["authority_boundary"]["spawns_process_or_executor"] is False


def test_unknown_transport_fields_and_attempt_identity_drift_fail_closed() -> None:
    unknown = _request()
    unknown["workspace_root"] = "/tmp/private-discovery"
    assert _evaluate(unknown)["status"] == "invalid_host_input"

    same_attempt = _request()
    same_attempt["independent_review"]["reviewer_attempt_ref"] = deepcopy(
        same_attempt["host_context"]["producer_attempt_ref"]
    )
    result = _evaluate(same_attempt)
    assert result["status"] == "invalid_host_input"
    assert "reviewer attempt must differ" in result["error"]["detail"]

    digest_drift = _request()
    digest_drift["independent_review"]["reviewed_output_sha256"] = _digest("f")
    result = _evaluate(digest_drift)
    assert result["status"] == "invalid_host_input"
    assert "exact hosted output digest" in result["error"]["detail"]


def test_source_gap_and_repair_budget_preserve_progress_semantics() -> None:
    source_gap = _request()
    source_gap["medical_evidence"]["source_readiness_status"] = "unknown"
    source_gap["medical_evidence"]["source_readiness_receipt_ref"] = None
    result = _evaluate(source_gap)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == "source_readiness_record_required"
    assert result["typed_blocker"] is None

    repair = _request()
    repair["independent_review"]["status"] = "revision_required"
    repair["independent_review"]["defect_refs"] = [
        _ref("mas_review_defect", "claim-wording", "0")
    ]
    repair["repair_state"] = {
        "status": "exhausted",
        "attempts_used": 3,
        "max_attempts": 3,
        "repair_attempt_refs": [
            _ref("opl_stage_attempt", f"repair-{index}", str(index))
            for index in range(1, 4)
        ],
        "latest_repair_output_ref": _ref("opl_action_output", "repair-output", "4"),
    }
    result = _evaluate(repair)
    assert result["status"] == "completed_with_quality_debt"
    assert result["stage_outcome"]["stage_transition_allowed"] is True
    assert "repair_budget_exhausted" in result["quality_debt"]["reason_codes"]


def test_only_typed_hard_or_human_gate_stops_transition() -> None:
    typed = _request()
    typed["hard_gate"] = {
        "kind": "medical_safety",
        "reason_code": "adverse_event_identity_unresolved",
        "evidence_refs": [_ref("mas_gate_evidence", "safety", "f")],
        "next_owner": "medical_safety_owner",
        "resume_condition": "resolve the adverse-event identity conflict",
    }
    result = _evaluate(typed)
    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["blocks_stage_transition"] is True

    human = _request()
    human["hard_gate"] = {
        "kind": "human_decision",
        "reason_code": "journal_scope_choice_required",
        "evidence_refs": [_ref("mas_gate_evidence", "journal-options", "e")],
        "next_owner": "human_principal_investigator",
        "resume_condition": "select the publication scope",
    }
    result = _evaluate(human)
    assert result["status"] == "human_gate"
    assert result["human_gate"]["blocks_stage_transition"] is True


def test_handler_has_no_private_transport_or_generic_io_closure() -> None:
    tree = ast.parse(HANDLER_SOURCE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    called_attributes: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_attributes.add(node.func.attr)

    assert imports == {"__future__", "hashlib", "json", "collections.abc", "typing"}
    assert not called_names & {"open", "exec", "eval", "compile", "__import__", "system"}
    assert not called_attributes & {
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "open",
        "connect",
        "Popen",
        "run",
        "spawn",
    }


def test_registry_schemas_and_functional_audit_bind_the_exact_handler() -> None:
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    audit = json.loads(
        (ROOT / "contracts/functional_privatization_audit.json").read_text(
            encoding="utf-8"
        )
    )
    input_schema = json.loads(
        (ROOT / "contracts/schemas/v2/mas-paper-mission-authority.input.schema.json")
        .read_text(encoding="utf-8")
    )
    output_schema = json.loads(
        (ROOT / "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json")
        .read_text(encoding="utf-8")
    )

    assert registry["handlers"] == [
        {
            "handler_id": "mas.paper-mission-authority-evaluate",
            "binding": {
                "kind": "python_callable",
                "module": "med_autoscience.authority_handlers.paper_mission",
                "callable": "evaluate_paper_mission_authority",
            },
        },
        {
            "handler_id": "mas.agent-lab-self-evolution-closeout",
            "binding": {
                "kind": "python_callable",
                "module": "med_autoscience.authority_handlers.self_evolution_closeout",
                "callable": "evaluate_agent_lab_self_evolution_closeout",
            },
        },
    ]
    assert input_schema["additionalProperties"] is False
    assert set(output_schema["properties"]["status"]["enum"]) == {
        "owner_receipt",
        "route_back",
        "completed_with_quality_debt",
        "typed_blocker",
        "human_gate",
        "invalid_host_input",
    }
    assert [module["module_id"] for module in audit["modules"]] == [
        "mas.paper_mission_authority",
        "mas.agent_lab_self_evolution_closeout",
    ]
    assert audit["modules"][0]["code_paths"][0] == (
        "src/med_autoscience/authority_handlers/paper_mission.py"
    )
