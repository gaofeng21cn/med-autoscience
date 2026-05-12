from __future__ import annotations

from pathlib import Path


def write_endpoint_provenance_note_fixture(paper_root: Path) -> None:
    (paper_root / "endpoint_provenance_note.md").write_text(
        "# Endpoint Provenance Note\n\n"
        "- endpoint_name: removal_rate\n"
        "- provenance_caveat: In the frozen cohort, `removal_rate` is treated as a working early residual / non-GTR label and retains an explicit 3-month MRI provenance caveat.\n"
        "- manuscript_required_statement: The endpoint was based on the audited removal_rate field and should be interpreted as a working proxy for early residual status with an explicit 3-month MRI provenance caveat.\n",
        encoding="utf-8",
    )
