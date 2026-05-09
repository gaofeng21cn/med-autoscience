from __future__ import annotations

from collections.abc import Callable, Mapping
import http.server
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from med_autoscience.profiles import WorkspaceProfile

from .authorized_actions import PortalActionError, write_action_receipt


def build_progress_portal_handler(
    *,
    serve_root: Path,
    refresh: Callable[[], Mapping[str, Any]],
    profile: WorkspaceProfile,
    study_id: str | None,
    enable_actions: bool,
) -> type[http.server.SimpleHTTPRequestHandler]:
    class ProgressPortalHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(serve_root), **kwargs)

        def do_GET(self) -> None:  # noqa: N802
            refresh()
            super().do_GET()

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/actions":
                self.send_error(404, "not found")
                return
            if not enable_actions:
                self._write_json({"status": "disabled", "reason": "portal_actions_disabled"}, status_code=404)
                return
            try:
                request = self._read_json_body()
                receipt = write_action_receipt(
                    profile=profile,
                    action=str(request.get("action") or ""),
                    study_id=str(request.get("study_id") or study_id or ""),
                    quest_id=str(request.get("quest_id") or ""),
                    idempotency_key=str(request.get("idempotency_key") or ""),
                    apply=True,
                )
            except PortalActionError as exc:
                self._write_json({"status": "rejected", "reason": exc.reason}, status_code=exc.status_code)
                return
            except json.JSONDecodeError:
                self._write_json({"status": "rejected", "reason": "invalid_json"}, status_code=400)
                return
            self._write_json(receipt, status_code=200)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8") if length else "{}")
            if not isinstance(payload, dict):
                raise PortalActionError(status_code=400, reason="json_body_not_object")
            return dict(payload)

        def _write_json(self, payload: Mapping[str, Any], *, status_code: int) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ProgressPortalHandler


__all__ = ["build_progress_portal_handler"]
