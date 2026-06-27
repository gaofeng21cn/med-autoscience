from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from types import SimpleNamespace

from med_autoscience.display_pack_paths import core_medical_display_pack_root


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_PACK_ROOT = core_medical_display_pack_root(REPO_ROOT)
CORE_PACK_MODULE_ROOT = (
    CORE_PACK_ROOT
    / "src"
    / "fenggaolab_org_medical_display_core"
)
CORE_PACK_SRC_ROOT = CORE_PACK_MODULE_ROOT.parent


def _candidate_request(
    *,
    template_id: str,
    payload: dict[str, object],
    output_dir: Path,
) -> Path:
    request_path = output_dir / f"{template_id}.request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "execution_mode": "subprocess",
                "renderer_family": "r_ggplot2",
                "figure_id": f"candidate-{template_id}",
                "template_id": f"fenggaolab.org.medical-display-core::{template_id}",
                "short_template_id": template_id,
                "display_payload": payload,
                "output_png_path": str(output_dir / f"{template_id}.png"),
                "output_pdf_path": str(output_dir / f"{template_id}.pdf"),
                "layout_sidecar_path": str(output_dir / f"{template_id}.layout.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return request_path
