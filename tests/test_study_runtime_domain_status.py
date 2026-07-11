from __future__ import annotations

import importlib

import pytest


def _modules():
    return (
        importlib.import_module("med_autoscience.controllers.domain_status_projection"),
        importlib.import_module("med_autoscience.controllers.progress_projection.runtime_result_types"),
    )


@pytest.mark.parametrize(
    ("analysis", "reporting", "expected_status", "expected_blockers"),
    [
        ({"status": "resolved", "reason_code": "analysis_ok"}, {"status": "resolved"}, "clear", ()),
        (
            {"status": "unsupported", "reason_code": "unsupported_family"},
            "invalid",
            "blocked",
            ("unsupported_medical_analysis_contract", "invalid_medical_reporting_contract"),
        ),
        (
            {"status": "draft", "reason_code": "needs_mapping"},
            None,
            "blocked",
            ("unresolved_medical_analysis_contract", "missing_medical_reporting_contract"),
        ),
    ],
)
def test_validate_startup_contract_resolution_preserves_domain_classification(
    analysis: object,
    reporting: object,
    expected_status: str,
    expected_blockers: tuple[str, ...],
) -> None:
    owner, _types = _modules()

    result = owner.validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": analysis,
            "medical_reporting_contract_summary": reporting,
        }
    )

    assert result.status.value == expected_status
    assert result.blockers == expected_blockers


def test_startup_contract_validation_round_trips_typed_payload() -> None:
    _owner, types = _modules()
    payload = {
        "status": "clear",
        "blockers": [],
        "contract_statuses": {
            "medical_analysis_contract": "resolved",
            "medical_reporting_contract": "resolved",
        },
        "reason_codes": {
            "medical_analysis_contract": "analysis_ok",
            "medical_reporting_contract": "reporting_ok",
        },
    }

    result = types.StartupContractValidation.from_payload(payload)

    assert result.to_dict() == payload


def test_startup_contract_validation_rejects_unknown_status() -> None:
    _owner, types = _modules()

    with pytest.raises(ValueError, match="unknown startup contract validation status"):
        types.StartupContractValidation(
            status="unexpected",
            blockers=(),
            medical_analysis_contract_status=None,
            medical_reporting_contract_status=None,
            medical_analysis_reason_code=None,
            medical_reporting_reason_code=None,
        )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ({"decision": "blocked", "quest_exists": True, "quest_status": "created", "reason": "startup_boundary_not_ready_for_resume"}, True),
        ({"decision": "resume", "quest_exists": True, "quest_status": "created", "reason": "startup_boundary_not_ready_for_resume"}, False),
        ({"decision": "blocked", "quest_exists": False, "quest_status": "created", "reason": "startup_boundary_not_ready_for_resume"}, False),
    ],
)
def test_should_refresh_startup_hydration_for_runtime_hold(status: dict[str, object], expected: bool) -> None:
    owner, _types = _modules()

    assert owner.should_refresh_startup_hydration_for_runtime_hold(status) is expected
