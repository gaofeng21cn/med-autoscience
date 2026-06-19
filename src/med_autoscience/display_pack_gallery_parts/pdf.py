from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from med_autoscience.display_pack_gallery_parts import paths


def _export_pdf() -> None:
    chrome_candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    )
    chrome = next((str(path) for path in chrome_candidates if path.exists()), None)
    if chrome is None:
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome is None:
        raise RuntimeError("Chrome/Chromium is required to export the gallery PDF")
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={paths.PDF_PATH}",
            f"file://{paths.HTML_PATH}",
        ],
        check=True,
        cwd=paths.REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )


def _copy_docs_gallery() -> None:
    paths.DOCS_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.PDF_PATH, paths.DOCS_PDF_PATH)
    shutil.copy2(paths.REFERENCE_PATH, paths.DOCS_REFERENCE_PATH)
    shutil.copy2(paths.QUALITY_AUDIT_PATH, paths.DOCS_QUALITY_AUDIT_PATH)
