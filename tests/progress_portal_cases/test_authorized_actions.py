from __future__ import annotations

import importlib
import io
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile
from tests.test_progress_portal import _progress_payload


def test_progress_portal_authorized_actions_write_idempotent_controller_receipt(tmp_path: Path) -> None:
    actions = importlib.import_module("med_autoscience.controllers.progress_portal_parts.authorized_actions")
    profile = make_profile(tmp_path)

    first = actions.write_action_receipt(
        profile=profile,
        action="pause",
        study_id="001-risk",
        idempotency_key="portal-action-001",
        requested_at="2026-05-09T01:00:00+00:00",
    )
    receipt_path = (
        profile.workspace_root
        / "artifacts"
        / "runtime"
        / "progress_portal"
        / "action_receipts"
        / "portal-action-001.json"
    )
    before = receipt_path.read_text(encoding="utf-8")

    second = actions.write_action_receipt(
        profile=profile,
        action="pause",
        study_id="001-risk",
        idempotency_key="portal-action-001",
        requested_at="2026-05-09T02:00:00+00:00",
    )

    assert first == second
    assert receipt_path.read_text(encoding="utf-8") == before
    assert first["action"] == "pause"
    assert first["study_id"] == "001-risk"
    assert first["mode"] == "action_request"
    assert first["apply"] is False
    assert first["controller_owned"] is True
    assert first["status"] == "accepted_for_controller_dispatch"
    assert first["audit_ref"] == "artifacts/runtime/progress_portal/action_receipts/portal-action-001.json"
    assert first["forbidden_writes"] == [
        "paper",
        "package",
        "publication_gate",
        "controller_decision",
        "runtime_sqlite_authority",
    ]
    assert not (profile.workspace_root / "artifacts" / "controller_decisions").exists()


def test_progress_portal_authorized_actions_mark_inspect_and_reconcile_as_dry_run(tmp_path: Path) -> None:
    actions = importlib.import_module("med_autoscience.controllers.progress_portal_parts.authorized_actions")
    profile = make_profile(tmp_path)

    inspect_receipt = actions.write_action_receipt(
        profile=profile,
        action="inspect",
        study_id="001-risk",
        idempotency_key="inspect-001",
    )
    reconcile_receipt = actions.write_action_receipt(
        profile=profile,
        action="reconcile-dry-run",
        study_id="001-risk",
        idempotency_key="reconcile-001",
    )

    assert inspect_receipt["mode"] == "dry_run"
    assert inspect_receipt["dry_run"] is True
    assert reconcile_receipt["mode"] == "dry_run"
    assert reconcile_receipt["dry_run"] is True


def test_progress_portal_actions_endpoint_is_default_off_and_enable_actions_writes_receipt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    served: dict[str, object] = {}

    class FakeServer:
        server_address = ("127.0.0.1", 4302)

        def __init__(self, address, handler):
            served["address"] = address
            served["handler"] = handler

        def serve_forever(self) -> None:
            served["served"] = True

        def server_close(self) -> None:
            served["closed"] = True

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.socketserver, "TCPServer", FakeServer)
    try:
        default_off = module.serve_progress_portal(
            profile=profile,
            study_id="001-risk",
            progress_payload=_progress_payload(),
            host="127.0.0.1",
            port=4302,
            once=True,
        )
        disabled_response = _post_progress_portal_action(
            served["handler"],
            {"action": "inspect", "study_id": "001-risk", "idempotency_key": "endpoint-disabled-001"},
        )

        enabled = module.serve_progress_portal(
            profile=profile,
            study_id="001-risk",
            progress_payload=_progress_payload(),
            host="127.0.0.1",
            port=4302,
            once=True,
            enable_actions=True,
        )
        enabled_response = _post_progress_portal_action(
            served["handler"],
            {"action": "inspect", "study_id": "001-risk", "idempotency_key": "endpoint-enabled-001"},
        )
    finally:
        monkeypatch.undo()

    assert default_off["actions_enabled"] is False
    assert disabled_response["status_code"] == 404
    assert disabled_response["body"]["status"] == "disabled"
    assert enabled["actions_enabled"] is True
    assert enabled_response["status_code"] == 200
    assert enabled_response["body"]["action"] == "inspect"
    assert enabled_response["body"]["mode"] == "dry_run"
    assert enabled_response["body"]["controller_owned"] is True
    assert (
        profile.workspace_root
        / "artifacts"
        / "runtime"
        / "progress_portal"
        / "action_receipts"
        / "endpoint-enabled-001.json"
    ).exists()


def _post_progress_portal_action(handler_class: object, payload: dict[str, object]) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8")
    handler = object.__new__(handler_class)
    handler.path = "/actions"
    handler.command = "POST"
    handler.request_version = "HTTP/1.1"
    handler.close_connection = False
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler.log_request = lambda *args, **kwargs: None
    handler.do_POST()
    raw = handler.wfile.getvalue()
    status_line, _, response_body = raw.partition(b"\r\n\r\n")
    status_code = int(status_line.split()[1])
    return {"status_code": status_code, "body": json.loads(response_body.decode("utf-8"))}
