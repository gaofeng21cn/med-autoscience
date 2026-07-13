from __future__ import annotations

import ast
from copy import deepcopy
import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HANDLER_SOURCE = REPO_ROOT / "src/med_autoscience/authority_handlers/paper_mission.py"
REGISTRY_PATH = REPO_ROOT / "contracts/domain_handler_registry.json"
PARITY_PATH = REPO_ROOT / "contracts/paper_mission_authority_handler_parity.json"
INPUT_SCHEMA_PATH = (
    REPO_ROOT / "contracts/schemas/v2/mas-paper-mission-authority.input.schema.json"
)
OUTPUT_SCHEMA_PATH = (
    REPO_ROOT / "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json"
)
AUTHORITY_INVENTORY_PATH = REPO_ROOT / "contracts/authority_kernel_inventory.json"


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
            "producer_attempt_ref": _ref("opl_stage_attempt", "attempt-producer", "b"),
            "output_ref": _ref("opl_action_output", "output-001", "c"),
            "output_state": "consumable",
        },
        "mission": {
            "program_id": "program-dm",
            "study_id": "dm002",
            "mission_id": "paper-mission-dm002",
            "stage_id": "manuscript_authoring",
            "stage_goal_ref": _ref("mas_stage_goal", "manuscript-authoring", "d"),
        },
        "medical_evidence": {
            "source_readiness_status": "ready",
            "source_readiness_receipt_ref": _ref(
                "mas_source_readiness_receipt", "dm002-source", "e"
            ),
            "claim_evidence_status": "aligned",
            "claim_boundary_ref": _ref("mas_claim_boundary", "dm002-claims", "f"),
            "candidate_artifact_refs": [_ref("mas_artifact", "manuscript", "1")],
            "evidence_refs": [_ref("mas_evidence", "evidence-ledger", "2")],
            "negative_result_refs": [_ref("mas_negative_result", "negative-1", "3")],
            "failed_path_refs": [_ref("mas_failed_path", "failed-path-1", "4")],
            "artifact_lineage_refs": [
                _ref("mas_artifact_lineage", "manuscript-lineage", "5")
            ],
            "reproducibility_refs": [
                _ref("mas_reproducibility", "analysis-reproducibility", "6")
            ],
        },
        "independent_review": {
            "status": "passed",
            "reviewer_attempt_ref": _ref("opl_stage_attempt", "attempt-reviewer", "7"),
            "reviewer_receipt_ref": _ref("mas_reviewer_receipt", "review-001", "8"),
            "rubric_ref": _ref("mas_quality_rubric", "manuscript-rubric", "9"),
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
    receipt = first["owner_receipt"]
    assert receipt["owner"] == "MedAutoScience"
    assert receipt["authorizes_stage_domain_completion"] is True
    assert receipt["authorizes_publication_or_submission"] is False
    assert receipt["independent_reviewer_attempt_ref"]["ref"].endswith("attempt-reviewer")
    assert receipt["negative_result_refs"] == original["medical_evidence"][
        "negative_result_refs"
    ]
    assert receipt["failed_path_refs"] == original["medical_evidence"]["failed_path_refs"]
    assert first["decision_fingerprint"].startswith("sha256:")
    assert first["authority_boundary"]["performs_filesystem_io"] is False
    assert first["authority_boundary"]["spawns_process_or_executor"] is False


def test_profile_path_and_unknown_transport_fields_fail_closed() -> None:
    request = _request()
    request["profile_ref"] = "/tmp/profile.toml"

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "unsupported fields: profile_ref" in result["error"]["detail"]
    assert result["host_refs"] is None
    assert result["owner_receipt"] is None


def test_reviewer_must_be_a_separate_attempt_bound_to_exact_output() -> None:
    same_attempt = _request()
    same_attempt["independent_review"]["reviewer_attempt_ref"] = deepcopy(
        same_attempt["host_context"]["producer_attempt_ref"]
    )
    same_attempt_result = _evaluate(same_attempt)
    assert same_attempt_result["status"] == "invalid_host_input"
    assert "reviewer attempt must differ" in same_attempt_result["error"]["detail"]

    digest_drift = _request()
    digest_drift["independent_review"]["reviewed_output_sha256"] = _digest("f")
    digest_drift_result = _evaluate(digest_drift)
    assert digest_drift_result["status"] == "invalid_host_input"
    assert "exact hosted output digest" in digest_drift_result["error"]["detail"]


def test_source_or_claim_gap_routes_back_without_typed_blocker() -> None:
    request = _request()
    request["medical_evidence"]["source_readiness_status"] = "unknown"
    request["medical_evidence"]["source_readiness_receipt_ref"] = None

    result = _evaluate(request)

    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == "source_readiness_record_required"
    assert result["typed_blocker"] is None
    assert result["stage_outcome"]["stage_transition_allowed"] is False


def test_owner_receipt_requires_evidence_or_negative_result_ref() -> None:
    request = _request()
    request["medical_evidence"]["evidence_refs"] = []
    request["medical_evidence"]["negative_result_refs"] = []

    result = _evaluate(request)

    assert result["status"] == "route_back"
    assert result["owner_receipt"] is None
    assert result["route_back"]["reason_code"] == "medical_evidence_record_required"
    assert result["stage_outcome"]["stage_transition_allowed"] is False


def test_repairable_review_routes_back_then_exhaustion_advances_with_quality_debt() -> None:
    request = _request()
    request["independent_review"]["status"] = "revision_required"
    request["independent_review"]["defect_refs"] = [
        _ref("mas_review_defect", "claim-wording", "0")
    ]
    request["repair_state"] = {
        "status": "pending",
        "attempts_used": 1,
        "max_attempts": 3,
        "repair_attempt_refs": [_ref("opl_stage_attempt", "repair-1", "1")],
        "latest_repair_output_ref": _ref("opl_action_output", "repair-output-1", "2"),
    }

    route_back = _evaluate(request)

    assert route_back["status"] == "route_back"
    assert route_back["route_back"]["remaining_repair_attempts"] == 2
    assert route_back["stage_outcome"]["stage_transition_allowed"] is False

    request["repair_state"] = {
        "status": "exhausted",
        "attempts_used": 3,
        "max_attempts": 3,
        "repair_attempt_refs": [
            _ref("opl_stage_attempt", "repair-1", "1"),
            _ref("opl_stage_attempt", "repair-2", "2"),
            _ref("opl_stage_attempt", "repair-3", "3"),
        ],
        "latest_repair_output_ref": _ref("opl_action_output", "repair-output-3", "4"),
    }
    exhausted = _evaluate(request)

    assert exhausted["status"] == "completed_with_quality_debt"
    assert exhausted["stage_outcome"]["stage_transition_allowed"] is True
    assert exhausted["quality_debt"][
        "blocks_quality_publication_export_and_submission_claims"
    ] is True
    assert "repair_budget_exhausted" in exhausted["quality_debt"]["reason_codes"]


def test_no_output_or_missing_reviewer_advances_only_with_quality_debt() -> None:
    no_output = _request()
    no_output["host_context"]["output_state"] = "no_output"
    no_output["medical_evidence"]["candidate_artifact_refs"] = []

    no_output_result = _evaluate(no_output)

    assert no_output_result["status"] == "completed_with_quality_debt"
    assert no_output_result["owner_receipt"] is None
    assert no_output_result["route_back"]["reason_code"] == "consumable_output_missing"

    no_review = _request()
    no_review["independent_review"] = {
        "status": "not_run",
        "reviewer_attempt_ref": None,
        "reviewer_receipt_ref": None,
        "rubric_ref": None,
        "reviewed_output_sha256": None,
        "defect_refs": [],
        "quality_debt_codes": [],
    }

    no_review_result = _evaluate(no_review)

    assert no_review_result["status"] == "completed_with_quality_debt"
    assert no_review_result["route_back"]["next_owner"] == "independent_reviewer"
    assert no_review_result["quality_debt"]["counts_as_owner_acceptance"] is False


def test_only_explicit_hard_or_human_gate_blocks_stage_transition() -> None:
    typed = _request()
    typed["hard_gate"] = {
        "kind": "medical_safety",
        "reason_code": "adverse_event_identity_unresolved",
        "evidence_refs": [_ref("mas_gate_evidence", "safety-record", "f")],
        "next_owner": "medical_safety_owner",
        "resume_condition": "resolve the adverse-event identity conflict",
    }
    typed_result = _evaluate(typed)
    assert typed_result["status"] == "typed_blocker"
    assert typed_result["typed_blocker"]["blocks_stage_transition"] is True
    assert typed_result["owner_receipt"] is None

    human = _request()
    human["hard_gate"] = {
        "kind": "human_decision",
        "reason_code": "journal_scope_choice_required",
        "evidence_refs": [_ref("mas_gate_evidence", "journal-options", "e")],
        "next_owner": "human_principal_investigator",
        "resume_condition": "select the publication scope",
    }
    human_result = _evaluate(human)
    assert human_result["status"] == "human_gate"
    assert human_result["human_gate"]["blocks_stage_transition"] is True
    assert human_result["typed_blocker"] is None


def test_none_hard_gate_cannot_smuggle_gate_fields() -> None:
    request = _request()
    request["hard_gate"]["reason_code"] = "hidden_gate"

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "none requires an empty gate record" in result["error"]["detail"]


def test_handler_source_has_no_private_transport_or_generic_io_closure() -> None:
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
    assert not called_names & {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "system",
    }
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


def test_registry_schemas_parity_and_authority_inventory_are_consistent() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    parity = json.loads(PARITY_PATH.read_text(encoding="utf-8"))
    input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(AUTHORITY_INVENTORY_PATH.read_text(encoding="utf-8"))

    assert registry["state"] == "candidate_pending_opl_v2_host_binding"
    assert registry["active_runtime_binding"] is False
    handler = registry["handlers"][0]
    assert handler["binding"] == {
        "kind": "python_callable",
        "module": "med_autoscience.authority_handlers.paper_mission",
        "callable": "evaluate_paper_mission_authority",
    }
    assert set(handler["forbidden_effects"]) >= {
        "profile_or_path_discovery",
        "filesystem_read_or_write",
        "process_spawn",
        "opl_or_codex_invoke",
        "queue_or_session_mutation",
        "runtime_ledger_read_or_write",
    }
    assert input_schema["additionalProperties"] is False
    assert "profile_ref" not in input_schema["properties"]
    assert "workspace_root" not in input_schema["properties"]
    hard_gate_condition = input_schema["properties"]["hard_gate"]["allOf"][0]
    assert hard_gate_condition["if"]["properties"]["kind"] == {"const": "none"}
    assert hard_gate_condition["then"]["properties"]["evidence_refs"] == {
        "maxItems": 0
    }
    assert hard_gate_condition["else"]["properties"]["evidence_refs"] == {
        "minItems": 1
    }
    assert set(output_schema["properties"]["status"]["enum"]) == set(handler["returns"])
    terminal_contracts = {
        item["if"]["properties"]["status"]["const"]: item["then"]["properties"]
        for item in output_schema["allOf"]
    }
    assert set(terminal_contracts) == set(handler["returns"])
    assert terminal_contracts["owner_receipt"]["owner_receipt"] == {
        "$ref": "#/$defs/owner_receipt"
    }
    assert terminal_contracts["route_back"]["owner_receipt"] == {"type": "null"}
    assert terminal_contracts["invalid_host_input"]["host_refs"] == {"type": "null"}

    behavior_ids = {item["behavior_id"] for item in parity["active_behavior_inventory"]}
    assert {
        "paper_mission.profile_workspace_discovery",
        "paper_mission.inspect_and_readback",
        "paper_mission.medical_source_and_evidence_semantics",
        "paper_mission.independent_review_quality",
        "paper_mission.repair_budget_and_route_back",
        "paper_mission.owner_receipt_blocker_human_gate",
        "paper_mission.candidate_and_artifact_persistence",
        "mainline.private_product_status_shell",
        "private_transport.domain_handler_export_queue",
        "private_transport.domain_handler_dispatch_task_path",
        "private_transport.owner_surface_queue_daemon_projection",
    } <= behavior_ids
    assert all(item["legacy_retained_until_cutover"] for item in parity["active_behavior_inventory"])
    assert parity["retirement_authorized"] is False
    assert all(gate["status"] != "done" for gate in parity["cutover_gates"])

    authority_item = next(
        item
        for item in inventory["items"]
        if item["item_id"] == "paper_mission_authority_handler.evaluate_hosted_result"
    )
    assert authority_item["allowed_writes"] == []
    assert authority_item["disposition"] == "retained_minimal_authority_function"
    assert authority_item["no_active_caller"] == "not_yet_active_pending_opl_v2_host_binding"
