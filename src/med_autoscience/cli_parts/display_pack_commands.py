from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json_object_file(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload file must contain an object")
    return payload


def _load_visual_audit_review_from_args(args: argparse.Namespace) -> dict[str, object]:
    payload_json = getattr(args, "visual_audit_review_json", None)
    payload_file = getattr(args, "visual_audit_review_file", None)
    if payload_file:
        return _load_json_object_file(payload_file)
    payload = json.loads(str(payload_json))
    if not isinstance(payload, dict):
        raise SystemExit("visual audit review JSON must contain an object")
    return payload


def handle_display_pack_command(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.command != "display-pack-e2e":
        return None

    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    return materialize_display_pack_publication_manifest(
        repo_root=Path(args.repo_root),
        paper_root=Path(args.paper_root),
        visual_audit_review=_load_visual_audit_review_from_args(args),
        figure_ids=list(getattr(args, "figure_id", []) or []),
    )
