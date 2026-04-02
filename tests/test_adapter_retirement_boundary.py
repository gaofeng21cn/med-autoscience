from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"
ADAPTER_ROOT = SRC_ROOT / "adapters" / "deepscientist"


def test_production_code_does_not_import_deepscientist_adapters() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(ADAPTER_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if "med_autoscience.adapters.deepscientist" not in text and "adapters.deepscientist" not in text:
            continue
        violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_legacy_deepscientist_adapter_modules_are_removed() -> None:
    assert not (ADAPTER_ROOT / "__init__.py").exists()
    assert not (ADAPTER_ROOT / "daemon_api.py").exists()
    assert not (ADAPTER_ROOT / "mailbox.py").exists()
    assert not (ADAPTER_ROOT / "runtime.py").exists()
    assert not (ADAPTER_ROOT / "paper_bundle.py").exists()
