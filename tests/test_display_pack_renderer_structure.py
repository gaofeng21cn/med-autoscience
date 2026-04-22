from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PACK_MODULE_ROOT = (
    REPO_ROOT
    / "display-packs"
    / "fenggaolab.org.medical-display-core"
    / "src"
    / "fenggaolab_org_medical_display_core"
)
CORE_PACK_SRC_ROOT = CORE_PACK_MODULE_ROOT.parent


def test_core_pack_evidence_renderer_is_split_into_maintainable_modules() -> None:
    legacy_single_file = CORE_PACK_MODULE_ROOT / "evidence_figures.py"
    evidence_package = CORE_PACK_MODULE_ROOT / "evidence_figures"

    assert not legacy_single_file.exists()
    assert (evidence_package / "__init__.py").exists()

    module_line_counts = {
        path.relative_to(CORE_PACK_MODULE_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in evidence_package.glob("*.py")
    }

    assert module_line_counts
    assert module_line_counts["evidence_figures/__init__.py"] <= 220
    assert max(module_line_counts.values()) <= 6500


def test_core_pack_evidence_renderer_keeps_stable_entrypoints() -> None:
    sys.path.insert(0, str(CORE_PACK_SRC_ROOT))
    module = importlib.import_module("fenggaolab_org_medical_display_core.evidence_figures")

    assert callable(module.render_r_evidence_figure)
    assert callable(module.render_python_evidence_figure)
